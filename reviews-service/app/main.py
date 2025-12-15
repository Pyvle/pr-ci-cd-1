
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from .db import init_db, get_conn
def _get_admin_token() -> str:
    return os.getenv("ADMIN_TOKEN", "change-me")

from .schemas import ReviewCreate, ReviewUpdate, ReportCreate, VoteRequest

app = FastAPI(title="reviews-service", version="1.0.0")

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

def _require_user(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return x_user_id

def _require_admin(x_admin_token: str | None) -> None:
    if not x_admin_token or x_admin_token != _get_admin_token():
        raise HTTPException(status_code=403, detail="Admin token invalid")

@app.post("/reviews")
def create_review(payload: ReviewCreate, x_user_id: str | None = Header(default=None, alias="X-User-Id")):
    user_id = _require_user(x_user_id)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reviews (product_id, author_user_id, rating, text) VALUES (?, ?, ?, ?)",
            (payload.product_id, user_id, payload.rating, payload.text),
        )
        review_id = cur.lastrowid
        conn.commit()
    # "Отзыв на товар создан"
    return JSONResponse(status_code=201, content={"id": review_id, "status": "created"})

@app.get("/reviews/{review_id}")
def get_review(review_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Review not found")
        return dict(row)

@app.put("/reviews/{review_id}")
def edit_review(
    review_id: int,
    payload: ReviewUpdate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    user_id = _require_user(x_user_id)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cur.fetchone()
        if not row or row["is_deleted"]:
            raise HTTPException(status_code=404, detail="Review not found")
        if row["author_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can edit only your own review")

        new_rating = payload.rating if payload.rating is not None else row["rating"]
        new_text = payload.text if payload.text is not None else row["text"]
        cur.execute(
            "UPDATE reviews SET rating = ?, text = ?, updated_at = datetime('now') WHERE id = ?",
            (new_rating, new_text, review_id),
        )
        conn.commit()
    # "Отзыв на товар отредактирован"
    return {"status": "edited", "id": review_id}

@app.delete("/reviews/{review_id}")
def delete_own_review(
    review_id: int,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    user_id = _require_user(x_user_id)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cur.fetchone()
        if not row or row["is_deleted"]:
            raise HTTPException(status_code=404, detail="Review not found")
        if row["author_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can delete only your own review")
        cur.execute(
            "UPDATE reviews SET is_deleted = 1, deleted_by = ?, updated_at = datetime('now') WHERE id = ?",
            (f"user:{user_id}", review_id),
        )
        conn.commit()
    # "Отзыв на товар удалён пользователем"
    return {"status": "deleted_by_user", "id": review_id}

@app.delete("/admin/reviews/{review_id}")
def moderator_delete_review(review_id: int, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cur.fetchone()
        if not row or row["is_deleted"]:
            raise HTTPException(status_code=404, detail="Review not found")
        cur.execute(
            "UPDATE reviews SET is_deleted = 1, deleted_by = 'moderator', updated_at = datetime('now') WHERE id = ?",
            (review_id,),
        )
        conn.commit()
    # "Отзыв на товар удалён модератором"
    return {"status": "deleted_by_moderator", "id": review_id}

@app.post("/reviews/{review_id}/report")
def report_review(
    review_id: int,
    payload: ReportCreate,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    _ = _require_user(x_user_id)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cur.fetchone()
        if not row or row["is_deleted"]:
            raise HTTPException(status_code=404, detail="Review not found")
        # простая политика: жалоба сразу помечает отзыв как нарушающий правила
        cur.execute(
            "UPDATE reviews SET reports_count = reports_count + 1, is_violation = 1, updated_at = datetime('now') WHERE id = ?",
            (review_id,),
        )
        conn.commit()
    # "Отзыв на товар помечен как нарушающий правила"
    return {"status": "marked_as_violation", "id": review_id, "reason": payload.reason}

@app.post("/reviews/{review_id}/vote")
def vote_review(
    review_id: int,
    payload: VoteRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    user_id = _require_user(x_user_id)
    if payload.value not in (1, -1):
        raise HTTPException(status_code=422, detail="value must be +1 or -1")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cur.fetchone()
        if not row or row["is_deleted"]:
            raise HTTPException(status_code=404, detail="Review not found")
        cur.execute(
            "INSERT OR REPLACE INTO review_votes (review_id, voter_user_id, value) VALUES (?, ?, ?)",
            (review_id, user_id, payload.value),
        )
        conn.commit()
    # "Отзыв отмечен пользователем как полезный/бесполезный"
    return {"status": "voted", "id": review_id, "value": payload.value}

@app.post("/products/{product_id}/recalculate-rating")
def recalc_rating(product_id: str):
    # "Пересчитать рейтинг товара" => "Оценка товара обновлена на основе отзывов"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) as cnt, AVG(rating) as avg
            FROM reviews
            WHERE product_id = ? AND is_deleted = 0 AND is_violation = 0
            """,
            (product_id,),
        )
        agg = cur.fetchone()
        cnt = int(agg["cnt"] or 0)
        avg = float(agg["avg"] or 0.0)
        cur.execute(
            "INSERT OR REPLACE INTO product_ratings (product_id, avg_rating, votes_count, updated_at) VALUES (?, ?, ?, datetime('now'))",
            (product_id, avg, cnt),
        )
        conn.commit()
        return {"product_id": product_id, "avg_rating": avg, "votes_count": cnt, "status": "updated"}

@app.get("/products/{product_id}/rating")
def get_rating(product_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM product_ratings WHERE product_id = ?", (product_id,))
        row = cur.fetchone()
        if not row:
            return {"product_id": product_id, "avg_rating": 0.0, "votes_count": 0}
        return dict(row)

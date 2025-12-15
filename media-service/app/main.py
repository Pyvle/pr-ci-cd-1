
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from .db import init_db, get_conn
def _get_admin_token() -> str:
    return os.getenv("ADMIN_TOKEN", "change-me")

from .schemas import ImageCreate, VideoCreate, GalleryUpdate

app = FastAPI(title="media-service", version="1.0.0")

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

def _require_admin(x_admin_token: str | None) -> None:
    if not x_admin_token or x_admin_token != _get_admin_token():
        raise HTTPException(status_code=403, detail="Admin token invalid")

# --- Admin actions (по диаграмме: администратор)

@app.post("/admin/products/{product_id}/images")
def upload_image(product_id: str, payload: ImageCreate, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO media (product_id, kind, url, is_main) VALUES (?, 'image', ?, 0)",
            (product_id, payload.url),
        )
        media_id = cur.lastrowid
        conn.commit()
    # "Изображение товара загружено"
    return JSONResponse(status_code=201, content={"id": media_id, "status": "image_uploaded"})

@app.delete("/admin/images/{image_id}")
def delete_image(image_id: int, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM media WHERE id = ? AND kind = 'image'", (image_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        conn.commit()
    # "Изображение товара удалено"
    return {"status": "image_deleted", "id": image_id}

@app.put("/admin/products/{product_id}/images/{image_id}/set-main")
def set_main_image(product_id: str, image_id: int, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE media SET is_main = 0, updated_at = datetime('now') WHERE product_id = ? AND kind = 'image'", (product_id,))
        cur.execute(
            "UPDATE media SET is_main = 1, updated_at = datetime('now') WHERE id = ? AND product_id = ? AND kind = 'image'",
            (image_id, product_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Image not found for product")
        conn.commit()
    # "Главное изображение товара изменено"
    return {"status": "main_image_changed", "id": image_id, "product_id": product_id}

@app.put("/admin/products/{product_id}/gallery")
def update_gallery(product_id: str, payload: GalleryUpdate, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        # replace only images for product
        cur.execute("DELETE FROM media WHERE product_id = ? AND kind = 'image'", (product_id,))
        for url in payload.urls:
            cur.execute("INSERT INTO media (product_id, kind, url, is_main) VALUES (?, 'image', ?, 0)", (product_id, url))
        conn.commit()
    # "Галерея изображений товара обновлена"
    return {"status": "gallery_updated", "product_id": product_id, "count": len(payload.urls)}

@app.post("/admin/products/{product_id}/videos")
def add_video_review(product_id: str, payload: VideoCreate, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO media (product_id, kind, url, title, is_main) VALUES (?, 'video', ?, ?, 0)",
            (product_id, payload.url, payload.title),
        )
        media_id = cur.lastrowid
        conn.commit()
    # "Видео-обзор товара добавлен"
    return JSONResponse(status_code=201, content={"id": media_id, "status": "video_added"})

@app.put("/admin/media/{media_id}/outdated")
def mark_outdated(media_id: int, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE media SET is_outdated = 1, updated_at = datetime('now') WHERE id = ?", (media_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Media not found")
        conn.commit()
    # "Медиа-файл помечен как неактуальный"
    return {"status": "marked_outdated", "id": media_id}

# --- User actions (по диаграмме: покупатель)

@app.get("/products/{product_id}/images")
def list_images(product_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM media WHERE product_id = ? AND kind = 'image' ORDER BY is_main DESC, id ASC",
            (product_id,),
        )
        return {"product_id": product_id, "images": [dict(r) for r in cur.fetchall()]}

@app.get("/images/{image_id}")
def view_image(image_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM media WHERE id = ? AND kind = 'image'", (image_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Image not found")
        cur.execute("UPDATE media SET views_count = views_count + 1, updated_at = datetime('now') WHERE id = ?", (image_id,))
        conn.commit()
        # "Изображение товара просмотрено пользователем"
        out = dict(row)
        out["views_count"] = out["views_count"] + 1
        return out

@app.get("/videos/{video_id}")
def view_video(video_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM media WHERE id = ? AND kind = 'video'", (video_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Video not found")
        cur.execute("UPDATE media SET views_count = views_count + 1, updated_at = datetime('now') WHERE id = ?", (video_id,))
        conn.commit()
        # "Видео-обзор товара просмотрен пользователем"
        out = dict(row)
        out["views_count"] = out["views_count"] + 1
        return out

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_create_edit_vote_recalc_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    from app.db import init_db
    init_db()

    r = client.post("/reviews", headers={"X-User-Id": "u1"}, json={"product_id": "p1", "rating": 5, "text": "ok"})
    assert r.status_code == 201
    review_id = r.json()["id"]

    r = client.put(f"/reviews/{review_id}", headers={"X-User-Id": "u1"}, json={"text": "better"})
    assert r.status_code == 200

    r = client.post(f"/reviews/{review_id}/vote", headers={"X-User-Id": "u2"}, json={"value": 1})
    assert r.status_code == 200
    assert r.json()["value"] == 1

    r = client.post("/products/p1/recalculate-rating")
    assert r.status_code == 200
    assert r.json()["votes_count"] == 1
    assert r.json()["avg_rating"] == 5.0

def test_report_marks_violation(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test2.db")
    from app.db import init_db
    init_db()

    r = client.post("/reviews", headers={"X-User-Id": "u1"}, json={"product_id": "p1", "rating": 4, "text": "meh"})
    review_id = r.json()["id"]

    r = client.post(f"/reviews/{review_id}/report", headers={"X-User-Id": "u2"}, json={"reason": "spam"})
    assert r.status_code == 200
    assert r.json()["status"] == "marked_as_violation"

    r = client.post("/products/p1/recalculate-rating")
    assert r.status_code == 200
    assert r.json()["votes_count"] == 0
    assert r.json()["avg_rating"] == 0.0

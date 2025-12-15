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

def test_admin_upload_and_view(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/m.db")
    monkeypatch.setenv("ADMIN_TOKEN", "secret")
    from app.db import init_db
    init_db()

    r = client.post("/admin/products/p1/images", headers={"X-Admin-Token": "secret"}, json={"url": "https://img/1.jpg"})
    assert r.status_code == 201
    img_id = r.json()["id"]

    r = client.get(f"/images/{img_id}")
    assert r.status_code == 200
    assert r.json()["views_count"] == 1

    r = client.post("/admin/products/p1/videos", headers={"X-Admin-Token": "secret"}, json={"url": "https://vid/1.mp4", "title": "demo"})
    assert r.status_code == 201
    vid_id = r.json()["id"]

    r = client.get(f"/videos/{vid_id}")
    assert r.status_code == 200
    assert r.json()["views_count"] == 1

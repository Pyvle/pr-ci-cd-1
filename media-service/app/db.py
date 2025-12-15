
import os
import sqlite3
from contextlib import contextmanager

DEFAULT_DB = "sqlite:////data/media.db"

def _sqlite_path(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite URLs are supported. Example: sqlite:////data/media.db")
    return database_url.replace("sqlite:///", "", 1)

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DB)

@contextmanager
def get_conn():
    db_url = get_database_url()
    path = _sqlite_path(db_url)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            kind TEXT NOT NULL, -- image|video
            url TEXT NOT NULL,
            title TEXT,
            is_main INTEGER NOT NULL DEFAULT 0,
            is_outdated INTEGER NOT NULL DEFAULT 0,
            views_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        conn.commit()


import os
import sqlite3
from contextlib import contextmanager

DEFAULT_DB = "sqlite:////data/reviews.db"

def _sqlite_path(database_url: str) -> str:
    # Accept forms:
    # - sqlite:////abs/path.db
    # - sqlite:///rel/path.db
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite URLs are supported. Example: sqlite:////data/reviews.db")
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
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            author_user_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            text TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            deleted_by TEXT,
            is_violation INTEGER NOT NULL DEFAULT 0,
            reports_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS review_votes (
            review_id INTEGER NOT NULL,
            voter_user_id TEXT NOT NULL,
            value INTEGER NOT NULL, -- +1 helpful, -1 unhelpful
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (review_id, voter_user_id)
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS product_ratings (
            product_id TEXT PRIMARY KEY,
            avg_rating REAL NOT NULL,
            votes_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        conn.commit()

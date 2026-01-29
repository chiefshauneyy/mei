import sqlite3
from pathlib import Path

def get_conn(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS kv (
      k TEXT PRIMARY KEY,
      v TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS price_watch (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      url TEXT NOT NULL,
      last_price REAL,
      currency TEXT,
      updated_at TEXT NOT NULL
    )
    """)
    conn.commit()

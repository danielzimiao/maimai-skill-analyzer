import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "db.sqlite"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS songs (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          name          TEXT NOT NULL,
          tags          TEXT NOT NULL,
          difficulty    REAL,
          release_date  TEXT,
          bg_image_url  TEXT
        )
    """)
    conn.commit()
    conn.close()


_init_db()


def insert_song(name: str, tags: list, difficulty: float | None, release_date: str | None, bg_image_url: str | None):
    conn = _connect()
    conn.execute(
        "INSERT INTO songs (name, tags, difficulty, release_date, bg_image_url) VALUES (?, ?, ?, ?, ?)",
        (name, json.dumps(tags), difficulty, release_date, bg_image_url),
    )
    conn.commit()
    conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["tags"] = json.loads(d["tags"])
    return {k: d[k] for k in ("name", "difficulty", "release_date", "bg_image_url", "tags")}


def find_similar(tags: list[str], limit: int = 3) -> list[dict]:
    if not tags:
        return []
    placeholders = ", ".join("?" * len(tags))
    sql = f"""
        SELECT *, (
          SELECT COUNT(*) FROM json_each(songs.tags)
          WHERE value IN ({placeholders})
        ) AS overlap
        FROM songs
        WHERE overlap > 0
        ORDER BY overlap DESC
        LIMIT ?
    """
    conn = _connect()
    rows = conn.execute(sql, tags + [limit]).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_songs_by_tag(tag: str) -> list[dict]:
    sql = """
        SELECT * FROM songs
        WHERE EXISTS (
          SELECT 1 FROM json_each(tags) WHERE value = ?
        )
        ORDER BY release_date DESC NULLS LAST, name ASC
    """
    conn = _connect()
    rows = conn.execute(sql, (tag,)).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]

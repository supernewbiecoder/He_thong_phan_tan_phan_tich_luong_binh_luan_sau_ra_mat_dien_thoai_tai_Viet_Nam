import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS quota(day TEXT PRIMARY KEY, units INTEGER DEFAULT 0,
  search_calls INTEGER DEFAULT 0, exhausted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS channels(channel_id TEXT PRIMARY KEY, handle TEXT, title TEXT, uploads_playlist TEXT);
CREATE TABLE IF NOT EXISTS videos(video_id TEXT PRIMARY KEY, channel_id TEXT, title TEXT,
  published_at TEXT, model TEXT, comment_count INTEGER,
  status TEXT DEFAULT 'pending',  -- pending | backfilling | tracking | done | disabled
  page_token TEXT, watermark TEXT, pending_max TEXT, last_crawled TEXT);
CREATE TABLE IF NOT EXISTS seen(comment_id TEXT PRIMARY KEY);
"""


VIDEO_EXTRA_COLS = {"channel_title": "TEXT", "video_type": "TEXT", "view_count": "INTEGER",
                    "like_count": "INTEGER", "fetched_at": "TEXT"}


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA synchronous=NORMAL")   # WAL + NORMAL: commit nhanh, giữ khóa ghi ngắn hơn
    conn.executescript(SCHEMA)
    have = {r[1] for r in conn.execute("PRAGMA table_info(videos)")}
    for name, typ in VIDEO_EXTRA_COLS.items():
        if name not in have:
            conn.execute(f"ALTER TABLE videos ADD COLUMN {name} {typ}")
    conn.commit()
    return conn

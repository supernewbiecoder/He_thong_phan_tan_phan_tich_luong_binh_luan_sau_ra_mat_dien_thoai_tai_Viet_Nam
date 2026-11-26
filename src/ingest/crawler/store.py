"""
Mục đích: Tạo và mở cơ sở dữ liệu trạng thái của crawler (src/ingest/data/state.db, SQLite); cập nhật lần cuối: 2026-11-11.

Bảng: quota (hạn mức đã dùng theo ngày), channels, uploads (mọi video của kênh, kể cả video không được chọn),
channel_scan (tiến độ quét kênh), videos (video được chọn và trạng thái crawl), seen (bình luận đã ghi, chống trùng),
comment_authors, authors (tài khoản người bình luận, có tên thật: chỉ giữ trên máy, không chia sẻ).
connect() tạo bảng nếu chưa có và bật chế độ WAL.
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS quota(day TEXT PRIMARY KEY, units INTEGER DEFAULT 0,
  search_calls INTEGER DEFAULT 0, exhausted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS channels(channel_id TEXT PRIMARY KEY, handle TEXT, title TEXT, uploads_playlist TEXT);
CREATE TABLE IF NOT EXISTS videos(video_id TEXT PRIMARY KEY, channel_id TEXT, title TEXT,
  published_at TEXT, model TEXT, comment_count INTEGER,
  status TEXT DEFAULT 'pending',  -- pending | backfilling | tracking | done | disabled | excluded
  page_token TEXT, watermark TEXT, pending_max TEXT, last_crawled TEXT);
CREATE TABLE IF NOT EXISTS seen(comment_id TEXT PRIMARY KEY);
-- Bộ nhớ đệm MỌI video trong playlist uploads của các kênh (kể cả video không khớp mẫu nào).
-- Nhờ đó đổi config (thêm mẫu/alias) chỉ cần phân loại lại trên máy, không tốn quota quét lại kênh.
CREATE TABLE IF NOT EXISTS uploads(video_id TEXT PRIMARY KEY, channel_id TEXT, title TEXT, published_at TEXT);
CREATE INDEX IF NOT EXISTS uploads_pub ON uploads(published_at);
-- Tiến độ quét uploads của từng kênh:
--   head_pub   video mới nhất đã thấy (lần sau chỉ quét phần mới hơn mốc này)
--   tail_token trang kế tiếp để quét tiếp về quá khứ; tail_pub video cũ nhất đã quét tới
--   tail_done  1 = đã quét hết playlist
-- Tài khoản người bình luận (KHÔNG xuất ra dataset chung; dataset chỉ có author_hash + các trường author_* đã tính):
--   comment_authors: comment -> kênh người viết (status ok | missing = comment đã bị xóa)
--   authors        : thông tin kênh người viết (status ok | missing = kênh bị khóa/xóa)
CREATE TABLE IF NOT EXISTS comment_authors(comment_id TEXT PRIMARY KEY, author_channel_id TEXT, author_name TEXT,
  status TEXT, fetched_at TEXT);
CREATE INDEX IF NOT EXISTS comment_authors_ch ON comment_authors(author_channel_id);
CREATE TABLE IF NOT EXISTS authors(channel_id TEXT PRIMARY KEY, title TEXT, created_at TEXT, video_count INTEGER,
  subscriber_count INTEGER, status TEXT, fetched_at TEXT);
CREATE TABLE IF NOT EXISTS channel_scan(channel_id TEXT PRIMARY KEY, head_pub TEXT, tail_token TEXT,
  tail_pub TEXT, tail_done INTEGER DEFAULT 0, pages INTEGER DEFAULT 0, last_scan TEXT);
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

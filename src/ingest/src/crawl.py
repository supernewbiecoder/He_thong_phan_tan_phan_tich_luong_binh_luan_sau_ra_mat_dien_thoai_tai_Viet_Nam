"""Cào comment theo từng video, có thể dừng/tiếp tục bất kỳ lúc nào (hết hạn mức, tắt máy).
Trạng thái lưu trong SQLite: page_token đang dở + watermark (comment mới nhất đã cào)."""
import hashlib
import logging
from .quota import QuotaExceeded
from .schema import SCHEMA_VERSION
from .models import window
from .timeutil import iso, now, parse
from .youtube import CommentsDisabled, YouTubeError

log = logging.getLogger("crawl")
STATS = {"new": 0}  # tổng comment mới của lần chạy hiện tại


def author_hash(author_channel, salt):
    return hashlib.sha256((salt + (author_channel or "unknown")).encode()).hexdigest()


def make_record(c, video, parent_id, parent_text, reply_count, fetched_at, salt):
    sn = c["snippet"]
    acid = (sn.get("authorChannelId") or {}).get("value")
    return {
        "comment_id": c["id"], "video_id": video["video_id"],
        "parent_id": parent_id,            # luôn trỏ về comment gốc (YouTube chỉ có 2 tầng)
        "parent_text": parent_text,        # nội dung comment gốc, làm ngữ cảnh cho reply
        "model": video["model"],           # tên mẫu theo video; video nhiều mẫu: 'a|b'
        "source": "youtube",
        "text": sn["textDisplay"], "text_norm": "",   # text_norm do Team Data Science ghi
        "author_hash": author_hash(acid, salt),
        "published_at": iso(parse(sn["publishedAt"])),
        "like_count": sn.get("likeCount", 0),
        "reply_count": reply_count,        # chỉ có ở comment gốc (totalReplyCount); reply thì None
        "fetched_at": fetched_at,           # thời điểm API trả like_count/reply_count
        "ingested_at": None,               # Sink điền lúc ghi archive/Kafka
        "schema_version": SCHEMA_VERSION,
    }


def crawl_video(cfg, yt, conn, sink, v):
    vid, start, end = v["video_id"], *window(cfg, v["model"])
    token = v["page_token"]
    pending_max = parse(v["pending_max"]) if v["pending_max"] else None
    floor = max(start, parse(v["watermark"])) if v["watermark"] else start
    streak_stop = cfg["crawl"]["older_streak_stop"]
    streak = 0
    conn.execute("UPDATE videos SET status=CASE WHEN status='pending' THEN 'backfilling' ELSE status END WHERE video_id=?", (vid,))
    conn.commit()   # nhả khóa ghi TRƯỚC khi gọi mạng

    def fresh(c, parent=None, parent_text=None, reply_count=None):
        ts = parse(c["snippet"]["publishedAt"])
        if not (start <= ts <= end):
            return None
        if conn.execute("SELECT 1 FROM seen WHERE comment_id=?", (c["id"],)).fetchone():
            return None
        return make_record(c, v, parent, parent_text, reply_count, fetched, cfg["salt"])

    while True:
        try:
            data = yt.comment_threads(vid, token)
            fetched = iso(now())
            recs, stop = [], False
            for th in data.get("items", []):
                top = th["snippet"]["topLevelComment"]
                ts = parse(top["snippet"]["publishedAt"])
                streak = streak + 1 if ts < floor else 0
                if streak >= streak_stop:
                    stop = True
                    break
                pending_max = max(pending_max, ts) if pending_max else ts
                r = fresh(top, reply_count=th["snippet"].get("totalReplyCount", 0))
                if r:
                    recs.append(r)
                replies = (th.get("replies") or {}).get("comments", [])
                if th["snippet"].get("totalReplyCount", 0) > len(replies):
                    replies = yt.all_replies(top["id"])
                for rp in replies:
                    r = fresh(rp, top["id"], top["snippet"]["textDisplay"])
                    if r:
                        recs.append(r)
        except CommentsDisabled:
            conn.execute("UPDATE videos SET status='disabled' WHERE video_id=?", (vid,))
            conn.commit()
            return 0
        # Xí chỗ nguyên tử: INSERT OR IGNORE vào `seen` trả rowcount=0 nếu comment đã có (do trang bị lặp,
        # lượt cào khác hoặc tiến trình khác). Chỉ comment xí được mới được ghi. Khóa ghi của SQLite được giữ
        # từ lúc xí chỗ đến commit nên hai bên không thể cùng ghi một comment.
        token = data.get("nextPageToken")
        try:
            claimed = [r for r in recs
                       if conn.execute("INSERT OR IGNORE INTO seen VALUES(?)", (r["comment_id"],)).rowcount]
            sink.write(claimed)   # lỗi (Kafka...) -> rollback, hoàn trả các comment đã xí
            conn.execute("UPDATE videos SET page_token=?, pending_max=? WHERE video_id=?",
                         (None if stop else token, iso(pending_max) if pending_max else None, vid))
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        STATS["new"] += len(claimed)
        if stop or not token:
            break

    wm = max(filter(None, [pending_max, parse(v["watermark"]) if v["watermark"] else None]), default=None)
    status = "tracking" if now() < end else "done"
    conn.execute("UPDATE videos SET status=?, page_token=NULL, pending_max=NULL, watermark=?, last_crawled=? WHERE video_id=?",
                 (status, iso(wm) if wm else None, iso(now()), vid))
    conn.commit()
    return 1


def run_crawl(cfg, yt, conn, sink):
    STATS["new"] = 0
    poll = cfg["crawl"]["min_poll_interval_min"] * 60
    rows = conn.execute("""SELECT * FROM videos WHERE status IN ('pending','backfilling')
                           ORDER BY (status='backfilling') DESC, published_at""").fetchall()
    tracking = [r for r in conn.execute("SELECT * FROM videos WHERE status='tracking' ORDER BY last_crawled").fetchall()
                if (now() - parse(r["last_crawled"])).total_seconds() >= poll]
    done = 0
    for v in list(rows) + tracking:
        try:
            done += crawl_video(cfg, yt, conn, sink, v)
        except QuotaExceeded as e:
            log.warning("Dừng crawl: %s (đã xong %d video)", e, done)
            break
        except YouTubeError as e:   # tiến độ video này đã lưu theo từng trang, lần sau làm tiếp
            log.warning("Video %s lỗi, bỏ qua lần này: %s", v["video_id"], e)
    log.info("Crawl xong: %d video, %d comment mới", done, STATS["new"])
    return STATS["new"]

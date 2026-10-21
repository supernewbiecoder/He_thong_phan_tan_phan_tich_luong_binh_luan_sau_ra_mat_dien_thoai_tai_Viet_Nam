"""Tìm video review/unbox/so sánh từ danh sách kênh. Tiết kiệm hạn mức: KHÔNG dùng search.list,
đi qua playlist 'uploads' của kênh (1 đơn vị / 50 video) rồi lọc theo tiêu đề + ngày đăng."""
import json
import logging
import re
from . import config
from .quota import QuotaExceeded
from .schema import SCHEMA_VERSION
from .youtube import YouTubeError
from .models import bounds, classify, window
from .timeutil import iso, now, parse, unaccent

log = logging.getLogger("discover")


def resolve_channels(cfg, yt, conn):
    """Đọc mục channels: channel_id (UC... hoặc @handle), name, enabled, tags."""
    out = []
    for ch in cfg.get("channels") or []:
        if not ch.get("enabled", True):
            continue
        key = ch.get("channel_id") or ch.get("handle") or ch.get("id")
        if not key:
            log.warning("Bỏ qua '%s': chưa có channel_id (chạy resolve-names hoặc tự điền)", ch.get("name"))
            continue
        row = conn.execute("SELECT * FROM channels WHERE handle=? OR channel_id=?", (key, key)).fetchone()
        if not row:
            by_handle = key.startswith("@")
            try:
                item = yt.channel(handle=key if by_handle else None, channel_id=None if by_handle else key)
            except YouTubeError as e:
                log.warning("Bỏ qua kênh %s (%s): %s", key, ch.get("name"), e)
                continue
            if not item:
                log.warning("Không tìm thấy kênh %s (%s)", key, ch.get("name"))
                continue
            conn.execute("INSERT OR REPLACE INTO channels VALUES(?,?,?,?)", (
                item["id"], key if by_handle else None, item["snippet"]["title"],
                item["contentDetails"]["relatedPlaylists"]["uploads"]))
            conn.commit()
            row = conn.execute("SELECT * FROM channels WHERE channel_id=?", (item["id"],)).fetchone()
        out.append(row)
    return out


def suggest_channel_ids(cfg, yt, limit=20):
    """Với kênh chỉ có name: search.list (100 đơn vị/kênh) + channels.list (1 đơn vị) để gợi ý channel_id.
    Trả về [(mục cấu hình, [channelId...], {channelId: thông tin})]. Người dùng PHẢI kiểm tra lại bằng mắt."""
    todo = [c for c in cfg.get("channels") or []
            if c.get("name") and not (c.get("channel_id") or c.get("handle") or c.get("id"))][:limit]
    out = []
    for ch in todo:
        d = yt.search_channels(ch["name"])
        ids = [(it.get("id") or {}).get("channelId") or it["snippet"]["channelId"] for it in d.get("items", [])]
        info = {i["id"]: i for i in yt.channels_info(ids)} if ids else {}
        out.append((ch, ids, info))
    return out


def classify_type(title):
    """Heuristic theo tiêu đề; chỉ để lọc/thống kê, không dùng làm nhãn."""
    t = unaccent(title)
    if re.search(r"\bso sanh\b|\bvs\b", t):
        return "compare"
    if re.search(r"unbox|mo hop|tren tay", t):
        return "unbox"
    if re.search(r"sau \d+|thoi gian dung|dung lau|trai nghiem", t):
        return "long_term"
    return "review"


def refresh_videos(yt, conn, ids, cfg=None):
    """Chụp số liệu video (view/like/comment) kèm fetched_at; mỗi lần chụp là 1 dòng trong
    data/raw/videos-YYYYMMDD.jsonl. 1 đơn vị quota cho mỗi 50 video."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetched = iso(now())
    path = config.raw_path(cfg, "videos")
    for i in range(0, len(ids), 50):
        lines = []
        for v in yt.videos(ids[i:i + 50]):
            st, sn = v.get("statistics", {}), v["snippet"]
            row = conn.execute("SELECT * FROM videos WHERE video_id=?", (v["id"],)).fetchone()
            if not row:
                continue
            rec = {"video_id": v["id"], "channel_id": row["channel_id"], "channel_title": sn.get("channelTitle"),
                   "title": row["title"], "published_at": row["published_at"], "model": row["model"],
                   "video_type": classify_type(row["title"]), "source": "youtube",
                   "view_count": int(st.get("viewCount", 0)), "like_count": int(st.get("likeCount", 0)),
                   "comment_count": int(st["commentCount"]) if "commentCount" in st else None,
                   "fetched_at": fetched, "schema_version": SCHEMA_VERSION}
            conn.execute("UPDATE videos SET channel_title=?, video_type=?, view_count=?, like_count=?, "
                         "comment_count=?, fetched_at=? WHERE video_id=?",
                         (rec["channel_title"], rec["video_type"], rec["view_count"], rec["like_count"],
                          rec["comment_count"], fetched, v["id"]))
            if rec["comment_count"] is None and row["status"] == "pending":   # tắt bình luận
                conn.execute("UPDATE videos SET status='disabled' WHERE video_id=?", (v["id"],))
            lines.append(rec)
        with open(path, "a", encoding="utf-8") as f:
            for r in lines:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        conn.commit()


def run_discover(cfg, yt, conn):
    earliest, latest = bounds(cfg)
    new_ids = []
    for ch in resolve_channels(cfg, yt, conn):
        try:
            for it in yt.uploads(ch["uploads_playlist"]):
                pub = parse(it["contentDetails"].get("videoPublishedAt") or it["snippet"]["publishedAt"])
                if pub < earliest:
                    break  # uploads xếp mới -> cũ nên dừng được
                if pub > latest:
                    continue
                model = classify(cfg, it["snippet"]["title"], pub)
                if not model:
                    continue
                vid = it["contentDetails"]["videoId"]
                cur = conn.execute(
                    "INSERT OR IGNORE INTO videos(video_id,channel_id,title,published_at,model) VALUES(?,?,?,?,?)",
                    (vid, ch["channel_id"], it["snippet"]["title"], iso(pub), model))
                if cur.rowcount:
                    new_ids.append(vid)
                else:   # video đã biết: nếu nhãn mới khác nhãn cũ
                    old = conn.execute("SELECT model, status FROM videos WHERE video_id=?", (vid,)).fetchone()
                    if old and old["model"] != model:
                        if old["status"] == "pending":   # chưa cào gì -> cập nhật nhãn an toàn
                            conn.execute("UPDATE videos SET model=? WHERE video_id=?", (model, vid))
                        else:
                            log.info("Video %s đã cào với nhãn '%s', nay khớp '%s': giữ nhãn cũ", vid, old["model"], model)
                conn.commit()   # không giữ transaction mở trong lúc chờ trang uploads kế tiếp
            conn.commit()
        except QuotaExceeded as e:
            log.warning("Dừng discover: %s", e)
            break
        except YouTubeError as e:
            conn.commit()   # giữ lại các video đã tìm được của kênh này
            log.warning("Kênh %s lỗi, bỏ qua, sẽ thử lại ở lần sau: %s", ch["title"], e)
            continue
    try:
        refresh_videos(yt, conn, new_ids, cfg)
    except (QuotaExceeded, YouTubeError) as e:
        log.warning("Chưa lấy được thống kê video: %s", e)
    log.info("Discover xong: %d video mới", len(new_ids))
    return len(new_ids)


def find_channels(cfg, yt, queries, calls=3):
    """Tìm kênh ứng viên bằng search.list (100 đơn vị/lần, giới hạn số lần). Chỉ chạy tay."""
    from collections import Counter
    start, end = bounds(cfg)
    cnt, ids = Counter(), {}
    for q in queries[:calls]:
        d = yt.search_videos(q=q, regionCode="VN", relevanceLanguage="vi",
                             publishedAfter=iso(start), publishedBefore=iso(end))
        for it in d.get("items", []):
            sn = it["snippet"]
            cnt[sn["channelTitle"]] += 1
            ids[sn["channelTitle"]] = sn["channelId"]
    return [(t, ids[t], n) for t, n in cnt.most_common()]

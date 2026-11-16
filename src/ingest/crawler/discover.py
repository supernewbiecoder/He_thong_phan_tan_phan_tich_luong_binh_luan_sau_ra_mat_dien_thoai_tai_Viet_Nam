"""Tìm video review/unbox/so sánh từ danh sách kênh. Tiết kiệm hạn mức: KHÔNG dùng search.list,
đi qua playlist 'uploads' của kênh (1 đơn vị / 50 video) rồi lọc theo tiêu đề + ngày đăng.

Quét TĂNG DẦN: mọi video đã đọc được lưu vào bảng `uploads`, tiến độ từng kênh lưu ở `channel_scan`.
Lần sau chỉ đọc video mới đăng + phần quá khứ chưa quét; phân loại theo config chạy trên cache (0 quota)."""
import json
import logging
import re
from . import config
from .quota import QuotaExceeded
from .schema import SCHEMA_VERSION
from .youtube import ApiError, YouTubeError
from .models import bounds, classify, specs
from .timeutil import iso, now, parse, unaccent

log = logging.getLogger("discover")


def my_channel_ids(cfg, conn):
    """channel_id (UC...) các kênh máy này phụ trách (owner == CRAWLER_WORKER), kể cả kênh khai báo bằng @handle."""
    me, default = cfg.get("worker", "p1"), (cfg.get("workers") or {}).get("default_owner", "p1")
    out = set()
    for ch in cfg.get("channels") or []:
        if not ch.get("enabled", True) or str(ch.get("owner") or default) != me:
            continue
        key = ch.get("channel_id") or ch.get("handle") or ch.get("id")
        if not key:
            continue
        row = conn.execute("SELECT channel_id FROM channels WHERE handle=? OR channel_id=?", (key, key)).fetchone()
        out.add(row[0] if row else key)
    return out


def resolve_channels(cfg, yt, conn):
    """Đọc mục channels: channel_id (UC... hoặc @handle), name, enabled, tags."""
    out = []
    me, default = cfg.get("worker", "p1"), (cfg.get("workers") or {}).get("default_owner", "p1")
    for ch in cfg.get("channels") or []:
        if not ch.get("enabled", True):
            continue
        if str(ch.get("owner") or default) != me:   # kênh của người khác
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


def _left(yt):
    """Số đơn vị còn lại trong ngân sách của lần chạy này."""
    led = yt.ledger
    return float("inf") if led.run_limit is None else led.run_limit - led.run_used


def _item_pub(it):
    return parse(it["contentDetails"].get("videoPublishedAt") or it["snippet"]["publishedAt"])


def _cache_page(conn, channel_id, items):
    """Lưu mọi video của trang vào bảng uploads; trả về danh sách ngày đăng (để dời con trỏ quét)."""
    pubs = []
    for it in items:
        pub = _item_pub(it)
        pubs.append(pub)
        if not it["contentDetails"].get("videoPublishedAt"):
            continue   # video riêng tư/đã xóa: không có ngày đăng thật, không lưu
        conn.execute("INSERT OR REPLACE INTO uploads VALUES(?,?,?,?)",
                     (it["contentDetails"]["videoId"], channel_id, it["snippet"]["title"], iso(pub)))
    return pubs


def _scan_state(conn, cid):
    conn.execute("INSERT OR IGNORE INTO channel_scan(channel_id) VALUES(?)", (cid,))
    conn.commit()   # nhả khóa ghi TRƯỚC khi gọi mạng (sổ quota ghi bằng kết nối riêng), kể cả khi không chèn gì
    return conn.execute("SELECT * FROM channel_scan WHERE channel_id=?", (cid,)).fetchone()


def _needs_backfill(st, earliest):
    return not st["tail_done"] and (st["tail_pub"] is None or parse(st["tail_pub"]) >= earliest)


def _scan_head(conn, yt, ch, reserve):
    """Kênh đã quét trước đây: chỉ đọc từ đầu playlist tới khi gặp lại video mới nhất đã biết
    (thường 1 trang = 1 đơn vị). Chưa tới được mốc cũ (hết ngân sách) thì chưa dời head_pub, lần sau làm lại."""
    cid = ch["channel_id"]
    st = _scan_state(conn, cid)
    if not st["head_pub"]:
        return
    head = parse(st["head_pub"])
    newest, token = head, None
    while _left(yt) > reserve:
        items, token = yt.uploads_page(ch["uploads_playlist"], token)
        pubs = _cache_page(conn, cid, items)
        if pubs:
            newest = max(newest, max(pubs))
        conn.execute("UPDATE channel_scan SET pages=pages+1 WHERE channel_id=?", (cid,))
        if not token or any(p <= head for p in pubs):
            conn.execute("UPDATE channel_scan SET head_pub=?, last_scan=? WHERE channel_id=?",
                         (iso(newest), iso(now()), cid))
            conn.commit()
            return
        conn.commit()


def _backfill_page(conn, yt, ch):
    """Quét thêm MỘT trang về quá khứ, lưu con trỏ ngay sau mỗi trang (dừng giữa chừng không mất tiến độ)."""
    cid = ch["channel_id"]
    st = _scan_state(conn, cid)
    try:
        items, nxt = yt.uploads_page(ch["uploads_playlist"], st["tail_token"])
    except ApiError as e:
        if not st["tail_token"]:
            raise
        log.warning("Kênh %s: page token cũ không dùng được (%s), quét lại từ đầu playlist", ch["title"], e)
        conn.execute("UPDATE channel_scan SET tail_token=NULL WHERE channel_id=?", (cid,))
        conn.commit()
        return
    pubs = _cache_page(conn, cid, items)
    tail = min([parse(st["tail_pub"])] + pubs if st["tail_pub"] else pubs, default=None)
    head = st["head_pub"] or (iso(max(pubs)) if pubs else None)
    conn.execute("UPDATE channel_scan SET tail_token=?, tail_pub=?, tail_done=?, head_pub=?, pages=pages+1, "
                 "last_scan=? WHERE channel_id=?",
                 (nxt, iso(tail) if tail else st["tail_pub"], 0 if nxt else 1, head, iso(now()), cid))
    conn.commit()


def scan_channels(cfg, yt, conn, channels, earliest):
    """Bước 1 (tốn quota): cập nhật bộ nhớ đệm uploads.
    a) Kênh đã quét: chỉ đọc phần video mới đăng.
    b) Kênh chưa quét xong (kênh mới thêm, hoặc config thêm mẫu cũ hơn): quét tiếp về quá khứ theo
       vòng tròn, mỗi kênh MỘT trang mỗi lượt, để ngân sách chia đều cho mọi kênh thay vì kênh đầu
       danh sách ăn hết như trước."""
    reserve = (cfg.get("discover") or {}).get("reserve_units", 20)   # chừa quota cho bước lấy thống kê video
    for ch in channels:
        try:
            _scan_head(conn, yt, ch, reserve)
        except YouTubeError as e:
            conn.commit()
            log.warning("Kênh %s lỗi khi quét video mới, bỏ qua lần này: %s", ch["title"], e)
    todo = [ch for ch in channels if _needs_backfill(_scan_state(conn, ch["channel_id"]), earliest)]
    conn.commit()
    if todo:
        log.info("Quét lùi về quá khứ cho %d kênh (mốc sớm nhất cần: %s)", len(todo), iso(earliest))
    while todo and _left(yt) > reserve:
        nxt = []
        for ch in todo:
            if _left(yt) <= reserve:
                break   # hết ngân sách giữa vòng; con trỏ đã lưu, lần chạy sau làm tiếp
            try:
                _backfill_page(conn, yt, ch)
            except YouTubeError as e:
                conn.commit()
                log.warning("Kênh %s lỗi, bỏ qua, sẽ thử lại ở lần sau: %s", ch["title"], e)
                continue
            if _needs_backfill(_scan_state(conn, ch["channel_id"]), earliest):
                nxt.append(ch)
        todo = nxt
    conn.commit()
    left = [ch["title"] for ch in channels if _needs_backfill(_scan_state(conn, ch["channel_id"]), earliest)]
    if left:
        log.warning("Còn %d kênh chưa quét đủ về %s (hết ngân sách lần chạy). Chạy discover thêm lần nữa, "
                    "hoặc `discover --budget 3000`: %s", len(left), iso(earliest)[:10], ", ".join(left))
    return left


def classify_cached(cfg, conn, channels):
    """Bước 2 (KHÔNG tốn quota): phân loại lại toàn bộ uploads đã lưu theo config hiện tại.
    Trả về danh sách video mới thêm vào bảng videos."""
    earliest, latest = bounds(cfg)
    sp = specs(cfg)
    ids = [ch["channel_id"] for ch in channels]
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = conn.execute(f"SELECT * FROM uploads WHERE channel_id IN ({marks}) AND published_at BETWEEN ? AND ? "
                        "ORDER BY published_at DESC", (*ids, iso(earliest), iso(latest))).fetchall()
    new_ids, relabeled, revived = [], 0, 0
    for u in rows:
        pub = parse(u["published_at"])
        model = classify(cfg, u["title"], pub, sp)
        if not model:
            continue
        vid = u["video_id"]
        cur = conn.execute(
            "INSERT OR IGNORE INTO videos(video_id,channel_id,title,published_at,model) VALUES(?,?,?,?,?)",
            (vid, u["channel_id"], u["title"], iso(pub), model))
        if cur.rowcount:
            new_ids.append(vid)
            continue
        old = conn.execute("SELECT model, status FROM videos WHERE video_id=?", (vid,)).fetchone()
        if old["status"] == "excluded":   # trước đây không khớp mẫu nào, nay khớp -> cào
            conn.execute("UPDATE videos SET model=?, status='pending', page_token=NULL, watermark=NULL, "
                         "pending_max=NULL WHERE video_id=?", (model, vid))
            revived += 1
        elif old["model"] != model:
            if old["status"] == "pending":   # chưa cào gì -> cập nhật nhãn an toàn
                conn.execute("UPDATE videos SET model=? WHERE video_id=?", (model, vid))
                relabeled += 1
            else:
                log.info("Video %s đã cào với nhãn '%s', nay khớp '%s': giữ nhãn cũ "
                         "(chạy `repair-missing` để đổi nhãn dữ liệu đã cào)", vid, old["model"], model)
    conn.commit()
    log.info("Phân loại %d video trong cache (%s -> %s): %d mới, %d đổi nhãn, %d mở lại",
             len(rows), iso(earliest)[:10], iso(latest)[:10], len(new_ids), relabeled, revived)
    return new_ids


def run_discover(cfg, yt, conn):
    earliest, _ = bounds(cfg)
    channels = resolve_channels(cfg, yt, conn)
    try:
        scan_channels(cfg, yt, conn, channels, earliest)
    except QuotaExceeded as e:
        conn.commit()
        log.warning("Dừng quét kênh: %s", e)
    new_ids = classify_cached(cfg, conn, channels)
    # lấy thống kê cho MỌI video chưa có (kể cả video mới của lần trước bị thiếu do hết quota)
    need = [r[0] for r in conn.execute(
        "SELECT video_id FROM videos WHERE fetched_at IS NULL AND status NOT IN ('excluded')")]
    try:
        refresh_videos(yt, conn, need, cfg)
    except (QuotaExceeded, YouTubeError) as e:
        log.warning("Chưa lấy được thống kê video: %s", e)
    log.info("Discover xong: %d video mới", len(new_ids))
    return len(new_ids)


def reset_scan(conn, channel_ids=None):
    """Xóa con trỏ quét để quét lại kênh từ đầu (giữ cache uploads)."""
    if channel_ids:
        conn.executemany("DELETE FROM channel_scan WHERE channel_id=?", [(c,) for c in channel_ids])
    else:
        conn.execute("DELETE FROM channel_scan")
    conn.commit()


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

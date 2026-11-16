"""Thông tin tài khoản người bình luận (schema v3, trường author_*).

Dữ liệu cũ chỉ có author_hash (băm 1 chiều) nên phải TRA NGƯỢC theo comment_id:
  1) backfill-authors : comments.list?id=<50 id>  -> kênh + tên người viết       (1 đơn vị / 50 comment)
  2) enrich-authors   : channels.list?id=<50 kênh> -> ngày tạo, số video, sub    (1 đơn vị / 50 kênh)
  3) apply-authors    : ghi 6 trường author_* vào data/raw/comments*.jsonl, nâng schema_version lên 3
Bước 1 và 2 chia được cho nhiều người/khóa API bằng --part i/n (chia theo băm id, không trùng nhau);
mỗi người `authors-export`, người tổng hợp `authors-import` rồi `apply-authors`.
Comment cào MỚI (crawl) được gắn thông tin ngay lúc cào qua attach(), không cần backfill.
Channel ID và tên thật chỉ nằm trong state.db; dataset chung chỉ có author_hash + các trường author_*."""
import json
import logging
import shutil
import zlib
from datetime import datetime, timedelta
from . import config
from .crawl import author_hash
from .quota import QuotaExceeded
from .schema import AUTHOR_FIELDS, COMMENT_FIELDS, SCHEMA_VERSION
from .timeutil import iso, now, parse
from .youtube import YouTubeError

log = logging.getLogger("authors")


def in_part(key, part):
    """part = (i, n): giữ key nếu crc32(key) % n == i-1. Ổn định giữa các máy, chia đều."""
    if not part:
        return True
    i, n = part
    return zlib.crc32(key.encode()) % n == i - 1


def parse_part(s):
    if not s:
        return None
    i, n = (int(x) for x in s.split("/"))
    if not 1 <= i <= n:
        raise SystemExit("--part phải dạng i/n với 1 <= i <= n, vd 1/2")
    return i, n


def _iter_comments(paths):
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


# ------------------------------------------------------------------ 1) comment -> kênh người viết
def backfill(cfg, yt, conn, part=None, ids_from=None):
    paths = [ids_from] if ids_from else config.raw_files("comments")
    done = {r[0] for r in conn.execute("SELECT comment_id FROM comment_authors")}
    todo = [r["comment_id"] for r in _iter_comments(paths)
            if r.get("source", "youtube") == "youtube" and r["comment_id"] not in done and in_part(r["comment_id"], part)]
    todo = list(dict.fromkeys(todo))
    log.info("Cần tra %d comment (phần %s), ước tính %d đơn vị", len(todo), part or "tất cả", -(-len(todo) // 50))
    got = 0
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        try:
            items = yt.comments_by_ids(batch)
        except QuotaExceeded as e:
            log.warning("Dừng: %s. Đã tra %d/%d, chạy lại lệnh để làm tiếp.", e, i, len(todo))
            break
        except YouTubeError as e:
            log.warning("Lô %d lỗi, bỏ qua lần này: %s", i // 50, e)
            continue
        ts, found = iso(now()), set()
        for it in items:
            sn = it["snippet"]
            found.add(it["id"])
            conn.execute("INSERT OR REPLACE INTO comment_authors VALUES(?,?,?,'ok',?)",
                         (it["id"], (sn.get("authorChannelId") or {}).get("value"), sn.get("authorDisplayName"), ts))
        conn.executemany("INSERT OR REPLACE INTO comment_authors VALUES(?,NULL,NULL,'missing',?)",
                         [(c, ts) for c in batch if c not in found])
        conn.commit()
        got += len(found)
        if (i // 50) % 200 == 0:
            log.info("  %d/%d comment, %d còn tồn tại", i + len(batch), len(todo), got)
    return got


# ------------------------------------------------------------------ 2) kênh -> ngày tạo, số video, sub
def _store_channels(conn, items, asked, ts):
    found = set()
    for it in items:
        sn, st = it.get("snippet", {}), it.get("statistics", {})
        found.add(it["id"])
        subs = None if st.get("hiddenSubscriberCount") else (int(st["subscriberCount"]) if "subscriberCount" in st else None)
        conn.execute("INSERT OR REPLACE INTO authors VALUES(?,?,?,?,?,'ok',?)",
                     (it["id"], sn.get("title"), iso(parse(sn["publishedAt"])) if sn.get("publishedAt") else None,
                      int(st["videoCount"]) if "videoCount" in st else None, subs, ts))
    conn.executemany("INSERT OR REPLACE INTO authors VALUES(?,NULL,NULL,NULL,NULL,'missing',?)",
                     [(c, ts) for c in asked if c not in found])


def enrich(cfg, yt, conn, part=None, refresh_days=None):
    q = """SELECT DISTINCT ca.author_channel_id FROM comment_authors ca LEFT JOIN authors a
           ON a.channel_id = ca.author_channel_id WHERE ca.author_channel_id IS NOT NULL AND a.channel_id IS NULL"""
    todo = [r[0] for r in conn.execute(q)]
    if refresh_days:   # làm mới thông tin cũ hơn N ngày (chính sách 30 ngày)
        cutoff = iso(now() - timedelta(days=refresh_days))
        todo += [r[0] for r in conn.execute("SELECT channel_id FROM authors WHERE fetched_at < ?", (cutoff,))]
    todo = [c for c in dict.fromkeys(todo) if in_part(c, part)]
    log.info("Cần tra %d kênh (phần %s), ước tính %d đơn vị", len(todo), part or "tất cả", -(-len(todo) // 50))
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        try:
            items = yt.channels_full(batch)
        except QuotaExceeded as e:
            log.warning("Dừng: %s. Đã tra %d/%d kênh, chạy lại để làm tiếp.", e, i, len(todo))
            break
        except YouTubeError as e:
            log.warning("Lô kênh %d lỗi: %s", i // 50, e)
            continue
        _store_channels(conn, items, batch, iso(now()))
        conn.commit()
    return len(todo)


# ------------------------------------------------------------------ lúc crawl: gắn ngay vào record mới
def attach(cfg, yt, conn, recs, video_channel_id):
    """recs có khóa tạm _author_channel_id/_author_name (make_record). Tra các kênh chưa biết (1 đơn vị/50),
    điền author_*, xóa khóa tạm. Hết quota thì vẫn ghi comment, author_* để None (enrich + apply bù sau)."""
    if not recs:
        return
    ts = iso(now())
    conn.executemany("INSERT OR REPLACE INTO comment_authors VALUES(?,?,?,'ok',?)",
                     [(r["comment_id"], r["_author_channel_id"], r["_author_name"], ts) for r in recs])
    conn.commit()   # nhả khóa ghi TRƯỚC khi gọi mạng (sổ quota ghi bằng kết nối riêng)
    ids = {r["_author_channel_id"] for r in recs if r["_author_channel_id"]}
    known = {row[0] for row in conn.execute(
        f"SELECT channel_id FROM authors WHERE channel_id IN ({','.join('?' * len(ids))})", tuple(ids))} if ids else set()
    unknown = sorted(ids - known)
    try:
        for i in range(0, len(unknown), 50):
            items = yt.channels_full(unknown[i:i + 50])
            _store_channels(conn, items, unknown[i:i + 50], ts)
            conn.commit()
    except (QuotaExceeded, YouTubeError) as e:
        log.info("Chưa lấy được thông tin %d kênh người bình luận (%s), sẽ bù bằng enrich-authors", len(unknown), e)
    info = _author_rows(conn, ids)
    creator = author_hash(video_channel_id, cfg["salt"]) if video_channel_id else None
    for r in recs:
        acid, name = r.pop("_author_channel_id"), r.pop("_author_name")
        r.update(_fields(info.get(acid), name, r["author_hash"] == creator))


def _author_rows(conn, ids):
    ids = list(ids)
    out = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for row in conn.execute(f"SELECT * FROM authors WHERE channel_id IN ({','.join('?' * len(chunk))})", chunk):
            out[row[0]] = row
    return out


def _fields(a, name, is_creator):
    ok = a is not None and a[5] == "ok"
    return {"author_name": name,
            "author_channel_created_at": a[2] if ok else None,
            "author_video_count": a[3] if ok else None,
            "author_subscriber_count": a[4] if ok else None,
            "author_is_creator": bool(is_creator),
            "author_fetched_at": a[6] if ok else None}


# ------------------------------------------------------------------ chia việc: xuất / nhập
def export(conn, path):
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for row in conn.execute("SELECT * FROM comment_authors"):
            f.write(json.dumps({"kind": "comment", "row": list(row)}, ensure_ascii=False) + "\n")
            n += 1
        for row in conn.execute("SELECT * FROM authors"):
            f.write(json.dumps({"kind": "channel", "row": list(row)}, ensure_ascii=False) + "\n")
            n += 1
    return n


def import_(conn, paths):
    c = a = 0
    for p in paths:
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            if d["kind"] == "comment":
                conn.execute("INSERT OR REPLACE INTO comment_authors VALUES(?,?,?,?,?)", d["row"])
                c += 1
            else:
                conn.execute("INSERT OR REPLACE INTO authors VALUES(?,?,?,?,?,?,?)", d["row"])
                a += 1
    conn.commit()
    return c, a


# ------------------------------------------------------------------ 3) ghi vào comments*.jsonl
def apply(cfg, conn, dry_run=False):
    salt = cfg["salt"]
    ca = {r[0]: (r[1], r[2]) for r in conn.execute("SELECT comment_id, author_channel_id, author_name FROM comment_authors")}
    info = {r[0]: r for r in conn.execute("SELECT * FROM authors")}
    vch = {r[0]: r[1] for r in conn.execute("SELECT video_id, channel_id FROM videos")}
    for p in config.raw_files("videos"):   # video do người khác cào (không có trong state.db của máy này)
        for v in _iter_comments([p]):
            vch.setdefault(v["video_id"], v.get("channel_id"))
    creator = {v: author_hash(c, salt) for v, c in vch.items() if c}
    backup = config.RAW_DIR.parent / "raw_backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    stat = {"tổng": 0, "có tên": 0, "có ngày tạo kênh": 0, "comment đã bị xóa": 0, "kênh bị khóa": 0,
            "chưa tra": 0, "chủ kênh": 0, "hash lệch salt": 0}
    for path in config.raw_files("comments"):
        tmp = path.with_name(path.name + ".authors-tmp")
        with open(path, encoding="utf-8") as src, open(tmp, "w", encoding="utf-8", newline="\n") as dst:
            for line in src:
                try:
                    r = json.loads(line)
                except ValueError:
                    dst.write(line)
                    continue
                stat["tổng"] += 1
                is_creator = r["author_hash"] == creator.get(r["video_id"])
                if r["comment_id"] not in ca and (r.get("schema_version") or 2) >= 3:   # đã gắn lúc crawl
                    f = {k: r.get(k) for k in AUTHOR_FIELDS} | {"author_is_creator": is_creator}
                    stat["có tên"] += f["author_name"] is not None
                    stat["có ngày tạo kênh"] += f["author_channel_created_at"] is not None
                    stat["chủ kênh"] += is_creator
                    r.update(f)
                    dst.write(json.dumps({k: r.get(k) for k in COMMENT_FIELDS}, ensure_ascii=False) + "\n")
                    continue
                acid, name = ca.get(r["comment_id"], (None, None))
                if r["comment_id"] not in ca:
                    stat["chưa tra"] += 1
                elif acid is None:
                    stat["comment đã bị xóa"] += 1
                elif author_hash(acid, salt) != r["author_hash"]:
                    stat["hash lệch salt"] += 1   # AUTHOR_SALT khác lúc cào -> không tin được ánh xạ
                    acid, name = None, None
                a = info.get(acid) if acid else None
                if a is not None and a[5] != "ok":
                    stat["kênh bị khóa"] += 1
                f = _fields(a, name, is_creator)
                stat["có tên"] += f["author_name"] is not None
                stat["có ngày tạo kênh"] += f["author_channel_created_at"] is not None
                stat["chủ kênh"] += f["author_is_creator"]
                out = {k: r.get(k) for k in COMMENT_FIELDS if k not in AUTHOR_FIELDS} | f
                out["schema_version"] = SCHEMA_VERSION
                dst.write(json.dumps({k: out[k] for k in COMMENT_FIELDS}, ensure_ascii=False) + "\n")
        if dry_run:
            tmp.unlink()
            continue
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup / path.name)
        tmp.replace(path)
    t = stat["tổng"] or 1
    for k, v in stat.items():
        print(f"  {k:20} {v:8}" + (f"  ({v / t:.1%})" if k != "tổng" else ""))
    if stat["hash lệch salt"]:
        print("CẢNH BÁO: có comment mà channel ID tra được không khớp author_hash -> AUTHOR_SALT trong .env khác "
              "salt lúc cào. Mọi người phải dùng CÙNG một AUTHOR_SALT.")
    print("(chạy thử, chưa ghi gì)" if dry_run else f"Đã ghi. Bản sao lưu: {backup}")
    return stat

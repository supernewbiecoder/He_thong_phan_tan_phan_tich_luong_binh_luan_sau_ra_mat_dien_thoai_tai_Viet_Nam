"""Sửa dữ liệu cũ bị "mồ côi": comment_id đã nằm trong bảng `seen` (và video đã ở trạng thái done)
nhưng comment KHÔNG có trong data/raw/comments*.jsonl (vì từng cào theo schema/nhãn cũ rồi chuyển ra backup).
Khi đó crawler tưởng đã cào rồi nên không bao giờ cào lại.

Các bước (mặc định chỉ báo cáo, thêm --apply để ghi):
  1. Phân loại lại mọi video trong state.db theo config hiện tại.
     - khớp nhãn khác      -> đổi nhãn trong state.db + trong comments/videos JSONL
     - không khớp mẫu nào  -> status='excluded' (không cào, không chụp số liệu), bỏ dòng khỏi videos JSONL.
       Video đã có comment trong archive thì GIỮ NGUYÊN (chỉ cảnh báo), không tự xóa dữ liệu thật.
  2. Xóa khỏi `seen` các comment_id không có trong archive -> crawler được phép cào lại chúng.
  3. Video hợp lệ nhưng archive không có comment nào -> đặt lại status='pending', xóa con trỏ
     (page_token/watermark) để lần `crawl` tới cào lại từ đầu cửa sổ, theo schema mới.
Sao lưu state.db + các file JSONL bị sửa vào data/raw_backup/<thời gian>/ trước khi ghi.
Chạy khi KHÔNG có crawler nào đang chạy (lệnh tự xin khóa)."""
import json
import shutil
import sqlite3
from collections import Counter
from datetime import datetime
from . import config
from .models import classify, specs
from .store import connect
from .timeutil import parse

CRAWLED = ("done", "tracking", "backfilling")


def _archive(kind):
    """{comment_id hoặc video_id: ...} của các file hiện có."""
    files = config.raw_files(kind)
    per_video, ids = Counter(), set()
    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            per_video[r.get("video_id")] += 1
            if kind == "comments":
                ids.add(r.get("comment_id"))
    return files, per_video, ids


def plan(cfg, conn):
    sp = specs(cfg)
    _, cm_per_video, cm_ids = _archive("comments")
    relabel, exclude, keep_warn, reset = {}, [], [], []
    for v in conn.execute("SELECT * FROM videos").fetchall():
        if v["status"] == "excluded":
            continue
        new = classify(cfg, v["title"] or "", parse(v["published_at"]), sp)
        n = cm_per_video.get(v["video_id"], 0)
        if not new:
            (keep_warn if n else exclude).append(v)
            continue
        if new != v["model"]:
            relabel[v["video_id"]] = (v["model"], new)
        if n == 0 and v["status"] in CRAWLED:
            reset.append(v)
    seen = {r[0] for r in conn.execute("SELECT comment_id FROM seen")}
    orphans = seen - cm_ids
    unseen = cm_ids - seen   # comment có trong archive nhưng thiếu trong seen -> thêm lại để không cào trùng
    return relabel, exclude, keep_warn, reset, orphans, unseen


def _rewrite(path, relabel, drop_ids, tmp_paths):
    """Ghi file tạm với nhãn mới / bỏ dòng của video bị loại. Trả về (số dòng đổi, số dòng bỏ)."""
    changed = dropped = 0
    tmp = path.with_name(path.name + ".repair-tmp")
    with open(path, encoding="utf-8") as src, open(tmp, "w", encoding="utf-8", newline="\n") as dst:
        for line in src:
            try:
                r = json.loads(line)
            except ValueError:
                dst.write(line)
                continue
            vid = r.get("video_id")
            if vid in drop_ids:
                dropped += 1
                continue
            if vid in relabel and r.get("model") != relabel[vid][1]:
                r["model"] = relabel[vid][1]
                changed += 1
                line = json.dumps(r, ensure_ascii=False) + "\n"
            dst.write(line)
    if changed or dropped:
        tmp_paths[path] = tmp
    else:
        tmp.unlink()
    return changed, dropped


def repair(cfg, apply=False):
    conn = connect(config.DB_PATH)
    try:
        relabel, exclude, keep_warn, reset, orphans, unseen = plan(cfg, conn)
        print(f"Video đổi nhãn theo config hiện tại: {len(relabel)}")
        for (old, new), n in Counter(relabel.values()).most_common():
            print(f"  {old} -> {new}: {n} video")
        print(f"Video không còn khớp mẫu nào -> excluded: {len(exclude)}  "
              f"(nhãn cũ: {dict(Counter(v['model'] for v in exclude))})")
        if keep_warn:
            print(f"CẢNH BÁO: {len(keep_warn)} video không khớp mẫu nào nhưng ĐÃ có comment trong archive -> giữ nguyên:")
            for v in keep_warn[:10]:
                print(f"  {v['video_id']} [{v['model']}] {v['title'][:70]}")
        print(f"Video sẽ cào lại từ đầu (archive không có comment nào): {len(reset)}  "
              f"(~{sum(v['comment_count'] or 0 for v in reset)} comment theo thống kê YouTube)")
        for m, n in Counter(relabel.get(v["video_id"], (0, v["model"]))[1] for v in reset).most_common():
            print(f"  {m}: {n} video")
        print(f"comment_id trong `seen` nhưng không có trong archive (sẽ xóa khỏi seen): {len(orphans)}")
        if unseen:
            print(f"comment_id có trong archive nhưng thiếu trong `seen` (sẽ thêm vào): {len(unseen)}")

        drop_ids = {v["video_id"] for v in exclude}
        tmp_paths, stats = {}, []
        for kind in ("comments", "videos"):
            for path in config.raw_files(kind):
                c, d = _rewrite(path, relabel, drop_ids, tmp_paths)
                stats.append((path.name, c, d))
        for name, c, d in stats:
            print(f"{name}: {c} dòng đổi nhãn, {d} dòng bỏ (video excluded)")

        if not apply:
            for t in tmp_paths.values():
                t.unlink()
            print("\nDRY-RUN: chưa ghi gì. Kiểm tra báo cáo rồi chạy lại với --apply.")
            return
        if not (relabel or exclude or reset or orphans or unseen or tmp_paths):
            print("\nKhông có gì cần sửa.")
            return

        backup = config.RAW_DIR.parent / "raw_backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
        backup.mkdir(parents=True, exist_ok=True)
        dst = sqlite3.connect(backup / "state.db")
        conn.backup(dst)   # an toàn với WAL, khác với copy file
        dst.close()
        for path in tmp_paths:
            shutil.copy2(path, backup / path.name)

        replaced = []
        try:
            conn.execute("BEGIN IMMEDIATE")
            for vid, (_, new) in relabel.items():
                conn.execute("UPDATE videos SET model=? WHERE video_id=?", (new, vid))
            conn.executemany("UPDATE videos SET status='excluded' WHERE video_id=?", [(v,) for v in drop_ids])
            conn.executemany("UPDATE videos SET status='pending', page_token=NULL, watermark=NULL, pending_max=NULL, "
                             "last_crawled=NULL WHERE video_id=?", [(v["video_id"],) for v in reset])
            conn.executemany("DELETE FROM seen WHERE comment_id=?", [(c,) for c in orphans])
            conn.executemany("INSERT OR IGNORE INTO seen VALUES(?)", [(c,) for c in unseen])
            for path, tmp in tmp_paths.items():
                tmp.replace(path)
                replaced.append(path)
            conn.commit()
        except BaseException:
            conn.rollback()
            for path in replaced:
                shutil.copy2(backup / path.name, path)
            raise
        finally:
            for t in tmp_paths.values():
                if t.exists():
                    t.unlink()
        print(f"\nĐã sửa. Bản sao lưu: {backup}")
        print("Tiếp theo: `python -m crawler.main crawl` (hoặc để `run` tự cào) để cào lại các video đã đặt pending.")
    finally:
        conn.close()

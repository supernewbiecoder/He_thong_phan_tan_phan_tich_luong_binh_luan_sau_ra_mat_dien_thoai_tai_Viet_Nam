"""Đổi nhãn `model` của dữ liệu đã cào (ví dụ main -> ip15prm) trong data/raw/*.jsonl và state.db.
CHỈ đổi các file được chỉ định (--files), và trong state.db chỉ đổi các video xuất hiện trong những file đó,
vì các lần cào với cấu hình khác nhau có thể cùng dùng nhãn cũ (main/rival). Chạy khi KHÔNG có crawler nào đang chạy.
File gốc được sao lưu vào data/raw_backup/<thời gian>/."""
import json
import shutil
from datetime import datetime
from . import config
from .store import connect


def _read(path):
    for line in open(path, encoding="utf-8"):
        try:
            yield line, json.loads(line)
        except ValueError:
            yield line, None


def relabel(mapping, files, dry_run=False):
    paths = []
    for name in files:
        p = config.RAW_DIR / name
        if not p.exists():
            raise SystemExit(f"Không thấy file {p}")
        paths.append(p)
    video_ids = {r["video_id"] for p in paths for _, r in _read(p) if r and r.get("video_id")}
    conn = connect(config.DB_PATH)
    total = 0
    for old, new in mapping.items():
        ids = [v for (v,) in conn.execute("SELECT video_id FROM videos WHERE model=?", (old,)) if v in video_ids]
        total += len(ids)
        print(f"state.db: {len(ids)} video (trong các file đã chọn) có model='{old}' -> '{new}'")
        if not dry_run:
            conn.executemany("UPDATE videos SET model=? WHERE video_id=?", [(new, v) for v in ids])
    conn.commit()
    backup = config.RAW_DIR.parent / "raw_backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    for p in paths:
        out, changed = [], 0
        for line, r in _read(p):
            if r is not None and r.get("model") in mapping:
                r["model"] = mapping[r["model"]]
                changed += 1
                out.append(json.dumps(r, ensure_ascii=False))
            else:
                out.append(line.rstrip("\r\n"))
        print(f"{p.name}: {changed}/{len(out)} dòng đổi nhãn")
        if changed and not dry_run:
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, backup / p.name)
            tmp = p.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(out) + "\n")
            tmp.replace(p)
    print("(chạy thử, chưa ghi gì)" if dry_run else f"Xong. Bản sao lưu: {backup}")

"""Loại comment trùng (cùng comment_id) khỏi các file comments, giữ bản đầu tiên.
--merge: gộp tất cả vào MỘT file comments.jsonl. File gốc luôn được sao lưu vào data/raw_backup/<thời gian>/.
Chạy khi KHÔNG có crawler nào đang chạy."""
import json
import shutil
from datetime import datetime
from . import config


def dedupe(merge=False, dry_run=False):
    files = config.raw_files("comments")
    if not files:
        print("Chưa có file comments nào trong data/raw.")
        return
    seen, plan, total_in, total_out = set(), [], 0, 0
    for f in files:
        keep, bad = [], 0
        for line in open(f, encoding="utf-8"):
            line = line.rstrip("\r\n")
            try:
                cid = json.loads(line)["comment_id"]
            except (ValueError, KeyError):
                bad += 1
                keep.append(line)   # giữ nguyên dòng lạ, không tự ý xóa
                continue
            total_in += 1
            if cid not in seen:
                seen.add(cid)
                keep.append(line)
        total_out += len(keep) - bad
        plan.append((f, keep))
        print(f"{f.name}: {len(keep)} dòng giữ lại" + (f" ({bad} dòng không đọc được, giữ nguyên)" if bad else ""))
    print(f"Tổng: {total_in} dòng -> {total_out} comment duy nhất (bỏ {total_in - total_out} dòng trùng).")
    if dry_run:
        print("(chạy thử, chưa ghi gì)")
        return
    backup = config.RAW_DIR.parent / "raw_backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup.mkdir(parents=True, exist_ok=True)
    for f, keep in plan:
        shutil.copy2(f, backup / f.name)
    if merge:
        target = config.RAW_DIR / "comments.jsonl"
        tmp = target.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as out:
            for _, keep in plan:
                out.writelines(k + "\n" for k in keep)
        for f, _ in plan:
            if f != target:
                f.unlink()
        tmp.replace(target)
        print(f"Đã gộp thành {target.name}. Bản sao lưu: {backup}")
    else:
        for f, keep in plan:
            tmp = f.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8", newline="\n") as out:
                out.writelines(k + "\n" for k in keep)
            tmp.replace(f)
        print(f"Xong. Bản sao lưu: {backup}")

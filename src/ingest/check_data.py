"""Kiểm tra chất lượng dữ liệu đã cào. Đặt file này ở thư mục gốc dự án (cạnh README.md), chạy:
    python check_data.py"""
import json
import random
from collections import Counter

from src import config
from src.config import raw_files
from src.schema import COMMENT_FIELDS, VIDEO_FIELDS
from src.models import window
from src.timeutil import parse


def read(kind):
    rows, bad = [], 0
    for f in raw_files(kind):
        for line in open(f, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                bad += 1
    return rows, bad


cfg = config.load()
cm, bad = read("comments")
print(f"== COMMENTS: {len(cm)} dòng, {len(raw_files('comments'))} file, {bad} dòng hỏng JSON")
ids = Counter(r["comment_id"] for r in cm)
print(f"  comment_id duy nhất: {len(ids)}  | dòng trùng: {len(cm) - len(ids)}  (trùng là bình thường, consumer sẽ upsert)")
print(f"  sai schema (thiếu/thừa trường): {sum(set(r) != set(COMMENT_FIELDS) for r in cm)}")
print(f"  text rỗng: {sum(not (r.get('text') or '').strip() for r in cm)}")

win = {m: window(cfg, m) for m in {r["model"] for r in cm}}
out = sum(1 for r in cm if not (win[r["model"]][0] <= parse(r["published_at"]) <= win[r["model"]][1]))
print(f"  ngoài cửa sổ thời gian: {out}")

u = {r["comment_id"]: r for r in cm}.values()
print("  theo model (đã khử trùng):", dict(Counter(r["model"] for r in u)))
print(f"  comment gốc: {sum(r['parent_id'] is None for r in u)} | reply: {sum(r['parent_id'] is not None for r in u)}")
pub = sorted(r["published_at"] for r in u)
if pub:
    print(f"  published_at từ {pub[0]} đến {pub[-1]}")
print(f"  số tác giả khác nhau: {len({r['author_hash'] for r in u})}")
print("  5 nội dung lặp nhiều nhất (gợi ý spam):")
for t, n in Counter(r["text"] for r in u).most_common(5):
    print(f"    {n:4}x  {t[:70]!r}")
print("  5 comment ngẫu nhiên:")
for r in random.sample(list(u), min(5, len(u))):
    print(f"    [{r['model']}] {r['text'][:90]!r}")

vd, bad = read("videos")
print(f"\n== VIDEOS: {len(vd)} dòng, {len({r['video_id'] for r in vd})} video duy nhất, {bad} dòng hỏng")
print(f"  sai schema: {sum(set(r) != set(VIDEO_FIELDS) for r in vd)}")
last = {r["video_id"]: r for r in sorted(vd, key=lambda x: x["fetched_at"])}.values()
print("  theo model:", dict(Counter(r["model"] for r in last)), "| theo loại:", dict(Counter(r["video_type"] for r in last)))
cid = {r["video_id"] for r in u}
print(f"  video có comment trong file: {len([v for v in last if v['video_id'] in cid])}/{len(list(last))}")

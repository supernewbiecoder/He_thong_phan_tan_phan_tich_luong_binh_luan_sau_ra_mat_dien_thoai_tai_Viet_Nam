"""Phát lại comment đã lưu vào Kafka theo thứ tự published_at, tốc độ 1x-100x.
Kỳ vọng: published_at giữ nguyên làm thời gian sự kiện; ingested_at ghi lại giờ máy lúc đẩy (đo độ trễ)."""
import json
import time
from datetime import datetime
from . import config
from .schema import COMMENT_FIELDS
from .sinks import make_producer, utcnow_iso
from .timeutil import parse


def load_records(models=None, since=None, until=None):
    seen, recs = set(), []
    for f in config.raw_files("comments"):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r["comment_id"] in seen or (models and not models & set((r["model"] or "").split("|"))):
                continue
            ts = parse(r["published_at"])
            if (since and ts < since) or (until and ts >= until):
                continue
            seen.add(r["comment_id"])
            recs.append((ts, r))
    recs.sort(key=lambda x: x[0])
    return recs


def run_replay(cfg, speed=10.0, models=None, since=None, until=None, max_gap=2.0, dry_run=False, strip_stats=False):
    recs = load_records(models, since, until)
    if not recs:
        print("Không có comment nào trong data/raw. Hãy chạy crawl trước.")
        return
    prod = None if dry_run or not cfg["kafka"]["bootstrap"] else make_producer(cfg["kafka"]["bootstrap"])
    print(f"Replay {len(recs)} comment, {recs[0][0]} -> {recs[-1][0]}, tốc độ {speed}x, "
          f"{'DRY-RUN' if prod is None else 'Kafka ' + cfg['kafka']['bootstrap']}")
    next_wall, prev = time.monotonic(), recs[0][0]
    for i, (ts, r) in enumerate(recs, 1):
        # khoảng nghỉ giữa 2 comment = chênh lệch thời gian sự kiện / tốc độ, chặn tối đa max_gap giây
        next_wall += min((ts - prev).total_seconds() / speed, max_gap)
        prev = ts
        delay = next_wall - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        for k in COMMENT_FIELDS:
            r.setdefault(k, None)
        if strip_stats:   # like/reply của "tương lai" so với thời điểm phát lại -> bỏ để demo không gian lận
            r["like_count"] = r["reply_count"] = None
        r["ingested_at"] = utcnow_iso()
        if prod:
            prod.produce(cfg["kafka"]["topic"], key=r["video_id"], value=json.dumps(r, ensure_ascii=False).encode("utf-8"))
            prod.poll(0)
        if i % 500 == 0:
            print(f"  {i}/{len(recs)}  (sự kiện: {ts})")
    if prod:
        left = prod.flush(60)
        if left:
            print(f"CẢNH BÁO: còn {left} message chưa gửi được vào Kafka")
    print("Xong.")

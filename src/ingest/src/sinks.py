"""Ghi ra 2 nơi: (1) archive JSONL (nguồn cho Replay, nguồn HDFS nếu môn yêu cầu),
(2) Kafka topic raw_comments khóa theo video_id (nếu có KAFKA_BOOTSTRAP)."""
import json
from datetime import datetime, timezone
from . import config
from .config import RAW_DIR
from .schema import COMMENT_FIELDS, check


def utcnow_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_producer(bootstrap):
    from confluent_kafka import Producer
    prod = Producer({"bootstrap.servers": bootstrap, "enable.idempotence": True, "acks": "all",
                     "linger.ms": 50, "compression.type": "lz4", "message.timeout.ms": 30000})
    try:   # kiểm tra kết nối ngay từ đầu để báo lỗi rõ ràng thay vì treo rồi mất dữ liệu
        prod.list_topics(timeout=8)
    except Exception as e:
        raise SystemExit(f"Không kết nối được Kafka tại {bootstrap} ({e}).\n"
                         "  - Chưa cần Kafka: để trống KAFKA_BOOTSTRAP trong .env (dữ liệu vẫn ghi ra data/raw/*.jsonl).\n"
                         "  - Cần Kafka: chạy 'docker compose -f docker-compose.dev.yml up -d' rồi kiểm tra 'docker ps'.")
    return prod


class Sink:
    def __init__(self, cfg):
        config.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.cfg = cfg
        self.topic = cfg["kafka"]["topic"]
        self.producer = make_producer(cfg["kafka"]["bootstrap"]) if cfg["kafka"]["bootstrap"] else None

    def write(self, recs):
        if not recs:
            return
        now = utcnow_iso()
        for r in recs:
            check(r, COMMENT_FIELDS)
            r["ingested_at"] = now
        # Thứ tự quan trọng: Kafka trước, file archive sau. Nếu Kafka lỗi thì chưa có gì trong archive,
        # lần thử lại không sinh bản trùng. Archive vì thế chỉ ghi đúng một lần cho mỗi trang.
        if self.producer:
            errors = []
            for r in recs:
                self.producer.produce(self.topic, key=r["video_id"],
                                      value=json.dumps(r, ensure_ascii=False).encode("utf-8"),
                                      on_delivery=lambda err, m: err and errors.append(err))
                self.producer.poll(0)
            remaining = self.producer.flush(30)   # số message CHƯA gửi được
            if errors or remaining:
                raise RuntimeError(f"Kafka lỗi: {len(errors)} message báo lỗi, {remaining} message chưa gửi được")
        path = config.raw_path(self.cfg, "comments")
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))

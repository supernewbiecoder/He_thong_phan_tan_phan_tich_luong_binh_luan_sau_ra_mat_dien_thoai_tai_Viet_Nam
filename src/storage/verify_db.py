#!/usr/bin/env python3
"""Mục đích: Kiểm một database MongoDB đã nạp đầu ra pipeline (python -m src.run --den nap_db): đủ collection, mention đúng contract aspect-mention v3, aggregates chỉ lưu số đếm, bình luận và danh mục máy đủ trường (docs/6-luu-tru/dac-ta.md); cập nhật lần cuối: 2026-11-26.

Bản đầu (Việt, Công việc 3, 28/10) tự nạp dữ liệu giả bằng seed_db.py khi database trống. seed_db.py đã gỡ ngày 26/11
vì sinh mention theo 9 khía cạnh cũ; database trống thì lệnh này báo lỗi, không tự sinh dữ liệu.

Chạy từ gốc repo:
    python -m src.storage.verify_db                      # MONGO_URI, MONGO_DB lấy từ biến môi trường
Trả mã 0 nếu mọi phép kiểm đạt, 1 nếu có phép kiểm hỏng.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pymongo import MongoClient

from src.storage.init_db import COLLECTIONS

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "aspect-mention.schema.json"
MAU_KIEM = 2000          # số mention lấy ra kiểm bằng JSON Schema
TRUONG_TY_LE = ("%", "percent", "pct", "ratio", "rate")   # aggregates không được có trường tỷ lệ
# Có thể trống ở giai đoạn chạy theo lô: chưa có luồng cảnh báo, chưa có nhãn người
CO_THE_TRONG = {"alerts", "gold_labels", "videos"}

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("verify_db")


class DBVerifier:
    def __init__(self, db):
        self.db = db
        self.results: List[Tuple[str, bool, str]] = []

    def record(self, name: str, passed: bool, message: str) -> None:
        self.results.append((name, passed, message))
        (logger.info if passed else logger.error)("[%s] %s: %s", "PASS" if passed else "FAIL", name, message)

    def verify_collections(self) -> None:
        existing = set(self.db.list_collection_names())
        counts = {c: self.db[c].count_documents({}) if c in existing else None for c in COLLECTIONS}
        empty = [c for c, n in counts.items() if not n and c not in CO_THE_TRONG]
        self.record("Collections", not empty,
                    f"Thiếu hoặc trống: {empty}. Chạy python -m src.run --den nap_db" if empty else f"Số document: {counts}")

    def verify_unique_keys(self) -> None:
        keys = {"models": "model_id", "comments": "comment_id", "aspect_mentions": "mention_id", "aggregates": "agg_id",
                "analysis_results": "analysis_id"}
        missing = []
        for collection, key in keys.items():
            indexes = self.db[collection].index_information() if collection in self.db.list_collection_names() else {}
            if not any(info.get("unique") and [k for k, _ in info["key"]] == [key] for info in indexes.values()):
                missing.append(f"{collection}.{key}")
        self.record("Unique indexes", not missing, f"Thiếu index duy nhất: {missing}" if missing else "Đủ index khóa chính")

    def verify_aggregates_counts_only(self) -> None:
        violations, checked = [], 0
        for doc in self.db.aggregates.find({}, {"_id": 0}):
            checked += 1
            agg = doc.get("agg_id", "?")
            for key in ("n_pos", "n_neg", "n_neu", "n_cmp", "n_total"):
                if type(doc.get(key)) is not int or doc[key] < 0:
                    violations.append(f"{agg}: {key} phải là số nguyên không âm")
            bad = [k for k in doc if any(t in k.lower() for t in TRUONG_TY_LE)]
            if bad:
                violations.append(f"{agg}: có trường tỷ lệ {bad}")
            if not violations and doc["n_total"] != doc["n_pos"] + doc["n_neg"] + doc["n_neu"] + doc["n_cmp"]:
                violations.append(f"{agg}: n_total khác tổng các ô")
            if len(violations) > 20:
                break
        self.record("Aggregates chỉ lưu số đếm", not violations,
                    f"{len(violations)} lỗi, ví dụ {violations[:3]}" if violations else f"Đã kiểm {checked} dòng")

    def verify_aspect_mentions(self) -> None:
        from jsonschema import Draft7Validator

        validator = Draft7Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
        violations, checked = [], 0
        for doc in self.db.aspect_mentions.find({}, {"_id": 0}).limit(MAU_KIEM):
            checked += 1
            errors = list(validator.iter_errors(doc))
            if errors:
                violations.append(f"{doc.get('mention_id')}: {errors[0].message}")
        self.record("Mention đúng contract v3", checked > 0 and not violations,
                    f"{len(violations)} lỗi, ví dụ {violations[:3]}" if violations else f"Đã kiểm {checked} mention")

    def verify_comments(self) -> None:
        violations = []
        for doc in self.db.comments.find({}, {"_id": 0}).limit(MAU_KIEM):
            for key in ("comment_id", "video_id", "model", "published_at", "is_spam", "is_vietnamese", "pipeline_version"):
                if doc.get(key) is None:
                    violations.append(f"{doc.get('comment_id')}: thiếu {key}")
        self.record("Bình luận đủ trường", not violations,
                    f"{len(violations)} lỗi, ví dụ {violations[:3]}" if violations else "Đủ trường tầng 2")

    def verify_models(self) -> None:
        missing = [doc.get("model_id") for doc in self.db.models.find({}, {"_id": 0}) if not doc.get("launch_date")]
        total = self.db.models.count_documents({})
        self.record("Danh mục máy", total > 0 and not missing,
                    f"Máy thiếu launch_date: {missing[:5]}" if missing else f"{total} máy, đều có launch_date")

    def run_all(self) -> bool:
        self.verify_collections()
        self.verify_unique_keys()
        self.verify_aggregates_counts_only()
        self.verify_aspect_mentions()
        self.verify_comments()
        self.verify_models()
        print("\n" + "=" * 70)
        for name, passed, msg in self.results:
            print(f"{name:<30} | {'PASS' if passed else 'FAIL':<4} | {msg[:80]}")
        print("=" * 70)
        return all(passed for _, passed, _ in self.results)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Kiểm database MongoDB đã nạp đầu ra pipeline")
    parser.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    parser.add_argument("--db", default=os.getenv("MONGO_DB", "smartphone_analytics"))
    args = parser.parse_args()
    client = MongoClient(args.uri, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")   # không có MongoDB thì dừng, không âm thầm kiểm database trong bộ nhớ
    sys.exit(0 if DBVerifier(client[args.db]).run_all() else 1)


if __name__ == "__main__":
    main()

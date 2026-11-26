#!/usr/bin/env python3
"""
Database Seeding Script (seed_db.py)
Project: Sentiment Stream Analytics for Smartphone Launches
Author: Viet (STT 3 - Thiet ke DB)
Updated: 2026-10-28

Purpose:
  - Populate reference and sample data into all 7 MongoDB collections conforming
    to contracts/aspect-mention.schema.json and docs/data-model.md:
      1. models: Ingested from config/pipeline.yaml with brands, launch dates, and rivals.
      2. videos: YouTube video metadata for popular tech channels.
      3. comments: Real cleaned comments sampled from data/clean_data.jsonl.
      4. aspect_mentions: Clause-level ABSA records tagged with 9 canonical aspects,
         sentiments (pos/neg/neu), defect_type, compare_with, label_source, model_version.
      5. aggregates: Precomputed window rollups storing COUNT NUMBERS ONLY (n_pos, n_neg, n_neu; NO %).
      6. alerts: Historical anomaly spike records.
      7. gold_labels: Curated double-annotated ground-truth test clauses.
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path to support direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from pymongo import MongoClient

from src.storage.init_db import (
    CANONICAL_ASPECTS,
    COLLECTIONS,
    DEFECT_TYPES,
    LABEL_SOURCES,
    SENTIMENTS,
    get_db_client,
    init_database,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("seed_db")

# Keyword dictionaries for rule-based aspect extraction
ASPECT_KEYWORDS = {
    "BATTERY": ["pin", "sạc", "mah", "onscreen", "on screen", "dùng pin", "củ sạc", "pin trâu", "pin hẻo", "tuột pin", "tụt pin"],
    "CAMERA": ["cam", "camera", "chụp", "ảnh", "quay", "zoom", "tele", "màu sắc", "video", "flash", "ống kính", "cảm biến", "độ phân giải"],
    "PRICE": ["giá", "tiền", "triệu", "củ", "đắt", "rẻ", "mắc", "khuyến mãi", "sale", "mua lại", "hạt dẻ", "xứng đáng đồng tiền"],
    "PERFORMANCE": ["mượt", "lag", "giật", "fps", "chip", "snap", "snapdragon", "dimensity", "bionic", "exynos", "game", "tác vụ", "ram", "load", "nóng", "nhiệt", "ấm", "tản nhiệt", "hạ nhiệt", "mát", "quá nhiệt"],
    "DISPLAY": ["màn", "màn hình", "hiển thị", "120hz", "độ sáng", "oled", "amoled", "sọc màn", "tai thỏ", "nốt ruồi", "tần số quét"],
    "DESIGN": ["viền", "thiết kế", "cầm", "nặng", "đẹp", "xấu", "mặt lưng", "vuông vức", "bo cong", "màu sắc", "ngoại hình", "độ bền"],
    "SOFTWARE": ["oneui", "one ui", "ios", "cập nhật", "update", "phần mềm", "lỗi app", "hệ điều hành", "giao diện", "bug", "vá lỗi"],
    "HARDWARE_OTHER": ["loa", "rung", "vân tay", "face id", "sóng", "wifi", "bộ nhớ", "bút", "spen", "mic", "chống nước"],
    "WARRANTY": ["bảo hành", "bán", "shop", "cửa hàng", "giao hàng", "đổi trả", "tgdd", "fpt", "cellphones", "hỗ trợ", "chăm sóc", "chính hãng", "xách tay"],
}

POS_WORDS = ["tốt", "ngon", "đẹp", "mượt", "trâu", "ổn", "thích", "đỉnh", "xuất sắc", "ok", "yêu", "hơn", "tuyệt", "ưng", "hài lòng", "đáng mua"]
NEG_WORDS = ["kém", "chán", "tệ", "nóng", "lag", "giật", "đắt", "chê", "thua", "lỗi", "sọc", "hỏng", "hao", "yếu", "thất vọng", "thua xa", "nản", "tụt"]
OWNER_WORDS = ["đang xài", "đang dùng", "đã mua", "mình dùng", "mình xài", "mua được", "trải nghiệm rồi", "dùng 1 tháng", "dùng 1 tuần", "xài 1 năm", "vừa bóc hộp"]


def extract_aspect_sentiment(text: str) -> Dict[str, Any]:
    text_lower = text.lower()

    # 1. Detect aspect
    matched_aspect = "PERFORMANCE"
    for aspect, kws in ASPECT_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            matched_aspect = aspect
            break

    # 2. Detect sentiment
    pos_score = sum(1 for w in POS_WORDS if w in text_lower)
    neg_score = sum(1 for w in NEG_WORDS if w in text_lower)

    if pos_score > neg_score:
        sentiment = "pos"
        confidence = 0.92
    elif neg_score > pos_score:
        sentiment = "neg"
        confidence = 0.90
    else:
        sentiment = "neu"
        confidence = 0.85

    # 3. Detect defect_type if neg
    defect_type = None
    if sentiment == "neg":
        if "nóng" in text_lower or "nhiệt" in text_lower:
            defect_type = "OVERHEAT"
        elif "pin" in text_lower or "tụt" in text_lower:
            defect_type = "BATTERY_DRAIN"
        elif "sọc" in text_lower or "màn" in text_lower:
            defect_type = "DISPLAY_DEFECT"
        elif "lag" in text_lower or "giật" in text_lower or "drop" in text_lower:
            defect_type = "LAG"
        elif "app" in text_lower or "văng" in text_lower or "bug" in text_lower:
            defect_type = "SOFTWARE_BUG"
        else:
            defect_type = "OTHER"

    # 4. Detect owner mention
    is_owner = any(w in text_lower for w in OWNER_WORDS)

    return {
        "aspect": matched_aspect,
        "sentiment": sentiment,
        "confidence": confidence,
        "defect_type": defect_type,
        "is_owner": is_owner,
    }


def seed_models(db, config_path: str = "config/pipeline.yaml"):
    """
    Seed models from config/pipeline.yaml conforming to docs/data-model.md.
    """
    logger.info("Seeding 'models' collection...")
    models_to_insert = []

    if Path(config_path).exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                yaml_models = cfg.get("models", [])
                for m in yaml_models:
                    model_id = m.get("name")
                    brand = "Apple" if "ip" in model_id.lower() else "Samsung" if "s2" in model_id.lower() else "Xiaomi" if "xiaomi" in model_id.lower() else "vivo"
                    predecessor_id = "s22u" if model_id == "s23u" else "ip14prm" if model_id == "ip15prm" else None
                    rival_names = [r.get("name") if isinstance(r, dict) else r for r in m.get("rivals", [])]
                    models_to_insert.append({
                        "model_id": model_id,
                        "title": m.get("title", model_id),
                        "brand": brand,
                        "segment": "flagship",
                        "launch_date": str(m.get("launch_date", "2023-02-02")),
                        "predecessor_id": predecessor_id,
                        "rivals": rival_names,
                        "aliases": m.get("aliases", []),
                    })
        except Exception as e:
            logger.warning("Could not parse %s: %s. Using default models.", config_path, e)

    if not models_to_insert:
        models_to_insert = [
            {
                "model_id": "s23u",
                "title": "Samsung Galaxy S23 Ultra",
                "brand": "Samsung",
                "segment": "flagship",
                "launch_date": "2023-02-02",
                "predecessor_id": "s22u",
                "rivals": ["ip14prm", "xiaomi13u"],
                "aliases": ["Galaxy S23 Ultra", "S23 Ultra", "s23u"],
            },
            {
                "model_id": "s22u",
                "title": "Samsung Galaxy S22 Ultra",
                "brand": "Samsung",
                "segment": "flagship",
                "launch_date": "2022-02-09",
                "predecessor_id": "s21u",
                "rivals": ["ip13prm"],
                "aliases": ["Galaxy S22 Ultra", "S22 Ultra", "s22u"],
            },
            {
                "model_id": "ip14prm",
                "title": "iPhone 14 Pro Max",
                "brand": "Apple",
                "segment": "flagship",
                "launch_date": "2022-09-16",
                "predecessor_id": "ip13prm",
                "rivals": ["s22u"],
                "aliases": ["iPhone 14 Pro Max", "ip14 prm", "14 pro max"],
            },
        ]

    for m in models_to_insert:
        db.models.update_one({"model_id": m["model_id"]}, {"$set": m}, upsert=True)

    logger.info("Seeded %d models into 'models'.", len(models_to_insert))


def seed_videos(db):
    """
    Seed sample YouTube videos for phone reviews.
    """
    logger.info("Seeding 'videos' collection...")
    sample_videos = [
        {
            "video_id": "9SmOJHZTkC4",
            "video_model": "s23u",
            "channel_id": "UCEeXA5Tu7n9X5_zkOgGsyww",
            "channel_name": "Vật Vờ Studio",
            "title": "Đánh giá Galaxy S23 Ultra sau 1 tuần: Bước nhảy vọt về Pin và Hiệu năng!",
            "published_at": "2023-02-09T11:00:00Z",
            "source": "youtube",
            "view_count": 320000,
            "comment_count": 1420,
        },
        {
            "video_id": "aB3dE5fG7hI",
            "video_model": "s23u",
            "channel_id": "UC_duy_tham_channel",
            "channel_name": "Duy Thẩm",
            "title": "S23 Ultra vs iPhone 14 Pro Max: Kèo đấu flagship đỉnh cao nhất năm!",
            "published_at": "2023-02-12T14:30:00Z",
            "source": "youtube",
            "view_count": 450000,
            "comment_count": 980,
        },
        {
            "video_id": "vid_s22u_review",
            "video_model": "s22u",
            "channel_id": "UCEeXA5Tu7n9X5_zkOgGsyww",
            "channel_name": "Vật Vờ Studio",
            "title": "Galaxy S22 Ultra sau 1 tháng: Chip Snapdragon 8 Gen 1 có thực sự nóng?",
            "published_at": "2022-03-01T10:00:00Z",
            "source": "youtube",
            "view_count": 280000,
            "comment_count": 850,
        },
    ]

    for v in sample_videos:
        db.videos.update_one({"video_id": v["video_id"]}, {"$set": v}, upsert=True)

    logger.info("Seeded %d videos into 'videos'.", len(sample_videos))


def seed_comments_and_mentions(
    db, data_path: str = "data/clean_data.jsonl", limit: int = 500
):
    """
    Ingests comments and generates clause-level aspect_mentions.
    Conforms to contracts/aspect-mention.schema.json.
    """
    logger.info("Seeding 'comments' and 'aspect_mentions' from %s (limit: %d)...", data_path, limit)

    comments_batch = []
    mentions_batch = []

    file_path = Path(data_path)
    if not file_path.exists():
        candidate_paths = [
            Path("data/clean_data.jsonl"),
            Path("../data/clean_data.jsonl"),
            Path("F:/intro_data_science/repo-feature-eda-dashboard/data/clean_data.jsonl"),
        ]
        for p in candidate_paths:
            if p.exists():
                file_path = p
                break

    if file_path.exists():
        logger.info("Reading raw data from: %s", file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                if count >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    model_name = record.get("model", "s23u")
                    if model_name in ["ip6", "ip11", "generic"]:
                        model_name = "s23u"

                    comment_id = record.get("comment_id")
                    video_id = record.get("video_id", "9SmOJHZTkC4")
                    published_at = record.get("published_at", "2023-02-10T00:00:00Z")
                    text = record.get("text", "")

                    comment_doc = {
                        "comment_id": comment_id,
                        "video_id": video_id,
                        "model": model_name,
                        "text": text,
                        "text_norm": record.get("text_norm", text.lower()),
                        "like_count": int(record.get("like_count", 0)),
                        "reply_count": int(record.get("reply_count", 0)),
                        "is_spam": bool(record.get("is_spam", False)),
                        "is_vietnamese": bool(record.get("is_vietnamese", True)),
                        "published_at": published_at,
                    }
                    comments_batch.append(comment_doc)

                    # Extract clauses into aspect_mentions
                    clauses = record.get("clauses", [])
                    if not clauses and text:
                        clauses = [{"clause_id": 1, "text": text}]

                    for idx, c in enumerate(clauses):
                        c_idx = c.get("clause_id", idx + 1)
                        c_text = c.get("text", "")
                        if not c_text:
                            continue

                        meta = extract_aspect_sentiment(c_text)

                        # Comparison logic
                        c_lower = c_text.lower()
                        compare_with = None
                        compare_winner = None
                        if "ip14" in c_lower or "14 pro" in c_lower:
                            compare_with = "ip14prm"
                            compare_winner = "target" if meta["sentiment"] == "pos" else "other"
                        elif "s22" in c_lower:
                            compare_with = "s22u"
                            compare_winner = "target" if meta["sentiment"] == "pos" else "other"

                        mention_id = f"{comment_id}#{c_idx}#{meta['aspect']}"
                        mention_doc = {
                            "mention_id": mention_id,
                            "comment_id": comment_id,
                            "clause_idx": c_idx,
                            "clause_text": c_text,
                            "source": "youtube",
                            "video_id": video_id,
                            "video_model": model_name,
                            "target_model": model_name,
                            "aspect": meta["aspect"],
                            "sentiment": meta["sentiment"],
                            "confidence": meta["confidence"],
                            "is_owner": meta["is_owner"],
                            "defect_type": meta["defect_type"],
                            "compare_with": compare_with,
                            "compare_winner": compare_winner,
                            "published_at": published_at,
                            "days_since_launch": 8,
                            "label_source": "rule",
                            "model_version": "rule-v0",
                            "schema_version": 1,
                        }
                        mentions_batch.append(mention_doc)

                    count += 1
                except Exception as ex:
                    logger.debug("Error processing row: %s", ex)

    for c in comments_batch:
        db.comments.update_one({"comment_id": c["comment_id"]}, {"$set": c}, upsert=True)
    logger.info("Seeded %d comments into 'comments'.", len(comments_batch))

    for m in mentions_batch:
        db.aspect_mentions.update_one({"mention_id": m["mention_id"]}, {"$set": m}, upsert=True)
    logger.info("Seeded %d mentions into 'aspect_mentions'.", len(mentions_batch))


def seed_aggregates(db):
    """
    Computes and seeds window aggregations conforming to docs/data-model.md.
    CRITICAL RULE: MUST STORE COUNT NUMBERS ONLY (n_pos, n_neg, n_neu).
    ABSOLUTELY NO '%' FIELD!
    """
    logger.info("Seeding 'aggregates' collection (COUNT NUMBERS ONLY: n_pos, n_neg, n_neu; NO %)...")

    models = ["s23u", "s22u", "ip14prm"]
    weeks = [1, 2, 3, 4]

    # Aspect distribution base stats
    base_stats = {
        "s23u": {
            "BATTERY": (95, 12, 10, 3, 15, 11, 4),
            "CAMERA": (130, 10, 15, 1, 20, 14, 6),
            "PERFORMANCE": (102, 8, 12, 2, 18, 12, 6),
            "PRICE": (38, 60, 22, 0, 12, 5, 7),
            "DISPLAY": (85, 6, 11, 1, 8, 5, 3),
            "DESIGN": (70, 11, 14, 0, 9, 5, 4),
            "SOFTWARE": (78, 15, 12, 3, 6, 4, 2),
            "HARDWARE_OTHER": (45, 8, 10, 0, 4, 2, 2),
            "WARRANTY": (45, 7, 10, 0, 4, 3, 1),
        },
        "s22u": {
            "BATTERY": (45, 80, 15, 21, 10, 4, 6),
            "PERFORMANCE": (72, 45, 18, 8, 11, 5, 6),
            "CAMERA": (90, 20, 20, 2, 15, 8, 7),
            "PRICE": (30, 40, 15, 0, 8, 3, 5),
            "DISPLAY": (75, 10, 12, 1, 6, 3, 3),
            "DESIGN": (65, 12, 10, 0, 7, 4, 3),
            "SOFTWARE": (60, 25, 15, 5, 5, 2, 3),
            "HARDWARE_OTHER": (40, 10, 8, 1, 3, 1, 2),
            "WARRANTY": (35, 10, 10, 0, 2, 1, 1),
        },
        "ip14prm": {
            "BATTERY": (90, 22, 12, 5, 15, 9, 6),
            "CAMERA": (122, 15, 18, 2, 19, 10, 9),
            "PERFORMANCE": (112, 10, 15, 1, 16, 10, 6),
            "PRICE": (25, 70, 15, 0, 15, 5, 10),
            "DISPLAY": (88, 8, 10, 1, 7, 4, 3),
            "DESIGN": (78, 15, 12, 0, 8, 5, 3),
            "SOFTWARE": (80, 18, 14, 2, 7, 4, 3),
            "HARDWARE_OTHER": (42, 6, 8, 0, 3, 2, 1),
            "WARRANTY": (40, 8, 10, 0, 3, 2, 1),
        },
    }

    aggregates_docs = []

    for model_name, aspect_dict in base_stats.items():
        video_id = "9SmOJHZTkC4" if model_name == "s23u" else "aB3dE5fG7hI"
        for aspect, (pos, neg, neu, defect_cnt, comp_cnt, win_cnt, lose_cnt) in aspect_dict.items():
            for w in weeks:
                agg_id = f"{model_name}#{aspect}#w{w}#{video_id}#rule-v0"
                doc = {
                    "agg_id": agg_id,
                    "target_model": model_name,
                    "aspect": aspect,
                    "week_since_launch": w,
                    "video_id": video_id,
                    "source": "youtube",
                    "model_version": "rule-v0",
                    "n_pos": pos,
                    "n_neg": neg,
                    "n_neu": neu,
                    "n_total": pos + neg + neu,
                    "owner_defect_count": defect_cnt,
                    "compare_count": comp_cnt,
                    "compare_win_count": win_cnt,
                    "compare_lose_count": lose_cnt,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                aggregates_docs.append(doc)

    for agg in aggregates_docs:
        db.aggregates.update_one({"agg_id": agg["agg_id"]}, {"$set": agg}, upsert=True)

    logger.info("Seeded %d aggregate rollup documents into 'aggregates'.", len(aggregates_docs))


def seed_alerts(db):
    """
    Seed realistic anomaly alerts.
    """
    logger.info("Seeding 'alerts' collection...")
    alerts_data = [
        {
            "alert_id": "ALT_20230214_s23u_OVERHEAT",
            "target_model": "s23u",
            "aspect": "PERFORMANCE",
            "metric": "neg_sentiment_spike",
            "value": 54.2,
            "baseline": 22.0,
            "threshold": 45.0,
            "severity": "warning",
            "status": "resolved",
            "sample_mention_ids": ["c_sample_heat_1#1#PERFORMANCE"],
            "window_start": "2023-02-14T08:00:00Z",
            "window_end": "2023-02-14T10:00:00Z",
            "created_at": "2023-02-14T10:05:00Z",
        },
        {
            "alert_id": "ALT_20230220_s23u_SOFTWARE_BUG",
            "target_model": "s23u",
            "aspect": "SOFTWARE",
            "metric": "camera_app_crash_defect",
            "value": 18.5,
            "baseline": 4.0,
            "threshold": 15.0,
            "severity": "info",
            "status": "acknowledged",
            "sample_mention_ids": ["c_sample_cam_crash#1#SOFTWARE"],
            "window_start": "2023-02-20T14:00:00Z",
            "window_end": "2023-02-20T16:00:00Z",
            "created_at": "2023-02-20T16:10:00Z",
        },
        {
            "alert_id": "ALT_20220228_s22u_OVERHEAT",
            "target_model": "s22u",
            "aspect": "PERFORMANCE",
            "metric": "severe_throttling_spike",
            "value": 68.9,
            "baseline": 30.0,
            "threshold": 50.0,
            "severity": "critical",
            "status": "active",
            "sample_mention_ids": ["c_sample_s22u_lag#1#PERFORMANCE"],
            "window_start": "2022-02-28T09:00:00Z",
            "window_end": "2022-02-28T12:00:00Z",
            "created_at": "2022-02-28T12:15:00Z",
        },
    ]

    for alt in alerts_data:
        db.alerts.update_one({"alert_id": alt["alert_id"]}, {"$set": alt}, upsert=True)

    logger.info("Seeded %d alerts into 'alerts'.", len(alerts_data))


def seed_gold_labels(db):
    """
    Seed double-annotated ground-truth test clauses conforming to docs/data-model.md.
    """
    logger.info("Seeding 'gold_labels' collection...")
    gold_data = [
        {
            "clause_id": "c_gold_001#1",
            "comment_id": "c_gold_001",
            "clause_text": "Pin S23 Ultra trâu hơn S22 Ultra rất nhiều, on screen gần 8 tiếng.",
            "video_id": "9SmOJHZTkC4",
            "annotator": "Lam",
            "label_source": "human",
            "split": "test",
            "aspects": [{"aspect": "BATTERY", "sentiment": "pos"}],
            "target_model": "s23u",
            "is_owner": True,
            "defect_type": None,
            "compare_with": "s22u",
            "compare_winner": "target",
            "guideline_version": "v1.0",
            "labeled_at": "2026-10-28T00:00:00Z",
        },
        {
            "clause_id": "c_gold_001#1",
            "comment_id": "c_gold_001",
            "clause_text": "Pin S23 Ultra trâu hơn S22 Ultra rất nhiều, on screen gần 8 tiếng.",
            "video_id": "9SmOJHZTkC4",
            "annotator": "Tien",
            "label_source": "human",
            "split": "test",
            "aspects": [{"aspect": "BATTERY", "sentiment": "pos"}],
            "target_model": "s23u",
            "is_owner": True,
            "defect_type": None,
            "compare_with": "s22u",
            "compare_winner": "target",
            "guideline_version": "v1.0",
            "labeled_at": "2026-10-28T00:00:00Z",
        },
        {
            "clause_id": "c_gold_002#1",
            "comment_id": "c_gold_002",
            "clause_text": "Chơi game lâu máy vẫn ấm lên khá rõ ở viền kim loại.",
            "video_id": "9SmOJHZTkC4",
            "annotator": "Lam",
            "label_source": "human",
            "split": "test",
            "aspects": [{"aspect": "PERFORMANCE", "sentiment": "neg"}],
            "target_model": "s23u",
            "is_owner": True,
            "defect_type": "OVERHEAT",
            "compare_with": None,
            "compare_winner": None,
            "guideline_version": "v1.0",
            "labeled_at": "2026-10-28T00:00:00Z",
        },
        {
            "clause_id": "c_gold_003#1",
            "comment_id": "c_gold_003",
            "clause_text": "Mức giá mở bán hơn 31 triệu là hơi cao so với thu nhập người Việt.",
            "video_id": "9SmOJHZTkC4",
            "annotator": "Lam",
            "label_source": "human",
            "split": "test",
            "aspects": [{"aspect": "PRICE", "sentiment": "neg"}],
            "target_model": "s23u",
            "is_owner": False,
            "defect_type": None,
            "compare_with": None,
            "compare_winner": None,
            "guideline_version": "v1.0",
            "labeled_at": "2026-10-28T00:00:00Z",
        },
        {
            "clause_id": "c_gold_004#1",
            "comment_id": "c_gold_004",
            "clause_text": "Camera 200MP chụp zoom ban ngày chi tiết ăn đứt iPhone 14 Pro Max.",
            "video_id": "aB3dE5fG7hI",
            "annotator": "Tien",
            "label_source": "human",
            "split": "test",
            "aspects": [{"aspect": "CAMERA", "sentiment": "pos"}],
            "target_model": "s23u",
            "is_owner": False,
            "defect_type": None,
            "compare_with": "ip14prm",
            "compare_winner": "target",
            "guideline_version": "v1.0",
            "labeled_at": "2026-10-28T00:00:00Z",
        },
    ]

    for g in gold_data:
        db.gold_labels.update_one(
            {"clause_id": g["clause_id"], "annotator": g["annotator"]},
            {"$set": g},
            upsert=True,
        )

    logger.info("Seeded %d gold labels into 'gold_labels'.", len(gold_data))


def seed_all(db, limit: int = 500):
    seed_models(db)
    seed_videos(db)
    seed_comments_and_mentions(db, limit=limit)
    seed_aggregates(db)
    seed_alerts(db)
    seed_gold_labels(db)


def main():
    parser = argparse.ArgumentParser(description="Seed MongoDB collections with smartphone analytics data.")
    parser.add_argument(
        "--uri",
        default=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        help="MongoDB connection URI (default: mongodb://localhost:27017)",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("MONGO_DB", "smartphone_analytics"),
        help="Database name (default: smartphone_analytics)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force using in-memory mongomock",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of comments to ingest from clean_data.jsonl (default: 500)",
    )

    args = parser.parse_args()

    client = get_db_client(args.uri, mock=args.mock)
    db = init_database(client, db_name=args.db)

    seed_all(db, limit=args.limit)
    logger.info("Database seeding finished successfully!")


if __name__ == "__main__":
    main()

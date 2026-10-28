#!/usr/bin/env python3
"""
Database Seeding Script (seed_db.py)
Project: Sentiment Stream Analytics for Smartphone Launches
Author: Viet (STT 3 - Thiet ke DB)
Updated: 2026-10-28

Purpose:
  - Populate initial reference and sample data into all 7 MongoDB collections:
      1. models: Ingested from config/pipeline.yaml with brands, launch dates, and rivals.
      2. videos: YouTube video metadata for popular tech channels.
      3. comments: Real cleaned comments sampled from data/clean_data.jsonl.
      4. aspect_mentions: Clause-level ABSA records tagged with 9 canonical aspects,
         sentiments, defect categories, comparison flags, label_source, and model_version.
      5. aggregates: Precomputed window rollups storing COUNT NUMBERS ONLY (NO % FIELD!).
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
from pymongo import MongoClient, UpdateOne

from src.storage.init_db import (
    CANONICAL_ASPECTS,
    COLLECTIONS,
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
    "PERFORMANCE": ["mượt", "lag", "giật", "fps", "chip", "snap", "snapdragon", "dimensity", "bionic", "exynos", "game", "tác vụ", "ram", "load"],
    "DISPLAY": ["màn", "màn hình", "hiển thị", "120hz", "độ sáng", "oled", "amoled", "sọc màn", "tai thỏ", "nốt ruồi", "tần số quét"],
    "THERMAL": ["nóng", "nhiệt", "ấm", "tản nhiệt", "hạ nhiệt", "mát", "bỏng tay", "quá nhiệt"],
    "DESIGN": ["viền", "thiết kế", "cầm", "nặng", "đẹp", "xấu", "mặt lưng", "vuông vức", "bo cong", "màu sắc", "ngoại hình"],
    "SOFTWARE": ["oneui", "one ui", "ios", "cập nhật", "update", "phần mềm", "lỗi app", "hệ điều hành", "giao diện", "bug", "vá lỗi"],
    "SERVICE": ["bảo hành", "bán", "shop", "cửa hàng", "giao hàng", "đổi trả", "tgdd", "fpt", "cellphones", "hỗ trợ", "chăm sóc"],
}

POS_WORDS = ["tốt", "ngon", "đẹp", "mượt", "trâu", "ổn", "thích", "đỉnh", "xuất sắc", "ok", "yêu", "hơn", "tuyệt", "ưng", "hài lòng", "đáng mua"]
NEG_WORDS = ["kém", "chán", "tệ", "nóng", "lag", "giật", "đắt", "chê", "thua", "lỗi", "sọc", "hỏng", "hao", "yếu", "thất vọng", "thua xa", "nản"]
OWNER_WORDS = ["đang xài", "đang dùng", "đã mua", "mình dùng", "mình xài", "mua được", "trải nghiệm rồi", "dùng 1 tháng", "dùng 1 tuần", "xài 1 năm", "vừa bóc hộp"]


def extract_aspect_sentiment(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    
    # 1. Detect aspect
    matched_aspect = "GENERAL"
    for aspect, kws in ASPECT_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            matched_aspect = aspect
            break

    # 2. Detect sentiment
    pos_score = sum(1 for w in POS_WORDS if w in text_lower)
    neg_score = sum(1 for w in NEG_WORDS if w in text_lower)

    if pos_score > neg_score:
        sentiment = "positive"
        score = 1
        confidence = 0.92
    elif neg_score > pos_score:
        sentiment = "negative"
        score = -1
        confidence = 0.90
    else:
        sentiment = "neutral"
        score = 0
        confidence = 0.85

    # 3. Detect defect category if negative
    defect_category = None
    if sentiment == "negative":
        if matched_aspect == "THERMAL":
            defect_category = "Quá nhiệt nóng máy"
        elif matched_aspect == "BATTERY":
            defect_category = "Hao pin tụt nhanh"
        elif matched_aspect == "DISPLAY":
            defect_category = "Lỗi sọc hoặc ám màn hình"
        elif matched_aspect == "PERFORMANCE":
            defect_category = "Giật khung hình drop FPS"
        elif matched_aspect == "SOFTWARE":
            defect_category = "Lỗi ứng dụng văng crash"

    # 4. Detect owner mention
    is_owner = any(w in text_lower for w in OWNER_WORDS)

    return {
        "aspect": matched_aspect,
        "sentiment": sentiment,
        "sentiment_score": score,
        "confidence": confidence,
        "defect_category": defect_category,
        "is_owner_mention": is_owner,
    }


def seed_models(db, config_path: str = "config/pipeline.yaml"):
    """
    Seed models from config/pipeline.yaml or fallback catalog.
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
                    brand = "Apple" if "ip" in model_id.lower() else "Samsung" if "s2" in model_id.lower() else "Xiaomi" if "xiaomi" in model_id.lower() else "Vivo"
                    predecessor = "s22u" if model_id == "s23u" else "ip14prm" if model_id == "ip15prm" else None
                    models_to_insert.append({
                        "model_id": model_id,
                        "name": model_id,
                        "title": m.get("title", model_id),
                        "brand": brand,
                        "segment": "flagship",
                        "launch_date": str(m.get("launch_date", "2023-02-02")),
                        "predecessor": predecessor,
                        "rivals": m.get("rivals", []),
                        "aliases": m.get("aliases", []),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception as e:
            logger.warning("Could not parse %s: %s. Using default models.", config_path, e)

    if not models_to_insert:
        # Fallback canonical flagship models
        models_to_insert = [
            {
                "model_id": "s23u",
                "name": "s23u",
                "title": "Samsung Galaxy S23 Ultra",
                "brand": "Samsung",
                "segment": "flagship",
                "launch_date": "2023-02-02",
                "predecessor": "s22u",
                "rivals": [
                    {"name": "ip14prm", "title": "iPhone 14 Pro Max", "launch_date": "2022-09-16"},
                    {"name": "xiaomi13u", "title": "Xiaomi 13 Ultra", "launch_date": "2023-04-18"},
                ],
                "aliases": ["Galaxy S23 Ultra", "S23 Ultra", "s23u"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "model_id": "s22u",
                "name": "s22u",
                "title": "Samsung Galaxy S22 Ultra",
                "brand": "Samsung",
                "segment": "flagship",
                "launch_date": "2022-02-09",
                "predecessor": "s21u",
                "rivals": [{"name": "ip13prm", "title": "iPhone 13 Pro Max", "launch_date": "2021-09-14"}],
                "aliases": ["Galaxy S22 Ultra", "S22 Ultra", "s22u"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "model_id": "ip14prm",
                "name": "ip14prm",
                "title": "iPhone 14 Pro Max",
                "brand": "Apple",
                "segment": "flagship",
                "launch_date": "2022-09-16",
                "predecessor": "ip13prm",
                "rivals": [{"name": "s22u", "title": "Samsung Galaxy S22 Ultra", "launch_date": "2022-02-09"}],
                "aliases": ["iPhone 14 Pro Max", "ip14 prm", "14 pro max"],
                "created_at": datetime.now(timezone.utc).isoformat(),
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
            "model": "s23u",
            "channel_id": "UCEeXA5Tu7n9X5_zkOgGsyww",
            "channel_name": "Vật Vờ Studio",
            "title": "Đánh giá Galaxy S23 Ultra sau 1 tuần: Bước nhảy vọt về Pin và Hiệu năng!",
            "published_at": "2023-02-09T11:00:00Z",
            "source": "youtube",
            "comment_count_ingested": 1420,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "video_id": "vid_s23u_duytham",
            "model": "s23u",
            "channel_id": "UC_duy_tham_channel",
            "channel_name": "Duy Thẩm",
            "title": "S23 Ultra vs iPhone 14 Pro Max: Kèo đấu flagship đỉnh cao nhất năm!",
            "published_at": "2023-02-12T14:30:00Z",
            "source": "youtube",
            "comment_count_ingested": 980,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "video_id": "vid_s22u_review",
            "model": "s22u",
            "channel_id": "UCEeXA5Tu7n9X5_zkOgGsyww",
            "channel_name": "Vật Vờ Studio",
            "title": "Galaxy S22 Ultra sau 1 tháng: Chip Snapdragon 8 Gen 1 có thực sự nóng?",
            "published_at": "2022-03-01T10:00:00Z",
            "source": "youtube",
            "comment_count_ingested": 850,
            "created_at": datetime.now(timezone.utc).isoformat(),
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
    """
    logger.info("Seeding 'comments' and 'aspect_mentions' from %s (limit: %d)...", data_path, limit)

    comments_batch = []
    mentions_batch = []

    file_path = Path(data_path)
    if not file_path.exists():
        # Fallback to parent path if running from repo root or subfolder
        candidate_paths = [
            Path("data/clean_data.jsonl"),
            Path("../data/clean_data.jsonl"),
            Path("../../data/clean_data.jsonl"),
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
                    # Normalize target model to s23u if generic for testing
                    model_name = record.get("model", "s23u")
                    if model_name in ["ip6", "ip11", "generic"]:
                        model_name = "s23u"

                    comment_id = record.get("comment_id")
                    video_id = record.get("video_id", "9SmOJHZTkC4")
                    published_at = record.get("published_at", "2023-02-10T00:00:00Z")
                    text = record.get("text", "")

                    # Check ownership
                    is_owner = any(w in text.lower() for w in OWNER_WORDS)

                    comment_doc = {
                        "comment_id": comment_id,
                        "video_id": video_id,
                        "parent_id": record.get("parent_id"),
                        "model": model_name,
                        "text": text,
                        "text_norm": record.get("text_norm", text.lower()),
                        "like_count": int(record.get("like_count", 0)),
                        "reply_count": int(record.get("reply_count", 0)),
                        "is_spam": bool(record.get("is_spam", False)),
                        "is_vietnamese": bool(record.get("is_vietnamese", True)),
                        "is_owner": is_owner,
                        "label_source": "rule",
                        "model_version": "v1.0.0",
                        "published_at": published_at,
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                    }
                    comments_batch.append(comment_doc)

                    # Extract clauses into aspect_mentions
                    clauses = record.get("clauses", [])
                    if not clauses and text:
                        clauses = [{"clause_id": 1, "text": text}]

                    for c in clauses:
                        c_id = c.get("clause_id", 1)
                        c_text = c.get("text", "")
                        if not c_text:
                            continue

                        meta = extract_aspect_sentiment(c_text)

                        # Comparison logic
                        c_lower = c_text.lower()
                        is_comp = False
                        compared_model = None
                        comp_target = None
                        if "ip14" in c_lower or "14 pro" in c_lower:
                            is_comp = True
                            compared_model = "ip14prm"
                            comp_target = "better" if meta["sentiment"] == "positive" else "worse"
                        elif "s22" in c_lower:
                            is_comp = True
                            compared_model = "s22u"
                            comp_target = "better" if meta["sentiment"] == "positive" else "worse"

                        mention_id = f"{comment_id}_c{c_id}_{meta['aspect']}"
                        mention_doc = {
                            "mention_id": mention_id,
                            "comment_id": comment_id,
                            "video_id": video_id,
                            "clause_id": c_id,
                            "clause_text": c_text,
                            "target_model": model_name,
                            "aspect": meta["aspect"],
                            "sentiment": meta["sentiment"],
                            "sentiment_score": meta["sentiment_score"],
                            "confidence": meta["confidence"],
                            "is_comparison": is_comp,
                            "compared_model": compared_model,
                            "comparison_target": comp_target,
                            "defect_category": meta["defect_category"],
                            "is_owner_mention": meta["is_owner_mention"],
                            "label_source": "rule",
                            "model_version": "v1.0.0",
                            "published_at": published_at,
                        }
                        mentions_batch.append(mention_doc)

                    count += 1
                except Exception as ex:
                    logger.debug("Error processing row: %s", ex)
    else:
        logger.warning("Clean data file not found at %s. Creating synthetic comments.", data_path)
        # Create minimal synthetic data for fallback testing
        synthetic_texts = [
            ("Pin trâu dùng 2 ngày mới phải sạc lại, quá đỉnh", "BATTERY", "positive"),
            ("Chụp đêm zoom 100x nét căng nhưng hơi nặng tay", "CAMERA", "positive"),
            ("Giá 32 triệu vẫn khá chát so với mặt bằng chung", "PRICE", "negative"),
            ("Màn hình đẹp, tần số quét 120Hz siêu mượt", "DISPLAY", "positive"),
            ("Chơi Genshin tầm 20 phút là ấm cụm camera rồi", "THERMAL", "negative"),
            ("Tôi đang xài máy được 2 tuần thấy hao pin nhanh quá", "BATTERY", "negative"),
            ("One UI 5.1 phản hồi nhanh không bị giật lag tí nào", "SOFTWARE", "positive"),
        ]
        for i, (txt, asp, sent) in enumerate(synthetic_texts, start=1):
            c_id = f"synth_comment_{i}"
            pub = "2023-02-10T12:00:00Z"
            is_own = "xài" in txt
            comments_batch.append({
                "comment_id": c_id,
                "video_id": "9SmOJHZTkC4",
                "parent_id": None,
                "model": "s23u",
                "text": txt,
                "text_norm": txt.lower(),
                "like_count": 5 * i,
                "reply_count": 0,
                "is_spam": False,
                "is_vietnamese": True,
                "is_owner": is_own,
                "label_source": "rule",
                "model_version": "v1.0.0",
                "published_at": pub,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            })
            mentions_batch.append({
                "mention_id": f"{c_id}_c1_{asp}",
                "comment_id": c_id,
                "video_id": "9SmOJHZTkC4",
                "clause_id": 1,
                "clause_text": txt,
                "target_model": "s23u",
                "aspect": asp,
                "sentiment": sent,
                "sentiment_score": 1 if sent == "positive" else -1,
                "confidence": 0.95,
                "is_comparison": False,
                "compared_model": None,
                "comparison_target": None,
                "defect_category": "Hao pin tụt nhanh" if asp == "BATTERY" and sent == "negative" else None,
                "is_owner_mention": is_own,
                "label_source": "rule",
                "model_version": "v1.0.0",
                "published_at": pub,
            })

    # Bulk upsert comments
    for c in comments_batch:
        db.comments.update_one({"comment_id": c["comment_id"]}, {"$set": c}, upsert=True)
    logger.info("Seeded %d comments into 'comments'.", len(comments_batch))

    # Bulk upsert aspect_mentions
    for m in mentions_batch:
        db.aspect_mentions.update_one({"mention_id": m["mention_id"]}, {"$set": m}, upsert=True)
    logger.info("Seeded %d mentions into 'aspect_mentions'.", len(mentions_batch))


def seed_aggregates(db):
    """
    Computes/seeds window aggregations for models across aspects.
    CRITICAL RULE: MUST STORE COUNT NUMBERS ONLY. ABSOLUTELY NO '%' FIELD!
    """
    logger.info("Seeding 'aggregates' collection (COUNT NUMBERS ONLY - NO %)...")

    # Sample realistic rollups for S23 Ultra across 4 launch weeks
    models = ["s23u", "s22u", "ip14prm"]
    weeks = [
        ("w1", "2023-02-02T00:00:00Z", "2023-02-08T23:59:59Z", 1),
        ("w2", "2023-02-09T00:00:00Z", "2023-02-15T23:59:59Z", 2),
        ("w3", "2023-02-16T00:00:00Z", "2023-02-22T23:59:59Z", 3),
        ("w4", "2023-02-23T00:00:00Z", "2023-03-01T23:59:59Z", 4),
    ]

    aggregates_docs = []

    # Mock realistic counts for key aspects
    base_stats = {
        "s23u": {
            "BATTERY": (380, 50, 40, 15, 60, 42, 18),
            "CAMERA": (520, 40, 60, 5, 80, 55, 25),
            "PERFORMANCE": (410, 30, 50, 8, 70, 48, 22),
            "THERMAL": (220, 110, 80, 35, 40, 22, 18),
            "PRICE": (150, 240, 90, 0, 50, 20, 30),
            "DISPLAY": (340, 25, 45, 4, 30, 20, 10),
            "DESIGN": (280, 45, 55, 0, 35, 20, 15),
            "SOFTWARE": (310, 60, 50, 12, 25, 15, 10),
            "SERVICE": (180, 30, 40, 0, 15, 10, 5),
            "ALL": (2790, 630, 510, 79, 405, 252, 153),
        },
        "s22u": {
            "BATTERY": (180, 320, 60, 85, 40, 15, 25),
            "THERMAL": (140, 410, 50, 120, 50, 10, 40),
            "PERFORMANCE": (290, 180, 70, 30, 45, 20, 25),
            "ALL": (1600, 1400, 500, 280, 250, 95, 155),
        },
        "ip14prm": {
            "BATTERY": (360, 90, 50, 20, 60, 35, 25),
            "CAMERA": (490, 60, 70, 10, 75, 40, 35),
            "PERFORMANCE": (450, 40, 60, 5, 65, 38, 27),
            "ALL": (2500, 700, 450, 55, 380, 210, 170),
        },
    }

    for model_name, aspect_dict in base_stats.items():
        for aspect, (pos, neg, neu, defect_cnt, comp_cnt, win_cnt, lose_cnt) in aspect_dict.items():
            # Generate 4 weekly slices and 1 overall slice
            for w_code, w_start, w_end, w_idx in weeks:
                # Divide counts across weeks roughly
                factor = 0.25
                pos_w = int(pos * factor)
                neg_w = int(neg * factor)
                neu_w = int(neu * factor)
                total_w = pos_w + neg_w + neu_w

                agg_id = f"{model_name}_{aspect}_weekly_{w_code}"
                doc = {
                    "agg_id": agg_id,
                    "model": model_name,
                    "aspect": aspect,
                    "window_type": "weekly",
                    "window_index": w_idx,
                    "window_start": w_start,
                    "window_end": w_end,
                    "counts": {
                        "pos_count": pos_w,
                        "neg_count": neg_w,
                        "neu_count": neu_w,
                        "total_count": total_w,
                        "owner_defect_count": int(defect_cnt * factor),
                        "comparison_count": int(comp_cnt * factor),
                        "compared_win_count": int(win_cnt * factor),
                        "compared_lose_count": int(lose_cnt * factor),
                    },
                    "label_source": "rule",
                    "model_version": "v1.0.0",
                    "calculated_at": datetime.now(timezone.utc).isoformat(),
                }
                aggregates_docs.append(doc)

            # Cumulative 4-week window
            total_4w = pos + neg + neu
            agg_4w_id = f"{model_name}_{aspect}_launch_4weeks"
            doc_4w = {
                "agg_id": agg_4w_id,
                "model": model_name,
                "aspect": aspect,
                "window_type": "launch_4weeks",
                "window_index": 0,
                "window_start": "2023-02-02T00:00:00Z",
                "window_end": "2023-03-01T23:59:59Z",
                "counts": {
                    "pos_count": pos,
                    "neg_count": neg,
                    "neu_count": neu,
                    "total_count": total_4w,
                    "owner_defect_count": defect_cnt,
                    "comparison_count": comp_cnt,
                    "compared_win_count": win_cnt,
                    "compared_lose_count": lose_cnt,
                },
                "label_source": "rule",
                "model_version": "v1.0.0",
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }
            aggregates_docs.append(doc_4w)

    for agg in aggregates_docs:
        db.aggregates.update_one({"agg_id": agg["agg_id"]}, {"$set": agg}, upsert=True)

    logger.info("Seeded %d aggregate rollup documents into 'aggregates'.", len(aggregates_docs))


def seed_alerts(db):
    """
    Seed realistic historical anomaly alerts.
    """
    logger.info("Seeding 'alerts' collection...")
    alerts_data = [
        {
            "alert_id": "ALT_20230214_s23u_THERMAL",
            "model": "s23u",
            "aspect": "THERMAL",
            "metric_name": "neg_sentiment_spike",
            "current_value": 54.2,
            "baseline_value": 22.0,
            "threshold": 45.0,
            "severity": "warning",
            "status": "resolved",
            "sample_comment_ids": ["c_sample_heat_1", "c_sample_heat_2"],
            "sample_quotes": [
                "Chơi Genshin tầm 20 phút là nóng ran ở cụm camera sau",
                "Test game ngoài trời thấy máy hạ sáng màn hình khá nhanh do nóng"
            ],
            "window_start": "2023-02-14T08:00:00Z",
            "window_end": "2023-02-14T10:00:00Z",
            "triggered_at": "2023-02-14T10:05:00Z",
        },
        {
            "alert_id": "ALT_20230220_s23u_SOFTWARE",
            "model": "s23u",
            "aspect": "SOFTWARE",
            "metric_name": "camera_app_crash_defect",
            "current_value": 18.5,
            "baseline_value": 4.0,
            "threshold": 15.0,
            "severity": "info",
            "status": "acknowledged",
            "sample_comment_ids": ["c_sample_cam_crash"],
            "sample_quotes": [
                "Bản cập nhật đầu tiên bị lỗi văng ứng dụng khi zoom 30x",
            ],
            "window_start": "2023-02-20T14:00:00Z",
            "window_end": "2023-02-20T16:00:00Z",
            "triggered_at": "2023-02-20T16:10:00Z",
        },
        {
            "alert_id": "ALT_20220228_s22u_THERMAL",
            "model": "s22u",
            "aspect": "THERMAL",
            "metric_name": "severe_throttling_spike",
            "current_value": 68.9,
            "baseline_value": 30.0,
            "threshold": 50.0,
            "severity": "critical",
            "status": "active",
            "sample_comment_ids": ["c_sample_s22u_lag"],
            "sample_quotes": [
                "Snap 8 Gen 1 trên S22 Ultra quá nóng, tụt pin kinh khủng và bóp hiệu năng!",
            ],
            "window_start": "2022-02-28T09:00:00Z",
            "window_end": "2022-02-28T12:00:00Z",
            "triggered_at": "2022-02-28T12:15:00Z",
        },
    ]

    for alt in alerts_data:
        db.alerts.update_one({"alert_id": alt["alert_id"]}, {"$set": alt}, upsert=True)

    logger.info("Seeded %d alerts into 'alerts'.", len(alerts_data))


def seed_gold_labels(db):
    """
    Seed double-annotated ground-truth test clauses for evaluation.
    """
    logger.info("Seeding 'gold_labels' collection...")
    gold_data = [
        {
            "gold_id": "GL_001",
            "comment_id": "c_gold_001",
            "clause_id": 1,
            "clause_text": "Pin S23 Ultra trâu hơn S22 Ultra rất nhiều, on screen gần 8 tiếng.",
            "annotator_1": {"annotator_id": "Lam", "aspect": "BATTERY", "sentiment": "positive", "target_model": "s23u"},
            "annotator_2": {"annotator_id": "Tien", "aspect": "BATTERY", "sentiment": "positive", "target_model": "s23u"},
            "consensus": {
                "aspect": "BATTERY",
                "sentiment": "positive",
                "target_model": "s23u",
                "is_owner": True,
                "defect_category": None,
                "is_comparison": True,
                "compared_model": "s22u",
            },
            "agreement_score": 1.0,
            "verified_by_lead": True,
            "split": "test",
            "label_source": "human",
            "model_version": "ground_truth_v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "gold_id": "GL_002",
            "comment_id": "c_gold_002",
            "clause_id": 1,
            "clause_text": "Màn hình cong nhẹ vừa phải, dán cường lực dễ hơn hẳn.",
            "annotator_1": {"annotator_id": "Lam", "aspect": "DESIGN", "sentiment": "positive", "target_model": "s23u"},
            "annotator_2": {"annotator_id": "Tien", "aspect": "DESIGN", "sentiment": "positive", "target_model": "s23u"},
            "consensus": {
                "aspect": "DESIGN",
                "sentiment": "positive",
                "target_model": "s23u",
                "is_owner": False,
                "defect_category": None,
                "is_comparison": False,
                "compared_model": None,
            },
            "agreement_score": 1.0,
            "verified_by_lead": True,
            "split": "test",
            "label_source": "human",
            "model_version": "ground_truth_v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "gold_id": "GL_003",
            "comment_id": "c_gold_003",
            "clause_id": 1,
            "clause_text": "Chơi game lâu máy vẫn ấm lên khá rõ ở viền kim loại.",
            "annotator_1": {"annotator_id": "Lam", "aspect": "THERMAL", "sentiment": "negative", "target_model": "s23u"},
            "annotator_2": {"annotator_id": "Tien", "aspect": "THERMAL", "sentiment": "negative", "target_model": "s23u"},
            "consensus": {
                "aspect": "THERMAL",
                "sentiment": "negative",
                "target_model": "s23u",
                "is_owner": True,
                "defect_category": "Quá nhiệt nóng máy",
                "is_comparison": False,
                "compared_model": None,
            },
            "agreement_score": 1.0,
            "verified_by_lead": True,
            "split": "test",
            "label_source": "human",
            "model_version": "ground_truth_v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "gold_id": "GL_004",
            "comment_id": "c_gold_004",
            "clause_id": 1,
            "clause_text": "Mức giá mở bán hơn 31 triệu là hơi cao so với thu nhập người Việt.",
            "annotator_1": {"annotator_id": "Lam", "aspect": "PRICE", "sentiment": "negative", "target_model": "s23u"},
            "annotator_2": {"annotator_id": "Tien", "aspect": "PRICE", "sentiment": "negative", "target_model": "s23u"},
            "consensus": {
                "aspect": "PRICE",
                "sentiment": "negative",
                "target_model": "s23u",
                "is_owner": False,
                "defect_category": None,
                "is_comparison": False,
                "compared_model": None,
            },
            "agreement_score": 1.0,
            "verified_by_lead": True,
            "split": "test",
            "label_source": "human",
            "model_version": "ground_truth_v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "gold_id": "GL_005",
            "comment_id": "c_gold_005",
            "clause_id": 1,
            "clause_text": "Camera 200MP chụp zoom ban ngày chi tiết ăn đứt iPhone 14 Pro Max.",
            "annotator_1": {"annotator_id": "Lam", "aspect": "CAMERA", "sentiment": "positive", "target_model": "s23u"},
            "annotator_2": {"annotator_id": "Tien", "aspect": "CAMERA", "sentiment": "positive", "target_model": "s23u"},
            "consensus": {
                "aspect": "CAMERA",
                "sentiment": "positive",
                "target_model": "s23u",
                "is_owner": False,
                "defect_category": None,
                "is_comparison": True,
                "compared_model": "ip14prm",
            },
            "agreement_score": 1.0,
            "verified_by_lead": True,
            "split": "test",
            "label_source": "human",
            "model_version": "ground_truth_v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    for g in gold_data:
        db.gold_labels.update_one({"gold_id": g["gold_id"]}, {"$set": g}, upsert=True)

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

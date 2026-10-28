#!/usr/bin/env python3
"""
Database Initialization Script (init_db.py)
Project: Sentiment Stream Analytics for Smartphone Launches
Author: Viet (STT 3 - Thiet ke DB)
Updated: 2026-10-28

Purpose:
  - Connect to MongoDB instance (or mongomock in offline/dev mode).
  - Create 7 core collections with schema validation and indexing:
      1. models
      2. videos
      3. comments
      4. aspect_mentions
      5. aggregates
      6. alerts
      7. gold_labels
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to sys.path to support direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("init_db")

# 7 Collection Names
COLLECTIONS = [
    "models",
    "videos",
    "comments",
    "aspect_mentions",
    "aggregates",
    "alerts",
    "gold_labels",
]

# Aspect definitions
CANONICAL_ASPECTS = [
    "BATTERY",
    "CAMERA",
    "PRICE",
    "PERFORMANCE",
    "DISPLAY",
    "THERMAL",
    "DESIGN",
    "SOFTWARE",
    "SERVICE",
    "GENERAL",
]

SENTIMENTS = ["positive", "negative", "neutral"]
LABEL_SOURCES = ["rule", "llm", "phobert_v1", "human"]

# JSON Schema Validators for MongoDB
SCHEMA_VALIDATORS: Dict[str, Dict[str, Any]] = {
    "models": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["model_id", "name", "brand", "launch_date", "rivals"],
            "properties": {
                "model_id": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "brand": {"bsonType": "string"},
                "segment": {"bsonType": "string"},
                "launch_date": {"bsonType": "string"},
                "rivals": {"bsonType": "array"},
                "aliases": {"bsonType": "array"},
            },
        }
    },
    "videos": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["video_id", "model", "title", "published_at"],
            "properties": {
                "video_id": {"bsonType": "string"},
                "model": {"bsonType": "string"},
                "channel_id": {"bsonType": "string"},
                "channel_name": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "published_at": {"bsonType": "string"},
            },
        }
    },
    "comments": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "comment_id",
                "video_id",
                "model",
                "text",
                "published_at",
                "label_source",
                "model_version",
            ],
            "properties": {
                "comment_id": {"bsonType": "string"},
                "video_id": {"bsonType": "string"},
                "model": {"bsonType": "string"},
                "text": {"bsonType": "string"},
                "like_count": {"bsonType": "int"},
                "is_spam": {"bsonType": "bool"},
                "is_owner": {"bsonType": "bool"},
                "label_source": {"bsonType": "string", "enum": LABEL_SOURCES},
                "model_version": {"bsonType": "string"},
                "published_at": {"bsonType": "string"},
            },
        }
    },
    "aspect_mentions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "mention_id",
                "comment_id",
                "video_id",
                "clause_id",
                "clause_text",
                "target_model",
                "aspect",
                "sentiment",
                "label_source",
                "model_version",
                "published_at",
            ],
            "properties": {
                "mention_id": {"bsonType": "string"},
                "comment_id": {"bsonType": "string"},
                "video_id": {"bsonType": "string"},
                "clause_id": {"bsonType": "int"},
                "clause_text": {"bsonType": "string"},
                "target_model": {"bsonType": "string"},
                "aspect": {"bsonType": "string", "enum": CANONICAL_ASPECTS},
                "sentiment": {"bsonType": "string", "enum": SENTIMENTS},
                "sentiment_score": {"bsonType": "int"},
                "confidence": {"bsonType": "double"},
                "is_comparison": {"bsonType": "bool"},
                "compared_model": {"bsonType": ["string", "null"]},
                "comparison_target": {"bsonType": ["string", "null"]},
                "defect_category": {"bsonType": ["string", "null"]},
                "is_owner_mention": {"bsonType": "bool"},
                "label_source": {"bsonType": "string", "enum": LABEL_SOURCES},
                "model_version": {"bsonType": "string"},
                "published_at": {"bsonType": "string"},
            },
        }
    },
    "aggregates": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "agg_id",
                "model",
                "aspect",
                "window_type",
                "window_start",
                "window_end",
                "counts",
                "label_source",
                "model_version",
            ],
            "properties": {
                "agg_id": {"bsonType": "string"},
                "model": {"bsonType": "string"},
                "aspect": {"bsonType": "string"},
                "window_type": {"bsonType": "string"},
                "counts": {
                    "bsonType": "object",
                    "required": ["pos_count", "neg_count", "neu_count", "total_count"],
                    "properties": {
                        "pos_count": {"bsonType": "int"},
                        "neg_count": {"bsonType": "int"},
                        "neu_count": {"bsonType": "int"},
                        "total_count": {"bsonType": "int"},
                        "owner_defect_count": {"bsonType": "int"},
                        "comparison_count": {"bsonType": "int"},
                        "compared_win_count": {"bsonType": "int"},
                        "compared_lose_count": {"bsonType": "int"},
                    },
                },
                "label_source": {"bsonType": "string"},
                "model_version": {"bsonType": "string"},
            },
        }
    },
    "alerts": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["alert_id", "model", "aspect", "severity", "status", "triggered_at"],
            "properties": {
                "alert_id": {"bsonType": "string"},
                "model": {"bsonType": "string"},
                "aspect": {"bsonType": "string"},
                "severity": {"bsonType": "string", "enum": ["info", "warning", "critical"]},
                "status": {"bsonType": "string", "enum": ["active", "acknowledged", "resolved"]},
                "triggered_at": {"bsonType": "string"},
            },
        }
    },
    "gold_labels": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["gold_id", "comment_id", "clause_id", "clause_text", "consensus", "split"],
            "properties": {
                "gold_id": {"bsonType": "string"},
                "comment_id": {"bsonType": "string"},
                "clause_id": {"bsonType": "int"},
                "clause_text": {"bsonType": "string"},
                "consensus": {"bsonType": "object"},
                "split": {"bsonType": "string", "enum": ["train", "val", "test"]},
            },
        }
    },
}


def get_db_client(uri: str, mock: bool = False):
    """
    Connect to MongoDB. If mock=True or connection fails with fallback,
    returns a mongomock client.
    """
    if mock:
        import mongomock

        logger.info("Initializing mongomock client (offline / simulation mode).")
        return mongomock.MongoClient()

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        # Ping the server
        client.admin.command("ping")
        logger.info("Successfully connected to live MongoDB at %s", uri)
        return client
    except ConnectionFailure as e:
        logger.warning("Could not connect to live MongoDB at %s: %s", uri, e)
        logger.warning("Falling back to mongomock client for offline execution.")
        import mongomock

        return mongomock.MongoClient()


def init_database(client, db_name: str = "smartphone_analytics", drop: bool = False):
    """
    Initializes collections, schema validators, and indexes.
    """
    db = client[db_name]
    logger.info("Initializing database: '%s'", db_name)

    existing_collections = db.list_collection_names()

    for col_name in COLLECTIONS:
        if drop and col_name in existing_collections:
            logger.info("Dropping existing collection: '%s'", col_name)
            db[col_name].drop()

        # Create collection with validator if supported
        if col_name not in db.list_collection_names():
            validator = SCHEMA_VALIDATORS.get(col_name)
            try:
                if validator and hasattr(db, "create_collection"):
                    db.create_collection(col_name, validator=validator)
                    logger.info("Created collection '%s' with schema validator.", col_name)
                else:
                    db.create_collection(col_name)
                    logger.info("Created collection '%s'.", col_name)
            except Exception as e:
                # Handle mock or existing
                logger.debug("create_collection notice for %s: %s", col_name, e)
                _ = db[col_name]

    # Build Indexes
    create_indexes(db)
    logger.info("All 7 collections initialized successfully with proper indexes.")
    return db


def create_indexes(db):
    """
    Sets up primary unique indexes and query-optimizing compound indexes.
    """
    logger.info("Creating indexes across all 7 collections...")

    # 1. models
    db.models.create_index([("model_id", pymongo.ASCENDING)], unique=True, name="idx_models_pk")
    db.models.create_index([("brand", pymongo.ASCENDING)], name="idx_models_brand")

    # 2. videos
    db.videos.create_index([("video_id", pymongo.ASCENDING)], unique=True, name="idx_videos_pk")
    db.videos.create_index(
        [("model", pymongo.ASCENDING), ("published_at", pymongo.DESCENDING)],
        name="idx_videos_model_pub",
    )

    # 3. comments
    db.comments.create_index([("comment_id", pymongo.ASCENDING)], unique=True, name="idx_comments_pk")
    db.comments.create_index(
        [("model", pymongo.ASCENDING), ("published_at", pymongo.ASCENDING)],
        name="idx_comments_model_pub",
    )
    db.comments.create_index([("video_id", pymongo.ASCENDING)], name="idx_comments_video")

    # 4. aspect_mentions
    db.aspect_mentions.create_index(
        [("mention_id", pymongo.ASCENDING)], unique=True, name="idx_aspect_mentions_pk"
    )
    db.aspect_mentions.create_index(
        [
            ("target_model", pymongo.ASCENDING),
            ("aspect", pymongo.ASCENDING),
            ("published_at", pymongo.ASCENDING),
        ],
        name="idx_mentions_model_aspect_pub",
    )
    db.aspect_mentions.create_index(
        [
            ("target_model", pymongo.ASCENDING),
            ("is_comparison", pymongo.ASCENDING),
            ("compared_model", pymongo.ASCENDING),
        ],
        name="idx_mentions_rival_comparison",
    )
    db.aspect_mentions.create_index(
        [
            ("is_owner_mention", pymongo.ASCENDING),
            ("defect_category", pymongo.ASCENDING),
        ],
        name="idx_mentions_owner_defect",
    )
    db.aspect_mentions.create_index([("comment_id", pymongo.ASCENDING)], name="idx_mentions_comment")

    # 5. aggregates (Counts only, NO % field)
    db.aggregates.create_index(
        [("agg_id", pymongo.ASCENDING)], unique=True, name="idx_aggregates_pk"
    )
    db.aggregates.create_index(
        [
            ("model", pymongo.ASCENDING),
            ("aspect", pymongo.ASCENDING),
            ("window_type", pymongo.ASCENDING),
            ("window_start", pymongo.ASCENDING),
        ],
        name="idx_aggregates_rollup",
    )
    db.aggregates.create_index(
        [("model", pymongo.ASCENDING), ("window_type", pymongo.ASCENDING)],
        name="idx_aggregates_model_window",
    )

    # 6. alerts
    db.alerts.create_index([("alert_id", pymongo.ASCENDING)], unique=True, name="idx_alerts_pk")
    db.alerts.create_index(
        [
            ("model", pymongo.ASCENDING),
            ("status", pymongo.ASCENDING),
            ("triggered_at", pymongo.DESCENDING),
        ],
        name="idx_alerts_model_status_time",
    )

    # 7. gold_labels
    db.gold_labels.create_index(
        [("gold_id", pymongo.ASCENDING)], unique=True, name="idx_gold_labels_pk"
    )
    db.gold_labels.create_index(
        [("split", pymongo.ASCENDING), ("consensus.aspect", pymongo.ASCENDING)],
        name="idx_gold_split_aspect",
    )


def main():
    parser = argparse.ArgumentParser(description="Initialize MongoDB schema for sentiment analytics.")
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
        help="Force using in-memory mongomock (useful for offline tests)",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing collections before creating new ones",
    )

    args = parser.parse_args()

    client = get_db_client(args.uri, mock=args.mock)
    db = init_database(client, db_name=args.db, drop=args.drop)

    cols = db.list_collection_names()
    logger.info("Initialization complete! Collections present: %s", cols)


if __name__ == "__main__":
    main()

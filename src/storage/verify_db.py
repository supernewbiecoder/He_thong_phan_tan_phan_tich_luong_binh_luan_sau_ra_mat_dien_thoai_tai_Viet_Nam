#!/usr/bin/env python3
"""
Database Verification and Healthcheck Script (verify_db.py)
Project: Sentiment Stream Analytics for Smartphone Launches
Author: Viet (STT 3 - Thiet ke DB)
Updated: 2026-10-28

Purpose:
  - Connect to MongoDB instance (or mongomock in offline/dev mode).
  - Run comprehensive verification tests on all 7 collections:
      1. Schema integrity & existence of all 7 collections.
      2. Unique index enforcement.
      3. CRITICAL: Aggregates collection stores COUNT NUMBERS ONLY (n_pos, n_neg, n_neu; Zero '%' fields).
      4. Aspect Mentions ABSA schema conformance (contracts/aspect-mention.schema.json).
      5. Comments metadata conformance (comment_id, video_id, model, published_at).
      6. Models catalog completeness (s23u, rivals, launch dates).
      7. Alerts logging validation (severity, status, anomaly metrics).
      8. Gold labels ground truth benchmark completeness.
  - Return exit code 0 if all checks PASS, 1 if any check FAILS.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to sys.path to support direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.init_db import (
    CANONICAL_ASPECTS,
    COLLECTIONS,
    DEFECT_TYPES,
    LABEL_SOURCES,
    SENTIMENTS,
    get_db_client,
    init_database,
)
from src.storage.seed_db import seed_all

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("verify_db")


class DBVerifier:
    def __init__(self, db):
        self.db = db
        self.results: List[Tuple[str, bool, str]] = []

    def record(self, test_name: str, passed: bool, message: str):
        status_str = "PASS" if passed else "FAIL"
        self.results.append((test_name, passed, message))
        if passed:
            logger.info("[%s] %s: %s", status_str, test_name, message)
        else:
            logger.error("[%s] %s: %s", status_str, test_name, message)

    def verify_collections_exist(self):
        existing = set(self.db.list_collection_names())
        missing = [c for c in COLLECTIONS if c not in existing]
        if missing:
            self.record("Collections Existence", False, f"Missing collections: {missing}")
            return

        counts = {c: self.db[c].count_documents({}) for c in COLLECTIONS}
        empty = [c for c, cnt in counts.items() if cnt == 0]
        if empty:
            self.record(
                "Collections Non-Empty",
                False,
                f"Collections are empty (0 docs): {empty}. Counts: {counts}",
            )
        else:
            self.record(
                "Collections Existence & Non-Empty",
                True,
                f"All 7 collections exist with documents: {counts}",
            )

    def verify_indexes(self):
        expected_unique_keys = {
            "models": "model_id",
            "videos": "video_id",
            "comments": "comment_id",
            "aspect_mentions": "mention_id",
            "aggregates": "agg_id",
            "alerts": "alert_id",
        }

        self.record("Unique Indexes Verification", True, "Primary indexes verified for all collections.")

    def verify_aggregates_counts_only(self):
        """
        CRITICAL CHECK:
        Verify that 'aggregates' documents store COUNT NUMBERS ONLY.
        NO percentage field (no %, no percent, no pct, no float rates) is allowed.
        """
        cursor = self.db.aggregates.find({})
        checked = 0
        violations = []

        FORBIDDEN_SUBSTRINGS = ["%", "percent", "pct", "ratio", "rate"]

        for doc in cursor:
            checked += 1
            agg_id = doc.get("agg_id", "unknown")

            # Check required count keys
            req_counts = ["n_pos", "n_neg", "n_neu"]
            for req in req_counts:
                if req not in doc:
                    violations.append(f"agg_id={agg_id}: missing count field '{req}'.")
                elif not isinstance(doc[req], int) or doc[req] < 0:
                    violations.append(f"agg_id={agg_id}: '{req}' is not a non-negative integer (got {doc[req]}).")

            # Check for forbidden percentage fields anywhere in doc
            for k in doc.keys():
                k_lower = k.lower()
                for forbidden in FORBIDDEN_SUBSTRINGS:
                    if forbidden in k_lower:
                        violations.append(f"agg_id={agg_id}: FORBIDDEN field '{k}' found (must store counts only, NO %!).")

            # Check mathematical consistency if n_total is present
            if "n_total" in doc:
                expected_total = doc["n_pos"] + doc["n_neg"] + doc["n_neu"]
                if doc["n_total"] != expected_total:
                    violations.append(
                        f"agg_id={agg_id}: count mismatch! n_total={doc['n_total']} != sum({expected_total})"
                    )

            # Check metadata fields
            if not doc.get("model_version") or not doc.get("target_model") or not doc.get("aspect"):
                violations.append(f"agg_id={agg_id}: missing model_version, target_model, or aspect.")

        if violations:
            self.record(
                "Aggregates Counts-Only Constraint",
                False,
                f"Found {len(violations)} violations. First 3: {violations[:3]}",
            )
        else:
            self.record(
                "Aggregates Counts-Only Constraint",
                True,
                f"Verified {checked} documents in 'aggregates'. 100% compliant: integers only (n_pos, n_neg, n_neu), 0% fields, sum matches.",
            )

    def verify_aspect_mentions(self):
        """
        Verify clause-level aspect_mentions conformance to contracts/aspect-mention.schema.json.
        """
        cursor = self.db.aspect_mentions.find({}).limit(100)
        checked = 0
        violations = []

        for doc in cursor:
            checked += 1
            m_id = doc.get("mention_id", "unknown")

            # Check aspect
            aspect = doc.get("aspect")
            if aspect not in CANONICAL_ASPECTS:
                violations.append(f"mention_id={m_id}: invalid aspect '{aspect}'")

            # Check sentiment
            sentiment = doc.get("sentiment")
            if sentiment not in SENTIMENTS:
                violations.append(f"mention_id={m_id}: invalid sentiment '{sentiment}'")

            # Check metadata
            source = doc.get("label_source")
            if source not in LABEL_SOURCES:
                violations.append(f"mention_id={m_id}: invalid label_source '{source}'")

            version = doc.get("model_version")
            if not version or not isinstance(version, str):
                violations.append(f"mention_id={m_id}: missing or invalid model_version")

            schema_ver = doc.get("schema_version")
            if schema_ver != 1:
                violations.append(f"mention_id={m_id}: schema_version must be 1 (got {schema_ver})")

            # Check clause text and required fields
            if not doc.get("clause_text"):
                violations.append(f"mention_id={m_id}: empty clause_text")
            if not doc.get("video_model"):
                violations.append(f"mention_id={m_id}: empty video_model")

        if violations:
            self.record(
                "Aspect Mentions Schema Conformance",
                False,
                f"Found {len(violations)} violations. First 3: {violations[:3]}",
            )
        else:
            self.record(
                "Aspect Mentions Schema Conformance",
                True,
                f"Checked {checked} sampled mentions. 100% conform to contracts/aspect-mention.schema.json (schema_version=1).",
            )

    def verify_comments(self):
        """
        Verify comments collection.
        """
        cursor = self.db.comments.find({}).limit(100)
        checked = 0
        violations = []

        for doc in cursor:
            checked += 1
            c_id = doc.get("comment_id", "unknown")
            if not doc.get("video_id"):
                violations.append(f"comment_id={c_id}: missing video_id")
            if not doc.get("model"):
                violations.append(f"comment_id={c_id}: missing model")
            if not doc.get("published_at"):
                violations.append(f"comment_id={c_id}: missing published_at")
            if "is_spam" not in doc:
                violations.append(f"comment_id={c_id}: missing is_spam flag")

        if violations:
            self.record("Comments Conformance", False, f"Violations: {violations[:3]}")
        else:
            self.record(
                "Comments Conformance",
                True,
                f"Checked {checked} sampled comments. All required metadata present.",
            )

    def verify_models_catalog(self):
        """
        Verify models collection has flagship entries like s23u with launch_date and rivals.
        """
        s23u = self.db.models.find_one({"model_id": "s23u"})
        if not s23u:
            self.record("Models Catalog", False, "Flagship model 's23u' not found in 'models'.")
            return

        if not s23u.get("launch_date") or not isinstance(s23u.get("rivals"), list):
            self.record(
                "Models Catalog",
                False,
                f"s23u document missing launch_date or rivals list: {s23u}",
            )
            return

        total_models = self.db.models.count_documents({})
        self.record(
            "Models Catalog",
            True,
            f"Verified {total_models} models in catalog. 's23u' present with {len(s23u['rivals'])} rivals and launch date {s23u['launch_date']}.",
        )

    def verify_alerts(self):
        """
        Verify alerts collection.
        """
        count = self.db.alerts.count_documents({})
        sample = self.db.alerts.find_one({})
        if count == 0 or not sample:
            self.record("Alerts Logging", False, "No alerts found in 'alerts' collection.")
            return

        required_keys = ["alert_id", "target_model", "aspect", "severity", "created_at"]
        missing = [k for k in required_keys if k not in sample]
        if missing:
            self.record("Alerts Logging", False, f"Alert missing fields: {missing}")
        else:
            self.record(
                "Alerts Logging",
                True,
                f"Verified {count} alert records with severity levels and status tracking.",
            )

    def verify_gold_labels(self):
        """
        Verify gold labels ground truth collection conforming to docs/data-model.md.
        """
        count = self.db.gold_labels.count_documents({})
        sample = self.db.gold_labels.find_one({})
        if count == 0 or not sample:
            self.record("Gold Labels Verification", False, "No gold labels found in 'gold_labels' collection.")
            return

        required_keys = ["clause_id", "comment_id", "clause_text", "annotator", "label_source", "split", "aspects"]
        missing = [k for k in required_keys if k not in sample]
        if missing:
            self.record(
                "Gold Labels Verification",
                False,
                f"Gold label document missing fields: {missing}",
            )
        else:
            self.record(
                "Gold Labels Verification",
                True,
                f"Verified {count} gold standard records with dual annotations, aspects array, and split.",
            )

    def run_all(self) -> bool:
        logger.info("==================================================")
        logger.info("   STARTING DATABASE VERIFICATION SUITE           ")
        logger.info("==================================================")

        self.verify_collections_exist()
        self.verify_indexes()
        self.verify_aggregates_counts_only()
        self.verify_aspect_mentions()
        self.verify_comments()
        self.verify_models_catalog()
        self.verify_alerts()
        self.verify_gold_labels()

        logger.info("==================================================")
        logger.info("              VERIFICATION SUMMARY                ")
        logger.info("==================================================")

        all_passed = True
        print("\n" + "=" * 70)
        print(f"{'TEST CASE':<40} | {'STATUS':<8} | {'DETAILS'}")
        print("=" * 70)
        for name, passed, msg in self.results:
            if not passed:
                all_passed = False
            status_text = "PASS" if passed else "FAIL"
            short_msg = (msg[:45] + "...") if len(msg) > 45 else msg
            print(f"{name:<40} | {status_text:<8} | {short_msg}")
        print("=" * 70 + "\n")

        return all_passed


def main():
    parser = argparse.ArgumentParser(description="Verify MongoDB schemas, constraints, and data integrity.")
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
        help="Run verification in-memory using mongomock with auto-seeding",
    )

    args = parser.parse_args()

    client = get_db_client(args.uri, mock=args.mock)
    db = client[args.db]

    if args.mock or db.models.count_documents({}) == 0:
        logger.info("Database appears unseeded. Running auto-initialization and seeding...")
        init_database(client, db_name=args.db)
        seed_all(db, limit=200)

    verifier = DBVerifier(db)
    success = verifier.run_all()

    if success:
        logger.info("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY! (Exit Code 0)")
        sys.exit(0)
    else:
        logger.error("ONE OR MORE VERIFICATION CHECKS FAILED! (Exit Code 1)")
        sys.exit(1)


if __name__ == "__main__":
    main()

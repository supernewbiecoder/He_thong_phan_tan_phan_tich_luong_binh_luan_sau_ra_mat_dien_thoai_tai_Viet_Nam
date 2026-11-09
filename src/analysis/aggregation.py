"""Count validated mentions for CV12, retaining video bootstrap units.

No rates, confidence intervals, tests or business conclusions are computed here.
Input labels and the validation index are never modified.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

from src.analysis.validation import (
    InputError, MENTION_SCHEMA_VERSION, ValidationConfig, load_schema_validator,
    parse_timestamp, validate_comparison, validate_schema, week_since_launch,
)

AGGREGATOR_VERSION = "cv12-aggregates-v4-contract2"
AGGREGATE_KEY = ("target_model", "aspect", "week_since_launch", "video_id", "source", "model_version")
COUNT_TABLES = (
    "aggregates", "q1_counts", "q2_q3a_q4_counts", "q3b_counts",
    "q5_denominators", "q5_defects", "video_units",
)
DEFECT_TYPES = (
    "BATTERY_DRAIN", "OVERHEAT", "LAG", "DISPLAY_DEFECT", "CAMERA_DEFECT",
    "SOFTWARE_BUG", "CONNECTIVITY", "HARDWARE_DEFECT", "OTHER",
)
ASPECTS = frozenset((
    "BATTERY", "DISPLAY", "PERFORMANCE", "CAMERA", "DESIGN", "SOFTWARE",
    "HARDWARE_OTHER", "PRICE", "WARRANTY",
))
ELIGIBILITY_KEYS = (
    "eligible_q1", "eligible_q2", "eligible_q3a", "eligible_q3b", "eligible_q4",
    "eligible_q5_denominator", "eligible_q5_numerator",
)


@dataclass
class AggregationResult:
    tables: dict[str, list[dict[str, Any]]]
    report: dict[str, Any]


def _unique_rows(records: Iterable[Mapping], name: str) -> dict[str, Mapping]:
    result = {}
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("mention_id"), str) or not row["mention_id"]:
            raise InputError(f"{name} contains a row without a mention_id")
        mid = row["mention_id"]
        if mid in result:
            raise InputError(f"Duplicate mention_id in {name}: {mid}; rerun validation")
        result[mid] = row
    return result


def _checked_pairs(mentions, analysis_index, config):
    records = _unique_rows(mentions, "valid_mentions")
    indices = _unique_rows(analysis_index, "analysis_index")
    if not records:
        raise InputError("No accepted mentions to aggregate")
    if records.keys() != indices.keys():
        raise InputError("Mentions and analysis_index must contain exactly the same mention IDs")
    validator = load_schema_validator()
    for mid in sorted(records):
        record, index = records[mid], indices[mid]
        schema_issues = validate_schema(record, validator)
        if schema_issues:
            raise InputError(f"{mid}: invalid contract v2 mention: {schema_issues[0].message}; rerun validation")
        if record["compare_with"] == record["target_model"]:
            raise InputError(f"{mid}: a model cannot be compared with itself; rerun validation")
        if type(index.get("schema_version")) is not int or index["schema_version"] != MENTION_SCHEMA_VERSION:
            raise InputError(f"{mid}: stale analysis_index schema version; rerun validation")
        for key in ("comment_id", "clause_idx", "author_hash", "parent_id", "author_is_creator"):
            if key not in index or type(index[key]) is not type(record[key]) or index[key] != record[key]:
                raise InputError(f"{mid}: analysis_index disagrees with v2 {key}")
        for key in ("target_model", "aspect", "video_id", "source", "model_version", "sentiment", "comment_id"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise InputError(f"{mid}: invalid {key}")
        if record["model_version"] != config.expected_model_version or index.get("model_version") != record["model_version"]:
            raise InputError(f"{mid}: mixed or unselected inference versions")
        if record["target_model"] not in config.scope:
            raise InputError(f"{mid}: target_model is outside the validated scope")
        if record["aspect"] not in ASPECTS or record["sentiment"] not in {"pos", "neg", "neu"}:
            raise InputError(f"{mid}: invalid aspect or sentiment")
        if record.get("label_source") not in {"rule", "llm", "model", "human"}:
            raise InputError(f"{mid}: invalid label_source")
        if type(record.get("clause_idx")) is not int or record["clause_idx"] < 0:
            raise InputError(f"{mid}: invalid clause_idx")
        if mid != f"{record['comment_id']}#{record['clause_idx']}#{record['aspect']}":
            raise InputError(f"{mid}: mention_id is inconsistent")
        days, week = index.get("days_since_launch"), index.get("week_since_launch")
        if type(days) is not int or type(week) is not int or week_since_launch(days, config.window_days) != week or week is None:
            raise InputError(f"{mid}: invalid day/week in analysis_index")
        if record.get("days_since_launch") is not None and record["days_since_launch"] != days:
            raise InputError(f"{mid}: mention and index disagree on days_since_launch")
        if type(index.get("requires_label_review")) is not bool:
            raise InputError(f"{mid}: requires_label_review must be boolean")
        if type(index.get("author_is_creator")) is not bool:
            raise InputError(f"{mid}: invalid author_is_creator in analysis_index")
        if index.get("author_is_creator") is True or record.get("author_is_creator") is True:
            raise InputError(f"{mid}: creator opinions must not reach aggregates")
        if record.get("is_owner") is not None and type(record["is_owner"]) is not bool:
            raise InputError(f"{mid}: is_owner must be boolean or null")
        if record.get("defect_type") is not None and (record["defect_type"] not in DEFECT_TYPES or record["sentiment"] != "neg"):
            raise InputError(f"{mid}: invalid defect/sentiment combination")
        if record.get("compare_winner") not in {None, "target", "other", "tie"}:
            raise InputError(f"{mid}: invalid comparison winner")
        _, comparison_ok, outcome = validate_comparison(record, {code: {} for code in config.scope}, config)
        is_x = record["target_model"] == config.target_model
        expected = {
            "eligible_q1": True, "eligible_q2": is_x, "eligible_q3a": True,
            "eligible_q3b": comparison_ok,
            "eligible_q4": record["target_model"] in {config.target_model, config.predecessor_model},
            "eligible_q5_denominator": is_x,
            "eligible_q5_numerator": is_x and record.get("is_owner") is True and record["sentiment"] == "neg" and record.get("defect_type") is not None,
        }
        if any(type(index.get(key)) is not bool or index[key] != value for key, value in expected.items()):
            raise InputError(f"{mid}: eligibility flags disagree with the validated mention")
        if index.get("x_comparison_outcome") != outcome:
            raise InputError(f"{mid}: comparison direction disagrees with the mention")
        yield record, index


def _add_sentiment(groups, key, record):
    groups[key]["n_" + record["sentiment"]] += 1


def _sentiment_rows(groups, dimensions):
    rows = []
    for key in sorted(groups):
        counts = groups[key]
        pos, neg, neu = (counts["n_" + label] for label in ("pos", "neg", "neu"))
        rows.append({**dict(zip(dimensions, key)), "n_pos": pos, "n_neg": neg,
                     "n_neu": neu, "n_total": pos + neg + neu, "n_opinionated": pos + neg})
    return rows


def build_aggregates(
    mentions: Iterable[Mapping], analysis_index: Iterable[Mapping], config: ValidationConfig,
    *, updated_at: str | None = None,
) -> AggregationResult:
    """Aggregate one validated inference version; reject duplicate or stale joins."""
    updated_at = updated_at or datetime.now(timezone.utc).isoformat()
    parse_timestamp(updated_at)
    aggregate, weekly, aspects, denominators = (defaultdict(Counter) for _ in range(4))
    comparisons, defects, videos = defaultdict(Counter), Counter(), defaultdict(Counter)
    video_models = defaultdict(set)
    models, sentiments, sources = Counter(), Counter(), Counter()
    eligibility = Counter()
    total = 0
    for record, index in _checked_pairs(mentions, analysis_index, config):
        total += 1
        target, aspect, week = record["target_model"], record["aspect"], index["week_since_launch"]
        video, source, version = record["video_id"], record["source"], record["model_version"]
        _add_sentiment(aggregate, (target, aspect, week, video, source, version), record)
        _add_sentiment(weekly, (target, week, video, source, version), record)
        _add_sentiment(aspects, (target, aspect, video, source, version), record)
        models[target] += 1
        sentiments[record["sentiment"]] += 1
        sources[record["label_source"]] += 1
        eligibility.update(key for key in ELIGIBILITY_KEYS if index[key])
        unit = (source, video, version)
        videos[unit]["n_mentions"] += 1
        videos[unit]["n_requires_label_review"] += index["requires_label_review"]
        videos[unit]["n_creator_status_unknown"] += index.get("author_is_creator") is None
        video_models[unit].add(target)
        if index["eligible_q3b"]:
            opponent = record["compare_with"] if target == config.target_model else target
            key = (target, opponent, aspect, week, video, source, version)
            comparisons[key]["n_x_" + index["x_comparison_outcome"]] += 1
        if index["eligible_q5_denominator"]:
            key = (target, week, video, source, version)
            _add_sentiment(denominators, key, record)
            denominators[key]["n_owner_unknown"] += record.get("is_owner") is None
            if index["eligible_q5_numerator"]:
                defects[(*key, record["defect_type"])] += 1
    rows = _sentiment_rows(aggregate, AGGREGATE_KEY)
    for row in rows:
        raw_key = json.dumps([row[key] for key in AGGREGATE_KEY], ensure_ascii=False, separators=(",", ":"))
        row["agg_id"] = "agg_" + hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        row["updated_at"] = updated_at
    q3b = []
    comparison_dimensions = ("target_model", "opponent_model", "aspect", "week_since_launch", "video_id", "source", "model_version")
    for key in sorted(comparisons):
        counts = comparisons[key]
        wins, losses, ties = counts["n_x_win"], counts["n_x_loss"], counts["n_x_tie"]
        q3b.append({**dict(zip(comparison_dimensions, key)), "model_x": config.target_model,
                    "n_x_win": wins, "n_x_loss": losses, "n_tie": ties,
                    "n_decisive": wins + losses, "n_total": wins + losses + ties})
    denominator_dimensions = ("target_model", "week_since_launch", "video_id", "source", "model_version")
    q5_denominators = _sentiment_rows(denominators, denominator_dimensions)
    q5_defects = []
    for row in q5_denominators:
        key = tuple(row[name] for name in denominator_dimensions)
        row["n_owner_unknown"] = denominators[key]["n_owner_unknown"]
        for defect in DEFECT_TYPES:
            q5_defects.append({**dict(zip(denominator_dimensions, key)), "defect_type": defect,
                               "n_defect": defects[(*key, defect)], "n_denominator": row["n_total"]})
    video_units = [
        {"source": source, "video_id": video, "model_version": version,
         "target_models": sorted(video_models[(source, video, version)]),
         "n_mentions": counts["n_mentions"],
         "n_requires_label_review": counts["n_requires_label_review"],
         "n_creator_status_unknown": counts["n_creator_status_unknown"]}
        for (source, video, version), counts in sorted(videos.items())
    ]
    tables = {
        "aggregates": rows,
        "q1_counts": _sentiment_rows(weekly, denominator_dimensions),
        "q2_q3a_q4_counts": _sentiment_rows(aspects, ("target_model", "aspect", "video_id", "source", "model_version")),
        "q3b_counts": q3b, "q5_denominators": q5_denominators,
        "q5_defects": q5_defects, "video_units": video_units,
    }
    invariants = {
        "primary_counts_equal_input": sum(row["n_total"] for row in rows) == total,
        "q1_counts_equal_input": sum(row["n_total"] for row in tables["q1_counts"]) == total,
        "aspect_counts_equal_input": sum(row["n_total"] for row in tables["q2_q3a_q4_counts"]) == total,
        "q3b_counts_equal_eligible": sum(row["n_total"] for row in q3b) == eligibility["eligible_q3b"],
        "q5_denominator_equal_all_x": sum(row["n_total"] for row in q5_denominators) == models[config.target_model],
        "q5_defects_equal_eligible": sum(row["n_defect"] for row in q5_defects) == eligibility["eligible_q5_numerator"],
        "q5_defects_within_denominator": all(0 <= row["n_defect"] <= row["n_denominator"] for row in q5_defects),
        "video_units_equal_input": sum(row["n_mentions"] for row in video_units) == total,
        "unique_aggregate_ids": len({row["agg_id"] for row in rows}) == len(rows),
    }
    if not all(invariants.values()):
        raise InputError("Aggregate reconciliation failed")
    return AggregationResult(tables, {
        "aggregator_version": AGGREGATOR_VERSION, "mention_schema_version": MENTION_SCHEMA_VERSION,
        "status": "passed", "counts_only": True,
        "input_mentions": total, "table_rows": {name: len(value) for name, value in tables.items()},
        "counts_by_model": dict(sorted(models.items())), "counts_by_sentiment": dict(sorted(sentiments.items())),
        "counts_by_label_source": dict(sorted(sources.items())),
        "eligibility_counts": {key: eligibility[key] for key in ELIGIBILITY_KEYS},
        "invariants": invariants, "video_bootstrap_units": len(video_units),
        "requires_label_review_rows": sum(row["n_requires_label_review"] for row in video_units),
        "creator_status_unknown_rows": sum(row["n_creator_status_unknown"] for row in video_units),
        "label_accuracy_verified": False, "ci_computed": False, "hypothesis_tests_computed": False,
        "can_publish_business_conclusions": False,
        "usage": "exploratory_only" if sources["rule"] else "awaiting_label_evaluation",
        "notes": [
            "All count tables retain source/video_id; resample these joint units for video bootstrap.",
            "Sparse sentiment/comparison cells missing for a video mean zero counts, not missing bootstrap units.",
            "Q3b wins/losses refer to model_x; week_since_launch always refers to target_model.",
            "Q5 denominators include all X mentions, including neutral sentiment and unknown owners.",
            "Q5 emits zero counts for every defect in every observed X video/week; do not sum repeated denominators across defect types.",
            "No rates, CI, Holm corrections, trend priorities or business conclusions are computed in this step.",
        ],
    })

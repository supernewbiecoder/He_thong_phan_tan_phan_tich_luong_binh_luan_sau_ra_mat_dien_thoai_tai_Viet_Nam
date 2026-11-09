"""Behavior and CLI tests for CV12 validation, including intentionally bad data."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.analysis.validate_inputs import FIXTURE_PATH, OUTPUT_NAMES, file_hash, fixture_case
from src.analysis.validation import (
    ROOT, InputError, ValidationConfig, build_report, calculate_days_since_launch,
    check_catalog, index_comments, load_config, load_model_catalog,
    find_model_aliases, load_schema_validator, model_catalog_from_data, strict_json_loads,
    validate_record, validate_records, validate_reference, validate_schema, week_since_launch,
)

PAYLOAD = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
CASES = PAYLOAD["cases"]


@pytest.fixture
def config():
    return load_config(ROOT / "config" / "analysis.yaml")


@pytest.fixture
def catalog():
    return model_catalog_from_data(PAYLOAD["models"])


@pytest.fixture
def validator():
    return load_schema_validator()


def base_context(config):
    record, comment = fixture_case(PAYLOAD, {"name": "unit"})
    return record, index_comments([comment], config)


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_fixture_expectations(case, config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, case)
    original = deepcopy(record)
    result = validate_record(record, index_comments([comment], config), catalog, config, validator=validator)
    assert result.status == case["expected_status"]
    assert set(case["expected_codes"]) == {i.code for i in result.issues}
    if "expected_week" in case:
        assert result.analysis["week_since_launch"] == case["expected_week"]
    assert record == original, "Validation must preserve original data"


@pytest.mark.parametrize("day,expected", [(-1, None), (0, 1), (6, 1), (7, 2), (13, 2), (14, 3), (20, 3), (21, 4), (27, 4), (28, None)])
def test_week_boundaries(day, expected):
    assert week_since_launch(day) == expected


def test_local_day_instead_of_elapsed_24_hours():
    assert calculate_days_since_launch("2023-02-01T17:30:00Z", "2023-02-02") == 0
    assert calculate_days_since_launch("2023-02-02T17:00:00Z", "2023-02-02") == 1


@pytest.mark.parametrize("stamp", ["not-a-date", "2023-02-30T00:00:00Z", "2023-02-02T00:00:00", "2023-02-02T24:00:00Z", "2023-02-02T00:00:00+00:60"])
def test_invalid_dates_are_checked_without_optional_format_packages(stamp, validator):
    record = {**PAYLOAD["base_mention"], "published_at": stamp}
    assert any(i.field == "$.published_at" for i in validate_schema(record, validator))


def test_equivalent_timezone_offsets(config, catalog, validator):
    record, comments = base_context(config)
    record["published_at"] = "2023-02-02T00:30:00+07:00"
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "accepted"
    assert result.analysis["days_since_launch"] == 0


def test_duplicate_does_not_inflate_counts(config, catalog, validator):
    record, comments = base_context(config)
    results = validate_records([record, deepcopy(record)], comments, catalog, config, validator)
    assert [r.status for r in results] == ["accepted", "duplicate"]
    report = build_report(results)
    assert report["counts"]["accepted"] == 1
    assert report["eligibility_counts"]["eligible_q5_denominator"] == 1


@pytest.mark.parametrize("reverse", [False, True])
def test_conflicting_labels_quarantine_every_member(reverse, config, catalog, validator):
    record, comments = base_context(config)
    changed = {**record, "sentiment": "neg"}
    records = [record, changed]
    if reverse:
        records.reverse()
    results = validate_records(records, comments, catalog, config, validator)
    assert all(r.status == "rejected" and r.analysis is None for r in results)
    assert all(r.issues[0].code == "DUPLICATE_CONFLICT" for r in results)


def test_old_version_cannot_conflict_with_selected_version(config, catalog, validator):
    record, comments = base_context(config)
    old = {**record, "model_version": "old-v0", "sentiment": "neg"}
    results = validate_records([record, old], comments, catalog, config, validator)
    assert [r.status for r in results] == ["accepted", "excluded"]


def test_target_may_differ_from_video_model(config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, {"name": "different_target"})
    record.update(target_model="ip14prm", published_at="2022-09-16T01:00:00Z", days_since_launch=0)
    comment["published_at"] = record["published_at"]
    result = validate_record(record, index_comments([comment], config), catalog, config, validator=validator)
    assert result.status == "accepted"
    assert result.record["video_model"] == "s23u"
    assert result.record["target_model"] == "ip14prm"


@pytest.mark.parametrize("winner,expected", [("target", "loss"), ("other", "win"), ("tie", "tie")])
def test_comparison_direction_is_normalized_to_x(winner, expected, config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, {"name": "reverse_comparison"})
    record.update(target_model="ip14prm", compare_with="s23u", compare_winner=winner,
                  published_at="2022-09-16T01:00:00Z", days_since_launch=0)
    comment["published_at"] = record["published_at"]
    result = validate_record(record, index_comments([comment], config), catalog, config, validator=validator)
    assert result.analysis["eligible_q3b"] is True
    assert result.analysis["x_comparison_outcome"] == expected


def test_q5_denominator_keeps_unknown_owner_and_neutral(config, catalog, validator):
    record, comments = base_context(config)
    record.update(is_owner=None, sentiment="neu")
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "accepted"
    assert result.record["is_owner"] is None
    assert result.analysis["eligible_q5_denominator"] is True
    assert result.analysis["eligible_q5_numerator"] is False


@pytest.mark.parametrize("metadata", [{"clause_id": 1}, {"idx": 7}, {"clause_id": 42, "idx": 9}])
def test_v2_clause_idx_is_array_position_independent_of_clause_ids(metadata, config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, {"name": "reference_mode"})
    comment["clauses"][0].update(metadata)
    assert record["clause_idx"] == 0
    result = validate_record(record, index_comments([comment], config), catalog, config, validator=validator)
    assert result.status == "accepted"


def test_clean_comments_are_not_validated_as_raw_events(config):
    comment = deepcopy(PAYLOAD["base_comment"])
    comment["pipeline_version"] = "cleaner-v1.1"
    assert comment["comment_id"] in index_comments([comment], config)


@pytest.mark.parametrize("key,value", [("is_spam", "false"), ("is_vietnamese", None), ("clause_count", 3)])
def test_bad_comment_metadata_fails_preflight(key, value, config):
    comment = {**deepcopy(PAYLOAD["base_comment"]), key: value}
    with pytest.raises(InputError):
        index_comments([comment], config)


def test_conflicting_comment_ids_fail_preflight(config):
    comment = deepcopy(PAYLOAD["base_comment"])
    with pytest.raises(InputError, match="Conflicting comments"):
        index_comments([comment, {**comment, "is_spam": True}], config)


def test_no_publication_from_future(config):
    comment = {**deepcopy(PAYLOAD["base_comment"]), "fetched_at": "2010-01-01T00:00:00Z"}
    with pytest.raises(InputError, match="published after"):
        index_comments([comment], config)


def test_catalog_includes_nested_rivals_and_rejects_conflicting_dates(tmp_path):
    path = tmp_path / "models.json"
    path.write_text(json.dumps({"models": [{"name": "a", "launch_date": "2023-01-01", "rivals": [
        {"name": "b", "launch_date": "2023-02-01"}, "c"
    ]}]}), encoding="utf-8")
    catalog = load_model_catalog(path)
    assert set(catalog) == {"a", "b", "c"}
    assert "launch_date" not in catalog["c"], "Never inherit another phone's date"
    with pytest.raises(InputError, match="Conflicting launch_date"):
        model_catalog_from_data([{"name": "a", "launch_date": "2023-01-01"}, {"name": "a", "launch_date": "2023-02-01"}])


def test_project_catalog_covers_configured_scope(config):
    check_catalog(load_model_catalog(ROOT / "config" / "pipeline.yaml"), config)


def test_default_config_selects_existing_rule_baseline(config):
    assert config.expected_model_version == "rule-v0"
    assert config.clause_reference == "position" and config.clause_text_field == "text"


@pytest.mark.parametrize("field", [
    "author_hash", "author_is_creator", "parent_id", "confidence", "is_owner",
    "defect_type", "compare_with", "compare_winner", "days_since_launch",
])
def test_v2_requires_nullable_fields_to_be_present(field, config, catalog, validator):
    record, comments = base_context(config)
    record.pop(field)
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected"
    assert {issue.code for issue in result.issues} == {"SCHEMA_ERROR"}


@pytest.mark.parametrize("field", ["author_hash", "author_is_creator", "parent_id"])
def test_v2_missing_source_metadata_cannot_be_invented(field, config, catalog, validator):
    record, comments = base_context(config)
    before = deepcopy(record)
    comments[record["comment_id"]].pop(field)
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected" and result.analysis is None
    assert any(issue.code == "REFERENCE_MISMATCH" and issue.field == f"$.{field}" for issue in result.issues)
    assert record == before


def test_v1_records_are_rejected_without_silent_conversion(config, catalog, validator):
    record, comments = base_context(config)
    record["schema_version"] = 1
    before = deepcopy(record)
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected" and record == before
    assert all(issue.code == "SCHEMA_ERROR" for issue in result.issues)


@pytest.mark.parametrize("kind", ["v1", "permissive_schema", "unversioned_property"])
def test_old_contract_cannot_be_selected_to_bypass_v2(kind, tmp_path):
    path = tmp_path / "old-schema.json"
    schema = json.loads((ROOT / "contracts/aspect-mention.schema.json").read_text(encoding="utf-8"))
    schema["properties"]["schema_version"]["const"] = 1
    if kind == "permissive_schema":
        schema = True
    elif kind == "unversioned_property":
        schema["properties"]["schema_version"] = True
    path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(InputError, match="contract v2"):
        load_schema_validator(path)


def test_second_clause_is_selected_by_array_position_and_original_text(config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, {"name": "second_clause"})
    comment["clauses"].append({"clause_id": 2, "text": "Camera rất tốt", "text_norm": "camera rất tốt"})
    comment["clause_count"] = 2
    record.update(clause_idx=1, clause_text=comment["clauses"][1]["text"], aspect="CAMERA")
    record["mention_id"] = f"{record['comment_id']}#1#CAMERA"
    comments = index_comments([comment], config)
    assert validate_record(record, comments, catalog, config, validator=validator).status == "accepted"
    record["clause_text"] = comment["clauses"][0]["text"]
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected" and result.issues[0].code == "CLAUSE_TEXT_MISMATCH"
    record["clause_text"] = comment["clauses"][1]["text_norm"]
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected" and result.issues[0].code == "CLAUSE_TEXT_MISMATCH"


def test_creator_flag_must_match_source_before_filtering(config, catalog, validator):
    record, comments = base_context(config)
    record["author_is_creator"] = True
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected" and result.issues[0].code == "REFERENCE_MISMATCH"
    comments[record["comment_id"]]["author_is_creator"] = True
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "excluded" and result.issues[0].code == "AUTHOR_IS_CREATOR"


def test_unknown_comparison_model_is_rejected_by_v2_semantics(config, catalog, validator):
    record, comments = base_context(config)
    record.update(compare_with="unknown_phone", compare_winner="target")
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "rejected" and result.issues[0].code == "UNKNOWN_COMPARISON_MODEL"


def test_known_model_outside_analysis_scope_only_excludes_q3b(config, catalog, validator):
    record, comments = base_context(config)
    record.update(compare_with="mi11", compare_winner="target")
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "accepted" and result.analysis["eligible_q1"]
    assert not result.analysis["eligible_q3b"]
    assert "OUT_OF_SCOPE_COMPARISON" in {issue.code for issue in result.issues}


def test_rule_confidence_is_not_treated_as_measured_accuracy(config, catalog, validator):
    record, comments = base_context(config)
    result = validate_record(record, comments, catalog, config, validator=validator)
    codes = {i.code for i in result.issues}
    assert {"RULE_BASELINE_LABEL", "HEURISTIC_CONFIDENCE", "BASELINE_TARGET_CONTEXT"} <= codes
    report = build_report([result])
    assert report["status"] == "passed" and report["can_build_aggregates"]
    assert report["usage"] == "exploratory_only"
    assert report["baseline_audit"]["confidence_kind"] == "heuristic_not_calibrated"
    assert not report["can_publish_business_conclusions"]
    assert not report["label_accuracy_verified"]


def test_negation_warns_without_changing_the_baseline_label(config, catalog, validator):
    case = next(c for c in CASES if c["name"] == "baseline_negation")
    record, comment = fixture_case(PAYLOAD, case)
    original = deepcopy(record)
    result = validate_record(record, index_comments([comment], config), catalog, config, validator=validator)
    assert result.record == original and result.record["sentiment"] == "pos"
    assert "NEGATION_REVIEW_REQUIRED" in {i.code for i in result.issues}
    assert result.analysis["requires_label_review"] is True


def test_multilabel_mentions_remain_separate_from_duplicates(config, catalog, validator):
    record, comments = base_context(config)
    camera = {**record, "aspect": "CAMERA", "sentiment": "neg"}
    camera["mention_id"] = f"{camera['comment_id']}#{camera['clause_idx']}#CAMERA"
    results = validate_records([record, camera], comments, catalog, config, validator)
    assert [r.status for r in results] == ["accepted", "accepted"]
    assert [r.record["sentiment"] for r in results] == ["pos", "neg"]
    report = build_report(results)
    assert report["multi_aspect_clause_count"] == 1
    assert report["accepted_by_aspect"] == {"BATTERY": 1, "CAMERA": 1}


@pytest.mark.parametrize("text,expected", [
    ("ip14prm", {"ip14prm"}),
    ("IPHONE 14 PRO MAX", {"ip14prm"}),
    ("s23u ip14prm", {"s23u", "ip14prm"}),
    ("xs23u2", set()),
    ("ss", set()),
])
def test_model_alias_hints_have_boundaries_and_specific_phone_codes(text, expected, catalog):
    assert find_model_aliases(text, catalog) == expected


def test_alias_catalog_merges_duplicate_entries_and_avoids_shared_or_shorter_aliases():
    catalog = model_catalog_from_data([
        {"model_id": "ip14", "aliases": ["iphone 14", "shared14"]},
        {"model_id": "ip14prm", "aliases": ["iphone 14 pro max", "shared14"]},
        {"model_id": "ip14prm", "aliases": ["14 prm"]},
    ])
    assert set(catalog["ip14prm"]["aliases"]) == {"iphone 14 pro max", "shared14", "14 prm"}
    assert find_model_aliases("iphone 14 pro max", catalog) == {"ip14prm"}
    assert find_model_aliases("shared14", catalog) == set()


@pytest.mark.parametrize("parent_in_index", [False, True])
def test_baseline_reviews_parent_context_before_video_fallback(parent_in_index, config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, {"name": "parent_context"})
    comment["parent_id"] = "parent_test"
    record["parent_id"] = "parent_test"
    parent = deepcopy(comment)
    parent.update(comment_id="parent_test", parent_id=None, text="iPhone 14 Pro Max")
    if not parent_in_index:
        comment["parent_text"] = parent["text"]
    comments = index_comments([comment, parent] if parent_in_index else [comment], config)
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.analysis["baseline_audit"]["target_evidence"] == "parent_alias"
    codes = {i.code for i in result.issues}
    assert "TARGET_ALIAS_CONFLICT" in codes and "BASELINE_TARGET_CONTEXT" not in codes
    assert result.record["target_model"] == "s23u", "The checker must not silently relabel a target"


def test_clause_alias_takes_precedence_over_parent_hint(config, catalog, validator):
    record, comment = fixture_case(PAYLOAD, {"name": "clause_context"})
    text = "Pin s23u tot"
    record["clause_text"] = text
    comment["clauses"][0]["text"] = text
    comment["parent_text"] = "ip14prm"
    result = validate_record(record, index_comments([comment], config), catalog, config, validator=validator)
    assert result.analysis["baseline_audit"]["target_evidence"] == "clause_alias"
    assert "TARGET_ALIAS_CONFLICT" not in {i.code for i in result.issues}


def test_owner_false_is_preserved_and_not_dropped_from_q5_denominator(config, catalog, validator):
    record, comments = base_context(config)
    record["is_owner"] = False
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.record["is_owner"] is False
    assert result.analysis["eligible_q5_denominator"] is True
    assert result.analysis["eligible_q5_numerator"] is False
    assert "BASELINE_OWNER_UNVERIFIED" in {i.code for i in result.issues}


def test_rule_comparison_keeps_direction_but_exposes_manual_review(config, catalog, validator):
    record, comments = base_context(config)
    record.update(compare_with="ip14prm", compare_winner="other")
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.analysis["eligible_q3b"] is True
    assert result.analysis["x_comparison_outcome"] == "loss"
    assert "BASELINE_COMPARISON_UNVERIFIED" in {i.code for i in result.issues}


def test_human_labels_are_not_reported_as_rule_predictions(config, catalog, validator):
    record, comments = base_context(config)
    record.update(label_source="human", confidence=None)
    result = validate_record(record, comments, catalog, config, validator=validator)
    assert result.status == "accepted" and result.analysis["baseline_audit"] is None
    report = build_report([result])
    assert report["baseline_audit"]["accepted_rows"] == 0
    assert report["accepted_by_label_source"] == {"human": 1}
    assert report["usage"] == "awaiting_label_evaluation"


@pytest.mark.parametrize("field,value", [("author_hash", "wrong_hash"), ("author_is_creator", True), ("parent_id", "wrong_parent")])
def test_v2_metadata_must_match_the_source_comment(field, value, config):
    record, comments = base_context(config)
    comment = comments[record["comment_id"]]
    comment.update(author_hash="a" * 64, author_is_creator=False, parent_id=None)
    record.update(author_hash="a" * 64, author_is_creator=False, parent_id=None)
    record[field] = value
    assert any(i.code == "REFERENCE_MISMATCH" and i.field == f"$.{field}" for i in validate_reference(record, comments, config))


def test_creator_flag_cannot_be_a_truthy_string(config):
    comment = {**deepcopy(PAYLOAD["base_comment"]), "author_is_creator": "false"}
    with pytest.raises(InputError, match="author_is_creator"):
        index_comments([comment], config)


@pytest.mark.parametrize("patch", [
    {"rival_models": ["s23u", "ip14prm"]}, {"rival_models": "ip14prm"},
    {"window_days": 56}, {"window_days": True}, {"expected_model_version": ""},
    {"timezone": "Invalid/Zone"}, {"clause_reference": "guess"}, {"typo": 1},
    {"clause_reference": "clause_id"}, {"clause_reference": "idx"}, {"clause_text_field": "text_norm"},
])
def test_bad_analysis_config_is_rejected(patch, config):
    data = {**asdict(config), "rival_models": list(config.rival_models), **patch}
    with pytest.raises(InputError):
        ValidationConfig.from_mapping(data)


@pytest.mark.parametrize("text", ['{"a": NaN}', '{"a": Infinity}', '{"a": 1, "a": 2}'])
def test_strict_json_rejects_ambiguous_or_nonfinite_values(text):
    with pytest.raises(ValueError):
        strict_json_loads(text)


def cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "src.analysis.validate_inputs", *map(str, args)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_cli_demo_valid_artifacts_and_reproducibility(tmp_path, validator):
    output = tmp_path / "valid"
    result = cli("--demo", "valid", "--output", output)
    assert result.returncode == 0, result.stderr
    assert set(p.name for p in output.iterdir()) == set(OUTPUT_NAMES)
    report = json.loads((output / "validation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed" and report["data_kind"] == "fixture"
    assert report["mention_schema_version"] == 2
    assert report["counts"]["accepted"] == 1
    assert report["label_accuracy_verified"] is False
    assert report["usage"] == "exploratory_only"
    assert report["baseline_audit"]["accepted_rows"] == 1
    record = read_jsonl(output / "valid_mentions.jsonl")[0]
    assert not validate_schema(record, validator)
    assert "eligible_q1" not in record and "week_since_launch" not in record
    index = read_jsonl(output / "analysis_index.jsonl")[0]
    assert record["schema_version"] == index["schema_version"] == 2
    assert record["clause_idx"] == index["clause_idx"] == 0
    assert index["author_hash"] == record["author_hash"] and index["parent_id"] is None
    assert index["days_since_launch"] == 0 and index["week_since_launch"] == 1
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    assert all(file_hash(output / name) == digest for name, digest in manifest["output_sha256"].items())
    before = {name: (output / name).read_bytes() for name in OUTPUT_NAMES[:-1]}
    assert cli("--demo", "valid", "--output", output).returncode == 0
    assert before == {name: (output / name).read_bytes() for name in OUTPUT_NAMES[:-1]}


def test_cli_mixed_demo_reports_expected_errors(tmp_path):
    output = tmp_path / "all"
    result = cli("--demo", "all", "--output", output)
    assert result.returncode == 1, result.stderr
    report = json.loads((output / "validation_report.json").read_text(encoding="utf-8"))
    expected = {status: sum(c["expected_status"] == status for c in CASES) for status in ("accepted", "rejected", "excluded")}
    assert all(report["counts"][status] == count for status, count in expected.items())
    assert report["counts"]["rows_read"] == len(CASES)
    assert report["row_accounting_ok"] is True
    assert report["can_build_aggregates"] is False
    assert read_jsonl(output / "issues.jsonl")


def test_cli_real_file_mode_handles_invalid_json_and_blank_lines(tmp_path):
    record, comment = fixture_case(PAYLOAD, {"name": "files"})
    mentions = tmp_path / "mentions.jsonl"
    comments = tmp_path / "comments.jsonl"
    models = tmp_path / "models.json"
    output = tmp_path / "out"
    mentions.write_text(json.dumps(record, ensure_ascii=False) + '\n\n{"broken":\nnull\n', encoding="utf-8")
    comments.write_text(json.dumps(comment, ensure_ascii=False) + "\n", encoding="utf-8")
    models.write_text(json.dumps(PAYLOAD["models"]), encoding="utf-8")
    before = mentions.read_bytes()
    result = cli("--mentions", mentions, "--comments", comments, "--models", models, "--output", output)
    assert result.returncode == 1, result.stderr
    report = json.loads((output / "validation_report.json").read_text(encoding="utf-8"))
    assert report["counts"] == {"rows_read": 3, "accepted": 1, "rejected": 2, "excluded": 0, "duplicate": 0, "blank_lines": 1}
    assert report["issue_counts"]["INVALID_JSON"] == 1
    assert mentions.read_bytes() == before


def test_missing_required_file_returns_input_error(tmp_path):
    result = cli("--mentions", tmp_path / "absent.jsonl", "--comments", tmp_path / "absent_comments.jsonl")
    assert result.returncode == 2
    assert json.loads(result.stderr)["status"] == "input_error"


def test_empty_selected_dataset_is_not_reported_as_passed(tmp_path):
    result = cli("--demo", "outside_scope", "--output", tmp_path)
    assert result.returncode == 1
    report = json.loads((tmp_path / "validation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "empty" and not report["can_build_aggregates"]


def test_cli_can_select_another_version_without_editing_config(tmp_path):
    result = cli("--demo", "other_version", "--model-version", "another-v2", "--output", tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "validation_report.json").read_text(encoding="utf-8"))
    assert report["config"]["expected_model_version"] == "another-v2"
    assert report["counts"]["accepted"] == 1


def test_cli_rejects_blank_selected_version(tmp_path):
    result = cli("--demo", "valid", "--model-version", " ", "--output", tmp_path)
    assert result.returncode == 2
    assert "model-version" in json.loads(result.stderr)["message"]


def test_output_cannot_overwrite_mention_input(tmp_path):
    record, comment = fixture_case(PAYLOAD, {"name": "protected"})
    mentions = tmp_path / "valid_mentions.jsonl"
    comments = tmp_path / "comments.jsonl"
    models = tmp_path / "models.json"
    mentions.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    comments.write_text(json.dumps(comment, ensure_ascii=False) + "\n", encoding="utf-8")
    models.write_text(json.dumps(PAYLOAD["models"]), encoding="utf-8")
    before = mentions.read_bytes()
    result = cli("--mentions", mentions, "--comments", comments, "--models", models, "--output", tmp_path)
    assert result.returncode == 2
    assert "overwrite" in json.loads(result.stderr)["message"]
    assert mentions.read_bytes() == before

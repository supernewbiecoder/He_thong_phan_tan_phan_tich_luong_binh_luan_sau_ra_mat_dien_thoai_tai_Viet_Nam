"""Hand-counted fixtures and CLI checks for the validated-mentions aggregate step."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.analysis.aggregation import AGGREGATE_KEY, COUNT_TABLES, DEFECT_TYPES, build_aggregates
from src.analysis.build_aggregates import OUTPUT_NAMES, load_validated_bundle
from src.analysis.validate_inputs import (
    build_parser as validation_parser, file_hash, fixture_case, run as run_validation,
)
from src.analysis.validation import (
    ROOT, InputError, index_comments, load_config, model_catalog_from_data, validate_records,
)

FIXTURE = ROOT / "tests/fixtures/aggregation_cases.json"
PAYLOAD = json.loads(FIXTURE.read_text(encoding="utf-8"))
EXPECTED = PAYLOAD["expected"]
STAMP = "2026-11-09T00:00:00+00:00"


@pytest.fixture
def validated():
    config = load_config(ROOT / "config/analysis.yaml")
    pairs = [fixture_case(PAYLOAD, case) for case in PAYLOAD["cases"]]
    comments = index_comments([comment for _, comment in pairs], config)
    results = validate_records([record for record, _ in pairs], comments, model_catalog_from_data(PAYLOAD["models"]), config)
    assert len(comments) == EXPECTED["unique_comments"]
    assert all(result.status == "accepted" for result in results)
    return [result.record for result in results], [result.analysis for result in results], config


@pytest.fixture
def aggregated(validated):
    return build_aggregates(*validated, updated_at=STAMP)


@pytest.fixture
def validation_bundle(tmp_path):
    directory = tmp_path / "validation"
    args = validation_parser().parse_args(["--demo", "all", "--fixtures", str(FIXTURE), "--output", str(directory)])
    report, _ = run_validation(args)
    assert report["status"] == "passed" and report["counts"]["accepted"] == 15
    return directory


def cli(*args):
    return subprocess.run([sys.executable, "-m", "src.analysis.build_aggregates", *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rewrite_report(directory, change):
    path = directory / "validation_report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    change(report)
    path.write_text(json.dumps(report), encoding="utf-8")
    path = directory / "run_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"]["validation_report.json"] = file_hash(directory / "validation_report.json")
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_hand_counted_total_and_count_reconciliation(aggregated):
    report = aggregated.report
    assert report["input_mentions"] == EXPECTED["input_mentions"]
    assert report["counts_by_model"] == EXPECTED["counts_by_model"]
    assert report["counts_by_sentiment"] == EXPECTED["counts_by_sentiment"]
    assert report["table_rows"]["aggregates"] == EXPECTED["aggregate_rows"]
    assert report["table_rows"]["q1_counts"] == EXPECTED["q1_rows"]
    assert all(report["invariants"].values())


def test_primary_key_and_multiaspect_counting(aggregated):
    rows = aggregated.tables["aggregates"]
    battery = next(row for row in rows if row["target_model"] == "s23u" and row["aspect"] == "BATTERY" and row["week_since_launch"] == 1)
    assert {name: battery[name] for name in ("n_pos", "n_neg", "n_neu", "n_total")} == {"n_pos": 1, "n_neg": 1, "n_neu": 0, "n_total": 2}
    camera = next(row for row in rows if row["target_model"] == "s23u" and row["aspect"] == "CAMERA" and row["week_since_launch"] == 1)
    assert camera["n_pos"] == 1 and camera["n_neu"] == 1
    assert len({tuple(row[key] for key in AGGREGATE_KEY) for row in rows}) == len(rows)
    assert len({row["agg_id"] for row in rows}) == len(rows)


def test_neutral_mentions_stay_in_total_but_not_opinionated_counts(aggregated):
    neutral = next(row for row in aggregated.tables["q1_counts"] if row["target_model"] == "xiaomi13u")
    assert neutral["n_total"] == neutral["n_neu"] == 1
    assert neutral["n_opinionated"] == neutral["n_pos"] == neutral["n_neg"] == 0
    assert sum(row["n_opinionated"] for row in aggregated.tables["q1_counts"]) == 11


def test_target_phone_and_weeks_are_not_taken_from_video_context(aggregated):
    rows = aggregated.tables["aggregates"]
    assert {row["target_model"] for row in rows} == {"s23u", "s22u", "ip14prm", "xiaomi13u"}
    assert {row["week_since_launch"] for row in rows if row["target_model"] == "s23u"} == {1, 2, 3, 4}
    assert aggregated.report["counts_by_model"]["ip14prm"] == 2


def test_video_units_do_not_merge_identical_ids_from_different_sources(aggregated):
    units = aggregated.tables["video_units"]
    assert len(units) == EXPECTED["video_bootstrap_units"]
    assert {(row["source"], row["video_id"]) for row in units} == {
        ("youtube", "video_a"), ("youtube", "video_b"), ("youtube", "video_c"), ("tinhte", "video_a"),
    }
    same_id = [row for row in units if row["video_id"] == "video_a"]
    assert sorted(row["n_mentions"] for row in same_id) == [1, 6]


def test_direct_comparison_wins_are_normalized_to_x_and_ties_are_separate(aggregated):
    rows = aggregated.tables["q3b_counts"]
    totals = {name: sum(row[name] for row in rows) for name in EXPECTED["q3b"]}
    assert totals == EXPECTED["q3b"]
    reverse = next(row for row in rows if row["target_model"] == "ip14prm")
    assert reverse["n_x_win"] == reverse["n_x_loss"] == 1
    assert reverse["model_x"] == "s23u" and reverse["opponent_model"] == "ip14prm"
    assert all(row["n_decisive"] == row["n_x_win"] + row["n_x_loss"] for row in rows)


def test_q5_denominator_includes_neutral_unknown_owner_and_nondefects(aggregated):
    denominators = aggregated.tables["q5_denominators"]
    assert len(denominators) == EXPECTED["q5_denominator_rows"]
    assert sum(row["n_total"] for row in denominators) == EXPECTED["q5"]["n_denominator"]
    assert sum(row["n_neu"] for row in denominators) == 3
    assert sum(row["n_owner_unknown"] for row in denominators) == EXPECTED["q5"]["n_owner_unknown"]
    assert {row["target_model"] for row in denominators} == {"s23u"}


def test_q5_keeps_zero_defects_for_every_observed_x_video_week(aggregated):
    rows = aggregated.tables["q5_defects"]
    assert len(rows) == EXPECTED["q5_defect_rows"]
    assert sum(row["n_defect"] for row in rows) == EXPECTED["q5"]["n_defect"]
    assert sum(row["n_defect"] == 0 for row in rows) == 50
    assert all(row["n_defect"] <= row["n_denominator"] for row in rows)
    for defect in DEFECT_TYPES:
        assert sum(row["n_denominator"] for row in rows if row["defect_type"] == defect) == 11


def test_count_tables_contain_integers_and_no_rates_or_conclusions(aggregated):
    assert set(aggregated.tables) == set(COUNT_TABLES)
    for rows in aggregated.tables.values():
        for row in rows:
            assert all(type(value) is int and value >= 0 for key, value in row.items() if key.startswith("n_"))
            assert not any(key in row for key in ("rate", "net_sentiment", "p_value", "priority", "ci_low", "ci_high"))
    assert aggregated.report["usage"] == "exploratory_only"
    assert not aggregated.report["can_publish_business_conclusions"]
    assert not aggregated.report["ci_computed"] and not aggregated.report["hypothesis_tests_computed"]


def test_join_is_by_mention_id_and_does_not_modify_input(validated, aggregated):
    mentions, index, config = validated
    before = deepcopy((mentions, index))
    reordered = build_aggregates(reversed(mentions), reversed(index), config, updated_at=STAMP)
    assert reordered.tables == aggregated.tables and reordered.report == aggregated.report
    assert (mentions, index) == before


@pytest.mark.parametrize("duplicate_index", [False, True])
def test_duplicate_rows_are_rejected_instead_of_double_counted(duplicate_index, validated):
    mentions, index, config = deepcopy(validated)
    rows = index if duplicate_index else mentions
    rows.append(deepcopy(rows[0]))
    with pytest.raises(InputError, match="Duplicate mention_id"):
        build_aggregates(mentions, index, config)


def test_missing_join_row_is_rejected(validated):
    mentions, index, config = validated
    with pytest.raises(InputError, match="same mention IDs"):
        build_aggregates(mentions, index[:-1], config)


@pytest.mark.parametrize("side,key,value", [
    ("mention", "model_version", "another-version"),
    ("mention", "target_model", "unknown_phone"),
    ("mention", "aspect", "THERMAL"),
    ("mention", "days_since_launch", 8),
    ("mention", "defect_type", "BATTERY_DRAIN"),
    ("index", "week_since_launch", 2),
    ("index", "week_since_launch", True),
    ("index", "days_since_launch", 28),
    ("index", "eligible_q5_denominator", False),
    ("index", "eligible_q1", 1),
    ("index", "author_is_creator", True),
    ("index", "x_comparison_outcome", "win"),
    ("mention", "schema_version", 1),
    ("index", "schema_version", 1),
    ("index", "author_hash", "b" * 64),
    ("index", "parent_id", "another_parent"),
    ("index", "clause_idx", True),
])
def test_inconsistent_metadata_cannot_silently_enter_counts(side, key, value, validated):
    mentions, index, config = deepcopy(validated)
    rows = mentions if side == "mention" else index
    rows[0][key] = value
    with pytest.raises(InputError):
        build_aggregates(mentions, index, config)


def test_empty_input_is_not_a_successful_aggregate(validated):
    with pytest.raises(InputError, match="No accepted"):
        build_aggregates([], [], validated[2])


def test_self_comparison_cannot_bypass_validation_through_the_aggregate_api(validated):
    mentions, index, config = deepcopy(validated)
    mentions[0].update(compare_with=mentions[0]["target_model"], compare_winner="target")
    with pytest.raises(InputError, match="itself"):
        build_aggregates(mentions, index, config)


def test_cli_writes_complete_outputs_and_checksums(validation_bundle, tmp_path):
    output = tmp_path / "aggregates"
    completed = cli("--validation-dir", validation_bundle, "--output", output)
    assert completed.returncode == 0, completed.stderr
    assert set(p.name for p in output.iterdir()) == set(OUTPUT_NAMES)
    manifest = json.loads((output / "aggregation_manifest.json").read_text(encoding="utf-8"))
    report = manifest["aggregation_report"]
    assert report["data_kind"] == "fixture" and report["input_mentions"] == 15
    assert all(report["invariants"].values()) and report["usage"] == "exploratory_only"
    assert all(file_hash(output / name) == digest for name, digest in manifest["output_sha256"].items())
    assert manifest["config"] == report["config"]


def test_rerunning_replaces_counts_without_accumulating(validation_bundle, tmp_path):
    output = tmp_path / "aggregates"
    assert cli("--validation-dir", validation_bundle, "--output", output).returncode == 0
    first = jsonl(output / "aggregates.jsonl")
    for row in first:
        row.pop("updated_at")
    assert cli("--validation-dir", validation_bundle, "--output", output).returncode == 0
    second = jsonl(output / "aggregates.jsonl")
    for row in second:
        row.pop("updated_at")
    assert second == first and sum(row["n_total"] for row in second) == 15


@pytest.mark.parametrize("filename", ["valid_mentions.jsonl", "analysis_index.jsonl", "issues.jsonl", "validation_report.json"])
def test_cli_blocks_modified_validation_artifacts(filename, validation_bundle, tmp_path):
    with (validation_bundle / filename).open("a", encoding="utf-8") as stream:
        stream.write("\n")
    output = tmp_path / "blocked"
    completed = cli("--validation-dir", validation_bundle, "--output", output)
    assert completed.returncode == 2 and "checksum" in json.loads(completed.stderr)["message"].lower()
    assert not output.exists()


@pytest.mark.parametrize("field,value", [("status", "failed"), ("can_build_aggregates", False), ("row_accounting_ok", False)])
def test_cli_blocks_a_validation_run_that_did_not_pass(field, value, validation_bundle, tmp_path):
    rewrite_report(validation_bundle, lambda report: report.update({field: value}))
    completed = cli("--validation-dir", validation_bundle, "--output", tmp_path / "blocked")
    assert completed.returncode == 2 and "gate" in json.loads(completed.stderr)["message"].lower()


def test_cli_rejects_a_stale_validation_version_even_with_valid_checksums(validation_bundle, tmp_path):
    rewrite_report(validation_bundle, lambda report: report.update(validator_version="cv12-validation-v2-baseline"))
    output = tmp_path / "blocked"
    completed = cli("--validation-dir", validation_bundle, "--output", output)
    assert completed.returncode == 2 and "version" in json.loads(completed.stderr)["message"]
    assert not output.exists()


def test_cli_cross_checks_validation_count_totals(validation_bundle, tmp_path):
    rewrite_report(validation_bundle, lambda report: report["counts"].update(accepted=16))
    completed = cli("--validation-dir", validation_bundle, "--output", tmp_path / "blocked")
    assert completed.returncode == 2 and "row count" in json.loads(completed.stderr)["message"].lower()


def test_cli_cross_checks_question_eligibility_totals(validation_bundle, tmp_path):
    rewrite_report(validation_bundle, lambda report: report["eligibility_counts"].update(eligible_q5_numerator=5))
    completed = cli("--validation-dir", validation_bundle, "--output", tmp_path / "blocked")
    assert completed.returncode == 2 and "eligibility" in json.loads(completed.stderr)["message"].lower()


def test_validation_bundle_uses_frozen_config_without_original_source_paths(validation_bundle):
    path = validation_bundle / "run_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["inputs"] = [{"path": "missing-on-this-machine", "sha256": "unused"}]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    mentions, index, config, report, _ = load_validated_bundle(validation_bundle)
    assert len(mentions) == len(index) == 15
    assert json.loads(json.dumps(asdict(config))) == report["config"]


def test_cli_rejects_missing_bundle_and_input_output_collision(validation_bundle, tmp_path):
    missing = cli("--validation-dir", tmp_path / "missing", "--output", tmp_path / "blocked")
    assert missing.returncode == 2
    collision = cli("--validation-dir", validation_bundle, "--output", validation_bundle)
    assert collision.returncode == 2 and "separate" in json.loads(collision.stderr)["message"]


def test_one_command_demo_keeps_final_outputs_and_validation_provenance(tmp_path):
    output = tmp_path / "aggregates"
    completed = cli("--demo", "--output", output)
    assert completed.returncode == 0, completed.stderr
    assert set(path.name for path in output.iterdir()) == set(OUTPUT_NAMES)
    assert set(OUTPUT_NAMES) == {"aggregates.jsonl", "business_questions.json", "aggregation_manifest.json"}
    assert list(tmp_path.iterdir()) == [output]
    manifest = json.loads((output / "aggregation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_mode"] == "demo"
    assert manifest["validation"]["report"]["counts"]["accepted"] == 15
    assert manifest["validation"]["report"]["status"] == "passed"
    assert manifest["mention_schema_version"] == manifest["validation"]["report"]["mention_schema_version"] == 2
    assert manifest["config"]["clause_reference"] == "position"
    assert manifest["validation"]["manifest"]["output_sha256"]["valid_mentions.jsonl"]
    assert all(Path(item["path"]).exists() and file_hash(Path(item["path"])) == item["sha256"] for item in manifest["inputs"])


def test_successful_run_removes_old_intermediates_but_preserves_other_files(tmp_path):
    output = tmp_path / "aggregates"
    output.mkdir()
    legacy = [name + ".jsonl" for name in COUNT_TABLES if name != "aggregates"] + ["aggregation_report.json"]
    for name in legacy:
        (output / name).write_text("old generated artifact", encoding="utf-8")
    notes = output / "my_notes.txt"
    notes.write_text("keep this user file", encoding="utf-8")
    completed = cli("--demo", "--output", output)
    assert completed.returncode == 0, completed.stderr
    assert all(not (output / name).exists() for name in legacy)
    assert notes.read_text(encoding="utf-8") == "keep this user file"
    manifest = json.loads((output / "aggregation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["aggregation_report"]["input_mentions"] == 15
    assert all(manifest["aggregation_report"]["invariants"].values())


def source_files(directory):
    directory.mkdir(parents=True, exist_ok=True)
    pairs = [fixture_case(PAYLOAD, case) for case in PAYLOAD["cases"]]
    mentions, comments, models = (directory / name for name in ("mentions.jsonl", "comments.jsonl", "models.json"))
    mentions.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record, _ in pairs), encoding="utf-8")
    comments.write_text("".join(json.dumps(comment, ensure_ascii=False) + "\n" for _, comment in pairs), encoding="utf-8")
    models.write_text(json.dumps(PAYLOAD["models"]), encoding="utf-8")
    return mentions, comments, models


def test_one_command_can_validate_source_files_and_aggregate_them(tmp_path):
    mentions, comments, models = source_files(tmp_path / "inputs")
    before = {path: path.read_bytes() for path in (mentions, comments, models)}
    output = tmp_path / "aggregates"
    completed = cli("--mentions", mentions, "--comments", comments, "--models", models, "--output", output)
    assert completed.returncode == 0, completed.stderr
    report = json.loads((output / "aggregation_manifest.json").read_text(encoding="utf-8"))["aggregation_report"]
    assert report["input_mode"] == "direct" and report["input_mentions"] == 15
    assert all(report["invariants"].values())
    assert all(path.read_bytes() == contents for path, contents in before.items())
    assert not (tmp_path / "validation").exists()


def test_one_command_rejects_bad_labels_without_creating_outputs(tmp_path):
    mentions, comments, models = source_files(tmp_path / "inputs")
    records = jsonl(mentions)
    records[0]["sentiment"] = "positive"
    mentions.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    output = tmp_path / "blocked"
    completed = cli("--mentions", mentions, "--comments", comments, "--models", models, "--output", output)
    assert completed.returncode == 2
    assert "SCHEMA_ERROR" in json.loads(completed.stderr)["message"]
    assert not output.exists()


@pytest.mark.parametrize("filename", ["aggregates.jsonl", "q3b_counts.jsonl", "aggregation_report.json"])
def test_one_command_cannot_overwrite_a_source_input(filename, tmp_path):
    mentions, comments, models = source_files(tmp_path / "inputs")
    protected = mentions.with_name(filename)
    mentions.rename(protected)
    original = protected.read_bytes()
    completed = cli("--mentions", protected, "--comments", comments, "--models", models, "--output", protected.parent)
    assert completed.returncode == 2
    assert "overwrite source" in json.loads(completed.stderr)["message"]
    assert protected.read_bytes() == original


@pytest.mark.parametrize("mode,extra", [("--demo", "--comments"), ("--validation-dir", "--config")])
def test_cli_rejects_source_options_that_would_be_ignored(mode, extra, validation_bundle, tmp_path):
    selected = [mode] if mode == "--demo" else [mode, validation_bundle]
    completed = cli(*selected, extra, ROOT / "config/analysis.yaml", "--output", tmp_path / "blocked")
    assert completed.returncode == 2
    assert not (tmp_path / "blocked").exists()

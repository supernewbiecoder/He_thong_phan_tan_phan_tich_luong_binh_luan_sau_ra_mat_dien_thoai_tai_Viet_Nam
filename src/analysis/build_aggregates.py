"""Validate, aggregate and answer Q1-Q5: python -m src.analysis.build_aggregates."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from jsonschema.exceptions import SchemaError
import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analysis.aggregation import AGGREGATOR_VERSION, COUNT_TABLES, build_aggregates
from src.analysis.questions import ANALYSIS_VERSION, InferenceSettings, analyze_questions
from src.analysis.validate_inputs import (
    OUTPUT_NAMES as VALIDATION_OUTPUTS, build_parser as validation_parser,
    file_hash, run as run_validation, write_json, write_jsonl,
)
from src.analysis.validation import (
    ROOT, MENTION_SCHEMA_VERSION, VALIDATOR_VERSION, InputError, ValidationConfig, iter_jsonl, strict_json_loads,
)

OUTPUT_NAMES = ("aggregates.jsonl", "business_questions.json", "aggregation_manifest.json")
INTERMEDIATE_OUTPUT_NAMES = tuple(name + ".jsonl" for name in COUNT_TABLES if name != "aggregates") + ("aggregation_report.json",)


def _read_json(path):
    data = strict_json_loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise InputError(f"Expected a JSON object: {path.name}")
    return data


def _read_rows(path):
    rows = []
    for line, row, error in iter_jsonl(path):
        if error:
            raise InputError(f"{path.name} line {line}: {error}; rerun validation")
        rows.append(row)
    return rows


def load_validated_bundle(directory: Path):
    """Require a complete passed run, matched IDs and untouched output hashes.

    Original source input paths need not exist on this machine. The exported
    validation bundle is self-contained and keeps its frozen config/manifest.
    """
    directory = directory.resolve()
    manifest = _read_json(directory / "run_manifest.json")
    hashes = manifest.get("output_sha256")
    if not isinstance(hashes, dict):
        raise InputError("Validation manifest has no output hashes")
    for name in VALIDATION_OUTPUTS[:-1]:
        if not isinstance(hashes.get(name), str) or file_hash(directory / name) != hashes[name]:
            raise InputError(f"Validation checksum mismatch: {name}; rerun validation")
    report = _read_json(directory / "validation_report.json")
    if (report.get("validator_version") != VALIDATOR_VERSION or manifest.get("validator_version") != VALIDATOR_VERSION
            or report.get("mention_schema_version") != MENTION_SCHEMA_VERSION
            or manifest.get("mention_schema_version") != MENTION_SCHEMA_VERSION):
        raise InputError("Validation bundle uses an old contract/validator version; rerun validation for v2")
    if (report.get("status") != "passed" or manifest.get("status") != "passed"
            or report.get("can_build_aggregates") is not True or report.get("row_accounting_ok") is not True):
        raise InputError("Validation gate is not passed; fix input and rerun validate_inputs first")
    if report.get("config") != manifest.get("config") or report.get("data_kind") != manifest.get("data_kind"):
        raise InputError("Validation report and manifest disagree on config/data_kind")
    if report.get("data_kind") not in {"fixture", "provided"}:
        raise InputError("Validation bundle has an unknown data_kind")
    counts = report.get("counts")
    if not isinstance(counts, dict) or type(counts.get("accepted")) is not int or counts["accepted"] <= 0 or counts.get("rejected") != 0:
        raise InputError("Validation report has no usable accepted dataset")
    config = ValidationConfig.from_mapping(report["config"])
    mentions = _read_rows(directory / "valid_mentions.jsonl")
    index = _read_rows(directory / "analysis_index.jsonl")
    if len(mentions) != counts["accepted"] or len(index) != counts["accepted"]:
        raise InputError("Accepted row count disagrees with validation report")
    return mentions, index, config, report, manifest


def build_parser():
    parser = argparse.ArgumentParser(description="Validate mentions, build aggregates and answer Q1-Q5 with video-cluster CI and Holm tests.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--mentions", type=Path, help="Mention JSONL (default: data/aspect_mentions.jsonl)")
    mode.add_argument("--demo", action="store_true", help="Run the 15-mention synthetic aggregation fixture")
    mode.add_argument("--validation-dir", type=Path, help="Reuse an existing passed validation bundle")
    parser.add_argument("--comments", type=Path, help="Clean comments JSONL (default: data/clean_data.jsonl)")
    parser.add_argument("--models", type=Path, help="Model catalog (default: config/pipeline.yaml)")
    parser.add_argument("--config", type=Path, help="Analysis config (default: config/analysis.yaml)")
    parser.add_argument("--schema", type=Path, help="Mention schema (default: contracts/aspect-mention.schema.json)")
    parser.add_argument("--model-version", help="Select one inference version instead of the config default")
    parser.add_argument("--bootstrap-resamples", type=int, default=1000, help="Video bootstrap iterations, at least 1000")
    parser.add_argument("--seed", type=int, default=42, help="Reproducible bootstrap seed")
    parser.add_argument("--output", type=Path, help="Output directory (default: data/aggregates/current, or demo with --demo)")
    return parser


def _run_bundle(directory: Path, output: Path, *, input_mode: str, settings: InferenceSettings):
    directory, output = directory.resolve(), output.resolve()
    if output == directory:
        raise InputError("Aggregate output must use a directory separate from validation inputs")
    protected = {(directory / name).resolve() for name in VALIDATION_OUTPUTS}
    if any((output / name).resolve() in protected for name in OUTPUT_NAMES + INTERMEDIATE_OUTPUT_NAMES):
        raise InputError("Aggregate outputs must not overwrite validation inputs")
    mentions, index, config, validation_report, validation_manifest = load_validated_bundle(directory)
    protected.update(Path(item["path"]).resolve() for item in validation_manifest.get("inputs", []))
    if any((output / name).resolve() in protected for name in OUTPUT_NAMES + INTERMEDIATE_OUTPUT_NAMES):
        raise InputError("Aggregate outputs must not overwrite source input files")
    generated_at = datetime.now(timezone.utc).isoformat()
    result = build_aggregates(mentions, index, config, updated_at=generated_at)
    if result.report["eligibility_counts"] != validation_report.get("eligibility_counts"):
        raise InputError("Aggregate eligibility totals disagree with the validation report")
    report = result.report
    report.update(counts_only=False, config=asdict(config), data_kind=validation_report["data_kind"], validation_status=validation_report["status"], input_mode=input_mode)
    if report["data_kind"] == "fixture" or validation_report.get("usage") == "exploratory_only":
        report["usage"] = "exploratory_only"
    questions = analyze_questions(result, config, validation_report=validation_report, mentions=mentions, settings=settings)
    report.update(analysis_version=ANALYSIS_VERSION, ci_computed=questions["ci_available_count"] > 0,
                  hypothesis_tests_computed=questions["estimable_tests"] > 0,
                  can_publish_business_conclusions=questions["can_publish_business_conclusions"],
                  question_analysis={"status": questions["status"], "estimable_tests": questions["estimable_tests"],
                                     "significant_tests": questions["significant_tests"], "ci_available_count": questions["ci_available_count"],
                                     "answers": {name: row["status"] for name, row in questions["answers"].items()},
                                     "publication_blockers": questions["publication_blockers"]})
    report["notes"] = [note for note in report["notes"] if not note.startswith("No rates,")]
    report["notes"].append("Rates, video-bootstrap CI, Holm tests and conclusion gates are in business_questions.json.")
    manifest = {
        "aggregator_version": AGGREGATOR_VERSION, "generated_at": generated_at,
        "mention_schema_version": MENTION_SCHEMA_VERSION,
        "output_format": "cv12-final-v1", "aggregation_report": report,
        "status": report["status"], "data_kind": report["data_kind"], "usage": report["usage"],
        "config": asdict(config), "validation_validator_version": validation_manifest.get("validator_version"),
        "input_mode": input_mode,
        "analysis_version": ANALYSIS_VERSION, "inference_settings": asdict(settings),
        "inputs": (
            [{"path": str(directory / name), "sha256": file_hash(directory / name)} for name in VALIDATION_OUTPUTS]
            if input_mode == "validated_bundle" else validation_manifest["inputs"]
        ),
        "validation": {"report": validation_report, "manifest": validation_manifest},
        "code_sha256": {name: file_hash(Path(__file__).parent / name) for name in (
            "aggregation.py", "build_aggregates.py", "validation.py", "validate_inputs.py", "questions.py",
        )},
    }
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".aggregates-", dir=output) as temporary:
        staging = Path(temporary)
        write_jsonl(staging / "aggregates.jsonl", result.tables["aggregates"])
        write_json(staging / "business_questions.json", questions)
        manifest["output_sha256"] = {name: file_hash(staging / name) for name in OUTPUT_NAMES[:-1]}
        write_json(staging / "aggregation_manifest.json", manifest)
        for name in OUTPUT_NAMES[:-1]:
            (staging / name).replace(output / name)
        # Prune only known artifacts from the old output format after success.
        # Source collisions were checked above; unrelated user files are kept.
        for name in INTERMEDIATE_OUTPUT_NAMES:
            (output / name).unlink(missing_ok=True)
        (staging / OUTPUT_NAMES[-1]).replace(output / OUTPUT_NAMES[-1])
    return report, output


def run(args):
    settings = InferenceSettings(resamples=args.bootstrap_resamples, seed=args.seed)
    output = args.output or ROOT / "data/aggregates" / ("demo" if args.demo else "current")
    options = (args.comments, args.models, args.config, args.schema, args.model_version)
    if args.validation_dir is not None:
        if any(value is not None for value in options):
            raise InputError("--validation-dir uses the bundle's frozen settings; do not combine it with source/config options")
        return _run_bundle(args.validation_dir, output, input_mode="validated_bundle", settings=settings)
    if args.demo and any(value is not None for value in (args.comments, args.models)):
        raise InputError("--demo cannot be combined with --comments or --models")
    validation_args = validation_parser().parse_args([])
    for name in ("mentions", "comments", "models", "config", "schema", "model_version"):
        if getattr(args, name) is not None:
            setattr(validation_args, name, getattr(args, name))
    if args.demo:
        validation_args.demo = "all"
        validation_args.fixtures = ROOT / "tests/fixtures/aggregation_cases.json"
    # Keep the validation gate, but discard its files when this run finishes.
    # The final manifest retains its report, config and source/code hashes.
    with TemporaryDirectory(prefix="cv12-validation-") as temporary:
        validation_args.output = Path(temporary)
        report, directory = run_validation(validation_args)
        if report["status"] != "passed":
            raise InputError(f"Validation {report['status']}: counts={report['counts']}; issues={report['issue_counts']}")
        return _run_bundle(directory, output, input_mode="demo" if args.demo else "direct", settings=settings)


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report, output = run(args)
    except (InputError, OSError, ValueError, TypeError, KeyError, yaml.YAMLError, SchemaError) as exc:
        print(json.dumps({"status": "input_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "data_kind": report["data_kind"],
                      "usage": report["usage"], "input_mentions": report["input_mentions"],
                      "table_rows": report["table_rows"], "question_analysis": report["question_analysis"],
                      "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

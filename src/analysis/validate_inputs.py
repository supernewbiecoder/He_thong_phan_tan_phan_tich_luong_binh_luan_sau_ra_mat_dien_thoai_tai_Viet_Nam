"""CLI for the CV12 input gate. Run from the repository root with
python -m src.analysis.validate_inputs --help.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import yaml
from jsonschema.exceptions import SchemaError

from src.analysis.validation import (
    ROOT, SCHEMA_PATH, VALIDATOR_VERSION, MENTION_SCHEMA_VERSION, InputError, Issue, ValidationResult,
    build_report, check_catalog, index_comments, issue_rows, iter_jsonl,
    load_comments, load_config, load_model_catalog, load_schema_validator,
    model_catalog_from_data, resolve_duplicates, strict_json_loads, validate_record,
)

OUTPUT_NAMES = (
    "valid_mentions.jsonl", "analysis_index.jsonl", "issues.jsonl",
    "validation_report.json", "run_manifest.json",
)
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "validation_cases.json"


def fixture_case(payload: dict, case: dict):
    """Create independent examples; case names become IDs, never real labels."""
    comment = deepcopy(payload["base_comment"])
    record = deepcopy(payload["base_mention"])
    cid = f"fixture_{case['name']}"
    comment["comment_id"] = cid
    record["comment_id"] = cid
    comment.update(deepcopy(case.get("comment_patch", {})))
    record.update(deepcopy(case.get("patch", {})))
    if "mention_id" not in case.get("patch", {}):
        record["mention_id"] = f"{record['comment_id']}#{record['clause_idx']}#{record['aspect']}"
    for key in case.get("remove_fields", []):
        record.pop(key, None)
    if "raw_record" in case:
        record = deepcopy(case["raw_record"])
    return record, comment


def file_hash(path: Path) -> str:
    with path.open("rb") as fh:
        digest = hashlib.sha256()
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, records) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")


def write_outputs(output: Path, results: list[ValidationResult], report: dict, manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    # Stage complete files before replacing a previous run's artifacts.
    with TemporaryDirectory(prefix=".validation-", dir=output) as temporary:
        staging = Path(temporary)
        write_jsonl(staging / OUTPUT_NAMES[0], (r.record for r in results if r.status == "accepted"))
        write_jsonl(staging / OUTPUT_NAMES[1], (r.analysis for r in results if r.status == "accepted"))
        write_jsonl(staging / OUTPUT_NAMES[2], issue_rows(results))
        write_json(staging / OUTPUT_NAMES[3], report)
        manifest["output_sha256"] = {name: file_hash(staging / name) for name in OUTPUT_NAMES[:-1]}
        write_json(staging / OUTPUT_NAMES[4], manifest)
        # The manifest is replaced last and fingerprints all other outputs.
        for name in OUTPUT_NAMES:
            (staging / name).replace(output / name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate CV12 mentions against contracts, comments, model catalog and scope.")
    parser.add_argument("--mentions", type=Path, help="Mention JSONL (default: data/aspect_mentions.jsonl)")
    parser.add_argument("--comments", type=Path, help="Clean comments JSONL (default: data/clean_data.jsonl)")
    parser.add_argument("--models", type=Path, help="pipeline.yaml or exported models JSON (default: config/pipeline.yaml)")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "analysis.yaml")
    parser.add_argument("--model-version", help="Select one inference version (default: expected_model_version in config)")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--output", type=Path, help="Output directory (default: data/validation or data/validation/demo)")
    parser.add_argument("--demo", nargs="?", const="all", metavar="CASE", help="Use synthetic fixtures: all, valid, or another fixture case name")
    parser.add_argument("--fixtures", type=Path, default=FIXTURE_PATH, help="Synthetic fixture definitions used by --demo")
    return parser


def run(args: argparse.Namespace) -> tuple[dict, Path]:
    if args.demo is not None and any((args.mentions, args.comments, args.models)):
        raise InputError("--demo cannot be combined with --mentions, --comments or --models")
    config = load_config(args.config)
    if args.model_version is not None:
        if not args.model_version.strip() or args.model_version != args.model_version.strip():
            raise InputError("--model-version must be a nonempty version without surrounding whitespace")
        config = replace(config, expected_model_version=args.model_version)
    validator = load_schema_validator(args.schema)
    blank_lines = 0
    input_paths = [args.config, args.schema]
    results = []
    if args.demo is not None:
        input_paths.append(args.fixtures)
        payload = strict_json_loads(args.fixtures.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
            raise InputError("Fixture file must be an object containing a cases list")
        cases = payload["cases"]
        if args.demo != "all":
            cases = [case for case in cases if case.get("name") == args.demo]
        if not cases:
            raise InputError(f"No fixture case found: {args.demo}")
        catalog = model_catalog_from_data(payload["models"])
        pairs = [fixture_case(payload, case) for case in cases]
        comments = index_comments((comment for _, comment in pairs), config)
        records = [(i, record, None) for i, (record, _) in enumerate(pairs, 1)]
    else:
        mentions_path = args.mentions or ROOT / "data" / "aspect_mentions.jsonl"
        comments_path = args.comments or ROOT / "data" / "clean_data.jsonl"
        models_path = args.models or ROOT / "config" / "pipeline.yaml"
        input_paths.extend((mentions_path, comments_path, models_path))
        catalog = load_model_catalog(models_path)
        comments = load_comments(comments_path, config)
        records = iter_jsonl(mentions_path)
    check_catalog(catalog, config)
    output = (args.output or ROOT / "data" / "validation" / ("demo" if args.demo is not None else "current")).resolve()
    resolved_inputs = {path.resolve() for path in input_paths}
    if any((output / name).resolve() in resolved_inputs for name in OUTPUT_NAMES):
        raise InputError("Output artifacts must not overwrite any input file")
    for number, record, error in records:
        if error == "blank":
            blank_lines += 1
        elif error:
            results.append(ValidationResult(number, None, "rejected", [Issue("INVALID_JSON", error)]))
        else:
            results.append(validate_record(record, comments, catalog, config, line_number=number, validator=validator))
    resolve_duplicates(results, config)
    report = build_report(results, blank_lines=blank_lines, data_kind="fixture" if args.demo is not None else "provided")
    report["config"] = asdict(config)
    manifest = {
        "validator_version": VALIDATOR_VERSION, "mention_schema_version": MENTION_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_kind": report["data_kind"], "demo_case": args.demo,
        "config": asdict(config), "status": report["status"],
        "inputs": [{"path": str(p.resolve()), "sha256": file_hash(p)} for p in input_paths],
        "code_sha256": {name: file_hash(Path(__file__).parent / name) for name in ("validation.py", "validate_inputs.py")},
    }
    write_outputs(output, results, report, manifest)
    return report, output


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report, output = run(args)
    except (InputError, OSError, ValueError, TypeError, KeyError, yaml.YAMLError, SchemaError) as exc:
        print(json.dumps({"status": "input_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": report["status"], "data_kind": report["data_kind"],
        "counts": report["counts"], "can_build_aggregates": report["can_build_aggregates"],
        "usage": report["usage"],
        "can_publish_business_conclusions": report["can_publish_business_conclusions"],
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

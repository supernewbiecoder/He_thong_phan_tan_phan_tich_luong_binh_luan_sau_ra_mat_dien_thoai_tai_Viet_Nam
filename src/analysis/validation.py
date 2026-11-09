"""Contract, reference and scope checks for CV12 inputs.

The original mention is never edited. Derived values and question eligibility
are returned separately. This module checks consistency, not label accuracy.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
import unicodedata
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft7Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts" / "aspect-mention.schema.json"
MENTION_SCHEMA_VERSION = 2
VALIDATOR_VERSION = "cv12-validation-v3-contract2"
FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=(ValueError, TypeError))
def _rfc3339_timestamp(value):
    # jsonschema's built-in date-time check otherwise depends on optional
    # packages. Register an explicit check so a fresh install checks dates too.
    if not isinstance(value, str):
        return True  # The schema's type constraint handles non-strings.
    pattern = (
        r"\d{4}-\d{2}-\d{2}[Tt](?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d"
        r"(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)"
    )
    if not re.fullmatch(pattern, value):
        return False
    return datetime.fromisoformat(value.upper().replace("Z", "+00:00")).tzinfo is not None


class InputError(ValueError):
    """Required input or configuration cannot be used safely."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON property: {key}")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def strict_json_loads(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_nonfinite)


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not FORMATS.conforms(value, "date-time"):
        raise ValueError("Expected an RFC3339 timestamp with timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00").replace("z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed


def calculate_days_since_launch(
    published_at: str, launch_date: str, timezone: str = "Asia/Ho_Chi_Minh"
) -> int:
    local_day = parse_timestamp(published_at).astimezone(ZoneInfo(timezone)).date()
    return (local_day - date.fromisoformat(launch_date)).days


def week_since_launch(days: int, window_days: int = 28) -> int | None:
    return days // 7 + 1 if 0 <= days < window_days else None


@dataclass(frozen=True)
class ValidationConfig:
    target_model: str
    predecessor_model: str
    rival_models: tuple[str, str]
    expected_model_version: str
    timezone: str = "Asia/Ho_Chi_Minh"
    window_days: int = 28
    clause_reference: str = "position"
    clause_text_field: str = "text"
    warning_confidence_threshold: float = 0.5

    @property
    def scope(self) -> frozenset[str]:
        return frozenset((self.target_model, self.predecessor_model, *self.rival_models))

    @classmethod
    def from_mapping(cls, data: Any) -> "ValidationConfig":
        if not isinstance(data, dict):
            raise InputError("Analysis config must be a YAML object")
        allowed = set(cls.__dataclass_fields__)
        if set(data) - allowed:
            raise InputError(f"Unknown analysis settings: {sorted(set(data) - allowed)}")
        required = {"target_model", "predecessor_model", "rival_models", "expected_model_version"}
        if required - set(data):
            raise InputError(f"Missing analysis settings: {sorted(required - set(data))}")
        rivals = data["rival_models"]
        if not isinstance(rivals, list) or len(rivals) != 2:
            raise InputError("rival_models must contain exactly two model codes")
        codes = [data["target_model"], data["predecessor_model"], *rivals]
        if any(not isinstance(v, str) or not v.strip() or v != v.strip() or "|" in v for v in codes):
            raise InputError("Scope must contain nonempty individual model codes")
        if len(set(codes)) != 4:
            raise InputError("X, predecessor and two rivals must be four distinct models")
        if not isinstance(data["expected_model_version"], str) or not data["expected_model_version"].strip():
            raise InputError("expected_model_version must be a nonempty string")
        if type(data.get("window_days", 28)) is not int or data.get("window_days", 28) != 28:
            raise InputError("CV12 currently requires a 28-day window")
        if data.get("clause_reference", "position") != "position":
            raise InputError("Contract v2 requires clause_reference=position (zero-based array index)")
        if data.get("clause_text_field", "text") != "text":
            raise InputError("Contract v2 requires clause_text_field=text (original clause text)")
        threshold = data.get("warning_confidence_threshold", 0.5)
        if type(threshold) not in {int, float} or not 0 <= threshold <= 1:
            raise InputError("warning_confidence_threshold must be between 0 and 1")
        tz = data.get("timezone", "Asia/Ho_Chi_Minh")
        try:
            ZoneInfo(tz)
        except (ZoneInfoNotFoundError, TypeError, ValueError) as exc:
            raise InputError(f"Invalid timezone: {tz}") from exc
        return cls(**{**data, "rival_models": tuple(rivals)})


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    field: str = "$"
    severity: str = "error"


@dataclass
class ValidationResult:
    line_number: int
    record: Any
    status: str
    issues: list[Issue] = field(default_factory=list)
    analysis: dict[str, Any] | None = None


def load_config(path: Path) -> ValidationConfig:
    return ValidationConfig.from_mapping(yaml.safe_load(path.read_text(encoding="utf-8-sig")))


def load_model_catalog(path: Path) -> dict[str, dict[str, Any]]:
    """Accept pipeline.yaml, an exported {models: [...]} JSON, or a JSON list.

    Nested rivals are included. Missing dates are not inherited from another
    phone; conflicting explicit dates fail instead of choosing one silently.
    """
    raw = path.read_text(encoding="utf-8-sig")
    data = strict_json_loads(raw) if path.suffix.lower() == ".json" else yaml.safe_load(raw)
    return model_catalog_from_data(data)


def model_catalog_from_data(data: Any) -> dict[str, dict[str, Any]]:
    entries = data.get("models") if isinstance(data, dict) else data
    if not isinstance(entries, list) or not entries:
        raise InputError("Model catalog must contain a nonempty models list")
    catalog: dict[str, dict[str, Any]] = {}

    def add(entry):
        if isinstance(entry, str):
            entry = {"model_id": entry}
        if not isinstance(entry, dict):
            raise InputError("Each catalog entry must be a model object or code")
        code = entry.get("model_id", entry.get("name"))
        if not isinstance(code, str) or not code.strip() or code != code.strip() or "|" in code:
            raise InputError(f"Invalid model code: {code!r}")
        existing = catalog.setdefault(code, {"model_id": code})
        ld = entry.get("launch_date")
        if ld is not None:
            ld = ld.isoformat() if isinstance(ld, date) else ld
            try:
                date.fromisoformat(ld)
            except (ValueError, TypeError) as exc:
                raise InputError(f"Invalid launch_date for {code}: {ld!r}") from exc
            if existing.get("launch_date") not in (None, ld):
                raise InputError(f"Conflicting launch_date values for {code}")
            existing["launch_date"] = ld
        if "title" in entry and not isinstance(entry["title"], str):
            raise InputError(f"title for {code} must be a string")
        for key in ("title", "predecessor_id"):
            if key in entry:
                existing[key] = entry[key]
        aliases = entry.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) or not alias.strip() for alias in aliases):
            raise InputError(f"aliases for {code} must be a list of nonempty strings")
        existing["aliases"] = list(dict.fromkeys([*existing.get("aliases", []), *aliases]))
        rivals = entry.get("rivals", [])
        if not isinstance(rivals, list):
            raise InputError(f"rivals for {code} must be a list")
        for rival in rivals:
            add(rival)

    for entry in entries:
        add(entry)
    return catalog


def check_catalog(catalog: Mapping, config: ValidationConfig) -> None:
    for code in config.scope:
        if code not in catalog:
            raise InputError(f"Scope model is missing from catalog: {code}")
        if not catalog[code].get("launch_date"):
            raise InputError(f"Scope model has no explicit launch_date: {code}")


def load_schema_validator(path: Path = SCHEMA_PATH) -> Draft7Validator:
    schema = strict_json_loads(path.read_text(encoding="utf-8-sig"))
    Draft7Validator.check_schema(schema)
    version_rule = schema.get("properties", {}).get("schema_version") if isinstance(schema, dict) else None
    if not isinstance(version_rule, dict) or version_rule.get("const") != MENTION_SCHEMA_VERSION:
        raise InputError("CV12 requires the current aspect-mention contract v2")
    return Draft7Validator(schema, format_checker=FORMATS)


def validate_schema(record: Any, validator: Draft7Validator | None = None) -> list[Issue]:
    try:
        json.dumps(record, allow_nan=False)
    except (ValueError, TypeError) as exc:
        return [Issue("INVALID_JSON_VALUE", str(exc))]
    validator = validator if validator is not None else load_schema_validator()
    return [
        Issue("SCHEMA_ERROR", error.message, error.json_path)
        for error in sorted(validator.iter_errors(record), key=lambda e: (e.json_path, e.message))
    ]


def iter_jsonl(path: Path):
    """Yield every nonblank line, including malformed lines as rejected results."""
    with path.open(encoding="utf-8-sig") as fh:
        for number, line in enumerate(fh, 1):
            if not line.strip():
                yield number, None, "blank"
                continue
            try:
                yield number, strict_json_loads(line), None
            except ValueError as exc:
                yield number, None, str(exc)


def clause_lookup(comment: Mapping, config: ValidationConfig) -> dict[int, Mapping]:
    if config.clause_reference != "position" or config.clause_text_field != "text":
        raise InputError("Contract v2 requires zero-based clause positions and original text")
    result = {}
    clauses = comment.get("clauses")
    if not isinstance(clauses, list):
        raise InputError("comments.clauses must be a list")
    for position, clause in enumerate(clauses):
        if not isinstance(clause, dict):
            raise InputError("Each clause must be an object")
        if not isinstance(clause.get(config.clause_text_field), str):
            raise InputError(f"Clause has no string {config.clause_text_field}")
        result[position] = clause
    return result


def index_comments(records: Iterable[Mapping], config: ValidationConfig) -> dict[str, Mapping]:
    """Validate the fields consumed by CV12; the raw-comment schema is not
    applied to enriched clean_data, which has additional processing fields.
    """
    indexed = {}
    for record in records:
        if not isinstance(record, dict):
            raise InputError("Each comment must be an object")
        for key in ("comment_id", "video_id", "model", "source"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise InputError(f"Comment has no nonempty {key}")
        for key in ("is_spam", "is_vietnamese"):
            if type(record.get(key)) is not bool:
                raise InputError(f"Comment {record['comment_id']} must have boolean {key}")
        if "author_is_creator" in record and type(record["author_is_creator"]) is not bool:
            raise InputError(f"Comment {record['comment_id']} must have boolean author_is_creator")
        if "author_hash" in record and (not isinstance(record["author_hash"], str)
                                      or not re.fullmatch(r"[0-9a-f]{64}", record["author_hash"])):
            raise InputError(f"Comment {record['comment_id']} must have a 64-character lowercase author_hash")
        if "parent_id" in record and record["parent_id"] is not None and not isinstance(record["parent_id"], str):
            raise InputError(f"Comment {record['comment_id']} must have string or null parent_id")
        try:
            published = parse_timestamp(record.get("published_at"))
            if record.get("fetched_at") is not None and published > parse_timestamp(record["fetched_at"]):
                raise InputError(f"Comment {record['comment_id']} was published after fetched_at")
        except ValueError as exc:
            raise InputError(f"Comment {record['comment_id']}: {exc}") from exc
        clause_lookup(record, config)
        if "clause_count" in record and record["clause_count"] != len(record["clauses"]):
            raise InputError(f"Comment {record['comment_id']} has an inconsistent clause_count")
        cid = record["comment_id"]
        if cid in indexed and indexed[cid] != record:
            raise InputError(f"Conflicting comments with comment_id={cid}")
        indexed[cid] = record
    if not indexed:
        raise InputError("Comments input contains no records")
    return indexed


def load_comments(path: Path, config: ValidationConfig) -> dict[str, Mapping]:
    def records():
        for number, record, error in iter_jsonl(path):
            if error == "blank":
                continue
            if error:
                raise InputError(f"Comments line {number}: {error}")
            yield record
    return index_comments(records(), config)


def validate_reference(record: Mapping, comments: Mapping, config: ValidationConfig) -> list[Issue]:
    comment = comments.get(record["comment_id"])
    if comment is None:
        return [Issue("COMMENT_NOT_FOUND", "comment_id is absent from comments", "$.comment_id")]
    issues = []
    for mention_key, comment_key in (("video_id", "video_id"), ("source", "source"), ("video_model", "model")):
        if record[mention_key] != comment[comment_key]:
            issues.append(Issue("REFERENCE_MISMATCH", f"{mention_key} differs from the comment", f"$.{mention_key}"))
    # All v2 metadata must come from the same comment. Missing source evidence
    # is rejected, never replaced with an invented author flag or parent.
    for key in ("author_hash", "author_is_creator", "parent_id"):
        if key not in comment or record[key] != comment[key]:
            issues.append(Issue("REFERENCE_MISMATCH", f"{key} differs from or is absent in the comment", f"$.{key}"))
    if parse_timestamp(record["published_at"]) != parse_timestamp(comment["published_at"]):
        issues.append(Issue("PUBLISHED_AT_MISMATCH", "Mention and comment timestamps differ", "$.published_at"))
    clause = clause_lookup(comment, config).get(record["clause_idx"])
    if clause is None:
        issues.append(Issue("CLAUSE_NOT_FOUND", "Referenced clause does not exist", "$.clause_idx"))
    elif record["clause_text"] != clause[config.clause_text_field]:
        issues.append(Issue("CLAUSE_TEXT_MISMATCH", "clause_text differs from the referenced clause", "$.clause_text"))
    return issues


def validate_comparison(record: Mapping, catalog: Mapping, config: ValidationConfig):
    """Resolve X's direction; an otherwise valid out-of-scope pair skips Q3b.

    Invalid v2 comparison metadata is rejected by validate_record beforehand.
    """
    other, winner = record.get("compare_with"), record.get("compare_winner")
    if other is None and winner is None:
        return [], False, None
    code = None
    if other is None or winner is None:
        code = "COMPARISON_INCOMPLETE"
    elif other == record["target_model"]:
        code = "SELF_COMPARISON"
    elif other not in catalog:
        code = "UNKNOWN_COMPARISON_MODEL"
    elif other not in config.scope:
        code = "OUT_OF_SCOPE_COMPARISON"
    if code:
        return [Issue(code, "Comparison cannot be used for Q3b", "$.compare_with", "warning")], False, None
    if config.target_model not in (record["target_model"], other):
        return [], False, None
    if winner == "tie":
        outcome = "tie"
    else:
        target_wins = winner == "target"
        x_wins = target_wins if record["target_model"] == config.target_model else not target_wins
        outcome = "win" if x_wins else "loss"
    return [], True, outcome


@lru_cache(maxsize=2048)
def _alias_text(text: str) -> str:
    folded = unicodedata.normalize("NFD", text.casefold().replace("\u0111", "d"))
    folded = "".join(c for c in folded if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", folded).strip()


def find_model_aliases(text: str, catalog: Mapping) -> set[str]:
    """Conservative lexical hints for review, never a target prediction.

    Use catalog aliases/codes/titles containing a digit. Shared aliases and
    aliases contained in a longer phone name cannot identify a unique phone.
    Brand-only words such as 'ss' or 'tao' are not a model ID.
    """
    aliases = defaultdict(set)
    for code, model in catalog.items():
        for value in (code, model.get("title", ""), *model.get("aliases", [])):
            alias = _alias_text(value)
            if alias and any(c.isdigit() for c in alias):
                aliases[alias].add(code)
    normalized = _alias_text(text)
    hits = []
    for alias, codes in aliases.items():
        if len(codes) != 1:
            continue
        for match in re.finditer(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", normalized):
            hits.append((match.start(), match.end(), next(iter(codes))))
    return {
        code for start, end, code in hits
        if not any(a <= start and end <= b and (a < start or end < b) for a, b, _ in hits)
    }


def audit_rule_baseline(record: Mapping, comment: Mapping, comments: Mapping, catalog: Mapping):
    """Expose limitations of CV8-10 rule outputs without changing their labels.

    The seed baseline selects the first aspect, counts polarity keywords,
    uses fixed confidence values and derives comparison direction from polarity.
    These checks flag review candidates; they do not measure model accuracy.
    """
    issues = [Issue("RULE_BASELINE_LABEL", "Rule labels require evaluation before business conclusions", "$.label_source", "warning")]
    if record.get("confidence") is not None:
        issues.append(Issue("HEURISTIC_CONFIDENCE", "Rule confidence is a heuristic score, not a calibrated probability", "$.confidence", "warning"))
    explicit = find_model_aliases(record["clause_text"], catalog)
    parent = comment.get("parent_text")
    if not isinstance(parent, str) or not parent.strip():
        parent_comment = comments.get(comment.get("parent_id"), {})
        parent = parent_comment.get("text", "")
    if not isinstance(parent, str):
        parent = ""
    parent_models = find_model_aliases(parent, catalog)
    target = record["target_model"]
    evidence = "clause_alias" if explicit else "parent_alias" if parent_models else "video_context"
    candidates = explicit or parent_models
    if candidates and target not in candidates:
        issues.append(Issue("TARGET_ALIAS_CONFLICT", "Target conflicts with explicit phone aliases; review clause and parent context", "$.target_model", "warning"))
    elif not candidates:
        issues.append(Issue("BASELINE_TARGET_CONTEXT", "No specific phone alias in clause/parent; video context does not verify the target", "$.target_model", "warning"))
    if len(candidates) > 1:
        evidence = "multiple_aliases"
        issues.append(Issue("MULTIPLE_TARGET_ALIASES", "Multiple phones are named; review which phone each opinion refers to", "$.target_model", "warning"))
    if record.get("compare_with") is not None or record.get("compare_winner") is not None:
        issues.append(Issue("BASELINE_COMPARISON_UNVERIFIED", "The seed rule infers comparison winner from sentiment; verify direction manually", "$.compare_winner", "warning"))
    if record.get("is_owner") is False:
        issues.append(Issue("BASELINE_OWNER_UNVERIFIED", "No owner keyword does not establish that the author has never used the phone", "$.is_owner", "warning"))
    if re.search(r"\b(?:khong|chua|chang|cha|ko|kh|k0)\b", _alias_text(record["clause_text"])):
        issues.append(Issue("NEGATION_REVIEW_REQUIRED", "Keyword polarity may fail on negation; review without auto-flipping sentiment", "$.sentiment", "warning"))
    return issues, {"target_evidence": evidence, "clause_model_aliases": sorted(explicit), "parent_model_aliases": sorted(parent_models)}


def validate_record(
    record: Any, comments: Mapping, catalog: Mapping, config: ValidationConfig,
    *, line_number: int = 1, validator: Draft7Validator | None = None,
) -> ValidationResult:
    issues = validate_schema(record, validator)
    if issues:
        return ValidationResult(line_number, record, "rejected", issues)
    for key in ("mention_id", "comment_id", "video_id", "source", "clause_text", "model_version"):
        if not record[key].strip():
            issues.append(Issue("EMPTY_VALUE", "Value must not be blank", f"$.{key}"))
    expected_id = f"{record['comment_id']}#{record['clause_idx']}#{record['aspect']}"
    if record["mention_id"] != expected_id:
        issues.append(Issue("MENTION_ID_MISMATCH", f"Expected {expected_id}", "$.mention_id"))
    if issues:
        return ValidationResult(line_number, record, "rejected", issues)
    # Other inference versions may refer to another comments snapshot.
    if record["model_version"] != config.expected_model_version:
        return ValidationResult(line_number, record, "excluded", [
            Issue("MODEL_VERSION_NOT_SELECTED", "Inference version is not selected", "$.model_version", "info")
        ])
    target = record["target_model"]
    for code in record["video_model"].split("|"):
        if code not in catalog:
            issues.append(Issue("UNKNOWN_VIDEO_MODEL", f"Unknown video model: {code}", "$.video_model"))
    if target is not None and target not in catalog:
        issues.append(Issue("UNKNOWN_MODEL", f"Unknown target model: {target}", "$.target_model"))
    other = record["compare_with"]
    if other is not None:
        if other == target:
            issues.append(Issue("SELF_COMPARISON", "compare_with must differ from target_model", "$.compare_with"))
        elif other not in catalog:
            issues.append(Issue("UNKNOWN_COMPARISON_MODEL", "compare_with is absent from the model catalog", "$.compare_with"))
    issues.extend(validate_reference(record, comments, config))
    if record.get("defect_type") is not None and record["sentiment"] != "neg":
        issues.append(Issue("DEFECT_WITHOUT_NEGATIVE_SENTIMENT", "A defect label requires negative sentiment", "$.defect_type"))
    if target is None and record.get("days_since_launch") is not None:
        issues.append(Issue("DAYS_WITHOUT_TARGET", "An unresolved target must not have days_since_launch", "$.days_since_launch"))
    if issues:
        return ValidationResult(line_number, record, "rejected", issues)
    comment = comments[record["comment_id"]]
    exclusions = []
    if target is None:
        exclusions.append(Issue("UNKNOWN_TARGET", "Target model is unresolved", "$.target_model", "info"))
    elif target not in config.scope:
        exclusions.append(Issue("OUT_OF_SCOPE_MODEL", "Target is outside the selected four models", "$.target_model", "info"))
    if comment["is_spam"]:
        exclusions.append(Issue("COMMENT_SPAM", "Referenced comment is spam", "$.comment_id", "info"))
    if not comment["is_vietnamese"]:
        exclusions.append(Issue("NON_VIETNAMESE", "Referenced comment is outside language scope", "$.comment_id", "info"))
    if comment.get("author_is_creator") is True:
        exclusions.append(Issue("AUTHOR_IS_CREATOR", "Channel creator replies are outside user-opinion aggregates", "$.comment_id", "info"))
    days = None
    if target is not None and target in config.scope:
        days = calculate_days_since_launch(record["published_at"], catalog[target]["launch_date"], config.timezone)
        if record.get("days_since_launch") is not None and record["days_since_launch"] != days:
            return ValidationResult(line_number, record, "rejected", [
                Issue("DAYS_SINCE_LAUNCH_MISMATCH", f"Received {record['days_since_launch']}; expected {days}", "$.days_since_launch")
            ])
        if week_since_launch(days, config.window_days) is None:
            exclusions.append(Issue("OUTSIDE_WINDOW", f"Day {days} is outside [0, {config.window_days})", "$.published_at", "info"))
    if exclusions:
        return ValidationResult(line_number, record, "excluded", exclusions)
    comparison_issues, eligible_q3b, outcome = validate_comparison(record, catalog, config)
    issues.extend(comparison_issues)
    if record.get("is_owner") is None:
        issues.append(Issue("OWNER_UNKNOWN", "Owner status is not established; retain Q5 denominator", "$.is_owner", "warning"))
    confidence = record.get("confidence")
    if record["label_source"] != "human" and confidence is None:
        issues.append(Issue("CONFIDENCE_UNKNOWN", "Label has no confidence value", "$.confidence", "warning"))
    elif confidence is not None and confidence < config.warning_confidence_threshold:
        issues.append(Issue("LOW_CONFIDENCE", "Confidence is below the warning threshold", "$.confidence", "warning"))
    baseline_audit = None
    if record["label_source"] == "rule":
        baseline_issues, baseline_audit = audit_rule_baseline(record, comment, comments, catalog)
        issues.extend(baseline_issues)
    analysis = {
        "mention_id": record["mention_id"], "model_version": record["model_version"],
        "schema_version": MENTION_SCHEMA_VERSION, "comment_id": record["comment_id"],
        "clause_idx": record["clause_idx"], "author_hash": record["author_hash"], "parent_id": record["parent_id"],
        "line_number": line_number, "days_since_launch": days,
        "week_since_launch": week_since_launch(days, config.window_days),
        "label_source": record["label_source"],
        "author_is_creator": record["author_is_creator"],
        "requires_label_review": any(i.severity == "warning" for i in issues),
        "baseline_audit": baseline_audit,
        "eligible_q1": True, "eligible_q2": target == config.target_model,
        "eligible_q3a": True, "eligible_q3b": eligible_q3b,
        "x_comparison_outcome": outcome,
        "eligible_q4": target in (config.target_model, config.predecessor_model),
        "eligible_q5_denominator": target == config.target_model,
        "eligible_q5_numerator": target == config.target_model and record["sentiment"] == "neg" and record.get("is_owner") is True and record.get("defect_type") is not None,
    }
    return ValidationResult(line_number, record, "accepted", issues, analysis)


def resolve_duplicates(results: list[ValidationResult], config: ValidationConfig) -> None:
    groups = defaultdict(list)
    for result in results:
        if result.status in {"accepted", "excluded"} and result.record["model_version"] == config.expected_model_version:
            groups[result.record["mention_id"]].append(result)
    for group in groups.values():
        if len(group) < 2:
            continue
        fingerprints = {json.dumps(r.record, sort_keys=True, ensure_ascii=False, allow_nan=False) for r in group}
        if len(fingerprints) > 1:
            # Quarantine every member: never keep the first conflicting label.
            for result in group:
                result.status, result.analysis = "rejected", None
                result.issues = [Issue("DUPLICATE_CONFLICT", "Same mention_id has different records", "$.mention_id")]
        else:
            for result in group[1:]:
                result.status, result.analysis = "duplicate", None
                result.issues = [Issue("DUPLICATE_RECORD", "Identical mention already encountered", "$.mention_id", "info")]


def validate_records(
    records: Iterable[Any], comments: Mapping, catalog: Mapping,
    config: ValidationConfig, validator: Draft7Validator | None = None,
) -> list[ValidationResult]:
    check_catalog(catalog, config)
    validator = validator if validator is not None else load_schema_validator()
    results = [validate_record(r, comments, catalog, config, line_number=i, validator=validator) for i, r in enumerate(records, 1)]
    resolve_duplicates(results, config)
    return results


def build_report(results: list[ValidationResult], *, blank_lines: int = 0, data_kind: str = "provided") -> dict:
    statuses = Counter(result.status for result in results)
    accepted = [r for r in results if r.status == "accepted"]
    codes = Counter(issue.code for r in results for issue in r.issues)
    severity = Counter(issue.severity for r in results for issue in r.issues)
    counts = {key: statuses[key] for key in ("accepted", "rejected", "excluded", "duplicate")}
    counts.update(rows_read=len(results), blank_lines=blank_lines)
    report_status = "failed" if counts["rejected"] else "passed" if accepted else "empty"
    baseline = [r for r in accepted if r.record["label_source"] == "rule"]
    clause_aspects = defaultdict(set)
    for result in accepted:
        clause_aspects[(result.record["comment_id"], result.record["clause_idx"])].add(result.record["aspect"])
    return {
        "validator_version": VALIDATOR_VERSION, "mention_schema_version": MENTION_SCHEMA_VERSION,
        "status": report_status, "data_kind": data_kind,
        "counts": counts, "row_accounting_ok": sum(counts[k] for k in ("accepted", "rejected", "excluded", "duplicate")) == len(results),
        "issue_counts": dict(sorted(codes.items())), "issues_by_severity": dict(sorted(severity.items())),
        "accepted_by_model": dict(sorted(Counter(r.record["target_model"] for r in accepted).items())),
        "accepted_by_aspect": dict(sorted(Counter(r.record["aspect"] for r in accepted).items())),
        "accepted_by_sentiment": dict(sorted(Counter(r.record["sentiment"] for r in accepted).items())),
        "accepted_by_label_source": dict(sorted(Counter(r.record["label_source"] for r in accepted).items())),
        "multi_aspect_clause_count": sum(len(aspects) > 1 for aspects in clause_aspects.values()),
        "requires_label_review_rows": sum(r.analysis["requires_label_review"] for r in accepted),
        "creator_status_unknown_rows": sum(r.analysis["author_is_creator"] is None for r in accepted),
        "baseline_audit": {
            "accepted_rows": len(baseline),
            "model_versions": dict(sorted(Counter(r.record["model_version"] for r in baseline).items())),
            "target_evidence": dict(sorted(Counter(r.analysis["baseline_audit"]["target_evidence"] for r in baseline).items())),
            "confidence_kind": "heuristic_not_calibrated" if baseline else None,
            "limitations": [
                "CV8 seed rules choose the first matching aspect, so other aspects can be missing.",
                "CV9 keyword counts do not establish correct polarity for each aspect, negation or sarcasm.",
                "CV10 seed targets use video context and comparison winners use sentiment; verify both.",
            ] if baseline else [],
        },
        "accepted_by_week": dict(sorted(Counter(str(r.analysis["week_since_launch"]) for r in accepted).items())),
        "unknown_target_rows": sum(any(i.code == "UNKNOWN_TARGET" for i in r.issues) for r in results),
        "unknown_owner_rows": sum(r.record.get("is_owner") is None for r in accepted),
        "comparison_fields_present_rows": sum("compare_with" in r.record and "compare_winner" in r.record for r in accepted),
        "owner_defect_fields_present_rows": sum("is_owner" in r.record and "defect_type" in r.record for r in accepted),
        "eligibility_counts": {key: sum(bool(r.analysis[key]) for r in accepted) for key in (
            "eligible_q1", "eligible_q2", "eligible_q3a", "eligible_q3b", "eligible_q4",
            "eligible_q5_denominator", "eligible_q5_numerator",
        )},
        "can_build_aggregates": bool(accepted) and not counts["rejected"],
        "label_accuracy_verified": False,
        "can_publish_business_conclusions": False,
        "usage": "exploratory_only" if baseline or data_kind == "fixture" else "awaiting_label_evaluation",
        "notes": [
            "Synthetic fixtures are only for testing and must not be used as official findings." if data_kind == "fixture" else "Label accuracy and model approval must be verified separately.",
            "Eligibility is not statistical significance; minimum sample sizes, CI and Holm are checked after aggregation.",
            "Absent comparisons or defects may mean no such mentions or incomplete labeling; confirm the handoff.",
            "Q5 denominator retains all eligible mentions about X, including unknown owners and neutral labels.",
        ],
    }


def issue_rows(results: Iterable[ValidationResult]):
    for result in results:
        for issue in result.issues:
            yield {
                "line_number": result.line_number,
                "mention_id": result.record.get("mention_id") if isinstance(result.record, dict) else None,
                "status": result.status, **asdict(issue),
            }

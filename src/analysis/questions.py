"""Q1-Q5 rates, video-cluster inference and guarded business conclusions.

Pairs cluster bootstrap resamples whole (source, video_id) units jointly.
Percentile CI use ratio-of-sums draws. Tests use centered, studentized draws
with cluster delta-method standard errors, not uncentered bootstrap tails.
See Cameron & Miller (2015), sections II.F and VI.C:
https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Iterable, Mapping

import numpy as np

from src.analysis.aggregation import ASPECTS, DEFECT_TYPES, AggregationResult
from src.analysis.validation import MENTION_SCHEMA_VERSION, InputError, ValidationConfig

ANALYSIS_VERSION = "cv12-questions-v3-contract2"
ASPECT_ORDER = tuple(sorted(ASPECTS))
BUSINESS_QUESTIONS = {
    "Q1": "X được đón nhận tốt hay dở?",
    "Q2": "Ưu điểm và nhược điểm của X là gì?",
    "Q3": "So với đối thủ, X mạnh hay yếu ở đâu?",
    "Q4": "Đời trước bị chê gì, đời này đã sửa được chưa?",
    "Q5": "Lỗi gì cần sửa, ưu tiên cái nào?",
}


@dataclass(frozen=True)
class InferenceSettings:
    resamples: int = 1000
    seed: int = 42
    alpha: float = 0.05
    min_count: int = 30
    min_videos: int = 20
    min_defects: int = 20
    min_valid_fraction: float = 0.95

    def __post_init__(self):
        for name, minimum in (("resamples", 1000), ("seed", 0), ("min_count", 30), ("min_videos", 2), ("min_defects", 20)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum:
                raise InputError(f"{name} must be an integer >= {minimum}")
        if self.alpha != 0.05 or type(self.alpha) is bool:
            raise InputError("CV12 requires alpha=0.05")
        if type(self.min_valid_fraction) not in (int, float) or not 0.9 <= self.min_valid_fraction <= 1:
            raise InputError("min_valid_fraction must be between 0.9 and 1")


def holm_adjust(pvalues: Iterable[float | None]) -> list[float | None]:
    """Keep all planned tests in the family; non-estimable tests count as p=1."""
    values = list(pvalues)
    if any(p is not None and (not math.isfinite(p) or not 0 <= p <= 1) for p in values):
        raise InputError("P-values must be finite probabilities or null")
    adjusted = [None] * len(values)
    previous = 0.0
    for rank, i in enumerate(sorted(range(len(values)), key=lambda i: 1.0 if values[i] is None else values[i])):
        value = 1.0 if values[i] is None else values[i]
        previous = min(1.0, max(previous, (len(values) - rank) * value))
        if values[i] is not None:
            adjusted[i] = previous
    return adjusted


def _rng(settings, key):
    digest = hashlib.sha256(f"{settings.seed}|{key}".encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def cluster_inference(
    numerator, denominator, *, key: str, settings: InferenceSettings,
    contrasts=None, null: float = 0.0, test: bool = False, support=None,
    extra_reasons: Iterable[str] = (),
) -> dict:
    """One ratio, paired ratio contrasts, or a joint Wald test over ratios.

    Rows are joint video units; columns are rates. Contrasts can overlap (Q2).
    The cluster influence is (success_g - rate * trials_g) / sum(trials).
    Duplicate bootstrap clusters contribute separately to the bootstrap SE.
    Low effective cluster counts, degenerate SE and failed draws suppress tests.
    """
    num, den = np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float)
    if num.ndim == 1:
        num, den = num[:, None], den[:, None]
    if num.ndim != 2 or den.shape != num.shape or num.shape[1] == 0:
        raise InputError("Cluster numerator and denominator arrays must have the same 2D shape")
    if not np.all(np.isfinite(num)) or not np.all(np.isfinite(den)) or np.any(num < 0) or np.any(num > den):
        raise InputError("Cluster counts require 0 <= numerator <= denominator and finite values")
    if np.any(num != np.floor(num)) or np.any(den != np.floor(den)):
        raise InputError("Cluster counts must be integers")
    mask = np.any(den > 0, axis=1)
    if support is not None:
        support = np.asarray(support)
        if support.shape != mask.shape:
            raise InputError("Bootstrap support must match video units")
        mask |= support > 0
    num, den = num[mask], den[mask]
    groups, columns = num.shape
    matrix = np.eye(columns) if contrasts is None else np.atleast_2d(np.asarray(contrasts, dtype=float))
    if matrix.shape[1] != columns or not np.all(np.isfinite(matrix)) or not math.isfinite(null):
        raise InputError("Invalid contrast matrix or null value")
    dimension = matrix.shape[0]
    totals = den.sum(axis=0)
    ratios = np.divide(num.sum(axis=0), totals, out=np.full(columns, np.nan), where=totals > 0)
    parameter = matrix @ ratios
    effect = parameter - null
    video_counts = (den > 0).sum(axis=0)
    effective = np.divide(totals**2, (den**2).sum(axis=0), out=np.zeros(columns), where=(den**2).sum(axis=0) > 0)
    reasons = list(extra_reasons)
    if np.any(totals == 0):
        reasons.append("zero_denominator")
    if np.any(totals < settings.min_count):
        reasons.append("insufficient_count")
    if np.any(video_counts < settings.min_videos):
        reasons.append("insufficient_videos")
    if np.any(effective + 1e-9 < settings.min_videos):
        reasons.append("concentrated_video_counts")
    result = {
        "estimate": float(effect[0] * 100) if dimension == 1 and np.isfinite(effect[0]) else None,
        "ci95": None, "p_value": None, "standard_error": None, "test_statistic": None,
        "sample_sizes": [int(value) for value in totals],
        "video_counts": [int(value) for value in video_counts],
        "effective_video_counts": [float(value) for value in effective],
        "joint_video_count": groups, "valid_ci_resamples": 0, "valid_test_resamples": 0,
        "status": "insufficient_data" if reasons else "ok", "reasons": sorted(set(reasons)),
        "method": "paired_video_cluster_bootstrap_t" if test else "video_cluster_percentile_bootstrap",
    }
    if reasons:
        return result
    influence = ((num - ratios * den) / totals) @ matrix.T
    covariance = groups / (groups - 1) * influence.T @ influence
    eigenvalues = np.linalg.eigvalsh(covariance)
    if eigenvalues[0] <= max(1e-18, eigenvalues[-1] * 1e-10):
        result.update(status="degenerate", reasons=["zero_variance_or_singular_covariance"])
        return result
    if dimension == 1:
        result["standard_error"] = float(math.sqrt(covariance[0, 0]) * 100)
        observed = abs(effect[0]) / math.sqrt(covariance[0, 0])
    else:
        observed = float(effect @ np.linalg.solve(covariance, effect))
    if test:
        result["test_statistic"] = float(observed)
    rng, draws, null_statistics = _rng(settings, key), [], []
    for start in range(0, settings.resamples, 100):
        size = min(100, settings.resamples - start)
        weights = rng.multinomial(groups, np.full(groups, 1 / groups), size=size)
        bootstrap_den = weights @ den
        valid = np.all(bootstrap_den > 0, axis=1)
        weights, bootstrap_den = weights[valid], bootstrap_den[valid]
        if not len(weights):
            continue
        bootstrap_ratios = (weights @ num) / bootstrap_den
        parameters = bootstrap_ratios @ matrix.T
        if dimension == 1:
            draws.extend((parameters[:, 0] - null).tolist())
        if not test:
            continue
        centered = parameters - parameter
        bootstrap_influence = ((num[None, :, :] - bootstrap_ratios[:, None, :] * den[None, :, :])
                               / bootstrap_den[:, None, :]) @ matrix.T
        bootstrap_covariance = groups / (groups - 1) * np.einsum("bg,bgi,bgj->bij", weights, bootstrap_influence, bootstrap_influence)
        eig = np.linalg.eigvalsh(bootstrap_covariance)
        usable = eig[:, 0] > np.maximum(1e-18, eig[:, -1] * 1e-10)
        if dimension == 1:
            null_statistics.extend((np.abs(centered[usable, 0]) / np.sqrt(bootstrap_covariance[usable, 0, 0])).tolist())
        elif np.any(usable):
            solved = np.linalg.solve(bootstrap_covariance[usable], centered[usable, :, None])[:, :, 0]
            null_statistics.extend(np.einsum("bi,bi->b", centered[usable], solved).tolist())
    result["valid_ci_resamples"] = len(draws) if dimension == 1 else 0
    result["valid_test_resamples"] = len(null_statistics)
    minimum = math.ceil(settings.resamples * settings.min_valid_fraction)
    if dimension == 1 and len(draws) >= minimum:
        result["ci95"] = [float(value * 100) for value in np.quantile(draws, [0.025, 0.975])]
    if test and len(null_statistics) >= minimum:
        exceedances = np.count_nonzero(np.asarray(null_statistics) >= observed - 1e-12)
        result["p_value"] = float((1 + exceedances) / (1 + len(null_statistics)))
    elif test or (dimension == 1 and result["ci95"] is None):
        result.update(status="unstable_bootstrap", reasons=["too_many_invalid_bootstrap_draws"])
    return result


class _Counts:
    def __init__(self, units, rows):
        self.units, self.rows = units, rows
        self.positions = {unit: i for i, unit in enumerate(units)}

    def array(self, numerator, denominator, **filters):
        num, den = np.zeros(len(self.units)), np.zeros(len(self.units))
        for row in self.rows:
            if all(row.get(key) == value for key, value in filters.items()):
                i = self.positions[(row["source"], row["video_id"])]
                num[i] += sum(row.get(key, 0) for key in numerator)
                den[i] += sum(row.get(key, 0) for key in denominator)
        return num, den

    def sentiment(self, **filters):
        pos, den = self.array(("n_pos",), ("n_pos", "n_neg"), **filters)
        neg, _ = self.array(("n_neg",), ("n_pos", "n_neg"), **filters)
        neu, _ = self.array(("n_neu",), ("n_pos", "n_neg", "n_neu"), **filters)
        return pos, neg, neu, den


def _summary(counts, filters, key, settings):
    pos, neg, neu, den = counts.sentiment(**filters)
    estimate = cluster_inference(pos, den, key=key, settings=settings)
    praise, interval = estimate["estimate"], estimate["ci95"]
    return {
        **filters, "n_pos": int(pos.sum()), "n_neg": int(neg.sum()), "n_neu": int(neu.sum()),
        "n_total": int((pos + neg + neu).sum()), "n_opinionated": int(den.sum()),
        "praise_pct": praise, "criticism_pct": None if praise is None else 100 - praise,
        "net": None if praise is None else 2 * praise - 100,
        "praise_ci95": interval,
        "criticism_ci95": None if interval is None else [100 - interval[1], 100 - interval[0]],
        "net_ci95": None if interval is None else [2 * interval[0] - 100, 2 * interval[1] - 100],
        "inference": estimate,
    }


def _contrast(left, right, key, settings, *, extra_reasons=()):
    return cluster_inference(np.column_stack((left[0], right[0])), np.column_stack((left[1], right[1])),
                             key=key, settings=settings, contrasts=[[1, -1]], test=True,
                             extra_reasons=extra_reasons)


def _test_row(identifier, inference, **fields):
    return {"test_id": identifier, **fields, **inference, "p_adjusted": None, "significant": False}


def _family(name, tests, settings):
    adjusted = holm_adjust(row["p_value"] for row in tests)
    for row, value in zip(tests, adjusted):
        row.update(family=name, p_adjusted=value, significant=value is not None and value < settings.alpha)
    return {"planned_tests": len(tests), "estimable_tests": sum(row["p_value"] is not None for row in tests),
            "method": "Holm", "alpha": settings.alpha}


def _candidates(mentions, *, target, aspect=None, defect=None):
    rows = [row for row in mentions if row["target_model"] == target and
            (aspect is None or row["aspect"] == aspect) and row["sentiment"] in {"pos", "neg"} and
            (defect is None or (row.get("defect_type") == defect and row.get("is_owner") is True and row["sentiment"] == "neg"))]
    rows.sort(key=lambda row: (row["label_source"] != "human", -(row.get("confidence") or 0), row["mention_id"]))
    # Include both praise and criticism when present; never claim these quotes
    # have been reviewed just because their model confidence is high.
    ordered = [next((row for row in rows if row["sentiment"] == label), None) for label in ("pos", "neg")]
    ordered += rows
    selected, seen = [], set()
    for row in ordered:
        if row is None or (row["comment_id"], row["clause_idx"]) in seen:
            continue
        seen.add((row["comment_id"], row["clause_idx"]))
        selected.append({key: row.get(key) for key in ("mention_id", "clause_text", "sentiment", "label_source", "confidence")})
        selected[-1]["requires_human_review"] = True
        if len(selected) == 3:
            break
    return selected


def _answer_summaries(test_groups, publication_blockers):
    """Expose exactly five answers; unsupported findings never enter conclusions."""
    answers = {}
    for name, tests in test_groups.items():
        supported = [row for row in tests if row["conclusion_allowed"]]
        estimable = sum(row["p_adjusted"] is not None for row in tests)
        status = (
            "supported_findings" if supported else
            "insufficient_data" if not estimable else
            "label_evaluation_required" if publication_blockers else
            "no_significant_evidence"
        )
        answers[name] = {
            "question": BUSINESS_QUESTIONS[name], "status": status,
            "planned_tests": len(tests), "estimable_tests": estimable,
            "significant_tests": sum(row["significant"] for row in tests),
            "conclusions": [
                {key: row[key] for key in ("test_id", "aspect", "compare_with", "defect_type", "conclusion") if key in row}
                for row in supported
            ],
            "unavailable_test_reasons": sorted({reason for row in tests for reason in row["reasons"]}),
            "publication_blockers": list(publication_blockers),
        }
    return answers


def analyze_questions(
    aggregates: AggregationResult, config: ValidationConfig, *, validation_report: Mapping,
    mentions: Iterable[Mapping] = (), settings: InferenceSettings | None = None,
) -> dict:
    settings, mentions = settings or InferenceSettings(), list(mentions)
    units = sorted((row["source"], row["video_id"]) for row in aggregates.tables["video_units"])
    if len(units) != len(set(units)) or not units:
        raise InputError("Analysis requires unique source/video bootstrap units")
    counts = _Counts(units, aggregates.tables["aggregates"])
    peers = (config.predecessor_model, *config.rival_models)
    models = (config.target_model, *peers)
    x = config.target_model
    publication_blockers = []
    if validation_report.get("data_kind") != "provided":
        publication_blockers.append("synthetic_or_unconfirmed_dataset")
    if validation_report.get("label_accuracy_verified") is not True:
        publication_blockers.append("label_accuracy_not_verified")
    if aggregates.report["counts_by_label_source"].get("rule", 0):
        publication_blockers.append("rule_baseline_labels")
    if aggregates.report["creator_status_unknown_rows"]:
        publication_blockers.append("creator_status_unknown")
    label_gate = not publication_blockers
    overall = [_summary(counts, {"target_model": model}, f"overall/{model}", settings) for model in models]
    weekly = [_summary(counts, {"target_model": model, "week_since_launch": week}, f"weekly/{model}/{week}", settings)
              for model in models for week in range(1, 5)]
    x_pos, x_neg, _, x_den = counts.sentiment(target_model=x)
    absolute = _test_row("Q1/reception", cluster_inference(x_pos, x_den, key="Q1/reception", settings=settings, null=0.5, test=True))
    q1_tests = [absolute]
    for peer in peers:
        pos, _, _, den = counts.sentiment(target_model=peer)
        q1_tests.append(_test_row(f"Q1/{peer}", _contrast((x_pos, x_den), (pos, den), f"Q1/{peer}", settings), compare_with=peer))
    q2, matrix, omnibus, pairwise, q3b, q4 = [], [], [], [], [], []
    comparisons = _Counts(units, aggregates.tables["q3b_counts"])
    for aspect in ASPECT_ORDER:
        summaries = [_summary(counts, {"target_model": model, "aspect": aspect}, f"aspect/{model}/{aspect}", settings) for model in models]
        matrix.extend(summaries)
        x_summary = summaries[0]
        ax_pos, ax_neg, _, ax_den = counts.sentiment(target_model=x, aspect=aspect)
        q2.append(_test_row(f"Q2/{aspect}", _contrast((ax_neg, ax_den), (x_neg, x_den), f"Q2/{aspect}", settings),
                            aspect=aspect, summary=x_summary, sample_candidates=_candidates(mentions, target=x, aspect=aspect)))
        group_values = [counts.sentiment(target_model=model, aspect=aspect) for model in models]
        joint = cluster_inference(np.column_stack([value[0] for value in group_values]),
                                  np.column_stack([value[3] for value in group_values]),
                                  key=f"Q3a/omnibus/{aspect}", settings=settings,
                                  contrasts=[[1, -1, 0, 0], [1, 0, -1, 0], [1, 0, 0, -1]], test=True)
        omnibus.append(_test_row(f"Q3a/omnibus/{aspect}", joint, aspect=aspect))
        for peer, values in zip(peers, group_values[1:]):
            pairwise.append(_test_row(f"Q3a/{aspect}/{peer}", _contrast((ax_pos, ax_den), (values[0], values[3]), f"Q3a/{aspect}/{peer}", settings), aspect=aspect, compare_with=peer))
        wins, decisive = comparisons.array(("n_x_win",), ("n_x_win", "n_x_loss"), aspect=aspect)
        losses, _ = comparisons.array(("n_x_loss",), ("n_x_win", "n_x_loss"), aspect=aspect)
        ties, total = comparisons.array(("n_tie",), ("n_total",), aspect=aspect)
        win_summary = cluster_inference(wins, decisive, key=f"Q3b/rate/{aspect}", settings=settings, support=total)
        q3b.append(_test_row(f"Q3b/{aspect}", cluster_inference(wins, decisive, key=f"Q3b/test/{aspect}", settings=settings, support=total, null=0.5, test=True),
                             aspect=aspect, n_x_win=int(wins.sum()), n_x_loss=int(losses.sum()), n_tie=int(ties.sum()),
                             n_decisive=int(decisive.sum()), win_pct=win_summary["estimate"], win_ci95=win_summary["ci95"]))
        _, previous_neg, _, previous_den = counts.sentiment(target_model=config.predecessor_model, aspect=aspect)
        q4.append(_test_row(f"Q4/{aspect}", _contrast((previous_neg, previous_den), (ax_neg, ax_den), f"Q4/{aspect}", settings),
                            aspect=aspect, predecessor_criticism_pct=summaries[1]["criticism_pct"], current_criticism_pct=x_summary["criticism_pct"]))
    defect_counts = _Counts(units, aggregates.tables["q5_defects"])
    denominators = _Counts(units, aggregates.tables["q5_denominators"])
    q5 = []
    for defect in DEFECT_TYPES:
        weeks, arrays = [], []
        for week in range(1, 5):
            num, _ = defect_counts.array(("n_defect",), ("n_denominator",), defect_type=defect, week_since_launch=week)
            den, _ = denominators.array(("n_total",), ("n_total",), week_since_launch=week)
            arrays.append((num, den))
            rate = cluster_inference(num, den, key=f"Q5/rate/{defect}/{week}", settings=settings)
            weeks.append({"week_since_launch": week, "n_defect": int(num.sum()), "n_denominator": int(den.sum()),
                          "defect_mention_pct": rate["estimate"], "ci95": rate["ci95"], "inference": rate})
        early = tuple(arrays[0][i] + arrays[1][i] for i in (0, 1))
        late = tuple(arrays[2][i] + arrays[3][i] for i in (0, 1))
        total_defects = int(early[0].sum() + late[0].sum())
        reasons = ["insufficient_defect_mentions"] if total_defects < settings.min_defects else []
        trend = _contrast(late, early, f"Q5/trend/{defect}", settings, extra_reasons=reasons)
        q5.append(_test_row(f"Q5/{defect}", trend, defect_type=defect, n_defect=total_defects, weekly=weeks,
                            early_pct=None if not early[1].sum() else float(100 * early[0].sum() / early[1].sum()),
                            late_pct=None if not late[1].sum() else float(100 * late[0].sum() / late[1].sum()),
                            sample_candidates=_candidates(mentions, target=x, defect=defect)))
    families = {"Q1": _family("Q1", q1_tests, settings), "Q2": _family("Q2", q2, settings),
                "Q3": _family("Q3", omnibus + pairwise + q3b, settings), "Q4": _family("Q4", q4, settings),
                "Q5": _family("Q5", q5, settings)}
    omnibus_by_aspect = {row["aspect"]: row for row in omnibus}
    for row in pairwise:
        row["passes_omnibus_gate"] = omnibus_by_aspect[row["aspect"]]["significant"]
        row["significant"] &= row["passes_omnibus_gate"]
    all_tests = q1_tests + q2 + omnibus + pairwise + q3b + q4 + q5
    for row in all_tests:
        row["conclusion_allowed"] = label_gate and row["significant"]
        row["conclusion"] = "Chưa đủ bằng chứng" if label_gate else "Chưa đủ điều kiện kết luận: nhãn chưa được kiểm chứng"
        if row["status"] != "ok":
            row["conclusion"] = "Không đủ dữ liệu hoặc biến thiên để kiểm định"
    for row in q1_tests:
        if row["conclusion_allowed"]:
            row["conclusion"] = ("Khen nhiều hơn chê" if row["estimate"] > 0 else "Chê nhiều hơn khen") if row is absolute else ("X được đón nhận tốt hơn" if row["estimate"] > 0 else "X được đón nhận kém hơn")
    for row in q2:
        if row["conclusion_allowed"]:
            row["conclusion"] = "Nhược điểm tương đối" if row["estimate"] > 0 else "Ưu điểm tương đối"
    for row in pairwise:
        if row["conclusion_allowed"]:
            row["conclusion"] = "X mạnh hơn" if row["estimate"] > 0 else "X yếu hơn"
    for row in omnibus:
        if row["conclusion_allowed"]:
            row["conclusion"] = "Có khác biệt giữa các máy ở khía cạnh này"
    for row in q3b:
        if label_gate and row["status"] == "ok" and not row["significant"]:
            row["conclusion"] = "Chưa phân định"
        if row["conclusion_allowed"]:
            row["conclusion"] = "X thắng nhiều hơn" if row["estimate"] > 0 else "X thua nhiều hơn"
    for row in q4:
        if row["conclusion_allowed"]:
            row["conclusion"] = "Đã cải thiện" if row["estimate"] > 0 else "Tệ hơn"
    for row in q5:
        candidate = "P3" if row["n_defect"] < settings.min_defects else None
        if row["p_adjusted"] is not None:
            candidate = "P1" if row["significant"] and row["estimate"] > 0 else "P2"
        row["priority_candidate"] = candidate
        row["priority"] = candidate if label_gate else None
        row["priority_requires_label_validation"] = not label_gate
        row["trend"] = "not_testable" if row["p_adjusted"] is None else "no_significant_change"
        if row["significant"]:
            row["trend"] = "significant_increase" if row["estimate"] > 0 else "significant_decrease"
            if row["conclusion_allowed"]:
                row["conclusion"] = "Lượt nhắc lỗi tăng có ý nghĩa" if row["estimate"] > 0 else "Lượt nhắc lỗi giảm có ý nghĩa"
    ci_count = (sum(row["praise_ci95"] is not None for row in overall + weekly + matrix)
                + sum(row["win_ci95"] is not None for row in q3b)
                + sum(week["ci95"] is not None for row in q5 for week in row["weekly"])
                + sum(row["ci95"] is not None for row in all_tests))
    answers = _answer_summaries({
        "Q1": q1_tests, "Q2": q2, "Q3": omnibus + pairwise + q3b, "Q4": q4, "Q5": q5,
    }, publication_blockers)
    return {
        "analysis_version": ANALYSIS_VERSION, "mention_schema_version": MENTION_SCHEMA_VERSION,
        "status": "completed", "settings": asdict(settings),
        "config": asdict(config), "label_sources": dict(aggregates.report["counts_by_label_source"]),
        "label_accuracy_verified": validation_report.get("label_accuracy_verified") is True,
        "data_kind": validation_report.get("data_kind"), "label_handoff_verified": label_gate,
        "publication_blockers": publication_blockers, "answers": answers,
        "can_publish_business_conclusions": label_gate and any(row["significant"] for row in all_tests),
        "usage": "exploratory_only" if not label_gate else "statistical_evidence",
        "q1": {"overall": overall, "weekly": weekly, "tests": q1_tests},
        "q2": q2, "q3a": {"matrix": matrix, "omnibus": omnibus, "pairwise": pairwise}, "q3b": q3b,
        "q4": q4, "q5": q5, "test_families": families,
        "estimable_tests": sum(row["p_value"] is not None for row in all_tests),
        "significant_tests": sum(row["significant"] for row in all_tests),
        "ci_available_count": ci_count,
        "protocol": {
            "bootstrap_unit": ["source", "video_id"], "numpy_version": np.__version__,
            "ci_method": "95% marginal percentile CI; not simultaneous Holm-adjusted intervals",
            "test_method": "Centered pairs cluster bootstrap-t; joint bootstrap Wald test for Q3a omnibus",
            "q2": "Aspect criticism minus overall X criticism, jointly recomputed in every resample",
            "holm": "One fixed family per question; untestable planned hypotheses retained as p=1 internally",
            "q1": "Four tests: X versus 50% praise, plus X versus predecessor and two rivals",
            "q3": "45 planned tests: nine omnibus, 27 X-peer contrasts and nine direct-comparison tests; posthoc also requires omnibus rejection",
            "q5": "P2 includes significant decreases; >=20 defects with unavailable trend test gets no priority",
            "limitations": [
                "Cluster bootstrap is approximate; minimum video/effective-video counts are an operational guard, not a validity guarantee.",
                "Clustering by video does not remove dependence of the same author across different videos.",
                "A statistically significant result cannot validate rule/model labels or establish causal product improvements.",
                "Sample quotations require human review. No extrapolation from the four launch weeks is performed.",
            ],
        },
    }

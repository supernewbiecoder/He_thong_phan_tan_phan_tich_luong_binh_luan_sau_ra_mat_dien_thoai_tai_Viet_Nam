"""Numerical, inference-gating and Q1-Q5 integration checks."""
from copy import deepcopy
import json
import math
import subprocess
import sys

import numpy as np
import pytest

from src.analysis.aggregation import AggregationResult, DEFECT_TYPES
from src.analysis.questions import InferenceSettings, analyze_questions, cluster_inference, holm_adjust
from src.analysis.validation import ROOT, InputError, load_config


@pytest.mark.parametrize("values,expected", [
    ([0.01, 0.03, 0.04, None], [0.04, 0.09, 0.09, None]),
    ([0.04, 0.001, 0.02], [0.04, 0.003, 0.04]),
    ([None, None], [None, None]),
    ([0.0, 1.0], [0.0, 1.0]),
])
def test_holm_known_values_and_planned_missing_hypotheses(values, expected):
    actual = holm_adjust(values)
    for value, target in zip(actual, expected):
        assert value is None if target is None else value == pytest.approx(target)


def test_missing_tests_are_not_dropped_from_holm_family():
    values = [0.002] + [None] * 44
    assert holm_adjust(values)[0] == pytest.approx(0.09)


@pytest.mark.parametrize("values", [[float("nan")], [-0.1], [1.1]])
def test_holm_rejects_nonprobabilities(values):
    with pytest.raises(InputError):
        holm_adjust(values)


@pytest.mark.parametrize("patch", [{"resamples": 999}, {"seed": -1}, {"min_videos": 1}, {"min_count": 29}, {"min_defects": 19}, {"alpha": 0.1}, {"resamples": True}, {"min_valid_fraction": float("nan")}])
def test_inference_settings_are_checked(patch):
    with pytest.raises(InputError):
        InferenceSettings(**patch)


def test_ratio_uses_summed_counts_not_average_of_video_percentages():
    result = cluster_inference([10, 0], [10, 90], key="weighted", settings=InferenceSettings(min_videos=2))
    assert result["estimate"] == 10


def test_zero_denominator_is_null_instead_of_zero_percent():
    result = cluster_inference([0] * 30, [0] * 30, key="empty", settings=InferenceSettings())
    assert result["estimate"] is result["ci95"] is result["p_value"] is None
    assert "zero_denominator" in result["reasons"]


def test_single_video_never_yields_a_confident_interval():
    result = cluster_inference([700], [1000], key="one-video", settings=InferenceSettings())
    assert result["estimate"] == 70
    assert result["ci95"] is None and "insufficient_videos" in result["reasons"]


def test_concentration_in_one_video_blocks_inference_even_with_many_ids():
    result = cluster_inference([5000] + [0] * 39, [10000] + [1] * 39, key="concentration", settings=InferenceSettings())
    assert result["video_counts"] == [40]
    assert result["effective_video_counts"][0] < 2
    assert "concentrated_video_counts" in result["reasons"] and result["p_value"] is None


def test_constant_rates_are_not_treated_as_zero_uncertainty():
    result = cluster_inference([100] * 40, [100] * 40, key="boundary", settings=InferenceSettings(), null=0.5, test=True)
    assert result["status"] == "degenerate"
    assert result["ci95"] is result["p_value"] is None


def test_null_centered_studentized_bootstrap_detects_large_effect_and_is_reproducible():
    numerator = np.array([70 + i % 10 for i in range(40)])
    denominator = np.full(40, 100)
    settings = InferenceSettings()
    result = cluster_inference(numerator, denominator, key="strong", settings=settings, null=0.5, test=True)
    assert result["status"] == "ok"
    assert result["p_value"] == pytest.approx(1 / 1001)
    assert result["ci95"][0] > 20 and result["ci95"][1] < 30
    assert result["valid_test_resamples"] == 1000
    assert result == cluster_inference(numerator, denominator, key="strong", settings=settings, null=0.5, test=True)


def test_exact_null_effect_does_not_become_significant():
    numerator = np.array([40, 60] * 20)
    result = cluster_inference(numerator, np.full(40, 100), key="null", settings=InferenceSettings(), null=0.5, test=True)
    assert result["estimate"] == 0
    assert result["p_value"] == 1
    assert result["ci95"][0] < 0 < result["ci95"][1]


def test_duplicating_mentions_within_videos_does_not_create_independent_samples():
    numerator, denominator = np.array([40, 60, 45, 55] * 10), np.full(40, 100)
    settings = InferenceSettings()
    first = cluster_inference(numerator, denominator, key="replication", settings=settings, null=0.5, test=True)
    repeated = cluster_inference(numerator * 100, denominator * 100, key="replication", settings=settings, null=0.5, test=True)
    assert first["ci95"] == pytest.approx(repeated["ci95"])
    assert first["standard_error"] == pytest.approx(repeated["standard_error"])
    assert first["p_value"] == repeated["p_value"]


def test_paired_overlap_standard_error_includes_covariance():
    numerator = np.column_stack((np.array([40, 50, 60, 50] * 10), np.array([30, 39, 51, 40] * 10)))
    denominator = np.full_like(numerator, 100)
    result = cluster_inference(numerator, denominator, key="paired", settings=InferenceSettings(), contrasts=[[1, -1]], test=True)
    means = numerator.sum(axis=0) / denominator.sum(axis=0)
    contributions = ((numerator - means * denominator) / denominator.sum(axis=0)) @ np.array([1, -1])
    expected_se = 100 * math.sqrt(40 / 39 * np.sum(contributions**2))
    assert result["standard_error"] == pytest.approx(expected_se)
    assert result["estimate"] == pytest.approx(10)


def test_many_invalid_bootstrap_draws_are_reported_not_silently_discarded():
    numerator, denominator = np.zeros((22, 2)), np.zeros((22, 2))
    numerator[:2, 0], denominator[:2, 0] = [20, 80], 100
    numerator[2:, 1], denominator[2:, 1] = [30, 70] * 10, 100
    result = cluster_inference(numerator, denominator, key="unstable", settings=InferenceSettings(min_videos=2), contrasts=[[1, -1]], test=True)
    assert result["status"] == "unstable_bootstrap"
    assert result["valid_test_resamples"] < 950 and result["p_value"] is None


def test_joint_wald_bootstrap_rejects_different_group_rates():
    rng = np.random.default_rng(123)
    numerator = rng.binomial(100, [0.8, 0.3, 0.4, 0.5], size=(60, 4))
    denominator = np.full_like(numerator, 100)
    result = cluster_inference(numerator, denominator, key="omnibus", settings=InferenceSettings(),
                               contrasts=[[1, -1, 0, 0], [1, 0, -1, 0], [1, 0, 0, -1]], test=True)
    assert result["status"] == "ok" and result["p_value"] < 0.01
    assert result["test_statistic"] > 0 and result["valid_test_resamples"] >= 950


def test_clustered_null_simulations_do_not_systematically_reject():
    # Beta-binomial videos deliberately have much more within-video dependence
    # than independent Bernoulli mentions. This catches treating n_mentions as G.
    rng = np.random.default_rng(8822)
    rejected = 0
    for simulation in range(20):
        latent_rate = rng.beta(2, 2, size=50)
        numerator = rng.binomial(100, latent_rate)
        result = cluster_inference(numerator, np.full(50, 100), key=f"null-simulation/{simulation}",
                                   settings=InferenceSettings(), null=0.5, test=True)
        assert result["p_value"] is not None
        rejected += result["p_value"] < 0.05
    assert rejected <= 4, "A nominal 5% test must not reject most clustered null datasets"


def test_all_sampling_draws_stay_inside_rate_and_net_ranges():
    result = cluster_inference([20, 80] * 20, [100] * 40, key="ranges", settings=InferenceSettings())
    assert 0 <= result["ci95"][0] <= result["ci95"][1] <= 100


@pytest.fixture(scope="module")
def plentiful_counts():
    config = load_config(ROOT / "config/analysis.yaml")
    rng = np.random.default_rng(1234)
    tables = {"aggregates": [], "video_units": [], "q3b_counts": [], "q5_denominators": [], "q5_defects": []}
    models = [config.target_model, config.predecessor_model, *config.rival_models]
    for g in range(60):
        video = f"video_{g:03}"
        common = {"source": "youtube", "video_id": video, "model_version": config.expected_model_version}
        tables["video_units"].append(common)
        for week in range(1, 5):
            for m, model in enumerate(models):
                for aspect in ("BATTERY", "CAMERA"):
                    probability = [0.8, 0.25, 0.5, 0.6][m] if aspect == "BATTERY" else [0.45, 0.45, 0.5, 0.6][m]
                    pos = int(rng.binomial(100, probability))
                    tables["aggregates"].append({**common, "target_model": model, "aspect": aspect,
                                                  "week_since_launch": week, "n_pos": pos, "n_neg": 100 - pos, "n_neu": 10})
            tables["q5_denominators"].append({**common, "target_model": config.target_model, "week_since_launch": week, "n_total": 220})
            for defect in DEFECT_TYPES:
                n_defect = 0
                if defect == "BATTERY_DRAIN":
                    n_defect = 2 + g % 3 if week <= 2 else 20 + g % 7
                if defect == "OVERHEAT":
                    n_defect = 20 + g % 5 if week <= 2 else 2 + g % 4
                tables["q5_defects"].append({**common, "target_model": config.target_model, "week_since_launch": week,
                                            "defect_type": defect, "n_defect": n_defect, "n_denominator": 220})
        win = int(rng.binomial(100, 0.8))
        tables["q3b_counts"].append({**common, "target_model": config.target_model, "aspect": "BATTERY", "week_since_launch": 1,
                                   "n_x_win": win, "n_x_loss": 100 - win, "n_tie": 10, "n_total": 110})
    result = AggregationResult(tables, {"counts_by_label_source": {"human": 100}, "creator_status_unknown_rows": 0})
    return result, config


@pytest.fixture(scope="module")
def ample_analysis(plentiful_counts):
    aggregates, config = plentiful_counts
    return analyze_questions(aggregates, config, validation_report={"data_kind": "provided", "label_accuracy_verified": True})


def test_all_five_questions_have_fixed_multiplicity_families(ample_analysis):
    assert {name: value["planned_tests"] for name, value in ample_analysis["test_families"].items()} == {"Q1": 4, "Q2": 9, "Q3": 45, "Q4": 9, "Q5": 9}
    assert len(ample_analysis["q1"]["weekly"]) == 16
    assert len(ample_analysis["q3a"]["matrix"]) == 36


def test_five_answer_summaries_only_publish_supported_findings(ample_analysis):
    groups = {
        "Q1": ample_analysis["q1"]["tests"], "Q2": ample_analysis["q2"],
        "Q3": ample_analysis["q3a"]["omnibus"] + ample_analysis["q3a"]["pairwise"] + ample_analysis["q3b"],
        "Q4": ample_analysis["q4"], "Q5": ample_analysis["q5"],
    }
    assert set(ample_analysis["answers"]) == set(groups)
    assert ample_analysis["publication_blockers"] == []
    for name, tests in groups.items():
        summary = ample_analysis["answers"][name]
        assert summary["question"] and summary["status"] == "supported_findings"
        published = {row["test_id"] for row in summary["conclusions"]}
        assert published
        assert published == {row["test_id"] for row in tests if row["conclusion_allowed"]}
        assert all(row["p_adjusted"] < 0.05 and row["significant"] for row in tests if row["test_id"] in published)


def test_q2_tests_aspect_minus_jointly_estimated_overall_baseline(ample_analysis):
    battery = next(row for row in ample_analysis["q2"] if row["aspect"] == "BATTERY")
    camera = next(row for row in ample_analysis["q2"] if row["aspect"] == "CAMERA")
    assert battery["estimate"] < 0 < camera["estimate"]
    assert battery["significant"] and camera["significant"]
    assert battery["conclusion"] == "Ưu điểm tương đối"
    assert camera["conclusion"] == "Nhược điểm tương đối"


def test_q3_uses_omnibus_gate_and_does_not_drop_ties_from_reporting(ample_analysis):
    direct = next(row for row in ample_analysis["q3b"] if row["aspect"] == "BATTERY")
    assert direct["n_decisive"] == 6000 and direct["n_tie"] == 600
    assert direct["win_pct"] == pytest.approx(100 * direct["n_x_win"] / 6000)
    assert direct["significant"] and direct["conclusion"] == "X thắng nhiều hơn"
    assert all(not row["significant"] or row["passes_omnibus_gate"] for row in ample_analysis["q3a"]["pairwise"])


def test_q4_only_calls_improvement_when_adjusted_test_supports_it(ample_analysis):
    battery = next(row for row in ample_analysis["q4"] if row["aspect"] == "BATTERY")
    assert battery["estimate"] > 0 and battery["p_adjusted"] < 0.05
    assert battery["conclusion"] == "Đã cải thiện"
    assert all(row["conclusion"] != "Đã cải thiện" or row["significant"] for row in ample_analysis["q4"])


def test_q5_trend_and_priorities_cover_significant_decreases(ample_analysis):
    battery = next(row for row in ample_analysis["q5"] if row["defect_type"] == "BATTERY_DRAIN")
    heat = next(row for row in ample_analysis["q5"] if row["defect_type"] == "OVERHEAT")
    absent = next(row for row in ample_analysis["q5"] if row["defect_type"] == "LAG")
    assert battery["priority"] == "P1" and battery["trend"] == "significant_increase"
    assert heat["priority"] == "P2" and heat["trend"] == "significant_decrease"
    assert absent["priority"] == "P3" and absent["p_value"] is None
    assert all(week["n_denominator"] == 13200 for week in battery["weekly"])


def test_baseline_and_fixture_labels_cannot_be_promoted_to_business_conclusions(plentiful_counts):
    aggregates, config = deepcopy(plentiful_counts)
    aggregates.report["counts_by_label_source"] = {"rule": 100}
    result = analyze_questions(aggregates, config, validation_report={"data_kind": "fixture", "label_accuracy_verified": True})
    assert result["significant_tests"] > 0
    assert not result["can_publish_business_conclusions"] and not result["label_handoff_verified"]
    assert all(row["priority"] is None for row in result["q5"])
    assert all(not row["conclusion_allowed"] for row in result["q4"])
    assert "rule_baseline_labels" in result["publication_blockers"]
    assert "synthetic_or_unconfirmed_dataset" in result["publication_blockers"]
    assert all(not row["conclusions"] for row in result["answers"].values())
    assert result["answers"]["Q2"]["status"] == "label_evaluation_required"


def test_q5_does_not_assign_p2_when_the_second_half_is_missing(plentiful_counts):
    aggregates, config = deepcopy(plentiful_counts)
    for name in ("aggregates", "q5_denominators", "q5_defects"):
        aggregates.tables[name] = [row for row in aggregates.tables[name] if row["week_since_launch"] <= 2]
    result = analyze_questions(aggregates, config, validation_report={"data_kind": "provided", "label_accuracy_verified": True})
    battery = next(row for row in result["q5"] if row["defect_type"] == "BATTERY_DRAIN")
    assert battery["n_defect"] >= 20 and battery["late_pct"] is None
    assert battery["priority"] is None and battery["trend"] == "not_testable"


def test_sample_candidates_are_balanced_and_always_require_human_review(plentiful_counts):
    aggregates, config = plentiful_counts
    samples = [{"mention_id": f"sample{i}#0#BATTERY", "comment_id": f"sample{i}", "clause_idx": 0,
                "clause_text": f"sample {i}", "target_model": config.target_model, "aspect": "BATTERY",
                "sentiment": "neg" if i == 3 else "pos", "label_source": "rule", "confidence": 0.9}
               for i in range(4)]
    result = analyze_questions(aggregates, config, validation_report={"data_kind": "fixture"}, mentions=samples)
    quotes = next(row for row in result["q2"] if row["aspect"] == "BATTERY")["sample_candidates"]
    assert len(quotes) == 3 and {row["sentiment"] for row in quotes} == {"pos", "neg"}
    assert all(row["requires_human_review"] for row in quotes)


def test_cli_exports_questions_and_fingerprints_new_output(tmp_path):
    output = tmp_path / "analysis"
    completed = subprocess.run([sys.executable, "-m", "src.analysis.build_aggregates", "--demo", "--output", str(output)],
                               cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert completed.returncode == 0, completed.stderr
    result = json.loads((output / "business_questions.json").read_text(encoding="utf-8"))
    assert result["status"] == "completed" and result["data_kind"] == "fixture"
    assert result["estimable_tests"] == 0
    assert not result["can_publish_business_conclusions"]
    assert all(row["status"] == "insufficient_data" and not row["conclusions"] for row in result["answers"].values())
    assert "label_accuracy_not_verified" in result["publication_blockers"]
    assert all(row["unavailable_test_reasons"] for row in result["answers"].values())
    manifest = json.loads((output / "aggregation_manifest.json").read_text(encoding="utf-8"))
    assert "business_questions.json" in manifest["output_sha256"]
    assert "questions.py" in manifest["code_sha256"]
    assert not (tmp_path / "validation").exists()
    json.dumps(result, allow_nan=False)


def test_cli_rejects_insufficient_bootstrap_repetitions(tmp_path):
    completed = subprocess.run([sys.executable, "-m", "src.analysis.build_aggregates", "--demo", "--bootstrap-resamples", "20", "--output", str(tmp_path / "blocked")],
                               cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert completed.returncode == 2 and "resamples" in json.loads(completed.stderr)["message"]
    assert not (tmp_path / "blocked").exists()

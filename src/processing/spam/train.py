"""Huấn luyện và đánh giá: rule-v0 so với mô hình ML và phương án kết hợp.

Quy trình (không để tập test ảnh hưởng tới bất kỳ lựa chọn nào):
  1. Trên tập train: cross-validation 5 phần, gom nhóm theo video_id, lấy điểm
     out-of-fold của từng mô hình ứng viên. Chọn mô hình theo average precision
     có trọng số; chọn ngưỡng theo F0,5 có trọng số (ưu tiên precision).
  2. Huấn luyện lại mô hình đã chọn trên toàn bộ train.
  3. Chấm MỘT lần trên tập test: các biến thể rule-v0, mô hình ML, phương án kết hợp.

Chạy:  python -m src.processing.spam.train
"""
import argparse
import collections
import json
import sys
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import sklearn
from sklearn.model_selection import StratifiedGroupKFold

from . import config, data
from .baseline import CONTENT_REASONS, FORM_REASONS, RULE_VARIANTS, flags, rule_reasons
from .evaluate import (average_precision, bootstrap_ci, cluster_resamples, cohen_kappa, f_beta,
                       hidden_positive_bound, mcnemar_exact, prf, recall_lower_bound, stratum_weights)
from .language import detect_language
from .model import SEED, build_candidates, scores
from .sampling import normalize_for_dup, stratum_of

GATE_REASONS = CONTENT_REASONS | FORM_REASONS
ML_NAME = "ML"
HYBRID_NAME = "Kết hợp (luật nội dung + hình thức, ML xác nhận)"
BASELINE_NAME = "rule-v0 (nguyên trạng)"


def load_rows() -> List[dict]:
    rows = data.attach_text(data.read_tsv(config.LABELS_PATH))
    for row in rows:
        row["y"] = 1 if row["label"] == "spam" else 0
        # Bộ luật chạy lại trên nội dung phải cho đúng kết quả đã lưu trong dữ liệu.
        if sorted(rule_reasons(row["text"])) != sorted(row["rule_reasons"]):
            raise ValueError(f"rule-v0 cho kết quả khác dữ liệu chuẩn ở {row['item_id']}")
    return rows


def population(strata_info: Dict[str, Dict[str, int]], key: str) -> Dict[str, int]:
    return {name: info[key] for name, info in strata_info.items()}


def best_threshold(y: np.ndarray, score: np.ndarray, weights: np.ndarray,
                   gate: Optional[np.ndarray] = None) -> Tuple[float, float]:
    """Ngưỡng cho F0,5 có trọng số cao nhất; hòa thì lấy ngưỡng cao hơn (thận trọng hơn).

    Với `gate`, một bình luận chỉ bị gắn cờ khi vừa qua cổng luật vừa đạt ngưỡng;
    ngưỡng -inf (giữ nguyên quyết định của luật) cũng là một lựa chọn.
    """
    candidates = [-np.inf] + sorted(set(score.tolist())) if gate is not None else sorted(set(score.tolist()))
    best = (-1.0, -np.inf)
    for threshold in candidates:
        predicted = score >= threshold
        if gate is not None:
            predicted = predicted & gate
        result = prf(y, predicted, weights)
        value = f_beta(result["precision"], result["recall"], beta=0.5)
        if value >= best[0]:
            best = (value, float(threshold))
    return best[1], best[0]


def describe(y: np.ndarray, predicted: np.ndarray, strata: List[str], pop: Dict[str, int],
             videos: np.ndarray, n_boot: int) -> Dict[str, object]:
    weights = stratum_weights(strata, pop)
    return {
        "sample": prf(y, predicted),
        "population": prf(y, predicted, weights),
        "population_ci95": bootstrap_ci(y, predicted, strata, pop, clusters=videos,
                                        n_boot=n_boot, seed=SEED),
        # Recall nếu các tầng không thấy spam nào vẫn có spam ở mức cận trên 95%.
        "recall_lower_bound": recall_lower_bound(y, predicted, strata, pop),
    }


def weighted_rate(values: np.ndarray, strata: List[str], pop: Dict[str, int],
                  videos: Optional[np.ndarray], n_boot: int) -> Dict[str, object]:
    """Tỷ lệ trong quần thể ước lượng từ mẫu phân tầng, kèm khoảng tin cậy bootstrap theo video."""
    weights = stratum_weights(strata, pop)
    estimate = float(np.sum(weights * values) / np.sum(weights))
    draws = [np.sum(w * values[index]) / np.sum(w)
             for index, w in cluster_resamples(strata, pop, videos, n_boot, SEED)]
    return {"estimate": estimate,
            "ci95": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
            "estimated_count": estimate * float(sum(pop.values()))}


def apply_to_dataset(pipeline, threshold_ml: float, threshold_hybrid: float) -> Dict[str, object]:
    """Đếm số bình luận từng phương án gắn cờ trên TOÀN BỘ dữ liệu, theo tầng.

    Không có nhãn cho toàn bộ dữ liệu nên đây không phải phép đo độ chính xác; nó cho
    biết mô hình ML có gắn cờ tràn lan ở vùng luật không bắt hay không.
    """
    comments = list(data.iter_comments())
    dup_counts = collections.Counter(normalize_for_dup(c["text"]) for c in comments)
    by_stratum = {name: {"N": 0, "rule_v0": 0, "ml": 0, "hybrid": 0} for name in config.STRATA_SIZES}
    languages, rule_not_vietnamese = collections.Counter(), 0
    for start in range(0, len(comments), 5000):
        chunk = comments[start:start + 5000]
        chunk_scores = scores(pipeline, [c["text"] for c in chunk])
        for comment, score in zip(chunk, chunk_scores):
            cell = by_stratum[stratum_of(comment, dup_counts)]
            gate = flags(comment["spam_reasons"], GATE_REASONS)
            cell["N"] += 1
            cell["rule_v0"] += bool(comment["spam_reasons"])
            cell["ml"] += bool(score >= threshold_ml)
            cell["hybrid"] += bool(gate and score >= threshold_hybrid)
            languages[detect_language(comment["text"])] += 1
            rule_not_vietnamese += not comment["is_vietnamese"]
    totals = {key: sum(cell[key] for cell in by_stratum.values()) for key in ("N", "rule_v0", "ml", "hybrid")}
    return {"by_stratum": by_stratum, "total": totals, "language_py": dict(languages),
            "rule_v0_not_vietnamese": rule_not_vietnamese}


def run(n_boot: int = 2000, save_model: bool = True, full_data: bool = True) -> Dict[str, object]:
    data.check_dataset_version()
    strata_info = json.loads((config.LABELS_DIR / "spam_strata_v1.json").read_text("utf-8"))["strata"]
    rows = load_rows()
    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] == "test"]
    assert not {r["video_id"] for r in train} & {r["video_id"] for r in test}, "video nằm ở cả hai tập"

    def arrays(part: List[dict]):
        return ([r["text"] for r in part], np.asarray([r["y"] for r in part]),
                [r["stratum"] for r in part], np.asarray([r["video_id"] for r in part]))

    x_train, y_train, strata_train, groups_train = arrays(train)
    x_test, y_test, strata_test, videos_test = arrays(test)
    pop_train, pop_test = population(strata_info, "N_train"), population(strata_info, "N_test")
    w_train = stratum_weights(strata_train, pop_train)
    gate_train = np.asarray([flags(r["rule_reasons"], GATE_REASONS) for r in train])
    gate_test = np.asarray([flags(r["rule_reasons"], GATE_REASONS) for r in test])

    # --- 1. Chọn mô hình và ngưỡng bằng cross-validation trên train ---
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
                 .split(x_train, y_train, groups_train))
    cv_results, oof_scores = {}, {}
    for name, pipeline in build_candidates().items():
        oof = np.zeros(len(x_train))
        for fit_index, held_index in folds:
            pipeline.fit([x_train[i] for i in fit_index], y_train[fit_index])
            oof[held_index] = scores(pipeline, [x_train[i] for i in held_index])
        threshold, f05 = best_threshold(y_train, oof, w_train)
        at_threshold = prf(y_train, oof >= threshold, w_train)
        cv_results[name] = {
            "average_precision_population": average_precision(y_train, oof, w_train),
            "average_precision_sample": average_precision(y_train, oof),
            "threshold": threshold, "f05_population": f05,
            "precision_population": at_threshold["precision"],
            "recall_population": at_threshold["recall"],
        }
        oof_scores[name] = oof
    selected = max(cv_results, key=lambda n: cv_results[n]["average_precision_population"])
    threshold_ml = cv_results[selected]["threshold"]
    threshold_hybrid, hybrid_f05 = best_threshold(y_train, oof_scores[selected], w_train, gate_train)
    rule_gate_oof = prf(y_train, gate_train, w_train)

    # --- 2. Huấn luyện lại trên toàn bộ train ---
    final = build_candidates()[selected]
    final.fit(x_train, y_train)
    test_scores = scores(final, x_test)

    # --- 3. Chấm một lần trên test ---
    predictions: Dict[str, np.ndarray] = {
        name: np.asarray([flags(r["rule_reasons"], active) for r in test])
        for name, active in RULE_VARIANTS.items()
    }
    predictions[ML_NAME] = test_scores >= threshold_ml
    predictions[HYBRID_NAME] = gate_test & (test_scores >= threshold_hybrid)
    test_results = {name: describe(y_test, pred, strata_test, pop_test, videos_test, n_boot)
                    for name, pred in predictions.items()}

    # Phương án kết hợp chỉ có thể bỏ bớt cờ của luật: nó giữ lại bao nhiêu spam mà luật bắt đúng?
    gate_hits = gate_test & (y_test == 1)
    kept_by_hybrid = {"rule_true_positives": int(gate_hits.sum()),
                      "kept_by_hybrid": int((gate_hits & predictions[HYBRID_NAME]).sum())}

    # Bình luận dán lặp có thể nằm ở cả train và test dù chia theo video: đo lại khi bỏ chúng ra.
    train_texts = {normalize_for_dup(text) for text in x_train}
    fresh = np.asarray([normalize_for_dup(text) not in train_texts for text in x_test])
    strata_fresh = [s for s, keep in zip(strata_test, fresh) if keep]
    duplicate_check = {
        "n_test_rows_also_in_train": int((~fresh).sum()),
        "n_test_spam_also_in_train": int(((~fresh) & (y_test == 1)).sum()),
        "without_them": {name: prf(y_test[fresh], predictions[name][fresh],
                                   stratum_weights(strata_fresh, pop_test))
                         for name in (BASELINE_NAME, ML_NAME, HYBRID_NAME)},
    }
    comparisons = {
        f"{name} so với {BASELINE_NAME}": mcnemar_exact(y_test, predictions[name],
                                                        predictions[BASELINE_NAME])
        for name in (ML_NAME, HYBRID_NAME, "rule-v0 chỉ nội dung + hình thức")
    }
    comparisons[f"{HYBRID_NAME} so với {ML_NAME}"] = mcnemar_exact(
        y_test, predictions[HYBRID_NAME], predictions[ML_NAME])

    def reason_group(reasons: List[str]) -> str:
        """Nhóm một dòng bị rule-v0 gắn cờ theo lý do mạnh nhất, để phân tích báo nhầm."""
        present = set(reasons)
        for group, members in (
            ("link_or_phone", {"contains_url", "contains_phone_number"}),
            ("contact_word", {"external_contact_invite"}),
            ("commerce_word", {"commercial_or_gambling_spam"}),
            ("no_text", {"no_alphabetical_content", "empty_text"}),
            ("form", FORM_REASONS),
        ):
            if present & members:
                return group
        return "language_only"

    baseline_pred = predictions[BASELINE_NAME]
    rule_fp_groups = dict(collections.Counter(
        reason_group(r["rule_reasons"]) for r, p in zip(test, baseline_pred) if p and not r["y"]))
    rule_tp_groups = dict(collections.Counter(
        reason_group(r["rule_reasons"]) for r, p in zip(test, baseline_pred) if p and r["y"]))

    errors = {}
    for name in (BASELINE_NAME, "rule-v0 chỉ nội dung + hình thức", ML_NAME, HYBRID_NAME):
        pred = predictions[name]
        errors[name] = {
            "false_positive": [r["item_id"] for r, p in zip(test, pred) if p and not r["y"]],
            "false_negative": [r["item_id"] for r, p in zip(test, pred) if not p and r["y"]],
        }

    # --- Ngôn ngữ: chỉ chấm trên test, bỏ các dòng lang = none (không có đáp án đúng) ---
    language_rows = [r for r in test if r["lang"] != "none"]
    lang_truth = np.asarray([r["lang"] == "other" for r in language_rows])
    language = {
        "n_rows": len(language_rows), "n_other": int(lang_truth.sum()),
        "note": "Lớp dương = ngôn ngữ khác (lang = other). Đếm trên mẫu, không trọng số.",
        "rule-v0 (is_vietnamese = false)": prf(
            lang_truth, [not r["rule_is_vietnamese"] for r in language_rows]),
        "language.py (lang = other)": prf(
            lang_truth, [detect_language(r["text"]) == "other" for r in language_rows]),
        "language.py: tiếng Việt bị xếp nhầm khác 'vi'": {
            "n_vi": int((~lang_truth).sum()),
            "n_missed": int(sum(detect_language(r["text"]) != "vi"
                                for r in language_rows if r["lang"] == "vi")),
        },
        "rule-v0: tiếng Việt bị coi là không phải tiếng Việt": {
            "n_vi": int((~lang_truth).sum()),
            "n_missed": int(sum(not r["rule_is_vietnamese"]
                                for r in language_rows if r["lang"] == "vi")),
        },
    }

    all_strata = [r["stratum"] for r in rows]
    pop_all = population(strata_info, "N")
    y_all = np.asarray([r["y"] for r in rows], dtype=float)
    videos_all = np.asarray([r["video_id"] for r in rows])
    label_sources = collections.Counter(r["label_source"] for r in rows)
    test_sources = collections.Counter(r["label_source"] for r in test)
    sample_table = collections.defaultdict(lambda: {"n": 0, "n_spam": 0})
    for row in rows:
        cell = sample_table[f"{row['stratum']}/{row['split']}"]
        cell["n"] += 1
        cell["n_spam"] += row["y"]

    model_info = None
    if save_model:
        config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": final, "model_version": config.MODEL_VERSION, "selected": selected,
                     "threshold_ml": threshold_ml, "threshold_hybrid": threshold_hybrid}, config.MODEL_PATH)
        model_info = {"path": str(config.MODEL_PATH.relative_to(config.REPO_ROOT)).replace("\\", "/"),
                      "sha256": data.file_sha256(config.MODEL_PATH)}

    # File làm việc cục bộ cho phân tích lỗi (có nội dung nên không vào git).
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    data.write_tsv(config.WORK_DIR / "test_predictions.tsv", [
        {"item_id": r["item_id"], "stratum": r["stratum"], "label": r["label"],
         "spam_type": r["spam_type"], "score": f"{s:.4f}",
         "rule": int(predictions[BASELINE_NAME][i]), "ml": int(predictions[ML_NAME][i]),
         "hybrid": int(predictions[HYBRID_NAME][i]), "rule_reasons": ",".join(r["rule_reasons"]),
         "text": r["text"].replace("\n", " ⏎ ").replace("\t", " ")[:400]}
        for i, (r, s) in enumerate(zip(test, test_scores))
    ], ["item_id", "stratum", "label", "spam_type", "score", "rule", "ml", "hybrid", "rule_reasons", "text"])

    return {
        "meta": {
            "dataset": config.DATASET_VERSION, "dataset_sha256": config.DATASET_SHA256,
            "guideline_version": rows[0]["guideline_version"], "rule_version": config.RULE_VERSION,
            "model_version": config.MODEL_VERSION, "seed": SEED, "bootstrap_resamples": n_boot,
            "scikit_learn": sklearn.__version__, "numpy": np.__version__,
            "n_labels": len(rows), "n_train": len(train), "n_test": len(test),
            "n_videos_train": len({r["video_id"] for r in train}),
            "n_videos_test": len({r["video_id"] for r in test}),
            "label_sources": dict(label_sources), "test_label_sources": dict(test_sources),
            "test_human_verified": set(test_sources) == {"human"},
        },
        "agreement": {
            "annotators": rows[0]["annotators"],
            "label_agreement": float(np.mean([r["label_a"] == r["label_b"] for r in rows])),
            "label_kappa": cohen_kappa([r["label_a"] for r in rows], [r["label_b"] for r in rows]),
            "lang_agreement": float(np.mean([r["lang_a"] == r["lang_b"] for r in rows])),
            "lang_kappa": cohen_kappa([r["lang_a"] for r in rows], [r["lang_b"] for r in rows]),
            "resolution": dict(collections.Counter(r["resolution"] for r in rows)),
        },
        "sample": dict(sorted(sample_table.items())),
        "spam_types": dict(collections.Counter(r["spam_type"] for r in rows if r["y"])),
        "prevalence": {
            "spam": weighted_rate(y_all, all_strata, pop_all, videos_all, n_boot),
            # Số spam tối đa có thể còn ẩn trong các tầng mà mẫu không thấy spam nào.
            "hidden_spam_upper_bound": hidden_positive_bound(y_all, all_strata, pop_all),
            "flag_rate": {
                name: weighted_rate(
                    np.asarray([flags(r["rule_reasons"], active) for r in rows], dtype=float),
                    all_strata, pop_all, None, 1)["estimate"]
                for name, active in RULE_VARIANTS.items()
            },
        },
        "cross_validation": {
            "candidates": cv_results, "selected": selected,
            "threshold_ml": threshold_ml, "threshold_hybrid": threshold_hybrid,
            "hybrid_f05_population": hybrid_f05,
            "rule_gate_population": rule_gate_oof,
        },
        "test": test_results,
        "test_population": {"n_comments": int(sum(pop_test.values())),
                            "hidden_spam_upper_bound": hidden_positive_bound(y_test, strata_test, pop_test)},
        "hybrid_keeps": kept_by_hybrid,
        "duplicate_text_check": duplicate_check,
        "mcnemar": comparisons,
        "errors": errors,
        "rule_v0_flags_by_reason_group": {"false_positive": rule_fp_groups, "true_positive": rule_tp_groups},
        "language": language,
        "full_dataset": apply_to_dataset(final, threshold_ml, threshold_hybrid) if full_data else None,
        "model_file": model_info,
    }


def _clean(value):
    """JSON không có Infinity: ngưỡng -inf (giữ nguyên luật) ghi thành null."""
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bootstrap", type=int, default=2000, help="số lần bootstrap cho khoảng tin cậy")
    args = parser.parse_args()

    results = _clean(run(n_boot=args.bootstrap))
    config.RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.RESULTS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", "utf-8")

    print(f"Đã ghi {config.RESULTS_PATH}")
    if not results["meta"]["test_human_verified"]:
        print("LƯU Ý: tập test còn nhãn chưa có người duyệt; kết quả là TẠM THỜI.")
    print(f"Mô hình chọn: {results['cross_validation']['selected']}")
    for name, result in results["test"].items():
        pop = result["population"]
        fmt = lambda v: "  n/a" if v is None else f"{v:.3f}"
        print(f"  {name:52s} P={fmt(pop['precision'])} R={fmt(pop['recall'])} F1={fmt(pop['f1'])}")


if __name__ == "__main__":
    main()

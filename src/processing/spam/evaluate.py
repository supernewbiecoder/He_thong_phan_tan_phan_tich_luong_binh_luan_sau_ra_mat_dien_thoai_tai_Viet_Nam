"""Chỉ số đánh giá cho bài toán spam (lớp dương = spam).

Mẫu gán nhãn được làm giàu spam nên precision/recall tính thẳng trên mẫu không
phản ánh dữ liệu thật. Mỗi dòng mang trọng số N_h/n_h của tầng nó thuộc về; các
chỉ số "quy về quần thể" là chỉ số tính với trọng số đó. Không dùng accuracy.
"""
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy.stats import binomtest


def confusion(y_true: Sequence[int], y_pred: Sequence[int],
              weights: Optional[Sequence[float]] = None) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)
    w = np.ones(len(y_true)) if weights is None else np.asarray(weights, dtype=float)
    return {
        "tp": float(w[y_true & y_pred].sum()),
        "fp": float(w[~y_true & y_pred].sum()),
        "fn": float(w[y_true & ~y_pred].sum()),
        "tn": float(w[~y_true & ~y_pred].sum()),
    }


def prf(y_true: Sequence[int], y_pred: Sequence[int],
        weights: Optional[Sequence[float]] = None) -> Dict[str, Optional[float]]:
    """Precision, recall, F1 của lớp spam. Mẫu số bằng 0 thì trả None, không trả 0."""
    cell = confusion(y_true, y_pred, weights)
    predicted, actual = cell["tp"] + cell["fp"], cell["tp"] + cell["fn"]
    precision = cell["tp"] / predicted if predicted else None
    recall = cell["tp"] / actual if actual else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None if precision is None or recall is None else 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {**cell, "precision": precision, "recall": recall, "f1": f1}


def f_beta(precision: Optional[float], recall: Optional[float], beta: float) -> float:
    if not precision or not recall:
        return 0.0
    return (1 + beta ** 2) * precision * recall / (beta ** 2 * precision + recall)


def stratum_weights(strata: Sequence[str], population: Dict[str, int]) -> np.ndarray:
    """Trọng số N_h/n_h, với n_h là số dòng của tầng h có mặt trong `strata`."""
    strata = list(strata)
    counts = {name: strata.count(name) for name in set(strata)}
    return np.asarray([population[name] / counts[name] for name in strata], dtype=float)


def bootstrap_ci(y_true: Sequence[int], y_pred: Sequence[int], strata: Sequence[str],
                 population: Dict[str, int], n_boot: int = 2000, seed: int = 42,
                 level: float = 0.95) -> Dict[str, Optional[List[float]]]:
    """Khoảng tin cậy phân vị cho precision/recall/F1 có trọng số.

    Bootstrap phân tầng: rút có hoàn lại trong từng tầng, giữ nguyên cỡ mẫu tầng,
    vì mẫu gốc cũng được rút như vậy.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    strata = np.asarray(strata)
    index_by_stratum = {name: np.flatnonzero(strata == name) for name in np.unique(strata)}
    weights = stratum_weights(strata, population)
    rng = np.random.default_rng(seed)
    draws: Dict[str, List[float]] = {"precision": [], "recall": [], "f1": []}
    for _ in range(n_boot):
        index = np.concatenate([rng.choice(idx, size=len(idx), replace=True)
                                for idx in index_by_stratum.values()])
        result = prf(y_true[index], y_pred[index], weights[index])
        for key in draws:
            if result[key] is not None:
                draws[key].append(result[key])
    lower, upper = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    intervals: Dict[str, Optional[List[float]]] = {}
    for key, values in draws.items():
        # Nếu quá nhiều lần rút không tính được chỉ số thì không báo cáo khoảng.
        if len(values) < 0.9 * n_boot:
            intervals[key] = None
        else:
            intervals[key] = [float(np.percentile(values, lower)), float(np.percentile(values, upper))]
    return intervals


def mcnemar_exact(y_true: Sequence[int], pred_a: Sequence[int],
                  pred_b: Sequence[int]) -> Dict[str, float]:
    """Kiểm định McNemar chính xác: hai phương pháp có tỷ lệ đúng khác nhau không.

    Chỉ các dòng mà hai phương pháp cho kết quả đúng/sai khác nhau mới mang thông tin.
    Tính trên mẫu (không trọng số) nên trả lời câu hỏi "trên các bình luận đã gán nhãn".
    """
    y_true = np.asarray(y_true)
    correct_a = np.asarray(pred_a) == y_true
    correct_b = np.asarray(pred_b) == y_true
    only_a = int(np.sum(correct_a & ~correct_b))
    only_b = int(np.sum(~correct_a & correct_b))
    discordant = only_a + only_b
    p_value = 1.0 if discordant == 0 else float(binomtest(only_a, discordant, 0.5).pvalue)
    return {"only_a_correct": only_a, "only_b_correct": only_b, "p_value": p_value}


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> Optional[float]:
    """Cohen's kappa cho hai người gán. Trả None nếu cả hai chỉ dùng đúng một nhãn."""
    labels_a, labels_b = list(labels_a), list(labels_b)
    if len(labels_a) != len(labels_b) or not labels_a:
        raise ValueError("Hai danh sách nhãn phải cùng độ dài và không rỗng")
    total = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / total
    expected = sum((labels_a.count(c) / total) * (labels_b.count(c) / total)
                   for c in set(labels_a) | set(labels_b))
    if expected == 1.0:
        return None
    return (observed - expected) / (1 - expected)


def average_precision(y_true: Sequence[int], score: Sequence[float],
                      weights: Optional[Sequence[float]] = None) -> Optional[float]:
    """Average precision có trọng số (diện tích dưới đường precision–recall)."""
    y_true = np.asarray(y_true, dtype=float)
    score = np.asarray(score, dtype=float)
    w = np.ones(len(y_true)) if weights is None else np.asarray(weights, dtype=float)
    positive_weight = float((w * y_true).sum())
    if positive_weight == 0:
        return None
    order = np.argsort(-score, kind="mergesort")
    y_sorted, w_sorted, s_sorted = y_true[order], w[order], score[order]
    cum_tp = np.cumsum(w_sorted * y_sorted)
    cum_all = np.cumsum(w_sorted)
    # Các dòng cùng điểm phải được tính chung một ngưỡng.
    last_of_tie = np.r_[s_sorted[1:] != s_sorted[:-1], True]
    precision = cum_tp[last_of_tie] / cum_all[last_of_tie]
    recall = cum_tp[last_of_tie] / positive_weight
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))

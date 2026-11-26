"""Mục đích: Chỉ số đo một bộ phân loại nhị phân (spam, tiếng Việt…) trên mẫu phân tầng có trọng số N_h/n_h: precision, recall, F1, khoảng tin cậy bootstrap phân tầng theo video, cận recall khi tầng không thấy ca dương, McNemar, kappa; dùng cho src/labeling/estimate.py và src/models/spam/ (docs/3-gan-nhan/dac-ta.md mục 3); cập nhật lần cuối: 2026-11-26.

Chuyển từ src/processing/spam/evaluate.py (Công việc 11, 17/11), không đổi công thức.
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


def cluster_resamples(strata: Sequence[str], population: Dict[str, int],
                      clusters: Optional[Sequence[str]], n_boot: int, seed: int):
    """Sinh `n_boot` mẫu bootstrap phân tầng theo cụm: mỗi lần trả (chỉ số dòng, trọng số)."""
    strata = np.asarray(strata)
    clusters = np.arange(len(strata)).astype(str) if clusters is None else np.asarray(clusters)
    rows_by_cluster: Dict[str, List[np.ndarray]] = {}
    for name in np.unique(strata):
        in_stratum = np.flatnonzero(strata == name)
        rows_by_cluster[name] = [in_stratum[clusters[in_stratum] == cluster]
                                 for cluster in np.unique(clusters[in_stratum])]
    rng = np.random.default_rng(seed)
    for _ in range(n_boot):
        index, weights = [], []
        for name, groups in rows_by_cluster.items():
            picked = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
            index.append(picked)
            weights.append(np.full(len(picked), population[name] / len(picked)))
        yield np.concatenate(index), np.concatenate(weights)


def bootstrap_ci(y_true: Sequence[int], y_pred: Sequence[int], strata: Sequence[str],
                 population: Dict[str, int], clusters: Optional[Sequence[str]] = None,
                 n_boot: int = 2000, seed: int = 42,
                 level: float = 0.95) -> Dict[str, Optional[List[float]]]:
    """Khoảng tin cậy phân vị cho precision/recall/F1 có trọng số.

    Bootstrap phân tầng theo cụm: trong từng tầng, rút có hoàn lại các CỤM (video) rồi
    lấy mọi dòng của cụm được rút. Các bình luận cùng một video không độc lập (vd hàng
    chục bài dự thi minigame của một video), rút từng dòng sẽ cho khoảng quá hẹp. Trọng
    số tính lại ở mỗi lần rút vì số dòng của tầng thay đổi. Không truyền `clusters` thì
    mỗi dòng là một cụm.

    Giới hạn: tầng không quan sát được spam nào thì lần rút nào cũng không có spam, nên
    khoảng này KHÔNG phản ánh khả năng tầng đó vẫn có spam. Xem `hidden_positive_bound`.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    draws: Dict[str, List[float]] = {"precision": [], "recall": [], "f1": []}
    for index, weights in cluster_resamples(strata, population, clusters, n_boot, seed):
        result = prf(y_true[index], y_pred[index], weights)
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


def zero_count_upper_rate(n: int, level: float = 0.95) -> float:
    """Cận trên một phía (mức `level`) của tỷ lệ khi quan sát 0 ca trong n mẫu.

    Công thức chính xác của phân phối nhị thức: 1 - (1 - level)^(1/n). Với level = 0,95
    nó xấp xỉ "quy tắc số 3" (3/n).
    """
    return 1.0 - (1.0 - level) ** (1.0 / n) if n > 0 else 1.0


def hidden_positive_bound(y_true: Sequence[int], strata: Sequence[str],
                          population: Dict[str, int]) -> Dict[str, float]:
    """Số spam tối đa có thể còn ẩn trong các tầng mà mẫu không thấy spam nào.

    Mẫu có 0 spam trong một tầng không chứng minh tầng đó không có spam. Với mỗi tầng
    như vậy, lấy cận trên 95% của tỷ lệ spam nhân với cỡ quần thể của tầng.
    """
    y_true = np.asarray(y_true, dtype=int)
    strata = np.asarray(strata)
    hidden = {}
    for name in np.unique(strata):
        rows = strata == name
        if y_true[rows].sum() == 0:
            hidden[str(name)] = population[name] * zero_count_upper_rate(int(rows.sum()))
    return hidden


def recall_lower_bound(y_true: Sequence[int], y_pred: Sequence[int], strata: Sequence[str],
                       population: Dict[str, int]) -> Optional[float]:
    """Recall trong tình huống xấu: mọi tầng không thấy spam đều có spam ở mức cận trên.

    Spam ẩn trong một tầng chỉ được tính là bắt được khi phương pháp gắn cờ TOÀN BỘ dòng
    mẫu của tầng đó; còn lại coi như bị sót.
    """
    y_true, y_pred, strata = np.asarray(y_true, dtype=int), np.asarray(y_pred, dtype=int), np.asarray(strata)
    base = prf(y_true, y_pred, stratum_weights(strata, population))
    caught = missed = 0.0
    for name, amount in hidden_positive_bound(y_true, strata, population).items():
        if y_pred[strata == name].all():
            caught += amount
        else:
            missed += amount
    total = base["tp"] + base["fn"] + caught + missed
    return (base["tp"] + caught) / total if total else None


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

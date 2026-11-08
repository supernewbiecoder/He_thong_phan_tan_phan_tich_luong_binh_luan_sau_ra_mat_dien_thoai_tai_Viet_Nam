# -*- coding: utf-8 -*-
"""
Công việc 9 - mô hình cảm xúc theo khía cạnh: BASELINE TF-IDF + Logistic Regression.

Đầu vào : data/task9/sentiment_train.jsonl, sentiment_val.jsonl   (từ build_sentiment_dataset.py)
Đầu ra  : data/task9/model/model.joblib, metrics.json, val_errors.csv

    pip install scikit-learn joblib
    python src/processing/task9/train_baseline.py

Mô hình: văn bản "<mã khía cạnh> <mệnh đề>" -> TF-IDF (từ 1-2 gram + ký tự 2-5) -> Logistic Regression (class_weight=balanced).
Chọn C bằng cross-validation gom nhóm theo video_id trên TRAIN (không đụng val/test).
Báo cáo: macro-F1, F1 từng lớp, confusion matrix, macro-F1 theo khía cạnh, và baseline "luôn đoán lớp đa số".

LƯU Ý: train và val đều là nhãn LLM, nên điểm trên val đo độ khớp với LLM, KHÔNG phải độ đúng thật.
Điểm báo cáo cuối cùng phải đo trên tập test do người gán (ml-training.md).
"""
import argparse, csv, json, os
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
import joblib

LABELS = ["pos", "neg", "neu"]


def load(path):
    rows = [json.loads(l) for l in open(path, "rb") if l.strip()]
    X = [f"ASP_{r['aspect']} {r['clause_text']}" for r in rows]
    return rows, X, [r["sentiment"] for r in rows], [r["video_id"] for r in rows]


def make_pipeline(C):
    feats = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True, lowercase=True)),
    ])
    clf = LogisticRegression(C=C, class_weight="balanced", max_iter=2000)
    return Pipeline([("tfidf", feats), ("clf", clf)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/task9/sentiment_train.jsonl")
    ap.add_argument("--val", default="data/task9/sentiment_val.jsonl")
    ap.add_argument("--outdir", default="data/task9/model")
    ap.add_argument("--cs", default="0.3,1,3,10", help="các giá trị C thử bằng cross-validation")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--learning-curve", action="store_true",
                    help="huấn luyện trên 25/50/75/100%% số video của train để xem thêm dữ liệu có còn giúp không")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    tr_rows, Xtr, ytr, gtr = load(args.train)
    va_rows, Xva, yva, gva = load(args.val)
    assert not (set(gtr) & set(gva)), "rò rỉ: có video nằm ở cả train và val"
    print(f"train {len(Xtr)} cặp ({len(set(gtr))} video) | val {len(Xva)} cặp ({len(set(gva))} video)")
    print("phân bố train:", dict(Counter(ytr)), "| val:", dict(Counter(yva)))
    if len(set(ytr)) < 2 or len(Xva) == 0:
        raise SystemExit("[DỪNG] cần ít nhất 2 lớp trong train và có dữ liệu val")

    # chọn C bằng CV gom nhóm theo video_id trên train
    n_splits = min(args.folds, len(set(gtr)))
    best_c, best_f1, cv = None, -1, {}
    for C in [float(c) for c in args.cs.split(",")]:
        scores = []
        for a, b in GroupKFold(n_splits=n_splits).split(Xtr, ytr, gtr):
            m = make_pipeline(C).fit([Xtr[i] for i in a], [ytr[i] for i in a])
            p = m.predict([Xtr[i] for i in b])
            scores.append(f1_score([ytr[i] for i in b], p, average="macro", labels=LABELS, zero_division=0))
        cv[C] = float(np.mean(scores))
        print(f"  C={C}: macro-F1 CV = {cv[C]:.3f}")
        if cv[C] > best_f1:
            best_c, best_f1 = C, cv[C]
    print("chọn C =", best_c)

    model = make_pipeline(best_c).fit(Xtr, ytr)
    pred = model.predict(Xva)
    maj = Counter(ytr).most_common(1)[0][0]
    f1_model = f1_score(yva, pred, average="macro", labels=LABELS, zero_division=0)
    f1_major = f1_score(yva, [maj] * len(yva), average="macro", labels=LABELS, zero_division=0)
    print(f"\nVAL macro-F1: mô hình {f1_model:.3f} | baseline lớp đa số ('{maj}') {f1_major:.3f}")
    print(classification_report(yva, pred, labels=LABELS, zero_division=0, digits=3))
    cm = confusion_matrix(yva, pred, labels=LABELS)
    print("confusion matrix (hàng = thật, cột = đoán; thứ tự pos, neg, neu):\n", cm)

    curve = {}
    if args.learning_curve:
        import random
        vids = sorted(set(gtr)); random.Random(0).shuffle(vids)
        print("\nĐường cong học (theo số video train; val giữ nguyên):")
        for frac in (0.25, 0.5, 0.75, 1.0):
            keep = set(vids[:max(1, int(len(vids) * frac))])
            idx = [i for i, g in enumerate(gtr) if g in keep]
            if len(set(ytr[i] for i in idx)) < 2:
                continue
            m = make_pipeline(best_c).fit([Xtr[i] for i in idx], [ytr[i] for i in idx])
            f1 = f1_score(yva, m.predict(Xva), average="macro", labels=LABELS, zero_division=0)
            curve[f"{int(frac * 100)}%"] = {"pairs": len(idx), "val_macro_f1": float(f1)}
            print(f"  {int(frac * 100):3d}% video ({len(idx):5d} cặp): macro-F1 val = {f1:.3f}")

    per_aspect = {}
    for asp in sorted({r["aspect"] for r in va_rows}):
        idx = [i for i, r in enumerate(va_rows) if r["aspect"] == asp]
        per_aspect[asp] = {"n": len(idx),
                           "macro_f1": float(f1_score([yva[i] for i in idx], [pred[i] for i in idx],
                                                      average="macro", labels=LABELS, zero_division=0)),
                           "accuracy": float(np.mean([yva[i] == pred[i] for i in idx]))}
    print("theo khía cạnh:", {k: (v["n"], round(v["macro_f1"], 2)) for k, v in per_aspect.items()})

    joblib.dump({"model": model, "labels": LABELS, "C": best_c, "input_format": "ASP_<ASPECT> <clause_text>"},
                os.path.join(args.outdir, "model.joblib"))
    with open(os.path.join(args.outdir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump({"train_pairs": len(Xtr), "val_pairs": len(Xva), "train_dist": dict(Counter(ytr)),
                   "val_dist": dict(Counter(yva)), "cv_macro_f1": cv, "chosen_C": best_c,
                   "val_macro_f1": f1_model, "val_majority_baseline_macro_f1": f1_major, "learning_curve": curve,
                   "confusion_matrix_pos_neg_neu": cm.tolist(), "per_aspect": per_aspect,
                   "note": "Nhãn train/val là nhãn LLM; đây là độ khớp với LLM, không phải độ đúng thật."},
                  f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.outdir, "val_errors.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["clause_id", "aspect", "clause_text", "label_llm", "pred", "note"])
        for r, p in zip(va_rows, pred):
            if r["sentiment"] != p:
                w.writerow([r["clause_id"], r["aspect"], r["clause_text"], r["sentiment"], p, ""])
    print(f"\nĐã lưu: {args.outdir}/model.joblib, metrics.json, val_errors.csv (phân loại 20-30 lỗi để làm phân tích lỗi)")


if __name__ == "__main__":
    main()

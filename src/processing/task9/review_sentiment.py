# -*- coding: utf-8 -*-
"""
Đối chiếu nhãn trên tập val với một reviewer: nhãn LLM khớp reviewer bao nhiêu, và mô hình khớp bao nhiêu.
Theo đặc tả, reviewer cần là người để tạo nhãn gold. Nếu một LLM điền CSV, kết quả chỉ là audit giữa các mô hình,
không phải nhãn gold hay đánh giá chính thức. Khoảng 100-150 cặp phù hợp cho một lượt rà soát nhỏ.

1) Xuất mẫu từ tập val (video val KHÔNG nằm trong train nên không rò rỉ khi chấm mô hình):
    python src/processing/task9/review_sentiment.py export --n 120
   -> data/task9/review_sentiment.csv  (mở bằng Excel/Google Sheets)
   Reviewer điền:
     aspect_ok       : y nếu mệnh đề THẬT SỰ nói về khía cạnh đó, n nếu không
     human_sentiment : pos / neg / neu  (tên cột legacy; chỉ điền khi aspect_ok = y; theo guideline)
   Cột nhãn LLM bị ẩn để reviewer không bị ảnh hưởng. Để trống = chưa kiểm tra (bị bỏ qua).

2) Chấm:
    python src/processing/task9/review_sentiment.py score
    python src/processing/task9/review_sentiment.py score --model data/task9/model/model.joblib
   In: mức khớp khía cạnh/sentiment của LLM và (nếu có --model) của mô hình với reviewer trên CÙNG các cặp.
   Khi báo cáo, nêu rõ reviewer là người hay LLM; chỉ nhãn người gán mới có thể dùng làm gold.
"""
import argparse, csv, json, random
from collections import Counter

LABELS = ["pos", "neg", "neu"]


def load_pairs(path):
    return {(r["clause_id"], r["aspect"]): r for r in map(json.loads, (l for l in open(path, "rb") if l.strip()))}


def macro_f1(y, p):
    f = []
    for c in LABELS:
        tp = sum(1 for a, b in zip(y, p) if a == c and b == c)
        fp = sum(1 for a, b in zip(y, p) if a != c and b == c)
        fn = sum(1 for a, b in zip(y, p) if a == c and b != c)
        pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
        f.append(2 * pr * rc / (pr + rc) if pr + rc else 0)
    return sum(f) / len(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["export", "score"])
    ap.add_argument("--val", default="data/task9/sentiment_val.jsonl")
    ap.add_argument("--csv", default="data/task9/review_sentiment.csv")
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--model", help="đường dẫn model.joblib (tùy chọn, khi score)")
    args = ap.parse_args()

    pairs = load_pairs(args.val)
    if args.mode == "export":
        keys = sorted(pairs)
        random.Random(args.seed).shuffle(keys)
        keys = keys[:args.n]
        with open(args.csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["clause_id", "aspect", "clause_text", "aspect_ok", "human_sentiment", "note"])
            w.writeheader()
            for cid, asp in keys:
                w.writerow({"clause_id": cid, "aspect": asp, "clause_text": pairs[(cid, asp)]["clause_text"],
                            "aspect_ok": "", "human_sentiment": "", "note": ""})
        print(f"Đã xuất {len(keys)} cặp -> {args.csv}")
        print("Phân bố cảm xúc LLM trong mẫu:", dict(Counter(pairs[k]["sentiment"] for k in keys)))
        return

    rows = []
    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            ok = (r.get("aspect_ok") or "").strip().lower()
            if not ok:
                continue
            if ok not in ("y", "n"):
                raise SystemExit(f"aspect_ok phải là y hoặc n, gặp {ok!r} ở {r['clause_id']}")
            hs = (r.get("human_sentiment") or "").strip().lower()
            if ok == "y" and hs not in LABELS:
                raise SystemExit(f"human_sentiment phải là pos/neg/neu khi aspect_ok = y ({r['clause_id']}, {r['aspect']})")
            rows.append((r["clause_id"], r["aspect"], ok, hs))
    if not rows:
        raise SystemExit("Chưa có dòng nào được điền.")
    n = len(rows); ok_rows = [r for r in rows if r[2] == "y"]
    print(f"Cặp đã review: {n} | khía cạnh LLM được reviewer xác nhận: {len(ok_rows)}/{n} = {len(ok_rows)/n:.2f}")
    if not ok_rows:
        return
    y = [r[3] for r in ok_rows]
    llm = [pairs[(r[0], r[1])]["sentiment"] for r in ok_rows]
    acc = sum(a == b for a, b in zip(y, llm)) / len(y)
    print(f"Sentiment LLM so với reviewer (trên {len(y)} cặp khía cạnh được xác nhận): agreement {acc:.2f} | macro-F1 {macro_f1(y, llm):.2f}")
    print("  phân bố nhãn reviewer:", dict(Counter(y)), "| ma trận (reviewer->LLM):",
          {f"{a}->{b}": c for (a, b), c in sorted(Counter(zip(y, llm)).items())})
    if args.model:
        import joblib
        m = joblib.load(args.model)["model"]
        texts = [f"ASP_{r[1]} {pairs[(r[0], r[1])]['clause_text']}" for r in ok_rows]
        pred = list(m.predict(texts))
        accm = sum(a == b for a, b in zip(y, pred)) / len(y)
        print(f"Mô hình so với reviewer (cùng các cặp): agreement {accm:.2f} | macro-F1 {macro_f1(y, pred):.2f}")
        print("  ma trận (reviewer->mô hình):", {f"{a}->{b}": c for (a, b), c in sorted(Counter(zip(y, pred)).items())})
    print("Nêu rõ reviewer là người hay LLM; đây không thay thế test gold.")


if __name__ == "__main__":
    main()

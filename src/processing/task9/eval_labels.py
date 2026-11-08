# -*- coding: utf-8 -*-
"""
So nhãn dự đoán (vd rule_labels.jsonl) với nhãn tham chiếu (vd nhãn người hoặc LLM đã kiểm tra).

    python src/processing/task9/eval_labels.py --pred data/task9/rule_labels.jsonl --ref data/task9/llm_labels.jsonl
    python src/processing/task9/eval_labels.py --pred ... --ref ... --ref-range 201 300   # chỉ chấm các dòng 201-300 của file ref
    python src/processing/task9/eval_labels.py --pred ... --ref ... --skip-uncertain-ref   # bỏ cặp ref đánh uncertain

In: precision/recall/F1 khía cạnh (tổng và từng khía cạnh), độ chính xác cảm xúc trên các cặp trùng khía cạnh.
"""
import argparse, json
from collections import Counter

ASP = ["BATTERY", "DISPLAY", "PERFORMANCE", "CAMERA", "DESIGN", "SOFTWARE", "HARDWARE_OTHER", "PRICE", "WARRANTY"]

def load(p):
    d, order = {}, []
    for l in open(p, "rb"):
        if l.strip():
            r = json.loads(l); d[r["clause_id"]] = r["annotations"]; order.append(r["clause_id"])
    return d, order

ap = argparse.ArgumentParser()
ap.add_argument("--pred", required=True); ap.add_argument("--ref", required=True)
ap.add_argument("--ref-range", nargs=2, type=int); ap.add_argument("--skip-uncertain-ref", action="store_true")
a = ap.parse_args()
pred, _ = load(a.pred); ref, order = load(a.ref)
ids = order[a.ref_range[0] - 1:a.ref_range[1]] if a.ref_range else order
ids = [i for i in ids if i in pred]
tp, fp, fn = Counter(), Counter(), Counter(); same = agree = 0; conf = Counter()
for cid in ids:
    R = {x["aspect"]: x for x in ref[cid] if not (a.skip_uncertain_ref and x["uncertain"])}
    Pm = {x["aspect"]: x for x in pred[cid]}
    for asp in set(R) | set(Pm):
        if asp in R and asp in Pm:
            tp[asp] += 1; same += 1; agree += R[asp]["sentiment"] == Pm[asp]["sentiment"]
            conf[(R[asp]["sentiment"], Pm[asp]["sentiment"])] += 1
        elif asp in Pm: fp[asp] += 1
        else: fn[asp] += 1
def prf(t, f, n):
    p = t / (t + f) if t + f else 0; r = t / (t + n) if t + n else 0
    return round(p, 2), round(r, 2), round(2 * p * r / (p + r), 2) if p + r else 0
print(f"mệnh đề chấm: {len(ids)}")
print("khía cạnh   P / R / F1   (tp fp fn)")
for asp in ASP:
    print(f"{asp:15}", prf(tp[asp], fp[asp], fn[asp]), (tp[asp], fp[asp], fn[asp]))
print(f"{'TỔNG (micro)':15}", prf(sum(tp.values()), sum(fp.values()), sum(fn.values())))
print(f"cảm xúc đúng trên cặp trùng khía cạnh: {agree}/{same} = {round(agree / same, 2) if same else None}")
print("ma trận (ref -> pred):", {f"{k[0]}->{k[1]}": v for k, v in sorted(conf.items())})

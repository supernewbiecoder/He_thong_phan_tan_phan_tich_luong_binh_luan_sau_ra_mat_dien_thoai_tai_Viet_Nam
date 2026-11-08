# -*- coding: utf-8 -*-
"""
Công việc 9 - kiểm tra chất lượng nhãn LLM bằng người (guideline yêu cầu ~200 mệnh đề).

1) Xuất mẫu ngẫu nhiên để người xem và điền nhãn (nên dùng --blind để không thấy nhãn LLM):
    python src/processing/task9/review_sample.py export --n 200 --blind
   -> data/task9/review_sample.csv  (mở bằng Excel/Google Sheets)
   Người kiểm tra điền cột `human_labels`:
       PERFORMANCE:neg;BATTERY:neg   (mỗi cặp ASPECT:sent, ngăn cách bằng dấu ;)
       NONE                          (mệnh đề không có khía cạnh nào)
       để trống                      (chưa kiểm tra -> bị bỏ qua khi chấm)

2) Chấm sau khi người đã điền:
    python src/processing/task9/review_sample.py score
   In: tỷ lệ mệnh đề khớp hoàn toàn, precision/recall cặp (aspect, sentiment),
   và tỷ lệ cảm xúc đúng khi hai bên cùng chọn một khía cạnh.
"""

import argparse, csv, json, os, random

ASPECTS = {"BATTERY", "DISPLAY", "PERFORMANCE", "CAMERA", "DESIGN", "SOFTWARE", "HARDWARE_OTHER", "PRICE", "WARRANTY"}
SENT = {"pos", "neg", "neu"}


def fmt(anns):
    return ";".join(f"{a['aspect']}:{a['sentiment']}" for a in anns)


def parse(s):
    out = {}
    for part in (s or "").replace(" ", "").split(";"):
        if not part or part.upper() == "NONE":
            continue
        asp, _, sen = part.partition(":")
        asp, sen = asp.upper(), sen.lower()
        if asp not in ASPECTS or sen not in SENT:
            raise SystemExit(f"Nhãn người không hợp lệ: {part!r}")
        out[asp] = sen
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["export", "score"])
    ap.add_argument("--labels", default="data/task9/llm_labels.jsonl")
    ap.add_argument("--clauses", default="data/task9/clauses.jsonl", help="để lấy parent_text")
    ap.add_argument("--csv", default="data/task9/review_sample.csv")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--blind", action="store_true", help="ẩn cột llm_labels khi xuất (khuyến nghị)")
    args = ap.parse_args()

    if args.mode == "export":
        rows = [json.loads(l) for l in open(args.labels, "rb") if l.strip()]
        random.Random(args.seed).shuffle(rows)
        rows = rows[:args.n]
        want = {r["clause_id"] for r in rows}
        parents = {}
        with open(args.clauses, "rb") as f:
            for l in f:
                if l.strip():
                    c = json.loads(l)
                    if c["clause_id"] in want:
                        parents[c["clause_id"]] = c.get("parent_text") or ""
        cols = ["clause_id", "clause_text", "parent_text", "human_labels", "note"]
        if not args.blind:
            cols.insert(3, "llm_labels")
        with open(args.csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                d = {"clause_id": r["clause_id"], "clause_text": r["clause_text"],
                     "parent_text": parents.get(r["clause_id"], ""), "human_labels": "", "note": ""}
                if not args.blind:
                    d["llm_labels"] = fmt(r["annotations"])
                w.writerow(d)
        print(f"Đã xuất {len(rows)} mệnh đề -> {args.csv}")
        return

    llm = {}
    for l in open(args.labels, "rb"):
        if l.strip():
            r = json.loads(l)
            llm[r["clause_id"]] = {a["aspect"]: a["sentiment"] for a in r["annotations"]}
    n = exact = tp = fp = fn = same_asp = same_sent = 0
    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not (row.get("human_labels") or "").strip():
                continue  # chưa kiểm tra
            h, m = parse(row["human_labels"]), llm.get(row["clause_id"])
            if m is None:
                continue
            n += 1
            exact += (h == m)
            tp += sum(1 for a, s in m.items() if h.get(a) == s)
            fp += sum(1 for a, s in m.items() if h.get(a) != s)
            fn += sum(1 for a, s in h.items() if m.get(a) != s)
            for a in set(h) & set(m):
                same_asp += 1
                same_sent += (h[a] == m[a])
    div = lambda a, b: round(a / b, 3) if b else None
    print(json.dumps({
        "clauses_scored": n, "exact_match_clause": div(exact, n),
        "pair_precision": div(tp, tp + fp), "pair_recall": div(tp, tp + fn),
        "sentiment_agree_when_same_aspect": div(same_sent, same_asp),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

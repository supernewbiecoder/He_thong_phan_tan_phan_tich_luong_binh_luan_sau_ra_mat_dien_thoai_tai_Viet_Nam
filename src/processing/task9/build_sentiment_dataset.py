# -*- coding: utf-8 -*-
"""
Công việc 9 - Giai đoạn 1, Bước 4: làm phẳng nhãn LLM thành bộ dữ liệu huấn luyện mô hình cảm xúc.

Đầu vào : data/task9/llm_labels.jsonl           (từ llm_label.py; mỗi dòng 1 mệnh đề, có list annotations)
Đầu ra  : data/task9/sentiment_train.jsonl      (mỗi dòng 1 cặp mệnh đề–khía cạnh–cảm xúc, uncertain = false)
          data/task9/sentiment_val.jsonl        (như trên; chia theo video_id)
          data/task9/sentiment_uncertain.jsonl  (cặp uncertain = true, tách riêng; KHÔNG vào train/val)
          data/task9/sentiment_stats.json       (phân bố nhãn, cảnh báo thiếu mẫu)

Chạy từ thư mục gốc repo:
    python src/processing/task9/build_sentiment_dataset.py
    python src/processing/task9/build_sentiment_dataset.py --val-frac 0.15 --seed 42 --include-uncertain

Lưu ý:
  - Nhãn do LLM (label_source = "llm") hoặc luật (label_source = "rule", dùng --label-source rule): chỉ dùng để huấn luyện/validate nội bộ, KHÔNG phải test.
    Tập test chính phải là gold do người gán (ml-training.md).
  - Chia theo video_id bằng băm (hash) nên ổn định: gán thêm dữ liệu về sau không làm video đổi tập.
  - Mệnh đề không có khía cạnh (annotations rỗng) không tạo mẫu cảm xúc; chúng vẫn nằm trong llm_labels.jsonl
    để dùng cho mô hình khía cạnh (Công việc 8).
"""
import argparse, hashlib, json, os
from collections import Counter, defaultdict

ASPECTS = ["BATTERY", "DISPLAY", "PERFORMANCE", "CAMERA", "DESIGN",
           "SOFTWARE", "HARDWARE_OTHER", "PRICE", "WARRANTY"]
SENTIMENTS = ["pos", "neg", "neu"]


def split_of(video_id, seed, val_frac):
    h = int(hashlib.sha1(f"{seed}:{video_id}".encode("utf-8")).hexdigest(), 16) % 10000
    return "val" if h < val_frac * 10000 else "train"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", nargs="+", default=["data/task9/llm_labels.jsonl"],
                    help="một hoặc nhiều file nhãn cùng label_source; cặp (clause_id, aspect) trùng thì lấy bản gặp đầu tiên")
    ap.add_argument("--outdir", default="data/task9")
    ap.add_argument("--val-frac", type=float, default=0.15, help="tỷ lệ VIDEO đưa vào val")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--label-source", choices=["llm", "rule"], default="llm",
                    help="nguồn nhãn của file đầu vào; phải khớp trường label_source trong file (llm_labels.jsonl -> llm, rule_labels.jsonl -> rule)")
    ap.add_argument("--max-aspects-per-clause", type=int, default=0,
                    help="bỏ các mệnh đề có NHIỀU HƠN số khía cạnh này (0 = không lọc; khuyến nghị 2). "
                         "Mệnh đề gán 3+ khía cạnh thường là gán thừa của LLM")
    ap.add_argument("--include-uncertain", action="store_true",
                    help="đưa cả cặp uncertain vào train/val (mặc định: tách ra sentiment_uncertain.jsonl)")
    ap.add_argument("--min-cell", type=int, default=50, help="cảnh báo nếu (khía cạnh, cảm xúc) trong train < ngưỡng này")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    paths = {k: os.path.join(args.outdir, f"sentiment_{k}.jsonl") for k in ("train", "val", "uncertain")}
    outs = {k: open(p, "w", encoding="utf-8", newline="\n") for k, p in paths.items()}

    seen = set()
    stats = Counter()
    cell = {"train": Counter(), "val": Counter()}
    videos = {"train": set(), "val": set()}
    run_ids, combos = set(), set()
    filters = Counter()
    try:
        for line in (l for p in args.input for l in open(p, "rb")):
            if True:
                if not line.strip():
                    continue
                r = json.loads(line)
                stats["clauses_in"] += 1
                if r.get("label_source") != args.label_source:
                    raise SystemExit(f"[LỖI] {r['clause_id']}: label_source phải là {args.label_source!r}, gặp {r.get('label_source')!r}. "
                                     f"Không trộn nhãn rule và llm; dùng --label-source đúng với file.")
                combos.add((r["annotator"], r["prompt_version"], r["guideline_version"]))
                filters[r.get("selection_filter") or "none (mẫu ngẫu nhiên rải đều theo video)"] += 1
                anns = r.get("annotations") or []
                if not anns:
                    stats["clauses_no_aspect"] += 1
                    continue
                if args.max_aspects_per_clause and len(anns) > args.max_aspects_per_clause:
                    stats["clauses_dropped_too_many_aspects"] += 1
                    stats["pairs_dropped_too_many_aspects"] += len(anns)
                    continue
                split = split_of(r["video_id"], args.seed, args.val_frac)
                for a in anns:
                    if a["aspect"] not in ASPECTS or a["sentiment"] not in SENTIMENTS:
                        stats["pairs_invalid_skipped"] += 1
                        continue
                    key = (r["clause_id"], a["aspect"])
                    if key in seen:
                        stats["pairs_duplicate_skipped"] += 1
                        continue
                    seen.add(key)
                    row = {
                        "clause_id": r["clause_id"], "comment_id": r["comment_id"], "video_id": r["video_id"],
                        "clause_idx": r["clause_idx"], "clause_text": r["clause_text"],
                        "aspect": a["aspect"], "sentiment": a["sentiment"], "uncertain": bool(a["uncertain"]),
                        "label_source": args.label_source, "annotator": r["annotator"],
                        "guideline_version": r["guideline_version"], "prompt_version": r["prompt_version"],
                    }
                    stats["pairs_total"] += 1
                    if row["uncertain"] and not args.include_uncertain:
                        row["split"] = None
                        outs["uncertain"].write(json.dumps(row, ensure_ascii=False) + "\n")
                        stats["pairs_uncertain_separated"] += 1
                        continue
                    row["split"] = split
                    outs[split].write(json.dumps(row, ensure_ascii=False) + "\n")
                    stats[f"pairs_{split}"] += 1
                    cell[split][(a["aspect"], a["sentiment"])] += 1
                    videos[split].add(r["video_id"])
    finally:
        for o in outs.values():
            o.close()

    assert not (videos["train"] & videos["val"]), "rò rỉ: có video nằm ở cả train và val"

    table = {sp: {asp: {s: cell[sp][(asp, s)] for s in SENTIMENTS} for asp in ASPECTS} for sp in cell}
    warnings = [f"train: {asp}/{s} chỉ có {table['train'][asp][s]} mẫu (< {args.min_cell})"
                for asp in ASPECTS for s in SENTIMENTS if table["train"][asp][s] < args.min_cell]
    out = {
        "input": args.input, "seed": args.seed, "val_frac_videos": args.val_frac,
        "include_uncertain": args.include_uncertain,
        "label_configs_seen": [list(c) for c in sorted(combos)],
        "counts": dict(stats),
        "clauses_by_selection_filter": dict(filters),
        "videos": {k: len(v) for k, v in videos.items()},
        "aspect_x_sentiment": table,
        "warnings": warnings,
        "label_source": args.label_source, "note": "Nhãn LLM/luật, không phải gold. Không dùng làm tập test.",
    }
    with open(os.path.join(args.outdir, "sentiment_stats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps(out["counts"], ensure_ascii=False, indent=2))
    print("videos:", out["videos"])
    print(f"{'aspect':16}" + "".join(f"{s+'(tr/va)':>16}" for s in SENTIMENTS))
    for asp in ASPECTS:
        print(f"{asp:16}" + "".join(f"{table['train'][asp][s]:>9}/{table['val'][asp][s]:<6}" for s in SENTIMENTS))
    for w in warnings:
        print("[CẢNH BÁO]", w)


if __name__ == "__main__":
    main()

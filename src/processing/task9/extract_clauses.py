# -*- coding: utf-8 -*-
"""
Công việc 9 - Giai đoạn 1, Bước 2: trích xuất mệnh đề từ clean_data.jsonl.

Chạy từ thư mục gốc repo:
    python src/processing/task9/extract_clauses.py
Tùy chọn:
    --input  data/clean_data.jsonl
    --output data/task9/clauses.jsonl
    --index-base 1      # clause_idx lấy đúng clause_id trong file nguồn (1-based). Dùng 0 nếu nhóm quy ước 0-based.

Quy tắc:
  - Bỏ bình luận is_spam = true. KHÔNG lọc thêm gì khác (không bỏ từ phủ định, không lọc is_vietnamese).
  - Mỗi phần tử của `clauses` -> 1 dòng. Văn bản gán nhãn = text_norm của mệnh đề; giữ `text` để đối chiếu.
  - clause_id (ổn định) = "<comment_id>#<clause_idx>", khớp quy ước gold_labels trong data-model.md.
  - Không sửa file đầu vào (chỉ đọc).
"""
import argparse, hashlib, json, os, sys
from collections import Counter


def iter_records(path):
    # Đọc nhị phân rồi strip để chịu được cả LF lẫn CRLF.
    with open(path, "rb") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield lineno, json.loads(raw)
            except json.JSONDecodeError as e:
                raise SystemExit(f"[LỖI] Dòng {lineno} không phải JSON hợp lệ: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/clean_data.jsonl")
    ap.add_argument("--output", default="data/task9/clauses.jsonl")
    ap.add_argument("--index-base", type=int, choices=(0, 1), default=1)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    tmp = args.output + ".tmp"

    stats = Counter()
    seen = set()
    h = hashlib.sha256()
    with open(tmp, "wb") as out:
        for lineno, r in iter_records(args.input):
            stats["comments_total"] += 1
            if r.get("is_spam"):
                stats["comments_spam_skipped"] += 1
                continue
            stats["comments_kept"] += 1
            clauses = r.get("clauses") or []
            if not clauses:
                stats["comments_without_clauses"] += 1
                continue
            parent_text = r.get("parent_text") or None
            for pos, c in enumerate(clauses):
                text_norm = (c.get("text_norm") or "").strip()
                if not text_norm:
                    stats["clauses_empty_text_norm_skipped"] += 1
                    continue
                # clause_id trong file nguồn là 1-based; đổi theo --index-base
                src_idx = c.get("clause_id", pos + 1)
                idx = src_idx - 1 if args.index_base == 0 else src_idx
                cid = f"{r['comment_id']}#{idx}"
                if cid in seen:
                    raise SystemExit(f"[LỖI] Trùng clause_id: {cid} (dòng {lineno})")
                seen.add(cid)
                row = {
                    "clause_id": cid,
                    "comment_id": r["comment_id"],
                    "clause_idx": idx,
                    "video_id": r.get("video_id"),
                    "video_model": r.get("model"),
                    "source": r.get("source"),
                    "text_norm": text_norm,
                    "text": c.get("text"),
                    "parent_id": r.get("parent_id") or None,
                    "parent_text": parent_text,
                    "is_vietnamese": r.get("is_vietnamese"),
                    "published_at": r.get("published_at"),
                }
                line = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
                out.write(line)
                h.update(line)
                stats["clauses_written"] += 1
                if parent_text:
                    stats["clauses_with_parent_text"] += 1
    os.replace(tmp, args.output)

    stats["videos"] = None
    summary = dict(stats)
    summary.pop("videos")
    summary["input"] = args.input
    summary["output"] = args.output
    summary["index_base"] = args.index_base
    summary["output_sha256"] = h.hexdigest()
    with open(os.path.splitext(args.output)[0] + "_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())

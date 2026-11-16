"""Quản lý nhãn spam: gộp hai người gán, phân giải lệch, và vòng người duyệt.

Các bước (chạy từ thư mục gốc repo):

  python -m src.processing.spam.labels merge            gộp annotator_A/B (+ adjudication) thành file nhãn
  python -m src.processing.spam.labels export-review    xuất CSV có nội dung cho người duyệt (mở bằng Excel)
  python -m src.processing.spam.labels import-review    nhập CSV đã duyệt, đổi label_source thành human

File làm việc (annotator_*.tsv, adjudication.tsv, review_*.csv) nằm trong
data/labels/spam/ và không vào git vì có nội dung bình luận. File nhãn cuối
src/processing/spam/labels/spam_labels_v1.tsv vào git, chỉ có ID và nhãn.
"""
import argparse
import collections
import csv
import sys
from typing import Dict, List

from . import config, data
from .evaluate import cohen_kappa

LABEL_FIELDS = [
    "item_id", "comment_id", "video_id", "text_sha1", "stratum", "split",
    "label", "spam_type", "lang",
    "label_a", "label_b", "spam_type_a", "spam_type_b", "lang_a", "lang_b",
    "resolution", "label_source", "annotators", "reviewed_by", "guideline_version", "note",
]
REVIEW_FIELDS = [
    "item_id", "split", "text", "parent_text", "label", "spam_type", "lang",
    "ok", "human_label", "human_spam_type", "human_lang", "human_note",
]


def _validate(row: Dict[str, str], who: str) -> None:
    item = row.get("item_id", "?")
    if row["label"] not in config.LABELS:
        raise ValueError(f"{who} {item}: label '{row['label']}' không hợp lệ")
    if row["lang"] not in config.LANGS:
        raise ValueError(f"{who} {item}: lang '{row['lang']}' không hợp lệ")
    if row["label"] == "spam" and row["spam_type"] not in config.SPAM_TYPES:
        raise ValueError(f"{who} {item}: spam phải có spam_type hợp lệ, đang là '{row['spam_type']}'")
    if row["label"] == "ham" and row["spam_type"]:
        raise ValueError(f"{who} {item}: ham không được có spam_type")


def _read_annotator(name: str, expected_ids: List[str]) -> Dict[str, Dict[str, str]]:
    path = config.WORK_DIR / f"annotator_{name}.tsv"
    rows = {}
    for row in data.read_tsv(path):
        row = {key: (value or "").strip() for key, value in row.items() if key}
        _validate(row, f"annotator_{name}")
        if row["item_id"] in rows:
            raise ValueError(f"annotator_{name}: trùng {row['item_id']}")
        rows[row["item_id"]] = row
    missing = set(expected_ids) - set(rows)
    extra = set(rows) - set(expected_ids)
    if missing or extra:
        raise ValueError(f"annotator_{name}: thiếu {sorted(missing)[:5]}, thừa {sorted(extra)[:5]}")
    return rows


def merge(annotator_names: str, annotator_ids: str) -> int:
    sample = data.read_tsv(config.SAMPLE_PATH)
    ids = [row["item_id"] for row in sample]
    first, second = annotator_names.split(",")
    ann_a, ann_b = _read_annotator(first, ids), _read_annotator(second, ids)

    adjudication_path = config.WORK_DIR / "adjudication.tsv"
    adjudicated = {}
    if adjudication_path.exists():
        for row in data.read_tsv(adjudication_path):
            row = {key: (value or "").strip() for key, value in row.items() if key}
            _validate(row, "adjudication")
            adjudicated[row["item_id"]] = row

    merged, unresolved = [], []
    for row in sample:
        a, b = ann_a[row["item_id"]], ann_b[row["item_id"]]
        agree = (a["label"], a["spam_type"], a["lang"]) == (b["label"], b["spam_type"], b["lang"])
        if agree:
            final, resolution = a, "agree"
        elif row["item_id"] in adjudicated:
            final, resolution = adjudicated[row["item_id"]], "adjudicated"
        else:
            unresolved.append(row["item_id"])
            continue
        notes = [n for n in (a.get("note"), b.get("note"),
                             final.get("note") if resolution == "adjudicated" else "") if n]
        merged.append({
            **row,
            "label": final["label"], "spam_type": final["spam_type"], "lang": final["lang"],
            "label_a": a["label"], "label_b": b["label"],
            "spam_type_a": a["spam_type"], "spam_type_b": b["spam_type"],
            "lang_a": a["lang"], "lang_b": b["lang"],
            "resolution": resolution, "label_source": "llm", "annotators": annotator_ids,
            "reviewed_by": "", "guideline_version": config.GUIDELINE_VERSION,
            "note": " | ".join(dict.fromkeys(notes)),
        })

    labels_a = [ann_a[i]["label"] for i in ids]
    labels_b = [ann_b[i]["label"] for i in ids]
    langs_a = [ann_a[i]["lang"] for i in ids]
    langs_b = [ann_b[i]["lang"] for i in ids]
    print(f"Số dòng: {len(ids)}")
    print(f"Đồng thuận label: {sum(x == y for x, y in zip(labels_a, labels_b)) / len(ids):.4f}"
          f" | Cohen's kappa = {cohen_kappa(labels_a, labels_b):.4f}")
    print(f"Đồng thuận lang : {sum(x == y for x, y in zip(langs_a, langs_b)) / len(ids):.4f}"
          f" | Cohen's kappa = {cohen_kappa(langs_a, langs_b):.4f}")
    print("Bảng chéo label (A, B):", dict(collections.Counter(zip(labels_a, labels_b))))

    if unresolved:
        out = config.WORK_DIR / "disagreements.txt"
        joined = {r["item_id"]: r for r in data.attach_text([r for r in sample if r["item_id"] in unresolved])}
        with open(out, "w", encoding="utf-8") as handle:
            for item in unresolved:
                a, b, row = ann_a[item], ann_b[item], joined[item]
                handle.write(f"### {item}\n")
                if row.get("parent_text"):
                    handle.write(f"(trả lời: «{row['parent_text'][:200]}»)\n")
                handle.write(row["text"][:900].replace("\n", " ⏎ ") + "\n")
                handle.write(f"A: {a['label']}/{a['spam_type']}/{a['lang']}  {a.get('note', '')}\n")
                handle.write(f"B: {b['label']}/{b['spam_type']}/{b['lang']}  {b.get('note', '')}\n\n")
        print(f"Còn {len(unresolved)} dòng lệch chưa phân giải, xem {out}")
        print("Ghi quyết định vào data/labels/spam/adjudication.tsv "
              "(item_id, label, spam_type, lang, note) rồi chạy lại merge.")
        return 1

    data.write_tsv(config.LABELS_PATH, merged, LABEL_FIELDS)
    resolved = collections.Counter(row["resolution"] for row in merged)
    print(f"Đã ghi {len(merged)} nhãn vào {config.LABELS_PATH} ({dict(resolved)})")
    return 0


def export_review(split: str) -> int:
    rows = [row for row in data.read_tsv(config.LABELS_PATH) if split in ("all", row["split"])]
    joined = data.attach_text(rows)
    path = config.WORK_DIR / f"review_{split}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig để Excel trên Windows hiển thị đúng tiếng Việt.
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for row in joined:
            writer.writerow({
                "item_id": row["item_id"], "split": row["split"], "text": row["text"],
                "parent_text": row.get("parent_text") or "", "label": row["label"],
                "spam_type": row["spam_type"], "lang": row["lang"],
                "ok": "", "human_label": "", "human_spam_type": "", "human_lang": "", "human_note": "",
            })
    print(f"Đã ghi {len(joined)} dòng vào {path}")
    print("Cách duyệt: nhãn đúng thì gõ x vào cột ok. Nhãn sai thì để trống ok và điền "
          "human_label (spam/ham), human_spam_type (nếu spam), human_lang (vi/other/none).")
    return 0


def import_review(path: str, reviewer: str) -> int:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reviewed = {row["item_id"]: row for row in csv.DictReader(handle)}
    labels = data.read_tsv(config.LABELS_PATH)
    llm_labels, human_labels, changed, done = [], [], [], 0
    for row in labels:
        review = reviewed.get(row["item_id"])
        if review is None:
            continue
        ok = (review.get("ok") or "").strip().lower() in ("x", "ok", "1", "yes", "y", "đ", "d")
        human_label = (review.get("human_label") or "").strip().lower()
        if not ok and not human_label:
            continue  # chưa duyệt dòng này
        if ok and human_label:
            raise ValueError(f"{row['item_id']}: vừa đánh dấu ok vừa điền human_label")
        before = (row["label"], row["spam_type"], row["lang"])
        if not ok:
            row["label"] = human_label
            row["spam_type"] = (review.get("human_spam_type") or "").strip().lower()
            row["lang"] = (review.get("human_lang") or "").strip().lower() or row["lang"]
            _validate(row, "review")
        llm_labels.append(before[0])
        human_labels.append(row["label"])
        if before != (row["label"], row["spam_type"], row["lang"]):
            changed.append(row["item_id"])
            row["resolution"] = "human_corrected"
        note = (review.get("human_note") or "").strip()
        if note:
            row["note"] = " | ".join(part for part in (row["note"], f"human: {note}") if part)
        row["label_source"], row["reviewed_by"] = "human", reviewer
        done += 1
    if not done:
        print("Không có dòng nào được duyệt trong file.")
        return 1
    data.write_tsv(config.LABELS_PATH, labels, LABEL_FIELDS)
    agreement = sum(x == y for x, y in zip(llm_labels, human_labels)) / done
    kappa = cohen_kappa(llm_labels, human_labels)
    print(f"Đã duyệt {done} dòng; người duyệt sửa {len(changed)} dòng: {changed[:20]}")
    print(f"Nhãn AI đúng so với người duyệt (label): {agreement:.4f}"
          + (f" | kappa = {kappa:.4f}" if kappa is not None else ""))
    remaining = sum(1 for row in labels if row["label_source"] != "human")
    print(f"Còn {remaining} dòng chưa có người duyệt. Chạy lại train để cập nhật kết quả.")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Quản lý nhãn spam (Công việc 11)")
    commands = parser.add_subparsers(dest="command", required=True)
    merge_cmd = commands.add_parser("merge", help="gộp hai người gán và phần phân giải")
    merge_cmd.add_argument("--annotators", default="A,B", help="hậu tố file annotator_<x>.tsv")
    merge_cmd.add_argument("--annotator-ids", required=True,
                           help="mã hai người gán và người phân giải, ghi vào cột annotators")
    review_cmd = commands.add_parser("export-review", help="xuất CSV cho người duyệt")
    review_cmd.add_argument("--split", choices=["test", "train", "all"], default="test")
    import_cmd = commands.add_parser("import-review", help="nhập CSV đã duyệt")
    import_cmd.add_argument("--file", default=str(config.WORK_DIR / "review_test.csv"))
    import_cmd.add_argument("--reviewer", required=True, help="mã người duyệt, vd nlquan")
    args = parser.parse_args()

    if args.command == "merge":
        return merge(args.annotators, args.annotator_ids)
    if args.command == "export-review":
        return export_review(args.split)
    return import_review(args.file, args.reviewer)


if __name__ == "__main__":
    sys.exit(main())

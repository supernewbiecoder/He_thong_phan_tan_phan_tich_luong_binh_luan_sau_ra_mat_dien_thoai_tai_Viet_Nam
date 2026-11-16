"""Lấy mẫu phân tầng các bình luận cần gán nhãn spam.

Vì spam hiếm (rule-v0 gắn cờ khoảng 3%), lấy ngẫu nhiên 500 bình luận sẽ chỉ có
vài chục spam và gần như không thấy spam mà luật bỏ sót. Mẫu được chia tầng theo
đầu ra của rule-v0, lấy ngẫu nhiên đơn giản trong từng tầng. Cỡ quần thể từng
tầng được lưu lại để quy kết quả trên mẫu về toàn bộ dữ liệu (trọng số N_h/n_h).

Chạy:  python -m src.processing.spam.sampling
"""
import argparse
import collections
import json
import sys
import random
import re
from typing import Dict, List

from . import config, data
from .baseline import CONTENT_REASONS, FORM_REASONS, NOTEXT_REASONS

# Dấu hiệu "đáng ngờ" KHÔNG dùng lại regex của rule-v0, để tìm spam mà luật bỏ sót.
PROMO_HINT = re.compile(
    r"(?<!\w)(sub|subscribe|đăng\s*k[ýí]|đk\s+kênh|kênh\s+(?:mình|em|tớ|tui|tôi|e|m)|ghé|"
    r"giao\s+lưu|shop|cửa\s+hàng|giá\s+sỉ|sỉ\s+lẻ|free\s*ship|thanh\s+lý|cần\s+bán|bán\s+lại|"
    r"pass\s+lại|ib|inb|sđt|sdt|lh|liên\s+hệ|fb|facebook|group|nhóm|kiếm\s+tiền|vay|mã\s+giảm|"
    r"khuyến\s+mãi|giveaway|tặng|link|web|trang|uy\s+tín|giá\s+tốt|giá\s+rẻ\s+nhất|ae\s+cần|"
    r"ai\s+cần|ai\s+mua|bên\s+(?:mình|em)|inbox)(?!\w)",
    re.IGNORECASE,
)
LONG_DIGITS = re.compile(r"\d[\d\s.\-]{7,}\d")
EMAIL = re.compile(r"\S+@\S+\.\S+")
DUP_MIN_CHARS = 25
DUP_MIN_COPIES = 3


def normalize_for_dup(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def stratum_of(comment: dict, dup_counts: Dict[str, int]) -> str:
    reasons = set(comment["spam_reasons"])
    if reasons & CONTENT_REASONS:
        return "rule_content"
    if reasons & NOTEXT_REASONS:
        return "rule_notext"
    if reasons & FORM_REASONS:
        return "rule_form"
    if reasons:
        return "rule_nonvn_only"
    text = comment["text"]
    normalized = normalize_for_dup(text)
    if len(normalized) >= DUP_MIN_CHARS and dup_counts[normalized] >= DUP_MIN_COPIES:
        return "unflagged_dup"
    if PROMO_HINT.search(text) or LONG_DIGITS.search(text) or EMAIL.search(text):
        return "unflagged_suspect"
    return "unflagged_rest"


def build_sample() -> Dict[str, object]:
    data.check_dataset_version()
    comments = list(data.iter_comments())
    dup_counts = collections.Counter(normalize_for_dup(c["text"]) for c in comments)

    by_stratum: Dict[str, List[dict]] = collections.defaultdict(list)
    for comment in comments:
        by_stratum[stratum_of(comment, dup_counts)].append(comment)

    rng = random.Random(config.SAMPLE_SEED)
    chosen: List[dict] = []
    strata_info: Dict[str, Dict[str, int]] = {}
    for stratum, size in config.STRATA_SIZES.items():
        # Sắp theo comment_id trước khi rút để kết quả không phụ thuộc thứ tự file.
        population = sorted(by_stratum[stratum], key=lambda c: c["comment_id"])
        picked = rng.sample(population, size)
        splits = collections.Counter(data.split_of(c["video_id"]) for c in population)
        strata_info[stratum] = {
            "N": len(population), "N_train": splits["train"], "N_test": splits["test"], "n": size,
        }
        for comment in picked:
            chosen.append({
                "comment_id": comment["comment_id"],
                "video_id": comment["video_id"],
                "text_sha1": data.text_hash(comment["text"]),
                "stratum": stratum,
                "split": data.split_of(comment["video_id"]),
            })

    # Xáo thứ tự để người gán không đoán được tầng từ vị trí.
    rng.shuffle(chosen)
    for index, row in enumerate(chosen, start=1):
        row["item_id"] = f"S{index:04d}"

    unknown = set(by_stratum) - set(config.STRATA_SIZES)
    assert not unknown, f"Tầng chưa khai báo cỡ mẫu: {unknown}"
    assert sum(info["N"] for info in strata_info.values()) == len(comments)
    return {"rows": chosen, "strata": strata_info, "n_comments": len(comments)}


def write_annotation_batches(rows: List[dict], batch_size: int = 160) -> List[str]:
    """Ghi các file văn bản cho người gán: chỉ có nội dung, không có tầng hay cờ của luật."""
    joined = data.attach_text(rows)
    config.WORK_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for start in range(0, len(joined), batch_size):
        chunk = joined[start:start + batch_size]
        path = config.WORK_DIR / f"annotation_batch_{start // batch_size + 1}.txt"
        with open(path, "w", encoding="utf-8") as handle:
            for row in chunk:
                text = row["text"].replace("\r", " ").replace("\n", " ⏎ ")
                if len(text) > 700:
                    text = text[:500] + " […] " + text[-150:]
                handle.write(f"### {row['item_id']} | máy của video: {row['video_model']}")
                if row.get("parent_text"):
                    parent = row["parent_text"].replace("\n", " ")[:160]
                    handle.write(f" | trả lời bình luận: «{parent}»")
                handle.write(f"\n{text}\n\n")
        paths.append(str(path))
    return paths


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định không in được tiếng Việt
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--export-batches", action="store_true",
                        help="ghi thêm file văn bản để gán nhãn vào data/labels/spam/")
    args = parser.parse_args()

    result = build_sample()
    fields = ["item_id", "comment_id", "video_id", "text_sha1", "stratum", "split"]
    rows = sorted(result["rows"], key=lambda r: r["item_id"])
    data.write_tsv(config.SAMPLE_PATH, rows, fields)
    strata_path = config.LABELS_DIR / "spam_strata_v1.json"
    strata_path.write_text(json.dumps({
        "dataset": config.DATASET_VERSION, "dataset_sha256": config.DATASET_SHA256,
        "n_comments": result["n_comments"], "seed": config.SAMPLE_SEED,
        "split_salt": config.SPLIT_SALT, "test_fraction": config.TEST_FRACTION,
        "strata": result["strata"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Đã ghi {len(rows)} dòng mẫu vào {config.SAMPLE_PATH}")
    for stratum, info in result["strata"].items():
        print(f"  {stratum:20s} N={info['N']:>7,}  n={info['n']:>3}")
    if args.export_batches:
        for path in write_annotation_batches(rows):
            print("  batch:", path)


if __name__ == "__main__":
    main()

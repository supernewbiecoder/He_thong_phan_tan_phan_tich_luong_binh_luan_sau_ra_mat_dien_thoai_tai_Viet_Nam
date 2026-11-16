"""Đọc dữ liệu và file nhãn của Công việc 11.

File nhãn trong git chỉ có ID và nhãn. Nội dung bình luận được nối lại từ
clean_data.jsonl theo comment_id; mỗi dòng nhãn lưu kèm mã băm của nội dung để
phát hiện trường hợp ai đó dùng nhầm phiên bản dữ liệu.
"""
import csv
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from . import config


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_dataset_version(path: Path = config.CLEAN_DATA_PATH) -> str:
    """Dừng ngay nếu clean_data.jsonl không phải bản chuẩn mà mẫu và nhãn dựa vào."""
    if not path.exists():
        raise FileNotFoundError(
            f"Không thấy {path}. Tạo bằng: python src/processing/run_cleaning.py "
            "(xem src/processing/README.md)."
        )
    actual = file_sha256(path)
    if actual != config.DATASET_SHA256:
        raise ValueError(
            f"{path.name} có SHA-256 {actual}, khác bản chuẩn {config.DATASET_VERSION} "
            f"({config.DATASET_SHA256}). Mẫu và nhãn spam chỉ đúng với bản chuẩn."
        )
    return actual


def iter_comments(path: Path = config.CLEAN_DATA_PATH) -> Iterator[dict]:
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def text_hash(text: str) -> str:
    """Mã băm ngắn của nội dung, đủ để phát hiện lệch phiên bản dữ liệu."""
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:12]


def split_of(video_id: str) -> str:
    """Tập train/test của một video; cố định theo mã băm, không phụ thuộc mô hình."""
    digest = hashlib.sha1(f"{config.SPLIT_SALT}:{video_id}".encode("utf-8")).hexdigest()
    return "test" if int(digest[:8], 16) / 0xFFFFFFFF < config.TEST_FRACTION else "train"


def read_tsv(path: Path) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def attach_text(rows: List[Dict[str, str]], comments: Optional[Dict[str, dict]] = None,
                path: Path = config.CLEAN_DATA_PATH) -> List[dict]:
    """Nối nội dung bình luận vào các dòng mẫu/nhãn và kiểm tra mã băm từng dòng."""
    wanted = {row["comment_id"] for row in rows}
    if comments is None:
        comments = {c["comment_id"]: c for c in iter_comments(path) if c["comment_id"] in wanted}
    joined = []
    for row in rows:
        comment = comments.get(row["comment_id"])
        if comment is None:
            raise KeyError(f"comment_id {row['comment_id']} không có trong {path.name}")
        if text_hash(comment["text"]) != row["text_sha1"]:
            raise ValueError(
                f"Nội dung của {row['comment_id']} khác lúc lấy mẫu: sai phiên bản dữ liệu."
            )
        joined.append({**row, "text": comment["text"], "parent_text": comment.get("parent_text"),
                       "video_model": comment.get("model", ""),
                       # Đầu ra của rule-v0 đã lưu trong bản dữ liệu chuẩn.
                       "rule_reasons": list(comment.get("spam_reasons") or []),
                       "rule_is_vietnamese": bool(comment.get("is_vietnamese"))})
    return joined

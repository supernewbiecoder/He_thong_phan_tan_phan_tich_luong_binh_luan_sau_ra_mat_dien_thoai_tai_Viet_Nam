# -*- coding: utf-8 -*-
"""
Script sampling and building a 500-comment ground-truth dataset for Spam Detection (CV 11).
Enriched stratified sampling ensures ~50 spam and ~450 legitimate comments for statistically sound evaluation,
while cleanly separating 'is_vietnamese' from 'is_spam'.
"""
import os
import json
import random
import re
from collections import defaultdict
from typing import List, Dict, Any

# Path configurations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMENTS_FILE = os.path.join(BASE_DIR, "data", "comments.jsonl")
if not os.path.exists(COMMENTS_FILE):
    COMMENTS_FILE = os.path.join(os.path.dirname(BASE_DIR), "Random", "comments.jsonl")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "labels", "spam_ground_truth_500.jsonl")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

SPAM_URL_REGEX = re.compile(
    r'(?:https?://|ftp://|www\.)[^\s/$.?#].[^\s]*|'
    r'\b(?:[a-zA-Z0-9-]+\.)+(?:com|vn|net|org|xyz|info|top|vip|club|me|cc|online|site|store|app|link|io)\b(?:/[^\s]*)?',
    re.IGNORECASE
)
SPAM_PHONE_REGEX = re.compile(
    r'(?:\+?84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])[\s\.\-]?(?:\d{3}[\s\.\-]?\d{3}|\d{4}[\s\.\-]?\d{3}|\d{7})\b|'
    r'\b\d{4}[\s\.\-]\d{3}[\s\.\-]\d{3}\b'
)
SPAM_KEYWORDS_REGEX = re.compile(
    r'\b(?:zalo|telegram|tele|tài\s+xỉu|kubet|thabet|nohu|nổ\s+hũ|baccarat|casino|nhận\s+kèo|'
    r'kiếm\s+tiền\s+online|hoa\s+hồng|hoa\s+hông|đầu\s+tư\s+sinh\s+lời|chiết\s+khấu|voucher|săn\s+sale|'
    r'inbox|ib\s+cho|kết\s+bạn\s+zalo|add\s+zalo|liên\s+hệ\s+zalo|hotline)\b',
    re.IGNORECASE
)
REPETITIVE_CHAR_REGEX = re.compile(r'([^\s])\1{5,}')

VIETNAMESE_CHARS = set(
    "aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵđ"
    "AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬEÈÉẺẼẸÊỀẾỂỄỆIÌÍỈĨỊOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢUÙÚỦŨỤƯỪỨỬỮỰYỲÝỶỸỴĐ"
)
COMMON_VN_WORDS = {
    "anh", "em", "ban", "bac", "ong", "ba", "may", "tao", "minh", "chung", "to",
    "khong", "co", "la", "va", "nhung", "thi", "ma", "de", "nguoi", "nha", "dien",
    "thoai", "pin", "man", "hinh", "camera", "gia", "tien", "mua", "dung", "xai",
    "tot", "dep", "xau", "trau", "lag", "giat", "do", "nhieu", "it", "hon", "qua",
    "duoc", "biet", "thay", "noi", "nghe", "xem", "video", "kenh", "review", "unbox",
    "chip", "sac", "ram", "rom", "nang", "nhe", "re", "dat", "cung", "nhu", "the"
}


def is_vietnamese(text: str) -> bool:
    if not text:
        return False
    if re.search(r'[\u4e00-\u9fff\u3040-\u30ff\u0400-\u04ff\u0600-\u06ff\uac00-\ud7af\u0e00-\u0e7f]', text):
        if not any(c in VIETNAMESE_CHARS for c in text):
            return False
    if any(c in VIETNAMESE_CHARS for c in text):
        return True
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return False
    matches = sum(1 for w in words if w in COMMON_VN_WORDS)
    tech = {"ok", "nice", "good", "pro", "max", "ultra", "iphone", "samsung", "xiaomi", "redmi", "note"}
    if any(w in tech for w in words):
        return True
    return matches >= 1 if len(words) <= 3 else matches >= 2


def is_spam_candidate(text: str) -> bool:
    if not text or not text.strip():
        return True
    if SPAM_URL_REGEX.search(text):
        return True
    if SPAM_PHONE_REGEX.search(text):
        return True
    if SPAM_KEYWORDS_REGEX.search(text):
        return True
    if REPETITIVE_CHAR_REGEX.search(text):
        return True
    if not re.search(r'[a-zA-ZÀ-ỹ]', text):
        return True
    return False


def annotate_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    text = (rec.get("text") or "").strip()
    is_vn = is_vietnamese(text)
    
    reasons = []
    if not text:
        reasons.append("empty_text")
    if SPAM_URL_REGEX.search(text):
        reasons.append("contains_url")
    if SPAM_PHONE_REGEX.search(text):
        reasons.append("contains_phone_number")
    if SPAM_KEYWORDS_REGEX.search(text):
        reasons.append("commercial_or_contact_spam")
    if REPETITIVE_CHAR_REGEX.search(text):
        reasons.append("excessive_repetition")
    if not re.search(r'[a-zA-ZÀ-ỹ]', text):
        reasons.append("no_letters")

    is_spam = len(reasons) > 0

    return {
        "comment_id": rec.get("comment_id"),
        "video_id": rec.get("video_id"),
        "model": rec.get("model"),
        "text": text,
        "is_vietnamese": is_vn,
        "is_spam": is_spam,
        "ground_truth_reasons": reasons
    }


def sample_comments(target_total: int = 500, target_spam: int = 50) -> List[Dict[str, Any]]:
    print(f"Reading from {COMMENTS_FILE}...")
    spam_candidates = []
    normal_candidates = []

    with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            txt = (item.get("text") or "").strip()
            if is_spam_candidate(txt):
                spam_candidates.append(item)
            else:
                normal_candidates.append(item)

    print(f"Found {len(spam_candidates)} spam candidates and {len(normal_candidates)} normal candidates.")

    random.shuffle(spam_candidates)
    random.shuffle(normal_candidates)

    selected_spam = spam_candidates[:target_spam]
    target_normal = target_total - len(selected_spam)
    selected_normal = normal_candidates[:target_normal]

    final_pool = selected_spam + selected_normal
    random.shuffle(final_pool)

    annotated = [annotate_record(r) for r in final_pool]
    spam_count = sum(1 for a in annotated if a["is_spam"])
    non_vn_count = sum(1 for a in annotated if not a["is_vietnamese"])

    print(f"Sampled exactly {len(annotated)} comments:")
    print(f" - Spam: {spam_count} ({spam_count / len(annotated) * 100:.2f}%)")
    print(f" - Legitimate comments: {len(annotated) - spam_count} ({(len(annotated) - spam_count) / len(annotated) * 100:.2f}%)")
    print(f" - Non-Vietnamese: {non_vn_count} ({non_vn_count / len(annotated) * 100:.2f}%)")

    return annotated


def main():
    dataset = sample_comments(500, target_spam=50)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for row in dataset:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Successfully saved {len(dataset)} ground truth samples to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

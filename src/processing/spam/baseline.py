"""Baseline rule-v0: bộ luật spam hiện có trong src/processing/cleaner.

Không sửa bộ luật; module này chỉ gọi lại và tách các lý do thành từng nhóm để
đánh giá riêng "spam" với "không phải tiếng Việt" (yêu cầu của Công việc 11).
"""
from typing import Dict, FrozenSet, Iterable, List

from ..cleaner.spam_detector import detect_spam

CONTENT_REASONS: FrozenSet[str] = frozenset({
    "contains_url", "contains_phone_number", "external_contact_invite",
    "commercial_or_gambling_spam",
})
FORM_REASONS: FrozenSet[str] = frozenset({"excessive_character_repetition", "repetitive_words"})
NOTEXT_REASONS: FrozenSet[str] = frozenset({"no_alphabetical_content", "empty_text"})
LANGUAGE_REASONS: FrozenSet[str] = frozenset({"non_vietnamese_language"})

# Ba cách đọc bộ luật, từ rộng tới hẹp. "as_is" là đúng hành vi hiện tại của cleaner.
RULE_VARIANTS: Dict[str, FrozenSet[str]] = {
    "rule-v0 (nguyên trạng)": CONTENT_REASONS | FORM_REASONS | NOTEXT_REASONS | LANGUAGE_REASONS,
    "rule-v0 bỏ lý do ngôn ngữ": CONTENT_REASONS | FORM_REASONS | NOTEXT_REASONS,
    "rule-v0 chỉ nội dung + hình thức": CONTENT_REASONS | FORM_REASONS,
    "rule-v0 chỉ nội dung": CONTENT_REASONS,
}


def rule_reasons(text: str) -> List[str]:
    """Danh sách lý do rule-v0 gắn cờ cho một bình luận (rỗng nếu không gắn cờ)."""
    return list(detect_spam(text)["spam_reasons"])


def flags(reasons: Iterable[str], active: FrozenSet[str]) -> bool:
    """Bình luận có bị gắn cờ không khi chỉ tính các lý do trong `active`."""
    return bool(set(reasons) & active)

# -*- coding: utf-8 -*-
"""
Rule-based spam detection and language verification module.
According to project specification:
- Binary label: is_spam (True / False)
- Criteria:
  1. External links / URLs (http, bit.ly, shopee, etc.)
  2. Phone numbers (Zalo/contact/sales)
  3. Invitations to inbox, Telegram, Zalo
  4. Commercial / shop ads / gambling / online earning fraud
  5. Excessive character / word repetition
  6. Empty / non-text / gibberish content
  7. Non-Vietnamese comments (outside scope according to spec)
"""
import re
from typing import Dict, Any, List
try:
    from cleaner.config import (
        URL_REGEX,
        PHONE_REGEX,
        CONTACT_INVITE_REGEX,
        COMMERCIAL_SPAM_REGEX,
        REPETITIVE_CHAR_REGEX,
        REPETITIVE_WORD_REGEX,
        VIETNAMESE_CHARS,
        COMMON_VIETNAMESE_WORDS,
    )
except ImportError:
    from .config import (
        URL_REGEX,
        PHONE_REGEX,
        CONTACT_INVITE_REGEX,
        COMMERCIAL_SPAM_REGEX,
        REPETITIVE_CHAR_REGEX,
        REPETITIVE_WORD_REGEX,
        VIETNAMESE_CHARS,
        COMMON_VIETNAMESE_WORDS,
    )

# Regex to check if text contains any alphabetic letter
ANY_LETTER_REGEX = re.compile(r'[a-zA-ZÀ-ỹ]')

# Non-Latin script detection (Chinese, Japanese, Cyrillic, Arabic, Korean, Thai)
NON_LATIN_SCRIPT_REGEX = re.compile(
    r'[\u4e00-\u9fff\u3040-\u30ff\u0400-\u04ff\u0600-\u06ff\uac00-\ud7af\u0e00-\u0e7f]'
)


def is_vietnamese_text(text: str) -> bool:
    """
    Checks if a comment is likely Vietnamese.
    - True if it contains Vietnamese diacritics, or
    - True if it contains common unaccented Vietnamese words, or
    - False if predominantly non-Latin scripts (Chinese/Russian/Arabic) or foreign text.
    """
    if not text:
        return False
        
    # If it contains significant foreign scripts
    if NON_LATIN_SCRIPT_REGEX.search(text):
        # If no Vietnamese diacritics at all and contains non-latin, classify as non-Vietnamese
        if not any(c in VIETNAMESE_CHARS for c in text):
            return False

    # Check 1: Vietnamese accented characters
    if any(c in VIETNAMESE_CHARS for c in text):
        return True
        
    # Check 2: Unaccented Vietnamese words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return False
        
    vn_word_matches = sum(1 for w in words if w in COMMON_VIETNAMESE_WORDS)
    
    # If at least 15% of words or 2 words match common Vietnamese vocabulary
    if len(words) <= 3 and vn_word_matches >= 1:
        return True
    if len(words) > 3 and (vn_word_matches >= 2 or (vn_word_matches / len(words)) >= 0.15):
        return True
        
    # Short tech-related comments like "ok", "good", "ip11", "note 20"
    tech_terms = {"ok", "nice", "good", "pro", "max", "ultra", "iphone", "samsung", "xiaomi", "redmi", "note"}
    if any(w in tech_terms for w in words):
        return True

    return False


def detect_spam(text: str) -> Dict[str, Any]:
    """
    Evaluates whether a comment is spam based on rules.
    Prioritizes High Precision to avoid filtering genuine negative feedback.
    
    Returns:
        {
            "is_spam": bool,
            "spam_reasons": List[str],
            "is_vietnamese": bool
        }
    """
    reasons: List[str] = []
    
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "is_spam": True,
            "spam_reasons": ["empty_text"],
            "is_vietnamese": False
        }

    clean_str = text.strip()

    # Rule 1: No letters at all (only symbols/digits/emojis like "...", "12345", "???")
    if not ANY_LETTER_REGEX.search(clean_str):
        reasons.append("no_alphabetical_content")

    # Rule 2: External Links / URLs
    if URL_REGEX.search(clean_str):
        reasons.append("contains_url")

    # Rule 3: Phone number pattern
    if PHONE_REGEX.search(clean_str):
        reasons.append("contains_phone_number")

    # Rule 4: Invitation to external platforms (Zalo, Telegram, Inbox...)
    if CONTACT_INVITE_REGEX.search(clean_str):
        reasons.append("external_contact_invite")

    # Rule 5: Commercial spam, gambling, coupon codes, seeding ads
    if COMMERCIAL_SPAM_REGEX.search(clean_str):
        reasons.append("commercial_or_gambling_spam")

    # Rule 6: Excessive character or word repetition (flooding)
    if REPETITIVE_CHAR_REGEX.search(clean_str):
        reasons.append("excessive_character_repetition")
    if REPETITIVE_WORD_REGEX.search(clean_str):
        reasons.append("repetitive_words")

    # Rule 7: Language check (spec: outside scope if non-Vietnamese)
    is_vn = is_vietnamese_text(clean_str)
    if not is_vn:
        reasons.append("non_vietnamese_language")

    is_spam = len(reasons) > 0

    return {
        "is_spam": is_spam,
        "spam_reasons": reasons,
        "is_vietnamese": is_vn
    }

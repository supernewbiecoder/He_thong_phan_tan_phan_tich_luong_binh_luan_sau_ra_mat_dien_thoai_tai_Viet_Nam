# -*- coding: utf-8 -*-
"""
Rule-based and Hybrid spam detection and language verification module.
Refined & Production-hardened by Nguyễn Lê Quân according to project specification:
- Binary label: is_spam (True / False)
- Binary label: is_vietnamese (True / False) - cleanly separated from is_spam
- Unicode Normalization: NFC enforcement to prevent decomposed diacritic mismatch
- Precision-first evaluation on imbalanced class
- Support for Ratings/Praise edge cases (e.g. '10/10', '100%', '+1')
- Hybrid ML extension support
"""
import re
import unicodedata
from typing import Dict, Any, List, Optional

try:
    from cleaner.config import (
        URL_REGEX,
        PHONE_REGEX,
        CONTACT_INVITE_REGEX,
        COMMERCIAL_SPAM_REGEX,
        REPETITIVE_CHAR_REGEX,
        REPETITIVE_WORD_REGEX,
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
        COMMON_VIETNAMESE_WORDS,
    )

# Regex to check if text contains any alphabetic letter (Latin or Vietnamese accented)
ANY_LETTER_REGEX = re.compile(r'[a-zA-ZÀ-ỹ]')

# Legitimate numerical ratings/enthusiastic expressions in tech reviews (e.g. 10/10, +1, 100%, 9.5/10)
RATING_EXPRESSION_REGEX = re.compile(
    r'^\s*(?:\+1|\d+(?:\.\d+)?\s*/\s*10|100%|\d+\s*(?:điểm|đ|sao))\s*$',
    re.IGNORECASE
)

# Pure emoji detection (not spam, but non-alphabetic)
EMOJI_PATTERN_REGEX = re.compile(
    r'^[\s\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]+$'
)

# Non-Latin script detection (Chinese, Japanese, Cyrillic, Arabic, Korean, Thai)
NON_LATIN_SCRIPT_REGEX = re.compile(
    r'[\u4e00-\u9fff\u3040-\u30ff\u0400-\u04ff\u0600-\u06ff\uac00-\ud7af\u0e00-\u0e7f]'
)

# Vietnamese accented characters (diacritics only, excluding plain ASCII Latin letters)
VIETNAMESE_DIACRITICS = set(
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    "ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ"
)

# Common smartphone model abbreviations frequently appearing in Vietnamese reviews
COMMON_TECH_ABBREVIATIONS = {
    "ip11", "ip12", "ip13", "ip14", "ip15", "ip16", "ip17", "ip18",
    "ip11prm", "ip12prm", "ip13prm", "ip14prm", "ip15prm", "ip16prm", "ip17prm", "ip18prm",
    "s20u", "s21u", "s22u", "s23u", "s24u", "s25u", "s26u",
    "mi12u", "mi13u", "mi14u", "mi15u", "fold", "flip"
}


def normalize_unicode(text: str) -> str:
    """
    Ensures text is normalized to Unicode NFC (composed) form.
    Prevents decomposed accents (NFD) from failing diacritic lookups.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def is_vietnamese_text(text: str) -> bool:
    """
    Checks if a comment is likely Vietnamese.
    - True if it contains Vietnamese diacritics, or
    - True if it contains common unaccented Vietnamese words, or
    - False if predominantly non-Latin scripts (Chinese/Russian/Arabic) or foreign text.
    """
    if not text:
        return False
        
    text = normalize_unicode(text).strip()
    if not text:
        return False

    # If it contains significant foreign scripts and no Vietnamese diacritics
    if NON_LATIN_SCRIPT_REGEX.search(text):
        if not any(c in VIETNAMESE_DIACRITICS for c in text):
            return False

    # Check 1: Vietnamese accented characters
    if any(c in VIETNAMESE_DIACRITICS for c in text):
        return True
        
    # Check 2: Unaccented Vietnamese words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        # If pure rating or emoji, consider in-context valid if no foreign indicators
        if RATING_EXPRESSION_REGEX.match(text):
            return True
        return False
        
    vn_word_matches = sum(1 for w in words if w in COMMON_VIETNAMESE_WORDS)
    
    # Short comments (<= 3 words) matching common VN vocabulary
    if len(words) <= 3 and vn_word_matches >= 1:
        return True
        
    # Longer comments require at least 2 common VN words and >= 25% of total words
    if len(words) > 3 and vn_word_matches >= 2 and (vn_word_matches / len(words)) >= 0.25:
        return True
        
    # Short tech-related abbreviations commonly used in VN forum posts
    if any(w in COMMON_TECH_ABBREVIATIONS for w in words):
        return True

    return False


def detect_spam(text: str, ml_model: Optional[Any] = None) -> Dict[str, Any]:
    """
    Evaluates whether a comment is spam based on Precision-First rules and optional ML inference.
    Properly separates 'is_vietnamese' from 'is_spam' according to project specifications.
    
    Args:
        text: Comment string.
        ml_model: Optional trained scikit-learn pipeline or HybridSpamDetector.
        
    Returns:
        {
            "is_spam": bool,
            "spam_reasons": List[str],
            "is_vietnamese": bool,
            "confidence": float
        }
    """
    reasons: List[str] = []
    
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "is_spam": True,
            "spam_reasons": ["empty_text"],
            "is_vietnamese": False,
            "confidence": 1.0
        }

    clean_str = normalize_unicode(text).strip()

    # Rule 1: No alphabetical letters (check if it's rating or emoji before flagging)
    if not ANY_LETTER_REGEX.search(clean_str):
        if RATING_EXPRESSION_REGEX.match(clean_str):
            # Legitimate rating (e.g. 10/10, +1)
            pass
        elif EMOJI_PATTERN_REGEX.match(clean_str):
            # Pure emoji: non-aspect bearing, but not fraudulent spam
            reasons.append("pure_emoji_no_text")
        else:
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

    # Rule 7: Language check (spec: outside scope if non-Vietnamese, but separated from is_spam)
    is_vn = is_vietnamese_text(clean_str)
    if not is_vn:
        reasons.append("non_vietnamese_language")

    # Hard fraud/ad/flooding patterns count towards is_spam
    actual_spam_reasons = [r for r in reasons if r not in ("non_vietnamese_language", "pure_emoji_no_text")]
    is_spam = len(actual_spam_reasons) > 0
    confidence = 1.0 if is_spam else 0.0

    # Optional ML model hook for nuanced cases if provided and no hard rule triggered
    if not is_spam and ml_model is not None and is_vn:
        try:
            if hasattr(ml_model, "predict_proba"):
                prob = ml_model.predict_proba([clean_str])[0][1]
                if prob > 0.65:
                    is_spam = True
                    reasons.append("ml_spam_classifier")
                    confidence = float(prob)
            elif hasattr(ml_model, "predict"):
                pred = ml_model.predict([clean_str])[0]
                if pred == 1:
                    is_spam = True
                    reasons.append("ml_spam_classifier")
                    confidence = 0.85
        except Exception:
            # Fallback defensively to rule results if ML fails
            pass

    return {
        "is_spam": is_spam,
        "spam_reasons": reasons,
        "is_vietnamese": is_vn,
        "confidence": confidence
    }

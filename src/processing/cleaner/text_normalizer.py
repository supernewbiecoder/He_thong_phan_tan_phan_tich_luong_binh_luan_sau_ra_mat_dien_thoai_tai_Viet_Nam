# -*- coding: utf-8 -*-
"""
Text normalization module for Vietnamese YouTube comments.
Performs:
- HTML entity unescaping
- Unicode NFC normalization
- Removal of invisible/control characters
- Character repetition compression (e.g. đẹp quáaaaa -> đẹp quá)
- Emoji spacing normalization (keeping emojis for sentiment analysis)
- Teencode / slang dictionary replacement
- Whitespace stripping and compression
- Detailed tracing of all changes made to the text
"""
import re
import html
import unicodedata
from typing import Dict, Any, Tuple, List
try:
    from cleaner.config import TEENCODE_DICT
except ImportError:
    from .config import TEENCODE_DICT

# Invisible and control character pattern
INVISIBLE_CHARS_REGEX = re.compile(r'[\u200b-\u200f\ufeff\u202a-\u202e\u2060\xa0]')
# HTML tags pattern
HTML_TAG_REGEX = re.compile(r'<[^>]+>')
# Character repetition pattern (3 or more identical characters -> 1 character, e.g. "đẹpppp" -> "đẹp")
REPEATED_CHARS_REGEX = re.compile(r'([a-zA-ZÀ-ỹ])\1{2,}', re.IGNORECASE)
# Emoji range regex pattern for spacing out emojis
EMOJI_REGEX = re.compile(
    r'([\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf])'
)

# Compile teencode pattern for fast lookup
sorted_teencode_keys = sorted(TEENCODE_DICT.keys(), key=lambda x: len(x), reverse=True)
teencode_pattern_str = r'(?<!\w)(' + '|'.join(re.escape(k) for k in sorted_teencode_keys) + r')(?!\w)'
TEENCODE_COMPILED_REGEX = re.compile(teencode_pattern_str, re.IGNORECASE)


def normalize_text(text: str, apply_teencode: bool = True) -> str:
    """
    Full text normalization pipeline for comment text.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 1. Unescape HTML entities
    text = html.unescape(text)
    
    # 2. Strip HTML tags
    text = HTML_TAG_REGEX.sub(" ", text)
    
    # 3. Unicode NFC Normalization
    text = unicodedata.normalize("NFC", text)
    
    # 4. Remove invisible characters
    text = INVISIBLE_CHARS_REGEX.sub(" ", text)
    
    # 5. Compress elongated characters
    text = REPEATED_CHARS_REGEX.sub(r'\1', text)
    
    # 6. Lowercase
    text = text.lower()
    
    # 7. Normalize spacing around emojis
    text = EMOJI_REGEX.sub(r' \1 ', text)
    
    # 8. Teencode replacement
    if apply_teencode:
        def replace_match(match):
            word = match.group(0).lower()
            return TEENCODE_DICT.get(word, word)
        text = TEENCODE_COMPILED_REGEX.sub(replace_match, text)
    
    # 9. Compress multiple whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_raw_text(text: str) -> str:
    """
    Light clean for raw text: strips HTML, normalizes Unicode NFC, removes control characters,
    preserving original case, punctuation, and wording.
    """
    if not text or not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = HTML_TAG_REGEX.sub(" ", text)
    text = unicodedata.normalize("NFC", text)
    text = INVISIBLE_CHARS_REGEX.sub(" ", text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def normalize_with_trace(text: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Normalizes text while tracking every specific change applied.
    
    Returns:
        Tuple of (cleaned_raw_text, text_norm, trace_details)
    """
    if not text or not isinstance(text, str):
        return "", "", {
            "was_modified": False,
            "changes_detected": [],
            "teencode_replacements": [],
            "repeated_chars_compressed": []
        }

    original = text
    changes = []
    
    # 1. Check HTML entities / tags
    unescaped = html.unescape(original)
    stripped_html = HTML_TAG_REGEX.sub(" ", unescaped)
    if stripped_html != original:
        changes.append("html_entities_or_tags_cleaned")
        
    # 2. Check Unicode NFC
    nfc_text = unicodedata.normalize("NFC", stripped_html)
    if nfc_text != stripped_html:
        changes.append("unicode_nfc_normalized")
        
    # 3. Check invisible characters
    visible_text = INVISIBLE_CHARS_REGEX.sub(" ", nfc_text)
    if visible_text != nfc_text:
        changes.append("invisible_characters_removed")
        
    cleaned_raw = re.sub(r'[ \t]+', ' ', visible_text)
    cleaned_raw = re.sub(r'\n{3,}', '\n\n', cleaned_raw).strip()
    
    # 4. Check repeated characters
    repeated_found = REPEATED_CHARS_REGEX.findall(cleaned_raw)
    compressed_text = REPEATED_CHARS_REGEX.sub(r'\1', cleaned_raw)
    if repeated_found:
        changes.append("repeated_characters_compressed")
        
    # 5. Lowercase
    lowered = compressed_text.lower()
    
    # 6. Check emojis
    emoji_spaced = EMOJI_REGEX.sub(r' \1 ', lowered)
    if emoji_spaced != lowered:
        changes.append("emoji_spacing_adjusted")
        
    # 7. Check teencode replacements
    teencode_replacements: List[Dict[str, str]] = []
    
    def trace_replace(match):
        w = match.group(0).lower()
        if w in TEENCODE_DICT:
            rep = TEENCODE_DICT[w]
            teencode_replacements.append({"original": w, "replacement": rep})
            return rep
        return w
        
    teencode_text = TEENCODE_COMPILED_REGEX.sub(trace_replace, emoji_spaced)
    if teencode_replacements:
        changes.append("teencode_replaced")
        
    # 8. Multiple spaces
    norm_text = re.sub(r'\s+', ' ', teencode_text).strip()
    if norm_text != teencode_text:
        changes.append("whitespace_collapsed")
        
    was_modified = (len(changes) > 0) or (norm_text != original)
    
    trace_details = {
        "was_modified": was_modified,
        "changes_count": len(changes),
        "changes_detected": changes,
        "teencode_replacements": teencode_replacements,
        "repeated_chars_compressed": list(set(repeated_found))
    }
    
    return cleaned_raw, norm_text, trace_details

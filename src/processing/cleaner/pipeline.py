# -*- coding: utf-8 -*-
"""
End-to-end data cleaning and integration pipeline with tracing support.
Processes a raw comment record, validates/normalizes schema,
populates text_norm, detects spam, extracts clauses, and records transformation trace.
"""
from typing import Dict, Any, Tuple

try:
    from cleaner.text_normalizer import normalize_with_trace
    from cleaner.clause_segmenter import split_into_clauses
    from cleaner.spam_detector import detect_spam
except ImportError:
    from .text_normalizer import normalize_with_trace
    from .clause_segmenter import split_into_clauses
    from .spam_detector import detect_spam


def process_comment_record(raw_record: Dict[str, Any], include_trace: bool = False) -> Any:
    """
    Cleans and enriches a single comment record, with optional change tracing.
    
    Args:
        raw_record: Dictionary representing raw comment from comments.jsonl.
        include_trace: If True, returns a tuple (clean_record, trace_record).
                       If False, returns clean_record.
                       
    Returns:
        clean_record or (clean_record, trace_record)
    """
    raw_text = raw_record.get("text", "") or ""
    
    # 1. Normalize text and capture detailed diff / trace
    cleaned_raw_text, text_norm, trace_details = normalize_with_trace(raw_text)
    
    # 2. Detect spam & verify language
    spam_info = detect_spam(cleaned_raw_text)
    is_spam = spam_info["is_spam"]
    spam_reasons = spam_info["spam_reasons"]
    is_vietnamese = spam_info["is_vietnamese"]
    
    # 3. Extract clauses if not spam (or extract anyway for completeness)
    if is_spam and ("empty_text" in spam_reasons or "no_alphabetical_content" in spam_reasons):
        clauses = []
    else:
        clauses = split_into_clauses(cleaned_raw_text)
        
    comment_id = str(raw_record.get("comment_id", "")).strip()
    model = str(raw_record.get("model", "")).strip()
    
    # 4. Build standardized clean record conforming to project schema
    clean_record = {
        "comment_id": comment_id,
        "video_id": str(raw_record.get("video_id", "")).strip(),
        "parent_id": raw_record.get("parent_id") if raw_record.get("parent_id") else None,
        "parent_text": raw_record.get("parent_text") if raw_record.get("parent_text") else None,
        "model": model,
        "source": str(raw_record.get("source", "youtube")).strip(),
        "text": cleaned_raw_text,
        "text_norm": text_norm,
        "author_hash": str(raw_record.get("author_hash", "")).strip(),
        "published_at": raw_record.get("published_at"),
        "like_count": int(raw_record.get("like_count", 0) or 0),
        "reply_count": int(raw_record.get("reply_count", 0) or 0),
        "fetched_at": raw_record.get("fetched_at"),
        "ingested_at": raw_record.get("ingested_at"),
        "is_spam": is_spam,
        "spam_reasons": spam_reasons,
        "is_vietnamese": is_vietnamese,
        "clause_count": len(clauses),
        "clauses": clauses,
        "schema_version": int(raw_record.get("schema_version", 2) or 2)
    }
    
    if not include_trace:
        return clean_record

    # 5. Build tracing record highlighting all before -> after differences
    overall_modified = trace_details["was_modified"] or is_spam or (raw_record.get("text_norm") != text_norm)

    trace_record = {
        "comment_id": comment_id,
        "model": model,
        "original_text": raw_text,
        "cleaned_text": cleaned_raw_text,
        "text_norm": text_norm,
        "was_modified": overall_modified,
        "changes_detected": trace_details["changes_detected"],
        "teencode_replacements": trace_details["teencode_replacements"],
        "repeated_chars_compressed": trace_details["repeated_chars_compressed"],
        "is_spam": is_spam,
        "spam_reasons": spam_reasons,
        "is_vietnamese": is_vietnamese,
        "clause_count": len(clauses),
        "clauses_summary": [c["text"] for c in clauses]
    }
    
    return clean_record, trace_record

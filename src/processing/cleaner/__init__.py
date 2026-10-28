# -*- coding: utf-8 -*-
try:
    from cleaner.config import TEENCODE_DICT, CLAUSE_CONJUNCTIONS, ASPECT_CATEGORIES
    from cleaner.text_normalizer import normalize_text, clean_raw_text, normalize_with_trace
    from cleaner.clause_segmenter import split_into_clauses
    from cleaner.spam_detector import detect_spam, is_vietnamese_text
    from cleaner.pipeline import process_comment_record
except ImportError:
    from .config import TEENCODE_DICT, CLAUSE_CONJUNCTIONS, ASPECT_CATEGORIES
    from .text_normalizer import normalize_text, clean_raw_text, normalize_with_trace
    from .clause_segmenter import split_into_clauses
    from .spam_detector import detect_spam, is_vietnamese_text
    from .pipeline import process_comment_record

__all__ = [
    "TEENCODE_DICT",
    "CLAUSE_CONJUNCTIONS",
    "ASPECT_CATEGORIES",
    "normalize_text",
    "clean_raw_text",
    "normalize_with_trace",
    "split_into_clauses",
    "detect_spam",
    "is_vietnamese_text",
    "process_comment_record",
]

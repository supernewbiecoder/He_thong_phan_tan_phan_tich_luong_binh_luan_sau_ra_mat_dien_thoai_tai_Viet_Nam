# -*- coding: utf-8 -*-
"""
Clause segmentation module according to project specifications.
Unit of analysis: Clause (Mệnh đề), split by punctuation marks (. , ! ? ; : newline)
and contrastive/coordinating conjunctions ("nhưng", "mà", "còn", "tuy", etc.).

Example: "pin trâu nhưng cam bệt" -> 
  - Clause 1: "pin trâu"
  - Clause 2: "cam bệt"
"""
import re
from typing import List, Dict, Any

try:
    from cleaner.config import CLAUSE_CONJUNCTIONS, PUNCT_SPLIT_REGEX
    from cleaner.text_normalizer import normalize_text
except ImportError:
    from .config import CLAUSE_CONJUNCTIONS, PUNCT_SPLIT_REGEX
    from .text_normalizer import normalize_text

# Regex to split on conjunctions when preceded and followed by word boundaries
sorted_conjs = sorted(CLAUSE_CONJUNCTIONS, key=lambda x: len(x), reverse=True)
CONJ_REGEX_STR = r'(?:(?<=[\s,\.!?;:])|(?<=^))(' + '|'.join(re.escape(c) for c in sorted_conjs) + r')(?:(?=[\s,\.!?;:])|(?=$))'
CONJ_SPLIT_REGEX = re.compile(CONJ_REGEX_STR, re.IGNORECASE)

# Pattern to clean up boundary punctuation and conjunction residue
STRIP_EDGE_REGEX = re.compile(r'^[\s\.,!?;:\-–—\(\)\[\]{}|"\'`]+|[\s\.,!?;:\-–—\(\)\[\]{}|"\'`]+$')
LEADING_CONJ_REGEX = re.compile(
    r'^(?:' + '|'.join(re.escape(c) for c in sorted_conjs) + r')\s+',
    re.IGNORECASE
)


def split_into_clauses(text: str) -> List[Dict[str, Any]]:
    """
    Splits a comment text into meaningful clauses based on punctuation and conjunctions.
    
    Args:
        text: Raw or lightly cleaned comment string.
        
    Returns:
        List of clause objects:
        [
            {
                "clause_id": 1,
                "text": "pin trâu",
                "text_norm": "pin trâu"
            },
            {
                "clause_id": 2,
                "text": "cam bệt",
                "text_norm": "camera bệt"
            }
        ]
    """
    if not text or not isinstance(text, str):
        return []

    # Step 1: Split into candidate chunks by major punctuation and newlines
    raw_chunks = PUNCT_SPLIT_REGEX.split(text)
    
    # Step 2: Split each chunk further by conjunctions
    all_clause_texts = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        
        # Split chunk by conjunction words
        sub_chunks = CONJ_SPLIT_REGEX.split(chunk)
        for sub in sub_chunks:
            sub = sub.strip()
            if not sub:
                continue
            # Check if this sub-chunk is just a conjunction word itself
            if sub.lower() in [c.lower() for c in CLAUSE_CONJUNCTIONS]:
                continue
            all_clause_texts.append(sub)

    # Step 3: Clean, strip edges, remove leading conjunction residue if still present
    cleaned_clauses = []
    clause_counter = 1
    
    for c_text in all_clause_texts:
        # Strip edge punctuation
        c_clean = STRIP_EDGE_REGEX.sub('', c_text).strip()
        # Strip leading conjunctions (e.g., "nhưng cam bệt" -> "cam bệt")
        c_clean = LEADING_CONJ_REGEX.sub('', c_clean).strip()
        c_clean = STRIP_EDGE_REGEX.sub('', c_clean).strip()
        
        # Filter out empty or trivially short snippets (< 2 characters)
        if len(c_clean) < 2:
            continue
            
        c_norm = normalize_text(c_clean, apply_teencode=True)
        if not c_norm or len(c_norm) < 2:
            continue
            
        cleaned_clauses.append({
            "clause_id": clause_counter,
            "text": c_clean,
            "text_norm": c_norm
        })
        clause_counter += 1

    # Fallback: if no valid clause was extracted but original text has content
    if not cleaned_clauses and text.strip():
        norm = normalize_text(text, apply_teencode=True)
        if norm:
            cleaned_clauses.append({
                "clause_id": 1,
                "text": text.strip(),
                "text_norm": norm
            })

    return cleaned_clauses

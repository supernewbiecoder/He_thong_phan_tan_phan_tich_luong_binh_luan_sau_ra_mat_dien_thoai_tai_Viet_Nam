"""Mục đích: Các mô hình ML ứng viên phát hiện spam (TF-IDF từ, ký tự, đặc trưng hình thức; Naive Bayes, Logistic Regression, SVM) để so với luật gắn cờ src/processing/flags.py (docs/4-mo-hinh/dac-ta-spam.md); cập nhật lần cuối: 2026-11-26.

Chuyển từ src/processing/spam/model.py (Công việc 11, 17/11); link và số điện thoại nhận bằng regex của tầng 2."""
import re
import unicodedata
from typing import Dict, List

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import MaxAbsScaler
from sklearn.svm import LinearSVC

from src.processing.normalize import PHONE_RE as PHONE_REGEX, URL_RE as URL_REGEX

_REPEAT = re.compile(r"(.)\1{3,}")
_SPACES = re.compile(r"\s+")
_HASHTAG = re.compile(r"#\w+")
_MENTION = re.compile(r"@\w+")
_LONG_REPEAT = re.compile(r"(\S)\1{5,}")

SEED = 42


def normalize_for_model(text: str) -> str:
    """Chuẩn hóa nhẹ trước khi vector hóa.

    Thay link và số điện thoại bằng token cố định để mô hình học "có link" thay vì
    học thuộc từng địa chỉ; rút chuỗi ký tự lặp về 3 ký tự.
    """
    text = unicodedata.normalize("NFC", text or "").lower()
    text = URL_REGEX.sub(" xxurl ", text)
    text = PHONE_REGEX.sub(" xxphone ", text)
    text = _REPEAT.sub(r"\1\1\1", text)
    return _SPACES.sub(" ", text).strip()


class MetaFeatures(BaseEstimator, TransformerMixin):
    """Đặc trưng hình thức của bình luận gốc (trước khi chuẩn hóa)."""

    names = ["log_len", "n_url", "has_phone", "digit_ratio", "upper_ratio", "long_repeat",
             "n_hashtag", "n_mention", "n_lines", "letter_ratio"]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for raw in X:
            text = unicodedata.normalize("NFC", raw or "")
            length = max(len(text), 1)
            rows.append([
                np.log1p(len(text)),
                len(URL_REGEX.findall(text)),
                1.0 if PHONE_REGEX.search(text) else 0.0,
                sum(ch.isdigit() for ch in text) / length,
                sum(ch.isupper() for ch in text) / length,
                1.0 if _LONG_REPEAT.search(text) else 0.0,
                len(_HASHTAG.findall(text)),
                len(_MENTION.findall(text)),
                text.count("\n") + 1,
                sum(ch.isalpha() for ch in text) / length,
            ])
        return np.asarray(rows, dtype=float)


def _word_tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(preprocessor=normalize_for_model, analyzer="word",
                           token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2), min_df=2,
                           sublinear_tf=True)


def _char_tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(preprocessor=normalize_for_model, analyzer="char_wb",
                           ngram_range=(2, 5), min_df=2, sublinear_tf=True)


def _union() -> FeatureUnion:
    return FeatureUnion([
        ("word", _word_tfidf()),
        ("char", _char_tfidf()),
        ("meta", Pipeline([("extract", MetaFeatures()), ("scale", MaxAbsScaler())])),
    ])


def _logreg() -> LogisticRegression:
    return LogisticRegression(C=10.0, class_weight="balanced", max_iter=2000, random_state=SEED)


def build_candidates() -> Dict[str, Pipeline]:
    """Các mô hình được so sánh bằng cross-validation trên tập train."""
    return {
        "nb-word": Pipeline([("features", _word_tfidf()), ("clf", ComplementNB(alpha=0.3))]),
        "lr-word": Pipeline([("features", _word_tfidf()), ("clf", _logreg())]),
        "lr-char": Pipeline([("features", _char_tfidf()), ("clf", _logreg())]),
        "lr-word+char+meta": Pipeline([("features", _union()), ("clf", _logreg())]),
        "svm-word+char+meta": Pipeline([
            ("features", _union()),
            ("clf", LinearSVC(C=1.0, class_weight="balanced", random_state=SEED)),
        ]),
    }


def scores(pipeline: Pipeline, texts: List[str]) -> np.ndarray:
    """Điểm spam liên tục (càng cao càng giống spam), dùng để chọn ngưỡng."""
    if hasattr(pipeline, "predict_proba"):
        return pipeline.predict_proba(texts)[:, 1]
    return pipeline.decision_function(texts)

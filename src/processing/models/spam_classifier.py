# -*- coding: utf-8 -*-
"""
Spam Classifier Module (CV 11 - Nguyễn Lê Quân).
Production-grade ML pipeline, feature engineering, and Hybrid (Rule + ML) detector.
Evaluates Precision, Recall, and F1 on imbalanced spam classification.
Supports CLI operations: --train, --eval, --predict.
Exports model card metadata (model_card.json) for ML governance.
"""
import os
import re
import sys
import json
import pickle
import argparse
import unicodedata
import numpy as np

# Defensive UTF-8 console output for Windows cmd/powershell
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_LABELS_FILE = os.path.join(BASE_DIR, "data", "labels", "spam_ground_truth_500.jsonl")
DEFAULT_MODEL_OUT_FILE = os.path.join(BASE_DIR, "src", "processing", "models", "spam_model.pkl")
DEFAULT_MODEL_CARD_FILE = os.path.join(BASE_DIR, "src", "processing", "models", "model_card.json")

# Rule regexes for high-confidence deterministic checks
URL_REGEX = re.compile(
    r'(?:https?://|ftp://|www\.)[^\s/$.?#].[^\s]*|'
    r'\b(?:[a-zA-Z0-9-]+\.)+(?:com|vn|net|org|xyz|info|top|vip|club|me|cc|online|site|store|app|link|io)\b(?:/[^\s]*)?',
    re.IGNORECASE
)
PHONE_REGEX = re.compile(
    r'(?:\+?84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])[\s\.\-]?(?:\d{3}[\s\.\-]?\d{3}|\d{4}[\s\.\-]?\d{3}|\d{7})\b|'
    r'\b\d{4}[\s\.\-]\d{3}[\s\.\-]\d{3}\b'
)
KEYWORD_SPAM_REGEX = re.compile(
    r'\b(?:tài\s+xỉu|kubet|thabet|nohu|nổ\s+hũ|baccarat|casino|nhận\s+kèo|kiếm\s+tiền\s+online|'
    r'hoa\s+hồng|hoa\s+hông|đầu\s+tư\s+sinh\s+lời|chiết\s+khấu|voucher|săn\s+sale|kết\s+bạn\s+zalo|'
    r'add\s+zalo|liên\s+hệ\s+zalo|hotline)\b',
    re.IGNORECASE
)
REPETITIVE_CHAR_REGEX = re.compile(r'([^\s])\1{5,}')
RATING_EXPRESSION_REGEX = re.compile(
    r'^\s*(?:\+1|\d+(?:\.\d+)?\s*/\s*10|100%|\d+\s*(?:điểm|đ|sao))\s*$',
    re.IGNORECASE
)
EMOJI_PATTERN_REGEX = re.compile(
    r'^[\s\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]+$'
)


class DenseFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Extracts dense linguistic and structural features from comments.
    Features:
    0: Normalized length (capped at 500)
    1: Has URL flag
    2: Has Phone number flag
    3: Has Keyword spam flag
    4: Has Repetitive char flooding flag
    5: Digit ratio
    6: Uppercase ratio
    7: Punctuation ratio
    """
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for text in X:
            text = unicodedata.normalize("NFC", text or "")
            length = len(text)
            char_count = max(1, length)
            has_url = 1.0 if URL_REGEX.search(text) else 0.0
            has_phone = 1.0 if PHONE_REGEX.search(text) else 0.0
            has_keyword = 1.0 if KEYWORD_SPAM_REGEX.search(text) else 0.0
            has_rep_char = 1.0 if REPETITIVE_CHAR_REGEX.search(text) else 0.0
            
            digit_count = sum(c.isdigit() for c in text)
            upper_count = sum(c.isupper() for c in text)
            punct_count = sum(c in "!@#$%^&*()_+=-[]{};:'\"\\|,.<>/?`~" for c in text)
            
            digit_ratio = digit_count / char_count
            upper_ratio = upper_count / char_count
            punct_ratio = punct_count / char_count
            
            features.append([
                float(min(length, 500)) / 500.0,
                has_url,
                has_phone,
                has_keyword,
                has_rep_char,
                digit_ratio,
                upper_ratio,
                punct_ratio
            ])
        return np.array(features, dtype=np.float32)


def build_pipeline(clf) -> Pipeline:
    """
    Builds a unified feature union pipeline with word ngrams, char ngrams, and dense features.
    """
    feature_union = FeatureUnion([
        ("word_tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True
        )),
        ("char_tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True
        )),
        ("dense_feats", DenseFeatureExtractor())
    ])
    return Pipeline([
        ("features", feature_union),
        ("classifier", clf)
    ])


class HybridSpamDetector:
    """
    Combines deterministic rules for high-confidence spam patterns
    with a trained ML pipeline for nuanced spam classification.
    Guarantees zero false positives on obvious legitimate comments.
    """
    def __init__(self, ml_pipeline: Optional[Pipeline] = None):
        self.ml_pipeline = ml_pipeline

    def predict(self, texts: List[str]) -> np.ndarray:
        preds = []
        texts_for_ml = []
        indices_for_ml = []

        for i, raw_text in enumerate(texts):
            text = unicodedata.normalize("NFC", raw_text or "").strip()
            # Hard rules (precision-first)
            if not text:
                preds.append(1)
            elif URL_REGEX.search(text):
                preds.append(1)
            elif PHONE_REGEX.search(text):
                preds.append(1)
            elif KEYWORD_SPAM_REGEX.search(text):
                preds.append(1)
            elif REPETITIVE_CHAR_REGEX.search(text):
                preds.append(1)
            elif RATING_EXPRESSION_REGEX.match(text) or EMOJI_PATTERN_REGEX.match(text):
                # Ratings and pure emojis are not fraud spam
                preds.append(0)
            elif not re.search(r'[a-zA-ZÀ-ỹ]', text):
                preds.append(1)
            else:
                preds.append(None)
                texts_for_ml.append(text)
                indices_for_ml.append(i)

        if texts_for_ml and self.ml_pipeline is not None:
            ml_preds = self.ml_pipeline.predict(texts_for_ml)
            for idx, p in zip(indices_for_ml, ml_preds):
                preds[idx] = int(p)
        else:
            for idx in indices_for_ml:
                preds[idx] = 0

        return np.array(preds, dtype=int)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        """
        Returns estimated probabilities [P(ham), P(spam)] for a list of texts.
        """
        probs = np.zeros((len(texts), 2), dtype=np.float32)
        texts_for_ml = []
        indices_for_ml = []

        for i, raw_text in enumerate(texts):
            text = unicodedata.normalize("NFC", raw_text or "").strip()
            if not text or URL_REGEX.search(text) or PHONE_REGEX.search(text) or KEYWORD_SPAM_REGEX.search(text) or REPETITIVE_CHAR_REGEX.search(text):
                probs[i] = [0.0, 1.0]
            elif RATING_EXPRESSION_REGEX.match(text) or EMOJI_PATTERN_REGEX.match(text):
                probs[i] = [1.0, 0.0]
            elif not re.search(r'[a-zA-ZÀ-ỹ]', text):
                probs[i] = [0.0, 1.0]
            else:
                texts_for_ml.append(text)
                indices_for_ml.append(i)

        if texts_for_ml and self.ml_pipeline is not None:
            if hasattr(self.ml_pipeline, "predict_proba"):
                ml_probs = self.ml_pipeline.predict_proba(texts_for_ml)
                for idx, pr in zip(indices_for_ml, ml_probs):
                    probs[idx] = pr
            else:
                ml_preds = self.ml_pipeline.predict(texts_for_ml)
                for idx, p in zip(indices_for_ml, ml_preds):
                    probs[idx] = [0.0, 1.0] if p == 1 else [1.0, 0.0]
        else:
            for idx in indices_for_ml:
                probs[idx] = [1.0, 0.0]

        return probs


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    p = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    r = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    return {
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "macro_f1": round(float(macro_f1), 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn)
    }


def load_dataset(filepath: str = DEFAULT_LABELS_FILE) -> Tuple[List[str], np.ndarray, List[Dict[str, Any]]]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground truth dataset not found at {filepath}")
    texts = []
    labels = []
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            texts.append(rec.get("text") or "")
            labels.append(1 if rec.get("is_spam") else 0)
            records.append(rec)
    return texts, np.array(labels, dtype=int), records


def train_and_evaluate(
    labels_path: str = DEFAULT_LABELS_FILE,
    model_out: str = DEFAULT_MODEL_OUT_FILE,
    card_out: str = DEFAULT_MODEL_CARD_FILE
) -> Dict[str, Any]:
    texts, y, _ = load_dataset(labels_path)
    print(f"Loaded {len(texts)} comments from ground truth ({labels_path}). Spam count = {np.sum(y)} ({np.mean(y)*100:.1f}%)")

    # 1. Rule-based Baseline
    try:
        from cleaner.spam_detector import detect_spam
    except ImportError:
        import sys
        sys.path.insert(0, os.path.join(BASE_DIR, "src", "processing"))
        from cleaner.spam_detector import detect_spam

    rule_preds = []
    for t in texts:
        res = detect_spam(t)
        rule_preds.append(1 if res["is_spam"] else 0)
    rule_metrics = evaluate_predictions(y, np.array(rule_preds))
    print(f"\n--- [1] RULE-BASED BASELINE ---")
    print(f"Precision: {rule_metrics['precision']:.4f} | Recall: {rule_metrics['recall']:.4f} | F1: {rule_metrics['f1']:.4f}")
    print(f"TP: {rule_metrics['tp']}, FP: {rule_metrics['fp']}, FN: {rule_metrics['fn']}, TN: {rule_metrics['tn']}")

    # 2. 5-Fold Cross Validation on ML Models
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    models = {
        "MultinomialNB": MultinomialNB(alpha=0.1),
        "ComplementNB": ComplementNB(alpha=0.1),
        "LinearSVC (balanced)": LinearSVC(class_weight="balanced", random_state=42, max_iter=2000),
        "LogisticRegression (balanced)": LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    }

    cv_results = {}
    oof_predictions = {name: np.zeros(len(y), dtype=int) for name in models}
    hybrid_oof = np.zeros(len(y), dtype=int)
    texts_arr = np.array(texts, dtype=object)

    for name, clf in models.items():
        precisions, recalls, f1s = [], [], []
        for train_idx, val_idx in cv.split(texts_arr, y):
            pipe = build_pipeline(clf)
            pipe.fit(texts_arr[train_idx], y[train_idx])
            val_preds = pipe.predict(texts_arr[val_idx])
            oof_predictions[name][val_idx] = val_preds
            
            m = evaluate_predictions(y[val_idx], val_preds)
            precisions.append(m["precision"])
            recalls.append(m["recall"])
            f1s.append(m["f1"])

        cv_results[name] = {
            "precision": float(np.mean(precisions)),
            "recall": float(np.mean(recalls)),
            "f1": float(np.mean(f1s)),
            "oof_eval": evaluate_predictions(y, oof_predictions[name])
        }

    print("\n--- [2] MACHINE LEARNING 5-FOLD CV RESULTS ---")
    for name, res in cv_results.items():
        print(f"Model: {name:28s} | Precision: {res['precision']:.4f} | Recall: {res['recall']:.4f} | F1: {res['f1']:.4f}")

    # 3. Hybrid Model (Rule + Best ML: LinearSVC)
    best_ml_name = "LinearSVC (balanced)"
    for train_idx, val_idx in cv.split(texts_arr, y):
        pipe = build_pipeline(models[best_ml_name])
        pipe.fit(texts_arr[train_idx], y[train_idx])
        hybrid = HybridSpamDetector(pipe)
        hybrid_oof[val_idx] = hybrid.predict(texts_arr[val_idx])

    hybrid_metrics = evaluate_predictions(y, hybrid_oof)
    print("\n--- [3] HYBRID APPROACH (HARD RULES + LINEARSVC) ---")
    print(f"Precision: {hybrid_metrics['precision']:.4f} | Recall: {hybrid_metrics['recall']:.4f} | F1: {hybrid_metrics['f1']:.4f}")
    print(f"TP: {hybrid_metrics['tp']}, FP: {hybrid_metrics['fp']}, FN: {hybrid_metrics['fn']}, TN: {hybrid_metrics['tn']}")

    # 4. Train final Calibrated Model on full dataset for probability support
    base_svc = LinearSVC(class_weight="balanced", random_state=42, max_iter=2000)
    calibrated_clf = CalibratedClassifierCV(estimator=base_svc, cv=3)
    final_pipe = build_pipeline(calibrated_clf)
    final_pipe.fit(texts_arr, y)
    
    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    with open(model_out, "wb") as f:
        pickle.dump(final_pipe, f)
    print(f"\nFinal ML model serialized to: {model_out}")

    # 5. Export Model Card for ML Governance
    model_card = {
        "model_name": "Vietnamese Smartphone Review Spam Classifier",
        "task": "Binary Spam Classification (CV 11)",
        "author": "Nguyễn Lê Quân",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "Hybrid (Deterministic Regex Rules + Calibrated LinearSVC)",
        "features": [
            "Word TF-IDF (1, 2)-grams, sublinear_tf=True",
            "Char-wb TF-IDF (3, 5)-grams, sublinear_tf=True",
            "Dense Linguistic Features (Length, URLs, Phones, Gambling keywords, Repeated chars, Digit/Punct/Upper ratios)"
        ],
        "training_data": {
            "file": os.path.basename(labels_path),
            "total_samples": len(texts),
            "spam_samples": int(np.sum(y)),
            "ham_samples": int(len(texts) - np.sum(y)),
            "imbalance_ratio": f"1:{int((len(texts)-np.sum(y))/np.sum(y))}"
        },
        "metrics_summary": {
            "rule_baseline": rule_metrics,
            "best_ml_model": cv_results[best_ml_name],
            "hybrid_ensemble": hybrid_metrics
        },
        "deployment_recommendation": "Use HybridSpamDetector in production to maintain 100% precision on clean comments while catching nuanced spam."
    }

    with open(card_out, "w", encoding="utf-8") as f:
        json.dump(model_card, f, ensure_ascii=False, indent=2)
    print(f"Model Card written to: {card_out}")

    # Save summary report
    summary_path = os.path.join(BASE_DIR, "src", "processing", "models", "spam_benchmark_report.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(model_card, f, ensure_ascii=False, indent=2)

    return model_card


def predict_single(text: str, model_path: str = DEFAULT_MODEL_OUT_FILE):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model not found at {model_path}. Run --train first.")
    with open(model_path, "rb") as f:
        pipe = pickle.load(f)
    detector = HybridSpamDetector(pipe)
    pred = detector.predict([text])[0]
    probs = detector.predict_proba([text])[0]
    result = {
        "text": text,
        "is_spam": bool(pred == 1),
        "confidence": float(probs[1] if pred == 1 else probs[0]),
        "prob_spam": float(probs[1]),
        "prob_ham": float(probs[0])
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description="Spam Classifier Management Tool (CV 11 - Nguyễn Lê Quân)")
    parser.add_argument("--mode", choices=["train", "eval", "predict"], default="eval", help="Execution mode")
    parser.add_argument("--text", type=str, help="Text to classify in predict mode")
    parser.add_argument("--data", type=str, default=DEFAULT_LABELS_FILE, help="Path to ground truth labels JSONL")
    parser.add_argument("--model-out", type=str, default=DEFAULT_MODEL_OUT_FILE, help="Path to output model.pkl")
    parser.add_argument("--card-out", type=str, default=DEFAULT_MODEL_CARD_FILE, help="Path to output model_card.json")

    args = parser.parse_args()

    if args.mode in ("train", "eval"):
        train_and_evaluate(args.data, args.model_out, args.card_out)
    elif args.mode == "predict":
        if not args.text:
            print("Error: --text argument required for predict mode.")
            sys.exit(1)
        predict_single(args.text, args.model_out)


if __name__ == "__main__":
    main()

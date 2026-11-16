"""Áp dụng phương án đã chọn lên bình luận: spam và ngôn ngữ là hai kết quả riêng.

Ba chế độ:
  hybrid  rule-v0 (nội dung + hình thức) gắn cờ VÀ mô hình ML xác nhận  [mặc định]
  ml      chỉ mô hình ML
  rule    rule-v0 nguyên trạng, để đối chiếu

Chạy cho cả file:
  python -m src.processing.spam.predict --input data/clean_data.jsonl --output data/spam_predictions.jsonl
"""
import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import joblib

from . import config
from .baseline import CONTENT_REASONS, FORM_REASONS, rule_reasons
from .language import detect_language
from .model import scores

GATE_REASONS = CONTENT_REASONS | FORM_REASONS
MODES = ("hybrid", "ml", "rule")


class SpamDetector:
    def __init__(self, bundle: Dict[str, object], mode: str = "hybrid"):
        if mode not in MODES:
            raise ValueError(f"mode phải là một trong {MODES}")
        self.pipeline = bundle["pipeline"]
        self.threshold = bundle["threshold_hybrid"] if mode == "hybrid" else bundle["threshold_ml"]
        self.mode = mode
        self.model_version = (config.RULE_VERSION if mode == "rule"
                              else f"{bundle['model_version']}-{mode}")

    @classmethod
    def load(cls, path: Path = config.MODEL_PATH, mode: str = "hybrid") -> "SpamDetector":
        if not Path(path).exists():
            raise FileNotFoundError(
                f"Chưa có mô hình tại {path}. Tạo bằng: python -m src.processing.spam.train")
        return cls(joblib.load(path), mode)

    def predict(self, texts: Iterable[str]) -> List[Dict[str, object]]:
        texts = [text or "" for text in texts]
        if not texts:
            return []
        reasons = [rule_reasons(text) for text in texts]
        score = scores(self.pipeline, texts)
        results = []
        for text, text_reasons, text_score in zip(texts, reasons, score):
            gate = sorted(set(text_reasons) & GATE_REASONS)
            if self.mode == "rule":
                is_spam = bool(text_reasons)
            elif self.mode == "ml":
                is_spam = bool(text_score >= self.threshold)
            else:
                is_spam = bool(gate) and bool(text_score >= self.threshold)
            language = detect_language(text)
            results.append({
                "is_spam": is_spam,
                "spam_score": round(float(text_score), 4),
                # Lý do của luật chỉ là giải thích kèm theo, không còn quyết định một mình.
                "spam_reasons": (sorted(text_reasons) if self.mode == "rule" else gate) if is_spam else [],
                "lang": language,
                "is_vietnamese": language == "vi",
                "label_source": "rule" if self.mode == "rule" else "model",
                "model_version": self.model_version,
            })
        return results


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--input", default=str(config.CLEAN_DATA_PATH))
    parser.add_argument("--output", default=str(config.REPO_ROOT / "data" / "spam_predictions.jsonl"))
    parser.add_argument("--mode", choices=MODES, default="hybrid")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()

    detector = SpamDetector.load(mode=args.mode)
    counts = collections.Counter()
    batch: List[dict] = []

    def flush(handle) -> None:
        for comment, result in zip(batch, detector.predict(c["text"] for c in batch)):
            handle.write(json.dumps({"comment_id": comment["comment_id"], **result},
                                    ensure_ascii=False) + "\n")
            counts["total"] += 1
            counts["spam"] += result["is_spam"]
            counts[f"lang_{result['lang']}"] += 1
        batch.clear()

    with open(args.input, encoding="utf-8") as source, \
            open(args.output, "w", encoding="utf-8") as target:
        for line in source:
            if line.strip():
                batch.append(json.loads(line))
            if len(batch) >= args.batch_size:
                flush(target)
        flush(target)

    total = counts["total"] or 1
    print(f"Đã ghi {counts['total']:,} dòng vào {args.output} (chế độ {args.mode}, {detector.model_version})")
    print(f"  spam: {counts['spam']:,} ({counts['spam'] / total:.2%})")
    for language in ("vi", "other", "none"):
        print(f"  lang = {language}: {counts[f'lang_{language}']:,} ({counts[f'lang_{language}'] / total:.2%})")


if __name__ == "__main__":
    main()

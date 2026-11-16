"""Sinh SỐ LIỆU MINH HỌA để chạy thử dashboard khi chưa có đầu ra của mô hình thật.

Nhãn ở đây do vài luật từ khóa thô gán (`label_source = "rule"`,
`model_version = "rule-v0-demo"`). Chúng KHÔNG phải kết quả phân tích: máy được
nhắc lấy luôn là máy của video, cảm xúc đoán theo từ khóa, `author_is_creator`
luôn là false vì dữ liệu sạch chưa có trường này. Dashboard tự gắn nhãn "số liệu
minh họa" cho mọi phiên bản có `label_source = rule`.

  python -m src.serving.demo_data            # ghi data/demo/aspect_mentions.jsonl và aggregates.jsonl

Khi Công việc 8–10 và 12 có đầu ra thật thì không dùng file này nữa; nạp thẳng
đầu ra đó bằng src/serving/load_db.py.
"""
import argparse
import collections
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from .api.settings import REPO_ROOT
from .load_db import AGGREGATE_KEY, aggregate_id, catalog_from_config, read_jsonl

MODEL_VERSION = "rule-v0-demo"
VN_OFFSET = timedelta(hours=7)
WINDOW_DAYS = 28

ASPECT_KEYWORDS = {
    "BATTERY": r"pin|sạc|mah|tụt pin|hao pin",
    "DISPLAY": r"màn hình|màn|hz|amoled|oled|độ sáng|tần số quét",
    "PERFORMANCE": r"chip|hiệu năng|lag|giật|mượt|nóng|snap|exynos|chơi game|fps|ram",
    "CAMERA": r"camera|cam|chụp|quay|zoom|selfie|ảnh",
    "DESIGN": r"thiết kế|đẹp|xấu|mỏng|nặng|nhẹ|viền|màu sắc|cầm|ngoại hình",
    "SOFTWARE": r"phần mềm|ios|android|one ui|miui|cập nhật|update|giao diện|tính năng",
    "HARDWARE_OTHER": r"loa|vân tay|face id|sóng|wifi|bộ nhớ|bút|s pen|rung",
    "PRICE": r"giá|tiền|đắt|rẻ|triệu|củ|đáng tiền",
    "WARRANTY": r"bảo hành|chính hãng|xách tay|sửa chữa|đổi trả",
}
ASPECT_PATTERNS = {aspect: re.compile(rf"(?<!\w)(?:{words})(?!\w)") for aspect, words in ASPECT_KEYWORDS.items()}
POSITIVE = re.compile(r"(?<!\w)(?:tốt|đẹp|ngon|mượt|trâu|đỉnh|thích|xịn|ổn|sạc nhanh|rẻ|đáng tiền|tuyệt|ok|hay)(?!\w)")
NEGATIVE = re.compile(r"(?<!\w)(?:tệ|xấu|lag|giật|nóng|chán|đắt|kém|yếu|lỗi|tụt|hao|chậm|thất vọng|dở|chát)(?!\w)")
NEGATION = re.compile(r"(?<!\w)(?:không|ko|chẳng|chả|chưa|đâu có)\s+(?:hề\s+|bị\s+)?$")
OWNER = re.compile(r"(?<!\w)(?:mình|tôi|em|tui|tớ)\s+(?:đang\s+|đã\s+|mới\s+)?(?:dùng|xài|mua|cầm|sắm)|máy (?:mình|tôi|em)(?!\w)")
COMPARATIVE = re.compile(r"(?<!\w)(?:hơn|thua|kém|ăn đứt|ngang|bằng)(?!\w)")
DEFECT_RULES = (
    ("BATTERY", r"tụt|hao|nhanh hết", "BATTERY_DRAIN"), ("PERFORMANCE", r"nóng", "OVERHEAT"),
    ("PERFORMANCE", r"lag|giật|đơ", "LAG"), ("DISPLAY", r"sọc|ám|lỗi|chết điểm", "DISPLAY_DEFECT"),
    ("CAMERA", r"lỗi|mờ|rung", "CAMERA_DEFECT"), ("SOFTWARE", r"lỗi|bug|văng", "SOFTWARE_BUG"),
    ("HARDWARE_OTHER", r"sóng|wifi|mất kết nối", "CONNECTIVITY"), ("HARDWARE_OTHER", r"lỗi|hỏng|rè", "HARDWARE_DEFECT"),
)


def sentiment_of(text: str) -> str:
    """Đoán cảm xúc theo từ khóa; từ phủ định đứng ngay trước thì đảo chiều."""
    score = 0
    for pattern, sign in ((POSITIVE, 1), (NEGATIVE, -1)):
        for match in pattern.finditer(text):
            score += -sign if NEGATION.search(text[:match.start()]) else sign
    return "pos" if score > 0 else "neg" if score < 0 else "neu"


def days_since_launch(published_at: str, launch: date) -> int:
    published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    return ((published + VN_OFFSET).date() - launch).days


def build_mentions(comments, catalog: List[dict]) -> Iterator[dict]:
    launches = {m["model_id"]: date.fromisoformat(m["launch_date"]) for m in catalog if m.get("launch_date")}
    aliases = sorted(((alias.lower(), m["model_id"]) for m in catalog
                      for alias in [*m.get("aliases", []), m["title"]] if len(alias) >= 6),
                     key=lambda pair: -len(pair[0]))
    for comment in comments:
        if comment.get("is_spam") or not comment.get("is_vietnamese"):
            continue
        video_model = comment.get("model") or ""
        target = video_model if video_model in launches else None  # video nhiều máy: không xác định
        for index, clause in enumerate(comment.get("clauses") or []):
            text = clause.get("text") or ""
            lowered = text.lower()
            if not lowered.strip():
                continue
            sentiment = sentiment_of(lowered)
            owner = True if OWNER.search(lowered) else None
            compare_with = None
            if target and COMPARATIVE.search(lowered):
                compare_with = next((model_id for alias, model_id in aliases
                                     if model_id != target and alias in lowered), None)
            winner = None
            if compare_with:
                winner = {"pos": "target", "neg": "other", "neu": "tie"}[sentiment]
            for aspect, pattern in ASPECT_PATTERNS.items():
                hits = len(pattern.findall(lowered))
                if not hits:
                    continue
                defect = None
                if sentiment == "neg" and owner:
                    defect = next((code for rule_aspect, words, code in DEFECT_RULES
                                   if rule_aspect == aspect and re.search(words, lowered)), None)
                yield {
                    "mention_id": f"{comment['comment_id']}#{index}#{aspect}",
                    "comment_id": comment["comment_id"], "parent_id": comment.get("parent_id"),
                    "clause_idx": index, "clause_text": text, "source": comment.get("source") or "youtube",
                    "video_id": comment["video_id"], "video_model": video_model, "target_model": target,
                    "author_hash": comment["author_hash"], "author_is_creator": False,
                    "aspect": aspect, "sentiment": sentiment,
                    "confidence": round(min(0.9, 0.4 + 0.1 * hits + (0.2 if sentiment != "neu" else 0)), 2),
                    "is_owner": owner, "defect_type": defect,
                    "compare_with": compare_with, "compare_winner": winner,
                    "published_at": comment["published_at"],
                    "days_since_launch": (days_since_launch(comment["published_at"], launches[target])
                                          if target else None),
                    "label_source": "rule", "model_version": MODEL_VERSION, "schema_version": 2,
                }


def build_aggregates(mentions, updated_at: str) -> List[dict]:
    """Số đếm theo docs/data-model.md mục 5: bỏ chủ kênh, chỉ lấy 4 tuần đầu, không lưu %."""
    groups: Dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    for mention in mentions:
        days = mention["days_since_launch"]
        if mention["target_model"] is None or mention["author_is_creator"] or not 0 <= days < WINDOW_DAYS:
            continue
        key = (mention["target_model"], mention["aspect"], days // 7 + 1, mention["video_id"],
               mention["source"], mention["model_version"])
        groups[key][mention["sentiment"]] += 1
    rows = []
    for key in sorted(groups):
        row = dict(zip(AGGREGATE_KEY, key))
        counts = groups[key]
        row.update({"n_pos": counts["pos"], "n_neg": counts["neg"], "n_neu": counts["neu"],
                    "n_total": sum(counts.values()), "updated_at": updated_at})
        row["agg_id"] = aggregate_id(row)
        rows.append(row)
    return rows


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Sinh số liệu minh họa cho dashboard")
    parser.add_argument("--comments", type=Path, default=REPO_ROOT / "data" / "clean_data.jsonl")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "pipeline.yaml")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "demo")
    args = parser.parse_args()

    catalog = catalog_from_config(args.config)
    mentions = list(build_mentions(read_jsonl(args.comments), catalog))
    aggregates = build_aggregates(mentions, datetime.now(timezone.utc).isoformat())
    args.out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("aspect_mentions.jsonl", mentions), ("aggregates.jsonl", aggregates)):
        with open(args.out / name, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with_target = sum(1 for m in mentions if m["target_model"])
    print(f"SỐ LIỆU MINH HỌA ({MODEL_VERSION}): {len(mentions):,} mention "
          f"({with_target:,} xác định được máy), {len(aggregates):,} dòng aggregates -> {args.out}")


if __name__ == "__main__":
    main()

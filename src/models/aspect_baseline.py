import re
from typing import Dict, List
import unicodedata

# 9 khía cạnh chuẩn theo contracts/aspect-mention.schema.json (schema_version = 2)
ASPECT_LABELS = [
    "BATTERY",
    "DISPLAY",
    "PERFORMANCE",
    "CAMERA",
    "DESIGN",
    "SOFTWARE",
    "HARDWARE_OTHER",
    "PRICE",
    "WARRANTY",
]

# Bộ luật từ khóa gốc từ eda_smartphone_comments.ipynb đã map sang 9 mã chuẩn
BASELINE_RULES_ASCII = {
    "BATTERY": r"\b(?:pin|sac|mah|sac nhanh)\b",
    "DISPLAY": r"\b(?:man hinh|oled|amoled|hz|do sang|tan so quet)\b",
    "PERFORMANCE": (
        r"\b(?:chip|snapdragon|exynos|bionic|muot|lag|giat|hieu"
        r" nang|game|fps|ram|cau hinh)\b"
    ),
    "CAMERA": r"\b(?:camera|cam|chup|selfie|quay phim|quay video|zoom)\b",
    "DESIGN": r"\b(?:dep|thiet ke|khung|vien|chat lieu|titan)\b",
    "SOFTWARE": (
        r"\b(?:ios|android|update|cap nhat|one ui|hyperos|miui|phan mem)\b"
    ),
    "HARDWARE_OTHER": r"\b(?:nong|tan nhiet|nhiet)\b",
    "PRICE": r"\b(?:gia|tien|trieu|re|dat|giam gia|dang tien)\b",
    "WARRANTY": (
        r"\b(?:bao hanh|chinh hang|tgdd|the gioi di dong|fpt|cellphones|hoang"
        r" ha|vn/a|quoc te|xach tay)\b"
    ),
}


def strip_accents_str(s: str) -> str:
  """Hàm bỏ dấu tiếng Việt và chuyển về chữ thường (lấy từ cell-02 của notebook EDA)."""
  if not isinstance(s, str):
    return ""
  norm = unicodedata.normalize("NFD", s.lower())
  clean = "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
  return clean.replace("đ", "d")


class RuleBasedAspectBaseline:
  """Mô hình Baseline dự đoán khía cạnh bằng bộ luật từ khóa (rule-v0)."""

  def __init__(self, model_version: str = "rule-v0"):
    self.model_version = model_version
    self.compiled_rules = {
        aspect: re.compile(pattern)
        for aspect, pattern in BASELINE_RULES_ASCII.items()
    }

  def predict_aspects_list(self, clause_texts: List[str]) -> List[List[str]]:
    """Dùng khi chấm điểm F1 với MultiLabelBinarizer trên tập test.

    Trả về danh sách các mã khía cạnh cho từng mệnh đề (vd: [["BATTERY",
    "PRICE"], []]).
    """
    predictions = []
    for text in clause_texts:
      text_ascii = strip_accents_str(text)
      matched = [
          aspect
          for aspect, regex in self.compiled_rules.items()
          if regex.search(text_ascii)
      ]
      predictions.append(matched)
    return predictions

  def predict_mentions(self, clause_text: str) -> List[Dict]:
    """Dùng khi xuất dữ liệu theo đúng chuẩn contracts/aspect-mention.schema.json."""
    text_ascii = strip_accents_str(clause_text)
    results = []
    for aspect, regex in self.compiled_rules.items():
      if regex.search(text_ascii):
        results.append({
            "aspect": aspect,
            "confidence": 1.0,
            "label_source": "rule",
            "model_version": self.model_version,
        })
    return results
"""Mục đích: Cấu hình của API dashboard: biến môi trường (cùng tên với src/storage), tên khía cạnh lấy từ bộ nhãn chốt, ngưỡng "ít dữ liệu" (docs/7-hien-thi/huong-dan.md); cập nhật lần cuối: 2026-11-26."""
import os
from dataclasses import dataclass
from pathlib import Path

from src.labeling.final_labels import ASPECTS as FINAL_ASPECTS, NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]
DASHBOARD_DIR = REPO_ROOT / "src" / "serving" / "dashboard"

# 11 khía cạnh của bộ nhãn chốt, theo thứ tự hiển thị (src/labeling/final_labels.py)
ASPECTS = {aspect: NAMES[aspect] for aspect in FINAL_ASPECTS}
# Nhãn từ các nguồn này chưa qua mô hình đã đánh giá: số liệu chỉ để minh họa.
UNVERIFIED_LABEL_SOURCES = {"rule": "Nhãn sinh từ luật từ khóa, chưa qua mô hình đã đánh giá",
                            "llm": "Nhãn do AI gán, chưa có người duyệt",
                            "unknown": "Có mention không ghi nguồn nhãn"}


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "smartphone_analytics"
    window_weeks: int = 4          # khớp window_weeks trong config/pipeline.yaml
    min_opinionated: int = 30      # muc-tieu.md mục 6: khen + chê < 30 thì "ít dữ liệu"
    timezone_offset_hours: int = 7  # giờ Việt Nam, dùng cho phân bố theo giờ
    cache_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mongo_uri=os.getenv("MONGO_URI", cls.mongo_uri),
            mongo_db=os.getenv("MONGO_DB", cls.mongo_db),
            window_weeks=int(os.getenv("WINDOW_WEEKS", cls.window_weeks)),
            min_opinionated=int(os.getenv("MIN_OPINIONATED", cls.min_opinionated)),
        )

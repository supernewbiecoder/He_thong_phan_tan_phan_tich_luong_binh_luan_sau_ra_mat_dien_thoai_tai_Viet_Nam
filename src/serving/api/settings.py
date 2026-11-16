"""Cấu hình của API, đọc từ biến môi trường (cùng tên với src/storage của Công việc 3)."""
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DASHBOARD_DIR = REPO_ROOT / "src" / "serving" / "dashboard"

ASPECTS = {
    "BATTERY": "Pin & sạc",
    "DISPLAY": "Màn hình",
    "PERFORMANCE": "Hiệu năng",
    "CAMERA": "Camera",
    "DESIGN": "Thiết kế & độ bền",
    "SOFTWARE": "Phần mềm",
    "HARDWARE_OTHER": "Phần cứng khác",
    "PRICE": "Giá",
    "WARRANTY": "Bảo hành & hậu mãi",
}
DEFECT_TYPES = {
    "BATTERY_DRAIN": "Hao pin",
    "OVERHEAT": "Nóng máy",
    "LAG": "Giật, lag",
    "DISPLAY_DEFECT": "Lỗi màn hình",
    "CAMERA_DEFECT": "Lỗi camera",
    "SOFTWARE_BUG": "Lỗi phần mềm",
    "CONNECTIVITY": "Lỗi kết nối",
    "HARDWARE_DEFECT": "Lỗi phần cứng",
    "OTHER": "Lỗi khác",
}
# Nhãn từ các nguồn này chưa qua mô hình đã đánh giá: số liệu chỉ để minh họa.
UNVERIFIED_LABEL_SOURCES = {"rule": "Nhãn sinh từ luật từ khóa, chưa qua mô hình đã đánh giá",
                            "llm": "Nhãn do AI gán, chưa có người duyệt"}


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "smartphone_analytics"
    window_weeks: int = 4          # khớp window_weeks trong config/pipeline.yaml
    min_opinionated: int = 30      # EDA_requirement 1.5: pos + neg < 30 thì "ít dữ liệu"
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

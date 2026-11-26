"""Mục đích: Luật mốc cho hai trường của Q5: người viết đã dùng máy chưa (`is_owner`) và loại lỗi (`defect_type`), dùng ở bước suy luận theo bình luận (docs/4-mo-hinh/dac-ta-suy-luan.md mục 6); cập nhật lần cuối: 2026-11-20.

Chỉ là mốc, chưa đo trên nhãn người. Không thấy dấu hiệu thì trả None (không biết), không trả False: không có từ
khóa không chứng minh người viết chưa dùng máy, và không có từ lỗi không chứng minh lời chê không phải lỗi.
"""

from __future__ import annotations

import re

# Chạy trên text_norm (chữ thường, viết tắt đã mở: "mik" → "mình")
DA_DUNG_RE = re.compile(
    r"(?<!\w)(?:"
    r"(?:mình|tôi|tui|em|tớ)\s+(?:đang\s+|đã\s+|mới\s+|vừa\s+)?(?:dùng|xài|sài|mua|lên đời)"   # không gồm "anh": thường là gọi người làm video
    r"|đang (?:dùng|xài|sài)|đã mua|mới mua|vừa mua|mua được|mới bóc hộp|vừa bóc hộp|đã trải nghiệm"
    r"|(?:dùng|xài|sài) được \d+ (?:ngày|tuần|tháng|năm)"
    r"|máy (?:mình|tôi|tui|em|tao)"
    r")(?!\w)"
)

# (khía cạnh, regex trên text_norm của mệnh đề chê, loại lỗi); khớp dòng đầu tiên thì dừng
LUAT_LOI = (
    ("BATTERY", r"hao|tụt|chai|sụt|hẻo|hết nhanh|nhanh hết", "BATTERY_DRAIN"),
    ("PERFORMANCE", r"nóng|quá nhiệt|nhiệt độ", "OVERHEAT"),
    ("PERFORMANCE", r"lag|giật|khựng|đơ|treo|chậm", "LAG"),
    ("DISPLAY", r"sọc|ám|điểm chết|chết điểm|lỗi màn|burn|bóng mờ|nhấp nháy|loang", "DISPLAY_DEFECT"),
    ("CAMERA", r"lỗi|hỏng|không lấy nét|văng|đơ", "CAMERA_DEFECT"),
    ("SOFTWARE", r"lỗi|bug|văng|crash|đơ|treo|tự khởi động", "SOFTWARE_BUG"),
    ("HARDWARE_OTHER", r"mất sóng|yếu sóng|sóng yếu|rớt mạng|mất kết nối|wifi|bluetooth|gps", "CONNECTIVITY"),
    ("HARDWARE_OTHER", r"hỏng|lỗi|liệt|kẹt|rè", "HARDWARE_DEFECT"),
)
_LUAT_LOI = tuple((kc, re.compile(rf"(?<!\w)(?:{mau})(?!\w)"), loai) for kc, mau, loai in LUAT_LOI)


def da_dung_may(text_norm: str) -> bool | None:
    """True nếu bình luận có dấu hiệu người viết đã dùng máy; None nếu không thấy (không biết)."""
    return True if text_norm and DA_DUNG_RE.search(text_norm.lower()) else None


def loai_loi(khia_canh: str, text_norm: str) -> str | None:
    """Mã `defect_type` cho một lời chê về `khia_canh`, hoặc None nếu không có từ chỉ lỗi cụ thể."""
    s = (text_norm or "").lower()
    for kc, mau, loai in _LUAT_LOI:
        if kc == khia_canh and mau.search(s):
            return loai
    return None

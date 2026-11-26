"""Mục đích: Luật mốc cho chiều 5 (đã dùng máy, trường `is_owner`) của Q5, dùng ở bước suy luận theo bình luận (docs/4-mo-hinh/dac-ta-suy-luan.md mục 6); cập nhật lần cuối: 2026-11-26.

Chỉ là mốc, chưa đo trên nhãn người. Không thấy dấu hiệu thì trả None (`khong_ro`), không trả False: không có từ
khóa không chứng minh người viết chưa dùng máy. Loại lỗi (`defect_type`) không còn luật: bộ loại lỗi cũ đã bỏ cùng
9 khía cạnh cũ, bộ mới chờ kế hoạch tổng thể bước 2.6, nên contract v3 luôn ghi null.
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


def da_dung_may(text_norm: str) -> bool | None:
    """True nếu bình luận có dấu hiệu người viết đã dùng máy; None nếu không thấy (không biết)."""
    return True if text_norm and DA_DUNG_RE.search(text_norm.lower()) else None


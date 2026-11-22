"""Mục đích: Tầng 2 – tiền xử lý bình luận: làm sạch (clean.py), chuẩn hóa (normalize.py), tách mệnh đề (clauses.py), gắn cờ tiếng Việt và spam (flags.py), lệnh chạy cả file (run.py). Đặc tả: docs/2-tien-xu-ly/dac-ta.md; cập nhật lần cuối: 2026-11-20.

Dùng trong code khác:
    from src.processing import lam_sach, chuan_hoa, tach_menh_de, gan_co
    text_clean = lam_sach(text)
    text_norm = chuan_hoa(text_clean)
    clauses = tach_menh_de(text_clean)
    co = gan_co(text_clean)   # {"is_vietnamese", "is_spam", "spam_reasons"}
"""

from .clauses import tach_menh_de
from .clean import lam_sach
from .flags import gan_co
from .normalize import chuan_hoa, chuan_hoa_tung_buoc, tach_emoji, tach_tu

# Đổi code hay từ điển làm thay đổi kết quả thì tăng số sau dấu chấm (1.0 → 1.1); đổi trường đầu ra hay thứ tự
# bước thì tăng số trước dấu chấm (1.x → 2.0). Rồi ghi một dòng vào bảng phiên bản ở docs/2-tien-xu-ly/dac-ta.md mục 6.
PIPELINE_VERSION = "processing-2.0"

__all__ = ["PIPELINE_VERSION", "lam_sach", "chuan_hoa", "chuan_hoa_tung_buoc", "tach_emoji", "tach_tu", "tach_menh_de",
           "gan_co"]

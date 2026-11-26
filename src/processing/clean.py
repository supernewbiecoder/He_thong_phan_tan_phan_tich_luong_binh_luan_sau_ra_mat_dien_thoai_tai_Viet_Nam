"""Mục đích: Bước 2.1 – làm sạch kỹ thuật văn bản bình luận (bước B1–B7 trong docs/2-tien-xu-ly/dac-ta-lam-sach.md); cập nhật lần cuối: 2026-11-19.

Chỉ sửa phần "kỹ thuật" của chuỗi, không đổi chữ: giải mã HTML entity, bỏ ký tự điều khiển và ký tự vô hình,
đưa Unicode về NFC, chuẩn xuống dòng và khoảng trắng. Kết quả là cột `text_clean`.
Notebook notebooks/2_1_clean.ipynb gọi lại đúng các hàm này để xem từng bước trước → sau.
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata

# ---------------------------------------------------------------- B1, B7. Bình luận rỗng


def la_rong(s) -> bool:
    """B1/B7: rỗng khi không phải chuỗi (null, NaN) hoặc chỉ có khoảng trắng."""
    return not isinstance(s, str) or s.strip() == ""


# ---------------------------------------------------------------- B2. HTML entity

ENTITY_RE = re.compile(r"&(?:#\d{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")


def giai_ma_html(s: str) -> str:
    """B2: đổi HTML entity (&amp; &#39; &quot;…) về ký tự thật; lặp tới khi không còn gì để đổi (tối đa 3 lần)."""
    for _ in range(3):
        moi = ENTITY_RE.sub(lambda m: html.unescape(m.group(0)), s)
        if moi == s:
            break
        s = moi
    return s


# ---------------------------------------------------------------- B3. Ký tự điều khiển, ký tự vô hình

GIU_CHO_BUOC_SAU = {"\t", "\n", "\r", "\x0b", "\x0c", "\x85"}   # khoảng trắng và xuống dòng: B5, B6 xử lý
ZWJ = "‍"                                                  # ký tự nối emoji ghép (👨‍👩‍👧)


def _can_bo(cp: int) -> bool:
    ch = chr(cp)
    if ch in GIU_CHO_BUOC_SAU or ch == ZWJ or 0xE0020 <= cp <= 0xE007F:   # E0020–E007F: ký tự tag của cờ 🏴
        return False
    return unicodedata.category(ch) in ("Cc", "Cf", "Cs")


def _tao_regex_ky_tu_bo() -> re.Pattern:
    """Gom mọi mã cần bỏ thành các khoảng liên tiếp, tạo một regex [ ... ] (chạy một lần lúc import, ~1 giây)."""
    khoang: list[list[int]] = []
    for cp in range(sys.maxunicode + 1):
        if _can_bo(cp):
            if khoang and cp == khoang[-1][1] + 1:
                khoang[-1][1] = cp
            else:
                khoang.append([cp, cp])

    def ma(cp: int) -> str:
        return f"\\U{cp:08X}"

    return re.compile("[" + "".join(ma(a) if a == b else f"{ma(a)}-{ma(b)}" for a, b in khoang) + "]")


KY_TU_BO_RE = _tao_regex_ky_tu_bo()


def _la_emoji(ch: str) -> bool:
    """Ký tự có thể đứng hai bên ZWJ trong emoji ghép: biểu tượng (So), màu da (Sk), emoji mới chưa có tên (Cn), U+FE0F."""
    return unicodedata.category(ch) in ("So", "Sk", "Cn") or ch == "️"


def _xu_ly_zwj(s: str) -> str:
    """Giữ ZWJ nằm giữa hai emoji, bỏ ZWJ ở mọi chỗ khác."""
    def thay(m: re.Match) -> str:
        i = m.start()
        truoc = s[i - 1] if i > 0 else ""
        sau = s[i + 1] if i + 1 < len(s) else ""
        return ZWJ if truoc and sau and _la_emoji(truoc) and _la_emoji(sau) else ""
    return re.sub(ZWJ, thay, s)


def bo_ky_tu_dieu_khien(s: str) -> str:
    """B3: bỏ ký tự điều khiển (Cc), định dạng vô hình (Cf: zero-width, BOM, đổi chiều chữ), surrogate lẻ (Cs).

    Giữ lại: tab và xuống dòng (B5, B6 xử lý), ZWJ nằm giữa hai emoji, ký tự tag của cờ.
    """
    s = KY_TU_BO_RE.sub("", s)
    if ZWJ in s:
        s = _xu_ly_zwj(s)
    return s


# ---------------------------------------------------------------- B4. Unicode NFC


def chuan_unicode(s: str) -> str:
    """B4: đưa chữ có dấu về dạng dựng sẵn (NFC), vd "e" + dấu mũ + dấu sắc thành "ế"."""
    return unicodedata.normalize("NFC", s)


# ---------------------------------------------------------------- B5. Xuống dòng

KIEU_XUONG_DONG_RE = re.compile(r"\r\n|[\r\x85]")
NHIEU_DONG_TRONG_RE = re.compile(r"\n(?:[^\S\n]*\n)+")   # \n + (các dòng trống / chỉ có khoảng trắng) + \n


def chuan_xuong_dong(s: str) -> str:
    """B5: các kiểu xuống dòng \\r\\n, \\r, U+0085 thành \\n; nhiều dòng trống liền nhau thành một \\n.

    U+2028, U+2029 không đổi ở đây: chúng là khoảng trắng nên B6 đổi thành dấu cách.
    """
    s = KIEU_XUONG_DONG_RE.sub("\n", s)
    return NHIEU_DONG_TRONG_RE.sub("\n", s)


# ---------------------------------------------------------------- B6. Khoảng trắng

KHOANG_TRANG_RE = re.compile(r"[^\S\n]+")   # mọi khoảng trắng trừ \n: dấu cách, tab, NBSP, U+3000...
CACH_QUANH_XUONG_DONG_RE = re.compile(r" ?\n ?")


def chuan_khoang_trang(s: str) -> str:
    """B6: gộp khoảng trắng thành một dấu cách, bỏ dấu cách quanh xuống dòng và ở hai đầu."""
    s = KHOANG_TRANG_RE.sub(" ", s)
    s = CACH_QUANH_XUONG_DONG_RE.sub("\n", s)
    return s.strip()


# ---------------------------------------------------------------- Cả Level 1

CAC_BUOC = [   # (mã, tên, hàm) theo đúng thứ tự chạy
    ("B2", "HTML entities", giai_ma_html),
    ("B3", "Ký tự điều khiển, ký tự vô hình", bo_ky_tu_dieu_khien),
    ("B4", "Unicode NFC", chuan_unicode),
    ("B5", "Xuống dòng", chuan_xuong_dong),
    ("B6", "Khoảng trắng", chuan_khoang_trang),
]


def lam_sach(s) -> str:
    """Chạy B1–B7: trả "" nếu bình luận rỗng (trước hoặc sau làm sạch), ngược lại trả `text_clean`."""
    if la_rong(s):
        return ""
    for _, _, ham in CAC_BUOC:
        s = ham(s)
    return s

"""Mục đích: Làm sạch nhẹ chữ bình luận để hiển thị trên phiếu và cho HAC đọc, không đổi chữ; che tên người dùng được nhắc dạng @tên và +Tên Họ trên những gì ghi ra cho người đọc (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 2, 3.1); cập nhật lần cuối: 2026-11-23."""

from __future__ import annotations

import html
import re
import unicodedata

NOI_EMOJI = "‍"   # ký tự nối emoji (ZWJ): giữ để emoji ghép không bị tách
NHAC_TEN = re.compile(r"(?<!\w)@[\w.\-]+(?:@[\w.\-]+)*")   # @tên (YouTube tự chèn khi reply), cả chuỗi @a@b dính liền
NHAC_TEN_CU = re.compile(r"(?<!\S)\+(\w+(?: \w+){0,3})")   # +Tên Họ: kiểu nhắc tên thời YouTube gắn Google+; lấy tối đa 4 chữ để xét
CHE_TEN = "@[người dùng]"


def lam_sach_nhe(text: str | None) -> str:
    """Giải HTML entity, chuẩn NFC, bỏ ký tự điều khiển và vô hình (trừ xuống dòng, ZWJ), gộp khoảng trắng."""
    if not text:
        return ""
    s = unicodedata.normalize("NFC", html.unescape(text))
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = "".join(c for c in s if c == "\n" or c == NOI_EMOJI or unicodedata.category(c) not in ("Cc", "Cf"))
    s = re.sub(r"[^\S\n]+", " ", s)          # mọi khoảng trắng trừ xuống dòng → một dấu cách
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _che_ten_cu(m: re.Match) -> str:
    """Che dấu + cùng các chữ viết hoa chữ cái đầu liền sau; trả lại các chữ còn lại. Chữ đầu không viết hoa ('+1') thì giữ nguyên."""
    chu = m.group(1).split(" ")
    k = 0
    while k < len(chu) and chu[k][:1].isupper():
        k += 1
    return m.group(0) if k == 0 else " ".join([CHE_TEN] + chu[k:])


def an_nhac_ten(text: str | None) -> str:
    """Thay tên người dùng được nhắc bằng CHE_TEN: dạng @tên, và dạng +Tên Họ (tối đa 4 chữ viết hoa liền sau dấu +).
    Tên viết không có @ hay + thì không che được."""
    return NHAC_TEN_CU.sub(_che_ten_cu, NHAC_TEN.sub(CHE_TEN, text or ""))

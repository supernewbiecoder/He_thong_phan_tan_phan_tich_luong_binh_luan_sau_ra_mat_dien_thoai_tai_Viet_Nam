"""Mục đích: Bước 2.4 – gắn cờ `is_vietnamese`, `is_spam`, `spam_reasons` cho từng bình luận bằng luật (docs/2-tien-xu-ly/dac-ta-gan-co.md); cập nhật lần cuối: 2026-11-20.

Đây là luật mốc, chưa đo độ chính xác: Công việc 11 gán tay ~500 bình luận để đo và thay bằng phương án tốt hơn.
Hai cờ tách riêng: bình luận tiếng nước ngoài không bị tính là spam, và ngược lại.
"""

from __future__ import annotations

import re
import unicodedata

from .normalize import PHONE_RE, doc_tu_dien, tach_tu

# ---------------------------------------------------------------- tiếng Việt

CHU_VIET = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")   # chữ có dấu, không có trong ASCII

# Một âm tiết tiếng Việt gõ không dấu: phụ âm đầu (có thể không có) + 1–3 nguyên âm + phụ âm cuối (có thể không có)
AM_TIET_RE = re.compile(r"(?:ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnprstvx])?[aeiouy]{1,3}(?:ch|ng|nh|[cmnpt])?")

# Từ mượn, tên hãng hay gặp trong bình luận điện thoại tiếng Việt: không dùng để kết luận là tiếng gì
TU_TRUNG_TINH = frozenset("""
    iphone ip samsung galaxy ultra pro max plus mini prm xiaomi redmi poco oppo vivo realme pixel google apple
    android ios oneui hyperos camera video clip review unbox unboxing youtube youtuber game chip snapdragon exynos
    dimensity bionic ram rom gb tb mah hz fps ok oke okay wow like sub wifi bluetooth nfc face id app update sale
    zoom selfie tele macro flagship test check link shop team fan fans tiktok facebook fb ytb ai
""".split())

NGUONG_AM_TIET = 0.5   # dưới tỷ lệ này (trên ít nhất 2 chữ đếm được) thì coi là tiếng nước ngoài

# Lý do của kết quả nhận tiếng Việt (ghi vào manifest để đếm)
CO_DAU, KHONG_DAU, KHONG_DU_CHU, CHU_KHAC_LATIN, NGOAI_NGU = (
    "co_dau_tieng_viet", "khong_dau_hop_le", "khong_du_chu", "chu_khac_latin", "khong_dau_ngoai_ngu")


def _la_chu_latin(c: str) -> bool:
    return "LATIN" in unicodedata.name(c, "")


def nhan_tieng_viet(text_clean: str) -> tuple[bool, str]:
    """Trả (is_vietnamese, lý do). Chỉ trả False khi có dấu hiệu là tiếng nước ngoài.

    Bình luận rỗng, chỉ có emoji, hay chỉ có tên máy không đủ chữ để kết luận: tính là tiếng Việt, vì dữ liệu lấy từ
    kênh tiếng Việt và các bình luận này không tạo mention nào.
    """
    chu = [t.lower() for t in tach_tu(text_clean or "") if not t.startswith("<")]
    ky_tu = [c for t in chu for c in t if c.isalpha()]
    if any(c in CHU_VIET for c in ky_tu):
        return True, CO_DAU
    if any(not _la_chu_latin(c) for c in ky_tu):
        return False, CHU_KHAC_LATIN
    viet_tat = doc_tu_dien()
    dem_duoc = [t for t in chu if t.isalpha() and t not in TU_TRUNG_TINH]
    if len(dem_duoc) < 2:
        return True, KHONG_DU_CHU
    hop_le = sum(1 for t in dem_duoc if t in viet_tat or AM_TIET_RE.fullmatch(t))
    if hop_le / len(dem_duoc) < NGUONG_AM_TIET:
        return False, NGOAI_NGU
    return True, KHONG_DAU


def la_tieng_viet(text_clean: str) -> bool:
    return nhan_tieng_viet(text_clean)[0]


# ---------------------------------------------------------------- spam

LIEN_KET, SO_DIEN_THOAI, MOI_LIEN_HE, CO_BAC_LUA_DAO = "lien_ket", "so_dien_thoai", "moi_lien_he", "co_bac_lua_dao"

# Link có http(s):// hoặc www., hoặc link rút gọn. Tên miền trần như "tgdd.vn" không tính: thường là nhắc tên cửa hàng.
LIEN_KET_RE = re.compile(
    r"(?:https?://|www\.)\S+"
    r"|(?<![\w.])(?:bit\.ly|tinyurl\.com|cutt\.ly|rb\.gy|t\.me|zalo\.me|shope\.ee|shp\.ee|s\.shopee\.vn|linktr\.ee)(?:/\S*)?",
    re.IGNORECASE,
)
MOI_LIEN_HE_RE = re.compile(
    r"(?<!\w)(?:"
    r"(?:qua|add|kết bạn|ket ban|kb|liên hệ|lien he|lh|ib|inbox)\s+(?:zalo|tele|telegram|fb|face)"
    r"|zalo\s*[:.]?\s*\+?\d+"
    r"|telegram|hotline"
    r"|(?:ib|inbox)\s+(?:cho|mình|mik|em|shop|ngay|riêng|rieng)"
    r")(?!\w)",
    re.IGNORECASE,
)
CO_BAC_LUA_DAO_RE = re.compile(
    r"(?<!\w)(?:"
    r"tài xỉu|tai xiu|kubet|thabet|nohu|nổ hũ|no hu|baccarat|casino|nhà cái|nha cai|cá cược|ca cuoc|nhận kèo|soi kèo"
    r"|kiếm tiền online|kiem tien online|kiếm tiền tại nhà|việc làm tại nhà|việc nhẹ lương cao|đầu tư sinh lời"
    r"|hoa hồng cao|vay tiền nhanh|app vay"
    r")(?!\w)",
    re.IGNORECASE,
)

LUAT_SPAM = (   # (lý do, regex), theo thứ tự ghi vào spam_reasons
    (LIEN_KET, LIEN_KET_RE),
    (SO_DIEN_THOAI, PHONE_RE),
    (MOI_LIEN_HE, MOI_LIEN_HE_RE),
    (CO_BAC_LUA_DAO, CO_BAC_LUA_DAO_RE),
)


def ly_do_spam(text_clean: str) -> list[str]:
    """Danh sách lý do spam theo thứ tự của LUAT_SPAM; rỗng nghĩa là không phải spam."""
    s = unicodedata.normalize("NFC", text_clean or "")
    return [ly_do for ly_do, mau in LUAT_SPAM if mau.search(s)]


def gan_co(text_clean: str) -> dict:
    """Ba trường của bước 2.4: {"is_vietnamese", "is_spam", "spam_reasons"}."""
    ly_do = ly_do_spam(text_clean)
    return {"is_vietnamese": la_tieng_viet(text_clean), "is_spam": bool(ly_do), "spam_reasons": ly_do}

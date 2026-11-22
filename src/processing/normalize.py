"""Mục đích: Bước 2.2 – chuẩn hóa ngôn ngữ cho bình luận đã làm sạch (bước N1–N7 trong docs/2-tien-xu-ly/dac-ta-chuan-hoa.md); cập nhật lần cuối: 2026-11-19.

Đầu vào là `text_clean`, đầu ra là `text_norm`, dùng để đếm từ, gán nhãn bằng máy, huấn luyện mô hình.
Không dùng `text_norm` để trích dẫn hay hiển thị cho người đọc: chuỗi đã viết thường, đã thay token, đã mở viết tắt.
Thứ tự các bước có chủ đích, xem đặc tả mục 4 trước khi đổi.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from .clean import chuan_khoang_trang

THU_MUC = Path(__file__).resolve().parent
TU_DIEN_VIET_TAT = THU_MUC / "resources" / "abbreviations.tsv"

KIEU_DAU = "cu"   # "cu": hòa, thủy, khỏe (dấu ở nguyên âm đầu); "moi": hoà, thuỷ, khoẻ. Chốt theo notebooks/2_2_normalize.ipynb mục 6.4.

CHU = r"[^\W\d_]"   # một chữ cái, ở mọi ngôn ngữ (không gồm chữ số và gạch dưới)

# ---------------------------------------------------------------- N1. Token

TOKEN_URL, TOKEN_EMAIL, TOKEN_PHONE, TOKEN_USER = "<url>", "<email>", "<phone>", "<user>"
CAC_TOKEN = (TOKEN_URL, TOKEN_EMAIL, TOKEN_PHONE, TOKEN_USER)

_TLD = "com|vn|net|org|io|me|ly|be|gl|ee|co|info|xyz|shop|store|app|link|top|vip|site|online|tv|cc|asia|biz"
EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.IGNORECASE)
URL_RE = re.compile(
    r"(?:https?://|www\.)\S+"                                                   # có http(s):// hoặc www.
    rf"|(?<![\w@.])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:{_TLD})\b(?:/\S*)?",  # tên miền trần: tgdd.vn, bit.ly/abc
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"(?<![\d+])(?:\+?84|0)[35789](?:[ .-]?\d){8}(?!\d)")   # số di động VN, có thể cách bằng . - hoặc dấu cách
USER_RE = re.compile(r"(?<![\w@])@\w[\w.\-]*")                                  # @handle của YouTube
DUOI_URL_RE = re.compile(r"[.,!?;:)\]}'\"”’]+$")                                 # dấu câu dính cuối URL, trả lại cho câu


def _thay_url(m: re.Match) -> str:
    duoi = DUOI_URL_RE.search(m.group(0))
    return TOKEN_URL + (duoi.group(0) if duoi else "")


def _thay_user(m: re.Match) -> str:
    ten = m.group(0)
    return TOKEN_USER + ten[len(ten.rstrip(".-")):]


def thay_token(s: str) -> str:
    """N1: email → <email>, URL → <url>, số điện thoại → <phone>, @tên → <user>.

    Chỉ bắt được @handle (không có dấu cách). Tên hiển thị có dấu cách kiểu "@Nguyễn Văn A" chỉ thay được chữ đầu.
    """
    s = EMAIL_RE.sub(TOKEN_EMAIL, s)
    s = URL_RE.sub(_thay_url, s)
    s = PHONE_RE.sub(TOKEN_PHONE, s)
    return USER_RE.sub(_thay_user, s)


# ---------------------------------------------------------------- N2. Chữ thường


def chu_thuong(s: str) -> str:
    """N2: viết thường toàn bộ (Đ → đ). Phân biệt "AI" với "ai" thì phải dùng `text_clean`."""
    return s.lower()


# ---------------------------------------------------------------- N3. Dấu thanh

DAU_THANH = "̣̀́̃̉"   # huyền, sắc, ngã, hỏi, nặng (dạng tổ hợp)
_O, _A, _E, _U, _Y = "oòóỏõọ", "aàáảãạ", "eèéẻẽẹ", "uùúủũụ", "yỳýỷỹỵ"
UNG_VIEN_DAU_RE = re.compile(rf"(?<!{CHU}){CHU}*(?:[{_O}][{_A}{_E}]|[{_U}][{_Y}])(?!{CHU})")
VAN_MO_RE = re.compile(r"(.*?)(oa|oe|uy)")


def _tach_dau(tu: str) -> tuple[str, list[str]]:
    """Trả (chữ đã bỏ dấu thanh, dạng NFC; danh sách dấu thanh có trong chữ)."""
    nfd = unicodedata.normalize("NFD", tu)
    dau = [c for c in nfd if c in DAU_THANH]
    return unicodedata.normalize("NFC", "".join(c for c in nfd if c not in DAU_THANH)), dau


def _van_doi_duoc(goc: str) -> re.Match | None:
    """Vần mở oa, oe, uy ở cuối chữ (không có phụ âm cuối), trừ "qu" + y (quý, quỳ: dấu luôn ở y)."""
    m = VAN_MO_RE.fullmatch(goc)
    if not m or (m.group(2) == "uy" and m.group(1).endswith("q")):
        return None
    return m


def dat_dau(tu: str, kieu: str = KIEU_DAU) -> str:
    """Đặt dấu thanh của một chữ (đã viết thường) theo kiểu cũ (hòa) hoặc kiểu mới (hoà). Chữ khác giữ nguyên."""
    goc, dau = _tach_dau(tu)
    m = _van_doi_duoc(goc) if len(dau) == 1 else None
    if not m:
        return tu
    i = len(m.group(1)) + (0 if kieu == "cu" else 1)
    return unicodedata.normalize("NFC", goc[:i + 1] + dau[0] + goc[i + 1:])


def kieu_dau_cua_tu(tu: str) -> str | None:
    """Cho EDA: "cu" nếu chữ đặt dấu kiểu cũ (hòa), "moi" nếu kiểu mới (hoà), None nếu chữ không thuộc diện này."""
    goc, dau = _tach_dau(tu)
    m = _van_doi_duoc(goc) if len(dau) == 1 else None
    if not m:
        return None
    vi_tri = next(i for i, ch in enumerate(tu) if any(c in DAU_THANH for c in unicodedata.normalize("NFD", ch)))
    dau_cap = len(m.group(1))
    return "cu" if vi_tri == dau_cap else "moi" if vi_tri == dau_cap + 1 else None


def chuan_dau_thanh(s: str, kieu: str = KIEU_DAU) -> str:
    """N3: chữ có vần mở oa, oe, uy được đặt dấu về một kiểu (mặc định kiểu cũ: hoà → hòa, thuỷ → thủy, khoẻ → khỏe)."""
    return UNG_VIEN_DAU_RE.sub(lambda m: dat_dau(m.group(0), kieu), s)


# ---------------------------------------------------------------- N4. Tiếng cười, emoticon, ký tự lặp

TIENG_CUOI = "haha"
CUOI_RE = re.compile(
    rf"(?<!{CHU})(?:k{{3,}}|h[ae]+(?:h+[ae]+)+h*|h[ij]+(?:h+[ij]+)+|k[ae]+(?:k+[ae]+)+)(?!{CHU})"
)   # kkk, haha, hahaaa, hehe, hihi, hjhj, kaka, keke (không gồm "huhu": tiếng khóc)
EMOTICON_RE = re.compile(r"(?<!\S)(?:[:;=x8]['^-]?[)(\]\[dpv3o/\\|*@]+|<3+|\^[_.\-]?\^+|[)(]{2,})(?!\S)")
LAP_TRONG_TU_RE = re.compile(rf"(?<!{CHU}){CHU}*({CHU})\1{{2,}}{CHU}*")   # chữ có ký tự lặp từ 3 lần
LAP_EMOTICON_RE = re.compile(r"(.)\1{2,}")
DAU_CAU_LAP_RE = re.compile(r"([!?,;~*])\1+")
BA_CHAM_RE = re.compile(r"(?:\.{2,}|…)+")


def _bo_dau_thanh_1_ky_tu(ch: str) -> str:
    return unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", ch) if c not in DAU_THANH))


def _rut_lap_trong_tu(m: re.Match) -> str:
    """Rút mọi đoạn từ 3 ký tự trở lên có cùng chữ gốc (bỏ dấu thanh) về 1 ký tự, ưu tiên ký tự mang dấu thanh.

    "quáaaaa" → "quá" (á và a cùng gốc a), "nhéeee" → "nhé", "đẹppp" → "đẹp".
    """
    tu = m.group(0)
    goc = [_bo_dau_thanh_1_ky_tu(ch) for ch in tu]
    if len(set(goc)) == 1:   # cả chữ chỉ là một ký tự lặp ("zzz", "aaaa"): giữ nguyên, rút thành 1 chữ sẽ bị đọc nhầm là viết tắt
        return tu
    ra, i = [], 0
    while i < len(tu):
        j = i
        while j < len(tu) and goc[j] == goc[i]:
            j += 1
        doan = tu[i:j]
        if j - i >= 3:
            doan = next((ch for ch in doan if ch != goc[i]), doan[0])   # ký tự có dấu thanh nếu có, không thì ký tự đầu
        ra.append(doan)
        i = j
    return "".join(ra)


def rut_gon_lap(s: str) -> str:
    """N4, theo thứ tự:
    1. tiếng cười (kkk, hahaha, hihi…) → "haha";
    2. emoticon đứng riêng (:)))))) rút còn tối đa 2 ký tự lặp (:)));
    3. chữ cái lặp từ 3 lần trong một chữ → 1 lần (đẹppppp → đẹp, quáaaa → quá);
    4. dấu câu lặp (!!!, ???) → 1; dấu chấm lửng (.., ...., …) → "...".
    """
    s = CUOI_RE.sub(TIENG_CUOI, s)
    s = EMOTICON_RE.sub(lambda m: LAP_EMOTICON_RE.sub(r"\1\1", m.group(0)), s)
    s = LAP_TRONG_TU_RE.sub(_rut_lap_trong_tu, s)
    s = DAU_CAU_LAP_RE.sub(r"\1", s)
    return BA_CHAM_RE.sub("...", s)


# ---------------------------------------------------------------- N5. Dấu câu dính chữ

DAU_CAU_DINH_RE = re.compile(rf"(?<=\S)([,;!?])(?={CHU})")   # đẹp,pin → đẹp, pin (";d" đứng riêng là emoticon, không tách)
CHAM_DINH_RE = re.compile(rf"(?<={CHU}{{2}})\.(?={CHU}{{2}})")   # đẹp.pin → đẹp. pin (v.v, 1.5tr không đổi)
BA_CHAM_DINH_RE = re.compile(rf"\.\.\.(?={CHU})")


def tach_dau_cau(s: str) -> str:
    """N5: thêm dấu cách sau , ; ! ? . … khi dấu câu dính liền chữ phía sau. Số (6.7 inch, 12,5) không đổi."""
    s = DAU_CAU_DINH_RE.sub(r"\1 ", s)
    s = CHAM_DINH_RE.sub(". ", s)
    return BA_CHAM_DINH_RE.sub("... ", s)


# ---------------------------------------------------------------- N6. Viết tắt, teencode

KHONG_DOI_SAU_SO = {"k", "kg", "v", "ms"}   # sau số là đơn vị: 500 k (nghìn), 1 kg, sạc 9 v, 50 ms
TOKEN_RE = re.compile(r"(?<!\S)([(\[\"'“‘]*)(\S+?)([.,!?;:)\]\"'”’…]*)(?!\S)")   # (mở ngoặc)(lõi)(dấu câu cuối)
SO_O_CUOI_RE = re.compile(r"\d\s*$")


@lru_cache(maxsize=4)
def doc_tu_dien(duong_dan: str | Path = TU_DIEN_VIET_TAT) -> dict[str, str]:
    """Đọc từ điển viết tắt (TSV: viết tắt <tab> đầy đủ <tab> ghi chú). Dòng bắt đầu bằng # là chú thích."""
    tu_dien: dict[str, str] = {}
    with open(duong_dan, encoding="utf-8") as f:
        for so_dong, dong in enumerate(f, start=1):
            if not dong.strip() or dong.startswith("#"):
                continue
            cot = dong.rstrip("\n").split("\t")
            if len(cot) < 2 or not cot[0].strip() or not cot[1].strip():
                raise ValueError(f"{duong_dan}:{so_dong}: cần ít nhất 2 cột cách nhau bằng tab")
            khoa = unicodedata.normalize("NFC", cot[0].strip().lower())
            if " " in khoa:
                raise ValueError(f"{duong_dan}:{so_dong}: viết tắt phải là một chữ, không có dấu cách: {khoa!r}")
            if khoa in tu_dien:
                raise ValueError(f"{duong_dan}:{so_dong}: '{khoa}' khai báo hai lần")
            tu_dien[khoa] = unicodedata.normalize("NFC", cot[1].strip())
    return tu_dien


def mo_viet_tat(s: str, tu_dien: dict[str, str] | None = None) -> str:
    """N6: thay từng chữ đứng riêng (tách bằng khoảng trắng, bỏ ngoặc và dấu câu hai đầu) theo từ điển viết tắt.

    Không thay bên trong chữ khác ("kon" không đổi), không thay emoticon (":v"), không đổi "k" đứng sau số.
    """
    td = doc_tu_dien() if tu_dien is None else tu_dien

    def thay(m: re.Match) -> str:
        mo, loi, dong = m.groups()
        moi = td.get(loi)
        if moi is None or (loi in KHONG_DOI_SAU_SO and SO_O_CUOI_RE.search(s, 0, m.start())):
            return m.group(0)
        return mo + moi + dong

    return TOKEN_RE.sub(thay, s)


# ---------------------------------------------------------------- Cả Level 2

CAC_BUOC = [   # (mã, tên, hàm) theo đúng thứ tự chạy
    ("N1", "URL, email, số điện thoại, @tên → token", thay_token),
    ("N2", "Chữ thường", chu_thuong),
    ("N3", "Dấu thanh về một kiểu", chuan_dau_thanh),
    ("N4", "Tiếng cười, emoticon, ký tự lặp", rut_gon_lap),
    ("N5", "Tách dấu câu dính chữ", tach_dau_cau),
    ("N6", "Viết tắt, teencode", mo_viet_tat),
    ("N7", "Dọn khoảng trắng", chuan_khoang_trang),
]


def chuan_hoa_tung_buoc(text_clean: str) -> list[tuple[str, str, str]]:
    """Trả [(mã bước, tên bước, chuỗi sau bước)] để xem từng bước đổi gì."""
    ket_qua, s = [], text_clean or ""
    for ma, ten, ham in CAC_BUOC:
        s = ham(s) if s else s
        ket_qua.append((ma, ten, s))
    return ket_qua


def chuan_hoa(text_clean: str) -> str:
    """Chạy N1–N7 trên `text_clean` (đầu ra của Level 1), trả `text_norm`."""
    s = text_clean or ""
    for _, _, ham in CAC_BUOC:
        if not s:
            break
        s = ham(s)
    return s


# ---------------------------------------------------------------- Emoji (cột `emojis`)

CO_KY_TU_CAO_RE = re.compile(r"[^\x00-῿]")   # lọc nhanh: emoji đều nằm từ U+2000 trở lên, chữ Việt thì dưới
GHEP_SAU = {"️", "︎", "⃣"}          # biến thể hiển thị, keycap


def _la_goc_emoji(ch: str) -> bool:
    cp = ord(ch)
    if cp < 0x2000 or 0x1F3FB <= cp <= 0x1F3FF or 0x1F1E6 <= cp <= 0x1F1FF:   # màu da và chữ cái cờ xử lý riêng
        return False
    return unicodedata.category(ch) == "So" or 0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF


def _la_ghep_sau(ch: str) -> bool:
    cp = ord(ch)
    return ch in GHEP_SAU or 0x1F3FB <= cp <= 0x1F3FF or 0xE0020 <= cp <= 0xE007F


def tach_emoji(s: str) -> list[str]:
    """Danh sách emoji theo thứ tự xuất hiện; emoji ghép (👨‍👩‍👧, 👍🏻, 🇻🇳, 1️⃣) tính là một.

    Khác Level 0 mục 2.5 ở chỗ không tính ký tự ASCII (^, `) và ký hiệu dưới U+2000 (°, ©) là emoji.
    """
    if not s or not CO_KY_TU_CAO_RE.search(s):
        return []
    ra, i, n = [], 0, len(s)
    while i < n:
        ch, cp = s[i], ord(s[i])
        if 0x1F1E6 <= cp <= 0x1F1FF:   # cờ quốc gia = 2 chữ cái cờ
            j = i + 2 if i + 1 < n and 0x1F1E6 <= ord(s[i + 1]) <= 0x1F1FF else i + 1
        elif ch in "0123456789#*" and s[i + 1:i + 2] == "⃣":
            j = i + 2
        elif ch in "0123456789#*" and s[i + 1:i + 3] == "️⃣":
            j = i + 3
        elif _la_goc_emoji(ch):
            j = i + 1
            while j < n:
                if _la_ghep_sau(s[j]):
                    j += 1
                elif s[j] == "‍" and j + 1 < n and _la_goc_emoji(s[j + 1]):
                    j += 2
                else:
                    break
        else:
            i += 1
            continue
        ra.append(s[i:j])
        i = j
    return ra


# ---------------------------------------------------------------- Tách chữ (cho EDA)

TU_RE = re.compile(r"<(?:url|email|phone|user)>|[^\W_]+")


def tach_tu(s: str) -> list[str]:
    """Tách chữ để đếm từ vựng: token <url>…, chữ và số; bỏ dấu câu, emoji, emoticon (":v" không thành chữ "v")."""
    return TU_RE.findall(EMOTICON_RE.sub(" ", s)) if s else []

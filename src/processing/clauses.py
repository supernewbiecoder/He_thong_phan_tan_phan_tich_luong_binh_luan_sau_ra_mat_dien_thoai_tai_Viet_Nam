"""Mục đích: Bước 2.3 – tách bình luận đã làm sạch (`text_clean`) thành mệnh đề cho cột `clauses` (docs/2-tien-xu-ly/dac-ta-tach-menh-de.md); cập nhật lần cuối: 2026-11-19.

Mệnh đề là đơn vị gán nhãn khía cạnh và cảm xúc: "Cam đẹp nhưng pin yếu" → "Cam đẹp" | "nhưng pin yếu".
Mỗi mệnh đề là một đoạn liền của `text_clean`, nên luôn có `text_clean[start:end] == text`.
"""

from __future__ import annotations

import re

from .normalize import CHU, DUOI_URL_RE, EMAIL_RE, URL_RE, chuan_hoa, tach_tu

MIN_CHU = 2   # mẩu cắt ở dấu phẩy có ít hơn số chữ này thì gộp sang mệnh đề bên kia dấu phẩy

# Loại ranh giới; mệnh đề ghi loại của ranh giới đứng ngay trước nó ở `ly_do` (khi gọi với kem_ly_do=True)
DAU, XUONG_DONG, HET_CAU, DAU_PHAY, TU_NOI = "dau", "xuong_dong", "het_cau", "dau_phay", "tu_noi"

HET_CAU_RE = re.compile(r"[.!?;…]+(?=\s|$)")    # "6.7", "v.v", "tgdd.vn" không cắt vì sau dấu chấm không có khoảng trắng
DAU_PHAY_RE = re.compile(rf",(?=\s|$|{CHU})")  # "12,5" không cắt; "đẹp,pin" có cắt
CAC_TU_NOI = ("nhưng mà", "nhưng", "tuy nhiên", "tuy vậy", "có điều", "được cái", "bù lại", "ngược lại", "nhma", "nma")
TU_NOI_RE = re.compile(rf"(?<=\s)(?:{'|'.join(CAC_TU_NOI)})(?!{CHU})", re.IGNORECASE)


def _vung_bao_ve(s: str) -> list[tuple[int, int]]:
    """Khoảng ký tự của URL và email: không cắt bên trong. Dấu câu dính cuối URL vẫn được cắt."""
    vung = [m.span() for m in EMAIL_RE.finditer(s)]
    for m in URL_RE.finditer(s):
        duoi = DUOI_URL_RE.search(m.group(0))
        vung.append((m.start(), m.end() - (len(duoi.group(0)) if duoi else 0)))
    return vung


def _cac_ranh_gioi(s: str) -> list[tuple[int, int, str]]:
    """[(vị trí hết mệnh đề trước, vị trí đầu mệnh đề sau, loại ranh giới)], sắp theo vị trí."""
    vung = _vung_bao_ve(s)

    def bi_chan(i: int) -> bool:
        return any(a <= i < b for a, b in vung)

    rg = [(m.start(), m.end(), XUONG_DONG) for m in re.finditer("\n", s)]
    rg += [(m.end(), m.end(), HET_CAU) for m in HET_CAU_RE.finditer(s) if not bi_chan(m.start())]   # dấu câu thuộc mệnh đề trước
    rg += [(m.start(), m.end(), DAU_PHAY) for m in DAU_PHAY_RE.finditer(s) if not bi_chan(m.start())]   # dấu phẩy bỏ ra ngoài
    rg += [(m.start(), m.start(), TU_NOI) for m in TU_NOI_RE.finditer(s) if not bi_chan(m.start())]   # từ nối thuộc mệnh đề sau
    return sorted(rg)


def _cat(s: str) -> list[list]:
    """Cắt theo ranh giới rồi bỏ khoảng trắng hai đầu; trả [[start, end, loại]], bỏ đoạn rỗng."""
    doan, dau, loai = [], 0, DAU
    for het, sau, k in _cac_ranh_gioi(s):
        if k == TU_NOI and not s[dau:het].strip():   # từ nối đứng ngay đầu mệnh đề vừa tách (", nhưng", "\nnhưng")
            continue
        if het < dau:   # ranh giới nằm trong ranh giới trước (vd "!!!" rồi "," liền sau): chỉ dời điểm bắt đầu
            dau, loai = max(dau, sau), k
            continue
        doan.append([dau, het, loai])
        dau, loai = sau, k
    doan.append([dau, len(s), loai])
    ra = []
    for a, b, k in doan:
        while a < b and s[a].isspace():
            a += 1
        while b > a and s[b - 1].isspace():
            b -= 1
        if a < b:
            ra.append([a, b, k])
    return ra


def _gop(s: str, doan: list[list]) -> list[list]:
    def so_chu(d: list) -> int:
        return len(tach_tu(s[d[0]:d[1]]))

    # 1. Mẩu không có chữ (chỉ emoji, emoticon, dấu câu) gộp vào mệnh đề trước; nếu đứng đầu thì gộp vào mệnh đề sau
    ra: list[list] = []
    for d in doan:
        if ra and so_chu(d) == 0:
            ra[-1][1] = d[1]
        else:
            ra.append(d)
    if len(ra) > 1 and so_chu(ra[0]) == 0:
        ra[1][0], ra[1][2] = ra[0][0], ra[0][2]
        ra.pop(0)

    # 2. Mẩu dưới MIN_CHU chữ nằm sát dấu phẩy gộp sang phía bên kia dấu phẩy ("ok, pin trâu" là một mệnh đề)
    doi = True
    while doi and len(ra) > 1:
        doi = False
        for i, d in enumerate(ra):
            if so_chu(d) >= MIN_CHU:
                continue
            if d[2] == DAU_PHAY and i > 0:
                ra[i - 1][1] = d[1]
            elif i + 1 < len(ra) and ra[i + 1][2] == DAU_PHAY:
                ra[i + 1][0], ra[i + 1][2] = d[0], d[2]
            else:
                continue
            ra.pop(i)
            doi = True
            break
    return ra


def tach_menh_de(text_clean: str, kem_norm: bool = True, kem_ly_do: bool = False) -> list[dict]:
    """Tách `text_clean` thành mệnh đề: [{"idx", "start", "end", "text", "text_norm"}], idx đếm từ 0.

    kem_norm=False bỏ `text_norm` (nhanh hơn, dùng cho EDA). kem_ly_do=True thêm `ly_do`: loại ranh giới
    đứng trước mệnh đề ("dau" với mệnh đề đầu, "xuong_dong", "het_cau", "dau_phay", "tu_noi").
    """
    s = text_clean or ""
    if not s.strip():
        return []
    ra = []
    for i, (a, b, k) in enumerate(_gop(s, _cat(s))):
        md = {"idx": i, "start": a, "end": b, "text": s[a:b]}
        if kem_norm:
            md["text_norm"] = chuan_hoa(md["text"])
        if kem_ly_do:
            md["ly_do"] = k
        ra.append(md)
    return ra

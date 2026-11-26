"""Mục đích: Luật mốc xác định máy được nhắc (`target_model`) cho từng lời nhận xét, xét cả bình luận chứ không chỉ một mệnh đề (docs/4-mo-hinh/dac-ta-suy-luan.md mục 5); cập nhật lần cuối: 2026-11-20.

Tên máy lấy từ danh mục `config/pipeline.yaml` (cùng file Công việc 12 dùng để kiểm). Chỉ nhận tên có chữ số và chỉ
thuộc đúng một máy ("ip17prm", "S26 Ultra"); tên hãng trơn ("táo", "ss", "iphone") không đủ để biết máy nào.
Chưa nhận câu so sánh: `compare_with` để Công việc 10 làm (cần nhãn để đo).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

GIO_VN = timezone(timedelta(hours=7))   # Việt Nam không đổi giờ theo mùa, nên dùng độ lệch cố định

# Nguồn của kết quả, theo thứ tự xét (ghi vào manifest để đếm)
MENH_DE, MENH_DE_TRUOC, BINH_LUAN, BINH_LUAN_CHA, VIDEO, KHONG_RO = (
    "menh_de", "menh_de_truoc", "binh_luan", "binh_luan_cha", "video", "khong_ro")


def gap_chu(s: str) -> str:
    """Chữ thường, bỏ dấu, "đ" → "d", gộp khoảng trắng: để so tên máy."""
    s = unicodedata.normalize("NFD", (s or "").casefold().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def doc_danh_muc(duong_dan: str | Path) -> dict[str, dict]:
    """{mã máy: {"title", "launch_date", "aliases"}} từ pipeline.yaml, gồm cả máy khai trong `rivals`."""
    import yaml   # chỉ cần khi đọc danh mục

    du_lieu = yaml.safe_load(Path(duong_dan).read_text(encoding="utf-8-sig"))
    danh_muc: dict[str, dict] = {}

    def them(muc) -> None:
        if isinstance(muc, str):
            muc = {"name": muc}
        ma = muc["name"]
        cu = danh_muc.setdefault(ma, {"title": None, "launch_date": None, "aliases": []})
        ngay = muc.get("launch_date")
        if ngay is not None:
            ngay = ngay.isoformat() if isinstance(ngay, date) else str(ngay)
            if cu["launch_date"] not in (None, ngay):
                raise ValueError(f"{ma}: hai launch_date khác nhau trong danh mục")
            cu["launch_date"] = ngay
        cu["title"] = cu["title"] or muc.get("title")
        cu["aliases"] = list(dict.fromkeys([*cu["aliases"], *muc.get("aliases", [])]))
        for doi_thu in muc.get("rivals", []) or []:
            them(doi_thu)

    for muc in du_lieu["models"]:
        them(muc)
    return danh_muc


def _mau_ten(ten_gap: str) -> str:
    """Regex cho một tên máy: cho phép có hoặc không có dấu cách ở chỗ chữ ↔ số và ở chỗ tên gốc có dấu cách."""
    khoi = re.findall(r"[a-z]+|\d+", ten_gap)
    return r"\s?".join(map(re.escape, khoi))


class BoNhanMay:
    """Tìm tên máy trong một đoạn chữ; trả mã máy theo thứ tự xuất hiện."""

    def __init__(self, danh_muc: dict[str, dict]):
        self.danh_muc = danh_muc
        theo_ten: dict[str, tuple[set[str], set[str]]] = {}   # tên viết liền -> (các mã máy, các regex)
        for ma, may in danh_muc.items():
            for ten in (ma, may.get("title") or "", *may.get("aliases", [])):
                g = gap_chu(ten)
                if g and any(c.isdigit() for c in g):
                    cac_ma, cac_regex = theo_ten.setdefault(re.sub(r"[^a-z0-9]", "", g), (set(), set()))
                    cac_ma.add(ma)
                    cac_regex.add(_mau_ten(g))
        self._ma_theo_ten = {}   # tên viết liền -> mã máy, chỉ giữ tên thuộc đúng một máy
        cac_mau = []
        for gon, (cac_ma, cac_regex) in theo_ten.items():
            if len(cac_ma) == 1:   # tên dùng chung cho nhiều máy thì không nhận
                self._ma_theo_ten[gon] = next(iter(cac_ma))
                cac_mau += [(len(gon), m) for m in cac_regex]
        cac_mau.sort(key=lambda x: (-x[0], x[1]))   # tên dài thử trước: "s26 ultra" thắng "s26u" ở cùng vị trí
        # Một regex gộp, quét một lượt từ trái sang phải: tên nằm bên trong tên dài hơn đã khớp thì không xét nữa
        self._mau = re.compile(r"(?<![a-z0-9])(?:" + "|".join(m for _, m in cac_mau) + r")(?![a-z0-9])") if cac_mau else None

    def tim(self, text: str) -> list[str]:
        """Mã máy được gọi tên trong `text`, theo vị trí xuất hiện, không lặp."""
        if self._mau is None or not text:
            return []
        return list(dict.fromkeys(self._ma_theo_ten[re.sub(r"\s", "", m.group())]
                                  for m in self._mau.finditer(gap_chu(text))))


def xac_dinh_may(i: int, may_theo_menh_de: list[list[str]], may_cha: list[str], may_video: str | None,
                 danh_muc: dict) -> tuple[str | None, str]:
    """Máy được nhắc của mệnh đề thứ `i` và nguồn của kết quả. Xét lần lượt:

    1. tên máy trong chính mệnh đề (nhiều tên thì lấy tên đứng đầu);
    2. tên máy gần nhất trong các mệnh đề đứng trước, cùng bình luận ("iPhone thì pin trâu, camera đẹp");
    3. cả bình luận gọi tên đúng một máy;
    4. bình luận cha gọi tên đúng một máy;
    5. máy của video, nếu video chỉ về một máy;
    6. không rõ: None.
    """
    if may_theo_menh_de[i]:
        return may_theo_menh_de[i][0], MENH_DE
    for j in range(i - 1, -1, -1):
        if may_theo_menh_de[j]:
            return may_theo_menh_de[j][-1], MENH_DE_TRUOC
    ca_bai = list(dict.fromkeys(ma for ds in may_theo_menh_de for ma in ds))
    if len(ca_bai) == 1:
        return ca_bai[0], BINH_LUAN
    if len(may_cha) == 1:
        return may_cha[0], BINH_LUAN_CHA
    if may_video and "|" not in may_video and may_video in danh_muc:
        return may_video, VIDEO
    return None, KHONG_RO


def so_ngay_tu_ra_mat(published_at: str, launch_date: str | None) -> int | None:
    """Ngày đăng (giờ Việt Nam) trừ ngày ra mắt; cùng cách tính với src/analysis/validation.py."""
    if not launch_date:
        return None
    dang = datetime.fromisoformat(published_at.replace("Z", "+00:00")).astimezone(GIO_VN).date()
    return (dang - date.fromisoformat(launch_date)).days

"""Mục đích: Thống kê mã tự do của mã hóa mở (B4) theo lô, hành vi, đối tượng, đối tượng mới từng lô; ghi docs/3-gan-nhan/bao-cao-ma-hoa-mo.md (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 5, 10); cập nhật lần cuối: 2026-11-23.

Chạy từ gốc repo:
    python -m src.labeling.code_stats

Chỉ đếm mã tự do, không phải phân bố nhãn, nên chỉ ghi số đếm. File ra chỉ có số và chữ của mã, không có chữ bình luận.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .sample import GOC, LO_MA_HOA_MO, RA, _sha256, doc_csv

PHIEU = RA / "phieu_ma_hoa_mo.csv"
BAO_CAO = GOC / "docs" / "3-gan-nhan" / "bao-cao-ma-hoa-mo.md"
KHONG_RO = ("không hiểu", "không rõ", "không nội dung")
DA_DUNG = re.compile(r"\b(đã|đang) dùng\b")
TOP_DOI_TUONG = 30


def tach_ma(o: str) -> list[dict]:
    """Tách ô ma_tu_do thành các mã: đối tượng, hành vi, các ghi chú phụ, có '?' hay không.
    Chữ chuẩn NFC, hành vi viết thường: 'Khen' và 'khen' gõ kiểu tổ hợp đều là 'khen' (đặc tả mục 5)."""
    ra = []
    for m in unicodedata.normalize("NFC", o or "").split(";"):
        m = m.strip()
        if not m:
            continue
        chua_chac = m.endswith("?")
        doi_tuong, _, sau = m.rstrip("?").strip().partition(":")
        sau = sau.strip()
        k = sau.find("(")
        ra.append({
            "doi_tuong": doi_tuong.strip(),
            "hanh_vi": (sau[:k] if k >= 0 else sau).strip().lower() or "?",
            "phu": re.findall(r"\(([^()]*)\)", sau),
            "chua_chac": chua_chac,
        })
    return ra


def _theo_lo(dong: list[dict]) -> dict:
    ma = [tach_ma(d["ma_tu_do"]) for d in dong]
    tat_ca = [m for x in ma for m in x]
    return {
        "n": len(dong),
        "so_ma": len(tat_ca),
        "nhieu_ma": sum(len(x) >= 2 for x in ma),
        "ma_chua_chac": sum(m["chua_chac"] for m in tat_ca),
        "bl_chua_chac": sum(any(m["chua_chac"] for m in x) for x in ma),
        "bl_khong_ro": sum(any(m["doi_tuong"] in KHONG_RO for m in x) for x in ma),
        "bl_da_dung": sum(any(DA_DUNG.search(p) for m in x for p in m["phu"]) for x in ma),
        "bl_reply": sum(d.get("la_reply") == "co" for d in dong),
    }


def thong_ke(dong: list[dict], lo_ngau_nhien: tuple = LO_MA_HOA_MO) -> dict:
    """Số liệu cho báo cáo. dong: các dòng phiếu (cột lo, ma_tu_do, la_reply)."""
    cac_lo = list(lo_ngau_nhien) + sorted({d["lo"] for d in dong} - set(lo_ngau_nhien))
    theo_lo = {lo: _theo_lo([d for d in dong if d["lo"] == lo]) for lo in cac_lo}
    nn = [d for d in dong if d["lo"] in lo_ngau_nhien]
    ma_nn = [tach_ma(d["ma_tu_do"]) for d in nn]
    hanh_vi_ma = Counter(m["hanh_vi"] for x in ma_nn for m in x)
    hanh_vi_bl = Counter(h for x in ma_nn for h in {m["hanh_vi"] for m in x})
    doi_tuong = Counter(m["doi_tuong"] for x in ma_nn for m in x)
    da_thay_dt, da_thay_hv, moi = set(), set(), {}
    for lo in lo_ngau_nhien:
        ma_lo = [m for d in nn if d["lo"] == lo for m in tach_ma(d["ma_tu_do"])]
        dt, hv = {m["doi_tuong"] for m in ma_lo}, {m["hanh_vi"] for m in ma_lo}
        moi[lo] = {"doi_tuong_moi": len(dt - da_thay_dt), "hanh_vi_moi": sorted(hv - da_thay_hv)}
        da_thay_dt |= dt
        da_thay_hv |= hv
    cd = [m for d in dong if d["lo"] not in lo_ngau_nhien for m in tach_ma(d["ma_tu_do"])]
    return {
        "theo_lo": theo_lo, "hanh_vi_ma": hanh_vi_ma, "hanh_vi_bl": hanh_vi_bl, "doi_tuong": doi_tuong,
        "moi": moi, "n_ngau_nhien": len(nn),
        "cd_hanh_vi": Counter(m["hanh_vi"] for m in cd),
        "cd_doi_tuong_moi": Counter(m["doi_tuong"] for m in cd if m["doi_tuong"] not in doi_tuong),
    }


def _bang(tieu_de: list[str], hang: list[list]) -> str:
    dong = ["| " + " | ".join(tieu_de) + " |", "|" + "---|" * len(tieu_de)]
    dong += ["| " + " | ".join(str(o) for o in h) + " |" for h in hang]
    return "\n".join(dong)


def viet_bao_cao(tk: dict, sha_phieu: str) -> str:
    ngay = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tl = tk["theo_lo"]
    nn = [lo for lo in tl if lo in tk["moi"]]
    cong = {k: sum(tl[lo][k] for lo in nn) for k in tl[nn[0]]}
    hang_lo = [[lo, v["n"], v["so_ma"], f"{v['so_ma'] / v['n']:.2f}" if v["n"] else "", v["nhieu_ma"],
                v["ma_chua_chac"], v["bl_chua_chac"], v["bl_khong_ro"], v["bl_da_dung"], v["bl_reply"]]
               for lo, v in tl.items()]
    hang_lo.insert(len(nn), [f"**Lô {nn[0]}–{nn[-1]}**", cong["n"], cong["so_ma"], f"{cong['so_ma'] / cong['n']:.2f}",
                             cong["nhieu_ma"], cong["ma_chua_chac"], cong["bl_chua_chac"], cong["bl_khong_ro"],
                             cong["bl_da_dung"], cong["bl_reply"]])
    dt = tk["doi_tuong"]
    s = [
        "# Báo cáo mã hóa mở (B4)",
        "",
        f"> Mục đích: Số liệu mã tự do của mã hóa mở trên mẫu khám phá nhãn: theo lô, hành vi, đối tượng, đối tượng mới từng lô; cập nhật lần cuối: {ngay}.",
        "",
        "**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.code_stats`. "
        f"Nguồn: `data/kham-pha/phieu_ma_hoa_mo.csv` (SHA-256 `{sha_phieu[:8]}…{sha_phieu[-4:]}`), dữ liệu v4, seed lấy mẫu `20261122`. "
        "Luật: [đặc tả khám phá nhãn](dac-ta-kham-pha-nhan.md) mục 5; cách mã: [guideline](huong-dan-kham-pha-nhan.md).",
        "",
        "**Người mã: Claude (người mã hóa A).** Trưởng nhóm chưa kiểm từng mã. Mọi lô đã được Claude tự rà lượt 2 (lô 1 ngày 22/11, các lô khác ngày 23/11); tự rà không thay được người kiểm.",
        "",
        "**Cách đọc:** đây là **đếm mã tự do, không phải phân bố nhãn**, nên chỉ ghi số đếm. Một bình luận có thể có nhiều mã. "
        "Phân bố, kèm khoảng tin cậy, chỉ tính ở B7 theo bộ nhãn đã kiểm.",
        "",
        "## 1. Theo lô",
        "",
        _bang(["Lô", "Bình luận", "Mã", "Mã / bình luận", "Bình luận ≥ 2 mã", "Mã `?`", "Bình luận có mã `?`",
               "Bình luận không hiểu, không rõ đối tượng", "Bình luận có \"đã/đang dùng\"", "Reply"], hang_lo),
        "",
        "Lô `CD` là mẫu có chủ đích (tìm theo từ khóa \"lỗi\", \"bảo hành\"…): **không đại diện**, không cộng vào lô 1–5.",
        "",
        f"## 2. Hành vi (lô {nn[0]}–{nn[-1]}, {tk['n_ngau_nhien']} bình luận)",
        "",
        _bang(["Hành vi", "Số mã", "Số bình luận có"],
              [[f"`{h}`", n, tk["hanh_vi_bl"][h]] for h, n in tk["hanh_vi_ma"].most_common()]),
        "",
        "`?` là mã `không hiểu: ?`.",
        "",
        f"## 3. Đối tượng (lô {nn[0]}–{nn[-1]})",
        "",
        f"- {sum(dt.values())} mã, **{len(dt)} đối tượng khác nhau**; {sum(1 for v in dt.values() if v == 1)} đối tượng chỉ gặp một lần.",
        "- Đối tượng giữ nguyên từ của bình luận (guideline quy tắc 3), nên từ đồng nghĩa chưa gộp. Gộp ở B5.",
        "",
        _bang(["Đối tượng", "Số mã"], [[f"`{o}`", n] for o, n in dt.most_common(TOP_DOI_TUONG)]),
        "",
        "## 4. Đối tượng và hành vi mới theo lô",
        "",
        _bang(["Lô", "Đối tượng mới", "Hành vi mới"],
              [[lo, v["doi_tuong_moi"], ", ".join(f"`{h}`" for h in v["hanh_vi_moi"]) or "không có"]
               for lo, v in tk["moi"].items()]),
        "",
        "Đối tượng mới chưa phải bão hòa: phần lớn là cách viết khác của cùng một ý. Bão hòa đếm theo **nhãn** sau khi gom (B5, đặc tả mục 6).",
        "",
        "## 5. Mẫu có chủ đích",
        "",
        _bang(["Hành vi", "Số mã"], [[f"`{h}`", n] for h, n in tk["cd_hanh_vi"].most_common()]),
        "",
        f"- {len(tk['cd_doi_tuong_moi'])} đối tượng chỉ gặp ở mẫu có chủ đích, không có trong lô 1–5. "
        "Đây là chỗ để B5 tìm loại hiếm (lỗi, bảo hành, trả góp…). Hay gặp nhất: "
        + ", ".join(f"`{o}` ({n})" for o, n in tk["cd_doi_tuong_moi"].most_common(15)) + ".",
        "",
    ]
    return "\n".join(s)


def chay(phieu: Path = PHIEU, ra: Path = BAO_CAO) -> dict:
    dong = doc_csv(phieu)
    trong = [d["stt"] for d in dong if not (d.get("ma_tu_do") or "").strip()]
    if trong:
        raise SystemExit(f"Còn {len(trong)} bình luận chưa có mã (stt {', '.join(trong[:10])}…): mã đủ rồi mới thống kê.")
    tk = thong_ke(dong)
    ra.write_text(viet_bao_cao(tk, _sha256(phieu)), encoding="utf-8")
    return {"file": str(ra.relative_to(GOC)), "so_binh_luan": len(dong),
            "so_ma": sum(v["so_ma"] for v in tk["theo_lo"].values())}


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="Thống kê mã hóa mở (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 5)").parse_args(argv)
    kq = chay()
    sys.stdout.reconfigure(encoding="utf-8")
    print(kq)


if __name__ == "__main__":
    main()

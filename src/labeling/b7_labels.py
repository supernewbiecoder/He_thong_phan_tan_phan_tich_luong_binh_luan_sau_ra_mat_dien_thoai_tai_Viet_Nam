"""Mục đích: Nhãn B7: đọc và kiểm nhãn của A, ghi phieu_b7.csv, xuất phiếu cho B kiểm, áp phần B sửa (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 7c, 8); cập nhật lần cuối: 2026-11-25.

Chạy từ gốc repo:
    python -m src.labeling.b7_labels nap         # nhan_b7_A.txt -> phieu_b7.csv
    python -m src.labeling.b7_labels phieu-kiem  # phieu_kiem_b7.csv cho B (không ghi đè phần B đã điền)
"""

from __future__ import annotations

import argparse
import csv
import io
import random
import re
import sys
from collections import Counter
from pathlib import Path

from .label_set import KHIA_CANH, MUC_DICH, NGOAI_KHIA_CANH
from .sample import LO_MA_HOA_MO, RA, SEED, _ghi_csv, doc_csv

PHIEU_A = RA / "phieu_ma_hoa_mo.csv"
NHAN_A = RA / "nhan_b7_A.txt"
PHIEU_B7 = RA / "phieu_b7.csv"
PHIEU_KIEM = RA / "phieu_kiem_b7.csv"
PHIEU_KIEM_DA_DIEN = RA / "phieu_kiem_b7_da_dien.csv"   # B lưu bản đã điền tên này; có thì dùng
PHIEU_KIEM_2 = RA / "phieu_kiem_b7_phan_2.csv"          # đợt 2: mọi bình luận lô 1–5 chưa kiểm (đặc tả mục 7c)
PHIEU_KIEM_2_DA_DIEN = RA / "phieu_kiem_b7_phan_2_da_dien.csv"
MAU = RA / "mau.csv"
SO_KIEM = 100

LIEN_QUAN = ("dien_thoai", "ngu_canh", "nguoi_binh_luan", "khong_lien_quan", "khong_noi_dung", "khong_xac_dinh")
NOI_VE = KHIA_CANH + ("khac",) + NGOAI_KHIA_CANH
THAI_DO = ("tich_cuc", "tieu_cuc", "so_sanh", "khong_danh_gia")
DA_DUNG = ("co", "khong_ro")
MAY_NHAC = ("goi_ten_may", "chi_hang", "khong_nhac")
CHIEU = {1: ("lien_quan", "1. Liên quan tới gì"), 2: ("noi_ve", "2. Nói về phần nào của điện thoại"),
         3: ("muc_dich", "3. Mục đích"), 4: ("thai_do", "4. Thái độ"), 5: ("da_dung", "5. Đã dùng máy"),
         6: ("may_nhac", "6. Máy được nhắc")}

# Chữ viết tắt trong nhan_b7_A.txt: stt|chiều 1|chiều 2 kèm thái độ|chiều 3|chiều 5|chiều 6|các chiều chưa chắc|ghi chú
TAT_1 = dict(zip("DNBLEX", LIEN_QUAN))
TAT_2 = dict(pin="pin_sac", man="man_hinh", hn="hieu_nang", nd="nhiet_do", cam="camera", tk="thiet_ke", db="do_ben",
             pm="phan_mem", at="am_thanh", pc="phan_cung_khac", gia="gia", mua="mua_ban", bh="bao_hanh_sua_chua",
             khac="khac", mc="may_chung", hang="hang_nguoi_dung")
TAT_3 = dict(dg="danh_gia", hoi="hoi", tt="thong_tin", dn="de_nghi", bt="ban_than", bl="bao_loi", tl="tranh_luan",
             dua="dua", ck="cong_kich", mg="minigame", qc="quang_cao", xg="xa_giao", x="khong_xac_dinh")
TAT_4 = {"+": "tich_cuc", "-": "tieu_cuc", "=": "so_sanh", "0": "khong_danh_gia"}
TAT_5 = dict(c="co", k="khong_ro")
TAT_6 = dict(t="goi_ten_may", h="chi_hang", k="khong_nhac")

COT_NHAN = ("lien_quan", "noi_ve_thai_do", "muc_dich", "da_dung", "may_nhac")
COT_SUA = tuple("sua_" + c for c in COT_NHAN)
COT_B7 = ("stt", "lo", "comment_id", "video_id", "may_video", "loai_video", "nhom_kenh", "tuan", "la_reply", "chu_kenh",
          "binh_luan", "binh_luan_cha") + COT_NHAN + ("chua_chac", "ghi_chu_a")
COT_KIEM = ("stt", "vi_sao_chon", "binh_luan", "binh_luan_cha") + COT_NHAN + ("chua_chac", "ghi_chu_a", "da_kiem") \
    + COT_SUA + ("ghi_chu_kiem",)


class LoiNhan(ValueError):
    """Nhãn không hợp lệ; thông báo ghi rõ dòng nào."""


def tach(o: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,]", o or "") if x.strip()]


def tach_cap(o: str) -> dict[str, tuple[str, ...]]:
    """'camera:tich_cuc+tieu_cuc; gia:khong_danh_gia' -> {'camera': ('tich_cuc', 'tieu_cuc'), 'gia': (...)}"""
    ra = {}
    for c in tach(o):
        nhan, _, td = c.partition(":")
        ra[nhan.strip()] = tuple(x.strip() for x in td.split("+") if x.strip())
    return ra


def kiem_tra(d: dict, ten: str) -> None:
    """Dừng nếu nhãn của một bình luận sai luật (đặc tả mục 8)."""
    cap = tach_cap(d["noi_ve_thai_do"])
    loi = []
    if d["lien_quan"] not in LIEN_QUAN:
        loi.append(f"chiều 1 {d['lien_quan']!r}")
    loi += [f"chiều 2 {k!r}" for k in cap if k not in NOI_VE]
    loi += [f"chiều 4 {k}:{v}" for k, v in cap.items() if not v or any(x not in THAI_DO for x in v)]
    md = tach(d["muc_dich"])
    loi += [f"chiều 3 {m!r}" for m in md if m not in MUC_DICH] + ([] if md else ["chiều 3 trống"])
    loi += [] if d["da_dung"] in DA_DUNG else [f"chiều 5 {d['da_dung']!r}"]
    loi += [] if d["may_nhac"] in MAY_NHAC else [f"chiều 6 {d['may_nhac']!r}"]
    if "ten_may" in d and (d["may_nhac"] == "goi_ten_may") != bool(tach(d["ten_may"])):
        loi.append("goi_ten_may thì phải ghi ten_may, nhãn khác thì để trống")
    if (d["lien_quan"] == "dien_thoai") != bool(cap):
        loi.append("dien_thoai thì phải có nhãn chiều 2, nhãn khác thì không được có")
    if loi:
        raise LoiNhan(f"{ten}: " + "; ".join(loi))


def mo_rong(cot: str, o: str) -> str:
    """Một ô nhãn người gõ (tên đầy đủ hay viết tắt) thành tên đầy đủ. Chữ lạ giữ nguyên để kiem_tra báo lỗi."""
    if cot == "noi_ve_thai_do":
        ra = []
        for x in tach(o):
            m = re.fullmatch(r"([a-z]+)\s*([-+=0]+)", x.lower())
            ra.append(TAT_2.get(m[1], m[1]) + ":" + "+".join(TAT_4[c] for c in m[2]) if m else x)
        return "; ".join(ra)
    tat = {"lien_quan": TAT_1, "muc_dich": TAT_3, "da_dung": TAT_5, "may_nhac": TAT_6}[cot]
    return "; ".join(tat.get(x) or tat.get(x.lower()) or tat.get(x.upper()) or x for x in tach(o))


def doc_nhan_a(chu: str) -> dict[int, dict]:
    """Đọc bản viết tắt của A thành nhãn đầy đủ; trùng stt hay chữ tắt lạ thì dừng."""
    ra: dict[int, dict] = {}
    for dong in chu.splitlines():
        if not dong.strip():
            continue
        o = dong.split("|")
        if len(o) not in (8, 9):
            raise LoiNhan(f"dòng phải có 8 ô (9 nếu có tên máy): {dong!r}")
        stt = int(o[0])
        if stt in ra:
            raise LoiNhan(f"stt {stt} trùng")
        try:
            cap = []
            for x in tach(o[2]):
                m = re.fullmatch(r"([a-z]+)([-+=0]+)", x)
                if not m:
                    raise KeyError(x)
                cap.append(TAT_2[m[1]] + ":" + "+".join(TAT_4[c] for c in m[2]))
            d = {"lien_quan": TAT_1[o[1]], "noi_ve_thai_do": "; ".join(cap),
                 "muc_dich": "; ".join(TAT_3[x] for x in tach(o[3])), "da_dung": TAT_5[o[4]], "may_nhac": TAT_6[o[5]],
                 "chua_chac": "; ".join(CHIEU[int(c)][0] for c in o[6]), "ghi_chu_a": o[7].strip()}
            if len(o) == 9:
                d["ten_may"] = "; ".join(tach(o[8].lower()))
        except KeyError as e:
            raise LoiNhan(f"stt {stt}: chữ tắt lạ {e}") from None
        kiem_tra(d, f"stt {stt}")
        ra[stt] = d
    return ra


def danh_muc_may() -> set[str]:
    """Mã máy trong danh mục (trường name của models.json, sinh từ config/pipeline.yaml)."""
    import json
    p = RA.parents[1] / "src" / "ingest" / "data" / "models.json"
    return {m["name"] for m in json.loads(p.read_text(encoding="utf-8"))["models"]} if p.exists() else set()


def thanh_nhan(d: dict) -> dict[str, set[str]]:
    """Nhãn của một bình luận thành tập theo chiều (chiều 4: các cặp 'nhãn chiều 2:thái độ')."""
    cap = tach_cap(d["noi_ve_thai_do"])
    return {"lien_quan": {d["lien_quan"]}, "noi_ve": set(cap), "muc_dich": set(tach(d["muc_dich"])),
            "thai_do": {f"{k}:{t}" for k, v in cap.items() for t in v}, "da_dung": {d["da_dung"]},
            "may_nhac": {d["may_nhac"]}}


def nap() -> dict:
    nhan = doc_nhan_a(NHAN_A.read_text(encoding="utf-8"))
    video = {d["comment_id"]: d["video_id"] for d in doc_csv(MAU)}
    dong = [d for d in doc_csv(PHIEU_A) if d["lo"] in LO_MA_HOA_MO]
    lech = {int(d["stt"]) for d in dong} ^ set(nhan)
    if lech:
        raise LoiNhan(f"stt thiếu hoặc thừa: {sorted(lech)[:10]}")
    _ghi_csv(PHIEU_B7, COT_B7, [{**d, "video_id": video[d["comment_id"]], **nhan[int(d["stt"])]} for d in dong])
    return {"so_binh_luan": len(dong), "co_chua_chac": sum(bool(n["chua_chac"]) for n in nhan.values()),
            "file": str(PHIEU_B7)}


def chon_kiem(dong: list[dict], so: int = SO_KIEM, seed: int = SEED) -> list[dict]:
    """Các dòng B phải xem: `so` bình luận ngẫu nhiên, và mọi bình luận có '?' (đặc tả mục 7c)."""
    nn = set(random.Random(seed).sample([d["stt"] for d in dong], min(so, len(dong))))
    ra = []
    for d in dong:
        vs = [t for t, dk in (("ngau_nhien", d["stt"] in nn), ("chua_chac", bool(d["chua_chac"]))) if dk]
        if vs:
            ra.append({**d, "vi_sao_chon": " + ".join(vs)})
    return ra


def doc_phieu_nguoi(p: Path) -> list[dict]:
    """Đọc phiếu đã qua Excel: nhận cả dấu ; làm dấu cách cột, và chữ không phải UTF-8 (nhãn chỉ là chữ ASCII)."""
    chu = p.read_bytes().decode("utf-8-sig", errors="replace")
    dau_cot = chu.split("\n", 1)[0]
    dau = ";" if dau_cot.count(";") > dau_cot.count(",") else ","
    return list(csv.DictReader(io.StringIO(chu, newline=""), delimiter=dau))


def da_dien(dong: list[dict]) -> bool:
    return any((d.get(c) or "").strip() for d in dong for c in ("da_kiem", "ghi_chu_kiem") + COT_SUA)


def phieu_kiem() -> dict:
    if PHIEU_KIEM.exists() and da_dien(doc_phieu_nguoi(PHIEU_KIEM)):
        raise SystemExit(f"{PHIEU_KIEM.name} đã có người điền; không ghi đè.")
    chon = chon_kiem(doc_csv(PHIEU_B7))
    _ghi_csv(PHIEU_KIEM, COT_KIEM, chon)
    return {"so_dong": len(chon), **Counter(d["vi_sao_chon"] for d in chon), "file": str(PHIEU_KIEM)}


def chon_kiem_2(dong: list[dict]) -> list[dict]:
    """Đợt 2: mọi bình luận chưa có trong đợt 1."""
    da = {d["stt"] for d in chon_kiem(dong)}
    return [{**d, "vi_sao_chon": "con_lai"} for d in dong if d["stt"] not in da]


def phieu_kiem_2() -> dict:
    if PHIEU_KIEM_2.exists() and da_dien(doc_phieu_nguoi(PHIEU_KIEM_2)):
        raise SystemExit(f"{PHIEU_KIEM_2.name} đã có người điền; không ghi đè.")
    chon = chon_kiem_2(doc_csv(PHIEU_B7))
    _ghi_csv(PHIEU_KIEM_2, COT_KIEM, chon)
    return {"so_dong": len(chon), "file": str(PHIEU_KIEM_2)}


def doc_kiem() -> list[dict]:
    """Mọi dòng B đã điền, cả hai đợt; bản _da_dien được ưu tiên."""
    ra = []
    for xong, tho in ((PHIEU_KIEM_DA_DIEN, PHIEU_KIEM), (PHIEU_KIEM_2_DA_DIEN, PHIEU_KIEM_2)):
        p = xong if xong.exists() else tho
        if p.exists():
            ra += doc_phieu_nguoi(p)
    return ra


def nhan_cuoi(dong: list[dict], kiem: list[dict], het: bool = False) -> tuple[list[dict], dict]:
    """(nhãn sau khi áp phần B sửa, tình trạng kiểm). Chỉ dùng các dòng B ghi da_kiem."""
    can = {d["stt"]: d["vi_sao_chon"] for d in chon_kiem(dong)}
    if het:   # đã mở đợt 2: phải kiểm hết
        can.update({d["stt"]: d["vi_sao_chon"] for d in chon_kiem_2(dong)})
    k = {d["stt"]: d for d in kiem if (d.get("da_kiem") or "").strip()}
    quen = [d["stt"] for d in kiem if d["stt"] not in k and any((d.get(c) or "").strip() for c in COT_SUA)]
    if quen:
        raise LoiNhan(f"có nhãn sửa nhưng chưa ghi da_kiem, stt: {quen[:10]}")
    ra, sua, theo_chieu = [], set(), Counter()
    for d in dong:
        m = dict(d)
        if d["stt"] in k:
            for c, s in zip(COT_NHAN, COT_SUA):
                moi = mo_rong(c, k[d["stt"]].get(s) or "")
                if not moi:
                    continue
                cu = thanh_nhan(m)
                m[c] = moi
                if thanh_nhan(m) != cu:
                    sua.add(d["stt"])
                    theo_chieu[c] += 1
            if m["lien_quan"] != "dien_thoai":
                m["noi_ve_thai_do"] = ""
            kiem_tra(m, f"phiếu kiểm, stt {d['stt']}")
        ra.append(m)
    phan = {t: [s for s, v in can.items() if t in v] for t in ("ngau_nhien", "chua_chac")}
    return ra, {"can_kiem": len(can), "da_kiem": len(set(k) & set(can)), "xong": set(can) <= set(k), "sua": len(sua),
                "theo_chieu": theo_chieu, "phan": {t: (sum(s in sua for s in v), len(v)) for t, v in phan.items()}}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Nhãn B7 (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 7c, 8)")
    p.add_argument("viec", choices=("nap", "phieu-kiem", "phieu-kiem-2"))
    viec = p.parse_args(argv).viec
    sys.stdout.reconfigure(encoding="utf-8")
    print({"nap": nap, "phieu-kiem": phieu_kiem, "phieu-kiem-2": phieu_kiem_2}[viec]())


if __name__ == "__main__":
    main()

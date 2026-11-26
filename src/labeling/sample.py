"""Mục đích: Lấy mẫu khám phá nhãn (800 ngẫu nhiên chia lô, 100 có chủ đích) và xuất phiếu mã hóa (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 3.2–3.5); cập nhật lần cuối: 2026-11-25.

Chạy từ gốc repo:
    python -m src.labeling.sample              # mau.csv, mau.manifest.json, phieu_ma_hoa_mo.csv (lô 1–5 và có chủ đích)
    python -m src.labeling.sample --xuat-lo K  # chỉ ở bước B6: phiếu trống lô K (hoặc D1, D2)
    python -m src.labeling.sample --ghi-de     # chỉ khi thật sự muốn lấy mẫu lại: XÓA phần người đã điền

Quy tắc mù: chữ bình luận của lô K và lô dự trữ không được ghi ra file nào cho tới khi gọi --xuat-lo.
Phiếu đã có người điền thì không ghi đè, chỉ kiểm mẫu chạy lại có khớp không (đặc tả mục 3.5).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .light_clean import an_nhac_ten, lam_sach_nhe

GOC = Path(__file__).resolve().parents[2]
RAW = GOC / "src" / "ingest" / "data" / "raw" / "comments.jsonl"
VIDEOS = GOC / "src" / "ingest" / "data" / "raw" / "videos.jsonl"
MODELS = GOC / "src" / "ingest" / "data" / "models.json"
RA = GOC / "data" / "kham-pha"

SEED = 20261122
CAC_LO = (("1", 100), ("2", 100), ("3", 100), ("4", 100), ("5", 100), ("K", 100), ("D1", 100), ("D2", 100))
LO_MA_HOA_MO = ("1", "2", "3", "4", "5")
TU_KHOA_CHU_DICH = ("lỗi", "hỏng", "bảo hành", "đổi trả", "mua về", "đang dùng", "đang xài", "nóng máy",
                    "tụt pin", "so với", "trả góp", "xách tay")
MOI_TU_KHOA = 10
SO_CHU_DICH = 100
SO_KENH_LON = 5
CAT_CHA = 600

COT_MAU = ("stt", "lo", "mau", "comment_id", "video_id", "may_video", "loai_video", "nhom_kenh", "tuan",
           "la_reply", "chu_kenh")
COT_PHIEU = ("stt", "lo", "mau", "comment_id", "may_video", "loai_video", "nhom_kenh", "tuan", "la_reply",
             "chu_kenh", "binh_luan", "binh_luan_cha", "nguoi_ma_hoa", "ma_tu_do", "ghi_chu")
COT_PHIEU_NHAN = COT_PHIEU[:-3] + ("nguoi_gan", "lien_quan", "noi_ve_thai_do", "muc_dich", "da_dung", "may_nhac",
                                    "chua_chac", "ghi_chu")   # phiếu lô K: gán theo bộ nhãn (B6)
COT_PHIEU_D2 = COT_PHIEU_NHAN[:-2] + ("ten_may",) + COT_PHIEU_NHAN[-2:]   # lô D2: kiểm lại định nghĩa, thêm tên máy
SO_D2 = 50                                                               # chỉ 50 bình luận đầu của D2 (đặc tả mục 7b)
COT_NGUOI = ("nguoi_ma_hoa", "ma_tu_do", "ghi_chu")   # cột người điền; code không bao giờ ghi đè khi đã có chữ


def chia_lo(so_luong: int = sum(n for _, n in CAC_LO)) -> list[str]:
    """Tên lô theo vị trí trong mẫu ngẫu nhiên: 100 đầu là lô 1, … , vị trí 501–600 là lô K."""
    ra = [ten for ten, n in CAC_LO for _ in range(n)]
    if so_luong > len(ra):
        raise ValueError("mẫu lớn hơn tổng các lô")
    return ra[:so_luong]


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def _ghi_csv(p: Path, cot: tuple, dong: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    with open(tam, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot, extrasaction="ignore")
        w.writeheader()
        w.writerows(dong)
    os.replace(tam, p)


def doc_csv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def da_co_nguoi_dien(dong: list[dict], cot_code: set[str]) -> bool:
    """Có ô nào ngoài các cột do code sinh (cột người điền, hay cột thêm sau như ghi_chu_kiem) đã có chữ."""
    return any(k not in cot_code and isinstance(v, str) and v.strip() for d in dong for k, v in d.items())


def giu_phieu_cu(p: Path, dong_moi: list[dict]) -> bool:
    """True: phiếu cũ đã có người điền và cùng stt, comment_id với mẫu mới, nên giữ nguyên.
    False: chưa có phiếu hoặc phiếu còn trống, được ghi. Đã có người điền mà mẫu khác thì dừng (đặc tả mục 3.5)."""
    if not p.exists():
        return False
    cu = doc_csv(p)
    if not da_co_nguoi_dien(cu, set(COT_PHIEU) - set(COT_NGUOI)):
        return False
    if [(d.get("stt"), d.get("comment_id")) for d in cu] == [(str(m["stt"]), m["comment_id"]) for m in dong_moi]:
        return True
    raise SystemExit(f"{p.name} đã có người điền nhưng mẫu chạy lại khác (dữ liệu hay code đã đổi). Không ghi file nào. "
                     "Thêm --ghi-de nếu thật sự muốn lấy mẫu lại; phần đã điền sẽ mất.")


def _che_ten(m: dict) -> dict:
    return {**m, "binh_luan": an_nhac_ten(m["binh_luan"]), "binh_luan_cha": an_nhac_ten(m["binh_luan_cha"])}


def _doc_du_lieu() -> tuple[list[dict], int, Counter]:
    """Đọc raw, làm sạch nhẹ; trả (bình luận có nội dung, số bình luận rỗng bị bỏ, số bình luận theo kênh)."""
    video = {}
    with open(VIDEOS, encoding="utf-8") as f:
        for dong in f:
            v = json.loads(dong)
            cu = video.get(v["video_id"])
            if cu is None or v.get("fetched_at", "") >= cu.get("fetched_at", ""):
                video[v["video_id"]] = v
    cua_so = {m["name"]: datetime.fromisoformat(m["window_start"].replace("Z", "+00:00"))
              for m in json.loads(MODELS.read_text(encoding="utf-8"))["models"] if m.get("window_start")}
    ds, rong, theo_kenh = [], 0, Counter()
    with open(RAW, encoding="utf-8") as f:
        for dong in f:
            r = json.loads(dong)
            chu = lam_sach_nhe(r.get("text"))
            if not chu:
                rong += 1
                continue
            v = video.get(r["video_id"], {})
            kenh = v.get("channel_title")
            theo_kenh[kenh] += 1
            dang = datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))
            tuan = ""
            for may in (r.get("model") or "").split("|"):
                if may in cua_so and 0 <= (dang - cua_so[may]).days < 28:
                    tuan = str((dang - cua_so[may]).days // 7 + 1)
                    break
            ds.append({
                "comment_id": r["comment_id"], "video_id": r["video_id"], "may_video": r.get("model", ""),
                "loai_video": v.get("video_type") or "", "kenh": kenh, "tuan": tuan,
                "la_reply": "co" if r.get("parent_id") else "khong",
                "chu_kenh": "co" if r.get("author_is_creator") else "khong",
                "binh_luan": chu, "binh_luan_cha": lam_sach_nhe(r.get("parent_text"))[:CAT_CHA],
            })
    return ds, rong, theo_kenh


def chay(xuat_lo: str | None = None, ghi_de: bool = False) -> dict:
    """Lấy mẫu và ghi file; hoặc chỉ xuất phiếu trống một lô (xuat_lo = 'K', 'D1', 'D2').
    Phiếu đã có người điền thì giữ, trừ khi ghi_de."""
    ds, rong, theo_kenh = _doc_du_lieu()
    kenh_lon = [k for k, _ in theo_kenh.most_common() if k][:SO_KENH_LON]
    for c in ds:
        c["nhom_kenh"] = "khong_ro" if not c["kenh"] else ("5_kenh_lon" if c["kenh"] in kenh_lon else "kenh_khac")

    rng = random.Random(SEED)
    chon = rng.sample(range(len(ds)), sum(n for _, n in CAC_LO))
    cac_lo = chia_lo(len(chon))
    da_chon = set(chon)
    chu_dich, dem_tu_khoa = [], {}
    for tu in TU_KHOA_CHU_DICH:
        khop = [i for i, c in enumerate(ds) if tu in c["binh_luan"].lower() and i not in da_chon]
        dem_tu_khoa[tu] = len(khop)
        for i in rng.sample(khop, min(MOI_TU_KHOA, len(khop))):
            if i not in chu_dich:
                chu_dich.append(i)
    if len(chu_dich) > SO_CHU_DICH:
        chu_dich = rng.sample(chu_dich, SO_CHU_DICH)

    mau = [{**ds[i], "lo": lo, "mau": "ngau_nhien"} for i, lo in zip(chon, cac_lo)]
    mau += [{**ds[i], "lo": "CD", "mau": "chu_dich"} for i in chu_dich]
    for k, m in enumerate(mau, start=1):
        m["stt"] = k

    if xuat_lo:
        dong = [m for m in mau if m["lo"] == xuat_lo]
        if xuat_lo == "D2":
            dong = dong[:SO_D2]
        if not dong:
            raise SystemExit(f"Không có lô {xuat_lo!r}")
        p = RA / f"phieu_lo_{xuat_lo}.csv"
        if not ghi_de and giu_phieu_cu(p, dong):
            return {"xuat_lo": xuat_lo, "so_dong": len(dong), "file": str(p), "ghi": "giữ file cũ: đã có người điền, mẫu khớp"}
        _ghi_csv(p, {"K": COT_PHIEU_NHAN, "D2": COT_PHIEU_D2}.get(xuat_lo, COT_PHIEU), [_che_ten(m) for m in dong])
        return {"xuat_lo": xuat_lo, "so_dong": len(dong), "file": str(p)}

    phieu = RA / "phieu_ma_hoa_mo.csv"
    dong_phieu = [m for m in mau if m["lo"] in LO_MA_HOA_MO or m["lo"] == "CD"]
    giu = not ghi_de and giu_phieu_cu(phieu, dong_phieu)   # kiểm trước khi ghi bất cứ file nào
    _ghi_csv(RA / "mau.csv", COT_MAU, mau)
    if not giu:
        _ghi_csv(phieu, COT_PHIEU, [_che_ten(m) for m in dong_phieu])
    manifest = {
        "chay_luc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "nguon": {"file": RAW.relative_to(GOC).as_posix(), "sha256": _sha256(RAW)},
        "so_binh_luan_co_noi_dung": len(ds),
        "so_binh_luan_rong_bi_bo": rong,
        "so_luong_theo_lo": dict(Counter(m["lo"] for m in mau)),
        "kenh_lon": kenh_lon,
        "tu_khoa_chu_dich": {"so_binh_luan_khop": dem_tu_khoa, "so_lay": len(chu_dich)},
        "phieu_xuat": ["giữ phieu_ma_hoa_mo.csv cũ: đã có người điền, mẫu chạy lại khớp" if giu
                       else "phieu_ma_hoa_mo.csv (lô 1–5 và CD)"],
    }
    (RA / "mau.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Lấy mẫu khám phá nhãn (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 3)")
    p.add_argument("--xuat-lo", choices=("K", "D1", "D2"), help="chỉ dùng ở bước B6: xuất phiếu trống một lô")
    p.add_argument("--ghi-de", action="store_true", help="ghi đè cả phiếu đã có người điền (phần đã điền sẽ mất)")
    a = p.parse_args(argv)
    kq = chay(a.xuat_lo, a.ghi_de)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

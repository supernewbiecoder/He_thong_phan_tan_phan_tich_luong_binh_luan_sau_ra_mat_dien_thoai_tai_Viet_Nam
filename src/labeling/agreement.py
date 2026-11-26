"""Mục đích: Đồng thuận mã hóa mở giữa người mã A (Claude) và người kiểm B: xuất phiếu trống cho B, tính kappa theo hành vi, xuất bình luận lệch (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 7d); cập nhật lần cuối: 2026-11-23.

Chạy từ gốc repo:
    python -m src.labeling.agreement xuat      # data/kham-pha/phieu_ma_hoa_mo_B.csv: cùng dòng, không có mã của A
    python -m src.labeling.agreement so-sanh   # dong_thuan_ma_hoa_mo.csv, lech_ma_hoa_mo.csv

Kappa chỉ tính trên hành vi (danh sách đóng). Đối tượng là chữ tự do nên chỉ đưa vào danh sách lệch để bàn.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import stats as T
from .code_stats import tach_ma
from .sample import COT_NGUOI, COT_PHIEU, RA, _ghi_csv, da_co_nguoi_dien, doc_csv

PHIEU_A = RA / "phieu_ma_hoa_mo.csv"
PHIEU_B = RA / "phieu_ma_hoa_mo_B.csv"
KQ = RA / "dong_thuan_ma_hoa_mo.csv"
LECH = RA / "lech_ma_hoa_mo.csv"


def xuat_phieu_trong(nguon: Path = PHIEU_A, ra: Path = PHIEU_B, ghi_de: bool = False) -> int:
    """Chép phiếu của A, xóa trắng các cột người điền. Không ghi đè phiếu B đã có người điền."""
    if ra.exists() and not ghi_de and da_co_nguoi_dien(doc_csv(ra), set(COT_PHIEU) - set(COT_NGUOI)):
        raise SystemExit(f"{ra.name} đã có người điền; không ghi đè. Thêm --ghi-de nếu thật sự muốn (phần đã điền sẽ mất).")
    dong = [{**d, **{c: "" for c in COT_NGUOI}} for d in doc_csv(nguon)]
    _ghi_csv(ra, COT_PHIEU, dong)
    return len(dong)


def _hanh_vi(o: str) -> set[str]:
    return {m["hanh_vi"] for m in tach_ma(o)}


def dong_thuan_hanh_vi(dong_a: list[dict], dong_b: list[dict]) -> tuple[list[dict], list[dict]]:
    """So theo comment_id trên các bình luận B đã mã. Trả (bảng theo hành vi, các cặp dòng lệch hành vi)."""
    a = {d["comment_id"]: d for d in dong_a}
    cap = [(a[d["comment_id"]], d) for d in dong_b
           if (d.get("ma_tu_do") or "").strip() and d["comment_id"] in a and (a[d["comment_id"]].get("ma_tu_do") or "").strip()]
    hv_a = [_hanh_vi(x["ma_tu_do"]) for x, _ in cap]
    hv_b = [_hanh_vi(y["ma_tu_do"]) for _, y in cap]
    bang = []
    for h in sorted(set().union(*hv_a, *hv_b)) if cap else []:
        ca, cb = [h in s for s in hv_a], [h in s for s in hv_b]
        bang.append({
            "hanh_vi": h, "n": len(cap), "a_gan": sum(ca), "b_gan": sum(cb),
            "ca_hai": sum(x and y for x, y in zip(ca, cb)),
            "dong_y_tho": round(sum(x == y for x, y in zip(ca, cb)) / len(cap), 3),
            "kappa": round(T.kappa(ca, cb), 3),
            "dong_y_duong": None if (d := T.dong_y_duong(ca, cb)) is None else round(d, 3),
        })
    # Chữ bình luận lấy từ phiếu A (code ghi): phiếu B qua tay người, Excel có thể đổi ô ('+…' thành '#NAME?').
    lech = [{"stt": x["stt"], "lo": x["lo"], "binh_luan": x["binh_luan"], "ma_A": x["ma_tu_do"], "ma_B": y["ma_tu_do"],
             "chi_A": "; ".join(sorted(sa - sb)), "chi_B": "; ".join(sorted(sb - sa))}
            for (x, y), sa, sb in zip(cap, hv_a, hv_b) if sa != sb]
    return bang, lech


def so_sanh(phieu_a: Path = PHIEU_A, phieu_b: Path = PHIEU_B) -> dict:
    bang, lech = dong_thuan_hanh_vi(doc_csv(phieu_a), doc_csv(phieu_b))
    if not bang:
        raise SystemExit(f"{phieu_b.name} chưa có bình luận nào được mã.")
    _ghi_csv(KQ, tuple(bang[0]), bang)
    _ghi_csv(LECH, ("stt", "lo", "binh_luan", "ma_A", "ma_B", "chi_A", "chi_B"), lech)
    return {"so_binh_luan_so": bang[0]["n"], "so_binh_luan_lech_hanh_vi": len(lech), "file": [str(KQ), str(LECH)]}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Đồng thuận mã hóa mở (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 7d)")
    p.add_argument("viec", choices=("xuat", "so-sanh"))
    p.add_argument("--ghi-de", action="store_true", help="xuat: ghi đè phiếu B đã có người điền")
    a = p.parse_args(argv)
    kq = {"so_dong": xuat_phieu_trong(ghi_de=a.ghi_de), "file": str(PHIEU_B)} if a.viec == "xuat" else so_sanh()
    sys.stdout.reconfigure(encoding="utf-8")
    print(kq)


if __name__ == "__main__":
    main()

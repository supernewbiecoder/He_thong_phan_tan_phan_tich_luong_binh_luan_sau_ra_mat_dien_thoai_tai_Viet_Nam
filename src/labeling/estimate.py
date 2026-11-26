"""Mục đích: Từ nhãn người của mẫu A, ước lượng cho cả dữ liệu tỷ lệ spam, không phải tiếng Việt, từng loại "liên quan", có nhãn chiều 2, kèm khoảng tin cậy; và đo precision, recall của luật gắn cờ spam và luật tiếng Việt (src/processing/flags.py) (docs/3-gan-nhan/dac-ta.md mục 3; Công việc 11); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo, sau `python -m src.labeling.check_sheet gop`:
    python -m src.labeling.estimate      # ghi data/labels/uoc_luong_mau_a.json

Nhãn spam thật = mục đích có `quang_cao` (bộ nhãn chốt gộp lừa đảo, cờ bạc vào đây). Luật nói spam = cờ `is_spam`
lúc lấy mẫu (ghi trong mau_a.jsonl). Không dùng accuracy: spam hiếm.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from . import final_labels as FL
from .sheet import RA
from .weighted_metrics import bootstrap_ci, cluster_resamples, prf, recall_lower_bound, stratum_weights

Z95 = 1.96
SO_LAN_BOOTSTRAP = 2000
SEED = 20261120


def doc_jsonl(p: Path) -> list[dict]:
    with open(p, encoding="utf-8") as f:
        return [json.loads(d) for d in f if d.strip()]


def ghep(mau: list[dict], nhan: list[dict]) -> list[dict]:
    """Dòng mẫu A có nhãn chuẩn, kèm các đại lượng 0/1 cần ước lượng."""
    theo_id = {x["comment_id"]: x for x in nhan}
    ra = []
    for r in mau:
        x = theo_id.get(r["comment_id"])
        if x is None:
            continue
        ra.append({**r, "spam": FL.SPAM_PURPOSE in x["muc_dich"], "ngoai_ngu": not x["tieng_viet"],
                   "lien_quan": x["lien_quan"], "co_nhan_chieu_2": bool(x["noi_ve"]),
                   "luat_spam": bool(r["is_spam"]), "luat_ngoai_ngu": r["is_vietnamese"] is False})
    return ra


def ty_le(dong: list[dict], cot: str, tong_the: dict[str, int]) -> dict:
    """p̂ = Σ W_h p̂_h, phương sai có hiệu chỉnh tổng thể hữu hạn (đặc tả mục 3). Tầng có p̂_h bằng 0 hay 1, hay
    dưới 5 ca, thì khoảng tin cậy lấy bằng bootstrap trong tầng (theo cụm video), không dùng công thức xấp xỉ."""
    N = sum(tong_the.values())
    p_hat = var = 0.0
    can_bootstrap = False
    theo_tang = {}
    for t, N_h in tong_the.items():
        ds = [r[cot] for r in dong if r["tang"] == t]
        n_h = len(ds)
        if not n_h:
            continue
        p_h = sum(ds) / n_h
        W = N_h / N
        p_hat += W * p_h
        var += W ** 2 * p_h * (1 - p_h) / n_h * (1 - n_h / N_h if N_h else 0)
        can_bootstrap |= p_h in (0.0, 1.0) or sum(ds) < 5
        theo_tang[t] = {"n_h": n_h, "N_h": N_h, "so_ca": sum(ds), "ty_le": p_h}
    if can_bootstrap:
        tang = [r["tang"] for r in dong]
        gia_tri = np.array([r[cot] for r in dong], dtype=float)
        rut = [float(np.sum(w * gia_tri[i]) / np.sum(w))
               for i, w in cluster_resamples(tang, tong_the, [r["video_id"] for r in dong], SO_LAN_BOOTSTRAP, SEED)]
        ktc, cach = [float(np.percentile(rut, 2.5)), float(np.percentile(rut, 97.5))], "bootstrap phân tầng theo video"
    else:
        nua = Z95 * math.sqrt(var)
        ktc, cach = [max(0.0, p_hat - nua), min(1.0, p_hat + nua)], "công thức phân tầng"
    return {"uoc_luong": p_hat, "ktc95": ktc, "cach_tinh_ktc": cach, "so_binh_luan_uoc_luong": p_hat * N,
            "so_binh_luan_ktc95": [ktc[0] * N, ktc[1] * N], "theo_tang": theo_tang}


def do_luat(dong: list[dict], that: str, luat: str, tong_the: dict[str, int]) -> dict:
    """Precision, recall của một luật gắn cờ, quy về cả dữ liệu bằng trọng số tầng; kèm cận recall xấu nhất."""
    y = [int(r[that]) for r in dong]
    yhat = [int(r[luat]) for r in dong]
    tang = [r["tang"] for r in dong]
    return {"tren_mau": prf(y, yhat),
            "quy_ve_ca_du_lieu": prf(y, yhat, stratum_weights(tang, tong_the)),
            "ktc95": bootstrap_ci(y, yhat, tang, tong_the, clusters=[r["video_id"] for r in dong],
                                  n_boot=SO_LAN_BOOTSTRAP, seed=SEED),
            "recall_can_duoi": recall_lower_bound(y, yhat, tang, tong_the)}


def uoc_luong(mau: list[dict], nhan: list[dict]) -> dict:
    tong_the = {}
    for r in mau:
        tong_the[r["tang"]] = r["N_h"]
    dong = ghep(mau, nhan)
    if not dong:
        raise SystemExit("Chưa có bình luận mẫu A nào có nhãn chuẩn. Chạy python -m src.labeling.check_sheet gop trước.")
    for t in FL.RELEVANCE:
        for r in dong:
            r[f"lq_{t}"] = r["lien_quan"] == t
    return {
        "so_binh_luan_mau_a": len(mau), "so_co_nhan": len(dong),
        "chua_du_nhan": len(dong) < len(mau),
        "ty_le": {"spam": ty_le(dong, "spam", tong_the), "khong_phai_tieng_viet": ty_le(dong, "ngoai_ngu", tong_the),
                  "co_nhan_chieu_2": ty_le(dong, "co_nhan_chieu_2", tong_the),
                  **{f"lien_quan_{t}": ty_le(dong, f"lq_{t}", tong_the) for t in FL.RELEVANCE}},
        "luat_spam": do_luat(dong, "spam", "luat_spam", tong_the),
        "luat_tieng_viet": do_luat(dong, "ngoai_ngu", "luat_ngoai_ngu", tong_the),
        "ghi_chu": ["Spam thật = muc_dich có quang_cao; luật = is_spam của src/processing/flags.py lúc lấy mẫu.",
                    "Tầng không thấy ca dương nào vẫn có thể có: xem recall_can_duoi và khoảng tin cậy rộng."],
    }


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Ước lượng từ nhãn mẫu A và đo luật gắn cờ")
    p.add_argument("--ra", type=Path, default=RA / "uoc_luong_mau_a.json")
    a = p.parse_args(argv)
    kq = uoc_luong(doc_jsonl(RA / "mau_a.jsonl"), doc_jsonl(RA / "nhan_binh_luan.jsonl"))
    a.ra.write_text(json.dumps(kq, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({k: kq[k] for k in ("so_binh_luan_mau_a", "so_co_nhan")} |
                     {"spam": kq["ty_le"]["spam"]["uoc_luong"],
                      "precision_luat_spam": kq["luat_spam"]["quy_ve_ca_du_lieu"]["precision"],
                      "recall_luat_spam": kq["luat_spam"]["quy_ve_ca_du_lieu"]["recall"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

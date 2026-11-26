"""Mục đích: So luật gắn cờ spam (src/processing/flags.py) với mô hình ML trên nhãn người của mẫu A, theo đề bài Công việc 11: chọn mô hình bằng cross-validation trên video train, chấm MỘT lần trên video test, báo precision, recall có trọng số tầng (docs/4-mo-hinh/dac-ta-spam.md); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo, sau khi gộp nhãn (python -m src.labeling.check_sheet gop):
    python -m src.models.spam.train

Ghi data/labels/spam_ml_eval.json và mô hình artifacts/spam/spam-ml.joblib (không vào git).
Chia train/test theo video_id: dùng data/labels/split.json (Công việc 7, trường "test_video_ids") nếu có; chưa có thì
tạm chia bằng băm video_id (25% video vào test) và ghi rõ điều đó trong kết quả.
Spam hiếm: chưa đủ MIN_SPAM_TRAIN ca spam trong video train thì dừng, không huấn luyện.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from src.labeling.estimate import doc_jsonl, ghep
from src.labeling.sheet import RA, VAO
from src.labeling.weighted_metrics import average_precision, bootstrap_ci, f_beta, mcnemar_exact, prf, stratum_weights

from .model import SEED, build_candidates, scores

GOC = Path(__file__).resolve().parents[3]
SPLIT = RA / "split.json"
MO_HINH = GOC / "artifacts" / "spam" / "spam-ml.joblib"
KET_QUA = RA / "spam_ml_eval.json"
MIN_SPAM_TRAIN = 20
TY_LE_TEST_TAM = 0.25


def video_test(video_ids: set[str]) -> tuple[set[str], str]:
    if SPLIT.exists():
        test = set(json.loads(SPLIT.read_text(encoding="utf-8"))["test_video_ids"])
        return test & video_ids, f"{SPLIT.relative_to(GOC).as_posix()} (Công việc 7)"
    test = {v for v in video_ids
            if int(hashlib.sha256(f"spam-split|{v}".encode()).hexdigest(), 16) % 1000 < TY_LE_TEST_TAM * 1000}
    return test, f"tạm: băm video_id, {TY_LE_TEST_TAM:.0%} video vào test (chưa có split.json của Công việc 7)"


def doc_chu(vao: Path, can: set[str]) -> dict[str, str]:
    chu = {}
    with open(vao, encoding="utf-8") as f:
        for d in f:
            if d.strip():
                r = json.loads(d)
                if r.get("comment_id") in can:
                    chu[r["comment_id"]] = r.get("text_clean") or ""
    return chu


def nguong_tot(y, diem, w, cong=None) -> float:
    """Ngưỡng cho F0,5 có trọng số cao nhất (ưu tiên precision); hòa thì lấy ngưỡng cao hơn."""
    ung_vien = sorted(set(diem.tolist()))
    tot = (-1.0, ung_vien[-1] if ung_vien else 0.0)
    for t in ung_vien:
        du_doan = (diem >= t) if cong is None else ((diem >= t) & cong)
        r = prf(y, du_doan, w)
        v = f_beta(r["precision"], r["recall"], 0.5)
        if v >= tot[0]:
            tot = (v, float(t))
    return tot[1]


def mo_ta(y, du_doan, tang, tong_the, video) -> dict:
    return {"tren_mau": prf(y, du_doan), "quy_ve_ca_du_lieu": prf(y, du_doan, stratum_weights(tang, tong_the)),
            "ktc95": bootstrap_ci(y, du_doan, tang, tong_the, clusters=video, n_boot=2000, seed=SEED)}


def chay(vao: Path = VAO) -> dict:
    from sklearn.base import clone
    from sklearn.model_selection import StratifiedGroupKFold

    mau, nhan = doc_jsonl(RA / "mau_a.jsonl"), doc_jsonl(RA / "nhan_binh_luan.jsonl")
    dong = ghep(mau, nhan)
    tong_the = {r["tang"]: r["N_h"] for r in mau}
    test_v, cach_chia = video_test({r["video_id"] for r in dong})
    chu = doc_chu(vao, {r["comment_id"] for r in dong})
    train = [r for r in dong if r["video_id"] not in test_v]
    test = [r for r in dong if r["video_id"] in test_v]
    so_spam_train = sum(r["spam"] for r in train)
    if so_spam_train < MIN_SPAM_TRAIN:
        raise SystemExit(f"Chỉ có {so_spam_train} bình luận spam (nhãn người) trong video train, cần ít nhất "
                         f"{MIN_SPAM_TRAIN}. Chưa huấn luyện; báo cáo luật bằng python -m src.labeling.estimate.")

    def mang(ds):
        return ([chu.get(r["comment_id"], "") for r in ds], np.array([int(r["spam"]) for r in ds]),
                [r["tang"] for r in ds], [r["video_id"] for r in ds], np.array([int(r["luat_spam"]) for r in ds]))

    X, y, tang, video, luat = mang(train)
    w = stratum_weights(tang, tong_the)
    so_phan = max(2, min(5, int(y.sum())))
    cv = StratifiedGroupKFold(n_splits=so_phan, shuffle=True, random_state=SEED)
    chon = {}
    for ten, mo_hinh in build_candidates().items():
        diem = np.zeros(len(y))
        for tr, te in cv.split(X, y, groups=video):
            m = clone(mo_hinh).fit([X[i] for i in tr], y[tr])
            diem[te] = scores(m, [X[i] for i in te])
        chon[ten] = {"ap_cv": average_precision(y, diem, w), "diem": diem}
    ten_tot = max(chon, key=lambda k: chon[k]["ap_cv"] or -1)
    nguong_ml = nguong_tot(y, chon[ten_tot]["diem"], w)
    nguong_kh = nguong_tot(y, chon[ten_tot]["diem"], w, cong=luat.astype(bool))
    mo_hinh = clone(build_candidates()[ten_tot]).fit(X, y)

    Xt, yt, tang_t, video_t, luat_t = mang(test)
    diem_t = scores(mo_hinh, Xt)
    ml_t = (diem_t >= nguong_ml).astype(int)
    kh_t = ((diem_t >= nguong_kh) & luat_t.astype(bool)).astype(int)
    import joblib

    MO_HINH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": mo_hinh, "threshold": nguong_ml, "hybrid_threshold": nguong_kh, "name": ten_tot}, MO_HINH)
    kq = {
        "cach_chia_train_test": cach_chia, "so_train": len(train), "so_test": len(test),
        "so_spam_train": int(y.sum()), "so_spam_test": int(yt.sum()),
        "chon_mo_hinh_cv": {k: v["ap_cv"] for k, v in chon.items()}, "mo_hinh_chon": ten_tot,
        "nguong_ml": nguong_ml, "nguong_ket_hop": nguong_kh,
        "test": {"luat_flags": mo_ta(yt, luat_t, tang_t, tong_the, video_t),
                 "ml": mo_ta(yt, ml_t, tang_t, tong_the, video_t),
                 "ket_hop_luat_va_ml": mo_ta(yt, kh_t, tang_t, tong_the, video_t),
                 "mcnemar_luat_vs_ml": mcnemar_exact(yt, luat_t, ml_t)},
        "mo_hinh_file": MO_HINH.relative_to(GOC).as_posix(),
        "ghi_chu": "Chỉ số 'quy_ve_ca_du_lieu' dùng trọng số tầng N_h/n_h của mẫu A; không dùng accuracy.",
    }
    KET_QUA.write_text(json.dumps(kq, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return kq


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="So luật gắn cờ spam với mô hình ML trên nhãn mẫu A").parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    kq = chay()
    print(json.dumps({k: kq[k] for k in ("mo_hinh_chon", "so_train", "so_test", "cach_chia_train_test")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

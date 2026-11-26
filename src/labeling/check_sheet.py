"""Mục đích: Kiểm phiếu gán nhãn theo bộ nhãn chốt (cú pháp, luật tự kiểm ở hướng dẫn gán chính thức mục 10), rồi gộp các phiếu mẫu A và hiệu chỉnh thành nhãn chuẩn mỗi bình luận một dòng, đưa ca lệch vào sổ phân xử và tính đồng thuận (docs/3-gan-nhan/dac-ta.md mục 7, 8); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo:
    python -m src.labeling.check_sheet kiem data/labels/phieu/mau_a_n01.xlsx   # in lỗi từng dòng, không ghi gì
    python -m src.labeling.check_sheet gop                                     # mọi phiếu trong data/labels/phieu/

`gop` ghi data/labels/nhan_binh_luan.jsonl (nhãn chuẩn), data/labels/so_phan_xu.csv (ca lệch: người thứ ba điền
các cột `px_*` rồi chạy lại `gop`), data/labels/dong_thuan.json (đồng ý thô, kappa từng chiều).
Phiếu đọc được cả .csv (UTF-8) lẫn .xlsx; có cả hai thì dùng .xlsx.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from src.models.target_model import doc_danh_muc

from . import final_labels as FL
from . import stats as T
from .sample import GOC, _ghi_csv, doc_csv
from .sheet import COT_NGUOI, DANH_MUC, PHIEU, RA

CHIEU_SO = {"1": "lien_quan", "2": "noi_ve_thai_do", "3": "muc_dich", "4": "noi_ve_thai_do", "5": "da_dung",
            "6": "may_nhac"}
# Phần chiều 2 viết tắt: "cam+-", "pin-@ip15prm", "pin=@s24u>ip15prm", "pin=@s24u~ip15prm"; hay tên đầy đủ "camera:tich_cuc@s24u"
PHAN_TAT = re.compile(r"^([a-z_]+)\s*([-+=0]+)\s*(?:@\s*([a-z0-9_]+)\s*(?:([>~])\s*([a-z0-9_]+))?)?$")
PHAN_DAY = re.compile(r"^([a-z_]+)\s*:\s*([a-z_+]+)\s*(?:@\s*([a-z0-9_]+)\s*(?:([>~])\s*([a-z0-9_]+))?)?$")


class LoiPhieu(ValueError):
    """Một dòng phiếu sai luật; thông báo ghi rõ dòng và cột."""


def tach(o: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,]", o or "") if x.strip()]


def _mot(o: str, tat: dict, day: tuple, cot: str) -> str:
    x = (o or "").strip()
    for k in (x, x.lower(), x.upper()):
        if k in tat:
            return tat[k]
    if x.lower() in day:
        return x.lower()
    raise LoiPhieu(f"{cot}: '{o}' không phải nhãn hợp lệ")


def doc_phan(o: str, ten_may: list[str]) -> list[dict]:
    """Cột noi_ve_thai_do -> [{aspect, thai_do: [...], may, so_voi, ben_hon}]."""
    ra = []
    for x in tach(o):
        m = PHAN_TAT.match(x.lower())
        if m:
            phan = FL.ABBR_DIM2.get(m[1], m[1])
            thai_do = [FL.ABBR_ATTITUDE[c] for c in dict.fromkeys(m[2])]
        else:
            m = PHAN_DAY.match(x.lower())
            if not m:
                raise LoiPhieu(f"noi_ve_thai_do: không đọc được '{x}' (ví dụ đúng: cam+-, pin-@ip15prm, pin=@s24u>ip15prm)")
            phan = m[1]
            thai_do = [FL.ABBR_ATTITUDE.get(t, t) for t in m[2].split("+") if t]
        if phan not in FL.DIM2_LABELS:
            raise LoiPhieu(f"noi_ve_thai_do: '{m[1]}' không phải nhãn chiều 2")
        if any(t not in FL.ATTITUDES for t in thai_do) or not thai_do:
            raise LoiPhieu(f"noi_ve_thai_do: '{x}' thiếu hay sai ký hiệu thái độ (+ - = 0)")
        may, dau, khac = m[3], m[4], m[5]
        for ma in (may, khac):
            if ma and ma not in ten_may:
                raise LoiPhieu(f"noi_ve_thai_do: máy '@{ma}' phải có trong ten_may")
        if dau and "so_sanh" not in thai_do:
            raise LoiPhieu(f"noi_ve_thai_do: '{x}' có '{dau}' nhưng thái độ không phải so sánh (=)")
        ra.append({"aspect": phan, "thai_do": thai_do, "may": may,
                   "so_voi": khac, "ben_hon": None if not dau else ("ngang" if dau == "~" else may)})
    return ra


def doc_dong(d: dict, danh_muc: set[str]) -> tuple[dict, list[str]]:
    """Một dòng phiếu đã điền -> (nhãn chuẩn hóa, cảnh báo). Sai luật thì ném LoiPhieu."""
    canh_bao = []
    tv = (d.get("tieng_viet") or "").strip().lower()
    if tv not in FL.ABBR_VIETNAMESE:
        raise LoiPhieu("tieng_viet: phải là 'co' hoặc 'khong'")
    lq = _mot(d.get("lien_quan"), FL.ABBR_RELEVANCE, FL.RELEVANCE, "lien_quan")
    ten_may = [x.lower() for x in tach(d.get("ten_may"))]
    phan = doc_phan(d.get("noi_ve_thai_do"), ten_may)
    md = [_mot(x, FL.ABBR_PURPOSE, FL.PURPOSES, "muc_dich") for x in tach(d.get("muc_dich"))]
    dd = _mot(d.get("da_dung"), FL.ABBR_OWNER, FL.OWNER, "da_dung")
    mn = _mot(d.get("may_nhac"), FL.ABBR_MODEL_MENTION, FL.MODEL_MENTION, "may_nhac")
    if (lq == "dien_thoai") != bool(phan):
        raise LoiPhieu("lien_quan là D thì phải có noi_ve_thai_do; khác D thì để trống noi_ve_thai_do")
    if not md:
        raise LoiPhieu("muc_dich không được trống")
    if (mn == "goi_ten_may") != bool(ten_may):
        raise LoiPhieu("may_nhac là t thì phải ghi ten_may; khác t thì để trống ten_may")
    if len(ten_may) >= 2 and any(p["may"] is None for p in phan):
        raise LoiPhieu("gọi tên từ hai máy: mỗi phần ở noi_ve_thai_do phải ghi @mã máy")
    canh_bao += [f"ten_may '{m}' không có trong danh mục (được, nếu máy ngoài danh mục)" for m in ten_may
                 if m not in danh_muc]
    if "bao_loi" in md and dd != "co":
        canh_bao.append("có bao_loi mà da_dung không phải c: xem lại")
    chua_chac = sorted({CHIEU_SO[c] for c in re.findall(r"[1-6]", d.get("chua_chac") or "")})
    return {"tieng_viet": FL.ABBR_VIETNAMESE[tv], "lien_quan": lq, "noi_ve": phan, "muc_dich": sorted(set(md)),
            "da_dung": dd, "may_nhac": mn, "ten_may": sorted(set(ten_may)), "chua_chac": chua_chac,
            "ghi_chu": (d.get("ghi_chu") or "").strip()}, canh_bao


def doc_tep(p: Path) -> list[dict]:
    if p.suffix.lower() == ".xlsx":
        from openpyxl import load_workbook

        ws = load_workbook(p, read_only=True, data_only=True)["phieu"]
        hang = list(ws.iter_rows(values_only=True))
        cot = [str(c) for c in hang[0]]
        return [{c: ("" if v is None else str(v)) for c, v in zip(cot, h)} for h in hang[1:] if any(h)]
    return doc_csv(p)


def da_dien(d: dict) -> bool:
    return any((d.get(c) or "").strip() for c in COT_NGUOI if c not in ("nguoi_gan", "ghi_chu"))


def kiem(p: Path, danh_muc: set[str]) -> tuple[list[dict], list[str], list[str]]:
    """Trả (nhãn các dòng đã điền đúng, lỗi, cảnh báo). Dòng chưa điền bỏ qua."""
    nhan, loi, canh_bao = [], [], []
    for d in doc_tep(p):
        if not da_dien(d):
            continue
        noi = f"{p.name} stt {d.get('stt')}"
        try:
            x, cb = doc_dong(d, danh_muc)
        except LoiPhieu as e:
            loi.append(f"{noi}: {e}")
            continue
        if not (d.get("nguoi_gan") or "").strip():
            loi.append(f"{noi}: thiếu nguoi_gan")
            continue
        canh_bao += [f"{noi}: {c}" for c in cb]
        nhan.append({"stt": int(d["stt"]), "comment_id": d["comment_id"], "nguoi_gan": d["nguoi_gan"].strip(),
                     "phieu": p.name, **x})
    return nhan, loi, canh_bao


# ---------------------------------------------------------------- gộp, phân xử, đồng thuận

def khoa_so_sanh(x: dict) -> dict:
    """Phần nhãn dùng để so hai người (bỏ ghi chú, chưa chắc)."""
    return {"tieng_viet": x["tieng_viet"], "lien_quan": x["lien_quan"], "muc_dich": x["muc_dich"],
            "da_dung": x["da_dung"], "may_nhac": x["may_nhac"], "ten_may": x["ten_may"],
            "noi_ve": sorted((p["aspect"], tuple(sorted(p["thai_do"])), p["may"] or "", p["so_voi"] or "",
                              p["ben_hon"] or "") for p in x["noi_ve"])}


COT_PX = ("stt", "comment_id", "binh_luan", "binh_luan_cha", "cac_ban_gan") + tuple(f"px_{c}" for c in COT_NGUOI[1:-2]) \
    + ("px_nguoi_phan_xu", "px_ghi_chu")


def dong_thuan(theo_bl: dict[str, list[dict]]) -> dict:
    """Đồng ý thô và kappa cho từng chiều, trên các bình luận có đúng hai người gán (bỏ đợt hiệu chỉnh)."""
    cap = [ds for ds in theo_bl.values() if len(ds) == 2]
    ra = {"so_binh_luan_gan_doi": len(cap)}
    if not cap:
        return ra
    for c in ("tieng_viet", "lien_quan", "da_dung", "may_nhac"):
        a, b = [ds[0][c] for ds in cap], [ds[1][c] for ds in cap]
        ra[c] = {"dong_y_tho": sum(x == y for x, y in zip(a, b)) / len(cap), "kappa": T.kappa(a, b)}
    spam_a = [FL.SPAM_PURPOSE in ds[0]["muc_dich"] for ds in cap]
    spam_b = [FL.SPAM_PURPOSE in ds[1]["muc_dich"] for ds in cap]
    ra["spam (muc_dich co quang_cao)"] = {"dong_y_tho": sum(x == y for x, y in zip(spam_a, spam_b)) / len(cap),
                                          "kappa": T.kappa(spam_a, spam_b), "dong_y_duong": T.dong_y_duong(spam_a, spam_b)}
    for nhan in FL.DIM2_LABELS:
        a = [any(p["aspect"] == nhan for p in ds[0]["noi_ve"]) for ds in cap]
        b = [any(p["aspect"] == nhan for p in ds[1]["noi_ve"]) for ds in cap]
        if any(a) or any(b):
            ra.setdefault("chieu_2", {})[nhan] = {"kappa": T.kappa(a, b), "dong_y_duong": T.dong_y_duong(a, b)}
    return ra


def gop(phieu: Path = PHIEU, ra: Path = RA, danh_muc: Path = DANH_MUC) -> dict:
    ma_may = set(doc_danh_muc(danh_muc))
    tep = {}
    for p in sorted(phieu.glob("*.csv")) + sorted(phieu.glob("*.xlsx")):
        if p.stem.startswith(("mau_a_", "hieu_chinh")):
            tep[p.stem] = p if p.suffix == ".xlsx" or p.stem not in tep else tep[p.stem]
    nhan, loi = [], []
    for p in tep.values():
        n, l, _ = kiem(p, ma_may)
        nhan += n
        loi += l
    if loi:
        raise SystemExit("Phiếu còn lỗi, chưa gộp. Sửa rồi chạy lại:\n" + "\n".join(loi[:50]))
    theo_bl: dict[str, list[dict]] = defaultdict(list)
    for x in nhan:
        theo_bl[x["comment_id"]].append(x)
    for cid, ds in theo_bl.items():
        ten = [x["nguoi_gan"] for x in ds]
        if len(ten) != len(set(ten)):
            raise SystemExit(f"{cid}: một người gán hai lần ({ten})")

    so_px = ra / "so_phan_xu.csv"
    px = {d["comment_id"]: d for d in doc_csv(so_px)} if so_px.exists() else {}
    chu = {}
    for p in tep.values():
        for d in doc_tep(p):
            chu.setdefault(d["comment_id"], d)
    chuan, lech = [], []
    for cid, ds in sorted(theo_bl.items(), key=lambda kv: kv[1][0]["stt"]):
        khoa = [json.dumps(khoa_so_sanh(x), sort_keys=True) for x in ds]
        if len(set(khoa)) == 1:
            chuan.append({**{k: v for k, v in ds[0].items() if k not in ("nguoi_gan", "phieu", "chua_chac", "ghi_chu")},
                          "annotator": sorted(x["nguoi_gan"] for x in ds), "label_source": "human",
                          "phan_xu": False})
            continue
        dong_px = px.get(cid)
        if dong_px and (dong_px.get("px_lien_quan") or "").strip():
            x, _ = doc_dong({c: dong_px.get(f"px_{c}", "") for c in COT_NGUOI}, ma_may)
            chuan.append({"stt": ds[0]["stt"], "comment_id": cid, **{k: v for k, v in x.items()
                                                                       if k not in ("chua_chac", "ghi_chu")},
                          "annotator": [dong_px.get("px_nguoi_phan_xu") or "phan_xu"], "label_source": "human",
                          "phan_xu": True})
            continue
        lech.append({"stt": ds[0]["stt"], "comment_id": cid, "binh_luan": chu[cid].get("binh_luan", ""),
                     "binh_luan_cha": chu[cid].get("binh_luan_cha", ""),
                     "cac_ban_gan": " || ".join(f"{x['nguoi_gan']}: {json.dumps(khoa_so_sanh(x), ensure_ascii=False)}"
                                                for x in ds)})
    _ghi_csv(so_px, COT_PX, lech + [d for d in px.values() if (d.get("px_lien_quan") or "").strip()])
    tam = ra / "nhan_binh_luan.jsonl.tam"
    with open(tam, "w", encoding="utf-8") as f:
        for x in chuan:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    os.replace(tam, ra / "nhan_binh_luan.jsonl")
    dt = dong_thuan({k: v for k, v in theo_bl.items() if not any(x["phieu"].startswith("hieu_chinh") for x in v)})
    (ra / "dong_thuan.json").write_text(json.dumps(dt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"so_binh_luan_co_nhan": len(theo_bl), "so_nhan_chuan": len(chuan), "so_ca_lech_chua_phan_xu": len(lech),
            "dong_thuan": dt}


def main(argv: list[str] | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Kiểm và gộp phiếu gán nhãn theo bộ nhãn chốt")
    sub = p.add_subparsers(dest="lenh", required=True)
    k = sub.add_parser("kiem", help="kiểm một hay nhiều phiếu, in lỗi, không ghi gì")
    k.add_argument("phieu", nargs="+", type=Path)
    sub.add_parser("gop", help="gộp mọi phiếu trong data/labels/phieu thành nhãn chuẩn")
    a = p.parse_args(argv)
    if a.lenh == "kiem":
        ma_may = set(doc_danh_muc(DANH_MUC))
        tong_loi = 0
        for tep in a.phieu:
            nhan, loi, canh_bao = kiem(tep, ma_may)
            print(f"{tep.name}: {len(nhan)} dòng đúng, {len(loi)} dòng lỗi, {len(canh_bao)} cảnh báo")
            for x in loi + [f"(cảnh báo) {c}" for c in canh_bao]:
                print("  " + x)
            tong_loi += len(loi)
        sys.exit(1 if tong_loi else 0)
    print(json.dumps(gop(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Mục đích: Lấy mẫu A (chất lượng dữ liệu, đo luật gắn cờ spam và tiếng Việt) và đợt hiệu chỉnh 50 bình luận, rồi xuất phiếu gán nhãn theo bộ nhãn chốt cho từng người (CSV và Excel có danh sách thả xuống), kèm danh sách nhãn và danh mục máy (docs/3-gan-nhan/dac-ta.md mục 3, 5, 6; huong-dan-gan-nhan-chinh-thuc.md mục 10); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo, sau tầng 2 (data/processed/comments.jsonl):
    python -m src.labeling.sheet                     # 11 người, mã n01…n11
    python -m src.labeling.sheet --nguoi an,binh,…   # mã người gán tự đặt (không dùng tên thật)
    python -m src.labeling.sheet --ghi-de            # chỉ khi thật sự muốn lấy mẫu lại: phần đã điền sẽ mất

Đầu ra trong data/labels/ (không vào git, chia sẻ qua kho chung của nhóm):
    mau_a.jsonl, mau_a.manifest.json        danh sách bình luận được chọn, tầng, trọng số, ai gán; seed, SHA-256 nguồn
    phieu/hieu_chinh_50.csv|.xlsx           50 bình luận cả nhóm cùng gán (đo kappa trước khi gán thật)
    phieu/mau_a_<người>.csv|.xlsx           phần mẫu A của từng người
    phieu/danh_sach_nhan.csv, danh_muc_may.csv

Phiếu không có tầng, trọng số hay cờ của luật, để người gán không bị dẫn dắt; các cột đó chỉ nằm trong mau_a.jsonl.
Phiếu không có author_name, author_hash; tên người được nhắc (@tên) đã che.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.models.target_model import doc_danh_muc

from . import final_labels as FL
from .light_clean import an_nhac_ten
from .sample import GOC, _ghi_csv, _sha256, da_co_nguoi_dien, doc_csv

VAO = GOC / "data" / "processed" / "comments.jsonl"
DANH_MUC = GOC / "config" / "pipeline.yaml"
RA = GOC / "data" / "labels"
PHIEU = RA / "phieu"

SEED = 20261120                               # đặc tả gán nhãn mục 3
CO_TANG = {"A1": 150, "A2": 100, "A3": 600}   # A1 luật gắn spam; A2 không spam, luật gắn ngoại ngữ; A3 còn lại
SO_GAN_DOI = 200
SO_HIEU_CHINH = 50
TANG_HIEU_CHINH = {"A1": 10, "A2": 5, "A3": 35}
CAT_CHA = 600

COT_CODE = ("stt", "comment_id", "video_id", "may_video", "la_reply", "binh_luan", "binh_luan_cha")
COT_NGUOI = ("nguoi_gan", "tieng_viet", "lien_quan", "noi_ve_thai_do", "muc_dich", "da_dung", "may_nhac", "ten_may",
             "chua_chac", "ghi_chu")
COT_PHIEU = COT_CODE + COT_NGUOI

# Gợi ý ngắn cho từng nhãn chiều 2 (hướng dẫn gán chính thức mục 2; định nghĩa đầy đủ ở đặc tả bộ nhãn)
GOM = {
    "pin_sac": "pin, thời lượng, tụt pin, sạc, củ sạc",
    "man_hinh": "màn hình, tần số quét, độ sáng, tai thỏ, lỗ khoét, lỗi màn",
    "hieu_nang": "chip, RAM, điểm số, game, độ mượt, đa nhiệm, nóng máy, tản nhiệt",
    "camera": "chụp, quay, zoom, chống rung, màu ảnh, app camera",
    "thiet_ke": "ngoại hình, màu máy, chất liệu, trọng lượng, kích thước; máy đẹp, xấu nói chung",
    "do_ben": "độ bền, rơi vỡ, chống nước, bung, nứt",
    "phan_mem": "hệ điều hành, giao diện, cập nhật, ứng dụng, AI, thông báo",
    "phan_cung_khac": "bộ nhớ, SIM, 5G, wifi, vân tay, Face ID, bút, cổng, loa, mic, phụ kiện",
    "gia": "giá bán, giá về Việt Nam, giữ giá, rớt giá, khuyến mãi",
    "mua_ban": "mua ở đâu, khi nào, trả góp, xách tay, bán máy cũ, lên đời, ý định mua",
    "bao_hanh_sua_chua": "bảo hành, sửa chữa, thay linh kiện, đổi trả",
    "may_chung": "cả máy, không nêu phần nào ('ngon', 'đỉnh'); máy nên mua; đời mới nâng cấp gì",
    "hang_nguoi_dung": "hãng, thương hiệu, fan, nhóm người mua",
    "khac": "phần của máy chưa có ở trên (rất hiếm; ghi rõ ở ghi_chu)",
}
TEN_CHIEU_1 = {"dien_thoai": "điện thoại", "ngu_canh": "video, kênh, người review, minigame",
               "nguoi_binh_luan": "chỉ nói với/về người bình luận khác", "khong_lien_quan": "chính trị, chuyện đời; máy tính bảng",
               "khong_xac_dinh": "không biết nói về cái gì; chỉ emoji, tiếng cười"}
TEN_MUC_DICH = {"danh_gia": "khen, chê, nhận xét, so sánh, dự đoán", "hoi": "hỏi, xin link",
                "thong_tin": "giải thích, trả lời, nhắc", "de_nghi": "khuyên, góp ý, yêu cầu, thách người review",
                "ban_than": "kể, khoe, than, mong muốn, định mua", "bao_loi": "lỗi máy của mình hay người nhà",
                "tranh_luan": "đồng ý, phản bác (phải có chữ tỏ thái độ)", "dua": "cố ý gây cười",
                "cong_kich": "cà khịa, chửi", "minigame": "dự thi, xin quà",
                "quang_cao": "quảng cáo, mời liên hệ, lừa đảo, cờ bạc (= spam)", "xa_giao": "chào, cảm ơn, chỉ cười",
                "khong_xac_dinh": "không hiểu viết để làm gì"}


# ---------------------------------------------------------------- lấy mẫu

def doc_khung(vao: Path) -> tuple[list[dict], int]:
    """Khung mẫu A: mọi bình luận tầng 2 có text_clean khác rỗng. Trả (bình luận, số bình luận rỗng)."""
    khung, rong = [], 0
    with open(vao, encoding="utf-8") as f:
        for dong in f:
            if not dong.strip():
                continue
            r = json.loads(dong)
            if not (r.get("text_clean") or "").strip():
                rong += 1
                continue
            khung.append({k: r.get(k) for k in ("comment_id", "video_id", "model", "parent_id", "parent_text",
                                                 "text_clean", "is_spam", "is_vietnamese", "spam_reasons")})
    return khung, rong


def tang_cua(r: dict) -> str:
    if r.get("is_spam"):
        return "A1"
    if r.get("is_vietnamese") is False:
        return "A2"
    return "A3"


def lay_mau(khung: list[dict], seed: int = SEED, co_tang: dict = CO_TANG) -> list[dict]:
    """Ngẫu nhiên đơn trong từng tầng; tầng ít hơn cỡ mẫu thì lấy hết. Mỗi dòng mang N_h, n_h, trọng số N_h/n_h."""
    rng = random.Random(seed)
    theo_tang: dict[str, list[dict]] = {t: [] for t in co_tang}
    for r in sorted(khung, key=lambda x: x["comment_id"]):   # thứ tự cố định, không phụ thuộc thứ tự file
        theo_tang[tang_cua(r)].append(r)
    mau = []
    for t, ds in theo_tang.items():
        chon = ds if len(ds) <= co_tang[t] else rng.sample(ds, co_tang[t])
        for r in sorted(chon, key=lambda x: x["comment_id"]):
            mau.append({**r, "tang": t, "N_h": len(ds), "n_h": len(chon),
                        "trong_so": len(ds) / len(chon) if chon else None})
    return mau


def chia_viec(mau: list[dict], nguoi: list[str], seed: int = SEED, so_gan_doi: int = SO_GAN_DOI,
              so_hieu_chinh: int = SO_HIEU_CHINH) -> None:
    """Gắn vào từng dòng: hieu_chinh (cả nhóm gán), gan_doi, nguoi_gan (danh sách). Ghi thẳng vào `mau`.

    Hiệu chỉnh lấy theo TANG_HIEU_CHINH (có cả spam, ngoại ngữ) và không vào phiếu riêng: nhãn của đợt đó dùng luôn.
    Gán đôi lấy ngẫu nhiên, tỷ lệ theo tầng, trong phần còn lại. Hai người gán của một dòng luôn khác nhau.
    """
    if len(nguoi) < 2:
        raise ValueError("cần ít nhất 2 người gán để gán đôi")
    rng = random.Random(seed + 1)
    for r in mau:
        r.update(hieu_chinh=False, gan_doi=False, nguoi_gan=[])
    can = {t: round(so_hieu_chinh * n / SO_HIEU_CHINH) for t, n in TANG_HIEU_CHINH.items()}
    for t, n in can.items():
        ds = [r for r in mau if r["tang"] == t]
        for r in rng.sample(ds, min(n, len(ds))):
            r["hieu_chinh"] = True
    con = [r for r in mau if not r["hieu_chinh"]]
    ti_le = so_gan_doi / len(con) if con else 0
    for t in sorted({r["tang"] for r in con}):
        ds = [r for r in con if r["tang"] == t]
        for r in rng.sample(ds, min(len(ds), round(ti_le * len(ds)))):
            r["gan_doi"] = True
    rng.shuffle(con)
    tai = Counter({n: 0 for n in nguoi})
    for r in sorted(con, key=lambda x: not x["gan_doi"]):   # chia dòng gán đôi trước để cân tải
        so = 2 if r["gan_doi"] else 1
        chon = sorted(nguoi, key=lambda n: (tai[n], rng.random()))[:so]
        r["nguoi_gan"] = chon
        tai.update(chon)


def dong_phieu(r: dict) -> dict:
    cha = an_nhac_ten(r.get("parent_text") or "")
    return {"stt": r["stt"], "comment_id": r["comment_id"], "video_id": r["video_id"], "may_video": r["model"],
            "la_reply": "co" if r.get("parent_id") else "", "binh_luan": an_nhac_ten(r["text_clean"]),
            "binh_luan_cha": cha[:CAT_CHA] + ("…" if len(cha) > CAT_CHA else "")}


# ---------------------------------------------------------------- ghi phiếu

def danh_sach_nhan() -> list[dict]:
    ds = [{"cot": "tieng_viet", "viet_tat": k, "nhan": k, "y_nghia": "có phải tiếng Việt (gán đầu tiên)"}
          for k in FL.ABBR_VIETNAMESE]
    ds += [{"cot": "lien_quan", "viet_tat": k, "nhan": v, "y_nghia": TEN_CHIEU_1[v]} for k, v in FL.ABBR_RELEVANCE.items()]
    ds += [{"cot": "noi_ve_thai_do (phần)", "viet_tat": k, "nhan": v,
            "y_nghia": ("[khía cạnh] " if v in FL.ASPECTS else "") + GOM[v]} for k, v in FL.ABBR_DIM2.items()]
    ds += [{"cot": "noi_ve_thai_do (thái độ)", "viet_tat": k, "nhan": v, "y_nghia": FL.NAMES[v]}
           for k, v in FL.ABBR_ATTITUDE.items()]
    ds += [{"cot": "muc_dich", "viet_tat": k, "nhan": v, "y_nghia": TEN_MUC_DICH[v]} for k, v in FL.ABBR_PURPOSE.items()]
    ds += [{"cot": "da_dung", "viet_tat": "c", "nhan": "co", "y_nghia": "nói rõ là máy của mình hay người nhà"},
           {"cot": "da_dung", "viet_tat": "k", "nhan": "khong_ro", "y_nghia": "không nói rõ"}]
    ds += [{"cot": "may_nhac", "viet_tat": "t", "nhan": "goi_ten_may", "y_nghia": "tên máy kèm số đời; ghi ten_may"},
           {"cot": "may_nhac", "viet_tat": "h", "nhan": "chi_hang", "y_nghia": "chỉ hãng hay dòng, không có đời"},
           {"cot": "may_nhac", "viet_tat": "k", "nhan": "khong_nhac", "y_nghia": "không nhắc máy hay hãng"}]
    ds += [{"cot": "chua_chac", "viet_tat": "1-6", "nhan": "", "y_nghia": "số chiều còn phân vân, lý do ghi ở ghi_chu"},
           {"cot": "cách ghi", "viet_tat": "cam+-, gia0", "nhan": "", "y_nghia": "phần + thái độ, nhiều phần cách bằng dấu phẩy"},
           {"cot": "cách ghi", "viet_tat": "cam+@s24u, pin-@ip15prm", "nhan": "",
            "y_nghia": "từ hai máy trở lên: thêm @mã máy (mã phải có trong ten_may)"},
           {"cot": "cách ghi", "viet_tat": "pin=@s24u>ip15prm; pin=@s24u~ip15prm", "nhan": "",
            "y_nghia": "so sánh: máy hơn đứng trước '>'; ngang nhau dùng '~'"}]
    return ds


def danh_muc_may(danh_muc: Path = DANH_MUC) -> list[dict]:
    return [{"ma_may": ma, "ten": m.get("title") or ma, "ngay_ra_mat": m.get("launch_date") or ""}
            for ma, m in sorted(doc_danh_muc(danh_muc).items())]


def ghi_xlsx(p: Path, dong: list[dict], nhan: list[dict], may: list[dict]) -> None:
    """Phiếu Excel: trang 'phieu' có danh sách thả xuống; trang 'danh_sach_nhan', 'danh_muc_may' để tra."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "phieu"
    ws.append(list(COT_PHIEU))
    for d in dong:
        ws.append([d.get(c, "") for c in COT_PHIEU])
    rong = {"stt": 6, "comment_id": 14, "video_id": 12, "may_video": 12, "la_reply": 8, "binh_luan": 60,
            "binh_luan_cha": 40, "nguoi_gan": 10, "tieng_viet": 10, "lien_quan": 9, "noi_ve_thai_do": 24,
            "muc_dich": 14, "da_dung": 8, "may_nhac": 9, "ten_may": 16, "chua_chac": 9, "ghi_chu": 30}
    for i, c in enumerate(COT_PHIEU, start=1):
        chu = ws.cell(row=1, column=i).column_letter
        ws.column_dimensions[chu].width = rong.get(c, 12)
        ws.cell(row=1, column=i).font = Font(bold=True)
        if c in COT_NGUOI:
            ws.cell(row=1, column=i).fill = PatternFill("solid", fgColor="FFF2CC")   # cột người gán điền
    for hang in ws.iter_rows(min_row=2):
        for o in hang:
            o.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    n = max(len(dong) + 1, 2)

    def chon(cot: str, gia_tri: list[str] | str, chan: bool = True) -> None:
        cong_thuc = gia_tri if isinstance(gia_tri, str) else '"' + ",".join(gia_tri) + '"'
        dv = DataValidation(type="list", formula1=cong_thuc, allow_blank=True, showErrorMessage=chan)
        chu = ws.cell(row=1, column=COT_PHIEU.index(cot) + 1).column_letter
        dv.add(f"{chu}2:{chu}{n}")
        ws.add_data_validation(dv)

    chon("tieng_viet", list(FL.ABBR_VIETNAMESE))
    chon("lien_quan", list(FL.ABBR_RELEVANCE))
    chon("da_dung", list(FL.ABBR_OWNER))
    chon("may_nhac", list(FL.ABBR_MODEL_MENTION))
    # Tên máy có thể nhiều mã cách nhau bằng ';' nên danh sách chỉ để gợi ý, không chặn
    chon("ten_may", f"danh_muc_may!$A$2:$A${len(may) + 1}", chan=False)

    for ten, ds, cot in (("danh_sach_nhan", nhan, ("cot", "viet_tat", "nhan", "y_nghia")),
                         ("danh_muc_may", may, ("ma_may", "ten", "ngay_ra_mat"))):
        trang = wb.create_sheet(ten)
        trang.append(list(cot))
        for d in ds:
            trang.append([d.get(c, "") for c in cot])
        for i, c in enumerate(cot, start=1):
            trang.column_dimensions[trang.cell(row=1, column=i).column_letter].width = 60 if c == "y_nghia" else 22
            trang.cell(row=1, column=i).font = Font(bold=True)
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    wb.save(tam)
    os.replace(tam, p)


def _phieu_da_dien(p: Path) -> bool:
    return p.exists() and da_co_nguoi_dien(doc_csv(p), set(COT_CODE))


def chay(vao: Path = VAO, ra: Path = RA, nguoi: list[str] | None = None, ghi_de: bool = False,
         danh_muc: Path = DANH_MUC) -> dict:
    nguoi = nguoi or [f"n{i:02d}" for i in range(1, 12)]
    if len(set(nguoi)) != len(nguoi):
        raise SystemExit("mã người gán bị trùng")
    phieu = ra / "phieu"
    da_dien = [p.name for p in sorted(phieu.glob("*.csv")) if _phieu_da_dien(p)] if phieu.exists() else []
    if da_dien and not ghi_de:
        raise SystemExit(f"Phiếu đã có người điền: {da_dien}. Không ghi file nào. Thêm --ghi-de nếu thật sự muốn "
                         "lấy mẫu lại (phần đã điền sẽ mất).")
    if not vao.exists():
        raise SystemExit(f"Không thấy {vao}. Chạy tầng 2 trước: python -m src.run --den tien_xu_ly")
    khung, rong = doc_khung(vao)
    mau = lay_mau(khung)
    for i, r in enumerate(mau, start=1):
        r["stt"] = i
    chia_viec(mau, nguoi)
    sha = _sha256(vao)
    nhan, may = danh_sach_nhan(), danh_muc_may(danh_muc)

    ra.mkdir(parents=True, exist_ok=True)
    tam = ra / "mau_a.jsonl.tam"
    with open(tam, "w", encoding="utf-8") as f:
        for r in mau:
            f.write(json.dumps({k: r[k] for k in ("stt", "comment_id", "video_id", "model", "tang", "N_h", "n_h",
                                                   "trong_so", "hieu_chinh", "gan_doi", "nguoi_gan", "is_spam",
                                                   "is_vietnamese", "spam_reasons")}, ensure_ascii=False) + "\n")
    os.replace(tam, ra / "mau_a.jsonl")

    tep = {}
    hc = [dong_phieu(r) for r in mau if r["hieu_chinh"]]
    random.Random(SEED + 2).shuffle(hc)
    _ghi_csv(phieu / "hieu_chinh_50.csv", COT_PHIEU, hc)
    ghi_xlsx(phieu / "hieu_chinh_50.xlsx", hc, nhan, may)
    tep["hieu_chinh_50"] = len(hc)
    for n in nguoi:
        dong = [dong_phieu(r) for r in mau if n in r["nguoi_gan"]]
        random.Random(f"{SEED}-{n}").shuffle(dong)   # trộn để tầng không lộ theo thứ tự
        for d in dong:
            d["nguoi_gan"] = n
        _ghi_csv(phieu / f"mau_a_{n}.csv", COT_PHIEU, dong)
        ghi_xlsx(phieu / f"mau_a_{n}.xlsx", dong, nhan, may)
        tep[f"mau_a_{n}"] = len(dong)
    _ghi_csv(phieu / "danh_sach_nhan.csv", ("cot", "viet_tat", "nhan", "y_nghia"), nhan)
    _ghi_csv(phieu / "danh_muc_may.csv", ("ma_may", "ten", "ngay_ra_mat"), may)

    theo_tang = {t: {"N_h": next((r["N_h"] for r in mau if r["tang"] == t), 0),
                     "n_h": sum(r["tang"] == t for r in mau)} for t in CO_TANG}
    manifest = {
        "chay_luc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "seed": SEED,
        "nguon": {"file": str(vao.relative_to(GOC)) if vao.is_relative_to(GOC) else str(vao), "sha256": sha,
                  "so_binh_luan_co_chu": len(khung), "so_binh_luan_rong": rong},
        "tang": theo_tang, "so_mau": len(mau), "so_hieu_chinh": len(hc),
        "so_gan_doi": sum(r["gan_doi"] for r in mau), "nguoi_gan": nguoi, "so_dong_moi_phieu": tep,
        "bo_nhan": "docs/3-gan-nhan/dac-ta-bo-nhan.md mục 8 (chốt 26/11)",
    }
    (ra / "mau_a.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Lấy mẫu A, đợt hiệu chỉnh và xuất phiếu gán nhãn theo bộ nhãn chốt")
    p.add_argument("--vao", type=Path, default=VAO, help="file tầng 2 (mặc định data/processed/comments.jsonl)")
    p.add_argument("--ra", type=Path, default=RA, help="thư mục ra (mặc định data/labels)")
    p.add_argument("--nguoi", default="", help="mã người gán, cách nhau bằng dấu phẩy (mặc định n01…n11)")
    p.add_argument("--ghi-de", action="store_true", help="lấy mẫu lại dù phiếu đã có người điền")
    a = p.parse_args(argv)
    nguoi = [x.strip() for x in a.nguoi.split(",") if x.strip()] or None
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(chay(a.vao, a.ra, nguoi, a.ghi_de), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

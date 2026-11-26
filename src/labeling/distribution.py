"""Mục đích: EDA phân bố nhãn B7: số đếm, tỷ lệ và khoảng tin cậy (chỉ khi B đã kiểm xong), thái độ, nhóm, đối chiếu; ghi docs/3-gan-nhan/bao-cao-phan-bo-nhan.md (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 8); cập nhật lần cuối: 2026-11-25.

Chạy từ gốc repo:
    python -m src.labeling.distribution

Báo cáo chỉ có số và tên nhãn, không có chữ bình luận.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import date

from . import stats as T
from .agreement import PHIEU_A, PHIEU_B
from .b7_labels import (PHIEU_KIEM_2, PHIEU_KIEM_2_DA_DIEN, doc_kiem, CHIEU, DA_DUNG, LIEN_QUAN, MAY_NHAC, NOI_VE, PHIEU_B7, PHIEU_KIEM, THAI_DO, doc_phieu_nguoi,
                        nhan_cuoi, tach, thanh_nhan)
from .b7_labels import COT_NHAN, MAU
from .lot_k import NHAN_K_PX, PHIEU_K
from .label_set import KHIA_CANH, MUC_DICH, NGOAI_KHIA_CANH, gan_nhan
from .sample import GOC, _sha256, doc_csv

BAO_CAO = GOC / "docs" / "3-gan-nhan" / "bao-cao-phan-bo-nhan.md"
NHOM_NHO = 30          # nhóm dưới ngần này bình luận: không ghi phần trăm (đặc tả mục 8)
IT_DU_LIEU = 30        # khen + chê dưới ngần này: chưa kết luận được thái độ (quy ước chung của đề tài)

NHOM = (("Gốc hay reply", "la_reply", {"khong": "bình luận gốc", "co": "reply"}),
        ("Nhóm kênh", "nhom_kenh", {"5_kenh_lon": "5 kênh lớn", "kenh_khac": "kênh khác", "khong_ro": "không rõ kênh"}),
        ("Tuần sau ra mắt", "tuan", {"1": "tuần 1–2", "2": "tuần 1–2", "3": "tuần 3–4", "4": "tuần 3–4"}),
        ("Loại video", "loai_video", {}),
        ("Của chủ kênh", "chu_kenh", {"khong": "người xem", "co": "chủ kênh"}))


def khoang(co: list[bool], cum: list[str]) -> dict:
    """Số đếm, tỷ lệ, khoảng bootstrap theo video, khoảng Wilson, deff của một nhãn (đặc tả mục 8)."""
    x, n = sum(co), len(co)
    p, wl, wu = T.wilson(x, n)
    if x == 0:
        return {"x": 0, "n": n, "p": 0.0, "bl": 0.0, "bu": T.quy_tac_ba(n), "wl": wl, "wu": wu, "deff": None}
    _, bl, bu = T.bootstrap_theo_cum(co, cum)
    return {"x": x, "n": n, "p": p, "bl": bl, "bu": bu, "wl": wl, "wu": wu, "deff": T.he_so_thiet_ke(bu - bl, wu - wl)}


def thong_ke(dong: list[dict]) -> dict:
    """Mọi bảng của báo cáo, từ các dòng có nhãn. Không cần chữ bình luận."""
    nhan = [thanh_nhan(d) for d in dong]
    video = [d["video_id"] for d in dong]
    tat_ca = list(range(len(dong)))
    dt = [i for i in tat_ca if nhan[i]["lien_quan"] == {"dien_thoai"}]
    mot = [next(iter(n["lien_quan"])) for n in nhan]
    td = [{c.split(":")[1] for c in n["thai_do"]} for n in nhan]

    def bang(chieu: str, ten_nhan, idx) -> dict[str, dict]:
        return {x: khoang([x in nhan[i][chieu] for i in idx], [video[i] for i in idx]) for x in ten_nhan}

    nhom = {}
    for ten, cot, doi in NHOM:
        g: dict[str, list[int]] = {}
        for i, d in enumerate(dong):
            g.setdefault(doi.get(d[cot], d[cot]) or "không xác định", []).append(i)
        nhom[ten] = {t: {"n": len(ix), "video": len({video[i] for i in ix}), "lq": Counter(mot[i] for i in ix),
                         "md": Counter(m for i in ix for m in nhan[i]["muc_dich"]),
                         "td": Counter(t2 for i in ix for t2 in td[i])} for t, ix in g.items()}
    bao_loi = [i for i in tat_ca if "bao_loi" in nhan[i]["muc_dich"]]
    mg = [i for i in tat_ca if "minigame" in nhan[i]["muc_dich"]]
    cap = Counter(tuple(c.split(":")) for n in nhan for c in n["thai_do"])
    return {
        "n": len(dong), "so_video": len(set(video)), "nhieu_nhat": max(Counter(video).values()), "n_dt": len(dt),
        "lien_quan": bang("lien_quan", LIEN_QUAN, tat_ca), "noi_ve": bang("noi_ve", NOI_VE, dt),
        "muc_dich": bang("muc_dich", MUC_DICH, tat_ca), "da_dung": bang("da_dung", DA_DUNG, tat_ca),
        "may_nhac": bang("may_nhac", MAY_NHAC, tat_ca), "may_nhac_dt": bang("may_nhac", MAY_NHAC, dt),
        "cap": cap, "so_cap": Counter(k for n in nhan for k in n["noi_ve"]),
        "so_nhan_c2": Counter(len(nhan[i]["noi_ve"]) for i in dt),
        "co_khia_canh": sum(bool(nhan[i]["noi_ve"] & set(KHIA_CANH)) for i in dt),
        "lq_md": Counter((mot[i], m) for i in tat_ca for m in nhan[i]["muc_dich"]),
        "bao_loi": len(bao_loi), "bao_loi_da_dung": sum(nhan[i]["da_dung"] == {"co"} for i in bao_loi),
        "mg": Counter(mot[i] for i in mg), "mg_td": Counter(t for i in mg for t in td[i]),
        "khen_dt": sum("tich_cuc" in td[i] for i in dt), "che_dt": sum("tieu_cuc" in td[i] for i in dt),
        "chi_khong_danh_gia": sum(td[i] == {"khong_danh_gia"} for i in dt),
        "nhom": nhom, "chua_chac": Counter(c for d in dong for c in tach(d["chua_chac"])),
        "co_chua_chac": sum(bool(d["chua_chac"]) for d in dong),
        "n_k": sum(d.get("lo") == "K" for d in dong),
    }


def _ghep(dong: list[dict], khac: list[dict]) -> list[tuple[dict, dict]]:
    k = {d["comment_id"]: d for d in khac if (d.get("ma_tu_do") or "").strip()}
    return [(thanh_nhan(d), gan_nhan(k[d["comment_id"]])) for d in dong if d["comment_id"] in k]


def doi_chieu(dong: list[dict], khac: list[dict]) -> dict:
    """Nhãn B7 so với nhãn suy từ một phiếu mã tự do: chiều 1 chung, và từng nhãn chiều 1, 2, 3 (đặc tả mục 8)."""
    ghep = _ghep(dong, khac)
    a1, b1 = [next(iter(p["lien_quan"])) for p, _ in ghep], [next(iter(q["lien_quan"])) for _, q in ghep]
    ra = []
    for chieu, ten_nhan in (("lien_quan", LIEN_QUAN), ("noi_ve", NOI_VE), ("muc_dich", tuple(MUC_DICH))):
        for x in ten_nhan:
            a, b = [x in p[chieu] for p, _ in ghep], [x in q[chieu] for _, q in ghep]
            if any(a) or any(b):
                ra.append({"chieu": chieu, "nhan": x, "b7": sum(a), "kia": sum(b),
                           "ca_hai": sum(u and v for u, v in zip(a, b)), "kappa": T.kappa(a, b),
                           "dyd": T.dong_y_duong(a, b)})
    return {"n": len(ghep), "kappa_1": T.kappa(a1, b1), "dong_y_1": sum(u == v for u, v in zip(a1, b1)) / len(ghep),
            "nhan": ra}


# ---- Báo cáo -----------------------------------------------------------------------------------------
def _so(x: float, le: int = 1) -> str:
    return f"{x:.{le}f}".replace(".", ",")


def _pt(x: float) -> str:
    return _so(100 * x)


def _bang(cot: list[str], hang: list[list]) -> list[str]:
    return ["| " + " | ".join(cot) + " |", "|" + "---|" * len(cot)] \
        + ["| " + " | ".join(str(o) for o in h) + " |" for h in hang] + [""]


def _bang_nhan(b: dict[str, dict], mo: bool, loai: bool = False) -> list[str]:
    hang = []
    for x, k in sorted(b.items(), key=lambda u: -u[1]["x"]):
        h = [f"`{x}`"] + (["ngoài khía cạnh" if x in NGOAI_KHIA_CANH else "khía cạnh"] if loai else []) + [k["x"]]
        if mo:
            kb = f"≤ {_pt(k['bu'])} (quy tắc ba)" if k["x"] == 0 else f"[{_pt(k['bl'])}; {_pt(k['bu'])}]"
            h += [_pt(k["p"]), kb, f"[{_pt(k['wl'])}; {_pt(k['wu'])}]", "" if k["deff"] is None else _so(k["deff"], 2)]
        hang.append(h)
    return _bang(["Nhãn"] + (["Loại"] if loai else []) + ["Số bình luận"]
                 + (["%", "KTC 95% (bootstrap video)", "KTC 95% (Wilson)", "deff"] if mo else []), hang)


def _o(x: int, n: int, mo: bool) -> str:
    return f"{x} ({_pt(x / n)}%)" if mo and n >= NHOM_NHO else str(x)


def viet_bao_cao(tk: dict, tt: dict, dc: dict[str, dict], sha: str, ngay: str) -> str:
    mo = tt["xong"]
    s = ["# Báo cáo phân bố nhãn (B7)", "",
         "> Mục đích: EDA nhãn 6 chiều của mẫu khám phá nhãn, do A (AI) gán lại từ chữ bình luận: số đếm (tỷ lệ khi đã kiểm), "
         f"thái độ, nhóm, mức chắc chắn, đối chiếu; cập nhật lần cuối: {ngay}.", "",
         "**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.distribution`. "
         f"Nguồn: `data/kham-pha/phieu_b7.csv` (SHA-256 `{sha[:8]}…{sha[-4:]}`), dữ liệu v4. "
         "Luật: [đặc tả khám phá nhãn](dac-ta-kham-pha-nhan.md) mục 7c, 8. Định nghĩa nhãn: [đặc tả bộ nhãn](dac-ta-bo-nhan.md).", ""]
    if mo:
        s += [f"**Trạng thái: trưởng nhóm đã kiểm {tt['da_kiem']}/{tt['can_kiem']} bình luận phải xem.** Nhãn do AI gán.", ""]
    else:
        s += [f"**Trạng thái: CHƯA KIỂM XONG ({tt['da_kiem']}/{tt['can_kiem']}).** Nhãn do AI gán. Báo cáo **chỉ có số đếm**, "
              "không có phần trăm và khoảng tin cậy; kiểm xong chạy lại thì có. Đừng trích như tỷ lệ của dữ liệu.", ""]
    s += [f"- **Mẫu:** {tk['n']} bình luận ngẫu nhiên ({tk['n'] - tk['n_k']} lô 1–5" + (f", {tk['n_k']} lô K" if tk["n_k"] else "")
          + f"), thuộc {tk['so_video']} video (nhiều nhất {tk['nhieu_nhat']} bình luận một video).",
          ("- **Lô K:** hai bên gán mù, B phân xử ca lệch ([báo cáo lô K](bao-cao-lo-k.md)); nhãn lô K không cần kiểm thêm."
           if tk["n_k"] else "- **Chưa có lô K.** Mẫu phân bố đủ là 600; lô K nhập vào sau khi phân xử (B6)."),
          "- **Bộ nhãn:** trưởng nhóm duyệt 25/11 (đặc tả bộ nhãn mục 7), thêm luật 8, 9 ngày 26/11 sau khi so lô K, chốt sau B8 (mục 8; bảng này dùng nhãn khám phá, chưa gộp); mọi chiều đạt κ ≥ 0,6 ở lô K.",
          "- Mẫu lấy trên cả v4, **không** suy cho bộ 4 máy.", "",
          "## 1. Liên quan tới gì (một nhãn)", ""]
    s += _bang_nhan(tk["lien_quan"], mo)
    s += ["## 2. Nói về phần nào của điện thoại (nhiều nhãn)", "",
          f"Phần áp dụng: **{tk['n_dt']} bình luận `dien_thoai`**. {tk['co_khia_canh']} bình luận có ít nhất một khía cạnh, "
          f"{tk['n_dt'] - tk['co_khia_canh']} chỉ có nhãn ngoài khía cạnh. Số nhãn chiều 2 mỗi bình luận: "
          + ", ".join(f"{k} nhãn ở {v} bình luận" for k, v in sorted(tk["so_nhan_c2"].items())) + ".", ""]
    s += _bang_nhan(tk["noi_ve"], mo, loai=True)
    s += ["## 3. Mục đích (nhiều nhãn)", ""] + _bang_nhan(tk["muc_dich"], mo)
    s += ["Mục đích theo nhãn chiều 1 (số bình luận):", ""]
    s += _bang(["Mục đích"] + [f"`{x}`" for x in LIEN_QUAN],
               [[f"`{m}`"] + [tk["lq_md"].get((x, m), 0) for x in LIEN_QUAN]
                for m, _ in sorted(tk["muc_dich"].items(), key=lambda u: -u[1]["x"])])
    s += ["## 4. Thái độ (theo cặp bình luận và nhãn chiều 2)", "",
          f"{sum(tk['so_cap'].values())} cặp. Một cặp có thể có nhiều thái độ, nên tổng hàng có thể vượt số cặp.", ""]
    hang = [[f"`{k}`", n] + [tk["cap"].get((k, t), 0) for t in THAI_DO] for k, n in tk["so_cap"].most_common()]
    hang.append(["**Tổng**", sum(tk["so_cap"].values())] + [sum(v for (_, u), v in tk["cap"].items() if u == t) for t in THAI_DO])
    s += _bang(["Nhãn chiều 2", "Số cặp"] + [f"`{t}`" for t in THAI_DO], hang)
    kc = {k: tk["cap"].get((k, "tich_cuc"), 0) + tk["cap"].get((k, "tieu_cuc"), 0) for k in NOI_VE}
    du = [k for k in NOI_VE if kc[k] >= IT_DU_LIEU]
    s += [f"- Bình luận `dien_thoai` có ít nhất một lời khen: {_o(tk['khen_dt'], tk['n_dt'], mo)}; có ít nhất một lời chê: "
          f"{_o(tk['che_dt'], tk['n_dt'], mo)}; chỉ có `khong_danh_gia`: {_o(tk['chi_khong_danh_gia'], tk['n_dt'], mo)}.",
          f"- Nhãn chiều 2 có khen + chê từ {IT_DU_LIEU} trở lên: " + (", ".join(f"`{k}` ({kc[k]})" for k in du) or "không có")
          + ". Nhãn dưới ngưỡng này ít dữ liệu, chưa kết luận được khen hay chê nhiều hơn.", "",
          "## 5. Đã dùng máy (một nhãn)", ""] + _bang_nhan(tk["da_dung"], mo)
    s += [f"`bao_loi`: {tk['bao_loi']} bình luận, trong đó {tk['bao_loi_da_dung']} có nhãn `co`. Q5 cần đúng loại này.", "",
          "## 6. Máy được nhắc (một nhãn)", ""] + _bang_nhan(tk["may_nhac"], mo)
    s += [f"Riêng {tk['n_dt']} bình luận `dien_thoai`: "
          + ", ".join(f"`{x}` {_o(k['x'], k['n'], mo)}" for x, k in tk["may_nhac_dt"].items()) + ".", "",
          "## 7. Minigame", "",
          f"{sum(tk['mg'].values())} bình luận: " + (", ".join(f"{v} ở `{k}`" for k, v in tk["mg"].most_common()) or "không có")
          + ". Thái độ: " + (", ".join(f"`{t}` {v}" for t, v in tk["mg_td"].most_common()) or "không có") + ".", "",
          "## 8. Theo nhóm", "", f"Số bình luận của nhóm có nhãn đó. Nhóm dưới {NHOM_NHO} bình luận chỉ ghi số đếm.", ""]
    for ten, gs in tk["nhom"].items():
        hang = [[g, v["n"], v["video"]]
                + [_o(v["lq"].get(x, 0), v["n"], mo) for x in ("dien_thoai", "ngu_canh", "nguoi_binh_luan")]
                + [_o(v["md"].get(m, 0), v["n"], mo) for m in ("danh_gia", "hoi", "tranh_luan", "cong_kich", "minigame")]
                + [_o(v["td"].get(t, 0), v["n"], mo) for t in ("tich_cuc", "tieu_cuc")]
                for g, v in sorted(gs.items(), key=lambda u: -u[1]["n"])]
        s += [f"**{ten}**", ""] + _bang(["Nhóm", "n", "Video", "`dien_thoai`", "`ngu_canh`", "`nguoi_binh_luan`", "`danh_gia`",
                                         "`hoi`", "`tranh_luan`", "`cong_kich`", "`minigame`", "có khen", "có chê"], hang)
    s += ["## 9. A chắc tới đâu", "",
          f"{tk['co_chua_chac']}/{tk['n']} bình luận có ít nhất một chiều A đánh dấu `?`. Theo chiều: "
          + ", ".join(f"{ten} {tk['chua_chac'].get(c, 0)}" for c, ten in CHIEU.values()) + ".", "",
          "## 10. Kiểm của trưởng nhóm", ""]
    if mo:
        x, n = tt["phan"]["ngau_nhien"]
        y, m = tt["phan"]["chua_chac"]
        p, lo, hi = T.wilson(x, n)
        s += [f"- Phần ngẫu nhiên: {x}/{n} bình luận phải sửa, {_pt(p)}% [{_pt(lo)}; {_pt(hi)}] (Wilson).",
              f"- Phần A đánh dấu `?`: {y}/{m} bình luận phải sửa."]
    elif tt["da_kiem"]:
        s += [f"- Đang kiểm: đã sửa {tt['sua']} trong {tt['da_kiem']} bình luận đã xem."]
    else:
        s += ["Chưa kiểm dòng nào.", ""]
    if tt["da_kiem"]:
        s += ["- Số bình luận sửa, theo cột: " + (", ".join(f"`{c}` {v}" for c, v in tt["theo_chieu"].most_common()) or "không có") + ".", ""]
    s += ["## 11. Đối chiếu với mã tự do", "",
          "Nhãn bên kia suy từ mã tự do bằng luật từ khóa của `label_set.py`, nên lệch có thể do luật. Phiếu B mã **trước** khi sửa "
          "bảng hành vi. Đây là chỉ báo, không thay cho lô K mù. Cột B7 là nhãn của A trước khi B sửa.", ""]
    for ten, r in dc.items():
        s += [f"**B7 so với {ten}** (n = {r['n']}). Chiều 1 như một câu 6 lựa chọn: đồng ý thô {_pt(r['dong_y_1'])}%, κ = {_so(r['kappa_1'], 2)}.", ""]
        s += _bang(["Chiều", "Nhãn", "B7", "Bên kia", "Cả hai", "κ", "Đồng ý dương"],
                   [[u["chieu"], f"`{u['nhan']}`", u["b7"], u["kia"], u["ca_hai"], _so(u["kappa"], 2),
                     "" if u["dyd"] is None else _so(u["dyd"], 2)] for u in r["nhan"]])
    return "\n".join(s)


def doc() -> tuple[list[dict], dict, list[dict]]:
    """(dòng có nhãn cuối, tình trạng kiểm, dòng có nhãn gốc của A)."""
    goc = doc_csv(PHIEU_B7)
    dong, tt = nhan_cuoi(goc, doc_kiem(), PHIEU_KIEM_2.exists() or PHIEU_KIEM_2_DA_DIEN.exists())
    return dong + doc_lo_k(), tt, goc


def doc_lo_k() -> list[dict]:
    """Lô K sau phân xử (đặc tả mục 7b, 8), kèm trường mô tả; chưa phân xử thì rỗng."""
    if not NHAN_K_PX.exists():
        return []
    meta = {d["stt"]: d for d in doc_csv(PHIEU_K)}
    video = {d["comment_id"]: d["video_id"] for d in doc_csv(MAU)}
    ra = []
    for d in doc_csv(NHAN_K_PX):
        m = meta[d["stt"]]
        ra.append({**{k: m[k] for k in ("stt", "lo", "comment_id", "loai_video", "nhom_kenh", "tuan", "la_reply", "chu_kenh")},
                   "video_id": video[m["comment_id"]], **{c: d[c] for c in COT_NHAN}, "chua_chac": "", "ghi_chu_a": ""})
    return ra


def chay() -> dict:
    dong, tt, goc = doc()
    dc = {ten: doi_chieu(goc, doc_csv(p)) for ten, p in (("mã tự do cũ của A", PHIEU_A), ("mã tự do của B (trưởng nhóm)", PHIEU_B))
          if p.exists()}
    BAO_CAO.write_text(viet_bao_cao(thong_ke(dong), tt, dc, _sha256(PHIEU_B7), date.today().isoformat()) + "\n", encoding="utf-8")
    return {"kiem_xong": tt["xong"], "da_kiem": f"{tt['da_kiem']}/{tt['can_kiem']}", "file": str(BAO_CAO)}


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="EDA nhãn B7 (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 8)").parse_args(argv)
    kq = chay()
    sys.stdout.reconfigure(encoding="utf-8")
    print(kq)


if __name__ == "__main__":
    main()

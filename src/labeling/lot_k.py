"""Mục đích: So nhãn lô K của A và B gán mù (B6): đọc phiếu B (xlsx hay csv), đồng ý thô, kappa, đồng ý dương, phân bố mỗi bên, ma trận lệch chiều 1; ghi docs/3-gan-nhan/bao-cao-lo-k.md, data/kham-pha/lech_lo_K.csv; phiếu phân xử markdown và nhãn sau phân xử (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 7b); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo:
    python -m src.labeling.lot_k            # so, báo cáo
    python -m src.labeling.lot_k phan-xu    # phiếu phân xử data/kham-pha/phan_xu_lo_K.md
    python -m src.labeling.lot_k nhap       # đọc phân xử -> data/kham-pha/nhan_lo_K_phan_xu.csv
    python -m src.labeling.lot_k --lo D2    # cùng các việc trên cho lô D2 (kiểm lại sau khi sửa định nghĩa)

Báo cáo chỉ có số, tên nhãn và stt; chữ bình luận chỉ nằm trong lech_lo_K.csv (ngoài git).
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

from . import stats as T
from .b7_labels import (danh_muc_may, COT_NHAN, DA_DUNG, LIEN_QUAN, MAY_NHAC, NOI_VE, THAI_DO, LoiNhan, doc_nhan_a, doc_phieu_nguoi,
                        kiem_tra, mo_rong, tach, thanh_nhan)
from .label_set import MUC_DICH
from .sample import GOC, RA, _ghi_csv, _sha256, doc_csv

TEN_LO = "K"
NGUON_B = {"D2": "- Phiếu B (`.xlsx`) được tạo bằng công cụ, không lưu từ Excel; trưởng nhóm xác nhận đã gán tay ngày 26/11."}
PHIEU_K = RA / "phieu_lo_K.csv"
NHAN_K_A = RA / "nhan_lo_K_A.txt"
PHIEU_K_B = (RA / "phieu_lo_K_B.xlsx", RA / "phieu_lo_K_B.csv")   # file nào có thì dùng, xlsx trước
LECH = RA / "lech_lo_K.csv"
BAO_CAO = GOC / "docs" / "3-gan-nhan" / "bao-cao-lo-k.md"
NGUONG = 0.6
CHIEU_MOT = (("lien_quan", "1. Liên quan tới gì", LIEN_QUAN), ("da_dung", "5. Đã dùng máy", DA_DUNG),
             ("may_nhac", "6. Máy được nhắc", MAY_NHAC))
CHIEU_NHIEU = (("noi_ve", "2. Nói về phần nào", NOI_VE), ("muc_dich", "3. Mục đích", tuple(MUC_DICH)))
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def dat_lo(lo: str) -> None:
    """Đổi mọi đường dẫn sang lô khác (K mặc định; D2 là lô kiểm lại, đặc tả mục 7b)."""
    global TEN_LO, PHIEU_K, NHAN_K_A, PHIEU_K_B, LECH, BAO_CAO, PHAN_XU, NHAN_K_PX
    TEN_LO = lo
    PHIEU_K, NHAN_K_A = RA / f"phieu_lo_{lo}.csv", RA / f"nhan_lo_{lo}_A.txt"
    PHIEU_K_B = (RA / f"phieu_lo_{lo}_B.xlsx", RA / f"phieu_lo_{lo}_B.csv")
    LECH, PHAN_XU, NHAN_K_PX = RA / f"lech_lo_{lo}.csv", RA / f"phan_xu_lo_{lo}.md", RA / f"nhan_lo_{lo}_phan_xu.csv"
    BAO_CAO = GOC / "docs" / "3-gan-nhan" / f"bao-cao-lo-{lo.lower()}.md"


# ---- Đọc phiếu ---------------------------------------------------------------------------------------
def _cot(ref: str) -> int:
    n = 0
    for c in re.match(r"[A-Z]+", ref)[0]:
        n = n * 26 + ord(c) - 64
    return n - 1


def doc_xlsx(p: Path) -> list[dict]:
    """Sheet đầu tiên có ô A1 = 'stt' của một file .xlsx, đọc bằng thư viện chuẩn (venv không có openpyxl)."""
    with zipfile.ZipFile(p) as z:
        chung = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                chung.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        tens = sorted((n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)),
                      key=lambda n: int(re.search(r"\d+", n.rsplit("/", 1)[1])[0]))
        for ten in tens:
            hang = []
            for row in ET.fromstring(z.read(ten)).iter("{%s}row" % NS["m"]):
                o = {}
                for c in row.findall("m:c", NS):
                    v, t = c.find("m:v", NS), c.get("t")
                    if t == "s" and v is not None:
                        gt = chung[int(v.text)]
                    elif t == "inlineStr":
                        gt = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                    else:
                        gt = "" if v is None else v.text or ""
                        if re.fullmatch(r"-?\d+\.0", gt):   # Excel lưu số nguyên dạng 501.0
                            gt = gt[:-2]
                    o[_cot(c.get("r"))] = gt
                hang.append([o.get(i, "") for i in range(max(o, default=-1) + 1)])
            if hang and hang[0] and hang[0][0] == "stt":
                dau = hang[0]
                return [dict(zip(dau, h + [""] * (len(dau) - len(h)))) for h in hang[1:] if any(x.strip() for x in h)]
    raise LoiNhan(f"{p.name}: không có sheet nào bắt đầu bằng cột stt")


def doc_phieu_b(p: Path) -> list[dict]:
    return doc_xlsx(p) if p.suffix.lower() == ".xlsx" else doc_phieu_nguoi(p)


def nhan_b(dong: list[dict]) -> tuple[dict[int, dict], list[str]]:
    """Nhãn của B theo stt (gõ tắt hay đủ đều được), và danh sách lỗi. Dòng có lỗi vẫn giữ để so, lỗi được báo."""
    ra, loi = {}, []
    for d in dong:
        stt = int(d["stt"])
        m = {c: mo_rong(c, d.get(c) or "") for c in COT_NHAN}
        m["chua_chac"] = d.get("chua_chac") or ""
        m["ghi_chu"] = d.get("ghi_chu") or ""
        if "ten_may" in d:
            m["ten_may"] = "; ".join(tach((d.get("ten_may") or "").lower()))
        try:
            kiem_tra(m, f"stt {stt}")
        except LoiNhan as e:
            loi.append(str(e))
        ra[stt] = m
    return ra, loi


# ---- So ----------------------------------------------------------------------------------------------
def _mot_nhan(a: list[bool], b: list[bool]) -> dict:
    return {"a": sum(a), "b": sum(b), "ca_hai": sum(x and y for x, y in zip(a, b)), "n": len(a),
            "kappa": T.kappa(a, b) if a else float("nan"), "dyd": T.dong_y_duong(a, b)}


def so_sanh(A: dict[int, dict], B: dict[int, dict]) -> dict:
    """Mọi chỉ số của mục 7b trên các stt cả hai cùng có."""
    stt = sorted(set(A) & set(B))
    la, lb = [thanh_nhan(A[s]) for s in stt], [thanh_nhan(B[s]) for s in stt]
    ra = {"n": len(stt), "mot": {}, "nhieu": {}, "thai_do": {}}
    for c, _, nhan in CHIEU_MOT:
        a, b = [next(iter(x[c])) for x in la], [next(iter(x[c])) for x in lb]
        ra["mot"][c] = {"p_o": sum(x == y for x, y in zip(a, b)) / len(a), "kappa": T.kappa(a, b),
                        "pa": Counter(a), "pb": Counter(b), "ma_tran": Counter(zip(a, b)),
                        "nhan": {k: _mot_nhan([x == k for x in a], [y == k for y in b]) for k in nhan}}
    for c, _, nhan in CHIEU_NHIEU:
        idx = range(len(stt)) if c == "muc_dich" else \
            [i for i in range(len(stt)) if la[i]["lien_quan"] == lb[i]["lien_quan"] == {"dien_thoai"}]
        tung = {k: _mot_nhan([k in la[i][c] for i in idx], [k in lb[i][c] for i in idx]) for k in nhan}
        gop_a = [k in la[i][c] for i in idx for k in nhan]
        gop_b = [k in lb[i][c] for i in idx for k in nhan]
        ra["nhieu"][c] = {"n": len(idx), "tung": tung, "gop": _mot_nhan(gop_a, gop_b),
                          "trung_khop": sum(la[i][c] == lb[i][c] for i in idx) / max(1, len(idx))}
    # chiều 4: chỉ trên các cặp (bình luận, nhãn chiều 2) mà cả hai cùng gán
    ca = [(i, k) for i in range(len(stt)) for k in la[i]["noi_ve"] & lb[i]["noi_ve"]]
    ra["so_cap_chung"] = len(ca)
    ra["thai_do"] = {t: _mot_nhan([f"{k}:{t}" in la[i]["thai_do"] for i, k in ca], [f"{k}:{t}" in lb[i]["thai_do"] for i, k in ca])
                     for t in THAI_DO}
    ra["thai_do_trung"] = sum({x for x in la[i]["thai_do"] if x.startswith(k + ":")} == {x for x in lb[i]["thai_do"] if x.startswith(k + ":")}
                              for i, k in ca) / max(1, len(ca))
    if all("ten_may" in A[s] and "ten_may" in B[s] for s in stt):   # tên máy: so trên bình luận cả hai gán goi_ten_may
        ca2 = [s for s in stt if A[s]["may_nhac"] == B[s]["may_nhac"] == "goi_ten_may"]
        tm = lambda d: {x.replace(" ", "") for x in tach(d["ten_may"])}   # "doogee s98" = "doogees98"
        ra["ten_may"] = {"n": len(ca2), "khop": sum(tm(A[s]) == tm(B[s]) for s in ca2),
                         "lech": [s for s in ca2 if tm(A[s]) != tm(B[s])],
                         "ngoai_danh_muc": sorted({x for s in stt for d in (A[s], B[s]) for x in tm(d)} - danh_muc_may())}
    ra["lech"] = [s for s, x, y in zip(stt, la, lb) if x != y]
    ra["lech_theo_chieu"] = Counter(c for x, y in zip(la, lb) for c in x if x[c] != y[c])
    return ra


# ---- Báo cáo -----------------------------------------------------------------------------------------
def _so(x: float, le: int = 2) -> str:
    return "–" if x != x else f"{x:.{le}f}".replace(".", ",")


def _bang(cot: list[str], hang: list[list]) -> list[str]:
    return ["| " + " | ".join(cot) + " |", "|" + "---|" * len(cot)] + ["| " + " | ".join(str(o) for o in h) + " |" for h in hang] + [""]


def _dat(k: float) -> str:
    return "**đạt**" if k == k and k >= NGUONG else "**chưa đạt**"


def viet_bao_cao(r: dict, loi: list[str], chua_chac: Counter, sha: tuple[str, str], ngay: str) -> str:
    s = [f"# Báo cáo gán mù lô {TEN_LO} (B6)", "",
         f"> Mục đích: So nhãn lô {TEN_LO} của A (Claude) và B (trưởng nhóm) gán mù: đồng ý thô, kappa, đồng ý dương, phân bố mỗi bên, chỗ lệch; cập nhật lần cuối: {ngay}.", "",
         f"**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.lot_k{'' if TEN_LO == 'K' else ' --lo ' + TEN_LO}`. "
         f"Nguồn: `{NHAN_K_A.name}` (SHA-256 `{sha[0][:8]}…{sha[0][-4:]}`), phiếu B (SHA-256 `{sha[1][:8]}…{sha[1][-4:]}`), dữ liệu v4. "
         "Luật: [đặc tả khám phá nhãn mục 7b](dac-ta-kham-pha-nhan.md#7-kiểm-b6); "
         + ("bộ nhãn duyệt 25/11." if TEN_LO == "K" else "bộ nhãn chốt 26/11, định nghĩa `dua`, `khong_xac_dinh` (chiều 1) sửa 26/11, thêm `ten_may`."), "",
         f"- **n = {r['n']} bình luận**, cả hai gán không xem của nhau. Ngưỡng dùng tiếp: κ ≥ {_so(NGUONG, 1)}.",
         "- A là AI. B gán theo [hướng dẫn gán lô K](huong-dan-gan-lo-k.md) do A viết, nên kappa có thể cao hơn hai người độc lập thật.",
         *([NGUON_B[TEN_LO]] if TEN_LO in NGUON_B else []),
         f"- n = {r['n']} nên kappa dao động mạnh: nhãn có dưới khoảng 10 bình luận thì xem đồng ý dương, đừng xét kappa riêng nó.",
         f"- Phiếu B có {len(loi)} dòng sai luật nhãn (mục 9); dòng sai vẫn được so như B đã gõ.",
         "- Một bình luận lệch ở chiều 2 thì thường lệch luôn ở chiều 4, vì thái độ gắn với nhãn chiều 2.", ""]
    s += ["## 1. Tóm tắt theo chiều", ""]
    hang = []
    for c, ten, _ in CHIEU_MOT:
        m = r["mot"][c]
        hang.append([ten, "một nhãn", r["n"], _so(100 * m["p_o"], 1) + "%", _so(m["kappa"]), _dat(m["kappa"])])
    for c, ten, _ in CHIEU_NHIEU:
        m = r["nhieu"][c]
        hang.append([ten, "nhiều nhãn", m["n"], _so(100 * m["trung_khop"], 1) + "% (trùng cả tập)",
                     _so(m["gop"]["kappa"]) + " (gộp)", _dat(m["gop"]["kappa"]) + " nếu xét theo kappa gộp"])
    hang.append(["4. Thái độ", "theo cặp", r["so_cap_chung"], _so(100 * r["thai_do_trung"], 1) + "% (trùng cả tập)", "xem mục 7", ""])
    s += _bang(["Chiều", "Loại", "n", "Đồng ý thô", "κ", "Ngưỡng 0,6"], hang)
    s += ["**Chiều nhiều nhãn xét ngưỡng bằng kappa gộp** (trưởng nhóm quyết 26/11): coi mỗi cặp (bình luận, nhãn) là một câu có/không và tính chung.", "",
          f"Chiều 2 chỉ tính trên {r['nhieu']['noi_ve']['n']} bình luận cả hai cùng gán `dien_thoai`; lệch ở chiều 1 đã tính ở chiều 1.", ""]
    for c, ten, nhan in CHIEU_MOT:
        m = r["mot"][c]
        s += [f"## {2 + [x[0] for x in CHIEU_MOT].index(c)}. Chiều {ten}", "", f"Đồng ý thô {_so(100 * m['p_o'], 1)}%, κ = {_so(m['kappa'])}.", ""]
        s += _bang(["Nhãn", "A", "B", "Cả hai", "κ (có/không)", "Đồng ý dương"],
                   [[f"`{k}`", v["a"], v["b"], v["ca_hai"], _so(v["kappa"]), "" if v["dyd"] is None else _so(v["dyd"])]
                    for k, v in m["nhan"].items() if v["a"] or v["b"]])
        if c == "lien_quan":
            dung = [k for k in nhan if m["pa"][k] or m["pb"][k]]
            s += ["Ma trận (hàng: A, cột: B):", ""]
            s += _bang(["A \\ B"] + [f"`{k}`" for k in dung], [[f"`{a}`"] + [m["ma_tran"].get((a, b), 0) for b in dung] for a in dung])
    for c, ten, _ in CHIEU_NHIEU:
        m = r["nhieu"][c]
        s += [f"## {5 + [x[0] for x in CHIEU_NHIEU].index(c)}. Chiều {ten} (n = {m['n']})", "",
              f"Trùng cả tập nhãn: {_so(100 * m['trung_khop'], 1)}%. Kappa gộp {_so(m['gop']['kappa'])}, đồng ý dương gộp {_so(m['gop']['dyd'])}.", ""]
        s += _bang(["Nhãn", "A", "B", "Cả hai", "κ", "Đồng ý dương"],
                   [[f"`{k}`", v["a"], v["b"], v["ca_hai"], _so(v["kappa"]), "" if v["dyd"] is None else _so(v["dyd"])]
                    for k, v in sorted(m["tung"].items(), key=lambda u: -(u[1]["a"] + u[1]["b"])) if v["a"] or v["b"]])
    s += ["## 7. Chiều 4. Thái độ", "", f"Trên {r['so_cap_chung']} cặp (bình luận, nhãn chiều 2) mà cả hai cùng gán. "
          f"Trùng cả tập thái độ: {_so(100 * r['thai_do_trung'], 1)}%.", ""]
    s += _bang(["Thái độ", "A", "B", "Cả hai", "κ", "Đồng ý dương"],
               [[f"`{t}`", v["a"], v["b"], v["ca_hai"], _so(v["kappa"]), "" if v["dyd"] is None else _so(v["dyd"])] for t, v in r["thai_do"].items()])
    if "ten_may" in r:
        tm = r["ten_may"]
        s += ["## Tên máy (`ten_may`)", "",
              f"Trên {tm['n']} bình luận cả hai gán `goi_ten_may`: khớp đúng tập tên máy {tm['khop']}/{tm['n']}"
              + (f" ({_so(100 * tm['khop'] / tm['n'], 1)}%)" if tm["n"] else "") + ". Lệch ở stt: " + (", ".join(map(str, tm["lech"])) or "không có") + ".", "",
              "Mã không có trong danh mục `models.json` (gõ sai, hay máy ngoài danh mục): "
              + (", ".join(f"`{x}`" for x in tm["ngoai_danh_muc"]) or "không có") + ".", ""]
    s += ["## 8. Lệch ở đâu", "",
          f"{len(r['lech'])}/{r['n']} bình luận lệch ít nhất một chiều. Theo chiều: "
          + ", ".join(f"`{c}` {v}" for c, v in r["lech_theo_chieu"].most_common()) + ".", "",
          f"Danh sách đầy đủ kèm chữ bình luận: `data/kham-pha/{LECH.name}` (ngoài git).", "",
          "Chiều B đánh dấu `chua_chac`: " + (", ".join(f"chiều {k} {v}" for k, v in sorted(chua_chac.items())) or "không có") + ".", "",
          "## 9. Dòng phiếu B sai luật nhãn", ""]
    s += [f"- {x}" for x in loi] if loi else ["Không có."]
    return "\n".join(s) + "\n"


COT_LECH = ("stt", "binh_luan", "binh_luan_cha", "chieu_lech") + tuple(f"{c}_{p}" for c in COT_NHAN for p in ("A", "B")) \
    + ("chua_chac_A", "chua_chac_B", "ghi_chu_A", "ghi_chu_B")
PHAN_XU = RA / "phan_xu_lo_K.md"
NHAN_K_PX = RA / "nhan_lo_K_phan_xu.csv"
TEN_COT = {"lien_quan": "chiều 1", "noi_ve_thai_do": "chiều 2 và 4", "muc_dich": "chiều 3", "da_dung": "chiều 5", "may_nhac": "chiều 6"}
CHIEU_SANG_COT = {"lien_quan": "lien_quan", "noi_ve": "noi_ve_thai_do", "thai_do": "noi_ve_thai_do", "muc_dich": "muc_dich",
                  "da_dung": "da_dung", "may_nhac": "may_nhac"}


def doc_ab() -> tuple[dict[int, dict], dict[int, dict], list[str], Path]:
    p_b = next((p for p in PHIEU_K_B if p.exists()), None)
    if p_b is None:
        raise SystemExit("Chưa có phiếu B: " + " hoặc ".join(p.name for p in PHIEU_K_B))
    A = doc_nhan_a(NHAN_K_A.read_text(encoding="utf-8"))
    B, loi = nhan_b(doc_phieu_b(p_b))
    if set(A) != set(B):
        raise LoiNhan(f"stt của A và B khác nhau: {sorted(set(A) ^ set(B))[:10]}")
    return A, B, loi, p_b


def cot_hoi(a: dict, b: dict) -> list[str]:
    """Các cột phải phân xử của một bình luận: cột có chiều lệch; lệch chiều 1 mà một bên là dien_thoai thì hỏi cả chiều 2, 4."""
    la, lb = thanh_nhan(a), thanh_nhan(b)
    cot = {CHIEU_SANG_COT[c] for c in la if la[c] != lb[c]}
    if "lien_quan" in cot and "dien_thoai" in (a["lien_quan"], b["lien_quan"]):
        cot.add("noi_ve_thai_do")
    return [c for c in COT_NHAN if c in cot]


# ---- Phiếu phân xử (markdown) ------------------------------------------------------------------------
def _khoi(chu: str) -> list[str]:
    rao = "`" * max(3, max((len(x) for x in re.findall(r"`+", chu)), default=0) + 1)
    return [rao + "text", chu, rao]


HUONG_DAN_PX = """# Phân xử ca lệch lô K

> Mục đích: Phiếu để trưởng nhóm (B) quyết nhãn cuối cho các bình luận lô K mà A và B gán lệch; có chữ bình luận thật, giữ ngoài git; cập nhật lần cuối: {ngay}.

**Do code sinh** (`python -m src.labeling.lot_k phan-xu`). Điền xong chạy `python -m src.labeling.lot_k nhap`. Luật: đặc tả khám phá nhãn mục 7b.

## Cách điền

Mỗi ca dưới đây có: chữ bình luận, bảng nhãn A và B (cột lệch in đậm), ghi chú hai bên, và **một khối `phan_xu`** để điền. Chỉ điền trong khối đó, sau dấu `:`.

| Ghi | Nghĩa |
|---|---|
| `A` | Lấy nhãn của A ở cột đó |
| `B` | Lấy nhãn của B ở cột đó |
| nhãn khác | Cả hai đều sai: gõ nhãn đúng, gõ tắt như lúc gán (`D`, `cam+, gia0`, `dg, hoi`…) |

- **Riêng cột `lien_quan`:** chữ `B` luôn nghĩa là "lấy của B". Muốn chọn người bình luận khác thì gõ đủ `nguoi_binh_luan`.
- **`ly_do` bắt buộc**, một câu ngắn là đủ (vd "theo luật 3", "không rõ đối tượng").
- Chỉ các cột lệch mới có trong khối. Cột hai bên đã khớp thì giữ nguyên.
- Chọn `lien_quan` khác `D` thì cột `noi_ve_thai_do` để trống hay ghi gì cũng bị bỏ.
- Ca nào chưa điền thì lệnh `nhap` báo lại, không tự đoán. Điền dở, lưu lại, lúc khác làm tiếp được.
- **Không sửa** dòng `## …`, tên cột trong khối, hay chữ bình luận.

**Luật hay dùng khi phân xử** (đặc tả bộ nhãn):
1. Gán theo **những gì được viết**, không đoán. Không rõ nói về cái gì thì chiều 1 là `X` (`khong_xac_dinh`).
2. Chiều 1 xét theo thứ tự `D` → `N` → `B` → `L` → `E` → `X`, gặp cái đúng đầu tiên thì dừng.
3. Câu mẫu dự minigame, kể cả khen tính năng máy, là `N` + `mg` (luật 8, mới 26/11).
4. Yêu cầu test kèm thông tin riêng về máy là `D` + `dn` (luật 9, mới 26/11); yêu cầu test đơn thuần là `N`.
5. `tl` (tranh luận) chỉ khi có chữ tỏ đồng ý hay phản đối ("đúng", "chuẩn", "sai", "làm gì có").
6. Cà khịa, bênh hãng mà không có lời khen chê thì thái độ là `0`.
7. Máy đẹp, xấu chung chung là `tk`; "ngon", "đỉnh" là `mc`.

**Đừng phân xử theo kiểu "tin A" hay "tin B".** A là AI; chọn theo luật, kể cả khi phải chọn khác cả hai.

"""


def viet_phan_xu(A: dict[int, dict], B: dict[int, dict], chu: dict[int, dict], ngay: str) -> str:
    s = [HUONG_DAN_PX.format(ngay=ngay)]
    lech = [k for k in sorted(A) if cot_hoi(A[k], B[k])]
    s += [f"Tổng cộng **{len(lech)} ca**.", ""]
    for k in lech:
        hoi = cot_hoi(A[k], B[k])
        s += ["---", "", f"## {k}", "", "**Bình luận:**", ""] + _khoi(chu[k]["binh_luan"]) + [""]
        if chu[k]["binh_luan_cha"].strip():
            s += ["**Bình luận cha** (chỉ để hiểu; nhãn là của bình luận trên):", ""] + _khoi(chu[k]["binh_luan_cha"][:400]) + [""]
        s += ["| Cột | A | B |", "|---|---|---|"]
        for c in COT_NHAN:
            dam = "**" if c in hoi else ""
            s.append(f"| {dam}{c}{dam} ({TEN_COT[c]}) | {A[k][c] or '–'} | {B[k][c] or '–'} |")
        s += ["", f"- Ghi chú A: {A[k]['ghi_chu_a'] or '–'} (chưa chắc: {A[k]['chua_chac'] or '–'})",
              f"- Ghi chú B: {B[k]['ghi_chu'] or '–'} (chưa chắc: {B[k]['chua_chac'] or '–'})", "", "```phan_xu"]
        s += [f"{c}: " for c in hoi] + ["ly_do: ", "```", ""]
    return "\n".join(s)


def doc_phan_xu(chu: str) -> dict[int, dict[str, str]]:
    """{stt: {cột: giá trị B ghi}} từ phiếu phân xử; ô trống là chuỗi rỗng."""
    ra = {}
    for m in re.finditer(r"^## (\d+)[ \t]*$(.*?)^```phan_xu[ \t]*$(.*?)^```[ \t]*$", chu.replace("\r\n", "\n"), re.M | re.S):
        o = {}
        for dong in m[3].splitlines():
            if ":" in dong:
                k, _, v = dong.partition(":")
                o[k.strip()] = v.strip()
        ra[int(m[1])] = o
    return ra


def nhan_sau_phan_xu(A: dict[int, dict], B: dict[int, dict], px: dict[int, dict[str, str]]) -> tuple[list[dict], list[str], Counter]:
    """(nhãn cuối của mọi bình luận, các lỗi hay ca còn thiếu, đếm chọn A/B/khác theo cột)."""
    ra, loi, dem = [], [], Counter()
    for k in sorted(A):
        hoi = cot_hoi(A[k], B[k])
        m = {c: A[k][c] for c in COT_NHAN}
        o = px.get(k, {})
        if hoi:
            lq = o.get("lien_quan", "")
            lq = (A if lq.upper() == "A" else B)[k]["lien_quan"] if lq.upper() in ("A", "B") else mo_rong("lien_quan", lq)
            if "lien_quan" in hoi and lq and lq != "dien_thoai":
                hoi = [c for c in hoi if c != "noi_ve_thai_do"]   # chiều 1 không phải dien_thoai: chiều 2, 4 bỏ
            thieu = [c for c in hoi + ["ly_do"] if not o.get(c)]
            if k not in px or thieu:
                loi.append(f"stt {k}: chưa điền " + ", ".join(thieu if k in px else ["cả ca (không thấy khối phan_xu)"]))
                continue
            for c in hoi:
                v = o[c]
                if v.upper() in ("A", "B"):
                    m[c] = (A if v.upper() == "A" else B)[k][c]
                    dem[(c, v.upper())] += 1
                else:
                    m[c] = mo_rong(c, v)
                    dem[(c, "khác")] += 1
            if m["lien_quan"] != "dien_thoai":
                m["noi_ve_thai_do"] = ""
        try:
            kiem_tra(m, f"stt {k}")
        except LoiNhan as e:
            loi.append(str(e))
            continue
        ra.append({"stt": k, **m, "phan_xu": "co" if hoi else "khop", "ly_do": o.get("ly_do", "")})
    return ra, loi, dem


def _da_dien(chu: str) -> bool:
    return any(v for o in doc_phan_xu(chu).values() for v in o.values())


def chay() -> dict:
    A, B, loi, p_b = doc_ab()
    r = so_sanh(A, B)
    chu = {int(d["stt"]): d for d in doc_csv(PHIEU_K)}
    lech = []
    for s in r["lech"]:
        la, lb = thanh_nhan(A[s]), thanh_nhan(B[s])
        lech.append({"stt": s, "binh_luan": chu[s]["binh_luan"], "binh_luan_cha": chu[s]["binh_luan_cha"],
                     "chieu_lech": "; ".join(c for c in la if la[c] != lb[c]),
                     **{f"{c}_A": A[s][c] for c in COT_NHAN}, **{f"{c}_B": B[s][c] for c in COT_NHAN},
                     "chua_chac_A": A[s]["chua_chac"], "chua_chac_B": B[s]["chua_chac"],
                     "ghi_chu_A": A[s]["ghi_chu_a"], "ghi_chu_B": B[s]["ghi_chu"]})
    _ghi_csv(LECH, COT_LECH, lech)
    cc = Counter(ch for d in B.values() for ch in re.findall(r"[1-6]", d["chua_chac"]))
    BAO_CAO.write_text(viet_bao_cao(r, loi, cc, (_sha256(NHAN_K_A), _sha256(p_b)), date.today().isoformat()), encoding="utf-8")
    return {"phieu_B": p_b.name, "n": r["n"], "lech": len(r["lech"]), "loi_B": len(loi),
            "kappa": {c: round(r["mot"][c]["kappa"], 2) for c in r["mot"]}, "file": str(BAO_CAO)}


def phan_xu() -> dict:
    if PHAN_XU.exists() and _da_dien(PHAN_XU.read_text(encoding="utf-8")):
        raise SystemExit(f"{PHAN_XU.name} đã có người điền; không ghi đè.")
    A, B, _, _ = doc_ab()
    chu = {int(d["stt"]): d for d in doc_csv(PHIEU_K)}
    PHAN_XU.write_text(viet_phan_xu(A, B, chu, date.today().isoformat()), encoding="utf-8")
    return {"so_ca": sum(bool(cot_hoi(A[k], B[k])) for k in A), "file": str(PHAN_XU)}


def nhap() -> dict:
    A, B, _, _ = doc_ab()
    ra, loi, dem = nhan_sau_phan_xu(A, B, doc_phan_xu(PHAN_XU.read_text(encoding="utf-8")))
    if loi:
        return {"chua_xong": len(loi), "chi_tiet": loi[:15], "ghi_file": False}
    _ghi_csv(NHAN_K_PX, ("stt",) + COT_NHAN + ("phan_xu", "ly_do"), ra)
    return {"so_binh_luan": len(ra), "chon": {f"{c} {v}": n for (c, v), n in sorted(dem.items())}, "file": str(NHAN_K_PX)}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="So lô K, phân xử (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 7b)")
    p.add_argument("viec", nargs="?", default="so", choices=("so", "phan-xu", "nhap"))
    p.add_argument("--lo", default="K", choices=("K", "D2"), help="lô cần so (mặc định K)")
    a = p.parse_args(argv)
    dat_lo(a.lo)
    viec = a.viec
    kq = {"so": chay, "phan-xu": phan_xu, "nhap": nhap}[viec]()
    sys.stdout.reconfigure(encoding="utf-8")
    print(kq)


if __name__ == "__main__":
    main()

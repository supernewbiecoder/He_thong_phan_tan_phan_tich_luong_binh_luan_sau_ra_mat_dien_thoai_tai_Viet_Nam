"""Mục đích: B8: so ba nguồn (bộ nhãn từ dữ liệu, HAC, bộ nhãn đặt sẵn trên main), áp luật chốt bộ nhãn, ghi đề xuất giữ / thêm / gộp / bỏ kèm số liệu vào docs/3-gan-nhan/bao-cao-kham-pha-nhan.md (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 4.4, 9); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo:
    python -m src.labeling.b8

Đếm từ khóa HAC đọc cả bộ dữ liệu v4 (khoảng một phút). Báo cáo chỉ có số và tên nhãn, không có chữ bình luận.
Cột "luật nói" do code tính từ tỷ lệ; cột "đề xuất" là ý kiến của A (AI), ghi ở DE_XUAT, trưởng nhóm quyết.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date

from . import distribution as D
from .b7_labels import tach_cap
from .label_set import KHIA_CANH, LUAT_DOI_TUONG
from .light_clean import lam_sach_nhe
from .lot_k import doc_ab, so_sanh
from .sample import GOC, RA, RAW, _sha256

BAO_CAO = GOC / "docs" / "3-gan-nhan" / "bao-cao-kham-pha-nhan.md"
HAC = RA / "hac_ung_vien.csv"
NGUONG_THEM, NGUONG_GOP = 0.03, 0.01
# Bộ nhãn chốt (đặc tả bộ nhãn mục 8): nhãn khám phá -> nhãn chốt. Nhãn không có ở đây giữ nguyên.
GOP = {"noi_ve": {"nhiet_do": "hieu_nang", "am_thanh": "phan_cung_khac"}, "lien_quan": {"khong_noi_dung": "khong_xac_dinh"}}

# nhãn: (chiều, nguồn, nhãn đặt sẵn tương ứng, phục vụ gì, đề xuất của A, lý do)
# nguồn: "đặt sẵn" | "mới" | "tách" (tách ra từ một nhãn đặt sẵn: tính là nhãn mới, đặc tả mục 9)
DE_XUAT: dict[str, tuple] = {
    # chiều 1
    "dien_thoai": (1, "đặt sẵn", "Trực tiếp", "Q1–Q6: phần dữ liệu để phân tích", "giữ", "Luật 1"),
    "ngu_canh": (1, "đặt sẵn", "Ngữ cảnh", "Chất lượng dữ liệu: loại khỏi Q1–Q4", "giữ", "Luật 1"),
    "khong_lien_quan": (1, "đặt sẵn", "Không liên quan", "Chất lượng dữ liệu", "giữ", "Luật 1"),
    "nguoi_binh_luan": (1, "mới", "", "Chất lượng dữ liệu: tách cãi nhau khỏi ý kiến về máy", "thêm", "Luật 2. Là lỗi hay gặp nhất của A ở B7, nên cần nhãn riêng để người gán chú ý"),
    "khong_xac_dinh": (1, "mới", "", "Chất lượng dữ liệu", "thêm", "Luật 2. Chiều nào cũng cần nhãn \"không xác định\" (đặc tả mục 6)"),
    "khong_noi_dung": (1, "mới", "", "Chất lượng dữ liệu", "gộp vào `khong_xac_dinh`", "Luật 2: dưới 3%. Bình luận chỉ có emoji, dấu câu thì code nhận ra được, không cần người gán"),
    # chiều 2: khía cạnh
    "pin_sac": (2, "đặt sẵn", "Pin & sạc", "Q2–Q4", "giữ", "Luật 1"),
    "man_hinh": (2, "đặt sẵn", "Màn hình", "Q2–Q4", "giữ", "Luật 1"),
    "hieu_nang": (2, "đặt sẵn", "Hiệu năng (gồm nóng máy)", "Q2–Q4", "giữ", "Luật 1"),
    "camera": (2, "đặt sẵn", "Camera", "Q2–Q4", "giữ", "Luật 1"),
    "thiet_ke": (2, "đặt sẵn", "Thiết kế & độ bền", "Q2–Q4", "giữ", "Luật 1"),
    "phan_mem": (2, "đặt sẵn", "Phần mềm", "Q2–Q5", "giữ", "Luật 1"),
    "phan_cung_khac": (2, "đặt sẵn", "Phần cứng khác", "Q2–Q4", "giữ", "Luật 1"),
    "gia": (2, "đặt sẵn", "Giá", "Q2–Q4", "giữ", "Luật 1"),
    "bao_hanh_sua_chua": (2, "đặt sẵn", "Bảo hành & hậu mãi", "Q5", "giữ", "Luật 1. Hiếm, ít dữ liệu cho Q5"),
    "do_ben": (2, "tách", "Thiết kế & độ bền", "Q2, Q5 (rơi vỡ, vào nước)", "thêm", "Luật 2: từ 3%"),
    "nhiet_do": (2, "tách", "Hiệu năng (gồm nóng máy)", "Q2, Q5", "gộp vào `hieu_nang`", "Luật 2: dưới 3%; về lại như bộ đặt sẵn. Nóng máy cho Q5 thì ghi ở loại lỗi"),
    "am_thanh": (2, "tách", "Phần cứng khác", "Q2", "gộp vào `phan_cung_khac`", "Luật 2: dưới 3%; về lại như bộ đặt sẵn"),
    "mua_ban": (2, "mới", "", "Gián tiếp: tách chuyện mua ở đâu, trả góp khỏi `gia` (Q2–Q4)", "thêm", "Luật 2: từ 3%. κ lô K 0,57: đã sửa định nghĩa (đặc tả bộ nhãn mục 2.1). Gộp vào `gia` sẽ lẫn chỗ mua, trả góp vào ý kiến về giá"),
    "khac": (2, "mới", "", "Dự phòng", "giữ", "Chiều nào cũng có nhãn \"khác\" (đặc tả mục 6)"),
    # chiều 2: ngoài khía cạnh
    "may_chung": (2, "mới", "", "Q1 (đón nhận chung), Q3", "thêm", "Luật 2"),
    "hang_nguoi_dung": (2, "mới", "", "Chất lượng dữ liệu: lời về hãng, fan không tính cho máy; Q6", "thêm", "Luật 2"),
    # chiều 3
    "danh_gia": (3, "mới", "", "Q1–Q4: lọc bình luận có ý kiến", "thêm", "Luật 2"),
    "thong_tin": (3, "mới", "", "Chất lượng dữ liệu", "thêm", "Luật 2"),
    "hoi": (3, "mới", "", "Chất lượng dữ liệu: câu hỏi không phải ý kiến", "thêm", "Luật 2"),
    "de_nghi": (3, "mới", "", "Chất lượng dữ liệu", "thêm", "Luật 2"),
    "tranh_luan": (3, "mới", "", "Chất lượng dữ liệu; Q6", "thêm", "Luật 2"),
    "cong_kich": (3, "mới", "", "Lọc bình luận độc hại (quyết định 25/11); Q6", "thêm", "Luật 2"),
    "ban_than": (3, "mới", "", "Chất lượng dữ liệu; Q5 (người đã dùng kể)", "thêm", "Luật 2"),
    "dua": (3, "mới", "", "Tách đùa với công kích (quyết định 25/11)", "thêm", "Luật 2. κ lô K 0,42 dưới 0,6: phải sửa định nghĩa"),
    "minigame": (3, "mới", "", "Phép thử độ nhạy (quyết định 5 của kế hoạch)", "thêm", "Luật 2, có câu hỏi cần riêng nó"),
    "xa_giao": (3, "mới", "", "Chất lượng dữ liệu", "thêm", "Luật 2"),
    "khong_xac_dinh_3": (3, "mới", "", "Chất lượng dữ liệu", "giữ", "Chiều nào cũng cần nhãn \"không xác định\" (đặc tả mục 6)"),
    "bao_loi": (3, "mới", "", "Q5", "thêm", "Luật 2: dưới 3% nhưng Q5 cần riêng nó (ví dụ có sẵn trong luật)"),
    "quang_cao": (3, "đặt sẵn", "Spam: quảng cáo, mời liên hệ", "Chất lượng dữ liệu (spam)", "giữ", "Luật 1, 3"),
    # chiều 4
    "tich_cuc": (4, "đặt sẵn", "Khen", "Q1–Q4", "giữ", "Luật 1"),
    "tieu_cuc": (4, "đặt sẵn", "Chê", "Q1–Q5", "giữ", "Luật 1"),
    "khong_danh_gia": (4, "đặt sẵn", "Trung tính", "Q1–Q4 (không vào mẫu số Net)", "giữ", "Luật 1"),
    "so_sanh": (4, "mới", "", "Q3 (câu so sánh trực tiếp)", "thêm", "Luật 2"),
    # chiều 5, 6
    "co": (5, "đặt sẵn", "Đã dùng", "Q5", "giữ", "Luật 1"),
    "khong_ro": (5, "đặt sẵn", "Không rõ", "Q5", "giữ", "Luật 1"),
    "goi_ten_may": (6, "đặt sẵn", "Gọi tên máy", "Q2–Q4: biết nhãn thuộc máy nào", "giữ", "Luật 1"),
    "khong_nhac": (6, "đặt sẵn", "Không rõ", "Q2–Q4", "giữ", "Luật 1"),
    "chi_hang": (6, "mới", "", "Q2–Q4: lời về hãng không gán cho một máy", "thêm", "Luật 2"),
}
# nhãn đặt sẵn không có trong bộ nhãn từ dữ liệu
DAT_SAN_VANG = (
    ("Spam: lừa đảo, cờ bạc", "Không gặp trong mẫu (đã gán `quang_cao` nếu có)", "gộp vào `quang_cao`", "Luật 5: không câu hỏi nào bắt buộc cần riêng"),
    ("Spam: khác", "Không gặp", "bỏ", "Luật 5"),
    ("Đã dùng: chưa", "Không tách được với \"không rõ\" khi gán", "bỏ (gộp vào `khong_ro`)", "Luật 5: Q5 chỉ cần biết có dùng"),
    ("9 loại lỗi", "Chỉ 8 bình luận `bao_loi` trong 600", "để tầng sau", "Luật 5: Q5 cần, nhưng mẫu ngẫu nhiên không đủ dữ liệu; gán loại lỗi trên mẫu riêng các bình luận báo lỗi"),
    ("Máy được nhắc: chỉ suy được từ video", "Không dùng: bộ nhãn cấm suy tên máy từ video", "bỏ", "Trái quy tắc gán theo chữ viết"),
)
CHIEU_TEN = {1: "1. Liên quan tới gì", 2: "2. Nói về phần nào", 3: "3. Mục đích", 4: "4. Thái độ", 5: "5. Đã dùng máy", 6: "6. Máy được nhắc"}
CHIEU_KHOA = {1: "lien_quan", 2: "noi_ve", 3: "muc_dich", 5: "da_dung", 6: "may_nhac"}


def sang_bo_chot(d: dict) -> dict:
    """Một dòng có nhãn khám phá -> nhãn chốt. Gộp hai nhãn chiều 2 thì gộp luôn thái độ của chúng."""
    m = dict(d)
    m["lien_quan"] = GOP["lien_quan"].get(d["lien_quan"], d["lien_quan"])
    cap: dict[str, list[str]] = {}
    for k, td in tach_cap(d["noi_ve_thai_do"]).items():
        moi = cap.setdefault(GOP["noi_ve"].get(k, k), [])
        moi += [t for t in td if t not in moi]
    m["noi_ve_thai_do"] = "; ".join(f"{k}:{'+'.join(v)}" for k, v in cap.items())
    return m


def tu_khoa() -> dict[str, list[str]]:
    """Từ khóa của mỗi khía cạnh, lấy từ ánh xạ mã -> nhãn (label_set.LUAT_DOI_TUONG); bỏ từ khóa khớp nguyên ('=…')."""
    ra: dict[str, list[str]] = {}
    for nhom, tus in LUAT_DOI_TUONG:
        if nhom in KHIA_CANH:
            ra.setdefault(nhom, []).extend(t for t in tus if not t.startswith("="))
    return ra


def dem_tu_khoa() -> tuple[int, Counter]:
    """(số bình luận có nội dung, số bình luận có nhắc ít nhất một từ khóa của mỗi khía cạnh) trên cả v4 (đặc tả mục 4.4)."""
    mau = {k: re.compile(r"(?<!\w)(?:" + "|".join(re.escape(t) for t in sorted(v, key=len, reverse=True)) + r")(?!\w)")
           for k, v in tu_khoa().items()}
    n, dem = 0, Counter()
    with open(RAW, encoding="utf-8") as f:
        for dong in f:
            chu = lam_sach_nhe(json.loads(dong).get("text")).lower()
            if not chu:
                continue
            n += 1
            for k, m in mau.items():
                if m.search(chu):
                    dem[k] += 1
    return n, dem


def ty_le(tk: dict) -> dict[str, dict]:
    """Tỷ lệ của mọi nhãn trên phần áp dụng của chiều (đặc tả mục 9). Chiều 4 tính trên cặp, không có khoảng tin cậy."""
    ra = {}
    for nhan, (c, *_) in DE_XUAT.items():
        if c == 4:
            tong = sum(tk["so_cap"].values())
            x = sum(v for (_, t), v in tk["cap"].items() if t == nhan)
            ra[nhan] = {"x": x, "n": tong, "p": x / tong, "bl": None, "bu": None}
        else:
            ten = "khong_xac_dinh" if nhan == "khong_xac_dinh_3" else nhan
            ra[nhan] = tk[CHIEU_KHOA[c]][ten]
    return ra


def luat_noi(nguon: str, k: dict) -> tuple[str, bool]:
    """(luật tự động nói gì, có sát ngưỡng không). Chưa xét 'phục vụ câu hỏi': phần đó ở cột đề xuất."""
    p = k["p"]
    sat = k["bl"] is not None and any(k["bl"] <= t <= k["bu"] for t in (NGUONG_GOP, NGUONG_THEM))
    if nguon == "đặt sẵn":
        return ("giữ" if k["x"] else "luật 5"), sat
    if p >= NGUONG_THEM:
        return "thêm", sat
    return ("gộp (dưới 1%)" if p < NGUONG_GOP else "gộp, trừ khi có câu hỏi cần"), sat


def kappa_lo_k() -> dict[str, float]:
    A, B, _, _ = doc_ab()
    r = so_sanh(A, B)
    ra = {}
    for c in ("lien_quan", "da_dung", "may_nhac"):
        ra.update({k: v["kappa"] for k, v in r["mot"][c]["nhan"].items() if v["a"] or v["b"]})
    for c in ("noi_ve", "muc_dich"):
        ra.update({(k + "_3" if c == "muc_dich" and k == "khong_xac_dinh" else k): v["kappa"]
                   for k, v in r["nhieu"][c]["tung"].items() if v["a"] or v["b"]})
    ra.update({t: v["kappa"] for t, v in r["thai_do"].items()})
    return ra


def _pt(x) -> str:
    return "–" if x is None else f"{100 * x:.1f}".replace(".", ",")


def viet(tk: dict, tl: dict, kp: dict, n_raw: int, dem: Counter, hac_moi: list[str], ngay: str, tk_chot: dict) -> str:
    s = ["# Báo cáo khám phá nhãn: so ba nguồn và đề xuất chốt bộ nhãn (B8)", "",
         f"> Mục đích: Áp luật chốt bộ nhãn (đặc tả khám phá nhãn mục 9) lên từng nhãn: tỷ lệ trong mẫu phân bố, nguồn, kappa lô K, đối chiếu HAC trên cả bộ dữ liệu, đề xuất giữ / thêm / gộp / bỏ để trưởng nhóm quyết; cập nhật lần cuối: {ngay}.", "",
         "**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.b8`. Đề xuất nằm trong `src/labeling/b8.py` (`DE_XUAT`); "
         "trưởng nhóm quyết xong thì sửa đặc tả bộ nhãn, không sửa file này.", "",
         f"**Trạng thái: trưởng nhóm duyệt cả bảng ngày 26/11; bộ nhãn chốt ở [đặc tả bộ nhãn mục 8](dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611).** Đề xuất do A (AI) soạn. Tỷ lệ lấy từ [báo cáo phân bố](bao-cao-phan-bo-nhan.md): mẫu {tk['n']} bình luận, "
         "nhãn lô 1–5 do AI gán và trưởng nhóm đã kiểm cả 500, lô K hai bên gán mù và đã phân xử. Kappa lấy từ [báo cáo lô K](bao-cao-lo-k.md).", "",
         "**Cách đọc:**",
         "- *Luật nói*: code áp ngưỡng 3% và 1% lên tỷ lệ đo được. Chưa xét nhãn có phục vụ câu hỏi nào không.",
         "- *Đề xuất*: A xét thêm việc nhãn phục vụ câu nào (kế hoạch mục 6) hoặc giúp đánh giá chất lượng dữ liệu.",
         "- *Sát ngưỡng*: khoảng tin cậy 95% (bootstrap theo video) trùm lên 1% hay 3%. Vẫn quyết theo tỷ lệ đo được, nhưng nên xem lại.",
         "- *κ lô K*: kappa có/không của riêng nhãn đó giữa A và B. Nhãn dưới khoảng 10 bình luận thì kappa dao động mạnh.", ""]
    for c in range(1, 7):
        mau_so = {1: f"{tk['n']} bình luận", 2: f"{tk['n_dt']} bình luận `dien_thoai`", 3: f"{tk['n']} bình luận",
                  4: f"{sum(tk['so_cap'].values())} cặp (bình luận, nhãn chiều 2)", 5: f"{tk['n']} bình luận", 6: f"{tk['n']} bình luận"}[c]
        s += [f"## Chiều {CHIEU_TEN[c]}", "", f"Phần áp dụng: {mau_so}.", "",
              "| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |", "|---|---|---|---|---|---|---|---|---|---|"]
        for nhan, (cc, nguon, ds, pv, dx, ly) in DE_XUAT.items():
            if cc != c:
                continue
            k = tl[nhan]
            ln, sat = luat_noi(nguon, k)
            ktc = "–" if k["bl"] is None else (f"≤ {_pt(k['bu'])}" if k["x"] == 0 else f"[{_pt(k['bl'])}; {_pt(k['bu'])}]")
            kap = kp.get(nhan)
            s.append(f"| `{nhan.removesuffix('_3')}` | {nguon} | {ds or '–'} | {_pt(k['p'])} | {ktc}{' **sát ngưỡng**' if sat else ''} | "
                     f"{'–' if kap is None else f'{kap:.2f}'.replace('.', ',')} | {ln} | {pv} | **{dx}** | {ly} |")
        s.append("")
    s += ["## Nhãn đặt sẵn không có trong bộ nhãn từ dữ liệu", "",
          "| Nhãn đặt sẵn | Trong mẫu | **Đề xuất** | Lý do |", "|---|---|---|---|"]
    s += [f"| {a} | {b} | **{c}** | {d} |" for a, b, c, d in DAT_SAN_VANG]
    s += ["", "## Phân bố theo bộ nhãn chốt", "",
          "Cùng mẫu, sau khi gộp theo đặc tả bộ nhãn mục 8. Chỉ ghi các nhãn có thay đổi; nhãn khác giữ số như các bảng trên.", "",
          "| Chiều | Nhãn chốt | Gộp từ | % | KTC 95% (bootstrap video) |", "|---|---|---|---|---|"]
    for c, ten, nhan in ((1, "lien_quan", "khong_xac_dinh"), (2, "noi_ve", "hieu_nang"), (2, "noi_ve", "phan_cung_khac")):
        k = tk_chot[ten][nhan]
        tu = ", ".join(f"`{a}`" for a, b in GOP[ten].items() if b == nhan)
        s.append(f"| {c} | `{nhan}` | `{nhan}`, {tu} | {_pt(k['p'])} | [{_pt(k['bl'])}; {_pt(k['bu'])}] |")
    s += ["", "## Đối chiếu HAC trên cả bộ dữ liệu (đặc tả mục 4.4)", "",
          "**Do AI làm, chưa có người kiểm.** Chỉ dùng để tìm khía cạnh mà mẫu 600 bỏ sót, không phải phân bố.", "",
          f"**1. Đếm từ khóa** trên {format(n_raw, ',').replace(',', '.')} bình luận có nội dung của v4. Từ khóa của mỗi khía cạnh lấy từ các mã đã gom vào nó "
          "(`label_set.py`). Số này là bình luận **có nhắc từ khóa**, chưa chắc nói về khía cạnh đó (vd \"cam\" có thể là quả cam).", "",
          "| Khía cạnh | Bình luận có nhắc | % cả bộ dữ liệu | % trong mẫu (chiều 2, trên `dien_thoai`) |", "|---|---|---|---|"]
    s += [f"| `{k}` | {format(dem[k], ',').replace(',', '.')} | {_pt(dem[k] / n_raw)} | {_pt(tl[k]['p'])} |"
          for k, _ in sorted(dem.items(), key=lambda u: -u[1])]
    s += ["", "**2. Rà 100 ứng viên HAC đầu** (`hac_ung_vien.csv`): ứng viên nào là khía cạnh mà bộ nhãn chưa có.", "",
          ("Không có. " if not hac_moi else "Có: " + ", ".join(hac_moi) + ". ")
          + "Các ứng viên là khía cạnh đều thuộc nhãn đã có (pin, sạc, giá, game, chip, màn, cam, ảnh, thiết kế, viền, màu, loa, nhiệt, tản nhiệt, "
          "chống rung, đa nhiệm, cấu hình, phần mềm, ios, chính hãng…). Còn lại là mảnh từ (\"độ\", \"sức\", \"kế\", \"năng\"), tên hãng, tên dòng, hay từ chung.", "",
          "## Tóm tắt đề xuất", ""]
    dem_dx = Counter("gộp" if v[4].startswith("gộp") else v[4] for v in DE_XUAT.values())
    s += [f"- {len(DE_XUAT)} nhãn: " + ", ".join(f"{k} {v}" for k, v in dem_dx.most_common()) + ".",
          "- Bộ nhãn chốt: chiều 1 có 5 nhãn; chiều 2 có 11 khía cạnh + 2 nhãn ngoài khía cạnh + `khac`; chiều 3 có 13; chiều 4, 5, 6 không đổi.",
          "- **Phải sửa định nghĩa trước khi gán chính thức** (κ lô K dưới 0,6): `dua`, `khong_xac_dinh` (chiều 1); `mua_ban` đã sửa 26/11.",
          "- Chiều 6 chưa ghi **tên** máy: Q3, Q4 cần biết máy nào, nên guideline gán chính thức phải thêm trường tên máy."]
    return "\n".join(s) + "\n"


def chay() -> dict:
    dong, _, _ = D.doc()
    tk = D.thong_ke(dong)
    tl = ty_le(tk)
    n_raw, dem = dem_tu_khoa()
    tk_chot = D.thong_ke([sang_bo_chot(d) for d in dong])
    BAO_CAO.write_text(viet(tk, tl, kappa_lo_k(), n_raw, dem, [], date.today().isoformat(), tk_chot), encoding="utf-8")
    return {"so_nhan": len(DE_XUAT), "n_raw": n_raw, "file": str(BAO_CAO), "sha_raw": _sha256(RAW)[:12]}


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="B8 (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 9)").parse_args(argv)
    kq = chay()
    sys.stdout.reconfigure(encoding="utf-8")
    print(kq)


if __name__ == "__main__":
    main()

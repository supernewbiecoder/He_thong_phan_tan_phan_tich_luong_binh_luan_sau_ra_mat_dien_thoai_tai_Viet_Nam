"""Mục đích: Gom mã tự do thành bộ nhãn (B5): ánh xạ mã -> nhãn theo 6 chiều, đếm số bình luận mỗi nhãn, lô gặp lần đầu, bão hòa; ghi docs/3-gan-nhan/bao-cao-bo-nhan.md (luật: docs/3-gan-nhan/dac-ta-bo-nhan.md); cập nhật lần cuối: 2026-11-24.

Chạy từ gốc repo:
    python -m src.labeling.label_set

Số ở đây là số bình luận có ít nhất một mã rơi vào nhãn, theo mã tự do của A. Đó là bằng chứng nhãn có trong dữ liệu,
không phải phân bố: phân bố tính ở B7 sau khi gán lại theo bộ nhãn và có người kiểm.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .code_stats import tach_ma
from .sample import GOC, LO_MA_HOA_MO, RA, _sha256, doc_csv

PHIEU_A = RA / "phieu_ma_hoa_mo.csv"
PHIEU_B = RA / "phieu_ma_hoa_mo_B.csv"
BAO_CAO = GOC / "docs" / "3-gan-nhan" / "bao-cao-bo-nhan.md"

# ---- Nhóm của một đối tượng: để suy nhãn chiều 2, và nhãn chiều 1 ---------------------------------
# Xét theo thứ tự, gặp luật đầu tiên khớp thì dừng. Từ khóa khớp nguyên từ trong đối tượng (viết thường);
# từ khóa bắt đầu bằng "=" thì đối tượng phải đúng bằng nó. Một nhóm có thể xuất hiện nhiều lần để xử lý ngoại lệ.
LUAT_DOI_TUONG: list[tuple[str, list[str]]] = [
    ("khong_noi_dung", ["=không nội dung"]),
    ("khong_xac_dinh", ["=không hiểu", "=không rõ"]),
    ("nguoi_binh_luan", ["=bình luận cha", "=người khác", "=người chê"]),
    ("camera", ["quay", "video 8k", "chống rung"]),                       # trước video_kenh: "quay video" là camera
    ("hang_nguoi_dung", ["fan", "người chê apple", "người dìm iphone", "người dùng", "người mua", "người có điều kiện",
                         "người chưa mua", "kiện", "samsung display"]),
    ("video_kenh", ["người review", "người làm kênh", "người trong video", "kênh", "nội dung kênh", "video",
                    "phỏng vấn", "nhạc nền", "xem sớm", "lên sóng", "like", "test", "bài test", "speedtest", "drop test",
                    "drip test", "tháo máy", "máy gửi review", "so sánh", "bảng xếp hạng", "người xem nước ngoài",
                    "áo 6 sao", "nghề này"]),
    ("minigame_qua", ["minigame", "quà", "miễn phí"]),
    ("khong_lien_quan", ["máy tính bảng", "tablet", "lịch sử", "lưỡi bò", "tủ đá", "giá bánh mì", "con số 69"]),
    ("bao_hanh_sua_chua", ["bảo hành", "sửa", "sửa chữa", "cách sửa", "thay màn", "đổi trả", "hoàn tiền"]),
    ("do_ben", ["độ bền", "bền", "chống nước", "kháng nước", "nứt", "bung"]),
    ("nhiet_do", ["nhiệt độ", "nóng", "nóng máy", "quá nhiệt"]),
    ("pin_sac", ["pin", "sạc", "sạc nhanh", "tụt pin", "hao pin", "super vooc", "mah", "thời gian dùng"]),
    ("thiet_ke", ["cụm cam", "cụm camera", "ít đụng hàng"]),                # trước camera: hình dáng cụm camera
    ("phan_cung_khac", ["dán màn hình", "miếng dán", "xuất màn hình"]),     # trước man_hinh: phụ kiện, cổng xuất
    ("camera", ["cam", "camera", "chụp", "zoom", "ảnh", "cảm biến", "gcam", "màu da", "màu ảnh", "vùng tối", "tone",
                "hình ảnh", "cà mặt"]),
    ("man_hinh", ["màn", "màn hình", "tai thỏ", "viên thuốc", "vô cực", "natural mode", "120hz", "oled", "2k",
                  "độ sáng"]),
    ("hieu_nang", ["chip", "hiệu năng", "exynos", "snap", "snapdragon", "gpu", "ram", "đa nhiệm", "game", "chơi game",
                   "liên quân", "pubg", "antutu", "điểm số", "xung chip", "tốc độ", "8gen1", "cấu hình", "thông số",
                   "shader compilation", "thao tác chạm", "mượt", "độ ổn định", "=ch"]),
    ("thiet_ke", ["thiết kế", "ngoại hình", "màu", "màu máy", "trọng lượng", "kích thước", "mỏng", "viền", "lưng",
                  "mặt sau", "vỏ", "nhôm", "titan", "gốm", "góc bo", "logo", "dán skin", "nếp gấp", "cạnh gập"]),
    ("phan_mem", ["phần mềm", "hệ điều hành", "ios", "android", "miui", "hyper", "cập nhật", "ứng dụng", "app", "ai",
                  "tối ưu", "thông báo", "bảo mật", "ngôn ngữ", "google", "thuật toán", "tính năng", "chạy ngầm",
                  "quảng cáo tự hiện", "tắt quảng cáo", "rom", "build", "cài lên", "danh bạ"]),
    ("am_thanh", ["loa", "mic", "âm thanh", "thu âm", "khử ồn"]),
    ("phan_cung_khac", ["bộ nhớ", "sim", "khay sim", "=5g", "kết nối", "wifi", "rung", "face id", "vân tay", "mở khóa",
                        "bút", "spen", "s pen", "ốp", "kính cường lực", "tai nghe", "apple watch", "smartwatch",
                        "phụ kiện", "ổ cứng", "cổng"]),
    ("gia", ["giá", "tiền", "rẻ", "đắt", "khuyến mãi"]),
    ("may_chung", ["=máy nên mua", "=máy (chung)"]),   # trước mua_ban, hang_nguoi_dung: "máy (chung)" không phải hãng
    ("mua_ban", ["mua", "chỗ mua", "cửa hàng", "trả góp", "xách tay", "chính hãng", "đổi máy", "lên đời", "trade lên",
                 "dân buôn", "đặt", "đơn đặt hàng", "ngày có hàng", "doanh số", "bản hàn", "bản mỹ", "chọn bản"]),
    ("hang_nguoi_dung", ["(chung)", "thương hiệu", "hãng mỹ", "hãng nhật", "mỗi hãng", "marketing", "tim cook",
                         "tẩy chay", "hàng trung quốc", "máy trung quốc", "samsung và iphone"]),
    ("may_chung", ["máy", "điện thoại", "flagship", "máy gập", "fold", "đời sau", "số đời máy", "dòng", "phiên bản",
                   "trải nghiệm", "chất lượng sản phẩm", "nâng cấp", "ít thay đổi", "không đổi mới", "khác biệt",
                   "ra mắt", "công nghệ", "tính đa dụng"]),
]
_HANG = r"iphone|ip|samsung|ss|galaxy|xiaomi|redmi|poco|oppo|vivo|huawei|honor|pixel|sony|htc|oneplus|realme|vsmart|" \
        r"vinsmart|bphone|nokia|apple|motorola|asus|nothing|tecno|infinix|meizu|lg|blackberry|lumia"
# Tên máy cụ thể: tên hãng/dòng kèm số, hay số kèm hậu tố đời máy (vd "s23u", "14prm", "note 10", "16+", "15 thường").
MAY_CU_THE = re.compile(
    r"(?<!\w)(?:(?:" + _HANG + r"|note|mi|s|a|k|n|x|z ?flip|z ?fold|fold|find n?|mate|gt neo|ace|tab|pad|xs|g)"
    r" ?\d+\w*(?: ?(?:pro|max|ultra|plus|prm|pm|promax|lite|edge|5g|\+))*|\d+ ?(?:pro|max|ultra|plus|prm|pm|"
    r"promax|thường|\+)\w*|xs max|950xl|u ultra)(?!\w)")
HANG = re.compile(r"(?<!\w)(?:" + _HANG + r")(?!\w)")

# Nhãn chiều 2. Khía cạnh là một phần, một tính chất của điện thoại, hay một việc khi mua và dùng; hai nhãn còn lại nói
# về điện thoại mà không nêu phần nào (đặc tả khám phá nhãn, Thuật ngữ; đặc tả bộ nhãn mục 2).
KHIA_CANH = ("pin_sac", "man_hinh", "hieu_nang", "nhiet_do", "camera", "thiet_ke", "do_ben", "phan_mem", "am_thanh",
             "phan_cung_khac", "gia", "mua_ban", "bao_hanh_sua_chua")
NGOAI_KHIA_CANH = ("may_chung", "hang_nguoi_dung")
NHOM_DIEN_THOAI = KHIA_CANH + NGOAI_KHIA_CANH
NHOM_NGU_CANH = ("video_kenh", "minigame_qua")

# ---- Chiều 3: mục đích (theo hành vi, danh sách đóng) ---------------------------------------------
MUC_DICH = {
    "danh_gia": ("khen", "chê", "nhận xét", "so sánh", "dự đoán"),
    "hoi": ("hỏi",),
    "thong_tin": ("giải thích", "trả lời", "nhắc"),
    "de_nghi": ("khuyên", "góp ý", "yêu cầu"),
    "ban_than": ("kể", "khoe", "than", "mong muốn", "lo ngại"),
    "bao_loi": ("báo lỗi",),
    "tranh_luan": ("đồng tình", "phản bác", "bênh", "cãi nhau"),
    "dua": ("đùa", "trêu"),
    "cong_kich": ("cà khịa", "chửi"),
    "minigame": ("dự thi", "xin"),
    "quang_cao": ("quảng cáo", "mời"),
    "xa_giao": ("chào", "cảm ơn", "cười"),
    "khong_xac_dinh": ("?",),
}
HANH_VI_SANG_MUC_DICH = {h: md for md, hs in MUC_DICH.items() for h in hs}

# ---- Chiều 4: thái độ với từng nhãn chiều 2 --------------------------------------------------------
THAI_DO = {"khen": "tich_cuc", "chê": "tieu_cuc", "báo lỗi": "tieu_cuc", "so sánh": "so_sanh"}   # còn lại: khong_danh_gia

# ---- Chiều 5, báo lỗi: nhận ra từ mã cũ (A mã trước khi có hành vi `báo lỗi`) ------------------------
DA_DUNG = re.compile(r"(?<!\w)(?:(?:đã|đang) (?:dùng|xài|sài)|người nhà|của mình)(?!\w)")
TU_LOI = re.compile(r"(?<!\w)(?:lỗi|hỏng|hư|sọc|xanh màn|kẻ màn|chết màn|nứt|bung|hở|rộp|tụt pin|hao pin|nóng|"
                    r"đơ|treo|khởi động lại|màn nháy|không nhận|phồng|vỡ|bay mặt kính|sập nguồn|lag|trễ)(?!\w)")
PHU_DINH = re.compile(r"(?<!\w)(?:không|ko|k|chưa|chẳng|ít|hết)(?: \w+){0,3} ?$")   # "không hề thấy nóng", "ít lỗi"


def _co_tu_loi(chu: str) -> bool:
    """Có chữ chỉ lỗi mà không bị phủ định ngay trước (trong 3 chữ)."""
    return any(not PHU_DINH.search(chu[max(0, m.start() - 30):m.start()]) for m in TU_LOI.finditer(chu))

CHIEU = {
    "lien_quan": "1. Liên quan tới gì (một nhãn)",
    "noi_ve": "2. Nói về phần nào của điện thoại (nhiều nhãn)",
    "muc_dich": "3. Mục đích (nhiều nhãn)",
    "thai_do": "4. Thái độ (nhiều nhãn, theo từng nhãn chiều 2)",
    "da_dung": "5. Đã dùng máy (một nhãn)",
    "may_nhac": "6. Máy được nhắc (một nhãn)",
}


def _khop(o: str, tu: str) -> bool:
    if tu.startswith("="):
        return o == tu[1:]
    return re.search(r"(?<!\w)" + re.escape(tu) + r"(?!\w)", o) is not None


def nhom_doi_tuong(doi_tuong: str) -> str:
    """Nhóm của một đối tượng theo LUAT_DOI_TUONG (nhãn chiều 2, hoặc nhóm phụ để suy nhãn chiều 1); tên máy cụ thể hay
    tên hãng còn lại thành máy chung; không khớp: 'chua_xep'."""
    o = doi_tuong.lower().strip()
    for nhom, tus in LUAT_DOI_TUONG:
        if any(_khop(o, t) for t in tus):
            return nhom
    if MAY_CU_THE.search(o) or HANG.search(o):
        return "may_chung"
    return "chua_xep"


def _la_bao_loi(m: dict) -> bool:
    """Mã báo lỗi: hành vi `báo lỗi`; hoặc mã cũ kể chuyện máy mình (`kể` hay ghi chú đã/đang dùng) có chữ chỉ lỗi."""
    if m["hanh_vi"] == "báo lỗi":
        return True
    cua_minh = m["hanh_vi"] == "kể" or any(DA_DUNG.search(p.lower()) for p in m["phu"])
    return cua_minh and _co_tu_loi(" ; ".join([m["doi_tuong"]] + m["phu"]).lower())


def gan_nhan(dong: dict) -> dict[str, set[str]]:
    """Nhãn của một bình luận theo 6 chiều, suy từ ô ma_tu_do (và ghi chú 'Không liên quan điện thoại')."""
    ma = tach_ma(dong.get("ma_tu_do") or "")
    nhom = [nhom_doi_tuong(m["doi_tuong"]) for m in ma]
    bao_loi = [_la_bao_loi(m) for m in ma]
    noi_ve = {n for n in nhom if n in NHOM_DIEN_THOAI}
    muc_dich = {HANH_VI_SANG_MUC_DICH.get(m["hanh_vi"], "khac") for m in ma} | ({"bao_loi"} if any(bao_loi) else set())
    thai_do = {f"{n}:{'tieu_cuc' if bl else THAI_DO.get(m['hanh_vi'], 'khong_danh_gia')}"
               for m, n, bl in zip(ma, nhom, bao_loi) if n in NHOM_DIEN_THOAI}
    khong_lq = "không liên quan điện thoại" in (dong.get("ghi_chu") or "").lower()
    if noi_ve:
        lien_quan = "dien_thoai"
    elif any(n in NHOM_NGU_CANH for n in nhom):
        lien_quan = "ngu_canh"
    elif "nguoi_binh_luan" in nhom:
        lien_quan = "nguoi_binh_luan"
    elif khong_lq or "khong_lien_quan" in nhom:
        lien_quan = "khong_lien_quan"
    elif "khong_noi_dung" in nhom:
        lien_quan = "khong_noi_dung"
    else:
        lien_quan = "khong_xac_dinh"
    da_dung = any(m["hanh_vi"] in ("kể", "báo lỗi") or any(DA_DUNG.search(p.lower()) for p in m["phu"]) for m in ma)
    chu_may = " ; ".join(m["doi_tuong"] + " " + " ".join(m["phu"]) for m in ma).lower()
    may_nhac = "goi_ten_may" if MAY_CU_THE.search(chu_may) else "chi_hang" if HANG.search(chu_may) else "khong_nhac"
    return {"lien_quan": {lien_quan}, "noi_ve": noi_ve, "muc_dich": muc_dich, "thai_do": thai_do,
            "da_dung": {"co" if da_dung else "khong_ro"}, "may_nhac": {may_nhac}}


def _dem_khia_canh(dong: list[dict]) -> dict[str, int]:
    """Trong các bình luận có nhãn dien_thoai: bao nhiêu có ít nhất một khía cạnh, bao nhiêu chỉ có nhãn ngoài khía cạnh."""
    nhan = [n for n in map(gan_nhan, dong) if n["lien_quan"] == {"dien_thoai"}]
    co = sum(bool(n["noi_ve"] & set(KHIA_CANH)) for n in nhan)
    return {"dien_thoai": len(nhan), "co_khia_canh": co, "chi_ngoai_khia_canh": len(nhan) - co}


def thong_ke_nhan(dong: list[dict], lo_ngau_nhien: tuple = LO_MA_HOA_MO) -> dict:
    """Số bình luận mỗi nhãn (lô ngẫu nhiên gộp, và mẫu có chủ đích riêng), lô gặp lần đầu, số nhãn mới từng lô."""
    nn = [d for d in dong if d["lo"] in lo_ngau_nhien]
    cd = [d for d in dong if d["lo"] not in lo_ngau_nhien]
    dem: dict[str, Counter] = {c: Counter() for c in CHIEU}
    dem_cd: dict[str, Counter] = {c: Counter() for c in CHIEU}
    lan_dau: dict[tuple[str, str], str] = {}
    for lo in lo_ngau_nhien:
        for d in (x for x in nn if x["lo"] == lo):
            for c, nhans in gan_nhan(d).items():
                for nh in nhans:
                    dem[c][nh] += 1
                    lan_dau.setdefault((c, nh), lo)
    for d in cd:
        for c, nhans in gan_nhan(d).items():
            dem_cd[c].update(nhans)
    moi = {lo: sorted(f"{c}/{nh}" for (c, nh), l in lan_dau.items() if l == lo and c != "thai_do") for lo in lo_ngau_nhien}
    chua_xep = Counter(m["doi_tuong"] for d in dong for m in tach_ma(d["ma_tu_do"])
                       if nhom_doi_tuong(m["doi_tuong"]) == "chua_xep")
    return {"n": len(nn), "n_cd": len(cd), "dem": dem, "dem_cd": dem_cd, "lan_dau": lan_dau, "moi": moi,
            "chua_xep": chua_xep, "khia_canh_nn": _dem_khia_canh(nn), "khia_canh_cd": _dem_khia_canh(cd)}


def do_phu(dong: list[dict]) -> tuple[int, int, Counter]:
    """(số mã, số mã có đối tượng chưa xếp được, các đối tượng đó) trên một phiếu khác, vd phiếu B."""
    ma = [m for d in dong for m in tach_ma(d.get("ma_tu_do") or "")]
    chua = Counter(m["doi_tuong"] for m in ma if nhom_doi_tuong(m["doi_tuong"]) == "chua_xep")
    return len(ma), sum(chua.values()), chua


def _bang(tieu_de: list[str], hang: list[list]) -> str:
    s = ["| " + " | ".join(tieu_de) + " |", "|" + "---|" * len(tieu_de)]
    return "\n".join(s + ["| " + " | ".join(str(o) for o in h) + " |" for h in hang])


def viet_bao_cao(tk: dict, sha_a: str, phu_b: tuple | None, sha_b: str | None) -> str:
    ngay = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    s = [
        "# Báo cáo bộ nhãn (B5)",
        "",
        f"> Mục đích: Số bình luận có mỗi nhãn của bộ nhãn nháp, theo mã tự do của A; lô gặp lần đầu; bão hòa; cập nhật lần cuối: {ngay}.",
        "",
        "**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.label_set`. "
        f"Nguồn: `data/kham-pha/phieu_ma_hoa_mo.csv` (SHA-256 `{sha_a[:8]}…{sha_a[-4:]}`), dữ liệu v4. "
        "Định nghĩa nhãn: [đặc tả bộ nhãn](dac-ta-bo-nhan.md); ánh xạ mã → nhãn: `src/labeling/label_set.py`.",
        "",
        "**Cách đọc:** mỗi số là **số bình luận** có ít nhất một mã rơi vào nhãn, đếm bằng luật từ khóa trên mã tự do của A "
        "(do AI mã, chưa có người kiểm từng mã). Đây là bằng chứng nhãn có trong dữ liệu, **không phải phân bố**: "
        "không ghi phần trăm. Phân bố tính ở B7, sau khi gán lại theo bộ nhãn và có người kiểm. "
        "Chiều 5 và 6 đếm gần đúng từ mã (mã tự do không ghi đủ hai điều này).",
        "",
    ]
    lan_dau = tk["lan_dau"]
    for c, ten in CHIEU.items():
        if c == "thai_do":
            td = ("tich_cuc", "tieu_cuc", "so_sanh", "khong_danh_gia")
            hang = [[f"`{kc}`"] + [tk["dem"][c].get(f"{kc}:{t}", 0) for t in td]
                    for kc, _ in tk["dem"]["noi_ve"].most_common()]
            s += [f"## {ten}", "", f"Lô 1–5 (n = {tk['n']}). Một bình luận có thể vừa khen vừa chê cùng một nhãn chiều 2.", "",
                  _bang(["Nhãn chiều 2"] + [f"`{t}`" for t in td], hang), ""]
            continue
        hang = [[f"`{nh}`", n, tk["dem_cd"][c].get(nh, 0), lan_dau.get((c, nh), "")]
                for nh, n in sorted(tk["dem"][c].items(), key=lambda x: -x[1])]
        hang += [[f"`{nh}`", 0, n, ""] for nh, n in tk["dem_cd"][c].items() if nh not in tk["dem"][c]]
        tieu_de = ["Nhãn", f"Lô 1–5 (n = {tk['n']})", f"CD (n = {tk['n_cd']})", "Lô gặp lần đầu"]
        if c == "noi_ve":   # nói rõ nhãn nào là khía cạnh
            tieu_de.insert(1, "Loại")
            hang = [[h[0], "khía cạnh" if h[0].strip("`") in KHIA_CANH else "ngoài khía cạnh"] + h[1:] for h in hang]
        s += [f"## {ten}", "", _bang(tieu_de, hang), ""]
        if c == "noi_ve":
            s += ["Trong các bình luận có nhãn `dien_thoai` ở chiều 1:", ""]
            for ten_lo, k in (("Lô 1–5", tk["khia_canh_nn"]), ("CD", tk["khia_canh_cd"])):
                s.append(f"- {ten_lo}: {k['dien_thoai']} bình luận; {k['co_khia_canh']} có ít nhất một khía cạnh, "
                         f"{k['chi_ngoai_khia_canh']} chỉ có nhãn ngoài khía cạnh.")
            s.append("")
    s += ["## 7. Bão hòa", "",
          "Số nhãn mới ở từng lô, theo thứ tự lô 1→5, của chiều 1, 2, 3, 5, 6 (chiều 4 là cặp nhãn chiều 2 × thái độ, không tính). "
          "Luật dừng: lô 5 không có nhãn mới ([đặc tả mục 6](dac-ta-kham-pha-nhan.md#6-gom-mã-thành-bộ-nhãn-và-bão-hòa-b5)).",
          "",
          _bang(["Lô", "Số nhãn mới", "Nhãn mới"], [[lo, len(v), ", ".join(f"`{x}`" for x in v)] for lo, v in tk["moi"].items()]),
          "",
          "## 8. Đối tượng chưa xếp vào nhãn nào", "",
          f"Phiếu A (cả lô 1–5 và CD): {sum(tk['chua_xep'].values())} mã: "
          + (", ".join(f"`{o}`" for o, _ in tk["chua_xep"].most_common()) or "không có") + ".",
          ""]
    if phu_b:
        so_ma, chua, ds = phu_b
        s += [f"**Độ phủ trên phiếu B** (trưởng nhóm mã độc lập; `phieu_ma_hoa_mo_B.csv`, SHA-256 `{sha_b[:8]}…{sha_b[-4:]}`): "
              f"{chua}/{so_ma} mã có đối tượng chưa xếp được: "
              + (", ".join(f"`{o}`" for o, _ in ds.most_common()) or "không có") + ".", ""]
    return "\n".join(s)


def chay(phieu_a: Path = PHIEU_A, phieu_b: Path = PHIEU_B, bao_cao: Path = BAO_CAO) -> dict:
    tk = thong_ke_nhan(doc_csv(phieu_a))
    phu_b = do_phu(doc_csv(phieu_b)) if phieu_b.exists() else None
    bao_cao.write_text(viet_bao_cao(tk, _sha256(phieu_a), phu_b, _sha256(phieu_b) if phu_b else None) + "\n",
                       encoding="utf-8")
    return {"n": tk["n"], "nhan_moi_theo_lo": {lo: len(v) for lo, v in tk["moi"].items()},
            "chua_xep_A": sum(tk["chua_xep"].values()), "chua_xep_B": phu_b[1] if phu_b else None, "file": str(bao_cao)}


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description="Bộ nhãn B5 (docs/3-gan-nhan/dac-ta-bo-nhan.md)").parse_args(argv)
    kq = chay()
    sys.stdout.reconfigure(encoding="utf-8")
    print(kq)


if __name__ == "__main__":
    main()

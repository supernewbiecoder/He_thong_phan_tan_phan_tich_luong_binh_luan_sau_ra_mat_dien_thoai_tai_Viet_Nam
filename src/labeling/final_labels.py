"""Mục đích: Bộ nhãn chốt ngày 26/11 (docs/3-gan-nhan/dac-ta-bo-nhan.md mục 8) dưới dạng hằng: mã nhãn từng chiều, tên tiếng Việt, chữ viết tắt trên phiếu (docs/3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md mục 2). Là nguồn duy nhất cho contract v3, luật mốc, phân tích, DB, dashboard và phiếu gán; cập nhật lần cuối: 2026-11-26.

Các file khác import từ đây, không chép tay danh sách nhãn. Sửa bộ nhãn thì sửa đặc tả bộ nhãn, file này,
contracts/aspect-mention.schema.json và test trong cùng một lần (tests/test_labeling_final_labels.py kiểm contract khớp).
"""

from __future__ import annotations

# ---- Chiều 1: liên quan tới gì (một nhãn) ------------------------------------------------------------
RELEVANCE = ("dien_thoai", "ngu_canh", "nguoi_binh_luan", "khong_lien_quan", "khong_xac_dinh")

# ---- Chiều 2: nói về phần nào (nhiều nhãn) ---------------------------------------------------------------
# 11 khía cạnh. Thứ tự này là thứ tự hiển thị ở báo cáo và dashboard.
ASPECTS = ("pin_sac", "man_hinh", "hieu_nang", "camera", "thiet_ke", "do_ben", "phan_mem", "phan_cung_khac", "gia",
           "mua_ban", "bao_hanh_sua_chua")
NON_ASPECTS = ("may_chung", "hang_nguoi_dung")   # nói về điện thoại mà không nêu phần nào: có thái độ, không là khía cạnh
RESERVE = ("khac",)                              # phần của máy chưa có ở trên (dự phòng)
DIM2_LABELS = ASPECTS + NON_ASPECTS + RESERVE    # mọi giá trị của trường `aspect` trong contract v3

# ---- Chiều 3: mục đích (nhiều nhãn) ----------------------------------------------------------------------
PURPOSES = ("danh_gia", "hoi", "thong_tin", "de_nghi", "ban_than", "bao_loi", "tranh_luan", "dua", "cong_kich",
            "minigame", "quang_cao", "xa_giao", "khong_xac_dinh")
SPAM_PURPOSE = "quang_cao"   # bộ chốt gộp "lừa đảo, cờ bạc" vào đây: nhãn người coi là spam khi có mục đích này

# ---- Chiều 4: thái độ, theo từng nhãn chiều 2 -------------------------------------------------------------
ATTITUDES = ("tich_cuc", "tieu_cuc", "so_sanh", "khong_danh_gia")
POSITIVE, NEGATIVE, COMPARISON, NO_OPINION = ATTITUDES

# ---- Chiều 5, 6 -------------------------------------------------------------------------------------------
OWNER = ("co", "khong_ro")
MODEL_MENTION = ("goi_ten_may", "chi_hang", "khong_nhac")

# ---- Tên tiếng Việt để hiển thị ----------------------------------------------------------------------------
NAMES = {
    "pin_sac": "Pin & sạc", "man_hinh": "Màn hình", "hieu_nang": "Hiệu năng (gồm nóng máy)", "camera": "Camera",
    "thiet_ke": "Thiết kế", "do_ben": "Độ bền", "phan_mem": "Phần mềm",
    "phan_cung_khac": "Phần cứng khác (gồm loa, mic, phụ kiện)", "gia": "Giá", "mua_ban": "Mua bán",
    "bao_hanh_sua_chua": "Bảo hành & sửa chữa", "may_chung": "Cả máy (không nêu phần nào)",
    "hang_nguoi_dung": "Hãng & người dùng", "khac": "Khác",
    "tich_cuc": "Khen", "tieu_cuc": "Chê", "so_sanh": "So sánh", "khong_danh_gia": "Không đánh giá",
}

# ---- Chữ viết tắt trên phiếu (hướng dẫn gán chính thức mục 2) ---------------------------------------------
ABBR_RELEVANCE = {"D": "dien_thoai", "N": "ngu_canh", "B": "nguoi_binh_luan", "L": "khong_lien_quan",
                  "X": "khong_xac_dinh"}
ABBR_DIM2 = {"pin": "pin_sac", "man": "man_hinh", "hn": "hieu_nang", "cam": "camera", "tk": "thiet_ke", "db": "do_ben",
             "pm": "phan_mem", "pc": "phan_cung_khac", "gia": "gia", "mua": "mua_ban", "bh": "bao_hanh_sua_chua",
             "mc": "may_chung", "hang": "hang_nguoi_dung", "khac": "khac"}
ABBR_ATTITUDE = {"+": "tich_cuc", "-": "tieu_cuc", "=": "so_sanh", "0": "khong_danh_gia"}
ABBR_PURPOSE = {"dg": "danh_gia", "hoi": "hoi", "tt": "thong_tin", "dn": "de_nghi", "bt": "ban_than", "bl": "bao_loi",
                "tl": "tranh_luan", "dua": "dua", "ck": "cong_kich", "mg": "minigame", "qc": "quang_cao",
                "xg": "xa_giao", "x": "khong_xac_dinh"}
ABBR_OWNER = {"c": "co", "k": "khong_ro"}
ABBR_MODEL_MENTION = {"t": "goi_ten_may", "h": "chi_hang", "k": "khong_nhac"}
ABBR_VIETNAMESE = {"co": True, "khong": False}

# Nhãn khám phá (src/labeling/label_set.py) -> nhãn chốt; bảng GOP của src/labeling/b8.py
MERGED_FROM_EXPLORATION = {"nhiet_do": "hieu_nang", "am_thanh": "phan_cung_khac", "khong_noi_dung": "khong_xac_dinh"}


def _kiem() -> None:
    """Bảng viết tắt phải phủ đúng bộ nhãn; sai thì dừng ngay khi import."""
    assert set(ABBR_RELEVANCE.values()) == set(RELEVANCE)
    assert set(ABBR_DIM2.values()) == set(DIM2_LABELS)
    assert set(ABBR_ATTITUDE.values()) == set(ATTITUDES)
    assert set(ABBR_PURPOSE.values()) == set(PURPOSES)
    assert set(ABBR_OWNER.values()) == set(OWNER)
    assert set(ABBR_MODEL_MENTION.values()) == set(MODEL_MENTION)
    assert set(DIM2_LABELS) | set(ATTITUDES) <= set(NAMES)


_kiem()

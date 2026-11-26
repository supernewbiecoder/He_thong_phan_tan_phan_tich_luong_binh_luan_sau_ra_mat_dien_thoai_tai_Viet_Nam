"""Mục đích: Luật mốc chấm thái độ khen/chê/không đánh giá (`tich_cuc`/`tieu_cuc`/`khong_danh_gia` của bộ nhãn chốt) cho một đoạn chữ đã chuẩn hóa (`text_norm`), dùng ở bước suy luận theo bình luận (docs/4-mo-hinh/dac-ta-suy-luan.md mục 4); cập nhật lần cuối: 2026-11-26.

Chỉ là mốc để so sánh và để chạy thông cả chuỗi khi chưa có mô hình. Chưa đo trên nhãn người: không dùng để kết luận.
Luật không nhận thái độ `so_sanh` (cần biết bên hơn), nên không bao giờ trả nhãn đó.
Cách chấm: đếm cụm từ khen, cụm từ chê (cụm dài khớp trước, "tụt nhanh" là chê dù "nhanh" là khen); cụm đứng sau
từ phủ định trong 2 chữ thì đổi chiều ("không lag" là khen); câu hỏi là không đánh giá.
"""

from __future__ import annotations

import re

from src.labeling.final_labels import NEGATIVE, NO_OPINION, POSITIVE

POS, NEG, NEU = POSITIVE, NEGATIVE, NO_OPINION

KHEN = (
    "tốt", "ngon", "đẹp", "mượt", "trâu", "ổn", "ok", "ổn định", "xịn", "xịn xò", "đỉnh", "đỉnh cao", "tuyệt", "tuyệt vời",
    "xuất sắc", "thích", "ưng", "ưng ý", "hài lòng", "đáng mua", "đáng tiền", "đáng đồng tiền", "nhanh", "rẻ", "bền", "nét",
    "sắc nét", "khỏe", "khủng", "mạnh", "mạnh mẽ", "ngon lành", "hợp lý", "sang trọng", "mát", "nhẹ", "mỏng", "chill",
    "ấn tượng", "yêu",
)
# Cố ý không đưa vào vì nhiều nghĩa: "sáng" (buổi sáng), "chất" (chất liệu), "sang" (sang năm), "hơn" (so sánh)
CHE = (
    "tệ", "kém", "yếu", "chán", "dở", "xấu", "lag", "giật", "khựng", "đơ", "nóng", "hao", "tụt", "lỗi", "hỏng", "hư",
    "sọc", "ám", "đắt", "mắc", "chát", "thất vọng", "phí tiền", "chậm", "mờ", "nhòe", "rè", "thua", "tồi", "rác", "hẻo",
    "chai", "nứt", "vỡ", "trầy", "xước", "ức chế", "bực", "khó chịu", "cùi", "phèn", "nặng", "dày", "lởm", "fail",
    "tụt nhanh", "hao nhanh", "hết nhanh", "nhanh hết", "nóng nhanh", "nhanh nóng", "sạc chậm", "không đáng",
)
PHU_DINH = ("không", "chẳng", "chả", "chưa", "không hề", "chẳng hề", "đâu có", "hết", "đỡ", "bớt")
SO_CHU_PHU_DINH = 2   # từ phủ định đứng trong bao nhiêu chữ ngay trước cụm thì đổi chiều

_CUM = sorted([(c, 1) for c in KHEN] + [(c, -1) for c in CHE], key=lambda x: -len(x[0].split()))   # cụm dài khớp trước
_PHU_DINH_RE = re.compile(r"(?<!\w)(?:" + "|".join(sorted(map(re.escape, PHU_DINH), key=len, reverse=True)) + r")(?!\w)")
# Câu hỏi: có "?" hoặc kết thúc bằng "không/chưa/sao/nhỉ". Không gồm "nào" ("không lag chút nào" là khen) và "chứ".
_CAU_HOI_RE = re.compile(r"\?|(?<!\w)(?:không|chưa|sao|nhỉ)\s*$")


def _diem(text_norm: str) -> int:
    s = text_norm.lower()
    da_khop = [False] * len(s)
    diem = 0
    for cum, dau in _CUM:
        for m in re.finditer(rf"(?<!\w){re.escape(cum)}(?!\w)", s):
            if any(da_khop[m.start():m.end()]):
                continue
            for i in range(m.start(), m.end()):
                da_khop[i] = True
            truoc = s[:m.start()].split()[-SO_CHU_PHU_DINH:]
            co_phu_dinh = bool(_PHU_DINH_RE.search(" ".join(truoc)))
            diem += -dau if co_phu_dinh else dau
    return diem


def cam_xuc(text_norm: str) -> str:
    """POS (`tich_cuc`), NEG (`tieu_cuc`) hoặc NEU (`khong_danh_gia`) cho một đoạn `text_norm` (thường là một mệnh đề)."""
    if not text_norm or _CAU_HOI_RE.search(text_norm.strip().lower()):
        return NEU
    d = _diem(text_norm)
    return POS if d > 0 else NEG if d < 0 else NEU

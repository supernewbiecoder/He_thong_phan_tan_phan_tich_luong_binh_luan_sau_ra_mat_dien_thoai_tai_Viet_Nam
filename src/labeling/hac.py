"""Mục đích: HAC (High Adjective Count) bản tiếng Việt không cần tách từ: tìm ứng viên khía cạnh là cụm đứng ngay trước một từ đánh giá, trên cả bộ dữ liệu (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 4); cập nhật lần cuối: 2026-11-22.

Chạy từ gốc repo:
    python -m src.labeling.hac    # ghi data/kham-pha/hac_ung_vien.csv và .manifest.json; dừng nếu file đã có người chấm
    python -m src.labeling.hac --ghi-de   # chạy lại cả khi đã có người chấm (phần đã chấm sẽ mất)

Ý tưởng từ Eirinaki và cộng sự (2012), Wiegard và cộng sự (ECIS 2017): mỗi tính từ đánh giá được gán cho danh từ
gần nhất. Tiếng Việt đặt danh từ trước từ đánh giá ("pin trâu", "màn hình đẹp"), nên chỉ cần nhìn ngược lại.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .light_clean import an_nhac_ten, lam_sach_nhe
from .sample import GOC, RA, RAW, SEED, _sha256, da_co_nguoi_dien, doc_csv

# Từ đánh giá (thay cho từ loại "tính từ" của bản gốc). Sửa danh sách là đổi kết quả: ghi vào báo cáo.
TU_DANH_GIA = frozenset("""
tốt đẹp xấu ngon dở tệ kém yếu khỏe mạnh mượt lag giật khựng đơ trâu hẻo nóng mát ổn ok xịn đỉnh chán nhanh
chậm nét mờ nhòe rẻ đắt mắc chát nặng nhẹ mỏng dày bền cùi phèn sang ảo rõ sáng tối to nhỏ hay lỗi
""".split()) | frozenset({"sắc nét", "tuyệt vời", "xuất sắc", "ấn tượng", "thất vọng", "hợp lý", "ngon lành",
                          "ổn định", "mạnh mẽ", "khủng khiếp", "tạm được", "quá tệ"})

# Đứng giữa danh từ và từ đánh giá thì bỏ qua: mức độ, phủ định (cả dạng teencode), hư từ, động từ cảm nhận
# ("thiết kế nhìn đẹp" → "thiết kế"). Bổ sung teencode và động từ cảm nhận sau lần chạy đầu 22/11 (báo cáo khám phá nhãn).
TU_BO_QUA = frozenset("""
quá rất hơi khá cực siêu cũng vẫn thì là lắm đã bị được không chẳng chả chưa hơn nhất rồi có thật khá
vô cùng càng đều cứ mới còn ko k kh khg hk hok hông khum đc dc thấy nhìn trông nghe
""".split())

# Không bao giờ là ứng viên: đại từ, loại từ, hư từ, từ chỉ định
TU_DUNG = frozenset("""
tôi mình tao tớ em anh chị bạn ae bác ông bà cô chú nó họ chúng ta mày này đó kia ấy nọ cái con chiếc các những
mấy một hai ba và với của cho nhưng mà nên vì rồi đi ra vào lên xuống ở khi lúc nhiều ít vậy thế như gì sao ai
đâu nào chứ nhé nha ạ à ơi ư nhỉ hả đây kìa thôi luôn lại nữa cả ngay sẽ đang vừa từng hay rằng thì là nhưng
quá rất hơi khá cực siêu cũng vẫn lắm đã bị được không chẳng chả chưa hơn nhất có thật vô càng đều cứ mới còn
làm nói phải chắc biết giờ nay sự để trước sau muốn lấy xem kêu đúng chỉ mãi đủ
""".split()) | TU_DANH_GIA | TU_BO_QUA

NHIN_NGUOC = 4      # nhìn ngược tối đa 4 âm tiết
SO_UNG_VIEN = 300   # số ứng viên ghi ra
SO_VI_DU = 3
CAT_VI_DU = 120
COT = ("hang", "ung_vien", "so_am_tiet", "diem_hac", "so_binh_luan", "so_tu_danh_gia_khac_nhau",
       "tu_danh_gia_hay_gap", "vi_du_1", "vi_du_2", "vi_du_3", "la_khia_canh", "nhom", "ghi_chu")
COT_NGUOI_CHAM = ("la_khia_canh", "nhom", "ghi_chu")

TACH_CAU = re.compile(r"[.!?…;\n]+")
AM_TIET = re.compile(r"[^\W_]+", re.UNICODE)


def _tu_danh_gia_tai(tu: list[str], i: int) -> int:
    """Số âm tiết của từ đánh giá bắt đầu ở vị trí i (2 hoặc 1), 0 nếu không phải."""
    if i + 1 < len(tu) and f"{tu[i]} {tu[i + 1]}" in TU_DANH_GIA:
        return 2
    return 1 if tu[i] in TU_DANH_GIA else 0


def _la_noi_dung(am_tiet: str) -> bool:
    return am_tiet not in TU_DUNG and not am_tiet.isdigit()


def trich_ung_vien(chu: str) -> list[tuple[str, str]]:
    """Các cặp (ứng viên, từ đánh giá) trong một đoạn chữ đã làm sạch. Ứng viên là 1 hoặc 2 âm tiết, chữ thường."""
    ra = []
    for cau in TACH_CAU.split(chu.lower()):
        tu = AM_TIET.findall(cau)
        i = 0
        while i < len(tu):
            dai = _tu_danh_gia_tai(tu, i)
            if not dai:
                i += 1
                continue
            danh_gia = " ".join(tu[i:i + dai])
            # nhìn ngược: bỏ qua TU_BO_QUA, dừng ở từ đánh giá khác, lấy tối đa 2 âm tiết nội dung liền nhau
            noi_dung: list[tuple[int, str]] = []
            j = i - 1
            while j >= 0 and i - j <= NHIN_NGUOC and len(noi_dung) < 2:
                if tu[j] in TU_DANH_GIA:
                    break
                if tu[j] in TU_BO_QUA:
                    if noi_dung:   # đã có âm tiết nội dung thì từ bỏ qua cắt đứt cụm
                        break
                    j -= 1
                    continue
                if not _la_noi_dung(tu[j]):
                    break
                noi_dung.append((j, tu[j]))
                j -= 1
            if noi_dung:
                ra.append((noi_dung[0][1], danh_gia))
                if len(noi_dung) == 2 and noi_dung[1][0] == noi_dung[0][0] - 1:
                    ra.append((f"{noi_dung[1][1]} {noi_dung[0][1]}", danh_gia))
            i += dai
    return ra


def _ghi_csv(p: Path, cot: list[str], dong: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    with open(tam, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        w.writerows(dong)
    os.replace(tam, p)


def chay(nguon: Path = RAW, so_ung_vien: int = SO_UNG_VIEN, ghi_de: bool = False) -> dict:
    """Hai lượt qua dữ liệu: đếm điểm, rồi lấy câu ví dụ cho các ứng viên điểm cao."""
    ra = RA / "hac_ung_vien.csv"
    if not ghi_de and ra.exists() and da_co_nguoi_dien(doc_csv(ra), set(COT) - set(COT_NGUOI_CHAM)):
        raise SystemExit(f"{ra.name} đã có người chấm; không ghi đè. Thêm --ghi-de nếu thật sự muốn chạy lại "
                         "(phần đã chấm sẽ mất).")
    diem, so_bl = Counter(), Counter()
    danh_gia_kem: dict[str, Counter] = defaultdict(Counter)
    lan_cuoi: dict[str, int] = {}
    so_doc = 0
    with open(nguon, encoding="utf-8") as f:
        for k, dong in enumerate(f):
            chu = lam_sach_nhe(json.loads(dong).get("text"))
            if not chu:
                continue
            so_doc += 1
            for uv, dg in trich_ung_vien(chu):
                diem[uv] += 1
                danh_gia_kem[uv][dg] += 1
                if lan_cuoi.get(uv) != k:
                    so_bl[uv] += 1
                    lan_cuoi[uv] = k

    top = [uv for uv, _ in diem.most_common(so_ung_vien)]
    can_vi_du = set(top)
    vi_du: dict[str, list[str]] = defaultdict(list)
    da_gap: Counter = Counter()
    rng = random.Random(SEED)
    with open(nguon, encoding="utf-8") as f:   # lấy mẫu hồ chứa: mỗi ứng viên giữ ngẫu nhiên 3 câu ví dụ
        for dong in f:
            chu = lam_sach_nhe(json.loads(dong).get("text"))
            for cau in TACH_CAU.split(chu):
                gap = {uv for uv, _ in trich_ung_vien(cau)} & can_vi_du
                for uv in sorted(gap):   # sorted: thứ tự set đổi theo từng tiến trình, seed sẽ không giữ được câu ví dụ
                    da_gap[uv] += 1
                    doan = an_nhac_ten(cau.strip())[:CAT_VI_DU]
                    if len(vi_du[uv]) < SO_VI_DU:
                        vi_du[uv].append(doan)
                    else:
                        r = rng.randrange(da_gap[uv])
                        if r < SO_VI_DU:
                            vi_du[uv][r] = doan

    dong = []
    for h, uv in enumerate(top, start=1):
        vd = vi_du.get(uv, []) + [""] * SO_VI_DU
        dong.append({
            "hang": h, "ung_vien": uv, "so_am_tiet": len(uv.split()), "diem_hac": diem[uv], "so_binh_luan": so_bl[uv],
            "so_tu_danh_gia_khac_nhau": len(danh_gia_kem[uv]),
            "tu_danh_gia_hay_gap": ", ".join(f"{dg} ({n})" for dg, n in danh_gia_kem[uv].most_common(5)),
            "vi_du_1": vd[0], "vi_du_2": vd[1], "vi_du_3": vd[2], "la_khia_canh": "", "nhom": "", "ghi_chu": "",
        })
    _ghi_csv(ra, list(COT), dong)
    manifest = {
        "chay_luc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nguon": {"file": nguon.resolve().relative_to(GOC).as_posix() if nguon.resolve().is_relative_to(GOC) else str(nguon),
                  "sha256": _sha256(nguon)},
        "so_binh_luan_da_doc": so_doc,
        "tham_so": {"nhin_nguoc": NHIN_NGUOC, "so_ung_vien": so_ung_vien, "so_tu_danh_gia": len(TU_DANH_GIA),
                    "so_tu_bo_qua": len(TU_BO_QUA), "so_tu_dung": len(TU_DUNG)},
        "so_ung_vien_khac_nhau": len(diem),
        "tong_diem": sum(diem.values()),
    }
    (RA / "hac_ung_vien.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="HAC tiếng Việt (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 4)")
    p.add_argument("--ghi-de", action="store_true", help="chạy lại cả khi file đã có người chấm (phần đã chấm sẽ mất)")
    kq = chay(ghi_de=p.parse_args(argv).ghi_de)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

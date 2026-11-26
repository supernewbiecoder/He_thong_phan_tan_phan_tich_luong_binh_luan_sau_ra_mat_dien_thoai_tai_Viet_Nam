"""Mục đích: Lệnh chạy cả chuỗi xử lý theo lô (docs/0-chung/luong-xu-ly.md mục 2): tầng 2 → suy luận → aggregates và Q1–Q5; cập nhật lần cuối: 2026-11-20.

Chạy từ gốc repo, mỗi ngày một lần sau khi crawler đã lấy thêm dữ liệu (hoặc bất cứ khi nào cần số mới):
    python -m src.run                          # cả 3 bước
    python -m src.run --tu suy_luan            # bỏ qua tầng 2 (file tầng 2 đã có và không đổi)
    python -m src.run --den suy_luan           # dừng trước bước phân tích

Mỗi bước ghi đè kết quả của lần chạy trước (không cộng dồn), nên chạy lại bao nhiêu lần cũng ra cùng kết quả
với cùng dữ liệu vào. Bước phân tích là code của Công việc 12, đọc bộ 4 máy ở config/analysis.yaml.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

GOC_REPO = Path(__file__).resolve().parents[1]
RAW = GOC_REPO / "src" / "ingest" / "data" / "raw" / "comments.jsonl"
DA_XU_LY = GOC_REPO / "data" / "processed" / "comments.jsonl"
MENTION = GOC_REPO / "data" / "aspect_mentions.jsonl"
CAC_BUOC = ("tien_xu_ly", "suy_luan", "phan_tich")


def chay(tu: str = CAC_BUOC[0], den: str = CAC_BUOC[-1]) -> int:
    """Chạy các bước từ `tu` tới `den`; trả mã thoát (0 là xong)."""
    buoc = CAC_BUOC[CAC_BUOC.index(tu):CAC_BUOC.index(den) + 1]
    if not buoc:
        print(f"--tu {tu} đứng sau --den {den}: không có bước nào để chạy", file=sys.stderr)
        return 2
    for ten in buoc:
        t0 = time.time()
        print(f"== {ten} ==", file=sys.stderr)
        if ten == "tien_xu_ly":
            from src.processing import run as tang_2
            if not RAW.exists():
                print(f"Không thấy dữ liệu raw: {RAW}", file=sys.stderr)
                return 2
            man = tang_2.chay(RAW, DA_XU_LY)
            print(f"   {man['ra']['so_dong']:,} bình luận → {DA_XU_LY}", file=sys.stderr)
        elif ten == "suy_luan":
            from src.models import run as suy_luan
            if not DA_XU_LY.exists():
                print(f"Không thấy file tầng 2: {DA_XU_LY}. Chạy bước tien_xu_ly trước.", file=sys.stderr)
                return 2
            man = suy_luan.chay(DA_XU_LY, MENTION)
            print(f"   {man['ra']['so_mention']:,} mention từ {man['ra_binh_luan']['so_binh_luan']:,} bình luận → {MENTION}",
                  file=sys.stderr)
        else:
            from src.analysis import build_aggregates
            from src.models.run import MODEL_VERSION, file_binh_luan_cv12
            ma = build_aggregates.main(["--mentions", str(MENTION), "--comments", str(file_binh_luan_cv12(MENTION)),
                                        "--model-version", MODEL_VERSION])
            if ma != 0:
                print("Bước phân tích dừng. Hay gặp nhất: bộ 4 máy trong config/analysis.yaml không có mention nào "
                      "(chờ Công việc 2 chốt bộ máy). Đọc thông báo lỗi JSON ở trên.", file=sys.stderr)
                return ma
        print(f"   xong sau {time.time() - t0:.0f} giây", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Chạy cả chuỗi xử lý theo lô (docs/0-chung/luong-xu-ly.md)")
    p.add_argument("--tu", choices=CAC_BUOC, default=CAC_BUOC[0], help="bắt đầu từ bước nào")
    p.add_argument("--den", choices=CAC_BUOC, default=CAC_BUOC[-1], help="dừng sau bước nào")
    a = p.parse_args(argv)
    return chay(a.tu, a.den)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

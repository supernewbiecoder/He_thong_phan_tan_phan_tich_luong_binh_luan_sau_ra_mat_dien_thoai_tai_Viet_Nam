"""Mục đích: Lệnh chạy cả chuỗi xử lý theo lô (docs/0-chung/luong-xu-ly.md mục 2): tầng 2 → suy luận → aggregates và Q1–Q5, và tùy chọn nạp MongoDB cho dashboard; cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo, mỗi ngày một lần sau khi crawler đã lấy thêm dữ liệu (hoặc bất cứ khi nào cần số mới):
    python -m src.run                          # cả 3 bước
    python -m src.run --tu suy_luan            # bỏ qua tầng 2 (file tầng 2 đã có và không đổi)
    python -m src.run --den suy_luan           # dừng trước bước phân tích
    python -m src.run --den nap_db             # thêm bước nạp MongoDB (MONGO_URI, MONGO_DB) cho dashboard
    python -m src.run --tu nap_db --den nap_db # chỉ nạp lại DB từ kết quả đã có

Mặc định dừng sau bước phân tích, để máy không có MongoDB vẫn chạy được chuỗi; bước nap_db phải gọi rõ.

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
AGG_DIR = GOC_REPO / "data" / "aggregates" / "current"
DANH_MUC = GOC_REPO / "config" / "pipeline.yaml"
CAC_BUOC = ("tien_xu_ly", "suy_luan", "phan_tich", "nap_db")
MAC_DINH_DEN = "phan_tich"


def nap_db() -> int:
    """Tạo collection, index (init_db) rồi nạp danh mục máy, bình luận tầng 2, mention, aggregates, Q1–Q5."""
    import os

    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    from src.storage import init_db, load_db
    uri, ten_db = os.getenv("MONGO_URI", "mongodb://localhost:27017"), os.getenv("MONGO_DB", "smartphone_analytics")
    can = [DA_XU_LY, MENTION, AGG_DIR / "aggregates.jsonl", AGG_DIR / "business_questions.json"]
    thieu = [str(p) for p in can if not p.exists()]
    if thieu:
        print(f"Thiếu kết quả để nạp: {thieu}. Chạy các bước trước.", file=sys.stderr)
        return 2
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")   # không có MongoDB thì dừng, không âm thầm ghi vào bộ nhớ
        init_db.init_database(client, db_name=ten_db)
        for dong in load_db.load_all(client[ten_db], models=DANH_MUC, comments=DA_XU_LY, mentions=MENTION,
                                     aggregates=AGG_DIR / "aggregates.jsonl",
                                     analysis=AGG_DIR / "business_questions.json"):
            print(f"   {dong}", file=sys.stderr)
    except PyMongoError as loi:
        print(f"Không nạp được MongoDB ({type(loi).__name__}). Kiểm MONGO_URI và MongoDB đã chạy chưa.",
              file=sys.stderr)
        return 2
    except ValueError as loi:
        print(f"Dữ liệu không nạp được: {loi}", file=sys.stderr)
        return 2
    return 0


def chay(tu: str = CAC_BUOC[0], den: str = MAC_DINH_DEN) -> int:
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
        elif ten == "nap_db":
            ma = nap_db()
            if ma != 0:
                return ma
        else:
            from src.analysis import build_aggregates
            from src.models.run import MODEL_VERSION, file_binh_luan_cv12
            ma = build_aggregates.main(["--mentions", str(MENTION), "--comments", str(file_binh_luan_cv12(MENTION)),
                                        "--model-version", MODEL_VERSION])
            if ma != 0:
                print("Bước phân tích dừng. Hay gặp nhất: bộ 4 máy trong config/analysis.yaml không có mention nào. "
                      "Đọc thông báo lỗi JSON ở trên.", file=sys.stderr)
                return ma
        print(f"   xong sau {time.time() - t0:.0f} giây", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Chạy cả chuỗi xử lý theo lô (docs/0-chung/luong-xu-ly.md)")
    p.add_argument("--tu", choices=CAC_BUOC, default=CAC_BUOC[0], help="bắt đầu từ bước nào")
    p.add_argument("--den", choices=CAC_BUOC, default=MAC_DINH_DEN,
                   help=f"dừng sau bước nào (mặc định {MAC_DINH_DEN}; nap_db cần MongoDB)")
    a = p.parse_args(argv)
    return chay(a.tu, a.den)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

"""Mục đích: Hàm dùng chung cho các notebook trong notebooks/: tìm gốc repo, đường dẫn dữ liệu, đọc JSONL và manifest, đọc bộ 4 máy, hiện ký tự vô hình, in bảng trước → sau; cập nhật lần cuối: 2026-11-19.

Notebook nào cũng mở đầu bằng:
    from helpers import *
"""

from __future__ import annotations

import json
import sys
import unicodedata
import re
from pathlib import Path

import pandas as pd
from IPython.display import display


def tim_goc_repo() -> Path:
    """Đi ngược lên từ thư mục hiện tại tới khi gặp config/pipeline.yaml, để mở notebook từ đâu cũng chạy được."""
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "config" / "pipeline.yaml").exists():
            return p
    raise FileNotFoundError("Không tìm thấy gốc repo (thư mục có config/pipeline.yaml)")


ROOT = tim_goc_repo()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))   # để import code trong src/

RAW_PATH = ROOT / "src" / "ingest" / "data" / "raw" / "comments.jsonl"        # crawler ghi ra (tầng 1)
VIDEOS_PATH = ROOT / "src" / "ingest" / "data" / "raw" / "videos.jsonl"
MODELS_PATH = ROOT / "src" / "ingest" / "data" / "models.json"                # danh mục máy kèm ngày ra mắt
PROCESSED_PATH = ROOT / "data" / "processed" / "comments.jsonl"               # src/processing/run.py ghi ra (tầng 2)
MANIFEST_PATH = PROCESSED_PATH.with_suffix(".manifest.json")
ANALYSIS_CONFIG = ROOT / "config" / "analysis.yaml"                           # bộ 4 máy dùng cho Q1–Q5

N_SHOW = 50   # số dòng in ra ở mỗi danh sách


def thiet_lap_hien_thi() -> None:
    """Hiện đủ mọi cột, không cắt ngắn bình luận dài."""
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.max_rows", 1000)
    pd.set_option("display.width", None)


def doc_jsonl(duong_dan: Path, cot: list[str] | None = None) -> pd.DataFrame:
    """Đọc file JSONL từng dòng. `cot` = chỉ giữ các trường này (đỡ tốn bộ nhớ). Không đổi kiểu dữ liệu."""
    dong = []
    with open(duong_dan, "rb") as f:
        for d in f:
            if d.strip():
                r = json.loads(d)
                dong.append({k: r.get(k) for k in cot} if cot else r)
    return pd.DataFrame(dong, columns=cot)


def doc_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def doc_da_xu_ly(cot: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    """Đọc file tầng 2 (`data/processed/comments.jsonl`) và manifest của nó. Báo rõ nếu chưa chạy lệnh tầng 2."""
    if not PROCESSED_PATH.exists() or not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có {PROCESSED_PATH.relative_to(ROOT).as_posix()}. Chạy lệnh tầng 2 trước, từ gốc repo:\n"
            "    .\\.venv\\Scripts\\python.exe -m src.processing.run\n"
            "(docs/2-tien-xu-ly/huong-dan.md mục 3)")
    from src.processing import PIPELINE_VERSION
    man = doc_manifest()
    print(f"File: {PROCESSED_PATH.relative_to(ROOT).as_posix()} | {man['ra']['so_dong']:,} dòng | "
          f"code {man['pipeline_version']}, chạy lúc {man['processed_at']}")
    if man["pipeline_version"] != PIPELINE_VERSION:
        print(f"⚠ File được tạo bằng {man['pipeline_version']}, code hiện tại là {PIPELINE_VERSION}: chạy lại lệnh tầng 2.")
    if man.get("chi_chay_thu"):
        print("⚠ File này là bản chạy thử (--limit), không phải toàn bộ dữ liệu.")
    return doc_jsonl(PROCESSED_PATH, cot), man


def doc_bo_may() -> dict[str, str]:
    """Bộ 4 máy {X, P, R1, R2} lấy từ config/analysis.yaml: cùng một bộ với phân tích Q1–Q5 (Công việc 12)."""
    import yaml
    cfg = yaml.safe_load(ANALYSIS_CONFIG.read_text(encoding="utf-8"))
    doi_thu = list(cfg.get("rival_models") or [])
    return {"X": cfg["target_model"], "P": cfg["predecessor_model"],
            **{f"R{i + 1}": m for i, m in enumerate(doi_thu)}}


def mau_ngau_nhien(df: pd.DataFrame, n: int | None, seed: int = 0) -> pd.DataFrame:
    """n dòng ngẫu nhiên (tái lập được); n = None hoặc lớn hơn số dòng thì trả cả bảng."""
    return df if n is None or n >= len(df) else df.sample(n, random_state=seed)


KY_HIEU = {"\n": "⏎", "\t": "⇥", "\r": "␍"}
DAU_CACH_THUA = re.compile(r" {2,}|^ +| +$", re.M)


def lo_ra(s) -> str:
    """Chuỗi để hiển thị: ký tự vô hình hiện thành ký hiệu nhìn thấy được, dấu cách thừa hiện là ·."""
    if not isinstance(s, str):
        return "<null>"
    out = []
    for ch in s:
        if ch in KY_HIEU:
            out.append(KY_HIEU[ch])
        elif ch != " " and unicodedata.category(ch) in ("Cc", "Cf", "Cs", "Zs", "Zl", "Zp"):
            out.append(f"⟨U+{ord(ch):04X}⟩")
        else:
            out.append(ch)
    return DAU_CACH_THUA.sub(lambda m: "·" * len(m.group()), "".join(out))


def bao_cao(ten: str, truoc: pd.Series, sau: pd.Series, ma: pd.Series, tong: int | None = None,
            ghi_vao: list | None = None, n: int = N_SHOW) -> int:
    """In số bình luận một bước đã sửa và tối đa n ví dụ trước → sau. Trả số bình luận bị sửa.

    ma: comment_id cùng chỉ số với truoc/sau. tong: mẫu số khi tính % (mặc định len(truoc)).
    ghi_vao: danh sách để ghi một dòng tổng kết.
    """
    doi = truoc != sau
    so, tong = int(doi.sum()), tong or len(truoc)
    if ghi_vao is not None:
        ghi_vao.append({"bước": ten, "số bình luận bị sửa": so, "tỷ lệ (%)": round(100 * so / max(tong, 1), 3)})
    print(f"{ten}: sửa {so:,} / {tong:,} bình luận ({100 * so / max(tong, 1):.3f}%)")
    if so:
        idx = doi[doi].index[:n]
        display(pd.DataFrame({
            "comment_id": ma.loc[idx].values,
            "trước": truoc.loc[idx].map(lo_ra).values,
            "sau": sau.loc[idx].map(lo_ra).values,
            "độ dài trước → sau": (truoc.loc[idx].str.len().astype(str) + " → " + sau.loc[idx].str.len().astype(str)).values,
        }))
    return so


__all__ = ["ROOT", "RAW_PATH", "VIDEOS_PATH", "MODELS_PATH", "PROCESSED_PATH", "MANIFEST_PATH", "ANALYSIS_CONFIG",
           "N_SHOW", "thiet_lap_hien_thi", "doc_jsonl", "doc_manifest", "doc_da_xu_ly", "doc_bo_may",
           "mau_ngau_nhien", "lo_ra", "bao_cao", "display", "pd"]

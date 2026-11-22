"""Mục đích: Chạy cả tầng 2 (làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ tiếng Việt và spam) cho cả file bình luận, ghi file đã xử lý và manifest (số dòng, SHA-256, số bình luận mỗi bước đã sửa, thống kê mệnh đề và cờ); cập nhật lần cuối: 2026-11-20.

Chạy từ gốc repo (vài phút với ~470 nghìn bình luận):
    python -m src.processing.run
    python -m src.processing.run --limit 2000 --output data/processed/thu.jsonl   # chạy thử

Mỗi dòng đầu ra = bản ghi raw giữ nguyên + text_clean, text_norm (điền vào trường crawler để rỗng), emojis,
clauses, is_vietnamese, is_spam, spam_reasons, pipeline_version, processed_at. File raw không bị sửa. Đặc tả đầu ra: docs/2-tien-xu-ly/dac-ta.md mục 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import PIPELINE_VERSION
from . import clauses as L3
from . import clean as L1
from . import flags as L4
from . import normalize as L2

GOC_REPO = Path(__file__).resolve().parents[2]
VAO_MAC_DINH = GOC_REPO / "src" / "ingest" / "data" / "raw" / "comments.jsonl"
RA_MAC_DINH = GOC_REPO / "data" / "processed" / "comments.jsonl"


def _tuong_doi(p: Path) -> str:
    try:
        return p.resolve().relative_to(GOC_REPO).as_posix()
    except ValueError:
        return str(p)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def xu_ly_ban_ghi(rec: dict, processed_at: str, dem: Counter | None = None, dem_md: Counter | None = None,
                  dem_co: Counter | None = None) -> dict:
    """Thêm các trường tầng 2 vào một bản ghi raw (sửa tại chỗ và trả lại).

    `dem` đếm số bản ghi mỗi bước đã sửa; `dem_md` đếm mệnh đề theo số mệnh đề / bình luận và theo loại ranh giới;
    `dem_co` đếm cờ của bước 2.4 và lý do.
    """
    goc = rec.get("text")
    if L1.la_rong(goc):
        clean = ""
        if dem is not None:
            dem["B1. Rỗng từ đầu"] += 1
    else:
        clean = goc
        for ma, ten, ham in L1.CAC_BUOC:
            moi = ham(clean)
            if dem is not None and moi != clean:
                dem[f"{ma}. {ten}"] += 1
            clean = moi
        if clean == "" and dem is not None:
            dem["B7. Rỗng sau làm sạch"] += 1
    norm = clean
    for ma, ten, ham in L2.CAC_BUOC:
        if not norm:
            break
        moi = ham(norm)
        if dem is not None and moi != norm:
            dem[f"{ma}. {ten}"] += 1
        norm = moi
    menh_de = L3.tach_menh_de(clean, kem_norm=True, kem_ly_do=True)
    if dem_md is not None and menh_de:
        dem_md[f"bình luận có {len(menh_de) if len(menh_de) < 5 else '5+'} mệnh đề"] += 1
        for md in menh_de:
            dem_md[f"ranh giới: {md['ly_do']}"] += 1
    for md in menh_de:
        del md["ly_do"]
    viet, ly_do_viet = L4.nhan_tieng_viet(clean)
    ly_do_spam = L4.ly_do_spam(clean)
    if dem_co is not None:
        dem_co[f"tiếng Việt: {ly_do_viet}"] += 1
        dem_co["is_vietnamese = false"] += not viet
        dem_co["is_spam = true"] += bool(ly_do_spam)
        for ly_do in ly_do_spam:
            dem_co[f"spam: {ly_do}"] += 1
    rec["text_clean"] = clean
    rec["text_norm"] = norm
    rec["emojis"] = L2.tach_emoji(clean)
    rec["clauses"] = menh_de
    rec["is_vietnamese"] = viet
    rec["is_spam"] = bool(ly_do_spam)
    rec["spam_reasons"] = ly_do_spam
    rec["pipeline_version"] = PIPELINE_VERSION
    rec["processed_at"] = processed_at
    return rec


def chay(vao: Path, ra: Path, limit: int | None = None, in_tien_do: bool = True) -> dict:
    """Đọc `vao` từng dòng, ghi `ra` và `ra` đổi đuôi thành .manifest.json. Trả nội dung manifest."""
    vao, ra = Path(vao), Path(ra)
    if vao.resolve() == ra.resolve():
        raise ValueError("File ra trùng file vào: không bao giờ ghi đè dữ liệu raw")
    ra.parent.mkdir(parents=True, exist_ok=True)
    tam = ra.with_name(ra.name + ".tam")
    processed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    L2.doc_tu_dien()   # đọc từ điển trước, lỗi định dạng thì dừng ngay

    h_vao, dem, dem_md, dem_co = hashlib.sha256(), Counter(), Counter(), Counter()
    so_dong_vao = so_dong_ra = so_rong = so_menh_de = 0
    t0 = time.time()
    with open(vao, "rb") as fin, open(tam, "wb") as fout:
        for dong in fin:
            h_vao.update(dong)
            if not dong.strip():
                continue
            so_dong_vao += 1
            if limit is not None and so_dong_ra >= limit:
                continue   # vẫn đọc hết để SHA-256 file vào khớp checksum trong docs/1-thu-thap/dac-ta.md
            rec = xu_ly_ban_ghi(json.loads(dong), processed_at, dem, dem_md, dem_co)
            so_rong += rec["text_clean"] == ""
            so_menh_de += len(rec["clauses"])
            fout.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
            so_dong_ra += 1
            if in_tien_do and so_dong_ra % 50_000 == 0:
                print(f"  đã xử lý {so_dong_ra:,} bình luận ({time.time() - t0:.0f} giây)", file=sys.stderr)
    os.replace(tam, ra)

    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "processed_at": processed_at,
        "thoi_gian_chay_giay": round(time.time() - t0, 1),
        "vao": {"file": _tuong_doi(vao), "so_dong": so_dong_vao, "sha256": h_vao.hexdigest()},
        "ra": {"file": _tuong_doi(ra), "so_dong": so_dong_ra, "sha256": _sha256(ra)},
        "chi_chay_thu": limit is not None,
        "kieu_dau_thanh": L2.KIEU_DAU,
        "tu_dien_viet_tat": {"file": _tuong_doi(L2.TU_DIEN_VIET_TAT), "so_muc": len(L2.doc_tu_dien()),
                             "sha256": _sha256(L2.TU_DIEN_VIET_TAT)},
        "so_binh_luan_rong": so_rong,
        "so_binh_luan_moi_buoc_sua": dict(sorted(dem.items())),
        "menh_de": {"tong_so": so_menh_de, **dict(sorted(dem_md.items()))},
        "co": {"is_vietnamese = false": dem_co["is_vietnamese = false"], "is_spam = true": dem_co["is_spam = true"],
               **dict(sorted((k, v) for k, v in dem_co.items() if ":" in k))},
    }
    ra.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Tầng 2: làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ (docs/2-tien-xu-ly/dac-ta.md)")
    p.add_argument("--input", type=Path, default=VAO_MAC_DINH, help=f"file raw (mặc định {_tuong_doi(VAO_MAC_DINH)})")
    p.add_argument("--output", type=Path, default=RA_MAC_DINH, help=f"file ra (mặc định {_tuong_doi(RA_MAC_DINH)})")
    p.add_argument("--limit", type=int, default=None, help="chỉ xử lý N bình luận đầu, để chạy thử")
    a = p.parse_args(argv)
    if not a.input.exists():
        sys.exit(f"Không thấy file vào: {a.input}")
    manifest = chay(a.input, a.output, a.limit)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

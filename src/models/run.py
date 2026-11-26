"""Mục đích: Bước suy luận theo bình luận (phương án A): đọc file tầng 2, ghi `aspect_mentions` đúng contract v3 (bộ nhãn chốt) và file bình luận Công việc 12 cần, kèm manifest (docs/4-mo-hinh/dac-ta-suy-luan.md); cập nhật lần cuối: 2026-11-26.

Chạy từ gốc repo, sau lệnh tầng 2:
    python -m src.models.run
    python -m src.models.run --limit 2000 --output data/thu/aspect_mentions.jsonl   # chạy thử

Phiên bản hiện tại dùng luật mốc (`label_source = "rule"`, `model_version = MODEL_VERSION`): từ khóa khía cạnh,
luật thái độ, luật nhận máy, luật máy được nhắc (chiều 6), luật đã dùng máy. Luật không suy
mục đích (`purposes` = null) và loại lỗi (`defect_type` = null). Có mô hình đã đánh giá trên nhãn người thì thay từng phần
trong `suy_luan_binh_luan` và đổi MODEL_VERSION; định dạng đầu ra giữ nguyên.
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

from .aspect import keywords as KC
from src.labeling.label_set import HANG, MAY_CU_THE

from .owner_defect import da_dung_may
from .sentiment import rules as CX
from .target_model import BoNhanMay, doc_danh_muc, so_ngay_tu_ra_mat, xac_dinh_may

MODEL_VERSION = "rule-v1.1"
SCHEMA_VERSION = 3
PHIEN_BAN_TANG_2 = "processing-2."   # cần file tầng 2 có cờ is_spam, is_vietnamese

GOC_REPO = Path(__file__).resolve().parents[2]
VAO_MAC_DINH = GOC_REPO / "data" / "processed" / "comments.jsonl"
RA_MAC_DINH = GOC_REPO / "data" / "aspect_mentions.jsonl"
DANH_MUC_MAC_DINH = GOC_REPO / "config" / "pipeline.yaml"

# Thứ tự trường theo contracts/aspect-mention.schema.json
CAC_TRUONG = (
    "mention_id", "comment_id", "parent_id", "clause_idx", "clause_text", "source", "video_id", "video_model",
    "target_model", "author_hash", "author_is_creator", "aspect", "sentiment", "confidence", "is_owner", "purposes",
    "model_mention", "target_model_source", "defect_type", "compare_with", "compare_winner", "published_at",
    "days_since_launch", "label_source", "model_version", "schema_version",
)
# Trường của bình luận mà Công việc 12 đọc để kiểm mention (src/analysis/validation.py: index_comments, validate_reference)
TRUONG_BINH_LUAN_CV12 = (
    "comment_id", "video_id", "model", "source", "parent_id", "author_hash", "author_is_creator", "published_at",
    "fetched_at", "is_spam", "is_vietnamese", "spam_reasons", "text_clean", "clauses",
)


def file_binh_luan_cv12(ra: Path) -> Path:
    """data/aspect_mentions.jsonl → data/aspect_mentions.comments.jsonl"""
    return ra.with_name(ra.stem + ".comments.jsonl")


def may_duoc_nhac(text_clean: str, may_theo_md: list[list[str]]) -> str:
    """Chiều 6 của cả bình luận: `goi_ten_may` khi có tên máy có số đời (trong danh mục, hay theo mẫu `MAY_CU_THE`),
    `chi_hang` khi chỉ có tên hãng hay dòng, còn lại `khong_nhac` (docs/4-mo-hinh/dac-ta-suy-luan.md mục 5)."""
    chu = text_clean.lower()
    if any(may_theo_md) or MAY_CU_THE.search(chu):
        return "goi_ten_may"
    return "chi_hang" if HANG.search(chu) else "khong_nhac"


def suy_luan_binh_luan(rec: dict, nhan_may: BoNhanMay, dem: Counter | None = None) -> list[dict]:
    """Các mention của một bình luận đã qua tầng 2. Rỗng nếu bình luận rỗng, spam, hoặc không phải tiếng Việt.

    Đơn vị là cả bình luận: mỗi (máy, khía cạnh) có tối đa một lời khen và một lời chê; chỉ khi không có khen, chê
    nào mới ghi một dòng trung tính. `clause_idx` và `clause_text` chỉ vị trí bằng chứng: mệnh đề đầu tiên mang
    nhận xét đó (docs/4-mo-hinh/dac-ta-suy-luan.md mục 2).
    """
    if not rec.get("text_clean"):
        return []
    if rec.get("is_spam"):
        if dem is not None:
            dem["bỏ qua: spam"] += 1
        return []
    if rec.get("is_vietnamese") is False:
        if dem is not None:
            dem["bỏ qua: không phải tiếng Việt"] += 1
        return []

    menh_de = rec.get("clauses") or []
    may_theo_md = [nhan_may.tim(md["text"]) for md in menh_de]
    may_cha = nhan_may.tim(rec.get("parent_text") or "")
    nhom: dict[tuple, dict[str, int]] = {}   # (máy, khía cạnh) -> {cảm xúc: mệnh đề đầu tiên}
    nguon_may: dict[tuple, str] = {}
    for i, md in enumerate(menh_de):
        cac_kc = KC.khia_canh(md["text"])
        if not cac_kc:
            continue
        may, nguon = xac_dinh_may(i, may_theo_md, may_cha, rec.get("model"), nhan_may.danh_muc)
        cx = CX.cam_xuc(md.get("text_norm") or "")
        for kc in cac_kc:
            nhom.setdefault((may, kc), {}).setdefault(cx, i)
            nguon_may.setdefault((may, kc), nguon)

    da_dung = da_dung_may(rec.get("text_norm") or "")
    nhac = may_duoc_nhac(rec.get("text_clean") or "", may_theo_md)
    ra = []
    for (may, kc), theo_cx in nhom.items():
        giu = {cx: i for cx, i in theo_cx.items() if cx != CX.NEU} or theo_cx   # có khen/chê thì bỏ dòng trung tính
        for cx, i in sorted(giu.items(), key=lambda x: x[1]):
            md = menh_de[i]
            launch = nhan_may.danh_muc[may]["launch_date"] if may else None
            ra.append(dict(zip(CAC_TRUONG, (
                f"{rec['comment_id']}#{i}#{kc}", rec["comment_id"], rec.get("parent_id"), i, md["text"],
                rec.get("source"), rec.get("video_id"), rec.get("model"), may, rec.get("author_hash"),
                rec.get("author_is_creator"), kc, cx, None, da_dung, None, nhac, nguon_may[(may, kc)], None,
                None, None, rec.get("published_at"),
                so_ngay_tu_ra_mat(rec["published_at"], launch) if may else None,
                "rule", MODEL_VERSION, SCHEMA_VERSION,
            ))))
            if dem is not None:
                dem[f"máy được nhắc lấy từ: {nguon_may[(may, kc)]}"] += 1
    return ra


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def _tuong_doi(p: Path) -> str:
    try:
        return p.resolve().relative_to(GOC_REPO).as_posix()
    except ValueError:
        return str(p)


def chay(vao: Path, ra: Path, danh_muc: Path = DANH_MUC_MAC_DINH, limit: int | None = None,
         in_tien_do: bool = True) -> dict:
    """Ghi `ra` (mention), file bình luận cho Công việc 12 và manifest `ra` đổi đuôi .manifest.json."""
    vao, ra = Path(vao), Path(ra)
    ra_bl = file_binh_luan_cv12(ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    nhan_may = BoNhanMay(doc_danh_muc(danh_muc))
    tam, tam_bl = ra.with_name(ra.name + ".tam"), ra_bl.with_name(ra_bl.name + ".tam")

    h_vao, dem, theo_kc, theo_cx, theo_may = hashlib.sha256(), Counter(), Counter(), Counter(), Counter()
    so_bl = so_bl_co_mention = so_mention = 0
    t0 = time.time()
    with open(vao, "rb") as fin, open(tam, "wb") as fout, open(tam_bl, "wb") as fout_bl:
        for dong in fin:
            h_vao.update(dong)
            if not dong.strip() or (limit is not None and so_bl >= limit):
                continue
            rec = json.loads(dong)
            so_bl += 1
            if so_bl == 1 and not str(rec.get("pipeline_version", "")).startswith(PHIEN_BAN_TANG_2):
                raise ValueError(f"File vào là {rec.get('pipeline_version')!r}, cần {PHIEN_BAN_TANG_2}x (có is_spam, "
                                 "is_vietnamese). Chạy lại tầng 2: python -m src.processing.run")
            mention = suy_luan_binh_luan(rec, nhan_may, dem)
            if not mention:
                continue
            so_bl_co_mention += 1
            fout_bl.write((json.dumps({k: rec.get(k) for k in TRUONG_BINH_LUAN_CV12}, ensure_ascii=False) + "\n")
                          .encode("utf-8"))
            for m in mention:
                fout.write((json.dumps(m, ensure_ascii=False) + "\n").encode("utf-8"))
                so_mention += 1
                theo_kc[m["aspect"]] += 1
                theo_cx[m["sentiment"]] += 1
                theo_may[m["target_model"] or "(không rõ)"] += 1
            if in_tien_do and so_bl % 50_000 == 0:
                print(f"  đã xét {so_bl:,} bình luận ({time.time() - t0:.0f} giây)", file=sys.stderr)
    os.replace(tam, ra)
    os.replace(tam_bl, ra_bl)

    manifest = {
        "model_version": MODEL_VERSION,
        "label_source": "rule",
        "schema_version": SCHEMA_VERSION,
        "chay_luc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "thoi_gian_chay_giay": round(time.time() - t0, 1),
        "vao": {"file": _tuong_doi(vao), "sha256": h_vao.hexdigest(), "so_binh_luan_da_xet": so_bl},
        "danh_muc_may": {"file": _tuong_doi(Path(danh_muc)), "sha256": _sha256(Path(danh_muc)),
                         "so_may": len(nhan_may.danh_muc)},
        "chi_chay_thu": limit is not None,
        "ra": {"file": _tuong_doi(ra), "so_mention": so_mention, "sha256": _sha256(ra)},
        "ra_binh_luan": {"file": _tuong_doi(ra_bl), "so_binh_luan": so_bl_co_mention, "sha256": _sha256(ra_bl)},
        "so_binh_luan_bo_qua": {k.split(": ", 1)[1]: v for k, v in sorted(dem.items()) if k.startswith("bỏ qua")},
        "mention_theo_khia_canh": dict(sorted(theo_kc.items())),
        "mention_theo_thai_do": dict(sorted(theo_cx.items())),
        "may_duoc_nhac_lay_tu": {k.split(": ", 1)[1]: v for k, v in sorted(dem.items()) if k.startswith("máy được")},
        "mention_theo_may_top20": dict(theo_may.most_common(20)),
    }
    ra.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Suy luận theo bình luận: ghi aspect_mentions (docs/4-mo-hinh/dac-ta-suy-luan.md)")
    p.add_argument("--input", type=Path, default=VAO_MAC_DINH, help=f"file tầng 2 (mặc định {_tuong_doi(VAO_MAC_DINH)})")
    p.add_argument("--output", type=Path, default=RA_MAC_DINH, help=f"file mention (mặc định {_tuong_doi(RA_MAC_DINH)})")
    p.add_argument("--catalog", type=Path, default=DANH_MUC_MAC_DINH, help="danh mục máy (mặc định config/pipeline.yaml)")
    p.add_argument("--limit", type=int, default=None, help="chỉ xét N bình luận đầu, để chạy thử")
    a = p.parse_args(argv)
    if not a.input.exists():
        sys.exit(f"Không thấy file vào: {a.input}. Chạy tầng 2 trước: python -m src.processing.run")
    manifest = chay(a.input, a.output, a.catalog, a.limit)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

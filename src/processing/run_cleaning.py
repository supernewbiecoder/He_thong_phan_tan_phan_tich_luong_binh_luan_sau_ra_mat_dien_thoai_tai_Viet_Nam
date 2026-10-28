# -*- coding: utf-8 -*-
"""
Script chạy 1 lệnh để làm sạch dữ liệu YouTube Comments và sinh ra data/clean_data.jsonl.
Hỗ trợ:
- Tự động định vị đường dẫn dữ liệu theo cấu trúc repo.
- Tự động tính toán số dòng và mã băm SHA-256 checksum sau khi làm sạch.
- Kiểm tra tính toàn vẹn (--verify) đối chiếu với phiên bản chuẩn của nhóm.

Cách sử dụng:
    # 1. Chạy từ thư mục gốc của repository:
    python src/processing/run_cleaning.py

    # 2. Hoặc kiểm tra checksum file clean_data.jsonl hiện có:
    python src/processing/run_cleaning.py --verify

    # 3. Chạy với tùy chọn tùy biến:
    python src/processing/run_cleaning.py --input data/comments.jsonl --output data/clean_data.jsonl --limit 100
"""
import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from collections import Counter

# Đảm bảo import được cleaner dù chạy từ repo root hay từ thư mục src/processing
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from cleaner.pipeline import process_comment_record
except ImportError:
    from src.processing.cleaner.pipeline import process_comment_record

# Cấu hình UTF-8 cho terminal Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thông tin phiên bản chuẩn chính thức của nhóm (Gold Baseline v1.0)
OFFICIAL_DATASET_VERSION = {
    "version": "v1.0 (2026-10-28)",
    "file_name": "clean_data.jsonl",
    "expected_lines": 109344,
    "expected_sha256": "df4c72c25a150108283fc54e7e6d1dd15a969b907088e168eb7a7405f1ea58ab",
    "raw_expected_lines": 109344,
    "raw_expected_sha256": "976eb7e9686b2a91459422760bfea4a11e0f2e23f050eb78eaea1e4806e68950"
}


def find_default_input_path() -> Path:
    """Tự động tìm kiếm file dữ liệu thô comments.jsonl theo các vị trí chuẩn trong repo."""
    candidates = [
        REPO_ROOT / "data" / "comments.jsonl",
        REPO_ROOT / "data" / "raw" / "comments.jsonl",
        REPO_ROOT / "src" / "ingest" / "data" / "raw" / "comments.jsonl",
        CURRENT_DIR / "comments.jsonl",
        Path.cwd() / "comments.jsonl",
        Path.cwd() / "data" / "comments.jsonl"
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return REPO_ROOT / "data" / "comments.jsonl"


def compute_file_stats(file_path: Path):
    """Tính số dòng và mã SHA-256 checksum của một tệp."""
    sha256 = hashlib.sha256()
    line_count = 0
    with open(file_path, "rb") as f:
        for chunk in f:
            sha256.update(chunk)
            line_count += chunk.count(b"\n")
    return line_count, sha256.hexdigest().lower()


def verify_dataset(clean_path: Path):
    """Kiểm tra số dòng và checksum của file dữ liệu sạch so với phiên bản chuẩn."""
    print("=" * 70)
    print("KIỂM TRA TÍNH TOÀN VẸN DỮ LIỆU (DATA INTEGRITY & CHECKSUM VERIFICATION)")
    print("=" * 70)
    print(f"[*] Đường dẫn kiểm tra: {clean_path}")

    if not clean_path.exists():
        print(f"[!] LỖI: Tệp '{clean_path}' không tồn tại!")
        print("    Vui lòng chạy 'python src/processing/run_cleaning.py' để sinh file dữ liệu.")
        return False

    file_size_mb = clean_path.stat().st_size / (1024 * 1024)
    print(f"[*] Dung lượng tệp    : {file_size_mb:.2f} MB ({clean_path.stat().st_size:,} bytes)")
    print("[*] Đang tính toán số dòng và mã băm SHA-256...")

    start_time = time.time()
    line_count, actual_hash = compute_file_stats(clean_path)
    calc_time = time.time() - start_time

    expected_hash = OFFICIAL_DATASET_VERSION["expected_sha256"]
    expected_lines = OFFICIAL_DATASET_VERSION["expected_lines"]

    print("-" * 70)
    print(f"-> Số dòng thực tế    : {line_count:,} dòng (Kỳ vọng: {expected_lines:,} dòng)")
    print(f"-> Mã SHA-256 thực tế : {actual_hash}")
    print(f"-> Mã SHA-256 kỳ vọng : {expected_hash}")
    print(f"-> Thời gian kiểm tra : {calc_time:.2f}s")
    print("-" * 70)

    is_lines_match = (line_count == expected_lines)
    is_hash_match = (actual_hash == expected_hash)

    if is_lines_match and is_hash_match:
        print("[SUCCESS] XÁC THỰC THÀNH CÔNG! Dữ liệu trùng khớp 100% với phiên bản chuẩn v1.0 của nhóm.")
        return True
    else:
        if not is_lines_match:
            print(f"[WARNING] Số dòng không khớp: lệch {line_count - expected_lines} dòng!")
        if not is_hash_match:
            print("[WARNING] Checksum SHA-256 KHÔNG KHỚP! Nội dung tệp có sự khác biệt so với bản chuẩn.")
        return False


def clean_dataset_with_trace(
    input_path: str = None,
    output_path: str = None,
    trace_path: str = None,
    summary_path: str = None,
    trace_only_changes: bool = True,
    limit: int = 0
):
    """
    Thực thi toàn bộ luồng làm sạch dữ liệu, lọc spam, bóc tách mệnh đề và ghi vết biến đổi.
    """
    in_file = Path(input_path) if input_path else find_default_input_path()
    out_file = Path(output_path) if output_path else REPO_ROOT / "data" / "clean_data.jsonl"
    tr_file = Path(trace_path) if trace_path else REPO_ROOT / "data" / "cleaning_trace.jsonl"
    sum_file = Path(summary_path) if summary_path else REPO_ROOT / "data" / "cleaning_summary.json"

    if not in_file.exists():
        print(f"[ERROR] Không tìm thấy tệp dữ liệu thô tại: {in_file}")
        print("Vui lòng tải hoặc đặt file 'comments.jsonl' vào thư mục 'data/' của dự án.")
        return

    # Tự động tạo thư mục đầu ra nếu chưa có
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tr_file.parent.mkdir(parents=True, exist_ok=True)
    sum_file.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PIPELINE LÀM SẠCH, TÁCH MỆNH ĐỀ & GHI VẾT DỮ LIỆU (DATA CLEANING)")
    print("=" * 70)
    print(f"[*] Dữ liệu đầu vào (Read-Only) : {in_file}")
    print(f"[*] Dữ liệu sạch đầu ra         : {out_file}")
    print(f"[*] File ghi vết thay đổi (Diff): {tr_file}")
    print(f"[*] File báo cáo thống kê       : {sum_file}")
    if limit > 0:
        print(f"[*] Chế độ giới hạn             : {limit} dòng đầu tiên")
    print("-" * 70)

    start_time = time.time()
    total_records = 0
    modified_records = 0
    spam_count = 0
    non_spam_count = 0
    non_vi_count = 0
    total_clauses = 0

    change_type_counter = Counter()
    teencode_counter = Counter()
    spam_reason_counter = Counter()
    model_counter = Counter()
    clause_distribution = Counter()

    trace_written_count = 0

    with open(in_file, "r", encoding="utf-8") as f_in, \
         open(out_file, "w", encoding="utf-8") as f_out, \
         open(tr_file, "w", encoding="utf-8") as f_trace:

        for line_idx, line in enumerate(f_in, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                raw_record = json.loads(line)
            except json.JSONDecodeError:
                continue

            clean_rec, trace_rec = process_comment_record(raw_record, include_trace=True)

            # Ghi bản ghi sạch vào clean_data.jsonl
            f_out.write(json.dumps(clean_rec, ensure_ascii=False) + "\n")

            # Ghi vết biến đổi vào cleaning_trace.jsonl
            if not trace_only_changes or trace_rec["was_modified"]:
                f_trace.write(json.dumps(trace_rec, ensure_ascii=False) + "\n")
                trace_written_count += 1

            total_records += 1
            if trace_rec["was_modified"]:
                modified_records += 1

            for ch in trace_rec["changes_detected"]:
                change_type_counter[ch] += 1

            for item in trace_rec["teencode_replacements"]:
                pair = f"{item['original']} -> {item['replacement']}"
                teencode_counter[pair] += 1

            model = clean_rec.get("model", "unknown")
            model_counter[model] += 1

            c_count = clean_rec.get("clause_count", 0)
            total_clauses += c_count
            clause_distribution[min(c_count, 10)] += 1

            if clean_rec.get("is_spam"):
                spam_count += 1
                for r in clean_rec.get("spam_reasons", []):
                    spam_reason_counter[r] += 1
            else:
                non_spam_count += 1

            if not clean_rec.get("is_vietnamese"):
                non_vi_count += 1

            # Log tiến độ mỗi 10.000 bình luận
            if total_records % 10000 == 0:
                elapsed = time.time() - start_time
                speed = total_records / elapsed if elapsed > 0 else 0
                print(f"-> Đã xử lý {total_records:,} bình luận... ({speed:,.0f} dòng/giây)")

            if 0 < limit <= total_records:
                print(f"[!] Đã đạt giới hạn {limit} dòng theo yêu cầu.")
                break

    elapsed_total = time.time() - start_time
    avg_speed = total_records / elapsed_total if elapsed_total > 0 else 0
    avg_clauses = total_clauses / total_records if total_records > 0 else 0
    mod_pct = (modified_records / total_records * 100) if total_records else 0

    print("-" * 70)
    print("HOÀN TẤT LÀM SẠCH, TÁCH MỆNH ĐỀ & GHI VẾT DỮ LIỆU!")
    print(f"-> Tổng số bình luận xử lý      : {total_records:,}")
    print(f"-> Bình luận có thay đổi (Norm) : {modified_records:,} ({mod_pct:.2f}%)")
    print(f"-> Số bản ghi ghi vào file trace: {trace_written_count:,}")
    print(f"-> Bình luận hợp lệ (Non-Spam)  : {non_spam_count:,} ({non_spam_count/total_records*100:.2f}%)")
    print(f"-> Bình luận Spam bị gắn cờ     : {spam_count:,} ({spam_count/total_records*100:.2f}%)")
    print(f"-> Tổng số từ teencode đã sửa   : {sum(teencode_counter.values()):,}")
    print(f"-> Tổng số mệnh đề bóc tách     : {total_clauses:,} (Trung bình {avg_clauses:.2f} mệnh đề/comment)")
    print(f"-> Thời gian thực hiện          : {elapsed_total:.2f}s ({avg_speed:,.0f} records/s)")

    # Lưu báo cáo thống kê json
    summary = {
        "execution_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "files": {
            "input_file": str(in_file),
            "output_clean_file": str(out_file),
            "trace_file": str(tr_file),
            "summary_file": str(sum_file)
        },
        "general_metrics": {
            "total_records_processed": total_records,
            "records_with_modifications": modified_records,
            "modification_rate_percent": round(mod_pct, 2),
            "trace_records_recorded": trace_written_count,
            "valid_non_spam_comments": non_spam_count,
            "spam_comments": spam_count,
            "spam_ratio_percent": round(spam_count / total_records * 100, 2) if total_records else 0,
            "non_vietnamese_comments": non_vi_count,
            "total_clauses_extracted": total_clauses,
            "average_clauses_per_comment": round(avg_clauses, 2),
            "execution_time_seconds": round(elapsed_total, 2),
            "records_per_second": round(avg_speed, 1)
        },
        "modification_types_breakdown": dict(change_type_counter),
        "top_20_teencode_replacements": dict(teencode_counter.most_common(20)),
        "spam_breakdown_by_reason": dict(spam_reason_counter),
        "comments_per_model": dict(model_counter.most_common(20)),
        "clause_distribution": {f"{k}_clauses": v for k, v in sorted(clause_distribution.items())}
    }

    with open(sum_file, "w", encoding="utf-8") as f_sum:
        json.dump(summary, f_sum, ensure_ascii=False, indent=2)
    print(f"[*] Báo cáo tổng hợp đã lưu tại : {sum_file}")

    # Tự động tính Checksum và Số dòng sau khi sinh xong (nếu chạy đủ)
    if limit == 0:
        print("-" * 70)
        print("[*] Kiểm tra tính toàn vẹn của tệp vừa tạo:")
        actual_lines, actual_hash = compute_file_stats(out_file)
        print(f"    - Số dòng      : {actual_lines:,}")
        print(f"    - Mã SHA-256   : {actual_hash}")
        if actual_hash == OFFICIAL_DATASET_VERSION["expected_sha256"]:
            print("    - Đánh giá     : [VALIDATED] Khớp 100% với phiên bản chuẩn của nhóm (v1.0)!")
        else:
            print("    - Đánh giá     : [NOTE] Mã hash khác bản chuẩn (có thể do cập nhật logic/từ điển).")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and trace YouTube comments dataset for the project.")
    parser.add_argument("--input", default=None, help="Đường dẫn tệp comments thô (mặc định: data/comments.jsonl)")
    parser.add_argument("--output", default=None, help="Đường dẫn tệp kết quả sạch (mặc định: data/clean_data.jsonl)")
    parser.add_argument("--trace", default=None, help="Đường dẫn tệp ghi vết diff (mặc định: data/cleaning_trace.jsonl)")
    parser.add_argument("--summary", default=None, help="Đường dẫn tệp báo cáo json (mặc định: data/cleaning_summary.json)")
    parser.add_argument("--all-trace", action="store_true", help="Ghi tất cả dòng vào file trace thay vì chỉ dòng có thay đổi")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số dòng xử lý để thử nghiệm (0 = toàn bộ)")
    parser.add_argument("--verify", action="store_true", help="Chỉ kiểm tra số dòng và SHA-256 checksum của clean_data.jsonl")

    args = parser.parse_args()

    if args.verify:
        target_path = Path(args.output) if args.output else (REPO_ROOT / "data" / "clean_data.jsonl")
        verify_dataset(target_path)
    else:
        clean_dataset_with_trace(
            input_path=args.input,
            output_path=args.output,
            trace_path=args.trace,
            summary_path=args.summary,
            trace_only_changes=not args.all_trace,
            limit=args.limit
        )

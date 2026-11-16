"""Hằng số dùng chung của Công việc 11: đường dẫn, phiên bản dữ liệu, thiết kế mẫu.

Mọi con số ảnh hưởng tới kết quả (seed, cỡ mẫu từng tầng, tỷ lệ test) đặt ở đây
để chạy lại cho ra đúng cùng một mẫu và cùng một cách chia tập.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SPAM_DIR = Path(__file__).resolve().parent

# --- Dữ liệu đầu vào: bản chuẩn của nhóm (Công việc 6), không nằm trong git ---
CLEAN_DATA_PATH = REPO_ROOT / "data" / "clean_data.jsonl"
DATASET_VERSION = "clean_data v1.0"
DATASET_LINES = 109_344
DATASET_SHA256 = "df4c72c25a150108283fc54e7e6d1dd15a969b907088e168eb7a7405f1ea58ab"

# --- File trong git (chỉ chứa ID + nhãn, không chứa nội dung bình luận) ---
LABELS_DIR = SPAM_DIR / "labels"
SAMPLE_PATH = LABELS_DIR / "spam_sample_v1.tsv"
LABELS_PATH = LABELS_DIR / "spam_labels_v1.tsv"
RESULTS_PATH = SPAM_DIR / "results" / "spam_eval_v1.json"

# --- File làm việc cục bộ (có nội dung bình luận nên bị .gitignore) ---
WORK_DIR = REPO_ROOT / "data" / "labels" / "spam"
MODEL_PATH = REPO_ROOT / "data" / "models" / "spam-lr-v1.joblib"

GUIDELINE_VERSION = "spam-guideline-v1.1"
RULE_VERSION = "rule-v0"
MODEL_VERSION = "spam-lr-v1"

# --- Thiết kế mẫu phân tầng ---
SAMPLE_SEED = 20261117
# Tầng xác định theo đầu ra của rule-v0 trên bản dữ liệu chuẩn; xem sampling.py.
STRATA_SIZES = {
    "rule_content": 150,       # luật gắn cờ vì link / SĐT / mời liên hệ / thương mại
    "rule_form": 70,           # chỉ vì lặp ký tự / lặp từ
    "rule_notext": 40,         # không có chữ cái / rỗng
    "rule_nonvn_only": 60,     # chỉ vì "không phải tiếng Việt"
    "unflagged_dup": 40,       # luật không bắt, nội dung dài bị dán lặp >= 3 lần
    "unflagged_suspect": 80,   # luật không bắt, có dấu hiệu quảng bá / dãy số / email
    "unflagged_rest": 200,     # luật không bắt, không có dấu hiệu nào
}

# --- Chia train/test theo video_id (không để một video nằm ở cả hai tập) ---
SPLIT_SALT = "cv11-spam-split-v1"
TEST_FRACTION = 0.40

LABELS = ("spam", "ham")
SPAM_TYPES = ("ad", "contact_sale", "scam", "channel_promo", "flood", "other")
LANGS = ("vi", "other", "none")

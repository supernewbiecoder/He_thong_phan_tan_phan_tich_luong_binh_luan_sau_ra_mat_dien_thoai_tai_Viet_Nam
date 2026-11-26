"""
Mục đích: Đọc cấu hình chung config/pipeline.yaml (gốc repo) và biến bí mật trong src/ingest/.env; chỉ chỗ ghi dữ liệu src/ingest/data/; cập nhật lần cuối: 2026-11-11.

Cách hoạt động: load() trả dict cấu hình, thêm api_key, salt (AUTHOR_SALT), kafka, worker (CRAWLER_WORKER) lấy từ .env.
raw_path()/raw_files() cho biết file comments/videos JSONL theo output.layout (single: một file; daily: mỗi ngày một file).
"""
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "pipeline.yaml"   # đặt ở gốc repo để các nhóm khác cùng đọc danh mục máy
load_dotenv(ROOT / ".env")
DB_PATH = ROOT / "data" / "state.db"
RAW_DIR = ROOT / "data" / "raw"


def load(path=None):
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["api_key"] = os.environ.get("YOUTUBE_API_KEY", "")
    cfg["kafka"] = {
        "bootstrap": os.environ.get("KAFKA_BOOTSTRAP", ""),
        "topic": os.environ.get("KAFKA_TOPIC", "raw_comments"),
    }
    cfg["salt"] = os.environ.get("AUTHOR_SALT", "")
    # Chia việc nhiều người: mỗi máy đặt CRAWLER_WORKER (p1, p2...) trong .env; kênh có `owner: p2` chỉ máy p2 cào.
    # Kênh không ghi owner thuộc về `default_owner` (mặc định p1).
    cfg["worker"] = os.environ.get("CRAWLER_WORKER", "p1").strip() or "p1"
    return cfg


def raw_path(cfg, kind):
    """File đầu ra của `kind` ('comments' | 'videos'). output.layout:
       daily  -> comments-YYYY-MM-DD.jsonl (ngày theo múi giờ trong config, không phải UTC)
       single -> comments.jsonl: MỘT file cho mọi mẫu máy và mọi ngày."""
    out = (cfg or {}).get("output") or {}
    if out.get("layout", "daily") == "single":
        return RAW_DIR / f"{kind}.jsonl"
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo((cfg or {}).get("timezone", "UTC"))
    return RAW_DIR / f"{kind}-{datetime.now(tz):%Y-%m-%d}.jsonl"


def raw_files(kind):
    """Mọi file dữ liệu đã có của `kind`, cả bố cục single lẫn daily, theo thứ tự tên."""
    files = sorted(RAW_DIR.glob(f"{kind}-*.jsonl"))
    single = RAW_DIR / f"{kind}.jsonl"
    return ([single] if single.exists() else []) + files

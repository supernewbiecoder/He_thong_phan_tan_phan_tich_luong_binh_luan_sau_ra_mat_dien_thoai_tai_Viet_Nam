import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "pipeline.yaml"
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

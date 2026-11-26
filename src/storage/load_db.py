"""Mục đích: Nạp đầu ra của chuỗi theo lô (bình luận tầng 2, aspect_mentions contract v3, aggregates và kết quả Q1–Q5 của Công việc 12, danh mục máy) vào MongoDB cho API và dashboard đọc (docs/6-luu-tru/huong-dan.md); cập nhật lần cuối: 2026-11-26.

Thường chạy qua bước `nap_db` của `python -m src.run --den nap_db`. Chạy riêng thì mỗi phần là tùy chọn; phần nào
truyền đường dẫn thì nạp phần đó:

  python -m src.storage.load_db \
      --models config/pipeline.yaml \
      --comments data/processed/comments.jsonl \
      --mentions data/aspect_mentions.jsonl \
      --aggregates data/aggregates/current/aggregates.jsonl \
      --analysis data/aggregates/current/business_questions.json

Chạy lại bao nhiêu lần cũng cho cùng một trạng thái DB: mọi bản ghi được upsert
theo khóa. Với mentions và aggregates, file được coi là toàn bộ dữ liệu của từng
cặp (model_version, target_model) có trong file: dòng cũ của cặp đó mà file không
còn thì bị xóa, để số đếm của một máy không lẫn giữa hai lần chạy mô hình. Máy và
phiên bản không có trong file thì không bị đụng tới.

Lưu ý về mentions: theo contract, mention_id là khóa và không chứa model_version,
nên collection chỉ giữ được MỘT phiên bản nhãn cho mỗi mention. Nạp phiên bản mới
đè lên mention của phiên bản khác sẽ làm phiên bản cũ thiếu dữ liệu; script dừng
lại và báo, trừ khi chạy với --replace-other-versions.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

import yaml
from pymongo import MongoClient, UpdateOne

REPO_ROOT = Path(__file__).resolve().parents[2]
BATCH = 2000
AGGREGATE_KEY = ("target_model", "aspect", "week_since_launch", "video_id", "source", "model_version")
COUNT_FIELDS = ("n_pos", "n_neg", "n_neu", "n_cmp")   # tich_cuc, tieu_cuc, khong_danh_gia, so_sanh
# Không đưa vào DB: tên người bình luận (AGENTS.md mục 3)
COMMENT_FIELDS_DROPPED = ("author_name",)
BRAND_PREFIXES = (
    ("iphone", "Apple"), ("apple", "Apple"), ("samsung", "Samsung"), ("galaxy", "Samsung"),
    ("xiaomi", "Xiaomi"), ("redmi", "Xiaomi"), ("poco", "Xiaomi"), ("mi ", "Xiaomi"),
    ("oppo", "OPPO"), ("vivo", "vivo"), ("huawei", "Huawei"), ("realme", "realme"),
    ("google", "Google"), ("oneplus", "OnePlus"), ("nokia", "Nokia"), ("sony", "Sony"),
)


def read_jsonl(path: Path) -> Iterator[dict]:
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{number}: không phải JSON hợp lệ ({error})") from error


def brand_of(title: str) -> str:
    lowered = (title or "").lower() + " "
    for prefix, brand in BRAND_PREFIXES:
        if lowered.startswith(prefix):
            return brand
    return "Khác"


def catalog_from_config(path: Path) -> List[dict]:
    """Danh mục máy phẳng từ config/pipeline.yaml (mẫu chính và đối thủ khai báo lồng bên trong)."""
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    entries: Dict[str, dict] = {}

    def remember(entry: dict, fallback_date: Optional[str], top_level: bool) -> str:
        name = entry["name"]
        known = entries.setdefault(name, {"model_id": name, "rivals": [], "_dated": False})
        for field in ("title", "aliases", "segment"):
            if entry.get(field) and (top_level or not known.get(field)):
                known[field] = entry[field]
        if entry.get("predecessor"):
            known["predecessor_id"] = entry["predecessor"]
        if entry.get("launch_date") and (top_level or not known["_dated"]):
            known["launch_date"], known["_dated"] = str(entry["launch_date"]), True
        elif fallback_date and "launch_date" not in known:
            # Theo ghi chú trong pipeline.yaml: đối thủ bỏ trống ngày thì dùng ngày của mẫu chính.
            known["launch_date"] = str(fallback_date)
        return name

    for model in config.get("models") or []:
        remember(model, None, top_level=True)
    for model in config.get("models") or []:
        # Đối thủ có thể viết là object hoặc chỉ là tên một mẫu đã khai báo nơi khác.
        rivals = [remember({"name": rival} if isinstance(rival, str) else rival,
                           model.get("launch_date"), top_level=False)
                  for rival in model.get("rivals") or []]
        entries[model["name"]]["rivals"] = rivals

    catalog = []
    for entry in entries.values():
        entry.pop("_dated")
        title = entry.get("title") or entry["model_id"]
        catalog.append({
            "model_id": entry["model_id"], "title": title, "brand": brand_of(title),
            "launch_date": entry.get("launch_date"), "predecessor_id": entry.get("predecessor_id"),
            "rivals": entry["rivals"], "aliases": list(entry.get("aliases") or []),
            **({"segment": entry["segment"]} if entry.get("segment") else {}),
        })
    return catalog


def _write_batch(collection, key: str, batch: List[dict]) -> None:
    try:
        collection.bulk_write([UpdateOne({key: doc[key]}, {"$set": doc}, upsert=True) for doc in batch],
                              ordered=False)
    except TypeError:
        # mongomock (dùng trong kiểm thử) không nhận được thao tác bulk của pymongo mới:
        # ghi từng bản ghi, kết quả trong DB giống hệt.
        for doc in batch:
            collection.update_one({key: doc[key]}, {"$set": doc}, upsert=True)


def upsert(collection, documents: Iterable[dict], key: str) -> int:
    """Upsert theo một trường khóa, gửi theo lô. Trả về số bản ghi đã gửi."""
    count, batch = 0, []
    for document in documents:
        batch.append(document)
        if len(batch) >= BATCH:
            _write_batch(collection, key, batch)
            count, batch = count + len(batch), []
    if batch:
        _write_batch(collection, key, batch)
        count += len(batch)
    return count


def prune(collection, key: str, documents: List[dict]) -> int:
    """Xóa bản ghi cũ mà file mới không còn, trong phạm vi các cặp (model_version, target_model) vừa nạp.

    Chỉ xóa trong đúng những cặp có mặt trong file, nên nạp một file chỉ gồm vài máy
    không làm mất dữ liệu của các máy khác cùng phiên bản.
    """
    keep = {document[key] for document in documents}
    scopes = {(document["model_version"], document.get("target_model")) for document in documents}
    stale = []
    for version in {version for version, _target in scopes}:
        for doc in collection.find({"model_version": version}, {key: 1, "target_model": 1}):
            # Bản ghi không có trường khóa không phải do script này ghi: không đụng tới.
            if doc.get(key) and doc[key] not in keep and (version, doc.get("target_model")) in scopes:
                stale.append(doc[key])
    for start in range(0, len(stale), BATCH):
        collection.delete_many({key: {"$in": stale[start:start + BATCH]}})
    return len(stale)


def other_versions_holding(collection, mention_ids: List[str], versions: set) -> Dict[str, int]:
    """Đếm mention đang có trong DB với cùng mention_id nhưng thuộc phiên bản nhãn khác."""
    found: Dict[str, int] = {}
    for start in range(0, len(mention_ids), BATCH):
        for doc in collection.find({"mention_id": {"$in": mention_ids[start:start + BATCH]},
                                    "model_version": {"$nin": sorted(versions)}}, {"model_version": 1}):
            version = doc.get("model_version") or "không ghi phiên bản"
            found[version] = found.get(version, 0) + 1
    return found


def aggregate_id(row: dict) -> str:
    """Cùng công thức với Công việc 12, để hai bên sinh ra cùng một khóa."""
    raw = json.dumps([row[key] for key in AGGREGATE_KEY], ensure_ascii=False, separators=(",", ":"))
    return "agg_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_aggregate(row: dict, where: str) -> dict:
    for key in AGGREGATE_KEY:
        if row.get(key) is None:
            raise ValueError(f"{where}: thiếu trường khóa '{key}'")
    if type(row["week_since_launch"]) is not int:
        raise ValueError(f"{where}: 'week_since_launch' phải là số nguyên")
    for key in ("target_model", "aspect", "video_id", "source", "model_version"):
        if not isinstance(row[key], str) or not row[key]:
            raise ValueError(f"{where}: '{key}' phải là chuỗi không rỗng")
    row = {"n_cmp": 0, **row}   # aggregates trước contract v3 không có n_cmp
    for key in COUNT_FIELDS:
        if type(row.get(key)) is not int or row[key] < 0:
            raise ValueError(f"{where}: '{key}' phải là số nguyên không âm (aggregates lưu số đếm, không lưu %)")
    if any("pct" in key or "%" in key or "percent" in key for key in row):
        raise ValueError(f"{where}: aggregates không được chứa trường tỷ lệ")
    row.setdefault("agg_id", aggregate_id(row))
    row["n_total"] = sum(row[key] for key in COUNT_FIELDS)
    row.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    return row


def load_models(db, path: Path) -> str:
    catalog = catalog_from_config(path)
    return f"models: {upsert(db.models, catalog, 'model_id')} máy từ {path.name}"


def load_comments(db, path: Path) -> str:
    """Bình luận đã qua tầng 2: giữ nguyên `pipeline_version`, `processed_at` của tầng 2, bỏ tên người viết."""
    def documents():
        for record in read_jsonl(path):
            if not record.get("comment_id"):
                raise ValueError(f"{path}: có bình luận thiếu comment_id")
            if not record.get("pipeline_version"):
                raise ValueError(f"{path}: bình luận {record['comment_id']} chưa qua tầng 2 (thiếu pipeline_version)")
            yield {k: v for k, v in record.items() if k not in COMMENT_FIELDS_DROPPED}

    return f"comments: {upsert(db.comments, documents(), 'comment_id'):,} bình luận từ {path.name}"


def load_mentions(db, path: Path, schema_path: Path, replace_other_versions: bool = False) -> str:
    from jsonschema import Draft7Validator

    validator = Draft7Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    mentions, seen = [], set()
    for number, mention in enumerate(read_jsonl(path), start=1):
        errors = sorted(validator.iter_errors(mention), key=lambda e: list(e.path))
        if errors:
            raise ValueError(f"{path}:{number}: sai contract aspect-mention: {errors[0].message}")
        if mention["mention_id"] in seen:
            raise ValueError(f"{path}:{number}: trùng mention_id {mention['mention_id']}")
        seen.add(mention["mention_id"])
        mentions.append(mention)
    versions = {mention["model_version"] for mention in mentions}
    clashes = other_versions_holding(db.aspect_mentions, sorted(seen), versions)
    replaced = ""
    if clashes:
        detail = ", ".join(f"{version}: {count:,}" for version, count in sorted(clashes.items()))
        if not replace_other_versions:
            raise ValueError(
                f"{path}: file sẽ ghi đè mention của phiên bản nhãn khác đang có trong DB ({detail}). "
                "mention_id là khóa nên mỗi mention chỉ giữ được một phiên bản; ghi đè một phần sẽ làm "
                "phiên bản cũ thiếu dữ liệu. Chưa ghi gì. Nếu muốn thay hẳn, chạy lại với "
                "--replace-other-versions (xóa toàn bộ mention của các phiên bản đó trước khi nạp).")
        for version in clashes:
            db.aspect_mentions.delete_many(
                {"model_version": None if version == "không ghi phiên bản" else version})
        replaced = f"; đã xóa toàn bộ mention của phiên bản bị thay ({detail})"
    count = upsert(db.aspect_mentions, mentions, "mention_id")
    removed = prune(db.aspect_mentions, "mention_id", mentions)
    return (f"aspect_mentions: {count:,} mention ({', '.join(sorted(versions))}) từ {path.name}; "
            f"xóa {removed:,} mention cũ cùng phiên bản và cùng máy{replaced}")


def load_aggregates(db, path: Path) -> str:
    rows = [check_aggregate(row, f"{path}:{number}") for number, row in enumerate(read_jsonl(path), start=1)]
    ids = {row["agg_id"] for row in rows}
    if len(ids) != len(rows):
        raise ValueError(f"{path}: có dòng trùng khóa aggregates")
    versions = {row["model_version"] for row in rows}
    count = upsert(db.aggregates, rows, "agg_id")
    removed = prune(db.aggregates, "agg_id", rows)
    return (f"aggregates: {count:,} dòng ({', '.join(sorted(versions))}) từ {path.name}; "
            f"xóa {removed:,} dòng cũ cùng phiên bản và cùng máy")


def load_analysis(db, path: Path) -> str:
    result = json.loads(path.read_text(encoding="utf-8"))
    config = result.get("config") or {}
    target, version = config.get("target_model"), config.get("expected_model_version")
    if not target or not version:
        raise ValueError(f"{path}: thiếu config.target_model hoặc config.expected_model_version")
    document = {
        "analysis_id": f"{target}|{version}", "target_model": target, "model_version": version,
        "loaded_at": datetime.now(timezone.utc).isoformat(),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "result": result,
    }
    db.analysis_results.update_one({"analysis_id": document["analysis_id"]}, {"$set": document}, upsert=True)
    return f"analysis_results: {document['analysis_id']} từ {path.name}"


def ensure_indexes(db) -> None:
    """Index tối thiểu để upsert và truy vấn của API không quét toàn bộ collection.

    src/storage/init_db.py tạo bộ index đầy đủ; các lệnh dưới đây trùng khóa với bộ đó và vô hại nếu index đã có.
    """
    def ensure(collection: str, keys: List[tuple], unique: bool = False) -> None:
        wanted = [name for name, _direction in keys]
        if not any(list(index["key"].keys()) == wanted for index in db[collection].list_indexes()):
            db[collection].create_index(keys, unique=unique)

    for collection, key in (("models", "model_id"), ("comments", "comment_id"),
                            ("aspect_mentions", "mention_id"), ("aggregates", "agg_id"),
                            ("analysis_results", "analysis_id")):
        ensure(collection, [(key, 1)], unique=True)
    ensure("aggregates", [("model_version", 1), ("target_model", 1)])
    ensure("aspect_mentions", [("model_version", 1), ("target_model", 1), ("aspect", 1)])


def load_all(db, *, models: Optional[Path] = None, comments: Optional[Path] = None, mentions: Optional[Path] = None,
             aggregates: Optional[Path] = None, analysis: Optional[Path] = None,
             schema: Path = REPO_ROOT / "contracts" / "aspect-mention.schema.json",
             replace_other_versions: bool = False) -> List[str]:
    """Nạp các phần có đường dẫn, theo thứ tự danh mục máy, bình luận, mention, aggregates, kết quả Q1–Q5.
    Lỗi dữ liệu thì ném ValueError; phần đã nạp trước đó giữ nguyên (mỗi phần tự upsert, chạy lại được)."""
    ensure_indexes(db)
    steps = [(models, load_models), (comments, load_comments),
             (mentions, lambda d, p: load_mentions(d, p, schema, replace_other_versions)),
             (aggregates, load_aggregates), (analysis, load_analysis)]
    return [loader(db, Path(path)) for path, loader in steps if path]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Nạp đầu ra pipeline vào MongoDB cho dashboard")
    parser.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    parser.add_argument("--db", default=os.getenv("MONGO_DB", "smartphone_analytics"))
    parser.add_argument("--models", type=Path, help="config/pipeline.yaml")
    parser.add_argument("--comments", type=Path, help="data/processed/comments.jsonl (đầu ra tầng 2)")
    parser.add_argument("--mentions", type=Path, help="aspect_mentions.jsonl đúng contract v3")
    parser.add_argument("--aggregates", type=Path, help="aggregates.jsonl")
    parser.add_argument("--analysis", type=Path, help="business_questions.json của Công việc 12")
    parser.add_argument("--schema", type=Path,
                        default=REPO_ROOT / "contracts" / "aspect-mention.schema.json")
    parser.add_argument("--replace-other-versions", action="store_true",
                        help="cho phép --mentions thay hẳn mention của phiên bản nhãn khác đang có trong DB")
    args = parser.parse_args()

    paths = [args.models, args.comments, args.mentions, args.aggregates, args.analysis]
    if not any(paths):
        parser.error("chưa chọn phần nào để nạp")
    for path in paths:
        if path and not path.exists():
            parser.error(f"không thấy file {path}")

    db = MongoClient(args.uri, serverSelectionTimeoutMS=5000)[args.db]
    db.command("ping")
    try:
        for line in load_all(db, models=args.models, comments=args.comments, mentions=args.mentions,
                             aggregates=args.aggregates, analysis=args.analysis, schema=args.schema,
                             replace_other_versions=args.replace_other_versions):
            print(line)
    except ValueError as error:
        print(f"LỖI: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

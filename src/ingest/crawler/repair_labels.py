"""
Mục đích: Gắn lại nhãn `model` cho mọi video trong state.db theo config hiện tại và đồng bộ sang các file JSONL; cập nhật lần cuối: 2026-11-11.

Cách hoạt động: phân loại lại tiêu đề + ngày đăng của từng video bằng models.classify, liệt kê video đổi nhãn hoặc bị bỏ,
rồi (chỉ khi có --apply) ghi lại state.db và comments/videos JSONL qua file tạm. Mặc định chỉ báo cáo.
Chạy (từ src/ingest): python -m crawler.repair_labels [--apply] [--config đường_dẫn]
"""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import config
from .models import classify
from .store import connect
from .timeutil import parse


def load_video_labels(cfg, conn):
    labels = {}
    changes = []
    skipped = []
    rows = conn.execute(
        "SELECT video_id, title, published_at, model, status FROM videos ORDER BY published_at"
    ).fetchall()

    for row in rows:
        try:
            published = parse(row["published_at"])
            new_model = classify(cfg, row["title"] or "", published)
        except Exception as exc:
            skipped.append((row["video_id"], f"Không phân loại được: {exc}"))
            continue

        if not new_model:
            skipped.append((row["video_id"], "Không khớp model nào trong config hiện tại"))
            continue

        labels[row["video_id"]] = new_model
        if row["model"] != new_model:
            changes.append({
                "video_id": row["video_id"],
                "title": row["title"] or "",
                "published_at": row["published_at"] or "",
                "old_model": row["model"],
                "new_model": new_model,
                "status": row["status"],
            })

    return labels, changes, skipped


def jsonl_files(kind):
    return config.raw_files(kind)


def scan_jsonl(paths, labels, kind):
    """Đếm số dòng sẽ đổi và tạo file tạm; không sửa file gốc ở bước này."""
    stats = {}
    temp_paths = {}
    for path in paths:
        if not path.exists():
            continue
        changed = 0
        total = 0
        tmp = path.with_name(path.name + ".repair-tmp")
        try:
            with path.open("r", encoding="utf-8") as src, tmp.open("w", encoding="utf-8", newline="\n") as dst:
                for line_no, line in enumerate(src, 1):
                    total += 1
                    if not line.strip():
                        dst.write(line)
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"{path.name}:{line_no}: JSON không hợp lệ: {exc}") from exc

                    vid = rec.get("video_id")
                    if vid in labels and "model" in rec and rec["model"] != labels[vid]:
                        rec["model"] = labels[vid]
                        changed += 1
                        line = json.dumps(rec, ensure_ascii=False) + "\n"
                    dst.write(line)
            stats[path] = {"total": total, "changed": changed}
            temp_paths[path] = tmp
        except Exception:
            if tmp.exists():
                tmp.unlink()
            for p in temp_paths.values():
                if p.exists():
                    p.unlink()
            raise
    return stats, temp_paths


def print_report(changes, skipped, stats):
    print(f"Video trong SQLite có nhãn cần đổi: {len(changes)}")
    for item in changes[:100]:
        print(
            f"- {item['video_id']} | {item['status']} | "
            f"{item['old_model']} -> {item['new_model']} | {item['title']}"
        )
    if len(changes) > 100:
        print(f"... còn {len(changes) - 100} video khác")

    print(f"\nVideo bỏ qua/không khớp: {len(skipped)}")
    for vid, reason in skipped[:20]:
        print(f"- {vid}: {reason}")
    if len(skipped) > 20:
        print(f"... còn {len(skipped) - 20} video khác")

    print("\nJSONL:")
    for path, info in stats.items():
        print(f"- {path.name}: {info['changed']} dòng sẽ đổi / {info['total']} dòng")


def apply_changes(conn, changes, temp_paths, stats):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backups = {}
    replaced = []

    try:
        # Tạo bản sao lưu trước khi thay bất kỳ file gốc nào.
        for path in temp_paths:
            backup = path.with_name(path.name + f".{timestamp}.bak")
            shutil.copy2(path, backup)
            backups[path] = backup

        conn.execute("BEGIN IMMEDIATE")
        for item in changes:
            conn.execute(
                "UPDATE videos SET model=? WHERE video_id=?",
                (item["new_model"], item["video_id"]),
            )

        # Thay JSONL bằng file tạm; SQLite vẫn đang ở trong transaction.
        for path, tmp in temp_paths.items():
            tmp.replace(path)
            replaced.append(path)

        conn.commit()
        return backups
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        for path in replaced:
            backup = backups.get(path)
            if backup and backup.exists():
                shutil.copy2(backup, path)
        raise
    finally:
        for tmp in temp_paths.values():
            if tmp.exists():
                tmp.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Tính lại nhãn model cho video và đồng bộ JSONL. Mặc định chỉ dry-run."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ghi thay đổi thật; nếu không có cờ này, chỉ báo cáo.",
    )
    parser.add_argument(
        "--config",
        help="Đường dẫn config YAML; mặc định dùng config/pipeline.yaml ở gốc repo.",
    )
    args = parser.parse_args()

    cfg = config.load(args.config)
    conn = connect(config.DB_PATH)
    try:
        labels, changes, skipped = load_video_labels(cfg, conn)
        paths = jsonl_files("comments") + jsonl_files("videos")
        stats, temp_paths = scan_jsonl(paths, labels, "all")
        print_report(changes, skipped, stats)

        if not args.apply:
            print("\nDRY-RUN: chưa thay đổi SQLite hoặc JSONL.")
            print("Nếu báo cáo đúng, chạy lại với --apply để cập nhật.")
            for tmp in temp_paths.values():
                if tmp.exists():
                    tmp.unlink()
            return

        if not changes and not any(v["changed"] for v in stats.values()):
            print("\nKhông có thay đổi cần áp dụng.")
            for tmp in temp_paths.values():
                if tmp.exists():
                    tmp.unlink()
            return

        backups = apply_changes(conn, changes, temp_paths, stats)
        print("\nĐã cập nhật nhãn.")
        print("Bản sao lưu JSONL:")
        for path, backup in backups.items():
            print(f"- {backup}")
        print(
            "\nLưu ý: script không xóa bảng seen và không gọi YouTube API. "
            "Các sự kiện Kafka đã gửi trước đây không bị sửa."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

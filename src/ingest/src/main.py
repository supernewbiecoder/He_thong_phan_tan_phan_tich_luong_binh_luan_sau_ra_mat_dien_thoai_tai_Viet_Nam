import argparse
import functools
import logging
import sys
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.blocking import BlockingScheduler
from . import config
from .crawl import run_crawl
from .discover import find_channels, refresh_videos, run_discover, suggest_channel_ids
from .quota import QuotaExceeded
from .lock import acquire
from .quota import QuotaLedger
from .replay import run_replay
from .sinks import Sink
from .store import connect
from .youtube import YouTube

log = logging.getLogger("main")


_JOB_LOCK = threading.Lock()
READ_ONLY = {"status", "models", "replay"}   # các lệnh này không cần khóa tiến trình duy nhất


def safe(fn):
    """Job lỗi chỉ ghi log rồi chờ lần lịch kế tiếp, không làm sập cả scheduler."""
    @functools.wraps(fn)
    def wrapper(cfg=None):
        try:
            with _JOB_LOCK:   # các job (discover/snapshot/crawl) chạy lần lượt, không giẫm lên nhau
                fn(config.load())   # nạp lại pipeline.yaml mỗi lần chạy: sửa file là có hiệu lực, không cần khởi động lại
        except SystemExit:
            raise
        except Exception:
            log.exception("Job %s lỗi, sẽ thử lại ở lần lịch kế tiếp", fn.__name__)
    return wrapper


def ctx(cfg):
    conn = connect(config.DB_PATH)
    q = cfg["quota"]
    ledger = QuotaLedger(config.DB_PATH, q["daily_limit"], q["safety_ratio"], q["search_daily_cap"])
    return conn, ledger, YouTube(cfg["api_key"], ledger)


def close_all(conn, ledger):
    ledger.close()
    conn.close()


def job_discover(cfg):
    conn, ledger, yt = ctx(cfg)
    ledger.start_run((cfg.get("discover") or {}).get("run_budget_units", 300))
    try:
        from .models import write_registry
        write_registry(cfg)   # cập nhật data/models.json mỗi khi config đổi
        run_discover(cfg, yt, conn)
    finally:
        close_all(conn, ledger)


def cmd_resolve_names(cfg, limit):
    conn, ledger, yt = ctx(cfg)
    ledger.start_run(limit * 105)
    results = []
    try:
        results = suggest_channel_ids(cfg, yt, limit)
    except QuotaExceeded as e:
        print("Dừng giữa chừng:", e)
    lines = ["# Gợi ý do API trả về. HÃY MỞ LINK KIỂM TRA TỪNG KÊNH rồi mới chép vào pipeline.yaml", "channels:"]
    for ch, ids, info in results:
        tags = ", ".join(f'"{t}"' for t in ch.get("tags", []))
        top = ids[0] if ids else ""
        i = info.get(top, {})
        lines += [f'  - channel_id: "{top}"', f'    name: "{ch["name"]}"', "    enabled: true", f"    tags: [{tags}]"]
        for cid in ids:
            sn, st = info.get(cid, {}).get("snippet", {}), info.get(cid, {}).get("statistics", {})
            lines.append(f'    # {"(chọn)" if cid == top else "(khác)"} {cid} | "{sn.get("title")}" | {sn.get("customUrl", "")} '
                         f'| {st.get("subscriberCount", "ẩn")} sub | {st.get("videoCount", "?")} video | https://www.youtube.com/channel/{cid}')
    out = config.CONFIG_PATH.parent / "channels.suggested.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nĐã ghi {out}. Hạn mức: {ledger.status()}")


def job_snapshot(cfg):
    conn, ledger, yt = ctx(cfg)
    ledger.start_run(100)
    try:
        ids = [r[0] for r in conn.execute("SELECT video_id FROM videos WHERE status!='disabled'")]
        refresh_videos(yt, conn, ids, cfg)
        log.info("Đã chụp số liệu %d video", len(ids))
    finally:
        close_all(conn, ledger)


def job_crawl(cfg):
    conn, ledger, yt = ctx(cfg)
    ledger.start_run(cfg["crawl"]["run_budget_units"])
    try:
        run_crawl(cfg, yt, conn, Sink(cfg))
    finally:
        close_all(conn, ledger)


def cmd_models(cfg):
    from .models import specs, write_registry
    sp, conn = specs(cfg), connect(config.DB_PATH)

    def line(s, prefix):
        r = conn.execute("SELECT COUNT(*) t, COALESCE(SUM(status='done'),0) d FROM videos WHERE instr('|'||model||'|', ?)>0",
                         (f"|{s['name']}|",)).fetchone()
        print(f"{prefix}{s['name']:12} {s['start']:%Y-%m-%d} -> {s['end']:%Y-%m-%d}  video {r['d']}/{r['t']} done  alias={s['aliases']}")

    for s in sp.values():
        if "main" in s["roles"]:
            line(s, "[main]  ")
            for rv in s["rivals"]:
                line(sp[rv], "   └ rival  ")
            if not s["rivals"]:
                print("   (chưa có đối thủ)")
    print("Đã ghi", write_registry(cfg))


def cmd_status(cfg):
    conn = connect(config.DB_PATH)
    q = cfg["quota"]
    print("Hạn mức:", QuotaLedger(config.DB_PATH, q["daily_limit"], q["safety_ratio"], q["search_daily_cap"]).status())
    print("\nVideo theo mẫu máy / trạng thái (dùng để chốt mục còn mở #1: cần >= 20 video/mẫu):")
    for r in conn.execute("SELECT model,status,COUNT(*) n,SUM(comment_count) c FROM videos GROUP BY 1,2 ORDER BY 1,2"):
        print(f"  {r['model']:6} {r['status']:12} {r['n']:4} video  ~{r['c'] or 0} comment")
    print("\nĐã cào:", conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0], "comment")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="yt-crawler")
    sp = p.add_subparsers(dest="cmd", required=True)
    for n in ("discover", "crawl", "run", "status", "snapshot-videos", "models"):
        sp.add_parser(n)
    rn = sp.add_parser("resolve-names")
    rn.add_argument("--limit", type=int, default=20)
    fc = sp.add_parser("find-channels")
    fc.add_argument("queries", nargs="+")
    fc.add_argument("--calls", type=int, default=3)
    rl = sp.add_parser("relabel", help="đổi nhãn model của dữ liệu đã cào, ví dụ: relabel main=ip15prm rival=s24u")
    rl.add_argument("pairs", nargs="+", help="cũ=mới")
    rl.add_argument("--files", nargs="+", required=True, help="tên các file trong data/raw cần đổi nhãn (comments-*.jsonl, videos-*.jsonl)")
    rl.add_argument("--dry-run", action="store_true")
    rp = sp.add_parser("replay")
    rp.add_argument("--speed", type=float, default=10)
    rp.add_argument("--model", help="chỉ phát lại một mẫu (name trong config), ví dụ ip15prm")
    rp.add_argument("--group", help="phát lại một mẫu chính cùng tất cả đối thủ của nó")
    rp.add_argument("--since"); rp.add_argument("--until")
    rp.add_argument("--max-gap", type=float, default=2.0)
    rp.add_argument("--dry-run", action="store_true")
    rp.add_argument("--strip-stats", action="store_true", help="bỏ like_count/reply_count khi phát lại")
    dd = sp.add_parser("dedupe", help="loại comment trùng khỏi data/raw (giữ bản đầu), --merge để gộp thành một file")
    dd.add_argument("--merge", action="store_true")
    dd.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    cfg = config.load()
    if a.cmd not in READ_ONLY:
        acquire()   # chỉ một tiến trình ghi tại một thời điểm

    if a.cmd == "discover":
        job_discover(cfg)
    elif a.cmd == "crawl":
        job_crawl(cfg)
    elif a.cmd == "resolve-names":
        cmd_resolve_names(cfg, a.limit)
    elif a.cmd == "dedupe":
        from .dedupe import dedupe
        dedupe(a.merge, a.dry_run)
    elif a.cmd == "relabel":
        from .relabel import relabel
        relabel(dict(x.split("=", 1) for x in a.pairs), a.files, a.dry_run)
    elif a.cmd == "models":
        cmd_models(cfg)
    elif a.cmd == "snapshot-videos":
        job_snapshot(cfg)
    elif a.cmd == "status":
        cmd_status(cfg)
    elif a.cmd == "find-channels":
        conn, ledger, yt = ctx(cfg)
        for title, cid, n in find_channels(cfg, yt, a.queries, a.calls):
            print(f"{n:3}  {title:40} {cid}")
    elif a.cmd == "replay":
        from .models import group_members
        pt = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc) if s else None
        wanted = ({a.model} if a.model else set()) | (group_members(cfg, a.group) if a.group else set())
        if a.group and not wanted:
            raise SystemExit(f"Không có mẫu chính '{a.group}' trong config.models")
        run_replay(cfg, a.speed, wanted or None, pt(a.since), pt(a.until), a.max_gap, a.dry_run, a.strip_stats)
    elif a.cmd == "run":
        tz = ZoneInfo(cfg["timezone"])
        now = datetime.now(tz)
        s = BlockingScheduler(timezone=tz)
        s.add_job(safe(job_discover), "cron", hour=cfg["schedule"]["discover_cron_hour"], args=[cfg],
                  id="discover", max_instances=1, coalesce=True)
        s.add_job(safe(job_snapshot), "cron", hour=cfg["schedule"]["discover_cron_hour"] + 1, args=[cfg],
                  id="snapshot", max_instances=1, coalesce=True)
        s.add_job(safe(job_crawl), "interval", minutes=cfg["schedule"]["crawl_every_min"], args=[cfg],
                  id="crawl", max_instances=1, coalesce=True, next_run_time=now + timedelta(minutes=3))
        s.add_job(safe(job_discover), "date", run_date=now + timedelta(seconds=5), args=[cfg], id="discover_now")
        log.info("Scheduler chạy: discover ngay bây giờ, crawl sau 3 phút rồi mỗi %d phút. Ctrl+C để dừng.",
                 cfg["schedule"]["crawl_every_min"])
        try:
            s.start()
        except (KeyboardInterrupt, SystemExit):
            pass


if __name__ == "__main__":
    main()

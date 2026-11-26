"""
Mục đích: Cửa vào dòng lệnh của crawler: python -m crawler.main <lệnh>, chạy từ src/ingest; cập nhật lần cuối: 2026-11-11.

Lệnh chính: discover (tìm video theo kênh), crawl (cào bình luận), run (tự chạy theo lịch), status, models, snapshot-videos, replay.
Dọn/sửa dữ liệu: dedupe, relabel, repair-missing. Tài khoản người bình luận (schema v3): backfill-authors, enrich-authors,
apply-authors, authors-export, authors-import. Chia máy: worker-init. Tìm kênh: resolve-names, find-channels.
Lệnh ghi dữ liệu xin khóa (lock.py) để chỉ một tiến trình ghi tại một thời điểm. Chi tiết: docs/1-thu-thap/huong-dan.md.
"""
import argparse
import functools
import logging
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
                fn(config.load())   # nạp lại config/pipeline.yaml mỗi lần chạy: sửa file là có hiệu lực, không cần khởi động lại
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


def job_discover(cfg, budget=None, rescan=False):
    conn, ledger, yt = ctx(cfg)
    ledger.start_run(budget or (cfg.get("discover") or {}).get("run_budget_units", 300))
    try:
        from .models import write_registry
        write_registry(cfg)   # cập nhật data/models.json mỗi khi config đổi
        if rescan:
            from .discover import reset_scan
            reset_scan(conn)
            log.info("Đã xóa con trỏ quét: quét lại mọi kênh từ đầu playlist")
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
    lines = ["# Gợi ý do API trả về. HÃY MỞ LINK KIỂM TRA TỪNG KÊNH rồi mới chép vào config/pipeline.yaml", "channels:"]
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
        from .discover import my_channel_ids
        mine = my_channel_ids(cfg, conn)
        ids = [r[0] for r in conn.execute("SELECT video_id, channel_id FROM videos WHERE status NOT IN ('disabled','excluded')")
               if r[1] in mine]
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


def cmd_authors(cfg, a):
    from . import authors as A
    if a.cmd in ("backfill-authors", "enrich-authors"):
        conn, ledger, yt = ctx(cfg)
        ledger.start_run(a.budget or 10 ** 9)
        try:
            if a.cmd == "backfill-authors":
                A.backfill(cfg, yt, conn, A.parse_part(a.part), a.ids_from)
            else:
                A.enrich(cfg, yt, conn, A.parse_part(a.part), a.refresh_days)
            print("Hạn mức:", ledger.status())
        finally:
            close_all(conn, ledger)
        return
    conn = connect(config.DB_PATH)
    try:
        if a.cmd == "authors-export":
            out = a.out or str(config.RAW_DIR / f"authors-export-{cfg['worker']}.jsonl")
            print(f"Đã xuất {A.export(conn, out)} dòng ra {out}")
        elif a.cmd == "authors-import":
            print("Đã nhập: %d comment, %d kênh" % A.import_(conn, a.files))
        elif a.cmd == "apply-authors":
            A.apply(cfg, conn, a.dry_run)
    finally:
        conn.close()


def cmd_worker_init(cfg):
    """Máy thứ hai bắt đầu từ BẢN SAO state.db của máy chính: xóa sổ quota (khóa API khác, hạn mức riêng)
    và in danh sách kênh máy này phụ trách."""
    if cfg["worker"] == (cfg.get("workers") or {}).get("default_owner", "p1"):
        raise SystemExit("worker-init chỉ chạy trên máy phụ (CRAWLER_WORKER khác p1 trong .env)")
    conn = connect(config.DB_PATH)
    conn.execute("DELETE FROM quota")
    conn.commit()
    mine = [c.get("name") for c in cfg.get("channels") or [] if str(c.get("owner")) == cfg["worker"] and c.get("enabled", True)]
    print(f"Máy {cfg['worker']}: đã xóa sổ quota cũ. Phụ trách {len(mine)} kênh: {', '.join(mine) or '(chưa có kênh nào có owner: ' + cfg['worker'] + ')'}")
    conn.close()


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
    ca = conn.execute("SELECT COUNT(*), COALESCE(SUM(status='ok'),0) FROM comment_authors").fetchone()
    au = conn.execute("SELECT COUNT(*), COALESCE(SUM(status='ok'),0) FROM authors").fetchone()
    print(f"Tài khoản người bình luận (máy {cfg['worker']}): đã tra {ca[0]} comment ({ca[1]} còn tồn tại), "
          f"{au[0]} kênh ({au[1]} còn hoạt động)")
    from .models import bounds
    from .timeutil import parse
    earliest = bounds(cfg)[0]
    print(f"\nTiến độ quét uploads của kênh (cần quét về {earliest:%Y-%m-%d}):")
    rows = conn.execute("""SELECT c.channel_id, c.title, s.head_pub, s.tail_pub, s.tail_done, s.pages,
                             (SELECT COUNT(*) FROM uploads u WHERE u.channel_id=c.channel_id) cached,
                             (SELECT COUNT(*) FROM videos v WHERE v.channel_id=c.channel_id AND v.status!='excluded') matched
                           FROM channels c LEFT JOIN channel_scan s USING(channel_id) ORDER BY c.title""").fetchall()
    enabled = {ch.get("channel_id") or ch.get("handle") or ch.get("id") for ch in cfg.get("channels") or []
               if ch.get("enabled", True)}
    for r in rows:
        if r["channel_id"] not in enabled:
            continue
        if r["tail_done"] or (r["tail_pub"] and parse(r["tail_pub"]) < earliest):
            state = "xong"
        elif r["pages"]:
            state = f"đang quét, tới {r['tail_pub'][:10]}"
        else:
            state = "chưa quét"
        print(f"  {r['title'][:28]:28} {state:24} cache {r['cached']:6} video | khớp mẫu {r['matched']:4}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="yt-crawler")
    sp = p.add_subparsers(dest="cmd", required=True)
    for n in ("crawl", "run", "status", "snapshot-videos", "models"):
        sp.add_parser(n)
    ds = sp.add_parser("discover")
    ds.add_argument("--budget", type=int, help="ngân sách quota cho lần chạy này (mặc định discover.run_budget_units)")
    ds.add_argument("--rescan", action="store_true", help="quét lại mọi kênh từ đầu playlist (giữ cache)")
    rm = sp.add_parser("repair-missing", help="sửa dữ liệu cũ: video đã đánh dấu cào nhưng comment không có trong data/raw")
    rm.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ báo cáo)")
    ba = sp.add_parser("backfill-authors", help="tra kênh + tên người viết cho comment cũ (1 đơn vị/50 comment)")
    ba.add_argument("--part", help="chia việc: i/n, vd 1/2 cho người 1, 2/2 cho người 2")
    ba.add_argument("--ids-from", help="đọc comment_id từ file jsonl này thay vì data/raw (máy phụ)")
    ba.add_argument("--budget", type=int, help="giới hạn đơn vị quota cho lần chạy")
    ea = sp.add_parser("enrich-authors", help="tra ngày tạo/số video/sub của kênh người viết (1 đơn vị/50 kênh)")
    ea.add_argument("--part")
    ea.add_argument("--budget", type=int)
    ea.add_argument("--refresh-days", type=int, help="làm mới cả thông tin cũ hơn N ngày (chính sách 30 ngày)")
    ex = sp.add_parser("authors-export", help="xuất bảng tra tài khoản để gửi cho người tổng hợp")
    ex.add_argument("--out")
    im = sp.add_parser("authors-import", help="nhập file authors-export của người khác")
    im.add_argument("files", nargs="+")
    ap = sp.add_parser("apply-authors", help="ghi 6 trường author_* vào data/raw/comments*.jsonl (schema v3)")
    ap.add_argument("--dry-run", action="store_true")
    sp.add_parser("worker-init", help="máy phụ: chuẩn bị bản sao state.db (xóa sổ quota cũ)")
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

    if a.cmd in ("backfill-authors", "enrich-authors", "authors-export", "authors-import", "apply-authors"):
        cmd_authors(cfg, a)
        return
    if a.cmd == "worker-init":
        cmd_worker_init(cfg)
        return
    if a.cmd == "discover":
        job_discover(cfg, a.budget, a.rescan)
    elif a.cmd == "repair-missing":
        from .repair_missing import repair
        repair(cfg, a.apply)
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

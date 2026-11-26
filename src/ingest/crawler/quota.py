"""Sổ cái hạn mức: đếm đơn vị TRƯỚC mỗi request (request lỗi cũng tốn >= 1 đơn vị).
Hạn mức YouTube reset lúc nửa đêm giờ Thái Bình Dương (PT) nên khóa ngày theo PT."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")

COSTS = {
    "channels.list": 1, "playlistItems.list": 1, "videos.list": 1,
    "commentThreads.list": 1, "comments.list": 1, "search.list": 100,
}


class QuotaExceeded(Exception):
    pass


class QuotaLedger:
    """Dùng KẾT NỐI RIÊNG ở chế độ autocommit: mỗi lệnh tự commit, không bao giờ giữ khóa ghi lâu,
    và việc 'kiểm tra + cộng đơn vị' là một lệnh UPDATE nguyên tử (an toàn khi nhiều tiến trình)."""

    def __init__(self, db_path, daily_limit=10000, safety_ratio=0.85, search_cap=80):
        self.conn = sqlite3.connect(db_path, timeout=60, isolation_level=None)
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.limit = int(daily_limit * safety_ratio)
        self.search_cap = search_cap
        self.run_limit = None
        self.run_used = 0

    def close(self):
        self.conn.close()

    @staticmethod
    def day():
        return datetime.now(PT).strftime("%Y-%m-%d")

    def start_run(self, budget):
        self.run_limit, self.run_used = budget, 0

    def charge(self, method, n=1):
        cost = COSTS.get(method, 1) * n
        day, is_search = self.day(), 1 if method == "search.list" else 0
        if self.run_limit is not None and self.run_used + cost > self.run_limit:
            raise QuotaExceeded("hết ngân sách của lần chạy này")
        self.conn.execute("INSERT OR IGNORE INTO quota(day) VALUES(?)", (day,))
        cur = self.conn.execute(
            "UPDATE quota SET units=units+?, search_calls=search_calls+? WHERE day=? AND exhausted=0 "
            "AND units+?<=? AND (?=0 OR search_calls<?)",
            (cost, is_search, day, cost, self.limit, is_search, self.search_cap))
        if cur.rowcount == 0:
            units, calls, exhausted = self.conn.execute(
                "SELECT units, search_calls, exhausted FROM quota WHERE day=?", (day,)).fetchone()
            if exhausted:
                raise QuotaExceeded("API báo hết hạn mức hôm nay")
            if is_search and calls >= self.search_cap:
                raise QuotaExceeded("hết số lần search.list cho phép hôm nay")
            raise QuotaExceeded(f"chạm ngưỡng ngày ({units}/{self.limit})")
        self.run_used += cost

    def mark_exhausted(self):
        self.conn.execute("INSERT OR IGNORE INTO quota(day) VALUES(?)", (self.day(),))
        self.conn.execute("UPDATE quota SET exhausted=1 WHERE day=?", (self.day(),))

    def status(self):
        day = self.day()
        self.conn.execute("INSERT OR IGNORE INTO quota(day) VALUES(?)", (day,))
        u, c, e = self.conn.execute("SELECT units, search_calls, exhausted FROM quota WHERE day=?", (day,)).fetchone()
        return {"day_pt": day, "used": u, "limit": self.limit, "search_calls": c, "exhausted": bool(e)}

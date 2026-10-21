"""Danh sách mẫu máy trong config/pipeline.yaml: mỗi mẫu chính (main) có thể có NHIỀU đối thủ (rivals).

models:
  - name: ip15prm                     # nhãn ghi vào trường `model` (không dấu, không chứa '|')
    title: iPhone 15 Pro Max          # (tùy chọn) tên hiển thị
    aliases: [iPhone 15 Pro Max]      # cách gọi trong tiêu đề video (không phân biệt hoa thường, dấu)
    exclude: [15 pro max vs]          # (tùy chọn) tiêu đề chứa cụm này thì KHÔNG tính
    launch_date: 2023-09-12           # ngày ra mắt tại VN; có thì cào đúng cửa sổ N tuần sau đó
    rivals:                           # NHIỀU đối thủ của mẫu này
      - name: s24u
        aliases: [Galaxy S24 Ultra, S24 Ultra]
        launch_date: 2024-01-10       # (tùy chọn) bỏ trống thì dùng ngày ra mắt của mẫu chính
      - p9pro                         # chỉ ghi tên: tham chiếu đến mẫu đã khai báo ở chỗ khác

Một mẫu có thể là đối thủ của nhiều mẫu chính (khai báo ở nhiều nơi cũng được, cùng một `name`).
Video nhắc nhiều mẫu thì model = tên các mẫu nối bằng '|' (xếp A-Z), ví dụ "ip15prm|s24u".
Quan hệ main/rival KHÔNG nằm trong từng comment mà trong data/models.json (lệnh `models` ghi ra)."""
import json
import logging
from datetime import datetime, timedelta, timezone
from . import config
from .timeutil import ICT, iso, now, unaccent

log = logging.getLogger("models")
_warned = set()


def _as_list(ms):
    """Chấp nhận cả định dạng cũ {main: {...}, rival: {...}} (rival thành đối thủ của main)."""
    if not isinstance(ms, dict):
        return [dict(m) for m in ms]
    out = [{**v, "name": k, "title": v.get("name")} for k, v in ms.items()]
    if "main" in ms and "rival" in ms:
        main = next(m for m in out if m["name"] == "main")
        rival = next(m for m in out if m["name"] == "rival")
        out.remove(rival)
        main["rivals"] = [rival]
    return out


def _add(out, m, role, parent=None, inherit_launch=None):
    if isinstance(m, str):
        m = {"name": m}
    name = str(m["name"]).strip()
    if not name or "|" in name:
        raise ValueError(f"Tên mẫu không hợp lệ: {name!r} (không được rỗng, không chứa '|')")
    s = out.setdefault(name, {"name": name, "title": name, "roles": set(), "rival_of": set(), "rivals": [],
                              "aliases": [], "exclude": [], "launch": None, "launch_explicit": False})
    s["roles"].add(role)
    if parent:
        s["rival_of"].add(parent)
    if m.get("title"):
        s["title"] = str(m["title"])
    for key in ("aliases", "exclude"):
        for v in m.get(key) or []:
            if str(v) not in s[key]:
                s[key].append(str(v))
    if m.get("launch_date"):
        ld = str(m["launch_date"])
        if s["launch_explicit"] and s["launch"] != ld:
            log.warning("Mẫu '%s' khai báo hai ngày ra mắt khác nhau (%s, %s): giữ giá trị đầu", name, s["launch"], ld)
        elif not s["launch_explicit"]:
            s["launch"], s["launch_explicit"] = ld, True
    elif s["launch"] is None and inherit_launch:
        s["launch"] = str(inherit_launch)   # đối thủ chưa có ngày ra mắt riêng -> dùng của mẫu chính
    return s


def specs(cfg):
    out = {}
    for m in _as_list(cfg["models"]):
        main = _add(out, m, "main")
        for r in m.get("rivals") or []:
            rs = _add(out, r, "rival", parent=main["name"], inherit_launch=main["launch"])
            if rs["name"] != main["name"] and rs["name"] not in main["rivals"]:
                main["rivals"].append(rs["name"])
    for s in out.values():
        s["aliases_raw"] = s["aliases"] or [s["title"], s["name"]]
        s["aliases"] = [unaccent(a) for a in s["aliases_raw"]]
        s["exclude_raw"] = s["exclude"]
        s["exclude"] = [unaccent(x) for x in s["exclude_raw"]]
        if len(s["rival_of"]) > 1 and not s["launch_explicit"]:
            log.warning("Đối thủ '%s' dùng chung cho %s nhưng chưa có launch_date riêng: tạm dùng ngày của mẫu chính khai báo đầu tiên. "
                        "Hãy điền launch_date cho nó.", s["name"], s["rival_of"])
        if s["launch"]:
            s["start"] = datetime.fromisoformat(s["launch"]).replace(tzinfo=ICT).astimezone(timezone.utc)
            s["end"] = s["start"] + timedelta(weeks=cfg["window_weeks"])
        else:
            if s["name"] not in _warned:
                log.warning("Mẫu '%s' chưa có launch_date: tạm quét video 365 ngày gần nhất, không giới hạn 4 tuần", s["name"])
                _warned.add(s["name"])
            s["start"], s["end"] = now() - timedelta(days=365), now() + timedelta(days=1)
        s["roles"], s["rival_of"] = sorted(s["roles"]), sorted(s["rival_of"])
    return out


def window(cfg, model_value):
    """Cửa sổ thời gian của comment. Video nhiều mẫu ('a|b') lấy cửa sổ hợp nhất.
    Mẫu đã bị xóa khỏi config thì bỏ qua; không còn mẫu nào thì dùng 365 ngày gần nhất."""
    sp = specs(cfg)
    known = [sp[n] for n in str(model_value).split("|") if n in sp]
    if not known:
        return now() - timedelta(days=365), now() + timedelta(days=1)
    return min(k["start"] for k in known), max(k["end"] for k in known)


def bounds(cfg):
    """Khoảng thời gian cần quét uploads của kênh: từ sớm nhất đến muộn nhất của mọi mẫu."""
    before = timedelta(days=cfg["video_window_before_days"])
    sp = specs(cfg).values()
    return min(s["start"] for s in sp) - before, max(s["end"] for s in sp)


def classify(cfg, title, published):
    """Trả về tên mẫu (hoặc 'a|b' nếu nhiều mẫu) hoặc None. Video phải đăng trong cửa sổ video của mẫu đó."""
    t = unaccent(title)
    before = timedelta(days=cfg["video_window_before_days"])
    hits = [s["name"] for s in specs(cfg).values()
            if s["start"] - before <= published <= s["end"]
            and any(a in t for a in s["aliases"]) and not any(x in t for x in s["exclude"])]
    return "|".join(sorted(hits)) or None


def group_members(cfg, main_name):
    """Mẫu chính + tất cả đối thủ của nó."""
    s = specs(cfg).get(main_name)
    return {main_name, *s["rivals"]} if s else set()


def registry(cfg):
    sp = specs(cfg)
    return {
        "generated_at": iso(now()),
        "groups": [{"main": s["name"], "rivals": s["rivals"]} for s in sp.values() if "main" in s["roles"]],
        "models": [{"name": s["name"], "title": s["title"], "roles": s["roles"], "rival_of": s["rival_of"],
                    "rivals": s["rivals"], "aliases": s["aliases_raw"], "exclude": s["exclude_raw"],
                    "launch_date": s["launch"], "window_start": iso(s["start"]), "window_end": iso(s["end"])}
                   for s in sp.values()],
    }


def write_registry(cfg):
    path = config.DB_PATH.parent / "models.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
    return path

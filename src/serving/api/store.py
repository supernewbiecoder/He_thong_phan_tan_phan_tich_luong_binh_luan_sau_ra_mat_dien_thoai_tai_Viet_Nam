"""Đọc MongoDB và dựng dữ liệu cho từng tab của dashboard.

Nguồn theo docs/data-model.md:
  aggregates        số đếm khen/chê/trung tính  -> Q1, Q2, Q3a, Q4
  aspect_mentions   từng mention                -> bình luận mẫu, Q3b, Q5
  models, comments, videos, alerts
  analysis_results  kết quả Công việc 12 (khoảng tin cậy, kiểm định, kết luận)

API tự tính các tỷ lệ mô tả từ số đếm. Khoảng tin cậy và kiểm định KHÔNG tính ở
đây: chúng lấy từ kết quả Công việc 12, và chỉ được gắn vào khi số đếm trong kết
quả đó khớp với số đếm đang có trong DB (tránh ghép kiểm định của một lần chạy
cũ với số liệu mới).
"""
import collections
import time
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from .metrics import add_counts, same_counts, summarize
from .settings import ASPECTS, DEFECT_TYPES, UNVERIFIED_LABEL_SOURCES, Settings

COLLECTIONS = ("models", "videos", "comments", "aspect_mentions", "aggregates", "alerts",
               "gold_labels", "analysis_results")
TEST_FIELDS = ("test_id", "estimate", "ci95", "p_value", "p_adjusted", "significant", "conclusion",
               "conclusion_allowed", "status", "reasons", "compare_with")
BLOCKER_TEXT = {
    "synthetic_or_unconfirmed_dataset": "Dữ liệu nhân tạo hoặc chưa được xác nhận",
    "label_accuracy_not_verified": "Chưa đánh giá độ chính xác của nhãn",
    "rule_baseline_labels": "Nhãn là baseline luật từ khóa",
}


class NotFound(Exception):
    """Không có dữ liệu cho máy hoặc phiên bản được hỏi."""


def _test(row: Optional[Mapping]) -> Optional[Dict[str, object]]:
    return None if row is None else {key: row.get(key) for key in TEST_FIELDS if key in row}


def _rival_ids(model: Mapping) -> List[str]:
    """`rivals` có thể là danh sách mã máy hoặc danh sách object như trong pipeline.yaml."""
    ids = []
    for rival in model.get("rivals") or []:
        rival_id = rival if isinstance(rival, str) else rival.get("model_id") or rival.get("name")
        if rival_id:
            ids.append(rival_id)
    return ids


def _parse_time(value) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


class DashboardStore:
    def __init__(self, db, settings: Optional[Settings] = None):
        self.db = db
        self.settings = settings or Settings()
        self._cache: Dict[str, Tuple[float, object]] = {}

    # ------------------------------------------------------------------ tiện ích

    def _cached(self, key: str, build: Callable[[], object]):
        hit = self._cache.get(key)
        if hit and time.monotonic() - hit[0] < self.settings.cache_seconds:
            return hit[1]
        value = build()
        self._cache[key] = (time.monotonic(), value)
        return value

    def _models(self) -> Dict[str, dict]:
        return {m["model_id"]: m for m in self.db.models.find({}, {"_id": 0}) if m.get("model_id")}

    def _card(self, model_id: str, role: str, models: Mapping[str, dict]) -> Dict[str, object]:
        model = models.get(model_id, {})
        return {"model_id": model_id, "role": role, "title": model.get("title") or model_id,
                "brand": model.get("brand"), "launch_date": model.get("launch_date"),
                "in_catalog": model_id in models}

    def _summary(self, counts: Mapping[str, int]) -> Dict[str, object]:
        return summarize(counts["n_pos"], counts["n_neg"], counts["n_neu"], self.settings.min_opinionated)

    def _weeks(self) -> List[int]:
        return list(range(1, self.settings.window_weeks + 1))

    # ------------------------------------------------------------------ phiên bản, phạm vi

    def versions(self) -> List[Dict[str, object]]:
        """Các model_version có trong aggregates, kèm nguồn nhãn lấy từ aspect_mentions."""
        return self._cached("versions", self._versions)

    def _versions(self) -> List[Dict[str, object]]:
        totals: Dict[str, int] = collections.Counter()
        for row in self.db.aggregates.aggregate([{"$group": {
                "_id": "$model_version",
                "n": {"$sum": {"$add": ["$n_pos", "$n_neg", "$n_neu"]}}}}]):
            if row["_id"]:
                totals[row["_id"]] = row["n"] or 0
        sources: Dict[str, Dict[str, int]] = collections.defaultdict(collections.Counter)
        for row in self.db.aspect_mentions.aggregate([{"$group": {
                "_id": {"version": "$model_version", "source": "$label_source"}, "n": {"$sum": 1}}}]):
            # Mention thiếu label_source vẫn được đếm, dưới tên "unknown", để không lọt qua kiểm tra.
            sources[row["_id"].get("version")][row["_id"].get("source") or "unknown"] += row["n"]
        return [{"model_version": version, "n_mentions_in_aggregates": totals[version],
                 "label_sources": dict(sources.get(version, {}))}
                for version in sorted(totals, key=lambda v: -totals[v])]

    def targets(self, model_version: str) -> List[Dict[str, object]]:
        return self._cached(f"targets|{model_version}", lambda: self._targets(model_version))

    def _targets(self, model_version: str) -> List[Dict[str, object]]:
        models = self._models()
        rows = self.db.aggregates.aggregate([
            {"$match": {"model_version": model_version}},
            {"$group": {"_id": "$target_model",
                        "n": {"$sum": {"$add": ["$n_pos", "$n_neg", "$n_neu"]}}}}])
        result = [{"model_id": row["_id"], "title": models.get(row["_id"], {}).get("title") or row["_id"],
                   "n_total": row["n"]} for row in rows if row["_id"]]
        return sorted(result, key=lambda item: (-item["n_total"], item["model_id"]))

    def _latest_analysis(self) -> Optional[dict]:
        docs = list(self.db.analysis_results.find({}, {"_id": 0, "result": 0}))
        return max(docs, key=lambda d: d.get("loaded_at") or "") if docs else None

    def defaults(self) -> Dict[str, Optional[str]]:
        """Phiên bản và máy mặc định: ưu tiên lần phân tích mới nhất, không có thì bộ nhiều dữ liệu nhất."""
        latest = self._latest_analysis()
        # Chỉ theo lần phân tích mới nhất khi DB thật sự có số đếm cho đúng máy và phiên bản đó.
        if latest and latest.get("model_version") and any(
                item["model_id"] == latest.get("target_model")
                for item in self.targets(latest["model_version"])):
            return {"model_version": latest["model_version"], "model": latest["target_model"]}
        versions = self.versions()
        if not versions:
            return {"model_version": None, "model": None}
        version = versions[0]["model_version"]
        targets = self.targets(version)
        return {"model_version": version, "model": targets[0]["model_id"] if targets else None}

    def meta(self, model_version: Optional[str] = None) -> Dict[str, object]:
        defaults = self.defaults()
        version = model_version or defaults["model_version"]
        return {
            "defaults": defaults, "versions": self.versions(),
            "targets": self.targets(version) if version else [],
            "aspects": ASPECTS, "defect_types": DEFECT_TYPES,
            "window_weeks": self.settings.window_weeks,
            "min_opinionated": self.settings.min_opinionated,
        }

    def _resolve(self, model: Optional[str], model_version: Optional[str]):
        defaults = self.defaults()
        version = model_version or defaults["model_version"]
        if not version:
            raise NotFound("Chưa có dữ liệu trong collection aggregates.")
        target = model or (defaults["model"] if version == defaults["model_version"] else None)
        available = self.targets(version)
        if not available:
            raise NotFound(f"Không có aggregates cho model_version '{version}'.")
        target = target or available[0]["model_id"]
        if target not in {item["model_id"] for item in available}:
            raise NotFound(f"Không có aggregates cho máy '{target}' ở model_version '{version}'.")

        models = self._models()
        document = self.db.analysis_results.find_one(
            {"target_model": target, "model_version": version}, {"_id": 0})
        analysis = (document or {}).get("result")
        config = (analysis or {}).get("config") or {}
        predecessor = config.get("predecessor_model") or models.get(target, {}).get("predecessor_id")
        rivals = list(config.get("rival_models") or _rival_ids(models.get(target, {})))
        with_data = {item["model_id"] for item in available}
        if not config:
            # Không có cấu hình phân tích: lấy tối đa hai đối thủ có dữ liệu.
            rivals = [r for r in rivals if r in with_data][:2]
        rivals = [r for r in rivals if r not in (target, predecessor)]

        cards = [self._card(target, "X", models)]
        if predecessor:
            cards.append(self._card(predecessor, "P", models))
        cards += [self._card(rival, f"R{i}", models) for i, rival in enumerate(rivals, start=1)]
        scope = {"target": target, "predecessor": predecessor, "rivals": rivals, "models": cards,
                 "model_version": version, "window_weeks": self.settings.window_weeks}
        return scope, analysis, document

    # ------------------------------------------------------------------ số đếm

    def _aggregate_rows(self, model_ids: Iterable[str], version: str) -> List[dict]:
        return list(self.db.aggregates.find(
            {"model_version": version, "target_model": {"$in": list(model_ids)}},
            {"_id": 0, "target_model": 1, "aspect": 1, "week_since_launch": 1, "video_id": 1,
             "n_pos": 1, "n_neg": 1, "n_neu": 1}))

    def _grouped(self, rows: List[dict], *keys: str) -> Dict[tuple, Dict[str, int]]:
        """Cộng số đếm theo khóa, chỉ lấy các tuần trong cửa sổ."""
        groups: Dict[tuple, List[dict]] = collections.defaultdict(list)
        weeks = set(self._weeks())
        for row in rows:
            if row.get("week_since_launch") in weeks:
                groups[tuple(row.get(key) for key in keys)].append(row)
        return {key: add_counts(items) for key, items in groups.items()}

    def _mention_query(self, version: str, **extra) -> Dict[str, object]:
        window_days = 7 * self.settings.window_weeks
        return {"model_version": version, "author_is_creator": {"$ne": True},
                "days_since_launch": {"$gte": 0, "$lt": window_days}, **extra}

    # ------------------------------------------------------------------ trạng thái dữ liệu

    def _analysis_matches(self, analysis: Optional[dict], by_model, by_week, by_cell) -> Dict[str, object]:
        """So số đếm trong kết quả Công việc 12 với số đếm đang có trong DB."""
        if not analysis:
            return {"available": False, "usable": False, "checked_cells": 0, "mismatched_cells": 0}
        checked = mismatched = 0
        zero = {"n_pos": 0, "n_neg": 0, "n_neu": 0}
        pairs = [(row, by_model.get((row.get("target_model"),), zero))
                 for row in (analysis.get("q1") or {}).get("overall") or []]
        pairs += [(row, by_week.get((row.get("target_model"), row.get("week_since_launch")), zero))
                  for row in (analysis.get("q1") or {}).get("weekly") or []]
        pairs += [(row, by_cell.get((row.get("target_model"), row.get("aspect")), zero))
                  for row in (analysis.get("q3a") or {}).get("matrix") or []]
        for row, counts in pairs:
            checked += 1
            mismatched += not same_counts(row, counts)
        return {"available": True, "usable": checked > 0 and mismatched == 0,
                "checked_cells": checked, "mismatched_cells": mismatched}

    def _data_status(self, version: str, analysis: Optional[dict], document: Optional[dict],
                     match: Mapping[str, object]) -> Dict[str, object]:
        sources = next((item["label_sources"] for item in self.versions()
                        if item["model_version"] == version), {})
        reasons = [text for source, text in UNVERIFIED_LABEL_SOURCES.items() if source in sources]
        if not sources:
            reasons.append("Không có aspect_mentions cho phiên bản này nên không xác định được nguồn nhãn")
        if not match["available"]:
            reasons.append("Chưa có kết quả kiểm định của Công việc 12: chỉ hiển thị số mô tả, không kết luận")
        elif not match["usable"]:
            reasons.append("Kết quả kiểm định được tính trên số liệu khác với DB hiện tại nên không hiển thị")
        if analysis:
            if analysis.get("data_kind") == "fixture":
                reasons.append("Dữ liệu là fixture nhân tạo để kiểm thử")
            for blocker in analysis.get("publication_blockers") or []:
                text = BLOCKER_TEXT.get(blocker, blocker)
                if text not in reasons:
                    reasons.append(text)
        # Minh họa khi và chỉ khi có ít nhất một lý do ở trên. Nhãn đã kiểm chứng mà không có
        # khác biệt nào có ý nghĩa thì vẫn là số liệu thật; từng kết luận do conclusion_allowed quyết định.
        return {
            "illustrative": bool(reasons), "reasons": reasons, "label_sources": sources,
            "analysis": {**match, "loaded_at": (document or {}).get("loaded_at"),
                         "analysis_version": (analysis or {}).get("analysis_version"),
                         "data_kind": (analysis or {}).get("data_kind")},
        }

    def _context(self, model: Optional[str], model_version: Optional[str]):
        scope, analysis, document = self._resolve(model, model_version)
        ids = [card["model_id"] for card in scope["models"]]
        rows = self._aggregate_rows(ids, scope["model_version"])
        by_model = self._grouped(rows, "target_model")
        by_week = self._grouped(rows, "target_model", "week_since_launch")
        by_cell = self._grouped(rows, "target_model", "aspect")
        match = self._analysis_matches(analysis, by_model, by_week, by_cell)
        status = self._data_status(scope["model_version"], analysis, document, match)
        outside = sum(add_counts([r for r in rows
                                  if r.get("week_since_launch") not in set(self._weeks())]).values())
        scope["n_mentions_outside_window"] = outside
        usable = analysis if match["usable"] else None
        return scope, usable, status, by_model, by_week, by_cell

    # ------------------------------------------------------------------ Tab 1: theo dõi ra mắt

    def launch(self, model: Optional[str] = None, model_version: Optional[str] = None) -> Dict[str, object]:
        scope, analysis, status, by_model, by_week, by_cell = self._context(model, model_version)
        target, version = scope["target"], scope["model_version"]
        zero = {"n_pos": 0, "n_neg": 0, "n_neu": 0}
        q1 = (analysis or {}).get("q1") or {}
        overall_ci = {row["target_model"]: row for row in q1.get("overall") or []}
        weekly_ci = {(row["target_model"], row["week_since_launch"]): row for row in q1.get("weekly") or []}

        overall, weekly = [], []
        for card in scope["models"]:
            model_id = card["model_id"]
            ci = overall_ci.get(model_id, {})
            overall.append({**card, **self._summary(by_model.get((model_id,), zero)),
                            "praise_ci95": ci.get("praise_ci95"), "net_ci95": ci.get("net_ci95")})
            for week in self._weeks():
                ci = weekly_ci.get((model_id, week), {})
                weekly.append({"model_id": model_id, "week_since_launch": week,
                               **self._summary(by_week.get((model_id, week), zero)),
                               "net_ci95": ci.get("net_ci95")})

        x_total = by_model.get((target,), zero)
        x_summary = self._summary(x_total)
        q2_tests = {row.get("aspect"): row for row in (analysis or {}).get("q2") or []}
        aspects = []
        for aspect, name in ASPECTS.items():
            summary = self._summary(by_cell.get((target, aspect), zero))
            gap = (None if summary["criticism_pct"] is None or x_summary["criticism_pct"] is None
                   else summary["criticism_pct"] - x_summary["criticism_pct"])
            aspects.append({"aspect": aspect, "name": name, **summary,
                            "criticism_gap_vs_overall": gap, "test": _test(q2_tests.get(aspect)),
                            "samples": self._samples(target, version, aspect)})
        aspects.sort(key=lambda item: (item["net"] is None, -(item["net"] or 0)))

        return {
            "scope": scope, "data_status": status,
            "q1": {"overall": overall, "weekly": weekly,
                   "tests": [_test(row) for row in q1.get("tests") or []]},
            "q2": {"overall": x_summary, "aspects": aspects},
            "q5": self._defects(target, version, by_week, (analysis or {}).get("q5") or []),
            "alerts": self._alerts(target),
            "answers": {key: (analysis or {}).get("answers", {}).get(key) for key in ("Q1", "Q2", "Q5")},
        }

    def _samples(self, target: str, version: str, aspect: str, per_sentiment: int = 2) -> List[dict]:
        samples = []
        for sentiment in ("neg", "pos"):
            cursor = self.db.aspect_mentions.find(
                self._mention_query(version, target_model=target, aspect=aspect, sentiment=sentiment),
                {"_id": 0, "mention_id": 1, "clause_text": 1, "sentiment": 1, "confidence": 1,
                 "label_source": 1, "is_owner": 1},
            ).sort([("confidence", -1), ("mention_id", 1)]).limit(per_sentiment)
            for mention in cursor:
                # EDA_requirement Q2: bình luận mẫu phải có người duyệt trước khi vào báo cáo.
                mention["requires_human_review"] = mention.get("label_source") != "human"
                samples.append(mention)
        return samples

    def _defects(self, target: str, version: str, by_week, analysis_rows: List[dict]) -> Dict[str, object]:
        zero = {"n_pos": 0, "n_neg": 0, "n_neu": 0}
        denominators = {week: sum(by_week.get((target, week), zero).values()) for week in self._weeks()}
        counts: Dict[Tuple[str, int], int] = collections.Counter()
        for mention in self.db.aspect_mentions.find(
                self._mention_query(version, target_model=target, is_owner=True,
                                    defect_type={"$ne": None}),
                {"_id": 0, "defect_type": 1, "days_since_launch": 1}):
            counts[(mention["defect_type"], mention["days_since_launch"] // 7 + 1)] += 1
        tests = {row.get("defect_type"): row for row in analysis_rows}
        defects = []
        for defect, name in DEFECT_TYPES.items():
            weekly = [{"week_since_launch": week, "n_defect": counts[(defect, week)],
                       "n_denominator": denominators[week],
                       "defect_mention_pct": (100.0 * counts[(defect, week)] / denominators[week]
                                              if denominators[week] else None)}
                      for week in self._weeks()]
            n_defect = sum(item["n_defect"] for item in weekly)
            row = tests.get(defect)
            # Chỉ dùng mức ưu tiên của Công việc 12 khi hai bên đếm ra cùng số lượt nhắc lỗi.
            agrees = row is not None and row.get("n_defect") == n_defect
            defects.append({
                "defect_type": defect, "name": name, "n_defect": n_defect, "weekly": weekly,
                "priority": row.get("priority") if agrees else None,
                "priority_candidate": row.get("priority_candidate") if agrees else None,
                "trend": row.get("trend") if agrees else None,
                "test": _test(row) if agrees else None,
                "count_differs_from_analysis": row is not None and not agrees,
            })
        defects.sort(key=lambda item: -item["n_defect"])
        return {"n_owner_defect_mentions": sum(item["n_defect"] for item in defects),
                "n_target_mentions": sum(denominators.values()), "defects": defects}

    def _alerts(self, target: str, limit: int = 20) -> List[dict]:
        alerts = list(self.db.alerts.find({"target_model": target}, {"_id": 0})
                      .sort("created_at", -1).limit(limit))
        for alert in alerts:
            ids = (alert.get("sample_mention_ids") or [])[:3]
            alert["samples"] = list(self.db.aspect_mentions.find(
                {"mention_id": {"$in": ids}}, {"_id": 0, "mention_id": 1, "clause_text": 1}))
            alert["aspect_name"] = ASPECTS.get(alert.get("aspect"), alert.get("aspect"))
        return alerts

    # ------------------------------------------------------------------ Tab 2: so sánh mẫu máy

    def compare(self, model: Optional[str] = None, model_version: Optional[str] = None) -> Dict[str, object]:
        scope, analysis, status, by_model, _by_week, by_cell = self._context(model, model_version)
        target, predecessor, version = scope["target"], scope["predecessor"], scope["model_version"]
        zero = {"n_pos": 0, "n_neg": 0, "n_neu": 0}
        q3a = (analysis or {}).get("q3a") or {}
        cell_ci = {(row["aspect"], row["target_model"]): row for row in q3a.get("matrix") or []}
        omnibus = {row.get("aspect"): row for row in q3a.get("omnibus") or []}
        pairwise: Dict[str, List[dict]] = collections.defaultdict(list)
        for row in q3a.get("pairwise") or []:
            pairwise[row.get("aspect")].append(_test(row))

        matrix = []
        for aspect, name in ASPECTS.items():
            cells = []
            for card in scope["models"]:
                ci = cell_ci.get((aspect, card["model_id"]), {})
                cells.append({"model_id": card["model_id"], "role": card["role"],
                              **self._summary(by_cell.get((card["model_id"], aspect), zero)),
                              "praise_ci95": ci.get("praise_ci95"),
                              "criticism_ci95": ci.get("criticism_ci95")})
            matrix.append({"aspect": aspect, "name": name, "cells": cells,
                           "omnibus": _test(omnibus.get(aspect)), "pairwise": pairwise.get(aspect, [])})

        q4_tests = {row.get("aspect"): row for row in (analysis or {}).get("q4") or []}
        generations = []
        if predecessor:
            for aspect, name in ASPECTS.items():
                before = self._summary(by_cell.get((predecessor, aspect), zero))
                after = self._summary(by_cell.get((target, aspect), zero))
                change = (None if before["criticism_pct"] is None or after["criticism_pct"] is None
                          else after["criticism_pct"] - before["criticism_pct"])
                generations.append({"aspect": aspect, "name": name, "predecessor": before, "current": after,
                                    "criticism_change": change, "test": _test(q4_tests.get(aspect))})

        return {
            "scope": scope, "data_status": status,
            "q3a": {"matrix": matrix},
            "q3b": self._head_to_head(target, [card["model_id"] for card in scope["models"][1:]], version,
                                      (analysis or {}).get("q3b") or []),
            "q4": {"predecessor": predecessor, "aspects": generations},
            "answers": {key: (analysis or {}).get("answers", {}).get(key) for key in ("Q3", "Q4")},
        }

    def _head_to_head(self, target: str, peers: List[str], version: str,
                      analysis_rows: List[dict]) -> List[dict]:
        """Đếm mệnh đề so sánh trực tiếp giữa X và một máy trong phạm vi (đời trước, đối thủ)."""
        counts: Dict[str, Dict[str, int]] = collections.defaultdict(collections.Counter)
        query = self._mention_query(version, **{"$or": [
            {"target_model": target, "compare_with": {"$in": peers}},
            {"target_model": {"$in": peers}, "compare_with": target}]})
        flip = {"target": "other", "other": "target", "tie": "tie"}
        for mention in self.db.aspect_mentions.find(
                query, {"_id": 0, "aspect": 1, "target_model": 1, "compare_winner": 1}):
            winner = mention.get("compare_winner")
            if mention.get("target_model") != target:
                winner = flip.get(winner)  # mệnh đề viết từ phía máy kia: đổi chiều về X
            key = {"target": "n_x_win", "other": "n_x_loss", "tie": "n_tie"}.get(winner)
            if key:
                counts[mention["aspect"]][key] += 1
        tests = {row.get("aspect"): row for row in analysis_rows}
        result = []
        for aspect, name in ASPECTS.items():
            wins, losses, ties = (counts[aspect][key] for key in ("n_x_win", "n_x_loss", "n_tie"))
            decisive = wins + losses
            row = tests.get(aspect)
            agrees = row is not None and (row.get("n_x_win"), row.get("n_x_loss")) == (wins, losses)
            result.append({
                "aspect": aspect, "name": name, "n_x_win": wins, "n_x_loss": losses, "n_tie": ties,
                "n_decisive": decisive, "win_pct": 100.0 * wins / decisive if decisive else None,
                "low_data": decisive < self.settings.min_opinionated,
                "win_ci95": row.get("win_ci95") if agrees else None,
                "test": _test(row) if agrees else None,
                "count_differs_from_analysis": row is not None and not agrees,
            })
        return result

    # ------------------------------------------------------------------ Tab 3 và 4

    def _comment_stats(self) -> Dict[str, object]:
        """Một lượt quét collection comments; kết quả được giữ trong bộ nhớ đệm ngắn hạn."""
        def build():
            offset = timedelta(hours=self.settings.timezone_offset_hours)
            by_model, by_hour, by_month = collections.Counter(), collections.Counter(), collections.Counter()
            reasons, versions = collections.Counter(), collections.Counter()
            totals = collections.Counter(total=0, replies=0, spam=0, not_vietnamese=0, usable=0)
            videos, latest = set(), None
            cursor = self.db.comments.find({}, {
                "_id": 0, "model": 1, "video_id": 1, "parent_id": 1, "published_at": 1, "is_spam": 1,
                "is_vietnamese": 1, "spam_reasons": 1, "pipeline_version": 1, "processed_at": 1})
            for comment in cursor:
                totals["total"] += 1
                totals["replies"] += bool(comment.get("parent_id"))
                totals["spam"] += bool(comment.get("is_spam"))
                totals["not_vietnamese"] += comment.get("is_vietnamese") is False
                totals["usable"] += (not comment.get("is_spam")) and comment.get("is_vietnamese") is not False
                by_model[comment.get("model") or "?"] += 1
                videos.add(comment.get("video_id"))
                versions[comment.get("pipeline_version") or "không ghi"] += 1
                for reason in comment.get("spam_reasons") or []:
                    reasons[reason] += 1
                published = _parse_time(comment.get("published_at"))
                if published:
                    local = published + offset
                    by_hour[local.hour] += 1
                    by_month[local.strftime("%Y-%m")] += 1
                processed = _parse_time(comment.get("processed_at"))
                if processed and (latest is None or processed > latest):
                    latest = processed
            return {"totals": dict(totals), "n_videos": len(videos - {None}), "by_model": dict(by_model),
                    "by_hour": [by_hour.get(hour, 0) for hour in range(24)],
                    "by_month": dict(sorted(by_month.items())), "spam_reasons": dict(reasons.most_common()),
                    "pipeline_versions": dict(versions),
                    "latest_processed_at": latest.isoformat() if latest else None}
        return self._cached("comment_stats", build)

    def system(self, request_stats: Optional[Mapping[str, object]] = None) -> Dict[str, object]:
        stats = self._comment_stats()
        latest = next(iter(self.db.aggregates.find({}, {"_id": 0, "updated_at": 1})
                           .sort("updated_at", -1).limit(1)), {})
        return {
            "collections": {name: self.db[name].count_documents({}) for name in COLLECTIONS},
            "comments": {**stats["totals"], "spam_reasons": stats["spam_reasons"],
                         "pipeline_versions": stats["pipeline_versions"],
                         "latest_processed_at": stats["latest_processed_at"]},
            "labels": self.versions(),
            "aggregates_updated_at": latest.get("updated_at"),
            "api": dict(request_stats or {}),
            # Giai đoạn 2 (Kafka/Spark) là tùy chọn và chưa dựng: không có số liệu thì không bịa.
            "streaming": {"deployed": False,
                          "note": "Chưa triển khai luồng Kafka/Spark (Giai đoạn 2, tùy chọn). "
                                  "Thông lượng, độ trễ xử lý và consumer lag sẽ hiển thị khi có."},
        }

    def overview(self) -> Dict[str, object]:
        stats = self._comment_stats()
        models = self._models()
        by_brand: Dict[str, int] = collections.Counter()
        by_model = []
        for model_id, count in stats["by_model"].items():
            # Video so sánh có model dạng "a|b": tính cho hãng "Nhiều máy".
            single = "|" not in model_id
            brand = (models.get(model_id, {}).get("brand") or "Chưa có trong danh mục") if single else "Video nhiều máy"
            by_brand[brand] += count
            by_model.append({"model": model_id, "title": models.get(model_id, {}).get("title") or model_id,
                             "brand": brand, "n_comments": count})
        by_model.sort(key=lambda item: -item["n_comments"])
        return {
            "totals": {**stats["totals"], "n_videos": stats["n_videos"],
                       "n_video_models": len(by_model), "n_catalog_models": len(models)},
            "by_brand": [{"brand": brand, "n_comments": count} for brand, count in by_brand.most_common()],
            "by_model": by_model, "by_hour": stats["by_hour"], "by_month": stats["by_month"],
            "timezone": f"UTC+{self.settings.timezone_offset_hours}",
        }

    def health(self) -> Dict[str, object]:
        self.db.command("ping")
        return {"status": "ok", "database": self.db.name,
                "collections": {name: self.db[name].estimated_document_count() for name in COLLECTIONS}}

"""Kiểm thử Công việc 13: API cho dashboard, script nạp DB và bộ sinh số liệu minh họa.

Chạy từ thư mục gốc repo:  python -m pytest tests/test_serving_dashboard.py -q
Dùng mongomock nên không cần MongoDB. Đặt biến môi trường TEST_MONGO_URI (vd
mongodb://localhost:27017) để chạy lại đúng các test này trên MongoDB thật.
"""
import json
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft7Validator
from pymongo.errors import ServerSelectionTimeoutError

from src.serving import demo_data, load_db
from src.serving.api.app import create_app
from src.serving.api.metrics import add_counts, same_counts, summarize
from src.serving.api.settings import ASPECTS, REPO_ROOT, Settings

VERSION = "model-v1"
SETTINGS = Settings(cache_seconds=0)


# ---------------------------------------------------------------- dữ liệu thử

def agg(target, aspect, week, video, pos, neg, neu, version=VERSION):
    row = {"target_model": target, "aspect": aspect, "week_since_launch": week, "video_id": video,
           "source": "youtube", "model_version": version, "n_pos": pos, "n_neg": neg, "n_neu": neu}
    return {**row, "agg_id": load_db.aggregate_id(row), "n_total": pos + neg + neu,
            "updated_at": "2026-11-10T00:00:00+00:00"}


def mention(mention_id, target, aspect, sentiment, days, *, source="model", creator=False, owner=None,
            defect=None, compare_with=None, winner=None, confidence=0.9, version=VERSION):
    comment_id = mention_id.split("#")[0]
    return {
        "mention_id": f"{comment_id}#0#{aspect}", "comment_id": comment_id, "parent_id": None,
        "clause_idx": 0, "clause_text": f"mệnh đề {mention_id}", "source": "youtube", "video_id": "v1",
        "video_model": target or "x1", "target_model": target, "author_hash": "a" * 64,
        "author_is_creator": creator, "aspect": aspect, "sentiment": sentiment,
        "confidence": None if source == "human" else confidence, "is_owner": owner, "defect_type": defect,
        "compare_with": compare_with, "compare_winner": winner, "published_at": "2023-02-10T03:15:00Z",
        "days_since_launch": days, "label_source": source, "model_version": version, "schema_version": 2,
    }


MODELS = [
    {"model_id": "x1", "title": "Máy X", "brand": "Samsung", "launch_date": "2023-02-02",
     "predecessor_id": "p1", "rivals": ["r1", "r2"], "aliases": []},
    {"model_id": "p1", "title": "Đời trước", "brand": "Samsung", "launch_date": "2022-02-25",
     "predecessor_id": None, "rivals": [], "aliases": []},
    {"model_id": "r1", "title": "Đối thủ 1", "brand": "Apple", "launch_date": "2022-09-16",
     "predecessor_id": None, "rivals": [], "aliases": []},
    {"model_id": "r2", "title": "Đối thủ 2", "brand": "Xiaomi", "launch_date": "2023-04-18",
     "predecessor_id": None, "rivals": [], "aliases": []},
]
AGGREGATES = [
    # X: camera tuần 1 ở hai video, pin tuần 2, và một dòng tuần 0 (trước ra mắt, ngoài cửa sổ).
    agg("x1", "CAMERA", 1, "v1", 30, 10, 5), agg("x1", "CAMERA", 1, "v2", 10, 10, 0),
    agg("x1", "BATTERY", 2, "v1", 5, 15, 2), agg("x1", "CAMERA", 0, "v1", 99, 0, 0),
    agg("p1", "CAMERA", 1, "v3", 20, 20, 0), agg("p1", "BATTERY", 1, "v3", 30, 10, 0),
    agg("r1", "CAMERA", 1, "v4", 45, 5, 0), agg("r2", "CAMERA", 1, "v5", 1, 1, 0),
    # Phiên bản nhãn khác không được lẫn vào.
    agg("x1", "CAMERA", 1, "v1", 500, 500, 0, version="other-v9"),
]
MENTIONS = [
    mention("c1", "x1", "CAMERA", "neg", 3, confidence=0.95),
    mention("c2", "x1", "CAMERA", "neg", 4, confidence=0.60),
    mention("c3", "x1", "CAMERA", "pos", 5, confidence=0.80),
    mention("c4", "x1", "CAMERA", "neg", 2, creator=True, confidence=0.99),       # chủ kênh: bỏ
    mention("c5", "x1", "CAMERA", "neg", 40, confidence=0.99),                    # ngoài 4 tuần: bỏ
    mention("c6", "x1", "BATTERY", "neg", 8, owner=True, defect="BATTERY_DRAIN"),
    mention("c7", "x1", "BATTERY", "neg", 9, owner=True, defect="BATTERY_DRAIN"),
    mention("c8", "x1", "BATTERY", "neg", 1, owner=None, defect="BATTERY_DRAIN"),  # không rõ đã dùng: bỏ
    mention("c9", "x1", "PERFORMANCE", "neg", 10, owner=True, defect="OVERHEAT", creator=True),  # chủ kênh: bỏ
    mention("d1", "x1", "CAMERA", "pos", 3, compare_with="r1", winner="target"),   # X thắng
    mention("d2", "r1", "CAMERA", "pos", 3, compare_with="x1", winner="target"),   # viết từ phía R1: X thua
    mention("d3", "x1", "CAMERA", "neu", 3, compare_with="r1", winner="tie"),
    mention("d4", "x1", "CAMERA", "pos", 3, compare_with="zz", winner="target"),   # máy ngoài phạm vi: bỏ
]


def analysis_document(overall_x=(45, 35, 7), can_publish=True, data_kind="provided"):
    """Kết quả Công việc 12 rút gọn, với số đếm khớp AGGREGATES."""
    cells = {("x1",): overall_x, ("p1",): (50, 30, 0), ("r1",): (45, 5, 0), ("r2",): (1, 1, 0)}
    overall = [{"target_model": key[0], "n_pos": c[0], "n_neg": c[1], "n_neu": c[2],
                "praise_ci95": [50.0, 60.0], "net_ci95": [1.0, 20.0]} for key, c in cells.items()]
    test = {"test_id": "Q1/p1", "compare_with": "p1", "estimate": -6.2, "ci95": [-9.0, -3.0], "p_value": 0.01,
            "p_adjusted": 0.03, "significant": True, "conclusion": "X kém hơn đời trước",
            "conclusion_allowed": can_publish, "status": "ok", "reasons": []}
    result = {
        "analysis_version": "cv12-test", "data_kind": data_kind,
        "can_publish_business_conclusions": can_publish,
        "publication_blockers": [] if can_publish else ["label_accuracy_not_verified"],
        "config": {"target_model": "x1", "predecessor_model": "p1", "rival_models": ["r1", "r2"],
                   "expected_model_version": VERSION},
        "answers": {"Q1": {"status": "ok"}},
        "q1": {"overall": overall, "weekly": [], "tests": [test]},
        "q2": [{"aspect": "BATTERY", "test_id": "Q2/BATTERY", "estimate": 31.25, "p_adjusted": 0.01,
                "significant": True, "conclusion": "Nhược điểm tương đối", "conclusion_allowed": can_publish,
                "status": "ok"}],
        "q3a": {"matrix": [{"aspect": "CAMERA", "target_model": "x1", "n_pos": 40, "n_neg": 20, "n_neu": 5,
                            "praise_ci95": [55.0, 75.0]}], "omnibus": [], "pairwise": []},
        "q3b": [{"aspect": "CAMERA", "n_x_win": 1, "n_x_loss": 1, "n_tie": 1, "win_ci95": [10.0, 90.0],
                 "test_id": "Q3b/CAMERA", "significant": False, "conclusion": "chưa phân định", "status": "ok"}],
        "q4": [{"aspect": "CAMERA", "test_id": "Q4/CAMERA", "p_adjusted": 0.2, "significant": False,
                "conclusion": "Chưa đủ bằng chứng", "conclusion_allowed": False, "status": "ok"}],
        "q5": [{"defect_type": "BATTERY_DRAIN", "n_defect": 2, "priority": None, "priority_candidate": "P3",
                "trend": "not_testable", "test_id": "Q5/BATTERY_DRAIN", "status": "insufficient_data"}],
    }
    return {"analysis_id": f"x1|{VERSION}", "target_model": "x1", "model_version": VERSION,
            "loaded_at": "2026-11-11T00:00:00+00:00", "result": result}


COMMENTS = [
    {"comment_id": "k1", "video_id": "v1", "parent_id": None, "model": "x1", "is_spam": False,
     "is_vietnamese": True, "spam_reasons": [], "published_at": "2023-02-10T18:30:00Z"},   # 01:30 giờ VN
    {"comment_id": "k2", "video_id": "v1", "parent_id": "k1", "model": "x1", "is_spam": True,
     "is_vietnamese": True, "spam_reasons": ["contains_url"], "published_at": "2023-02-10T03:15:00Z"},
    {"comment_id": "k3", "video_id": "v2", "parent_id": None, "model": "r1|x1", "is_spam": True,
     "is_vietnamese": False, "spam_reasons": ["non_vietnamese_language"], "published_at": "2023-02-11T03:59:00Z"},
]


@pytest.fixture()
def db():
    """mongomock mặc định; MongoDB thật (database tạm, xóa sau test) khi có TEST_MONGO_URI."""
    uri = os.getenv("TEST_MONGO_URI")
    if uri:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        name = f"test_cv13_{uuid.uuid4().hex[:10]}"
        yield client[name]
        client.drop_database(name)
        client.close()
    else:
        import mongomock
        yield mongomock.MongoClient()["test_cv13"]


@pytest.fixture()
def seeded(db):
    db.models.insert_many([dict(m) for m in MODELS])
    db.aggregates.insert_many([dict(a) for a in AGGREGATES])
    db.aspect_mentions.insert_many([dict(m) for m in MENTIONS])
    db.comments.insert_many([dict(c) for c in COMMENTS])
    db.analysis_results.insert_one(analysis_document())
    return db


def client_for(db) -> TestClient:
    return TestClient(create_app(db=db, settings=SETTINGS))


def get(db, path, **params):
    response = client_for(db).get(f"/api/{path}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------- công thức

def test_summarize_uses_the_single_formula_and_keeps_neutral_out_of_the_denominator():
    result = summarize(45, 35, 7)
    assert result["n_total"] == 87 and result["n_opinionated"] == 80
    assert result["praise_pct"] == pytest.approx(56.25)
    assert result["criticism_pct"] == pytest.approx(43.75)
    assert result["net"] == pytest.approx(12.5)
    assert summarize(45, 35, 700)["praise_pct"] == pytest.approx(56.25)


def test_summarize_returns_none_not_zero_when_nobody_praised_or_criticised():
    result = summarize(0, 0, 12)
    assert result["praise_pct"] is None and result["criticism_pct"] is None and result["net"] is None
    assert result["low_data"] is True


def test_low_data_threshold_is_thirty_opinionated_mentions():
    assert summarize(20, 9, 100)["low_data"] is True
    assert summarize(20, 10, 0)["low_data"] is False


def test_counts_are_added_before_dividing():
    total = add_counts([{"n_pos": 75, "n_neg": 25, "n_neu": 0}, {"n_pos": 5, "n_neg": 5, "n_neu": 3}])
    assert total == {"n_pos": 80, "n_neg": 30, "n_neu": 3}
    # Trung bình hai tỷ lệ (75% và 50%) sẽ ra 62,5%: sai. Cộng tử và mẫu ra 72,7%.
    assert summarize(**total)["praise_pct"] == pytest.approx(100 * 80 / 110)
    assert same_counts(total, {"n_pos": 80, "n_neg": 30, "n_neu": 3, "extra": 1})
    assert not same_counts(total, {"n_pos": 80, "n_neg": 31, "n_neu": 3})


# ---------------------------------------------------------------- phạm vi, phiên bản

def test_meta_defaults_follow_latest_analysis_and_report_label_sources(seeded):
    meta = get(seeded, "meta")
    assert meta["defaults"] == {"model_version": VERSION, "model": "x1"}
    versions = {v["model_version"]: v for v in meta["versions"]}
    assert versions[VERSION]["label_sources"] == {"model": len(MENTIONS)}
    assert versions["other-v9"]["n_mentions_in_aggregates"] == 1000
    assert [t["model_id"] for t in meta["targets"]][0] == "x1"
    assert meta["aspects"] == ASPECTS and meta["min_opinionated"] == 30
    assert [t["model_id"] for t in get(seeded, "meta", model_version="other-v9")["targets"]] == ["x1"]


def test_scope_takes_predecessor_and_rivals_from_models_when_there_is_no_analysis(seeded):
    seeded.analysis_results.delete_many({})
    scope = get(seeded, "launch", model="x1", model_version=VERSION)["scope"]
    assert scope["predecessor"] == "p1" and scope["rivals"] == ["r1", "r2"]
    assert [m["role"] for m in scope["models"]] == ["X", "P", "R1", "R2"]
    assert scope["models"][0]["title"] == "Máy X" and scope["models"][0]["launch_date"] == "2023-02-02"


def test_unknown_model_or_version_is_a_404_with_a_reason(seeded):
    client = client_for(seeded)
    for params in ({"model": "khongco"}, {"model_version": "khongco"}):
        response = client.get("/api/launch", params=params)
        assert response.status_code == 404 and response.json()["error"] == "not_found"
    assert client.get("/api/khong-ton-tai").status_code == 404


# ---------------------------------------------------------------- Tab 1

def test_q1_counts_sum_over_videos_inside_the_window_only(seeded):
    data = get(seeded, "launch")
    overall = {row["model_id"]: row for row in data["q1"]["overall"]}
    # X: (30+10+5) khen, (10+10+15) chê, (5+0+2) trung tính. Dòng tuần 0 và phiên bản khác không tính.
    assert (overall["x1"]["n_pos"], overall["x1"]["n_neg"], overall["x1"]["n_neu"]) == (45, 35, 7)
    assert overall["x1"]["net"] == pytest.approx(12.5)
    assert overall["r2"]["low_data"] is True and overall["r1"]["low_data"] is False
    assert data["scope"]["n_mentions_outside_window"] == 99
    weekly = {(p["model_id"], p["week_since_launch"]): p for p in data["q1"]["weekly"]}
    assert len(weekly) == 4 * 4
    assert weekly[("x1", 1)]["n_pos"] == 40 and weekly[("x1", 2)]["n_neg"] == 15
    assert weekly[("x1", 3)]["net"] is None and weekly[("x1", 3)]["n_total"] == 0


def test_inference_from_cv12_is_attached_when_counts_match(seeded):
    data = get(seeded, "launch")
    assert data["data_status"]["analysis"]["usable"] is True
    assert data["data_status"]["analysis"]["mismatched_cells"] == 0
    x = data["q1"]["overall"][0]
    assert x["praise_ci95"] == [50.0, 60.0] and x["net_ci95"] == [1.0, 20.0]
    assert data["q1"]["tests"][0]["conclusion"] == "X kém hơn đời trước"
    battery = next(a for a in data["q2"]["aspects"] if a["aspect"] == "BATTERY")
    assert battery["test"]["conclusion"] == "Nhược điểm tương đối"


def test_stale_analysis_is_never_shown_next_to_newer_counts(seeded):
    # Mô hình chạy lại, aggregates đổi, nhưng kết quả kiểm định vẫn của lần chạy cũ.
    seeded.aggregates.update_one({"agg_id": AGGREGATES[0]["agg_id"]}, {"$set": {"n_pos": 31}})
    data = get(seeded, "launch")
    status = data["data_status"]
    assert status["analysis"]["available"] is True and status["analysis"]["usable"] is False
    assert status["analysis"]["mismatched_cells"] >= 1 and status["illustrative"] is True
    assert any("khác với DB" in reason for reason in status["reasons"])
    assert data["q1"]["overall"][0]["n_pos"] == 46            # số mô tả vẫn lấy từ DB
    assert data["q1"]["overall"][0]["net_ci95"] is None and data["q1"]["tests"] == []
    assert all(a["test"] is None for a in data["q2"]["aspects"])


def test_without_analysis_only_descriptive_numbers_are_returned(seeded):
    seeded.analysis_results.delete_many({})
    data = get(seeded, "launch", model="x1", model_version=VERSION)
    assert data["q1"]["overall"][0]["net"] == pytest.approx(12.5)
    assert data["q1"]["tests"] == [] and data["q1"]["overall"][0]["praise_ci95"] is None
    assert data["data_status"]["illustrative"] is True
    assert any("Chưa có kết quả kiểm định" in reason for reason in data["data_status"]["reasons"])


@pytest.mark.parametrize("source, reason", [("rule", "luật từ khóa"), ("llm", "AI gán")])
def test_rule_and_llm_labels_are_always_marked_illustrative(seeded, source, reason):
    seeded.aspect_mentions.update_many({}, {"$set": {"label_source": source}})
    for path in ("launch", "compare"):
        status = get(seeded, path)["data_status"]
        assert status["illustrative"] is True
        assert any(reason in text for text in status["reasons"])


def test_only_evaluated_labels_with_publishable_analysis_are_not_illustrative(seeded):
    status = get(seeded, "launch")["data_status"]
    assert status == {**status, "illustrative": False, "reasons": []}
    # Công việc 12 chưa cho phép công bố thì vẫn là minh họa, dù nhãn do mô hình gán.
    seeded.analysis_results.replace_one({}, analysis_document(can_publish=False))
    blocked = get(seeded, "launch")["data_status"]
    assert blocked["illustrative"] is True and "Chưa đánh giá độ chính xác của nhãn" in blocked["reasons"]
    seeded.analysis_results.replace_one({}, analysis_document(data_kind="fixture"))
    assert get(seeded, "launch")["data_status"]["illustrative"] is True


def test_missing_mentions_means_unknown_label_source_so_illustrative(seeded):
    seeded.aspect_mentions.delete_many({})
    status = get(seeded, "launch")["data_status"]
    assert status["illustrative"] is True and status["label_sources"] == {}


def test_q2_is_sorted_by_net_and_gap_uses_the_same_criticism_definition(seeded):
    q2 = get(seeded, "launch")["q2"]
    assert q2["overall"]["criticism_pct"] == pytest.approx(43.75)
    with_data = [a for a in q2["aspects"] if a["net"] is not None]
    assert [a["aspect"] for a in with_data] == ["CAMERA", "BATTERY"]
    battery = with_data[1]
    assert battery["criticism_pct"] == pytest.approx(75.0)
    assert battery["criticism_gap_vs_overall"] == pytest.approx(75.0 - 43.75)
    assert len(q2["aspects"]) == len(ASPECTS)
    assert all(a["net"] is None for a in q2["aspects"][2:])


def test_sample_comments_skip_creator_and_out_of_window_and_need_review(seeded):
    camera = next(a for a in get(seeded, "launch")["q2"]["aspects"] if a["aspect"] == "CAMERA")
    negatives = [s for s in camera["samples"] if s["sentiment"] == "neg"]
    # c4 (chủ kênh) và c5 (ngày 40) có confidence cao nhất nhưng không được lấy.
    assert [s["clause_text"] for s in negatives] == ["mệnh đề c1", "mệnh đề c2"]
    assert all(s["requires_human_review"] for s in camera["samples"])
    seeded.aspect_mentions.update_many({}, {"$set": {"label_source": "human", "confidence": None}})
    reviewed = next(a for a in get(seeded, "launch")["q2"]["aspects"] if a["aspect"] == "CAMERA")
    assert not any(s["requires_human_review"] for s in reviewed["samples"])


def test_q5_counts_only_owner_reported_defects_and_uses_all_mentions_as_denominator(seeded):
    q5 = get(seeded, "launch")["q5"]
    assert q5["n_owner_defect_mentions"] == 2 and q5["n_target_mentions"] == 87
    drain = q5["defects"][0]
    assert drain["defect_type"] == "BATTERY_DRAIN" and drain["n_defect"] == 2
    week2 = drain["weekly"][1]
    assert (week2["n_defect"], week2["n_denominator"]) == (2, 22)
    assert week2["defect_mention_pct"] == pytest.approx(100 * 2 / 22)
    assert drain["weekly"][2]["defect_mention_pct"] is None      # tuần 3 không có mention nào
    assert drain["priority"] is None and drain["priority_candidate"] == "P3"
    assert drain["count_differs_from_analysis"] is False
    overheat = next(d for d in q5["defects"] if d["defect_type"] == "OVERHEAT")
    assert overheat["n_defect"] == 0                              # mention của chủ kênh không tính


def test_alerts_are_read_from_the_collection_with_sample_text(seeded):
    assert get(seeded, "launch")["alerts"] == []
    seeded.alerts.insert_one({"alert_id": "a1", "created_at": "2023-02-12T00:00:00Z", "target_model": "x1",
                              "aspect": "BATTERY", "metric": "criticism_pct", "value": 75.0, "baseline": 25.0,
                              "threshold": 20.0, "severity": "high",
                              "sample_mention_ids": ["c6#0#BATTERY", "khong-co"]})
    alert = get(seeded, "launch")["alerts"][0]
    assert alert["aspect_name"] == "Pin & sạc" and alert["severity"] == "high"
    assert [s["clause_text"] for s in alert["samples"]] == ["mệnh đề c6"]


# ---------------------------------------------------------------- Tab 2

def test_q3a_matrix_has_every_aspect_and_model_with_counts_from_aggregates(seeded):
    matrix = {row["aspect"]: row for row in get(seeded, "compare")["q3a"]["matrix"]}
    assert list(matrix) == list(ASPECTS)
    camera = {cell["model_id"]: cell for cell in matrix["CAMERA"]["cells"]}
    assert camera["x1"]["praise_pct"] == pytest.approx(100 * 40 / 60)
    assert camera["x1"]["praise_ci95"] == [55.0, 75.0]
    assert camera["r1"]["praise_pct"] == pytest.approx(90.0) and camera["r2"]["low_data"] is True
    assert matrix["PRICE"]["cells"][0]["praise_pct"] is None


def test_q3b_flips_mentions_written_from_the_rival_side_and_ignores_outside_models(seeded):
    camera = next(row for row in get(seeded, "compare")["q3b"] if row["aspect"] == "CAMERA")
    assert (camera["n_x_win"], camera["n_x_loss"], camera["n_tie"]) == (1, 1, 1)
    assert camera["win_pct"] == pytest.approx(50.0) and camera["low_data"] is True
    assert camera["win_ci95"] == [10.0, 90.0] and camera["count_differs_from_analysis"] is False
    # Nếu Công việc 12 đếm ra số khác thì không ghép kiểm định của họ vào số của mình.
    document = analysis_document()
    document["result"]["q3b"][0]["n_x_win"] = 7
    seeded.analysis_results.replace_one({}, document)
    mismatched = next(row for row in get(seeded, "compare")["q3b"] if row["aspect"] == "CAMERA")
    assert mismatched["test"] is None and mismatched["count_differs_from_analysis"] is True


def test_q4_reports_change_in_criticism_from_predecessor_to_target(seeded):
    q4 = get(seeded, "compare")["q4"]
    rows = {row["aspect"]: row for row in q4["aspects"]}
    assert q4["predecessor"] == "p1"
    assert rows["CAMERA"]["predecessor"]["criticism_pct"] == pytest.approx(50.0)
    assert rows["CAMERA"]["current"]["criticism_pct"] == pytest.approx(100 * 20 / 60)
    assert rows["CAMERA"]["criticism_change"] == pytest.approx(100 * 20 / 60 - 50.0)
    assert rows["CAMERA"]["test"]["conclusion"] == "Chưa đủ bằng chứng"
    assert rows["PRICE"]["criticism_change"] is None


def test_q4_is_empty_when_no_predecessor_is_known(seeded):
    seeded.analysis_results.delete_many({})
    seeded.models.update_one({"model_id": "x1"}, {"$set": {"predecessor_id": None}})
    data = get(seeded, "compare", model="x1", model_version=VERSION)
    assert data["scope"]["predecessor"] is None and data["q4"]["aspects"] == []
    assert [m["role"] for m in data["scope"]["models"]] == ["X", "R1", "R2"]


# ---------------------------------------------------------------- Tab 3, 4, trạng thái trống

def test_system_reports_real_counts_and_does_not_invent_streaming_metrics(seeded):
    client = client_for(seeded)
    client.get("/api/meta")
    system = client.get("/api/system").json()
    assert system["collections"]["comments"] == 3 and system["collections"]["aggregates"] == len(AGGREGATES)
    assert system["comments"]["spam"] == 2 and system["comments"]["not_vietnamese"] == 1
    assert system["comments"]["usable"] == 1
    assert system["comments"]["spam_reasons"] == {"contains_url": 1, "non_vietnamese_language": 1}
    assert system["streaming"]["deployed"] is False
    assert not any(key in system["streaming"] for key in ("throughput", "consumer_lag", "latency"))
    assert system["api"]["n_requests_measured"] == 1 and system["api"]["latency_ms_p50"] >= 0


def test_overview_uses_vietnam_time_and_groups_multi_model_videos_separately(seeded):
    overview = get(seeded, "overview")
    assert overview["totals"]["total"] == 3 and overview["totals"]["replies"] == 1
    assert overview["totals"]["n_videos"] == 2
    hours = overview["by_hour"]
    assert len(hours) == 24 and sum(hours) == 3
    assert hours[1] == 1 and hours[10] == 2                       # 18:30Z -> 01:30; 03:15Z và 03:59Z -> 10h
    brands = {row["brand"]: row["n_comments"] for row in overview["by_brand"]}
    assert brands == {"Samsung": 2, "Video nhiều máy": 1}


def test_empty_database_gives_empty_states_not_errors(db):
    client = client_for(db)
    assert client.get("/api/health").json()["status"] == "ok"
    meta = client.get("/api/meta").json()
    assert meta["defaults"] == {"model_version": None, "model": None} and meta["versions"] == []
    assert client.get("/api/launch").status_code == 404
    assert client.get("/api/system").json()["comments"].get("total", 0) == 0
    assert client.get("/api/overview").json()["by_hour"] == [0] * 24


def test_database_outage_is_reported_as_503():
    class Broken:
        name = "down"

        def __getattr__(self, _name):
            raise ServerSelectionTimeoutError("no server")

        __getitem__ = __getattr__

    response = TestClient(create_app(db=Broken(), settings=SETTINGS)).get("/api/meta")
    assert response.status_code == 503 and response.json()["error"] == "database_unavailable"


def test_dashboard_page_is_served_and_embeds_no_data(seeded):
    client = client_for(seeded)
    page = client.get("/")
    assert page.status_code == 200 and "app.js" in page.text
    script = client.get("/app.js").text
    assert "fetch(`/api/" in script
    for static_source in ("executive_report_data", "dashboard_exec_data", "eda_smartphone_outputs"):
        assert static_source not in page.text and static_source not in script
    assert client.get("/api/launch").headers["cache-control"] == "no-store"


# ---------------------------------------------------------------- script nạp DB

def test_catalog_flattens_pipeline_yaml_into_one_entry_per_model():
    catalog = {m["model_id"]: m for m in load_db.catalog_from_config(REPO_ROOT / "config" / "pipeline.yaml")}
    s23u = catalog["s23u"]
    assert s23u["title"] == "Samsung Galaxy S23 Ultra" and s23u["brand"] == "Samsung"
    assert s23u["launch_date"] == "2023-02-02" and "ip14prm" in s23u["rivals"]
    assert all(isinstance(rival, str) and rival in catalog for m in catalog.values() for rival in m["rivals"])
    assert all(m["launch_date"] for m in catalog.values())
    assert catalog["ip14prm"]["brand"] == "Apple"


def write_jsonl(path: Path, rows) -> Path:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return path


def test_loading_aggregates_twice_does_not_double_count_and_drops_stale_rows(db, tmp_path):
    rows = [{k: v for k, v in row.items() if k != "agg_id"} for row in AGGREGATES[:3]]
    path = write_jsonl(tmp_path / "aggregates.jsonl", rows)
    load_db.load_aggregates(db, path)
    load_db.load_aggregates(db, path)
    assert db.aggregates.count_documents({}) == 3
    assert sum(doc["n_pos"] for doc in db.aggregates.find()) == 45
    # Lần chạy mô hình sau không còn dòng BATTERY: dòng cũ phải biến mất, phiên bản khác giữ nguyên.
    db.aggregates.insert_one(dict(AGGREGATES[-1]))
    load_db.load_aggregates(db, write_jsonl(path, rows[:2]))
    assert db.aggregates.count_documents({"model_version": VERSION}) == 2
    assert db.aggregates.count_documents({"model_version": "other-v9"}) == 1


@pytest.mark.parametrize("change, message", [
    ({"n_pos": -1}, "số nguyên không âm"), ({"n_neg": 2.5}, "số nguyên không âm"),
    ({"praise_pct": 75.0}, "tỷ lệ"), ({"video_id": None}, "thiếu trường khóa"),
])
def test_aggregates_must_be_integer_counts_without_percentages(db, tmp_path, change, message):
    row = {**{k: v for k, v in AGGREGATES[0].items() if k != "agg_id"}, **change}
    with pytest.raises(ValueError, match=message):
        load_db.load_aggregates(db, write_jsonl(tmp_path / "bad.jsonl", [row]))
    assert db.aggregates.count_documents({}) == 0


def test_mentions_are_validated_against_the_contract_before_anything_is_written(db, tmp_path):
    schema = REPO_ROOT / "contracts" / "aspect-mention.schema.json"
    good = [dict(m) for m in MENTIONS[:3]]
    message = load_db.load_mentions(db, write_jsonl(tmp_path / "mentions.jsonl", good), schema)
    assert "3 mention" in message and db.aspect_mentions.count_documents({}) == 3
    bad = dict(MENTIONS[0], sentiment="positive")
    with pytest.raises(ValueError, match="sai contract"):
        load_db.load_mentions(db, write_jsonl(tmp_path / "bad.jsonl", [dict(MENTIONS[1]), bad]), schema)
    assert db.aspect_mentions.count_documents({}) == 3


def test_analysis_is_stored_once_per_target_and_version(db, tmp_path):
    result = analysis_document()["result"]
    path = tmp_path / "business_questions.json"
    path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    load_db.load_analysis(db, path)
    load_db.load_analysis(db, path)
    assert db.analysis_results.count_documents({}) == 1
    stored = db.analysis_results.find_one()
    assert stored["analysis_id"] == f"x1|{VERSION}" and stored["result"]["config"]["target_model"] == "x1"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu config"):
        load_db.load_analysis(db, path)


def test_loaded_files_can_be_served_end_to_end(db, tmp_path):
    """File -> load_db -> MongoDB -> API: đúng đường đi của dữ liệu thật."""
    db.models.insert_many([dict(m) for m in MODELS])
    load_db.load_aggregates(db, write_jsonl(tmp_path / "a.jsonl",
                                            [{k: v for k, v in row.items() if k != "agg_id"} for row in AGGREGATES]))
    load_db.load_mentions(db, write_jsonl(tmp_path / "m.jsonl", [dict(m) for m in MENTIONS]),
                          REPO_ROOT / "contracts" / "aspect-mention.schema.json")
    (tmp_path / "q.json").write_text(json.dumps(analysis_document()["result"], ensure_ascii=False), "utf-8")
    load_db.load_analysis(db, tmp_path / "q.json")
    data = get(db, "launch")
    assert data["scope"]["target"] == "x1" and data["data_status"]["analysis"]["usable"] is True
    assert data["q1"]["overall"][0]["net"] == pytest.approx(12.5)


# ---------------------------------------------------------------- số liệu minh họa

@pytest.mark.parametrize("text, expected", [
    ("pin trâu dùng thích", "pos"), ("máy lag quá", "neg"), ("không lag chút nào", "pos"),
    ("camera không đẹp", "neg"), ("giá bao nhiêu vậy", "neu"),
])
def test_demo_sentiment_handles_negation(text, expected):
    assert demo_data.sentiment_of(text) == expected


def demo_comment(comment_id, text, published_at="2023-02-10T03:15:00Z", model="s23u", **extra):
    return {"comment_id": comment_id, "video_id": "vid", "parent_id": None, "model": model, "source": "youtube",
            "author_hash": "b" * 64, "published_at": published_at, "is_spam": False, "is_vietnamese": True,
            "clauses": [{"clause_id": 1, "text": text}], **extra}


CATALOG = [{"model_id": "s23u", "title": "Samsung Galaxy S23 Ultra", "launch_date": "2023-02-02",
            "aliases": ["S23 Ultra"]},
           {"model_id": "ip14prm", "title": "iPhone 14 Pro Max", "launch_date": "2022-09-16",
            "aliases": ["14 pro max"]}]


def test_demo_mentions_follow_the_contract_and_are_labelled_as_rule_output():
    comments = [
        demo_comment("c1", "mình đang dùng pin tụt nhanh quá"),
        demo_comment("c2", "camera đẹp hơn iphone 14 pro max"),
        demo_comment("c3", "pin ổn", model="s23u|ip14prm"),
        demo_comment("c4", "pin tệ", is_spam=True),
        demo_comment("c5", "hello"),
    ]
    mentions = list(demo_data.build_mentions(comments, CATALOG))
    validator = Draft7Validator(json.loads(
        (REPO_ROOT / "contracts" / "aspect-mention.schema.json").read_text(encoding="utf-8")))
    for item in mentions:
        assert not list(validator.iter_errors(item)), item
        assert item["label_source"] == "rule" and item["model_version"] == demo_data.MODEL_VERSION
    by_id = {m["mention_id"]: m for m in mentions}
    assert set(by_id) == {"c1#0#BATTERY", "c2#0#CAMERA", "c2#0#DESIGN", "c3#0#BATTERY"}
    drain = by_id["c1#0#BATTERY"]
    assert (drain["sentiment"], drain["is_owner"], drain["defect_type"]) == ("neg", True, "BATTERY_DRAIN")
    assert drain["days_since_launch"] == 8
    duel = by_id["c2#0#CAMERA"]
    assert (duel["compare_with"], duel["compare_winner"]) == ("ip14prm", "target")
    multi = by_id["c3#0#BATTERY"]
    assert multi["target_model"] is None and multi["days_since_launch"] is None


def test_days_since_launch_uses_the_vietnam_calendar_day():
    from datetime import date
    launch = date(2023, 2, 2)
    assert demo_data.days_since_launch("2023-02-01T17:30:00Z", launch) == 0     # 00:30 ngày 2/2 giờ VN
    assert demo_data.days_since_launch("2023-02-01T16:59:00Z", launch) == -1    # 23:59 ngày 1/2 giờ VN


def test_demo_aggregates_keep_only_the_first_four_weeks_and_store_counts():
    def row(mention_id, sentiment, days, creator=False, target="s23u"):
        return {"target_model": target, "aspect": "BATTERY", "sentiment": sentiment, "days_since_launch": days,
                "author_is_creator": creator, "video_id": "vid", "source": "youtube",
                "model_version": demo_data.MODEL_VERSION, "mention_id": mention_id}
    rows = demo_data.build_aggregates([
        row("a", "pos", 0), row("b", "neg", 6), row("c", "neu", 7), row("d", "pos", 27),
        row("e", "pos", 28), row("f", "pos", -1), row("g", "pos", 3, creator=True),
        {**row("h", "pos", None, target=None)},
    ], "2026-11-17T00:00:00+00:00")
    weeks = {r["week_since_launch"]: (r["n_pos"], r["n_neg"], r["n_neu"]) for r in rows}
    assert weeks == {1: (1, 1, 0), 2: (0, 0, 1), 4: (1, 0, 0)}
    assert all(r["agg_id"] == load_db.aggregate_id(r) and r["n_total"] == sum(weeks[r["week_since_launch"]])
               for r in rows)
    assert not any("pct" in key for r in rows for key in r)


# ---------------------------------------------------------------- sau lượt review độc lập

SCHEMA = REPO_ROOT / "contracts" / "aspect-mention.schema.json"


def test_mentions_of_another_label_version_are_never_partly_overwritten(db, tmp_path):
    old = [dict(m) for m in MENTIONS]                                   # phiên bản model-v1
    load_db.load_mentions(db, write_jsonl(tmp_path / "old.jsonl", old), SCHEMA)
    new = [dict(m, model_version="model-v2") for m in MENTIONS[:5]]     # cùng mention_id, phiên bản mới
    path = write_jsonl(tmp_path / "new.jsonl", new)

    with pytest.raises(ValueError, match="ghi đè mention của phiên bản nhãn khác"):
        load_db.load_mentions(db, path, SCHEMA)
    assert db.aspect_mentions.count_documents({"model_version": VERSION}) == len(MENTIONS)
    assert db.aspect_mentions.count_documents({"model_version": "model-v2"}) == 0

    message = load_db.load_mentions(db, path, SCHEMA, replace_other_versions=True)
    assert "đã xóa toàn bộ mention của phiên bản bị thay" in message
    # Không còn trạng thái lưng chừng: phiên bản cũ biến mất hẳn, phiên bản mới đủ 5 mention.
    assert db.aspect_mentions.count_documents({"model_version": VERSION}) == 0
    assert db.aspect_mentions.count_documents({"model_version": "model-v2"}) == 5


def test_loading_a_file_for_some_models_keeps_other_models_of_the_same_version(db, tmp_path):
    strip = lambda rows: [{k: v for k, v in row.items() if k != "agg_id"} for row in rows]
    everything = [row for row in AGGREGATES if row["model_version"] == VERSION]
    load_db.load_aggregates(db, write_jsonl(tmp_path / "all.jsonl", strip(everything)))
    # File sau chỉ có máy X và không còn dòng BATTERY của X.
    only_x = [row for row in everything if row["target_model"] == "x1" and row["aspect"] == "CAMERA"]
    message = load_db.load_aggregates(db, write_jsonl(tmp_path / "x.jsonl", strip(only_x)))
    assert "xóa 1 dòng cũ" in message
    assert db.aggregates.count_documents({"target_model": "x1"}) == len(only_x)
    for other in ("p1", "r1", "r2"):
        assert db.aggregates.count_documents({"target_model": other}) == \
            sum(row["target_model"] == other for row in everything)


def test_prune_leaves_documents_it_did_not_write(db, tmp_path):
    db.aggregates.insert_one({"model_version": VERSION, "target_model": "x1", "note": "không có agg_id"})
    rows = [{k: v for k, v in AGGREGATES[0].items() if k != "agg_id"}]
    load_db.load_aggregates(db, write_jsonl(tmp_path / "a.jsonl", rows))
    assert db.aggregates.count_documents({"note": "không có agg_id"}) == 1


@pytest.mark.parametrize("change, message", [
    ({"week_since_launch": "1"}, "week_since_launch"), ({"week_since_launch": 1.0}, "week_since_launch"),
    ({"target_model": 5}, "target_model"), ({"aspect": ""}, "aspect"),
])
def test_aggregate_key_fields_are_type_checked(db, tmp_path, change, message):
    row = {**{k: v for k, v in AGGREGATES[0].items() if k != "agg_id"}, **change}
    with pytest.raises(ValueError, match=message):
        load_db.load_aggregates(db, write_jsonl(tmp_path / "bad.jsonl", [row]))


def test_catalog_accepts_a_rival_written_as_a_bare_name(tmp_path):
    config = tmp_path / "pipeline.yaml"
    config.write_text(
        "models:\n"
        "  - name: a1\n    title: Samsung Galaxy A1\n    launch_date: '2024-01-01'\n"
        "    rivals:\n      - b1\n      - name: c1\n        title: Xiaomi C1\n"
        "  - name: b1\n    title: iPhone B1\n    launch_date: '2024-02-02'\n", encoding="utf-8")
    catalog = {m["model_id"]: m for m in load_db.catalog_from_config(config)}
    assert catalog["a1"]["rivals"] == ["b1", "c1"]
    assert catalog["b1"]["launch_date"] == "2024-02-02" and catalog["b1"]["brand"] == "Apple"
    assert catalog["c1"]["launch_date"] == "2024-01-01"      # đối thủ không ghi ngày: lấy ngày của mẫu chính


def test_defaults_ignore_an_analysis_that_has_no_counts_in_the_database(seeded):
    document = analysis_document()
    document.update(analysis_id="x1|khong-co", model_version="khong-co", loaded_at="2030-01-01T00:00:00+00:00")
    seeded.analysis_results.insert_one(document)
    meta = get(seeded, "meta")
    assert meta["defaults"]["model_version"] in {v["model_version"] for v in meta["versions"]}
    assert meta["targets"], "trang mở ra phải có máy để chọn"
    assert client_for(seeded).get("/api/launch").status_code == 200


def test_verified_labels_without_any_significant_result_are_real_not_illustrative(seeded):
    # Công việc 12: can_publish = false khi không phép kiểm định nào có ý nghĩa, dù nhãn đã kiểm chứng.
    document = analysis_document()
    document["result"]["can_publish_business_conclusions"] = False
    document["result"]["publication_blockers"] = []
    seeded.analysis_results.replace_one({}, document)
    status = get(seeded, "launch")["data_status"]
    assert status["illustrative"] is False and status["reasons"] == []


def test_illustrative_always_comes_with_a_reason(seeded):
    for mutate in (lambda: seeded.analysis_results.delete_many({}),
                   lambda: seeded.aspect_mentions.update_many({}, {"$set": {"label_source": "rule"}}),
                   lambda: seeded.aspect_mentions.delete_many({})):
        mutate()
        status = get(seeded, "launch", model="x1", model_version=VERSION)["data_status"]
        assert status["illustrative"] is True and status["reasons"]


def test_mention_without_label_source_is_counted_as_unknown_and_flagged(seeded):
    seeded.aspect_mentions.update_one({"mention_id": MENTIONS[0]["mention_id"]},
                                      {"$unset": {"label_source": ""}})
    versions = {v["model_version"]: v for v in get(seeded, "meta")["versions"]}
    assert versions[VERSION]["label_sources"]["unknown"] == 1
    status = get(seeded, "launch")["data_status"]
    assert status["illustrative"] is True and "Có mention không ghi nguồn nhãn" in status["reasons"]


def test_incomplete_aggregate_rows_do_not_break_the_api(seeded):
    seeded.aggregates.insert_one({"agg_id": "thieu", "target_model": "x1", "aspect": "CAMERA",
                                  "week_since_launch": 9, "video_id": "v1", "source": "youtube",
                                  "model_version": VERSION, "n_pos": 3})
    data = get(seeded, "launch")
    assert data["scope"]["n_mentions_outside_window"] == 99 + 3
    assert get(seeded, "compare")["scope"]["target"] == "x1"


def test_database_error_message_does_not_leak_the_connection_string():
    class Broken:
        name = "down"

        def __getattr__(self, _name):
            raise ServerSelectionTimeoutError("no server")

        __getitem__ = __getattr__

    secret = Settings(mongo_uri="mongodb://admin:S3cret@db.internal:27017", cache_seconds=0)
    body = TestClient(create_app(db=Broken(), settings=secret)).get("/api/meta").text
    assert "S3cret" not in body and "admin" not in body and "db.internal" not in body


def test_empty_comments_collection_still_has_every_total(db):
    totals = get(db, "overview")["totals"]
    assert totals["total"] == 0 and totals["replies"] == 0 and totals["n_videos"] == 0


def test_frontend_never_inserts_non_numeric_values_as_numbers():
    script = (REPO_ROOT / "src" / "serving" / "dashboard" / "app.js").read_text(encoding="utf-8")
    assert "const isNumber = (value) => typeof value === \"number\"" in script
    for helper in ("fmtInt", "fmtNum", "fmtPct", "fmtSigned"):
        definition = script[script.index(f"const {helper} ="):].split(";")[0]
        assert "isNumber(value)" in definition, helper

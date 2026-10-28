# -*- coding: utf-8 -*-
"""
Unit tests for Dashboard API (CV 13 - Nguyễn Lê Quân).
Tests all 4 Tab endpoints, query parameter handling, and live spam API.
"""
import os
import sys
import json
import pytest
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "serving", "api"))
from server import DashboardApiHandler, GLOBAL_DATA, GLOBAL_SPAM


class MockServer(DashboardApiHandler):
    def __init__(self, path: str, command: str = "GET", body: bytes = b""):
        self.path = path
        self.command = command
        self.request_version = "HTTP/1.1"
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.status = None
        self.sent_headers = {}

    def send_response(self, code, message=None):
        self.status = code

    def send_header(self, keyword, value):
        self.sent_headers[keyword] = value

    def end_headers(self):
        pass


def test_api_health_endpoint():
    handler = MockServer("/api/health")
    handler.do_GET()
    assert handler.status == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert res["status"] == "healthy"
    assert res["author"] == "Nguyễn Lê Quân"
    assert res["server_type"] == "ThreadingHTTPServer"


def test_api_launch_tracker_tab1_with_query_params():
    handler = MockServer("/api/launch-tracker?model=iPhone+15+Pro+Max&compare_to=iPhone+14+Pro+Max")
    handler.do_GET()
    assert handler.status == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert res["model_x"] == "iPhone 15 Pro Max"
    assert res["predecessor"] == "iPhone 14 Pro Max"
    assert "weekly_net_sentiment" in res
    assert "alerts" in res
    assert len(res["alerts"]) > 0
    assert "top_comments" in res["alerts"][0]


def test_api_comparison_tab2_with_brand_filter():
    handler = MockServer("/api/comparison?brand=Samsung")
    handler.do_GET()
    assert handler.status == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "praise_matrix" in res
    assert "head_to_head" in res
    assert "owner_defects" in res


def test_api_system_health_tab3():
    handler = MockServer("/api/system-health")
    handler.do_GET()
    assert handler.status == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "throughput_msg_per_sec" in res
    assert "kafka_consumer_lag" in res
    assert "spam_filtering" in res
    assert res["spam_filtering"]["spam_ratio_pct"] > 0
    assert "hybrid_approach" in res["spam_filtering"]


def test_api_overview_tab4():
    handler = MockServer("/api/overview")
    handler.do_GET()
    assert handler.status == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "raw_rows" in res
    assert res["raw_rows"] == 109344
    assert "brand_counts" in res
    assert "bigrams" in res


def test_api_live_spam_check_get_and_post():
    # 1. Test GET query
    handler_get = MockServer("/api/spam-check?text=Vao+link+nhan+thuong+http://bit.ly/qua")
    handler_get.do_GET()
    assert handler_get.status == 200
    res_get = json.loads(handler_get.wfile.getvalue().decode("utf-8"))
    assert res_get["is_spam"] is True

    # 2. Test POST json body
    post_body = json.dumps({"text": "Máy dùng rất ngon, màn hình 120Hz mượt mà"}).encode("utf-8")
    handler_post = MockServer("/api/spam-check", command="POST", body=post_body)
    handler_post.do_POST()
    assert handler_post.status == 200
    res_post = json.loads(handler_post.wfile.getvalue().decode("utf-8"))
    assert res_post["is_spam"] is False
    assert res_post["is_vietnamese"] is True

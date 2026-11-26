"""Mục đích: API chỉ đọc cho dashboard 4 tab và máy chủ phục vụ trang dashboard, đọc MongoDB đã nạp bằng `python -m src.run --den nap_db` (docs/7-hien-thi/huong-dan.md); cập nhật lần cuối: 2026-11-26.

Chạy (từ thư mục gốc repo):
  python -m src.serving.api.app --port 8000
rồi mở http://localhost:8000/

Biến môi trường: MONGO_URI (mặc định mongodb://localhost:27017), MONGO_DB
(mặc định smartphone_analytics).
"""
import collections
import time
from typing import Deque, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .settings import DASHBOARD_DIR, Settings
from .store import DashboardStore, NotFound


def _percentile(values, fraction: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))]


def create_app(db=None, settings: Optional[Settings] = None) -> FastAPI:
    """Tạo ứng dụng. `db` chỉ truyền vào khi kiểm thử; bình thường kết nối theo cấu hình."""
    settings = settings or Settings.from_env()
    if db is None:
        client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
        db = client[settings.mongo_db]
    store = DashboardStore(db, settings)
    started = time.time()
    durations: Deque[float] = collections.deque(maxlen=500)

    app = FastAPI(title="Dashboard bình luận sau ra mắt điện thoại", version="1.0.0",
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    app.state.store = store

    @app.middleware("http")
    async def measure(request: Request, call_next):
        begin = time.perf_counter()
        response = await call_next(request)
        if request.url.path.startswith("/api/") and request.url.path != "/api/system":
            durations.append((time.perf_counter() - begin) * 1000)
        # Số liệu thay đổi theo DB: không cho trình duyệt giữ bản cũ.
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(NotFound)
    async def not_found(_request: Request, error: NotFound):
        return JSONResponse(status_code=404, content={"error": "not_found", "detail": str(error)})

    @app.exception_handler(PyMongoError)
    async def database_down(_request: Request, error: PyMongoError):
        return JSONResponse(status_code=503, content={
            "error": "database_unavailable",
            # Không trả lại MONGO_URI: chuỗi kết nối có thể chứa mật khẩu.
            "detail": f"Không đọc được MongoDB (database '{settings.mongo_db}'): {type(error).__name__}"})

    @app.get("/api/health")
    def health():
        return store.health()

    @app.get("/api/meta")
    def meta(model_version: Optional[str] = Query(None, description="liệt kê máy có dữ liệu ở phiên bản này")):
        return store.meta(model_version)

    @app.get("/api/launch")
    def launch(model: Optional[str] = Query(None, description="mã máy X, vd s23u"),
               model_version: Optional[str] = Query(None, description="phiên bản nhãn, vd rule-v1.1")):
        return store.launch(model, model_version)

    @app.get("/api/compare")
    def compare(model: Optional[str] = Query(None), model_version: Optional[str] = Query(None)):
        return store.compare(model, model_version)

    @app.get("/api/system")
    def system():
        return store.system({
            "uptime_seconds": round(time.time() - started, 1), "n_requests_measured": len(durations),
            "latency_ms_p50": _percentile(durations, 0.50), "latency_ms_p95": _percentile(durations, 0.95),
        })

    @app.get("/api/overview")
    def overview():
        return store.overview()

    @app.get("/api/{rest:path}", include_in_schema=False)
    def unknown_endpoint(rest: str):
        return JSONResponse(status_code=404, content={"error": "not_found", "detail": f"/api/{rest}"})

    if DASHBOARD_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
    return app


def main() -> None:
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Chạy API và dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()

# Bản đồ code: file nào để làm gì

> Mục đích: Giải thích từng thư mục và file code để làm gì, ai dùng, khi nào phải sửa; cập nhật lần cuối: 2026-11-11.

**Đọc theo thứ tự này:** mục 1 để thấy dữ liệu đi qua những file nào; mục 2 để tra một file cụ thể; mục 3 khi cần sửa một thứ mà không biết sửa ở đâu.

Tài liệu (docs) đã có bảng riêng ở [README mục 4](../../README.md#4-bản-đồ-tài-liệu); file này chỉ nói về **code và dữ liệu**. Code đang nằm trên các nhánh chưa merge xem ở [sổ tay](../ke-hoach/so-tay.md).

## 1. Dữ liệu đi qua những file nào

| Bước | Làm gì | File code | Đầu ra |
|---|---|---|---|
| 1. Thu thập | Tìm video trên các kênh trong config, cào bình luận qua YouTube API | `src/ingest/crawler/` | `src/ingest/data/raw/comments.jsonl` (bản v4), `videos.jsonl`, `state.db` |
| 2. Tiền xử lý | Chuẩn hóa chữ, gắn cờ spam / tiếng Việt, tách mệnh đề | chưa có (Công việc 6; bản cũ đã gỡ ngày 11/11) | `clean_data.jsonl` |
| 3. Mô hình | Gán khía cạnh, cảm xúc, máy được nhắc cho từng mệnh đề | chưa có trên `main` (Công việc 8–11) | `aspect_mentions` |
| 4. Tổng hợp, Q1–Q5 | Đếm khen/chê, khoảng tin cậy, kiểm định | chưa có trên `main` (Công việc 12) | `aggregates`, kết quả Q1–Q5 |
| 5. Hiển thị | Dashboard | chưa có trên `main` (Công việc 13) | trang web |

Hiện repo chỉ có code cho bước 1; các bước sau là kế hoạch ở [roadmap](../ke-hoach/roadmap.md).

Ba thứ **không phải code** nhưng code đọc trực tiếp, nên sửa chúng là đổi hành vi của code:

| File | Chứa gì | Ai đọc |
|---|---|---|
| `config/pipeline.yaml` | Danh mục máy (mã, tên gọi, `launch_date`, đối thủ), danh sách kênh, cửa sổ thời gian, hạn mức API | Crawler |
| `contracts/*.schema.json` | Định dạng bắt buộc của một bình luận raw và một mention | Crawler (`crawler/schema.py` phải khớp), các nhóm ghi/đọc dữ liệu |
| `src/ingest/.env` (tự tạo từ `.env.example`, không commit) | API key YouTube, salt băm tác giả, địa chỉ Kafka, tên máy crawl (`CRAWLER_WORKER`) | Crawler |

## 2. Từng thư mục

### `src/ingest/`: crawler YouTube

Chạy từ `src/ingest/` bằng `python -m crawler.main <lệnh>`. Hướng dẫn chạy: [src/ingest/README.md](../../src/ingest/README.md). Luật crawler phải theo: [docs/spec/thu-thap.md](../spec/thu-thap.md).

| File | Để làm gì |
|---|---|
| `crawler/main.py` | Cửa vào: nhận lệnh `discover` (tìm video), `crawl` (cào bình luận), `run` (chạy liên tục theo lịch), `status` (đếm video, hạn mức), `models` (in cửa sổ thời gian từng máy), `snapshot-videos` (cập nhật lượt xem, like), `replay`, `dedupe`, `relabel`, `repair-missing`, các lệnh `*-authors`, `worker-init`, `resolve-names`, `find-channels` |
| `crawler/discover.py` | Quét danh sách video đã đăng của từng kênh trong config (không dùng tìm kiếm YouTube), giữ video có tiêu đề chứa tên gọi của máy và đăng trong khoảng ngày cho phép |
| `crawler/models.py` | Đọc danh mục máy từ config: tên gọi, `launch_date`, cửa sổ thời gian của từng máy, phân loại tiêu đề video thuộc máy nào |
| `crawler/crawl.py` | Cào bình luận của từng video, dừng/tiếp tục được bất cứ lúc nào (nhớ trang đang dở), chỉ giữ bình luận trong cửa sổ, băm tác giả thành `author_hash` |
| `crawler/youtube.py` | Gọi YouTube Data API (kênh, video, bình luận, reply, tìm kênh), xử lý lỗi và thử lại |
| `crawler/quota.py` | Đếm đơn vị hạn mức API trước mỗi lần gọi, dừng khi gần hết hạn mức ngày |
| `crawler/store.py` | Tạo cơ sở dữ liệu trạng thái `data/state.db`: kênh, mọi video của kênh (`uploads`), video được chọn và trạng thái crawl (`videos`), bình luận đã thấy, tài khoản người bình luận, hạn mức đã dùng |
| `crawler/sinks.py` | Ghi bình luận ra file JSONL (và Kafka nếu bật) |
| `crawler/schema.py` | Danh sách trường của một bình luận, một video và `SCHEMA_VERSION` mà crawler ghi ra |
| `crawler/config.py` | Đọc `config/pipeline.yaml` và `.env`, chỉ đường dẫn `data/` |
| `crawler/lock.py` | Không cho hai crawler cùng ghi một lúc |
| `crawler/timeutil.py` | Đọc/ghi thời gian, bỏ dấu tiếng Việt khi so tiêu đề |
| `crawler/authors.py` | Lấy 6 trường `author_*` (schema v3) cho bình luận: tra ngược kênh người viết, rồi ngày tạo kênh, số video, số người đăng ký |
| `crawler/replay.py` | Phát lại bình luận đã lưu vào Kafka theo đúng thứ tự thời gian (phần streaming, tùy chọn) |
| `crawler/dedupe.py`, `crawler/relabel.py` | Dọn dữ liệu đã cào: bỏ bình luận trùng; đổi nhãn máy của dữ liệu cũ |
| `crawler/repair_labels.py`, `crawler/repair_missing.py` | Sửa dữ liệu cũ sau khi đổi config: gắn lại nhãn máy cho video theo config hiện tại; cào lại bình luận bị "mồ côi" (đã đánh dấu là đã thấy nhưng không có trong file) |
| `crawler/__init__.py` | Chỉ để Python coi `crawler/` là một gói |
| `check_data.py` | Kiểm tra nhanh dữ liệu vừa cào: dòng hỏng, trùng, sai schema, ngoài cửa sổ, phân bố theo máy |
| `docker-compose.dev.yml` | Dựng Kafka trên máy để thử phần streaming (tùy chọn) |
| `requirements.txt` | Thư viện cần cài để chạy crawler |

Tiêu đề video, kênh và trạng thái crawl nằm trong `src/ingest/data/raw/videos.jsonl` và `state.db`, không có trong `comments.jsonl`.

### `tests/`

Chưa có test nào. Kế hoạch: [tests/README.md](../../tests/README.md). Kiểm tra dữ liệu crawl hiện dùng `src/ingest/check_data.py`.

### Thư mục không vào git (`.gitignore`)

| Thư mục / file | Chứa gì | Xóa được không |
|---|---|---|
| `.venv/` | Môi trường Python | Được; tạo lại theo [cai-dat.md](cai-dat.md) |
| `src/ingest/data/` | Dữ liệu raw bản v4 (`raw/comments.jsonl`, `raw/videos.jsonl`), `state.db` của crawler (có cả tên thật người bình luận), `models.json` | **Không**: đây là bản dữ liệu duy nhất trên máy; nếu xóa phải xin lại |
| `src/ingest/.env` | API key YouTube và `AUTHOR_SALT` của nhóm | **Không**, và không gửi cho ai ngoài nhóm: mất salt thì `author_hash` của lần crawl sau không khớp dữ liệu cũ |
| `data/` | Dữ liệu cũ v1.0 (`comments.jsonl`, 109.344 dòng); không còn code nào đọc | Hỏi trưởng nhóm trước |
| `__pycache__/` | File Python tự sinh | Được, tự sinh lại |

## 3. Muốn làm việc này thì sửa ở đâu

| Muốn | Sửa ở | Rồi |
|---|---|---|
| Thêm cách gọi tên một máy ("táo", "s26u") | `aliases` của máy đó trong `config/pipeline.yaml` | Crawler dùng danh sách này để chọn video; chạy lại `discover` |
| Sửa `launch_date`, thêm máy, thêm đối thủ | `config/pipeline.yaml` (Công việc 2) | Dữ liệu đã crawl theo ngày cũ không tự đổi; xem `crawler/repair_labels.py` |
| Thêm kênh để crawl | Mục `channels` trong `config/pipeline.yaml` | Chạy `discover` rồi `crawl` |
| Kiểm tra một video đã crawl chưa | Tìm `video_id` trong `src/ingest/data/raw/videos.jsonl` | Không có thì đối chiếu 3 điều kiện chọn video ở [thu-thap.md mục 2](../spec/thu-thap.md#2-chọn-video) và xem kênh có trong config không |
| Đổi định dạng dữ liệu | `contracts/*.schema.json` + `src/ingest/crawler/schema.py`, tăng `schema_version` | Báo cả nhóm |

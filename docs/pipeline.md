# Đường ống dữ liệu (Data Pipeline)

> Mục đích: Mô tả các bước thu thập, xử lý, lưu trữ và phục vụ dữ liệu; tách phần bắt buộc (theo lô) và phần streaming tùy chọn; cập nhật lần cuối: 2026-10-28.

## 1. Tổng quan

Dự án làm theo hai giai đoạn:

| Giai đoạn | Trạng thái | Mục tiêu |
|---|---|---|
| **1. Xử lý theo lô** | **Bắt buộc**, đang làm | Trả lời Q1–Q5 trên dữ liệu đã crawl |
| **2. Streaming** | Tùy chọn | Demo xử lý gần thời gian thực và cảnh báo bằng Kafka/Spark |

Cả hai giai đoạn dùng **cùng** contract và cùng các collection trong [data-model.md](data-model.md). Giai đoạn 2 chỉ thay cách dữ liệu chạy qua các bước, không đổi định dạng.

## 2. Giai đoạn 1: Xử lý theo lô (bắt buộc)

```text
1. Thu thập     YouTube API → crawler → data/raw/comments.jsonl            ✅ src/ingest
2. Tiền xử lý   comments.jsonl → lọc spam, nhận diện tiếng Việt,
                chuẩn hóa text_norm, tách mệnh đề → clean_data.jsonl         ⚠️ code chưa có trong repo
3. Nạp DB       models, videos, comments                                     ❌ Công việc 3
4. Suy luận     mô hình khía cạnh + cảm xúc + máy được nhắc
                → aspect_mentions                                            ❌ Công việc 8–10
5. Tổng hợp     aspect_mentions → aggregates (số đếm theo máy, khía cạnh,
                tuần, video)                                                 ❌ Công việc 12
6. Phân tích    Q1–Q5: tỷ lệ, khoảng tin cậy, kiểm định                     ❌ Công việc 12
7. Hiển thị     dashboard + báo cáo                                          ⚠️ bản nháp tĩnh
```

### 2.1 Thu thập

Crawler đi qua playlist uploads của các kênh trong `config/pipeline.yaml`, lọc video theo tiêu đề và ngày đăng, rồi cào bình luận gốc và reply trong cửa sổ 4 tuần sau `launch_date`. Chi tiết: [src/ingest/README.md](../src/ingest/README.md).

Lưu ý: trường `model` của bình luận là **máy của video**, không phải máy được nhắc. Máy được nhắc xác định ở bước 4.

### 2.2 Tiền xử lý

- Lọc spam (hiện bằng luật: link, số điện thoại, mời liên hệ, cờ bạc, lặp ký tự…). Tách riêng "không phải tiếng Việt" khỏi "spam" khi báo cáo tỷ lệ spam.
- Chuẩn hóa: chữ thường, khoảng trắng, emoji, teencode → `text_norm`.
- Tách mệnh đề theo dấu câu và từ nối ("nhưng", "còn"…). Cẩn thận với "mà" vì từ này nhiều nghĩa trong tiếng Việt; kiểm tra chất lượng tách trên mẫu.
- Giữ `parent_text` để hiểu ngữ cảnh reply.
- Dùng `published_at` làm thời gian sự kiện.

### 2.3 Suy luận và tổng hợp

Mỗi mệnh đề không spam đi qua 3 mô hình, ghi một dòng `aspect_mentions` cho mỗi khía cạnh được nhắc. `days_since_launch` tính theo `launch_date` của `target_model`. `aggregates` ghi bằng upsert theo khóa để chạy lại không bị cộng dồn. Chi tiết: [ml-training.md](ml-training.md#7-đưa-mô-hình-vào-dữ-liệu).

## 3. Giai đoạn 2: Streaming (tùy chọn)

Chỉ làm khi Giai đoạn 1 xong và giảng viên yêu cầu phần hệ thống phân tán.

```text
replay (src/ingest) → Kafka raw_comments (key = video_id)
   → Spark Structured Streaming: kiểm tra schema, dedupe theo comment_id,
     tiền xử lý, suy luận (nạp mô hình theo model_version)
   → upsert aspect_mentions, aggregates
   → cửa sổ trượt (vd 1 giờ, bước 10 phút) trên số mention neg theo (target_model, aspect)
   → vượt baseline → Kafka alerts → collection alerts
```

- **Replay** phát lại dữ liệu đã crawl theo `published_at` với hệ số tốc độ (`--speed 10`), `--strip-stats` để bỏ like/reply "của tương lai".
- **Ngưỡng cảnh báo** tham khảo: tỷ lệ chê trong cửa sổ vượt trung bình + 2 độ lệch chuẩn của 24 giờ trước; phải hiệu chỉnh trên dữ liệu thật và chỉ áp dụng khi cửa sổ đủ số mention.
- **Idempotent:** mọi sink upsert theo `comment_id`/`mention_id`/khóa aggregate để replay hoặc retry không tạo bản trùng.
- **Đo:** độ trễ từ `ingested_at` đến khi ghi `aspect_mentions`; consumer lag ở tốc độ 1x và 10x.

Hạ tầng dev hiện có: Kafka 1 node ([docker-compose.dev.yml](../src/ingest/docker-compose.dev.yml)). Cụm nhiều broker, Spark, MongoDB và các kịch bản trong [runbooks](../runbooks/incident-response.md) **chưa được dựng**.

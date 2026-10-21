# Kịch bản Ứng phó Sự cố (Incident Response Runbook)

> Mục đích: Hướng dẫn nhận diện và xử lý các sự cố vận hành hoặc demo của hệ thống; cập nhật lần cuối: 2026-10-21.

Tài liệu này hướng dẫn cách xử lý nhanh các sự cố kỹ thuật có thể xảy ra trong quá trình vận hành hệ thống hoặc trong lúc demo bảo vệ đồ án. Hệ thống được thiết kế theo kiến trúc phân tán nên đa số các lỗi node mạng đều có cơ chế tự phục hồi.

## Mức độ nghiêm trọng (Severity Levels)
- **SEV-1 (Nghiêm trọng):** Luồng dữ liệu chết hoàn toàn, Dashboard không cập nhật. Cần xử lý ngay lập tức.
- **SEV-2 (Cảnh báo):** Hệ thống chạy chậm, có độ trễ lớn (High Consumer Lag), dữ liệu dội về quá nhanh nhưng chưa sập.
- **SEV-3 (Thông tin):** Lỗi cục bộ ở một vài record (ví dụ: parser lỗi 1 comment emoji lạ), hệ thống bỏ qua và chạy tiếp.

---

## 🛠️ Các kịch bản sự cố & Cách khắc phục

### Sự cố 1: Độ trễ xử lý tăng vọt (High Consumer Lag) - [SEV-2]
- **Triệu chứng:** Biểu đồ trên Streamlit cập nhật rất chậm. Thời gian chênh lệch giữa `published_at` (lúc user cmt) và `ingested_at` (lúc hệ thống xử lý xong) kéo dài hơn 10 giây (khi ở tốc độ Replay 1x).
- **Nguyên nhân:** Lượng bình luận đổ về quá lớn, 1 worker của Spark không tính toán kịp (đặc biệt ở khâu chạy mô hình ML).
- **Cách khắc phục (Mitigation):**
  1. Mở terminal, sử dụng Docker Compose / Docker Swarm để scale thêm worker cho Spark:
     ```bash
     docker-compose up --scale spark-worker=3 -d
     ```
  2. Spark Streaming sẽ tự động phân bổ lại micro-batches sang các worker mới. Hệ thống sẽ mất khoảng 1-2 phút để "nuốt" hết lượng lag và bắt kịp thời gian thực (hành vi này gọi là Catch-up).

### Sự cố 2: Một Broker Kafka bị chết đột ngột - [SEV-1 / Bài test Demo]
- **Triệu chứng:** Trong lúc demo, cố tình tắt 1 container Kafka (hoặc máy ảo chứa broker bị sập). 
- **Nguyên nhân:** Mô phỏng lỗi phần cứng trong hệ thống phân tán.
- **Cơ chế tự phục hồi (Auto-recovery):**
  - Vì Kafka topic `raw_comments` được cấu hình với `Replication Factor = 2` hoặc `3`, luồng dữ liệu sẽ tạm khựng lại khoảng 3-5 giây để bầu (elect) lại Leader partition mới.
  - Sau đó Crawler và Spark sẽ tự kết nối lại và xử lý tiếp. Không mất bất kỳ một comment nào.
  - Các comment bị xử lý trùng lặp (nếu có) sẽ được MongoDB xử lý bằng cơ chế **Upsert dựa trên `comment_id`**, đảm bảo tính toàn vẹn dữ liệu (Idempotency).
- **Lệnh test sự cố:**
  ```bash
  docker stop kafka-broker-2
  # Chờ 5s xem dashboard chạy tiếp, sau đó bật lại
  docker start kafka-broker-2
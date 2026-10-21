# Hệ thống phân tán phân tích luồng bình luận sau ra mắt điện thoại

> Mục đích: Giới thiệu tổng quan, kiến trúc và cấu trúc thư mục của hệ thống; cập nhật lần cuối: 2026-10-21.

## 📌 Bối cảnh dự án
Hệ thống được thiết kế để hỗ trợ một hãng điện thoại (giả định) vừa ra mắt mẫu máy mới tại thị trường Việt Nam. Trong giai đoạn đầu ra mắt, hệ thống sẽ thu thập liên tục các bình luận từ các video review, unbox tiếng Việt trên YouTube để giải quyết 3 bài toán nghiệp vụ cốt lõi:
1. **Lọc dữ liệu rác (Spam Detection):** Tự động loại bỏ bình luận seeding, quảng cáo.
2. **Phân tích khía cạnh (Aspect-based Sentiment):** Theo dõi tỷ lệ khen/chê về 9 khía cạnh (Pin, Màn hình, Hiệu năng, Camera, Thiết kế và độ bền, Phần mềm, Phần cứng khác, giá, Bảo hành và hậu mãi) giữa mẫu máy mới và mẫu đối thủ.
3. **Cảnh báo khủng hoảng (Anomaly Alerting):** Phát hiện tức thời khi lượng bình luận tiêu cực về một khía cạnh tăng đột biến trong cửa sổ thời gian ngắn.

## 🏗️ Kiến trúc Công nghệ (Tech Stack)
Hệ thống sử dụng kiến trúc xử lý luồng phân tán (Distributed Stream Processing):
- **Data Ingestion:** YouTube Data API v3, Python Crawler.
- **Message Broker:** Apache Kafka (Topics: `raw_comments`, `alerts`).
- **Stream Processing:** Apache Spark Structured Streaming (Tiền xử lý, Chạy mô hình ML, Tính toán cửa sổ trượt).
- **Storage:** MongoDB (Collections: `comments`, `aggregates`, `alerts`).
- **Serving & Visualization:** FastAPI (Backend REST API) & Streamlit (Real-time Dashboard).
- **Machine Learning:** TF-IDF kết hợp SVM/Naive Bayes/Random Forest.

## 🤖 Vòng đời dữ liệu và mô hình

- Dữ liệu bình luận tổng hợp từ Internet/dataset bên ngoài được EDA, gán nhãn và chia theo `video_id`/nguồn/thời gian để huấn luyện **Teacher**.
- Crawler YouTube ghi raw archive tại `src/ingest/data/raw/comments.jsonl`; dữ liệu này đi vào Kafka/Spark để inference và cảnh báo, không mặc định là dữ liệu train.
- Một mẫu YouTube được gán nhãn thủ công có thể dùng làm `youtube_test_labeled.jsonl` để đánh giá khả năng chuyển miền.
- Nếu dùng Teacher–Student, Teacher tạo pseudo-label có lọc confidence cho dữ liệu YouTube; Student chỉ được triển khai sau khi đánh giá độc lập.
- Xem quy trình đầy đủ tại [`docs/ml-training.md`](docs/ml-training.md).

## 📂 Cấu trúc Thư mục
- `/config`: Cấu hình hệ thống, tham số pipeline.
- `/contracts`: Định nghĩa Schema dữ liệu (VD: JSON schema cho comment).
- `/docs`: Tài liệu kiến trúc và luồng dữ liệu (Mermaid, Markdown).
- `/runbooks`: Hướng dẫn vận hành, kịch bản xử lý sự cố (Incident Response).
- `/src/ingest`: Script cào dữ liệu và phát lại (Replay) đẩy vào Kafka.
- `/src/processing`: Các job Spark Streaming xử lý dữ liệu và chạy ML.
- `/src/serving`: API Backend bằng FastAPI và Frontend bằng Streamlit.
- `/tests`: Unit tests và Integration tests.
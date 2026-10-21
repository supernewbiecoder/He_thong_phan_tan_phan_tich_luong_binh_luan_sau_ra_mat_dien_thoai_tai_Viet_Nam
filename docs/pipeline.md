# Chi tiết Đường ống Dữ liệu (Data Pipeline)

> Mục đích: Mô tả luồng thu thập, xử lý, lưu trữ và phục vụ dữ liệu bình luận; cập nhật lần cuối: 2026-10-21.

Đường ống dữ liệu của hệ thống được thiết kế theo kiến trúc **Stream Processing**, đảm bảo xử lý liên tục với độ trễ thấp ngay khi có bình luận mới.

> **Phân biệt dữ liệu:** dữ liệu bình luận tổng hợp từ Internet/dataset bên ngoài được dùng để EDA, gán nhãn và huấn luyện Teacher. Dữ liệu YouTube trong `src/ingest/data/raw/comments.jsonl` là raw input cho test tích hợp, đánh giá khác miền sau khi gán nhãn và inference production; không dùng trực tiếp để train khi chưa có nhãn. Xem chi tiết tại [Vòng đời mô hình học máy](./ml-training.md).

## 1. Data Ingestion (Hứng dữ liệu vào Kafka)
- **Nguồn:** API của YouTube sẽ trả về dữ liệu bình luận dạng JSON (bao gồm comment gốc và reply). 
- **Quy trình:** Script `crawler` lấy dữ liệu, giữ lại các trường quan trọng (comment_id, text, model, published_at, author_hash) và đẩy trực tiếp vào Topic `raw_comments` của cụm Apache Kafka. Kafka chia partition theo `video_id` để tăng tốc độ phân phối và chống nghẽn nút cổ chai.
- **Chế độ Demo (Replay):** Khi bảo vệ đồ án, để đảm bảo tính ổn định, hệ thống sẽ đọc từ file lịch sử và bắn vào Kafka với hệ số tua nhanh (ví dụ: x10, x100 lần thời gian thực).

## 2. Stream Processing (Xử lý tập trung với Apache Spark)
Spark Structured Streaming thực hiện chuỗi tác vụ sau trên từng micro-batch:
1. **Tiền xử lý (Preprocessing):** Tách bình luận thành các mệnh đề nhỏ dựa trên dấu câu và từ nối ("nhưng", "mà"). Sau đó làm sạch văn bản (chuyển chữ không dấu, dịch teencode, chuẩn hóa emoji) lưu vào trường `text_norm`.
2. **Suy luận ML (Inference):** 
   - Chạy qua mô hình phân loại Spam (Lọc bỏ nếu là rác).
   - Chạy qua mô hình đa nhãn để xác định Khía cạnh (1 trong 9 khía cạnh: Pin, Màn hình, Hiệu năng...).
   - Chạy qua mô hình Cảm xúc (Tích cực, Tiêu cực, Trung tính).
3. **Phát hiện bất thường (Anomaly Detection):** Spark sử dụng hàm cửa sổ trượt (Sliding Window - ví dụ trượt 1 giờ, nhảy 10 phút) để đếm số lượng mệnh đề tiêu cực. Nếu tỷ lệ tiêu cực vượt quá ngưỡng (trung bình + 2 độ lệch chuẩn của 24h trước), hệ thống kích hoạt cảnh báo, đẩy vào Topic `alerts`.

## 3. Data Storage (Lưu trữ vào MongoDB)
Dữ liệu sau khi đi qua Spark được ghi đè (upsert theo `comment_id` để chống trùng lặp do phân tán) vào 3 collections trong MongoDB:
- `comments`: Lưu chi tiết từng mệnh đề kèm 3 nhãn dự đoán.
- `aggregates`: Lưu kết quả đếm (count) tổng hợp theo thời gian (giúp dashboard load nhanh hơn thay vì query từ bảng comments).
- `alerts`: Lưu trữ lịch sử các lần xảy ra cảnh báo khủng hoảng.

## 4. Serving (Hiển thị Real-time)
- **FastAPI** cung cấp các REST endpoint để truy vấn số liệu thống kê.
- **Streamlit** gọi API theo chu kỳ (polling) để cập nhật biểu đồ đường (Line chart) biểu diễn xu hướng cảm xúc và hiển thị pop-up danh sách cảnh báo ngay khi MongoDB có dữ liệu `alerts` mới.
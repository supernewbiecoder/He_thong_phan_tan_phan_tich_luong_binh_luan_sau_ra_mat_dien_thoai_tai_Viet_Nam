# Test strategy

> Mục đích: Mô tả chiến lược kiểm thử hợp đồng, đơn vị, tích hợp và chất lượng dữ liệu; cập nhật lần cuối: 2026-10-28.

**Trạng thái:** chưa có test nào. Ưu tiên viết theo thứ tự dưới đây.

1. **Contract tests** (làm ngay sau Công việc 4): validate mẫu dữ liệu thật với [contracts/comment-event.schema.json](../contracts/comment-event.schema.json) và [contracts/aspect-mention.schema.json](../contracts/aspect-mention.schema.json).
2. **Unit tests:** chuẩn hóa văn bản, tách mệnh đề (gồm các câu khó như "không lag chút nào", "cam đẹp nhưng pin yếu"), nhận diện `target_model` theo alias, tính `days_since_launch`, tính `aggregates`.
3. **Data quality tests:** khóa không trùng, không có bình luận "từ tương lai", reply mồ côi, tỷ lệ `target_model = null`, mọi `model` có trong danh mục máy.
4. **Integration tests** (chỉ khi làm Giai đoạn 2 streaming): replay vào Kafka, chạy processor, kiểm tra upsert không tạo bản trùng.

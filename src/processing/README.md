# Processing

> Mục đích: Phạm vi thư mục xử lý: tiền xử lý, gán nhãn bằng mô hình, tổng hợp và notebook phân tích; cập nhật lần cuối: 2026-10-28.

Đặt tại đây: code tiền xử lý (Công việc 6), suy luận mô hình ghi `aspect_mentions` (Công việc 8–10), tính `aggregates` và phân tích Q1–Q5 (Công việc 12). Xem [docs/pipeline.md](../../docs/pipeline.md) và [docs/roadmap.md](../../docs/roadmap.md).

## Còn thiếu

- **Code tạo `data/clean_data.jsonl`** (lọc spam, nhận diện tiếng Việt, tách mệnh đề) chưa có trong repo.
- **Code tạo bundle Executive Report** (`src/serving/dashboard/eda_smartphone_outputs/dashboard_exec_data.json`) chưa có trong repo.

Cả hai thuộc Công việc 6. Chưa có thì không ai tái lập được kết quả.

## Notebook EDA (bản nháp)

[`eda_smartphone_comments.ipynb`](eda_smartphone_comments.ipynb) là **bản nháp để hình dung đầu ra**, chưa phải kết quả:

- Phần EDA (mục 1–3) đọc `data/clean_data.jsonl`. Lần chạy gần nhất: 225.968 bản ghi, 211.627 không spam.
- Phần Executive Report (mục 4) chỉ hiển thị bundle của dashboard, được sinh từ **một phiên bản dữ liệu khác** (109.344 bản ghi). Hai nửa notebook đang không cùng dữ liệu.
- Khía cạnh và khen/chê đang là **luật từ khóa chưa được đánh giá**, nên mọi tỷ lệ chỉ là **số liệu minh họa**.
- Một số nhận xét viết tay trong notebook không khớp với output ngay phía trên (vd tỷ lệ 3 hãng lớn, tỷ lệ emoji, tỷ lệ tác giả bình luận 1 lần). Sửa hoặc xóa trước khi dùng.
- `MODEL_INFO` thiếu 7 model nên ~13% dữ liệu bị xếp vào hãng "Khác".

Phân tích chính thức làm theo [docs/EDA_requirement.md](../../docs/EDA_requirement.md) sau khi có mô hình.

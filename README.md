# Nhánh `kham-pha-nhan`: dữ liệu v4 và khám phá nhãn

> Mục đích: Giới thiệu nhánh khám phá nhãn: để làm gì, có gì, không có gì, bắt đầu từ đâu; cập nhật lần cuối: 2026-11-22.

Đồ án môn Khoa học dữ liệu, nhóm 11 người: phân tích bình luận YouTube tiếng Việt sau khi một điện thoại ra mắt.

**Nhánh này để làm gì:** bắt đầu lại từ dữ liệu. Đọc một mẫu bình luận để tìm ra **bình luận v4 có những loại nội dung nào và mỗi loại chiếm bao nhiêu**, rồi mới chốt bộ nhãn để gán. Lý do và lộ trình: [kế hoạch nhánh](docs/0-chung/ke-hoach.md).

## Có gì

```text
config/pipeline.yaml        cấu hình đã dùng để crawl dữ liệu v4 (danh mục máy, kênh, cửa sổ thời gian)
config/analysis.yaml        bộ 4 máy ứng viên (chưa chốt), cho notebook mục 3.4
notebooks/1_raw_audit.ipynb kiểm tra cấu trúc dữ liệu (EDA): rỗng, trùng, độ dài, ngôn ngữ, thời gian, theo máy, kênh, video
notebooks/helpers.py        hàm dùng chung cho notebook
src/labeling/               code khám phá nhãn: lấy mẫu, HAC, công thức thống kê
tests/test_labeling.py      test của src/labeling (python -m unittest tests.test_labeling)
docs/                       tài liệu: kế hoạch, đặc tả dữ liệu, khám phá nhãn (mục lục: docs/README.md)
AGENTS.md, CLAUDE.md        luật cho trợ lý AI
src/ingest/data/            dữ liệu v4 (NGOÀI GIT, xem dưới)
data/kham-pha/              mẫu, phiếu mã hóa, ứng viên HAC (NGOÀI GIT: có nội dung bình luận thật)
```

**Cố ý không có:** code crawler, tiền xử lý, mô hình, phân tích Q1–Q6, DB. Chúng ở nhánh `main`. Nhánh này là **nhánh mồ côi**: không chung lịch sử với `main`, nên không merge vào `main`. Kết quả đưa về `main` bằng cách chép file.

## Dữ liệu

Dữ liệu v4 **không nằm trong git**:
- file 388 MB, quá giới hạn 100 MB/file của GitHub;
- có `author_name` là dữ liệu cá nhân.

Đặt đúng các đường dẫn sau, rồi kiểm số dòng và SHA-256 theo [đặc tả dữ liệu mục 3](docs/1-thu-thap/dac-ta.md#3-phiên-bản):

```text
src/ingest/data/raw/comments.jsonl   473.786 dòng
src/ingest/data/raw/videos.jsonl
src/ingest/data/models.json
```

Nhánh này và `main` dùng **chung một thư mục**, chuyển qua lại bằng GitHub Desktop (*Current branch*). Dữ liệu và `.venv` nằm ngoài git nên ở nguyên khi chuyển nhánh, dùng chung cho cả hai. Trước khi chuyển nhánh phải commit hoặc bỏ các thay đổi đang dở.

## Bắt đầu

1. Đọc [kế hoạch nhánh](docs/0-chung/ke-hoach.md).
2. Chạy kiểm tra cấu trúc (bước B1): [hướng dẫn](docs/1-thu-thap/huong-dan-kiem-tra-du-lieu.md).
3. Bước khám phá nhãn (B2–B8): [đặc tả](docs/3-gan-nhan/dac-ta-kham-pha-nhan.md) và [guideline mã hóa](docs/3-gan-nhan/huong-dan-kham-pha-nhan.md).

**Chưa push lên GitHub.** Trưởng nhóm quyết khi nào push.

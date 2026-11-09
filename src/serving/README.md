# Serving

> Mục đích: Phạm vi thư mục phục vụ: ghi DB, API và dashboard; cập nhật lần cuối: 2026-10-28.

Đặt tại đây: script ghi/đọc DB theo [docs/data-model.md](../../docs/data-model.md), API cho dashboard, dashboard (Công việc 3, 13). Mọi thao tác ghi phải idempotent (upsert theo khóa) để chạy lại hoặc replay không tạo bản trùng.

## Dashboard (bản nháp)

[`dashboard/index.html`](dashboard/index.html) là **bản nháp tĩnh** để thống nhất cả nhóm muốn đầu ra trông thế nào:

- Đọc dữ liệu từ file snapshot trong `dashboard/eda_smartphone_outputs/` (`executive_report_data.js`, `dashboard_exec_data.json`), chưa nối DB/API.
- Số liệu sinh từ luật từ khóa trên một phiên bản dữ liệu cũ (109.344 bản ghi): **chỉ để minh họa**.
- Đã bỏ giao diện và code dự báo tuần 8 từ 4 điểm tuần. Phần phân cụm vẫn là nội dung khám phá của bản nháp, xem [docs/EDA_requirement.md](../../docs/EDA_requirement.md#5-lỗi-đã-gặp-ở-bản-nháp-tránh-lặp-lại).
- Cách chạy và đọc kết quả CV12: [hướng dẫn duy nhất](../analysis/README.md). Snapshot trên dashboard chưa tự cập nhật từ kết quả mới.

Bản chính thức (Công việc 13) đọc từ `aggregates` và `aspect_mentions`, hiển thị khoảng tin cậy và kết quả kiểm định theo đặc tả.

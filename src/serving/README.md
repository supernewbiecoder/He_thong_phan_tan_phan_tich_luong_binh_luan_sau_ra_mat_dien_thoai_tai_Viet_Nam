# Serving boundary

> Mục đích: Xác định ranh giới các thành phần sink, API dashboard và cảnh báo; cập nhật lần cuối: 2026-10-21.

Đặt sink tới object storage, analytical store, dashboard API và alerting tại đây. Sink phải idempotent theo khóa cửa sổ hoặc event version để replay không tạo bản ghi trùng.

## Dashboard tham khảo

Dashboard tĩnh cho EDA nằm tại [`dashboard/index.html`](dashboard/index.html). File cần đi cùng `dashboard/eda_smartphone_outputs/executive_report_data.js`; dữ liệu hiện là snapshot nhúng trong giao diện, chưa kết nối API của hệ thống.

# Serving boundary

> Mục đích: Xác định ranh giới các thành phần sink, API dashboard và cảnh báo; cập nhật lần cuối: 2026-10-27.

Đặt sink tới object storage, analytical store, dashboard API và alerting tại đây. Sink phải idempotent theo khóa cửa sổ hoặc event version để replay không tạo bản ghi trùng.

## Dashboard tham khảo

Dashboard tĩnh cho EDA nằm tại [`dashboard/index.html`](dashboard/index.html). File đi cùng thư mục `dashboard/eda_smartphone_outputs/` chứa dữ liệu snapshot (`executive_report_data.js`, `dashboard_exec_data.json`) cùng toàn bộ biểu đồ PNG/SVG; dữ liệu hiện là snapshot nhúng trong giao diện, chưa kết nối API của hệ thống.

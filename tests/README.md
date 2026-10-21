# Test strategy

> Mục đích: Mô tả chiến lược kiểm thử hợp đồng, đơn vị, tích hợp và chất lượng dữ liệu; cập nhật lần cuối: 2026-10-21.

- **Contract tests:** mọi adapter validate event mẫu với JSON Schema.
- **Unit tests:** normalization, fingerprint/deduplication, late event, update/delete và aggregate.
- **Integration tests:** publish vào raw topic, chạy processor, kiểm tra normalized/DLQ/metrics.
- **Data quality tests:** freshness, null rate, contract validity, lag và reconciliation theo ngưỡng trong `config/pipeline.yaml`.

# Processing boundary

> Mục đích: Xác định phạm vi các job xử lý luồng và các bước phân tích dữ liệu; cập nhật lần cuối: 2026-10-27.

Đặt stream job tại đây: validation, normalization, deduplication, enrichment, sentiment/topic classification và windowed aggregation.

## Notebook phân tích & EDA

**`eda_smartphone_comments.ipynb`** (Notebook EDA duy nhất - Đã gộp và tối ưu):
- **Nguồn dữ liệu:** Đọc trực tiếp từ `data/clean_data.jsonl` (tập dữ liệu 109.344 dòng đã qua tiền xử lý, gán cờ spam, nhận diện tiếng Việt và tách mệnh đề).
- **Kiểm tra dữ liệu (1 Cell duy nhất):** Bảng kiểm định 13 tiêu chí chất lượng (schema, khóa chính, tính toàn vẹn thời gian/mệnh đề, kiểm tra nhãn spam và tỷ lệ dữ liệu sạch).
- **Phân tích khám phá đa chiều:** Phân bố tương tác (heavy-tail CCDF, Lorenz curve, Gini, Kruskal-Wallis), tương quan Like vs Reply (Spearman rho + hexbin), chuỗi thời gian & nhịp sinh học tuần/giờ GMT+7, vòng đời chú ý của model, từ vựng Unicode & từ đặc trưng (Monroe log-odds), ma trận khía cạnh (Aspect) và đối sánh thương hiệu chéo.
- **Báo cáo điều hành (Executive Report):** Trả lời 5 câu hỏi nghiệp vụ theo đặc tả [`docs/EDA_requirement.md`](../../docs/EDA_requirement.md) và kết nối trực tiếp với bundle dữ liệu phục vụ Dashboard tại `src/serving/dashboard/`.
- **Tóm tắt:** Tự động sinh số liệu tổng kết trực tiếp từ tập dữ liệu.

Mọi business rule thay đổi phải cập nhật [tài liệu pipeline](../../docs/pipeline.md) và test tương ứng.

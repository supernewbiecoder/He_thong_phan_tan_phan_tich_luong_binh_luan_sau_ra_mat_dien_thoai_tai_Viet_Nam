# Storage Layer: MongoDB Sentiment Analytics

> **Phụ trách:** Việt (Công việc STT 3 - Thiết kế DB)  
> **Phiên bản:** v1.0.0 (Cập nhật ngày 28/10/2026)  
> **Database:** MongoDB 7.0 (Hỗ trợ cả chế độ giả lập offline `mongomock`)

---

## 1. Tổng quan Kiến trúc

Tầng lưu trữ (Storage Layer) là trung tâm kết nối giữa **Spark Streaming** (xử lý luồng NLP/ABSA) và **FastAPI Backend / Dashboard** (phục vụ người dùng cuối):

```mermaid
flowchart LR
    Spark[Spark Streaming ABSA] -->|Bản ghi bình luận| C[comments]
    Spark -->|Mệnh đề bóc tách ABSA| AM[aspect_mentions]
    Spark -->|Sliding Windows (Số đếm)| AGG[aggregates]
    Spark -->|Cảnh báo bất thường| ALT[alerts]

    CFG[config/pipeline.yaml] -->|Danh mục máy| M[models]
    Team[Gán nhãn chuyên viên] -->|Ground Truth 3K| GL[gold_labels]
    Crawler[YouTube Crawler] -->|Metadata Video| V[videos]

    M & V & C & AM & AGG & ALT & GL --> FastAPI[FastAPI Backend]
    FastAPI --> Dashboard[Executive Dashboard]
```

---

## 2. Danh sách 7 Collection Trọng tâm

| STT | Collection | Khóa chính | Mục đích & Chi tiết |
|:---:|:---|:---|:---|
| 1 | `models` | `model_id` | Danh mục máy, thương hiệu, phân khúc, ngày ra mắt tại VN, danh sách đối thủ cạnh tranh (`rivals`). |
| 2 | `videos` | `video_id` | Danh mục video review được thu thập (Vật Vờ Studio, Duy Thẩm, Tinh Tế, Schannel...). |
| 3 | `comments` | `comment_id` | Bình luận đã làm sạch theo hợp đồng `comment-event.schema.json` (có `like_count`, `is_owner`, `is_spam`). |
| 4 | `aspect_mentions` | `mention_id` | Mệnh đề bóc tách gán nhãn 9 khía cạnh kỹ thuật, cảm xúc (`positive`/`negative`/`neutral`), phân loại lỗi, cờ so sánh (`contracts/aspect-mention.schema.json`). |
| 5 | `aggregates` | `agg_id` | Số liệu tổng hợp theo cửa sổ thời gian (Tuần 1–4, 4 tuần đầu) — **Lưu số đếm nguyên, KHÔNG lưu %**. |
| 6 | `alerts` | `alert_id` | Nhật ký các đợt bùng phát tiêu cực bất thường (Spike detection) theo dõi khủng hoảng truyền thông. |
| 7 | `gold_labels` | `gold_id` | 3.000 mệnh đề được 2 chuyên viên gán nhãn độc lập + hội đồng duyệt dùng đo Cohen's Kappa và kiểm thử mô hình. |

---

## 3. Nguyên tắc Thiết kế Bắt buộc

### 3.1. Collection `aggregates` CHỈ lưu số đếm nguyên (Counts Only, Tuyệt đối KHÔNG lưu %)
* **Lý do toán học:** Phần trăm là đại lượng không có tính chất cộng dồn (non-additive). Ví dụ: Tuần 1 có 75% tích cực ($n=100$), Tuần 2 có 50% tích cực ($n=10$). Ta **không thể** lấy trung bình cộng $(75\% + 50\%)/2 = 62.5\%$ vì tỷ lệ thực tế là $\frac{75 + 5}{100 + 10} = \frac{80}{110} \approx 72.7\%$.
* **Quy chuẩn lưu trữ:**
  ```json
  "counts": {
    "pos_count": 380,
    "neg_count": 50,
    "neu_count": 40,
    "total_count": 470,
    "owner_defect_count": 15,
    "comparison_count": 60,
    "compared_win_count": 42,
    "compared_lose_count": 18
  }
  ```
* **Tính toán tại thời điểm truy vấn (FastAPI / Dashboard):**
  $$\% \text{ Khen} = \frac{\text{pos\_count}}{\text{pos\_count} + \text{neg\_count}} \times 100$$
  $$\text{Net Sentiment} = \% \text{ Khen} - \% \text{ Chê}$$

### 3.2. Bắt buộc có Metadata nguồn gốc và phiên bản
Mọi bản ghi gán nhãn trong `aspect_mentions`, `aggregates`, `comments` đều phải có:
* `label_source`: `"rule"`, `"llm"`, `"phobert_v1"`, hoặc `"human"`.
* `model_version`: Ví dụ `"v1.0.0"`.

---

## 4. Hướng dẫn Vận hành & Lệnh Thực thi

### 4.1. Khởi chạy MongoDB qua Docker Compose
```bash
docker compose -f src/ingest/docker-compose.dev.yml up -d mongodb
```
* MongoDB chạy tại: `mongodb://localhost:27017`
* Database mặc định: `smartphone_analytics`

### 4.2. Khởi tạo Cơ sở Dữ liệu & Đánh Index (`init_db.py`)
Tự động tạo 7 collection, thiết lập schema validators và các chỉ mục (Unique Index, Compound Index):
```bash
# Chạy với MongoDB thật:
python -m src.storage.init_db --uri mongodb://localhost:27017

# Chạy giả lập offline (mongomock, không cần cài MongoDB):
python -m src.storage.init_db --mock
```

### 4.3. Nạp Dữ liệu Mẫu (`seed_db.py`)
Nạp danh mục máy từ `config/pipeline.yaml`, bóc tách mệnh đề từ `data/clean_data.jsonl`, tính toán số đếm tổng hợp và nạp dữ liệu mẫu cho alerts & gold labels:
```bash
# Nạp dữ liệu vào MongoDB thật:
python -m src.storage.seed_db --uri mongodb://localhost:27017 --limit 500

# Nạp dữ liệu giả lập offline:
python -m src.storage.seed_db --mock --limit 200
```

### 4.4. Chạy Bộ Kiểm thử Toàn vẹn CSDL (`verify_db.py`)
Kiểm tra tự động 8 tiêu chuẩn vàng:
1. Đủ 7 collection và có dữ liệu.
2. Unique index hoạt động chính xác.
3. **Aggregates lưu đúng số đếm, không chứa bất kỳ trường `%` nào, tổng khớp $pos + neg + neu = total$.**
4. Aspect mentions tuân thủ đúng 9 khía cạnh chuẩn, có `label_source` và `model_version`.
5. Comments có đủ metadata.
6. Models có đủ S23 Ultra, đối thủ cạnh tranh và ngày ra mắt.
7. Alerts có đủ trạng thái và ngưỡng phát hiện.
8. Gold labels có đủ nhãn độc lập và nhãn đồng thuận.

```bash
# Chạy kiểm thử với MongoDB thật:
python -m src.storage.verify_db --uri mongodb://localhost:27017

# Chạy kiểm thử tự động offline (tự khởi tạo + nạp mẫu + kiểm tra):
python -m src.storage.verify_db --mock
```

---

## 5. Tài liệu Chi tiết
* Thiết kế chi tiết & Ánh xạ 5 câu hỏi nghiệp vụ: xem [`docs/database_design.md`](file:///f:/intro_data_science/repo-feature-eda-dashboard/docs/database_design.md).
* Hợp đồng JSON Schema cho Aspect Mentions: xem [`contracts/aspect-mention.schema.json`](file:///f:/intro_data_science/repo-feature-eda-dashboard/contracts/aspect-mention.schema.json).

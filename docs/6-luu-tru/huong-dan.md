# Storage Layer: MongoDB Sentiment Analytics

> Mục đích: Cách dựng MongoDB, tạo collection, nạp đầu ra của chuỗi theo lô và kiểm DB; cập nhật lần cuối: 2026-11-26.

> **Phụ trách:** Việt (Công việc 3, bản 28/10); sửa theo contract v3, thêm nạp dữ liệu thật: Nguyễn Lê Quân (26/11).  
> **Database:** MongoDB 7.0. Test chạy được bằng `mongomock`.

---

## 1. Tổng quan Kiến trúc

Tầng lưu trữ nối **chuỗi theo lô** (`python -m src.run`, đang dùng) và sau này **Spark Streaming** (để sau) với **API và dashboard** ([tầng 7](../7-hien-thi/huong-dan.md)). Hiện dữ liệu vào DB bằng bước `nap_db`; sơ đồ dưới là thiết kế cho giai đoạn streaming:

```mermaid
flowchart LR
    Spark[Spark Streaming ABSA] -->|Bản ghi bình luận| C[comments]
    Spark -->|Mệnh đề bóc tách ABSA| AM[aspect_mentions]
    Spark -->|Sliding Windows (Số đếm)| AGG[aggregates]
    Spark -->|Cảnh báo bất thường| ALT[alerts]

    CFG[config/pipeline.yaml] -->|Danh mục máy| M[models]
    Team[Gán nhãn người] -->|Nhãn chuẩn| GL[gold_labels]
    CV12[Công việc 12] -->|Q1–Q5| AR[analysis_results]
    Crawler[YouTube Crawler] -->|Metadata Video| V[videos]

    M & V & C & AM & AGG & ALT & GL & AR --> FastAPI[FastAPI Backend]
    FastAPI --> Dashboard[Executive Dashboard]
```

---

## 2. Danh sách 8 collection

| STT | Collection | Khóa chính | Mục đích & Chi tiết |
|:---:|:---|:---|:---|
| 1 | `models` | `model_id` | Danh mục máy, thương hiệu, phân khúc, ngày ra mắt tại VN, danh sách đối thủ cạnh tranh (`rivals`). |
| 2 | `videos` | `video_id` | Danh mục video review được thu thập (Vật Vờ Studio, Duy Thẩm, Tinh Tế, Schannel...). |
| 3 | `comments` | `comment_id` | Bình luận raw (`comment-event` v3) cộng kết quả tầng 2 (`text_clean`, `clauses`, `is_spam`, `is_vietnamese`…); không lưu `author_name`. |
| 4 | `aspect_mentions` | `mention_id` | Nhận xét theo (bình luận, máy, nhãn chiều 2) của bộ nhãn chốt, thái độ `tich_cuc`/`tieu_cuc`/`so_sanh`/`khong_danh_gia`, cờ so sánh; đúng contract `aspect-mention` v3. |
| 5 | `aggregates` | `agg_id` | Số liệu tổng hợp theo cửa sổ thời gian (Tuần 1–4, 4 tuần đầu) — **Lưu số đếm nguyên, KHÔNG lưu %**. |
| 6 | `alerts` | `alert_id` | Nhật ký các đợt bùng phát tiêu cực bất thường (Spike detection) theo dõi khủng hoảng truyền thông. |
| 7 | `gold_labels` | `clause_id` + `annotator` | Nhãn người của tập test (gán đôi, phân xử), dùng chấm mô hình. Chưa có dữ liệu. |
| 8 | `analysis_results` | `analysis_id` | Kết quả Q1–Q5 của Công việc 12 (`business_questions.json`), mỗi máy X × phiên bản nhãn một document (thêm 26/11). |

---

## 3. Nguyên tắc Thiết kế Bắt buộc

### 3.1. Collection `aggregates` CHỈ lưu số đếm nguyên (Counts Only, Tuyệt đối KHÔNG lưu %)
* **Lý do toán học:** Phần trăm là đại lượng không có tính chất cộng dồn (non-additive). Ví dụ: Tuần 1 có 75% tích cực ($n=100$), Tuần 2 có 50% tích cực ($n=10$). Ta **không thể** lấy trung bình cộng $(75\% + 50\%)/2 = 62.5\%$ vì tỷ lệ thực tế là $\frac{75 + 5}{100 + 10} = \frac{80}{110} \approx 72.7\%$.
* **Quy chuẩn lưu trữ:**
  mỗi dòng có `n_pos`, `n_neg`, `n_neu`, `n_cmp` (số mention `tich_cuc`, `tieu_cuc`, `khong_danh_gia`, `so_sanh`), `n_total`, `n_opinionated`. Định nghĩa: [thiết kế dữ liệu mục 5](../0-chung/thiet-ke-du-lieu.md#5-aggregates).
* **Tính toán tại thời điểm truy vấn (FastAPI / Dashboard):**
  $$\% \text{ Khen} = \frac{n_{pos}}{n_{pos} + n_{neg}} \times 100$$
  $$\text{Net Sentiment} = \% \text{ Khen} - \% \text{ Chê}$$

### 3.2. Bắt buộc có Metadata nguồn gốc và phiên bản
Mọi bản ghi gán nhãn trong `aspect_mentions`, `aggregates`, `comments` đều phải có:
* `label_source`: `"rule"`, `"llm"`, `"model"`, hoặc `"human"`.
* `model_version`: ví dụ `"rule-v1.1"`.

---

## 4. Hướng dẫn Vận hành & Lệnh Thực thi

### 4.1. Khởi chạy MongoDB qua Docker Compose
```bash
docker compose -f src/ingest/docker-compose.dev.yml up -d mongodb
```
* MongoDB chạy tại: `mongodb://localhost:27017`
* Database mặc định: `smartphone_analytics`

Hoặc một container tạm: `docker run -d --rm --name mongo-tam -p 27017:27017 mongo:7.0`. Kết nối khác mặc định thì đặt biến môi trường `MONGO_URI`, `MONGO_DB`.

### 4.2. Nạp đầu ra của chuỗi theo lô (cách thường dùng)

```bash
python -m src.run --den nap_db               # chạy cả chuỗi rồi nạp DB
python -m src.run --tu nap_db --den nap_db   # chỉ nạp lại từ kết quả đã có
```

Bước `nap_db` gọi `init_db.init_database` (tạo 8 collection, validator, index; không xóa dữ liệu) rồi `load_db.load_all`:

| Phần | File | Collection | Kiểm khi nạp |
|---|---|---|---|
| Danh mục máy | `config/pipeline.yaml` | `models` | Làm phẳng máy chính và đối thủ khai báo lồng nhau |
| Bình luận | `data/processed/comments.jsonl` | `comments` | Có `comment_id` và `pipeline_version` (đã qua tầng 2); bỏ `author_name` |
| Mention | `data/aspect_mentions.jsonl` | `aspect_mentions` | Từng dòng đúng contract v3; sai một dòng thì không ghi gì |
| Aggregates | `data/aggregates/current/aggregates.jsonl` | `aggregates` | Số nguyên không âm, không có trường tỷ lệ, không trùng khóa |
| Q1–Q5 | `data/aggregates/current/business_questions.json` | `analysis_results` | Có máy X và phiên bản nhãn trong `config` |

Mọi bản ghi upsert theo khóa, nên nạp lại không sinh bản trùng. Với mention và aggregates, file được coi là toàn bộ dữ liệu của từng cặp (`model_version`, máy) có trong file: dòng cũ của cặp đó mà file mới không còn thì bị xóa; máy và phiên bản khác giữ nguyên. Nạp riêng từng phần: `python -m src.storage.load_db --help`.

### 4.3. Chỉ tạo collection và index (`init_db.py`)
```bash
python -m src.storage.init_db --uri mongodb://localhost:27017
python -m src.storage.init_db --mock      # thử bằng mongomock, không cần MongoDB
```

`seed_db.py` (nạp dữ liệu giả theo 9 khía cạnh cũ) đã gỡ ngày 26/11.

### 4.4. Kiểm DB đã nạp (`verify_db.py`)
Kiểm: đủ collection (được trống: `alerts`, `gold_labels`, `videos`); index khóa chính; aggregates chỉ có số đếm và `n_total` bằng tổng bốn cột; tối đa 2.000 mention đúng contract v3; bình luận đủ trường tầng 2; mọi máy có `launch_date`.

```bash
python -m src.storage.verify_db --uri mongodb://localhost:27017
```

Không có MongoDB thì lệnh dừng; DB trống thì báo FAIL, không tự sinh dữ liệu. Test của phần nạp DB: `tests/test_serving_api.py` (mongomock; đặt `TEST_MONGO_URI` để chạy trên MongoDB thật).

---

## 5. Tài liệu Chi tiết
* Thiết kế chi tiết & Ánh xạ 5 câu hỏi nghiệp vụ: xem [`docs/6-luu-tru/dac-ta.md`](dac-ta.md).
* Hợp đồng JSON Schema cho Aspect Mentions: xem [`contracts/aspect-mention.schema.json`](../../contracts/aspect-mention.schema.json).

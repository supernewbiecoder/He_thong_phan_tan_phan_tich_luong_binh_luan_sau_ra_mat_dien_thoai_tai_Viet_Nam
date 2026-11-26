# Tài liệu Thiết kế Cơ sở Dữ liệu (Database Design Document)

> **Dự án:** Hệ thống phân tán phân tích luồng bình luận sau ra mắt điện thoại tại Việt Nam  
> **Người thực hiện:** Việt (Công việc STT 3: Thiết kế DB)  
> **Hệ quản trị CSDL:** MongoDB (NoSQL Document Store)  
> **Cập nhật lần cuối:** 26/11/2026  

> Mục đích: Thiết kế các collection MongoDB, quan hệ giữa chúng, index và chiến lược ghi chống trùng; cập nhật lần cuối: 2026-11-26.

**Cập nhật 26/11 (Nguyễn Lê Quân, theo contract `aspect-mention` v3):** bản gốc ngày 28/10 của Việt viết theo 9 khía cạnh cũ và schema v1. Bản này đổi:
- mã khía cạnh, thái độ theo [bộ nhãn chốt](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611) (trong code: `src/labeling/final_labels.py`); `defect_type` luôn `null`;
- 8 collection: thêm `analysis_results` (kết quả Q1–Q5 của Công việc 12, dashboard đọc);
- dữ liệu vào DB bằng `src/storage/load_db.py` (bước `nap_db` của `python -m src.run`), không còn `seed_db.py` (dữ liệu giả, gỡ 26/11);
- `aggregates` có thêm `n_cmp` (số mention `so_sanh`); các trường `owner_defect_count`, `compare_*_count` không còn (Q3b, Q5 đếm từ `aspect_mentions`).

Trường và kiểu chính xác lấy theo [thiết kế dữ liệu](../0-chung/thiet-ke-du-lieu.md) và `contracts/aspect-mention.schema.json`; khi file này lệch thì theo hai nguồn đó. Các phần về Kafka, Spark dưới đây là thiết kế cho giai đoạn streaming (để sau).

---

## 1. Tổng quan Kiến trúc Lưu trữ (Storage Layer Architecture)

Trong kiến trúc tổng thể của hệ thống:
1. **Tầng Ingestion:** Python Crawler thu thập bình luận YouTube đẩy vào Kafka topic `raw_comments`.
2. **Tầng Stream Processing:** Apache Spark đọc luồng micro-batches, tiền xử lý, chạy mô hình học máy (Spam, Aspect, Sentiment), tính toán sliding windows và phát hiện bất thường vào topic `alerts`.
3. **Tầng Lưu trữ (MongoDB):** Hứng kết quả từ Spark Streaming và cung cấp dữ liệu phục vụ báo cáo.
4. **Tầng Phục vụ (Serving):** FastAPI và Dashboard truy vấn dữ liệu từ MongoDB.

```mermaid
flowchart LR
    subgraph Spark_Stream [Tầng Xử lý Luồng Spark]
        Inference[Mô hình ML / ABSA]
        WindowCalc[Sliding Window Aggregation]
        Anomaly[Phát hiện Bất thường]
    end

    subgraph MongoDB_Collections [CSDL MongoDB: smartphone_analytics]
        M1[(models)]
        M2[(videos)]
        M3[(comments)]
        M4[(aspect_mentions)]
        M5[(aggregates)]
        M6[(alerts)]
        M7[(gold_labels)]
    end

    subgraph Serving [Tầng Phục vụ]
        FastAPI[FastAPI Backend]
        Dash[Executive Dashboard]
    end

    Inference -->|Ghi nhận bình luận| M3
    Inference -->|Bóc tách & gán nhãn| M4
    WindowCalc -->|Ghi số đếm tổng hợp| M5
    Anomaly -->|Ghi log cảnh báo| M6
    M1 -.-> Inference
    M7 -.->|Huấn luyện & Đánh giá| Inference

    M1 --> FastAPI
    M3 --> FastAPI
    M4 --> FastAPI
    M5 --> FastAPI
    M6 --> FastAPI
    FastAPI --> Dash
```

---

## 2. Danh sách 7 Collection Trọng tâm

| STT | Tên Collection | Mục đích nghiệp vụ | Khóa chính (Unique Key) | Index Phụ Trọng yếu |
|:---:|:---|:---|:---|:---|
| 1 | `models` | Danh mục dòng máy, hãng, ngày ra mắt VN, đối thủ cạnh tranh, đời trước | `model_id` | `brand` |
| 2 | `videos` | Danh mục video YouTube được theo dõi, kênh review, thống kê lượt xem | `video_id` | `model`, `published_at` |
| 3 | `comments` | Bản ghi bình luận gốc và phản hồi (reply), metadata và cờ lọc spam | `comment_id` | `video_id`, `model`, `published_at` |
| 4 | `aspect_mentions` | Từng mệnh đề bóc tách kèm nhãn khía cạnh, cảm xúc, đối thủ so sánh (ABSA) | `mention_id` | `target_model` + `aspect` + `published_at` |
| 5 | `aggregates` | Số đếm tổng hợp theo cửa sổ thời gian (khen/chê/trung tính) — **Lưu số đếm, KHÔNG lưu %** | `agg_id` | `target_model` + `aspect` + `week_since_launch` |
| 6 | `alerts` | Lịch sử các đợt phát hiện tiêu cực bất thường (Spike detection) | `alert_id` | `target_model` + `status` + `created_at` |
| 7 | `gold_labels` | Tập dữ liệu mẫu đã được chuyên viên/người gán nhãn kiểm duyệt độc lập (Ground Truth) | `clause_id` / `gold_id` | `split` + `target_model` + `aspects` |

---

## 3. Sơ đồ Quan hệ Thực thể Toàn diện (Entity-Relationship Diagram - ERD)

### 3.1. Sơ đồ ERD Trực quan (Mermaid ERD)

```mermaid
erDiagram
    MODELS ||--o{ VIDEOS : "khởi nguồn ngữ cảnh (model_id -> model)"
    MODELS ||--o{ ASPECT_MENTIONS : "đối tượng đánh giá (model_id -> target_model)"
    MODELS ||--o{ AGGREGATES : "tổng hợp chỉ số (model_id -> target_model)"
    MODELS ||--o{ ALERTS : "giám sát bất thường (model_id -> target_model)"
    MODELS |o--o| MODELS : "đời tiền nhiệm (model_id -> predecessor_id)"
    
    VIDEOS ||--o{ COMMENTS : "chứa bình luận (video_id -> video_id)"
    VIDEOS ||--o{ ASPECT_MENTIONS : "ngữ cảnh gốc (video_id -> video_id)"
    
    COMMENTS ||--o{ ASPECT_MENTIONS : "tách mệnh đề va gán nhãn (comment_id -> comment_id)"
    COMMENTS ||--o{ GOLD_LABELS : "trích mẫu gán nhãn chuẩn (comment_id -> comment_id)"
    
    ASPECT_MENTIONS }o--|| AGGREGATES : "gom số đếm n_pos, n_neg, n_neu (target_model + aspect + week)"

    MODELS {
        string model_id PK "Mã định danh máy (vd: s23u)"
        string title "Tên thương mại đầy đủ"
        string brand "Hãng sản xuất (Samsung, Apple...)"
        date launch_date "Ngày mở bán tại VN"
        string predecessor_id FK "Mã máy đời trước (cho Q4)"
        string_array rivals "Danh sách mã máy đối thủ (cho Q3)"
        string_array aliases "Biệt danh nhận diện tên máy"
        string segment "Phân khúc (flagship, mid...)"
    }
    
    VIDEOS {
        string video_id PK "ID video YouTube / nguồn gốc"
        string model FK "Mã máy video hướng tới"
        string channel_id "ID kênh review"
        string channel_name "Tên kênh review"
        string title "Tiêu đề video"
        datetime published_at "Thời điểm đăng tải"
        string source "Nguồn crawl (youtube...)"
        int comment_count_ingested "Số lượng bình luận đã crawl"
    }
    
    COMMENTS {
        string comment_id PK "ID bình luận gốc"
        string video_id FK "ID video nguồn"
        string parent_id FK "ID bình luận cha (nếu là reply)"
        string model FK "Máy của video (ngữ cảnh)"
        string source "Nguồn dữ liệu (youtube...)"
        string text "Văn bản thô ban đầu"
        string text_norm "Văn bản đã chuẩn hóa"
        string author_hash "Mã băm danh tính tác giả"
        datetime published_at "Thời điểm đăng bình luận"
        int like_count "Lượt thích"
        int reply_count "Lượt phản hồi"
        boolean is_spam "Cờ phát hiện spam"
        string_array spam_reasons "Lý do phát hiện spam"
        boolean is_vietnamese "Cờ nhận diện tiếng Việt"
        object_array clauses "Mảng các mệnh đề đã tách"
        string pipeline_version "Phiên bản tiền xử lý"
    }
    
    ASPECT_MENTIONS {
        string mention_id PK "comment_id#clause_idx#aspect"
        string comment_id FK "ID bình luận nguồn"
        string video_id FK "ID video nguồn"
        int clause_idx "Vị trí mệnh đề trong bình luận"
        string clause_text "Văn bản mệnh đề"
        string source "Nguồn crawl"
        string video_model "Máy của video (ngữ cảnh)"
        string target_model FK "Máy được nhắc (phục vụ Q1-Q5)"
        enum aspect "nhãn chiều 2: 11 khía cạnh + may_chung, hang_nguoi_dung, khac"
        enum sentiment "tich_cuc | tieu_cuc | so_sanh | khong_danh_gia"
        float confidence "Độ tin cậy của nhãn"
        boolean is_owner "Người dùng đã mua/trải nghiệm máy (Q5)"
        string_array purposes "Mục đích của bình luận (chiều 3), null = chưa suy luận"
        enum model_mention "goi_ten_may | chi_hang | khong_nhac"
        enum target_model_source "menh_de | ... | video | khong_ro | nguoi_gan"
        null defect_type "Luôn null ở v3 (chờ bộ loại lỗi)"
        string compare_with FK "Mã máy đối thủ được so sánh (Q3)"
        enum compare_winner "target | other | tie"
        datetime published_at "Thời điểm đăng bình luận"
        int days_since_launch "Số ngày sau ra mắt tại VN"
        enum label_source "rule | llm | model | human"
        string model_version "Phiên bản mô hình gán nhãn"
        int schema_version "Phiên bản schema (= 3)"
    }
    
    AGGREGATES {
        string agg_id PK "target_model#aspect#week#video_id"
        string target_model FK "Mã máy phân tích"
        string aspect "Khía cạnh kỹ thuật"
        int week_since_launch "Tuần sau ra mắt (1..8)"
        string video_id FK "ID video dùng để bootstrap"
        string source "Nguồn thu thập"
        int n_pos "Số đếm khen (KHÔNG lưu %)"
        int n_neg "Số đếm chê (KHÔNG lưu %)"
        int n_neu "Số đếm không đánh giá (KHÔNG lưu %)"
        int n_cmp "Số đếm so sánh (v3)"
        int n_total "Tổng số lượt nhắc"
        int n_opinionated "n_pos + n_neg"
        string label_source "Nguồn nhãn (rule/model)"
        string model_version "Phiên bản mô hình tổng hợp"
        datetime updated_at "Thời điểm tổng hợp"
    }
    
    ALERTS {
        string alert_id PK "Mã định danh cảnh báo"
        string target_model FK "Mã máy cảnh báo"
        string aspect "Khía cạnh bất thường"
        string metric "Chỉ số kích hoạt (neg_sentiment_spike)"
        float value "Giá trị thực tế đo được"
        float baseline "Ngưỡng kỳ vọng bình thường"
        float threshold "Ngưỡng kích hoạt cảnh báo"
        enum severity "info | warning | critical"
        enum status "active | acknowledged | resolved"
        string_array sample_mention_ids "Danh sách mention_id mẫu"
        datetime window_start "Bắt đầu cửa sổ phát hiện"
        datetime window_end "Kết thúc cửa sổ phát hiện"
        datetime created_at "Thời điểm phát hiện"
    }
    
    GOLD_LABELS {
        string gold_id PK "Mã bản ghi ground truth"
        string clause_id "comment_id#clause_idx"
        string comment_id FK "ID bình luận gốc"
        string video_id FK "ID video nguồn"
        string clause_text "Văn bản mệnh đề"
        string annotator "Mã chuyên viên gán nhãn"
        enum label_source "human | llm"
        enum split "train | test (chia theo video_id)"
        object_array aspects "Mảng các cặp [aspect, sentiment]"
        string target_model FK "Mã máy được gán"
        boolean is_owner "Xác nhận người dùng thật"
        enum model_mention "goi_ten_may | chi_hang | khong_nhac"
        string compare_with FK "Máy được so sánh"
        enum compare_winner "target | other | tie"
        datetime labeled_at "Thời điểm gán nhãn"
    }
```

---

### 3.2. Bảng Ma trận Quan hệ Liên Thực thể (Entity Relationship & Cardinality Matrix)

Bảng dưới đây chuẩn hóa các liên kết tham chiếu (Logical Foreign Keys) và bản số giữa các collection trong MongoDB (`analysis_results` thêm 26/11, không có khóa ngoại: mỗi document là kết quả Q1–Q5 của một máy X và một phiên bản nhãn):

| Collection Nguồn (Parent) | Collection Đích (Child) | Khóa Liên kết (Join Key) | Bản số (Cardinality) | Ý nghĩa Nghiệp vụ & Ràng buộc Toàn vẹn |
|:---|:---|:---|:---:|:---|
| `models` | `videos` | `models.model_id` = `videos.model` | $1 : N$ | Mỗi dòng máy được theo dõi qua nhiều video review từ các kênh công nghệ. |
| `models` | `models` | `models.model_id` = `models.predecessor_id` | $1 : 1$ | Liên kết máy đời trước (vd: `s22u` là tiền nhiệm của `s23u`), phục vụ giải quyết **Câu hỏi Q4**. |
| `models` | `aspect_mentions` | `models.model_id` = `aspect_mentions.target_model` | $1 : N$ | Đối tượng máy thực tế được bình luận nhắc tới (tách biệt khỏi máy của video). Trọng tâm của **Q1, Q2, Q4, Q5**. |
| `models` | `aspect_mentions` | `models.model_id` = `aspect_mentions.compare_with` | $1 : N$ | Dòng máy đối thủ được đưa lên bàn cân so sánh trực tiếp, phục vụ **Câu hỏi Q3**. |
| `models` | `aggregates` | `models.model_id` = `aggregates.target_model` | $1 : N$ | Gom số đếm phân tích theo từng dòng máy qua các mốc tuần sau khi ra mắt. |
| `models` | `alerts` | `models.model_id` = `alerts.target_model` | $1 : N$ | Cảnh báo khủng hoảng truyền thông hoặc bùng phát lỗi nghiêm trọng theo máy. |
| `videos` | `comments` | `videos.video_id` = `comments.video_id` | $1 : N$ | Một video chứa danh sách nhiều bình luận gốc và phản hồi (reply). |
| `videos` | `aggregates` | `videos.video_id` = `aggregates.video_id` | $1 : N$ | Giữ `video_id` trong bản ghi tổng hợp để hỗ trợ kỹ thuật **Bootstrap Resampling** tính khoảng tin cậy. |
| `comments` | `comments` | `comments.comment_id` = `comments.parent_id` | $1 : N$ | Quan hệ phân cấp giữa bình luận gốc và chuỗi phản hồi (Replies). |
| `comments` | `aspect_mentions` | `comments.comment_id` = `aspect_mentions.comment_id` | $1 : N$ | Một bình luận tạo nhiều mention: mỗi (máy, nhãn chiều 2) tối đa một lời khen và một lời chê (phương án A). |
| `comments` | `gold_labels` | `comments.comment_id` = `gold_labels.comment_id` | $1 : N$ | Bình luận được trích mẫu vào tập 3.000 mệnh đề gán nhãn chuẩn kiểm thử (Ground Truth). |
| `aspect_mentions`| `aggregates` | `target_model` + `aspect` + `week` | $N : 1$ | Spark / Aggregation Pipeline định kỳ cộng dồn các `aspect_mentions` thành số đếm trong `aggregates`. |

---

### 3.3. Bảng Ma trận Ánh xạ Schema tới 5 Câu hỏi Phân tích (Q1 - Q5 Analytical Mapping Table)

| Câu hỏi | Câu hỏi Cốt lõi | Collections Phục vụ | Điều kiện Lọc chính ($match) | Trường Dữ liệu & Phép tính ($group / Formula) |
|:---|:---|:---|:---|:---|
| **Q1: Tiếp nhận máy X (Tuần 1–4)** | Dòng máy X được đón nhận tốt hay dở trong 4 tuần đầu ra mắt? | `aggregates` | `target_model: "s23u"`, `week_since_launch: {$lte: 4}` | Lấy `n_pos`, `n_neg`. Tính $\text{Net Sentiment} = \frac{n_{pos} - n_{neg}}{n_{pos} + n_{neg}} \times 100$. Kiểm định xu hướng (Mann-Kendall). |
| **Q2: Ưu / Nhược điểm theo Khía cạnh** | Điểm mạnh và điểm yếu nổi bật nhất của dòng máy X là gì? | `aggregates`, `aspect_mentions` | `target_model: "s23u"`, `aspect: {$ne: null}` | Tỷ lệ tích cực từng Aspect $= \frac{n_{pos}}{n_{pos} + n_{neg}}$. Trích xuất câu trích dẫn mẫu có `confidence` cao từ `aspect_mentions`. |
| **Q3: Đối sánh 4 máy & So sánh Trực tiếp** | So với đối thủ cạnh tranh, máy X mạnh hay yếu ở khía cạnh nào? | `aggregates`, `aspect_mentions` | `target_model: "s23u"`, `compare_with: {$ne: null}` | Lập ma trận Aspect $\times$ Model từ `aggregates`. Tỷ lệ thắng đối đầu $= \frac{\text{compare\_win\_count}}{\text{compare\_count}}$ từ `aspect_mentions`. |
| **Q4: Cải thiện Thế hệ (Đời trước $\to$ Đời này)** | Những điểm đời trước bị chê nhiều đã được cải thiện ở đời này chưa? | `models`, `aggregates` | `target_model` $\in$ `{s22u, s23u}` (dựa trên `models.predecessor_id`) | So sánh tỷ lệ tiêu cực $\frac{n_{neg}}{n_{total}}$ giữa 2 đời trên từng Aspect. Kiểm định 2 tỷ lệ độc lập (Z-test có hiệu chỉnh Bonferroni). |
| **Q5: Ưu tiên Khắc phục Lỗi từ Người Dùng Thật** | Người đã mua máy phản ánh lỗi gì nhiều nhất và cần ưu tiên sửa lỗi nào? | `aspect_mentions` | `target_model: "s23u"`, `is_owner: true`, `sentiment: "tieu_cuc"` | Nhóm theo `aspect` (bộ loại lỗi chưa chốt), đếm theo tuần. Khoảng tin cậy và kiểm định do Công việc 12 tính, lưu ở `analysis_results`. |

---

## 4. Chi tiết Cấu trúc Từng Collection (Data Dictionary)

### 4.1. Collection `models` (Danh mục máy)
Lưu thông tin danh mục máy theo yêu cầu của Công việc 2:
```json
{
  "model_id": "s23u",
  "name": "s23u",
  "title": "Samsung Galaxy S23 Ultra",
  "brand": "Samsung",
  "segment": "flagship",
  "launch_date": "2023-02-02",
  "predecessor": "s22u",
  "rivals": [
    { "name": "ip14prm", "title": "iPhone 14 Pro Max", "launch_date": "2022-09-16" },
    { "name": "xiaomi13u", "title": "Xiaomi 13 Ultra", "launch_date": "2023-04-18" },
    { "name": "x90proplus", "title": "Vivo X90 Pro Plus", "launch_date": "2022-11-22" }
  ],
  "aliases": ["Samsung Galaxy S23 Ultra", "S23 Ultra", "s23u", "s23 ultra"],
  "created_at": "2026-10-28T00:00:00Z"
}
```

* **Index:** `{"model_id": 1}` (Unique).

---

### 4.2. Collection `videos` (Metadata video)
```json
{
  "video_id": "9SmOJHZTkC4",
  "model": "s23u",
  "channel_id": "UCEeXA5Tu7n9X5_zkOgGsyww",
  "channel_name": "Vật Vờ Studio",
  "title": "Đánh giá chi tiết Galaxy S23 Ultra sau 1 tuần sử dụng",
  "published_at": "2023-02-09T11:00:00Z",
  "source": "youtube",
  "comment_count_ingested": 1420,
  "created_at": "2026-10-28T00:00:00Z"
}
```

* **Index:** `{"video_id": 1}` (Unique), `{"model": 1, "published_at": -1}`.

---

### 4.3. Collection `comments` (Bình luận làm sạch)
Khớp với `contracts/comment-event.schema.json`:
```json
{
  "comment_id": "UgxA1b2C3d4E5f6G7h4AaABAg",
  "video_id": "9SmOJHZTkC4",
  "parent_id": null,
  "parent_text": null,
  "model": "s23u",
  "source": "youtube",
  "text": "Pin trâu hơn đời trước rõ rệt, dùng cả ngày không lo sạc.",
  "text_norm": "pin trâu hơn đời trước rõ rệt dùng cả ngày không lo sạc",
  "author_hash": "a1b2c3d4e5f6...",
  "published_at": "2023-02-10T14:20:00Z",
  "like_count": 45,
  "reply_count": 3,
  "is_spam": false,
  "spam_reasons": [],
  "is_vietnamese": true,
  "clause_count": 2,
  "is_owner": true,
  "label_source": "rule",
  "model_version": "v1.0.0",
  "ingested_at": "2026-10-28T00:00:00Z"
}
```

* **Index:** `{"comment_id": 1}` (Unique), `{"model": 1, "published_at": 1}`, `{"video_id": 1}`.

---

### 4.4. Collection `aspect_mentions` (Mệnh đề & Khía cạnh — Hạt nhân của ABSA)
Mỗi document tương ứng với một mệnh đề hoặc một lượt nhắc khía cạnh cụ thể, giải quyết bài toán: một bình luận có thể vừa khen khía cạnh này, vừa chê khía cạnh khác.
Ví dụ theo `contracts/aspect-mention.schema.json` (schema_version = 3):
```json
{
  "mention_id": "UgxA1b2C3d4E5f6G7h4AaABAg#1#pin_sac",
  "comment_id": "UgxA1b2C3d4E5f6G7h4AaABAg",
  "parent_id": null,
  "video_id": "9SmOJHZTkC4",
  "clause_idx": 1,
  "clause_text": "Pin trâu hơn đời trước rõ rệt",
  "source": "youtube",
  "video_model": "s23u",
  "target_model": "s23u",
  "author_hash": "069722f199073a1f8b0223df1aa448cd79e0695bd87f82fd737f9f892520bdcb",
  "author_is_creator": false,
  "aspect": "pin_sac",
  "sentiment": "so_sanh",
  "confidence": null,
  "is_owner": true,
  "purposes": null,
  "model_mention": "goi_ten_may",
  "target_model_source": "video",
  "defect_type": null,
  "compare_with": "s22u",
  "compare_winner": "target",
  "published_at": "2023-02-10T14:20:00Z",
  "days_since_launch": 8,
  "label_source": "rule",
  "model_version": "rule-v1.1",
  "schema_version": 3
}
```

* **Nhãn chiều 2 (`aspect`):** 11 khía cạnh `pin_sac`, `man_hinh`, `hieu_nang` (gồm nóng máy), `camera`, `thiet_ke`, `do_ben`, `phan_mem`, `phan_cung_khac` (gồm loa, mic, phụ kiện), `gia`, `mua_ban`, `bao_hanh_sua_chua`; thêm `may_chung`, `hang_nguoi_dung`, `khac`. Định nghĩa ở [thiết kế dữ liệu](../0-chung/thiet-ke-du-lieu.md#danh-mục-mã).

* **Index:**
  * `{"mention_id": 1}` (Unique).
  * `{"target_model": 1, "aspect": 1, "published_at": 1}` (Tối ưu query Q1, Q2, Q4).
  * `{"target_model": 1, "compare_with": 1}` (Tối ưu query đối đầu trực tiếp Q3).
  * `{"target_model": 1, "is_owner": 1, "sentiment": 1}` (Tối ưu query lời chê của người đã dùng máy, Q5).

---

### 4.5. Collection `aggregates` (Số liệu tổng hợp)

> [!IMPORTANT]
> **YÊU CẦU BẮT BUỘC:** `aggregates` **chỉ lưu SỐ ĐẾM (counts: n_pos, n_neg, n_neu, n_cmp)**, tuyệt đối **KHÔNG lưu phần trăm (%)**.  
> **Lý do kỹ thuật:** Phần trăm không có tính chất cộng gộp (non-additive). Nếu lưu sẵn `75%` cho Tuần 1 (n=100) và `50%` cho Tuần 2 (n=10), ta không thể cộng trung bình `(75 + 50)/2 = 62.5%` vì thực tế `(75 + 5) / 110 = 72.7%`. Việc lưu số đếm cho phép dashboard hay API tùy ý `SUM()` trên mọi chiều (thời gian, model, aspect) một cách chính xác tuyệt đối, sau đó tính tỷ lệ % tại thời điểm truy vấn.

```json
{
  "agg_id": "agg_<sha256 của khóa (target_model, aspect, week_since_launch, video_id, source, model_version)>",
  "target_model": "s23u",
  "aspect": "pin_sac",
  "week_since_launch": 1,
  "video_id": "9SmOJHZTkC4",
  "source": "youtube",
  "model_version": "rule-v1.1",
  "n_pos": 352,
  "n_neg": 108,
  "n_neu": 85,
  "n_cmp": 12,
  "n_total": 557,
  "n_opinionated": 460,
  "updated_at": "2026-11-26T00:00:00Z"
}
```

Số trong ví dụ là số minh họa định dạng. `n_pos`, `n_neg`, `n_neu`, `n_cmp` là số mention `tich_cuc`, `tieu_cuc`, `khong_danh_gia`, `so_sanh`.

* **Công thức dẫn xuất tại tầng API/Dashboard:**
  * $\% \text{ Tích cực (Khen)} = \frac{n_{pos}}{n_{pos} + n_{neg}} \times 100$
  * $\% \text{ Tiêu cực (Chê)} = \frac{n_{neg}}{n_{pos} + n_{neg}} \times 100$
  * $\text{Net Sentiment} = \% \text{ Khen} - \% \text{ Chê} = \frac{n_{pos} - n_{neg}}{n_{pos} + n_{neg}} \times 100$

* **Index:** `{"agg_id": 1}` (Unique), `{"target_model": 1, "aspect": 1, "week_since_launch": 1}`.

---

### 4.6. Collection `alerts` (Lịch sử cảnh báo khủng hoảng)
```json
{
  "alert_id": "ALT_20230214_s23u_hieu_nang",
  "target_model": "s23u",
  "aspect": "hieu_nang",
  "metric": "neg_sentiment_spike",
  "value": 59.4,
  "baseline": 25.0,
  "threshold": 45.0,
  "severity": "warning",
  "status": "active",
  "sample_mention_ids": ["UgxA1#1#hieu_nang", "UgxB2#2#hieu_nang"],
  "window_start": "2023-02-14T08:00:00Z",
  "window_end": "2023-02-14T09:00:00Z",
  "created_at": "2023-02-14T09:05:00Z"
}
```

* **Index:** `{"alert_id": 1}` (Unique), `{"target_model": 1, "status": 1, "created_at": -1}`.

---

### 4.7. Collection `gold_labels` (Tập dữ liệu chuẩn phục vụ kiểm thử)
Lưu trữ tập 3.000 mệnh đề được chuyên viên gán nhãn độc lập (Công việc STT 1) để tính độ đồng thuận Cohen's Kappa và benchmark mô hình:
```json
{
  "clause_id": "UgxA1b2C3d4E5f6G7h4AaABAg#1",
  "comment_id": "UgxA1b2C3d4E5f6G7h4AaABAg",
  "video_id": "9SmOJHZTkC4",
  "clause_text": "Pin trâu hơn đời trước rõ rệt",
  "annotator": "Lâm",
  "label_source": "human",
  "split": "test",
  "aspects": [
    {
      "aspect": "pin_sac",
      "sentiment": "so_sanh"
    }
  ],
  "target_model": "s23u",
  "is_owner": true,
  "model_mention": "goi_ten_may",
  "compare_with": "s22u",
  "compare_winner": "target",
  "guideline_version": "huong-dan-gan-nhan-chinh-thuc 2026-11-26",
  "labeled_at": "2026-10-28T00:00:00Z"
}
```

* **Index:** `{"clause_id": 1}` (Unique), `{"split": 1, "target_model": 1}`.

---

### 4.8. Collection `analysis_results` (kết quả Q1–Q5, thêm 26/11)
Mỗi document là toàn bộ `business_questions.json` của Công việc 12 cho một máy X và một phiên bản nhãn. Khóa `analysis_id = "<target_model>|<model_version>"`; `load_db.py` ghi kèm `loaded_at` và SHA-256 của file nguồn. Dashboard chỉ gắn khoảng tin cậy, kiểm định vào số liệu khi số đếm trong document khớp số đếm trong `aggregates`.

* **Index:** `{"analysis_id": 1}` (Unique).

---

## 5. Chiến lược Idempotency & Quản lý Phiên bản

1. **Khóa chống trùng (Upsert Idempotent):**
   * Mọi thao tác ghi từ Kafka/Spark đều sử dụng toán tử `updateOne(filter, update, upsert=True)` dựa trên khóa chính tự sinh xác định (`comment_id`, `mention_id`, `agg_id`). Dữ liệu phát lại (replay) bao nhiêu lần cũng không gây tăng khống số liệu.
2. **Metadata Nguồn gốc & Phiên bản:**
   * Mọi document gán nhãn đều có bắt buộc:
     * `label_source`: `"rule"`, `"llm"`, `"model"`, hoặc `"human"`.
     * `model_version`: Định danh phiên bản mô hình (vd: `"rule-v1.1"`, `"phobert_v1"`).
   * Giúp hệ thống dễ dàng so sánh hiệu năng giữa các phiên bản mô hình khác nhau trên cùng một tập dữ liệu.


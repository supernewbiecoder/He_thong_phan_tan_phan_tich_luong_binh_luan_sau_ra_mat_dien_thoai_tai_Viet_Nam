# Vòng đời mô hình học máy

> Mục đích: mô tả nguồn dữ liệu, cách huấn luyện Teacher, đánh giá và cách đưa mô hình vào luồng YouTube; cập nhật lần cuối: 2026-10-21.

## 1. Phân biệt dữ liệu huấn luyện và dữ liệu vận hành

Hệ thống có hai nguồn dữ liệu với hai vai trò khác nhau:

| Nguồn | Vai trò chính | Có dùng train Teacher trực tiếp không? |
|---|---|---|
| Bình luận tổng hợp từ Internet/dataset bên ngoài | EDA, gán nhãn, huấn luyện và đánh giá mô hình ban đầu | Có, sau khi đã kiểm tra và gán nhãn |
| Bình luận YouTube từ `src/ingest/data/raw/comments.jsonl` | Test tích hợp, đánh giá khác miền sau khi gán nhãn, inference production và cảnh báo | Không dùng trực tiếp khi chưa có nhãn |

`comments.jsonl` là vùng **raw landing/archive** dạng append-only. Crawler ghi thêm comment sau mỗi trang API thành công; file này không phải dataset train đã chuẩn hóa.

## 2. Luồng huấn luyện Teacher

```text
Dataset bình luận bên ngoài
        |
        v
EDA và kiểm tra chất lượng
        |
        v
Chuẩn hóa riêng cho training + gán nhãn
        |
        v
Train/validation/test theo video hoặc nguồn
        |
        v
Teacher: spam + aspect + sentiment
        |
        v
Đánh giá trên test độc lập
```

### 2.1 Chuẩn bị dữ liệu

1. Lưu dữ liệu bên ngoài vào vùng riêng, không trộn với `src/ingest/data/raw`.
2. Kiểm tra schema, encoding, dòng JSON lỗi, thiếu text, trùng ID và phân bố nhãn.
3. Chọn phạm vi nhãn:
   - **Spam:** `spam`/`not_spam`.
   - **Aspect:** multi-label cho 9 khía cạnh của dự án.
   - **Sentiment:** `positive`/`negative`/`neutral`.
4. Gán nhãn bằng human labeling hoặc quy trình weak labeling rồi kiểm tra thủ công một mẫu. Nhãn luật chỉ là nhãn yếu, không được coi là ground truth nếu chưa xác nhận.
5. Chuẩn hóa text cho training trong một bước có version. Không sửa file raw gốc.

### 2.2 Chia tập dữ liệu

Không chia ngẫu nhiên từng comment nếu nhiều comment cùng một video, vì như vậy có thể làm rò rỉ chủ đề và văn phong giữa train/test. Ưu tiên:

- chia theo `video_id` nếu có;
- nếu không có `video_id`, chia theo nguồn hoặc theo thời gian;
- giữ test set độc lập và không dùng để chọn siêu tham số.

Ví dụ cấu trúc:

```text
data/
├── external/
│   └── comments_raw.jsonl
└── training/
    ├── teacher_train.jsonl
    ├── teacher_valid.jsonl
    ├── teacher_test.jsonl
    └── youtube_test_labeled.jsonl
```

`youtube_test_labeled.jsonl` là một mẫu YouTube được gán nhãn thủ công để đo khả năng chuyển miền; không lấy toàn bộ comment YouTube chưa nhãn làm test có ground truth.

### 2.3 Mô hình Teacher

Teacher được train riêng cho từng nhiệm vụ hoặc theo pipeline nhiều tầng:

```text
text
  └─> spam classifier
        └─ nếu không phải spam
              ├─ aspect multi-label classifier
              └─ sentiment classifier
```

Baseline có thể dùng TF-IDF kết hợp Linear SVM/Logistic Regression/Naive Bayes. Việc chọn mô hình cuối cùng phải dựa trên validation và báo cáo trên test, không chọn theo một vài ví dụ dự đoán.

Tối thiểu cần lưu:

- phiên bản dữ liệu và snapshot;
- cách tiền xử lý/tokenizer;
- danh sách nhãn;
- siêu tham số;
- metric theo từng nhiệm vụ;
- model artifact và checksum;
- ngày huấn luyện.

Metric nên báo cáo gồm precision, recall, F1 (macro và theo nhãn); với aspect multi-label nên bổ sung micro-F1 và exact-match nếu phù hợp. Không dùng accuracy đơn lẻ khi nhãn mất cân bằng.

## 3. Dữ liệu YouTube sau khi crawler chạy

```text
YouTube API
    |
    v
src/ingest/data/raw/comments.jsonl
    |
    +--> Kafka raw_comments
    |
    v
Spark: validation + preprocessing
    |
    v
Teacher/Student inference
    |
    +--> MongoDB comments
    +--> aggregates
    +--> Kafka alerts
```

Khi có comment mới:

1. Crawler giữ bản raw và gửi event vào `raw_comments` nếu Kafka được bật.
2. Spark kiểm tra schema, deduplicate theo `comment_id`, chuẩn hóa text và tách mệnh đề.
3. Mô hình được nạp theo version đã đăng ký.
4. Pipeline ghi nhãn dự đoán cùng `model_version`, `predicted_at` và confidence/probability nếu mô hình cung cấp.
5. Kết quả được dùng để tính aggregate và cảnh báo; không ghi đè raw archive bằng text đã làm sạch.

## 4. Teacher–Student

Nếu dự án dùng knowledge distillation:

```text
External labeled data
        |
        v
Train Teacher
        |
        +--> nhãn chuẩn để đánh giá
        |
        v
YouTube raw chưa nhãn
        |
        v
Teacher pseudo-label + confidence filtering
        |
        v
Human review mẫu khó / mẫu đại diện
        |
        v
Train hoặc fine-tune Student
        |
        v
Student inference trong Spark
```

Student chỉ được đưa vào production sau khi so sánh với Teacher trên:

- `teacher_test.jsonl`;
- `youtube_test_labeled.jsonl`;
- latency/throughput thực tế;
- độ ổn định theo model điện thoại và theo thời gian.

Pseudo-label từ Teacher không được trộn vào test set. Các comment có confidence thấp nên đưa vào hàng đợi human review thay vì tự động coi là nhãn đúng.

## 5. Nguyên tắc chống rò rỉ dữ liệu

- Không train trên comment YouTube đã dùng để báo cáo kết quả production.
- Không dùng `youtube_test_labeled.jsonl` để chọn hyperparameter.
- Không chia comment cùng một video vào cả train và test.
- Không coi output dự đoán của Teacher là ground truth nếu chưa kiểm tra.
- Raw archive và dataset đã xử lý phải có đường dẫn, phiên bản và thời điểm snapshot riêng.
- Khi mô hình hoặc preprocessing đổi, tăng `model_version` và chạy lại đánh giá.

## 6. Liên kết với các thành phần hệ thống

- Crawler và archive raw: [`src/ingest/README.md`](../src/ingest/README.md)
- Luồng Kafka/Spark/MongoDB: [`pipeline.md`](./pipeline.md)
- Phân tích EDA snapshot YouTube: [`Phan_tich_binh_luan_tong_hop.ipynb`](../src/processing/Phan_tich_binh_luan_tong_hop.ipynb)

# Đường ống dữ liệu (Data Pipeline)

> Mục đích: Mô tả các bước thu thập, xử lý, lưu trữ và phục vụ dữ liệu: chuỗi chạy theo lô mỗi ngày (đang làm) và phần streaming (để sau); cập nhật lần cuối: 2026-11-26.

## 1. Tổng quan

| Giai đoạn | Trạng thái | Mục tiêu |
|---|---|---|
| **1. Theo lô, mỗi ngày một lần** | **Đang làm** (chốt 20/11) | Trả lời Q1–Q5 trên dữ liệu đã crawl; mỗi ngày chạy lại cả chuỗi để có số mới |
| **2. Streaming** | Để sau, khi giai đoạn 1 xong | Xử lý gần thời gian thực và cảnh báo bằng Kafka/Spark |

Cả hai giai đoạn dùng **cùng** contract, cùng các bảng trong [thiết kế dữ liệu](thiet-ke-du-lieu.md) và cùng code xử lý từng bình luận. Giai đoạn 2 chỉ thay cách dữ liệu chạy qua các bước.

**Đơn vị phân tích là cả bình luận** (phương án A, chốt 20/11): mô hình đọc cả bình luận, đếm theo (bình luận, máy, nhãn chiều 2 của [bộ nhãn chốt](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611)). Lý do: [muc-tieu.md mục 4](muc-tieu.md#4-phạm-vi) và [đặc tả suy luận mục 2](../4-mo-hinh/dac-ta-suy-luan.md#2-đơn-vị-và-quy-tắc-gộp).

## 2. Giai đoạn 1: theo lô

```text
1. Thu thập     YouTube API → crawler → src/ingest/data/raw/comments.jsonl          ✅ src/ingest (chạy riêng, theo lịch của crawler)
2. Tiền xử lý   làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ tiếng Việt và spam
                → data/processed/comments.jsonl                                       ✅ src/processing
3. Suy luận     theo cả bình luận: khía cạnh + thái độ + máy được nhắc
                + đã dùng máy → data/aspect_mentions.jsonl (contract v3)              ⚠️ src/models/run.py: mới có luật mốc rule-v1.1
4. Tổng hợp     aspect_mentions → aggregates (số đếm theo máy, khía cạnh, tuần, video) ✅ src/analysis (Công việc 12)
5. Phân tích    Q1–Q5: tỷ lệ, khoảng tin cậy, kiểm định                               ✅ src/analysis (Công việc 12)
6. Nạp DB       models, comments, aspect_mentions, aggregates, analysis_results       ✅ ⚠️ src/storage (bước nap_db, contract v3; chưa nạp videos)
7. Hiển thị     API + dashboard 4 tab đọc MongoDB                                      ✅ src/serving (Công việc 13; số liệu minh họa); báo cáo ❌ Công việc 14
```

Bước 2–5 (và bước 6 khi gọi rõ) chạy bằng **một lệnh**, từ gốc repo:

```powershell
.\.venv\Scripts\python.exe -m src.run                   # cả chuỗi: tiền xử lý → suy luận → aggregates, Q1–Q5
.\.venv\Scripts\python.exe -m src.run --tu suy_luan     # file tầng 2 đã có, chỉ chạy lại từ suy luận
.\.venv\Scripts\python.exe -m src.run --den suy_luan    # dừng trước bước phân tích
.\.venv\Scripts\python.exe -m src.run --den nap_db      # thêm bước nạp MongoDB (MONGO_URI, MONGO_DB) cho dashboard
.\.venv\Scripts\python.exe -m src.serving.api.app --port 8000   # mở dashboard ở http://localhost:8000/
```

Mặc định lệnh dừng sau bước phân tích, để máy không có MongoDB vẫn chạy được. Bước `nap_db` cần MongoDB đang chạy ([hướng dẫn dashboard](../7-hien-thi/huong-dan.md)).

- Mỗi bước ghi đè kết quả lần trước, không cộng dồn: chạy lại bao nhiêu lần trên cùng dữ liệu cũng ra cùng kết quả.
- Mỗi bước ghi manifest (số dòng, SHA-256, phiên bản code) cạnh file ra.
- Cần cài `src/analysis/requirements.txt` (PyYAML, jsonschema, tzdata, numpy) cho bước 3–5.

### 2.1 Thu thập

Crawler đi qua playlist uploads của các kênh trong `config/pipeline.yaml`, lọc video theo tiêu đề và ngày đăng, rồi cào bình luận gốc và reply trong cửa sổ 4 tuần sau `launch_date`. Crawler có lịch riêng (`schedule` trong `config/pipeline.yaml`); chuỗi theo lô chỉ đọc file raw nó đã ghi. Chi tiết: [docs/1-thu-thap/huong-dan.md](../1-thu-thap/huong-dan.md).

Lưu ý: trường `model` của bình luận là **máy của video**, không phải máy được nhắc. Máy được nhắc xác định ở bước 3.

### 2.2 Tiền xử lý

Làm sạch (`text_clean`), chuẩn hóa (`text_norm`, `emojis`), tách mệnh đề (`clauses`), gắn cờ (`is_vietnamese`, `is_spam`, `spam_reasons`). Luật: [đặc tả tầng 2](../2-tien-xu-ly/dac-ta.md). Lệnh riêng: `python -m src.processing.run`.

### 2.3 Suy luận

Mỗi bình luận không rỗng, không spam, là tiếng Việt: tìm khía cạnh, thái độ, máy được nhắc (xét cả bình luận, rồi comment cha, rồi máy của video; ghi nguồn ở `target_model_source`), chiều 6 (`model_mention`), đã dùng máy. Gộp theo (máy, khía cạnh), mỗi dòng `aspect_mentions` ghi kèm mệnh đề làm bằng chứng. Loại lỗi chưa có bộ mã nên luôn `null`. Hiện là luật mốc `rule-v1.1`: số liệu ra là **số liệu minh họa** cho tới khi có mô hình đã đánh giá trên nhãn người. Đặc tả: [dac-ta-suy-luan.md](../4-mo-hinh/dac-ta-suy-luan.md). Lệnh riêng: `python -m src.models.run`.

### 2.4 Tổng hợp và phân tích

Code Công việc 12: kiểm từng mention với contract và file bình luận, tính `aggregates`, trả lời Q1–Q5 (bootstrap theo video, Holm). Bộ 4 máy đọc ở `config/analysis.yaml`: **còn là bộ cũ** (S23U…), phải đổi theo Công việc 2 thì bước này mới có mention để tính. Hướng dẫn: [docs/5-phan-tich/huong-dan.md](../5-phan-tich/huong-dan.md). `days_since_launch` tính theo `launch_date` của `target_model`.

### 2.5 Nạp DB và hiển thị

Bước `nap_db` tạo collection và index (`src/storage/init_db.py`), rồi nạp danh mục máy, bình luận tầng 2 (bỏ `author_name`), mention (kiểm theo contract v3), aggregates và `business_questions.json` (`src/storage/load_db.py`). Mọi bản ghi upsert theo khóa nên nạp lại không sinh bản trùng. Dashboard (`src/serving`) chỉ đọc DB; chỗ nào nhãn là luật hay LLM thì ghi "số liệu minh họa". Chi tiết: [docs/6-luu-tru/huong-dan.md](../6-luu-tru/huong-dan.md), [docs/7-hien-thi/huong-dan.md](../7-hien-thi/huong-dan.md).

### 2.6 Chạy mỗi ngày

Trên Windows, đặt lịch bằng Task Scheduler, ví dụ 7 giờ sáng (sau giờ crawler tìm video mới ở `schedule.discover_cron_hour`):

```powershell
schtasks /Create /SC DAILY /ST 07:00 /TN "khdl-chuoi-theo-lo" `
  /TR "cmd /c cd /d <gốc repo> && .venv\Scripts\python.exe -m src.run >> data\chuoi-theo-lo.log 2>&1"
```

Sau mỗi lần chạy, xem log và manifest trước khi dùng số. Số trong báo cáo chính thức phải ghi rõ ngày chạy và SHA-256 của file vào.

## 3. Giai đoạn 2: streaming (để sau)

Chỉ làm khi giai đoạn 1 xong. Phương án A hợp với streaming: mỗi tin nhắn Kafka là một bình luận, xử lý độc lập; khóa upsert `mention_id` không đổi khi chạy lại. Ba điều kiện phải giữ khi làm:

1. **LLM không nằm trên đường chạy liên tục.** LLM chỉ gán nhãn offline. Luồng chạy dùng mô hình đã huấn luyện, khóa bằng `model_version`.
2. **Mô hình chạy theo lô nhỏ:** mỗi worker nạp mô hình một lần, suy luận cả micro-batch. Đo độ trễ và consumer lag ở tốc độ phát lại 1x và 10x.
3. **Thống kê không chạy trong luồng:** bootstrap, kiểm định, Holm chạy theo lô định kỳ trên `aggregates` (đã có khóa `video_id`).

```text
replay (src/ingest) → Kafka raw_comments (key = video_id)
   → Spark Structured Streaming: kiểm tra schema, dedupe theo comment_id,
     tiền xử lý, suy luận (nạp mô hình theo model_version)
   → upsert aspect_mentions, aggregates
   → cửa sổ trượt (vd 1 giờ, bước 10 phút) trên số mention `tieu_cuc` theo (target_model, aspect)
   → vượt baseline → Kafka alerts → collection alerts
```

- **Replay** phát lại dữ liệu đã crawl theo `published_at` với hệ số tốc độ (`--speed 10`), `--strip-stats` để bỏ like/reply "của tương lai".
- **Ngưỡng cảnh báo** tham khảo: tỷ lệ chê trong cửa sổ vượt trung bình + 2 độ lệch chuẩn của 24 giờ trước; phải hiệu chỉnh trên dữ liệu thật và chỉ áp dụng khi cửa sổ đủ số mention.
- **Idempotent:** mọi sink upsert theo `comment_id`/`mention_id`/khóa aggregate để replay hoặc retry không tạo bản trùng. Bình luận bị sửa: xóa mọi mention của `comment_id` đó rồi ghi lại.
- **Cờ Q6** (cùng câu từ nhiều tài khoản, đăng dồn) cần cửa sổ trên nhiều bình luận, có thể tới sau khi bình luận đã được tính: lọc lúc truy vấn, không lọc lúc ghi.

Hạ tầng dev hiện có: Kafka 1 node ([docker-compose.dev.yml](../../src/ingest/docker-compose.dev.yml)). Cụm nhiều broker, Spark, MongoDB và các kịch bản trong [hướng dẫn sự cố](huong-dan-su-co-streaming.md) **chưa được dựng**.

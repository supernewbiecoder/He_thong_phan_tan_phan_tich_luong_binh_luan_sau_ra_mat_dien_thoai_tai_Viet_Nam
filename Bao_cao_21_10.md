# BÁO CÁO CÔNG VIỆC

## Phân tích bình luận sau ra mắt điện thoại tại Việt Nam

**Ngày báo cáo:** 21/10/2026 · **Cập nhật:** 28/10/2026  
**Nguồn dữ liệu:** YouTube Data API v3  
**Phạm vi:** Bình luận tiếng Việt trên YouTube, gồm comment gốc và reply

> **Thay đổi so với bản 21/10:** câu hỏi nghiệp vụ chuyển sang 5 câu Q1–Q5; kiến trúc tách thành Giai đoạn 1 xử lý theo lô (bắt buộc) và Giai đoạn 2 streaming (tùy chọn); bổ sung trường máy được nhắc (`target_model`) và collection `aspect_mentions`; sửa mô tả trường `model`; mục tiến độ ghi đúng trạng thái thực tế.

## 1. Tóm tắt

Dự án theo dõi phản hồi của người dùng sau khi một hãng điện thoại ra mắt máy mới (máy X) tại Việt Nam. Thay vì đọc thủ công hàng trăm video và hàng nghìn bình luận, nhóm thu thập bình luận YouTube, loại spam, tách thành mệnh đề, gán nhãn khía cạnh – cảm xúc – máy được nhắc, rồi trả lời 5 câu hỏi nghiệp vụ bằng số liệu có kiểm định thống kê.

Đầu ra chính là báo cáo và dashboard so sánh X với đời trước và hai đối thủ trong 4 tuần đầu sau ra mắt:

- Mức độ đón nhận theo tuần (net sentiment).
- Ưu, nhược điểm của X theo từng khía cạnh, kèm bình luận thật.
- So sánh từng khía cạnh với đối thủ và với đời trước.
- Danh sách lỗi kỹ thuật do người đã dùng máy báo, có mức ưu tiên.
- Tỷ lệ bình luận spam/quảng cáo đã bị loại.

## 2. Phát biểu bài toán

Trong vài tuần đầu sau ngày ra mắt, các video review, unbox và so sánh xuất hiện liên tục, kéo theo lượng lớn bình luận và reply, trong đó có spam, quảng cáo, seeding. Nếu tính thẳng trên dữ liệu thô, các bình luận này làm sai lệch đánh giá về sản phẩm. Ngoài ra, bình luận dưới video của máy X thường nói về cả máy khác, nên phải xác định đúng máy được nhắc trong từng mệnh đề.

Năm câu hỏi nghiệp vụ (đặc tả đầy đủ tại [`docs/EDA_requirement.md`](docs/EDA_requirement.md)):

| # | Câu hỏi | Dùng để |
|---|---|---|
| Q1 | X được đón nhận tốt hay dở? | Đánh giá tổng thể đợt ra mắt |
| Q2 | Ưu điểm và nhược điểm của X là gì? | Chọn thông điệp marketing |
| Q3 | So với đối thủ, X mạnh/yếu ở đâu? | Định vị cạnh tranh |
| Q4 | Đời trước bị chê gì, đời này đã sửa chưa? | Đánh giá cải tiến sản phẩm |
| Q5 | Lỗi gì cần sửa, ưu tiên cái nào? | Ưu tiên cho kỹ thuật, CSKH |

Yêu cầu đi kèm: spam phải bị loại trước khi tính mọi số liệu, và tỷ lệ spam được báo cáo riêng. Phát hiện bất thường theo thời gian thực là phần mở rộng tùy chọn (Giai đoạn 2).

### 2.1. Đầu vào

- Bình luận từ YouTube Data API v3, gồm comment gốc và reply (reply có thêm `parent_text`).
- Metadata video: kênh, tiêu đề, ngày đăng, máy của video, số view/like/comment.
- Danh mục máy: ngày ra mắt, đời trước, đối thủ ([`config/pipeline.yaml`](config/pipeline.yaml)).
- Dataset tiếng Việt đã gán nhãn từ bên ngoài (UIT-ViSFD…) để hỗ trợ huấn luyện.

### 2.2. Đầu ra

- Bình luận đã chuẩn hóa, gắn cờ spam, tách mệnh đề (`comments`).
- Mỗi mệnh đề × khía cạnh kèm cảm xúc và máy được nhắc (`aspect_mentions`).
- Số đếm tổng hợp theo máy, khía cạnh, tuần (`aggregates`).
- Kết quả Q1–Q5 có khoảng tin cậy và kiểm định; dashboard và báo cáo.
- (Tùy chọn) cảnh báo bất thường (`alerts`).

### 2.3. Ngoài phạm vi

- Không xử lý hình ảnh, âm thanh hoặc nội dung video.
- Không phân tích bình luận không phải tiếng Việt.
- Không lưu tên thật của tác giả; chỉ lưu mã băm ẩn danh.
- Nguồn ngoài YouTube: chưa thu thập; đang khảo sát trang đánh giá sản phẩm của các nhà bán lẻ để bổ sung bình luận từ người đã mua (xem [`docs/roadmap.md`](docs/roadmap.md)).

## 3. Kiến trúc hệ thống

Hệ thống gồm bốn tầng (thu thập, xử lý, lưu trữ, phân tích & hiển thị) và một khối huấn luyện offline. Dự án làm theo hai giai đoạn dùng chung định dạng dữ liệu:

- **Giai đoạn 1 – xử lý theo lô (bắt buộc):** đọc archive JSONL, xử lý bằng Python, ghi vào cơ sở dữ liệu, trả lời Q1–Q5.
- **Giai đoạn 2 – streaming (tùy chọn):** phát lại dữ liệu qua Kafka, xử lý bằng Spark Structured Streaming, phát hiện bất thường theo cửa sổ trượt.

![Sơ đồ kiến trúc hệ thống](docs/architecture.svg)

_Hình 1. Kiến trúc hệ thống, dựng từ [`docs/architecture.mmd`](docs/architecture.mmd). Nét liền: Giai đoạn 1. Nét đứt, màu xám: Giai đoạn 2 (tùy chọn)._

### 3.1. Tầng thu thập

Python Crawler ([`src/ingest`](src/ingest/README.md)) đi qua playlist uploads của các kênh công nghệ, lọc video theo tên máy trong tiêu đề và ngày đăng, rồi cào comment gốc và reply trong cửa sổ 4 tuần sau ngày ra mắt của máy. Mỗi trang kết quả được ghi nối vào archive JSONL; khi có cấu hình Kafka, bản ghi được gửi vào topic `raw_comments` trước rồi mới ghi archive.

Các cơ chế đã có:
- Đếm quota trước mỗi request, 3 lớp chặn (ngưỡng ngày, ngân sách mỗi lần chạy, số lần `search.list`).
- Lưu `page_token` sau mỗi trang để dừng giữa chừng vẫn cào tiếp được.
- Chống trùng bằng bảng `seen` trong SQLite: mỗi `comment_id` chỉ được ghi một lần.
- Ẩn danh tác giả bằng `author_hash` = SHA-256(salt + channel ID).

**Replay** đọc lại archive theo thứ tự `published_at` và gửi vào Kafka với hệ số tốc độ tùy chọn; `ingested_at` được ghi lại tại thời điểm phát để đo độ trễ, `--strip-stats` bỏ like/reply "của tương lai" khi demo.

### 3.2. Tầng xử lý

1. **Tiền xử lý:** lọc spam (hiện bằng luật), nhận diện tiếng Việt, chuẩn hóa `text_norm`, tách mệnh đề.
2. **Suy luận:** với mỗi mệnh đề không spam, dự đoán các khía cạnh được nhắc, cảm xúc cho từng khía cạnh và máy được nhắc (`target_model`). Mô hình được nạp theo `model_version`.
3. **Tổng hợp:** đếm số mention khen/chê/trung tính theo máy × khía cạnh × tuần kể từ ra mắt × video.
4. **(Tùy chọn) Phát hiện bất thường:** cửa sổ trượt 1 giờ, bước 10 phút trên số mention tiêu cực theo (máy, khía cạnh); cảnh báo khi vượt trung bình + 2 độ lệch chuẩn của 24 giờ trước. Ngưỡng cần hiệu chỉnh trên dữ liệu thật.

Ở Giai đoạn 2, các bước 1–4 chạy trong Spark Structured Streaming đọc micro-batch từ `raw_comments`, có thêm kiểm tra schema và dedupe theo `comment_id`.

### 3.3. Huấn luyện offline

Mô hình học từ `gold_labels` (mẫu mệnh đề YouTube gán tay, có hỗ trợ AI cho phần train) và dataset ngoài đã ánh xạ về bộ khía cạnh của dự án. Tập train/test chia theo `video_id`; tập test chỉ gồm nhãn người gán. Chi tiết: [`docs/ml-training.md`](docs/ml-training.md).

### 3.4. Tầng lưu trữ

MongoDB gồm các collection (thiết kế chi tiết: [`docs/data-model.md`](docs/data-model.md)):

| Collection | Nội dung |
|---|---|
| `models`, `videos` | Danh mục máy (ngày ra mắt, đời trước, đối thủ) và metadata video |
| `comments` | Bình luận raw + kết quả tiền xử lý |
| `aspect_mentions` | Mỗi dòng một mệnh đề × khía cạnh, kèm cảm xúc, máy được nhắc, nguồn nhãn |
| `aggregates` | Số đếm khen/chê/trung tính đã gom sẵn |
| `alerts` | (Tùy chọn) lịch sử cảnh báo |
| `gold_labels` | Nhãn dùng để huấn luyện và đánh giá |

Mọi thao tác ghi là upsert theo khóa (`comment_id`, `mention_id`, khóa aggregate) để chạy lại hoặc replay không tạo bản trùng.

### 3.5. Tầng phân tích và hiển thị

Phân tích Q1–Q5 đọc `aggregates` và `aspect_mentions`, tính tỷ lệ, khoảng tin cậy và kiểm định. Kết quả hiển thị trên dashboard và đưa vào báo cáo; mỗi bình luận minh họa có `comment_id`/`video_id` để truy ngược ngữ cảnh. Dashboard hiện là bản nháp HTML tĩnh; bản chính thức sẽ đọc từ cơ sở dữ liệu.

## 4. Schema dữ liệu

### 4.1. Bình luận raw (schema v2)

`comment_id` là khóa; contract: [`contracts/comment-event.schema.json`](contracts/comment-event.schema.json), khớp với `src/ingest/src/schema.py`.

| Trường | Kiểu | Ý nghĩa và lưu ý |
|---|---|---|
| `comment_id` | string | ID YouTube của comment/reply; khóa upsert |
| `video_id` | string | Video chứa comment; khóa partition Kafka |
| `parent_id` | string/null | ID comment gốc nếu là reply; comment gốc là `null` |
| `parent_text` | string/null | Nội dung comment gốc, chỉ có ở reply |
| `model` | string | Mã **máy của video** theo config (vd `s23u`); video nhắc nhiều máy nối bằng `\|` (vd `ip15prm\|s24u`). Không phải máy được nhắc trong bình luận |
| `source` | string | Nguồn dữ liệu, hiện là `youtube` |
| `text` | string | Nội dung chữ thuần lấy từ `textDisplay` |
| `text_norm` | string | Nội dung sau chuẩn hóa; crawler để rỗng |
| `author_hash` | string | SHA-256 của `salt + channel ID`; không lưu tên thật |
| `published_at` | datetime UTC | Thời điểm đăng; thời gian sự kiện |
| `like_count` | int/null | Số like tại thời điểm `fetched_at` |
| `reply_count` | int/null | Tổng reply; chỉ có ở comment gốc |
| `fetched_at` | datetime UTC | Thời điểm API trả dữ liệu |
| `ingested_at` | datetime UTC/null | Thời điểm ghi archive/Kafka; replay ghi lại |
| `schema_version` | int | Hiện là `2` |

Ví dụ:

```json
{
  "comment_id": "UgxA1b2C3d4E5f6G7h4AaABAg.9xYz",
  "video_id": "aB3dE5fG7hI",
  "parent_id": "UgxA1b2C3d4E5f6G7h4AaABAg",
  "parent_text": "pin tụt như rơi",
  "model": "s23u",
  "source": "youtube",
  "text": "@An chuẩn luôn bác",
  "text_norm": "",
  "author_hash": "9f86d081884c7d65...",
  "published_at": "2023-02-10T03:15:00Z",
  "like_count": 2,
  "reply_count": null,
  "fetched_at": "2026-10-17T15:58:28Z",
  "ingested_at": "2026-10-17T15:58:30Z",
  "schema_version": 2
}
```

Quan hệ giữa các máy (đời trước, đối thủ) nằm trong danh mục máy, không nằm trong từng bình luận.

### 4.2. Mention (mệnh đề × khía cạnh)

Đơn vị phân tích của Q1–Q5. Các trường chính: `mention_id`, `comment_id`, `clause_text`, `video_model`, **`target_model`** (máy được nhắc), `aspect`, `sentiment`, `confidence`, `is_owner`, `defect_type`, `compare_with`, `days_since_launch`, `label_source`, `model_version`. Contract (bản nháp): [`contracts/aspect-mention.schema.json`](contracts/aspect-mention.schema.json).

## 5. Phương pháp phân tích

### 5.1. Tiền xử lý

- Chuẩn hóa chữ thường, dấu câu, khoảng trắng và emoji; chuyển một số teencode; tạo `text_norm`.
- Tách bình luận thành mệnh đề theo dấu câu và từ nối như "nhưng", "còn". Từ "mà" nhiều nghĩa trong tiếng Việt nên cần kiểm tra chất lượng tách trên mẫu.
- Giữ `parent_text` để hiểu ngữ cảnh reply.
- Dùng `published_at` làm thời gian sự kiện, không dùng `ingested_at` để tính xu hướng.

### 5.2. Lọc spam

Lọc spam là bước đầu tiên: bình luận spam/quảng cáo/seeding bị loại khỏi mọi thống kê về khía cạnh và cảm xúc. Hiện dùng bộ luật (link, số điện thoại, mời liên hệ, cờ bạc, lặp ký tự…); sẽ so sánh với một mô hình ML trên tập có nhãn.

```text
tỷ lệ spam = số bình luận bị phân loại spam / tổng số bình luận tiếng Việt đã kiểm tra
```

Bình luận không phải tiếng Việt được tách riêng, không tính là spam.

### 5.3. Khía cạnh, cảm xúc và máy được nhắc

Đơn vị là **mệnh đề**. Một mệnh đề có thể nhắc nhiều khía cạnh, nên khía cạnh là bài toán phân loại **đa nhãn có giám sát**. Chín khía cạnh (đề xuất, chốt ở Công việc 4):

1. Pin & sạc.
2. Màn hình.
3. Hiệu năng (gồm nhiệt độ).
4. Camera.
5. Thiết kế và độ bền.
6. Phần mềm.
7. Phần cứng khác.
8. Giá.
9. Bảo hành và hậu mãi.

Với mỗi cặp (mệnh đề, khía cạnh), cảm xúc là khen, chê hoặc trung tính. Máy được nhắc xác định bằng tên/alias trong mệnh đề, sau đó đến comment cha và máy của video.

Baseline là bộ luật từ khóa hiện có; mô hình thử nghiệm gồm TF-IDF + Logistic Regression/Linear SVM, và PhoBERT nếu đủ điều kiện. Dữ liệu YouTube chưa gán nhãn không dùng trực tiếp để train. Dataset ngoài (UIT-ViSFD) được ánh xạ về bộ khía cạnh trên để tăng dữ liệu train; tập test YouTube gán tay dùng để đo khả năng chuyển miền.

### 5.4. Phân tích thống kê

- Tỷ lệ khen/chê tính trên `pos + neg` (bỏ trung tính khỏi mẫu số), dùng một công thức cho mọi câu hỏi.
- Khoảng tin cậy 95% bằng bootstrap theo video, vì các mệnh đề cùng video không độc lập.
- Kiểm định: z-test hai tỷ lệ, chi-square, kiểm định nhị thức; hiệu chỉnh Holm cho từng câu hỏi.
- Chỉ kết luận khi có ý nghĩa thống kê; ngược lại ghi "chưa đủ bằng chứng".

### 5.5. Phát hiện bất thường (tùy chọn)

Với từng cặp (máy, khía cạnh), theo dõi số mention hợp lệ, số và tỷ lệ mention tiêu cực, cửa sổ thời gian và baseline. Một cảnh báo chứa ít nhất: `alert_id`, `created_at`, `window_start`, `window_end`, máy và khía cạnh, chỉ số hiện tại, baseline, ngưỡng, mức độ, và các mention minh họa.

## 6. Tiến độ (tính đến 28/10/2026)

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Chốt bài toán và phạm vi | ✅ Xong | 5 câu hỏi Q1–Q5, đặc tả trong `docs/EDA_requirement.md` |
| Crawler và Replay | ✅ Xong | Quota, resume, chống trùng, ẩn danh, replay |
| Dữ liệu thô | ✅ Có | ~226 nghìn bình luận, 1.715 video, 51 mã máy |
| Thiết kế kiến trúc và dữ liệu | ✅ Bản nháp | Sơ đồ mới, `docs/data-model.md`, contract đang chờ chốt |
| Tiền xử lý | ⚠️ Một phần | Đã có kết quả (lọc spam ~6,35%, tách mệnh đề); code chưa đưa vào repo |
| EDA và dashboard | ⚠️ Bản nháp | Dùng để thống nhất đầu ra; nhãn là luật từ khóa nên số liệu chỉ minh họa |
| Gán nhãn | ❌ Chưa | Guideline và 3000 mệnh đề |
| Mô hình | ❌ Chưa | Khía cạnh, cảm xúc, máy được nhắc, spam |
| Cơ sở dữ liệu | ❌ Chưa | Mới có thiết kế |
| Trả lời Q1–Q5 bằng mô hình | ❌ Chưa | |
| Streaming (Kafka/Spark) | ⏸ Tùy chọn | Mới có Kafka 1 node cho môi trường dev |

Kế hoạch chi tiết và phân công: [`docs/roadmap.md`](docs/roadmap.md).

## 7. Tiêu chí đánh giá

### 7.1. Chất lượng nhãn

- Độ đồng thuận giữa hai người gán (Cohen's kappa) trên tập test, mục tiêu ≥ 0,6.
- Tỷ lệ đúng của nhãn AI so với người kiểm tra.

### 7.2. Chất lượng mô hình

- Khía cạnh: F1 từng khía cạnh, micro-F1, macro-F1.
- Cảm xúc: macro-F1 và confusion matrix.
- Máy được nhắc: precision, recall, tỷ lệ không xác định.
- Spam: precision, recall, F1 cho lớp `spam`.
- Mọi mô hình so với baseline luật từ khóa, đo trên tập test YouTube gán tay.

### 7.3. Chất lượng phân tích

- Mọi tỷ lệ có khoảng tin cậy; mọi kết luận có kiểm định đã hiệu chỉnh.
- Bình luận minh họa đúng khía cạnh, đúng máy, đã được người duyệt.
- Kết quả chạy lại được từ code và phiên bản dữ liệu ghi rõ.

### 7.4. Chất lượng hệ thống

- Không tạo bản ghi trùng khi retry hoặc replay.
- Crawl dừng giữa chừng tiếp tục được mà không mất page token.
- Không tính bình luận spam vào tỷ lệ nghiệp vụ; dùng đúng thời gian sự kiện.
- (Giai đoạn 2) Đo được độ trễ từ `ingested_at` đến khi có kết quả.

## 8. Kết luận

Phần thu thập dữ liệu đã hoàn thành với các cơ chế đảm bảo không trùng, không mất tiến độ và ẩn danh người dùng. Bài toán đã được cụ thể hóa thành 5 câu hỏi có cách tính và điều kiện kết luận rõ ràng, cùng thiết kế dữ liệu lấy mệnh đề × khía cạnh × máy được nhắc làm đơn vị phân tích. Trọng tâm giai đoạn tới là gán nhãn, huấn luyện và đánh giá mô hình, sau đó trả lời Q1–Q5 bằng số liệu có kiểm định. Phần streaming với Kafka và Spark được giữ như hướng mở rộng, dùng chung định dạng dữ liệu nên có thể bổ sung mà không phải thiết kế lại.

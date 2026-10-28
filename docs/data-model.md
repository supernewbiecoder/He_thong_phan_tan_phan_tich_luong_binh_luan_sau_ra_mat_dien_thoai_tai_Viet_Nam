# Thiết kế dữ liệu

> Mục đích: Định nghĩa các collection, trường, mã danh mục và quy ước dùng chung giữa các nhóm; cập nhật lần cuối: 2026-10-28.

**Trạng thái: BẢN NHÁP**, chốt ở Công việc 4. Sau khi chốt, đổi bất kỳ trường nào phải tăng `schema_version` và báo cả nhóm.

## Nguyên tắc

1. **Đơn vị phân tích là mệnh đề × khía cạnh** (`aspect_mentions`), không phải cả bình luận.
2. **Tách máy của video và máy được nhắc.** `video_model` là ngữ cảnh; `target_model` là máy mà mệnh đề đang nói tới. Mọi thống kê dùng `target_model`.
3. **Lưu số đếm, không lưu %.** `aggregates` chỉ chứa `n_pos`, `n_neg`, `n_neu`; tỷ lệ, khoảng tin cậy, kiểm định tính ở tầng phân tích.
4. **Mọi nhãn đều có nguồn gốc:** `label_source` (`rule`, `llm`, `model`, `human`) và `model_version`. Nhờ vậy dashboard chạy được ngay với nhãn luật, sau này thay bằng mô hình mà không đổi schema.
5. **Mã tiếng Anh trong DB, tiếng Việt ở tầng hiển thị.** Không lưu cột kiểu `"% Khen"`.
6. **Không sửa dữ liệu raw.** Kết quả xử lý ghi sang trường/collection khác, có `pipeline_version`.

## Danh mục mã

### Khía cạnh (`aspect`)

| Mã | Tên | Bao gồm |
|---|---|---|
| `BATTERY` | Pin & sạc | dung lượng, thời lượng dùng, tốc độ sạc, sạc không dây |
| `DISPLAY` | Màn hình | độ sáng, màu, tần số quét, kích thước, độ phân giải |
| `PERFORMANCE` | Hiệu năng | chip, độ mượt, chơi game, RAM, **nhiệt độ/nóng máy** |
| `CAMERA` | Camera | chụp, quay, zoom, selfie, chụp đêm |
| `DESIGN` | Thiết kế & độ bền | ngoại hình, chất liệu, trọng lượng, cầm nắm, độ bền, chống nước |
| `SOFTWARE` | Phần mềm | hệ điều hành, giao diện, cập nhật, tính năng phần mềm, AI |
| `HARDWARE_OTHER` | Phần cứng khác | loa, rung, vân tay, Face ID, sóng, wifi, bộ nhớ, bút |
| `PRICE` | Giá | giá bán, đáng tiền, giữ giá, khuyến mãi |
| `WARRANTY` | Bảo hành & hậu mãi | bảo hành, sửa chữa, cửa hàng, chính hãng/xách tay |

Định nghĩa chi tiết và ví dụ biên nằm trong guideline gán nhãn (Công việc 1).

### Cảm xúc (`sentiment`)
`pos` (khen), `neg` (chê), `neu` (trung tính: hỏi, mô tả, không rõ thái độ).

### Loại lỗi (`defect_type`)
`BATTERY_DRAIN`, `OVERHEAT`, `LAG`, `DISPLAY_DEFECT`, `CAMERA_DEFECT`, `SOFTWARE_BUG`, `CONNECTIVITY`, `HARDWARE_DEFECT`, `OTHER`.

### Mã máy (`model_id`)
Lấy đúng `name` trong [config/pipeline.yaml](../config/pipeline.yaml) (vd `s23u`, `ip14prm`). Không dùng tên đầy đủ, không tự đặt tên mới.

## 1. `models`

Danh mục máy, sinh từ `config/pipeline.yaml` (Công việc 2). Khóa: `model_id`.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `model_id` | string | vd `s23u` |
| `title` | string | vd `Samsung Galaxy S23 Ultra` |
| `brand` | string | `Apple`, `Samsung`, `Xiaomi`, `OPPO`, `vivo`, `Huawei`, `realme` |
| `launch_date` | date | ngày ra mắt tại VN, giờ VN |
| `predecessor_id` | string/null | đời trước, dùng cho Q4 |
| `rivals` | string[] | đối thủ cùng thời điểm |
| `aliases` | string[] | cách gọi, dùng cho nhận diện `target_model` |
| `segment` | string | `flagship`, `mid`… |

## 2. `videos`

Như mô tả trong [src/ingest/README.md](../src/ingest/README.md#3-schema-v2-nguồn-sự-thật-srcschemapy). Khóa: `video_id`; giữ bản chụp số liệu mới nhất. Với nguồn ngoài YouTube, `video_id` hiểu là "id trang/bài gốc".

## 3. `comments`

Bản ghi raw (schema v2, [contracts/comment-event.schema.json](../contracts/comment-event.schema.json)) cộng kết quả tiền xử lý. Khóa: `comment_id`, ghi bằng upsert.

| Trường thêm | Kiểu | Ghi chú |
|---|---|---|
| `text_norm` | string | văn bản đã chuẩn hóa |
| `is_spam` | bool | |
| `spam_reasons` | string[] | lý do gắn cờ |
| `is_vietnamese` | bool | tách riêng khỏi `is_spam` |
| `clauses` | object[] | `{idx, text}` theo thứ tự trong bình luận |
| `pipeline_version` | string | phiên bản code tiền xử lý |
| `processed_at` | datetime UTC | |

## 4. `aspect_mentions`

Collection quan trọng nhất. Mỗi dòng = một mệnh đề nhắc một khía cạnh. Contract: [contracts/aspect-mention.schema.json](../contracts/aspect-mention.schema.json). Khóa: `mention_id`.

| Trường | Kiểu | Ghi chú | Ai ghi |
|---|---|---|---|
| `mention_id` | string | `<comment_id>#<clause_idx>#<aspect>` | B |
| `comment_id` | string | | B |
| `clause_idx` | int | vị trí mệnh đề trong `comments.clauses` | B |
| `clause_text` | string | | B |
| `source` | string | `youtube`, … | B |
| `video_id` | string | | B |
| `video_model` | string | máy của video (có thể dạng `a\|b`) | B |
| `target_model` | string/null | máy được nhắc; `null` = không xác định | B3 |
| `aspect` | enum | xem danh mục | B1 |
| `sentiment` | enum | `pos`/`neg`/`neu` | B2 |
| `confidence` | number/null | 0–1; `null` với nhãn người gán | B |
| `is_owner` | bool/null | người viết đã dùng máy | B3 |
| `defect_type` | enum/null | chỉ khi mệnh đề báo lỗi | B3 |
| `compare_with` | string/null | máy được so sánh cùng | B3 |
| `compare_winner` | enum/null | `target`/`other`/`tie` | B3 |
| `published_at` | datetime UTC | thời điểm đăng bình luận | B |
| `days_since_launch` | int/null | tính theo `launch_date` của `target_model`, giờ VN | A |
| `label_source` | enum | `rule`/`llm`/`model`/`human` | B |
| `model_version` | string | vd `rule-v0`, `aspect-lr-v1` | B |
| `schema_version` | int | hiện là `1` | B |

Quy ước:
- Mệnh đề nhắc 2 khía cạnh → 2 dòng.
- Mệnh đề không thuộc khía cạnh nào → không có dòng.
- Bình luận spam → không tạo mention.
- Mention có `target_model = null` không vào Q1–Q5, nhưng được đếm để báo cáo tỷ lệ không xác định được máy.

Index cần có: `target_model + aspect + days_since_launch`; `target_model + is_owner + defect_type` (Q5); `compare_with` (Q3b).

## 5. `aggregates`

Số đếm gom sẵn. Khóa:
`(target_model, aspect, week_since_launch, video_id, source, model_version)`

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `week_since_launch` | int | `days_since_launch // 7 + 1` |
| `n_pos`, `n_neg`, `n_neu` | int | |
| `updated_at` | datetime UTC | |

Giữ `video_id` trong khóa để **bootstrap theo video** được: muốn tổng thì cộng qua các video; muốn khoảng tin cậy thì rút ngẫu nhiên các video. Ghi bằng upsert theo khóa để chạy lại không bị cộng dồn.

## 6. `alerts`

Dùng cho phần cảnh báo (tùy chọn).

| Trường | Kiểu |
|---|---|
| `alert_id`, `created_at`, `window_start`, `window_end` | |
| `target_model`, `aspect` | |
| `metric`, `value`, `baseline`, `threshold`, `severity` | |
| `sample_mention_ids` | string[] |

## 7. `gold_labels`

Nhãn gán tay/AI để huấn luyện và đánh giá. Mỗi dòng = một mệnh đề do một người gán (2 người gán cùng mệnh đề → 2 dòng).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `clause_id` | string | `<comment_id>#<clause_idx>` |
| `comment_id`, `clause_text`, `video_id` | | |
| `annotator` | string | mã người gán, hoặc tên mô hình nếu `llm` |
| `label_source` | enum | `human`/`llm` |
| `split` | enum | `train`/`test` (theo `video_id`, Công việc 7) |
| `aspects` | object[] | `[{aspect, sentiment}]`; rỗng nếu không có khía cạnh |
| `target_model` | string/null | |
| `is_owner`, `defect_type`, `compare_with`, `compare_winner` | | như `aspect_mentions` |
| `guideline_version` | string | |
| `labeled_at` | datetime UTC | |

Tập `test` chỉ được chứa `label_source = "human"`.

## 8. Câu hỏi → dữ liệu

| Câu | Nhóm theo | Nguồn |
|---|---|---|
| Q1 | máy × tuần | `aggregates` |
| Q2 | X × khía cạnh | `aggregates` + mẫu từ `aspect_mentions` |
| Q3a | máy × khía cạnh | `aggregates` |
| Q3b | khía cạnh, mention có `compare_with` | `aspect_mentions` |
| Q4 | {P, X} × khía cạnh | `aggregates` + `models.predecessor_id` |
| Q5 | loại lỗi × tuần, `is_owner = true` | `aspect_mentions` |

Chi tiết cách tính: [EDA_requirement.md](EDA_requirement.md).

# Thiết kế dữ liệu

> Mục đích: Định nghĩa các collection, trường, mã danh mục và quy ước dùng chung giữa các nhóm; cập nhật lần cuối: 2026-11-26.

**Trạng thái: ĐÃ CHỐT** (Công việc 4, 2026-10-28; aspect_mentions lên v2 ngày 2026-11-08 sau khi đối chiếu Data_vip_pro_v4; lên **v3 ngày 2026-11-26** theo bộ nhãn chốt, Nguyễn Lê Quân làm theo giao việc của trưởng nhóm). Đổi bất kỳ trường nào phải tăng `schema_version` và báo cả nhóm.

## Nguyên tắc

1. **Đơn vị phân tích là cả bình luận** (phương án A, 20/11): đếm theo (bình luận, máy, nhãn chiều 2). Mỗi dòng `aspect_mentions` ghi kèm mệnh đề bằng chứng (`clause_idx`).
2. **Tách máy của video và máy được nhắc.** `video_model` là ngữ cảnh; `target_model` là máy mà nhận xét nói tới. Mọi thống kê dùng `target_model`.
3. **Lưu số đếm, không lưu %.** `aggregates` chỉ chứa số đếm `n_pos`, `n_neg`, `n_neu`, `n_cmp`; tỷ lệ, khoảng tin cậy, kiểm định tính ở tầng phân tích.
4. **Mọi nhãn đều có nguồn gốc:** `label_source` (`rule`, `llm`, `model`, `human`) và `model_version`. Nhờ vậy dashboard chạy được ngay với nhãn luật, sau này thay bằng mô hình mà không đổi schema.
5. **Mã tiếng Anh trong DB, tiếng Việt ở tầng hiển thị.** Không lưu cột kiểu `"% Khen"`.
6. **Không sửa dữ liệu raw.** Kết quả xử lý ghi sang trường/collection khác, có `pipeline_version`.

## Danh mục mã

### Nhãn chiều 2 (`aspect`)

Theo [bộ nhãn chốt](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611) (26/11). Trong code, danh sách chỉ có ở một nơi: [src/labeling/final_labels.py](../../src/labeling/final_labels.py). Định nghĩa và ca khó nằm ở đặc tả bộ nhãn và [hướng dẫn gán chính thức](../3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md).

| Mã | Tên | Bao gồm |
|---|---|---|
| `pin_sac` | Pin & sạc | pin, thời lượng, tụt pin, sạc, củ sạc |
| `man_hinh` | Màn hình | độ sáng, tần số quét, tai thỏ, lỗ khoét, lỗi màn |
| `hieu_nang` | Hiệu năng | chip, RAM, điểm số, game, độ mượt, **nóng máy, tản nhiệt** |
| `camera` | Camera | chụp, quay, zoom, chống rung, màu ảnh |
| `thiet_ke` | Thiết kế | ngoại hình, màu máy, chất liệu, trọng lượng; máy đẹp, xấu nói chung |
| `do_ben` | Độ bền | độ bền, rơi vỡ, chống nước, bung, nứt |
| `phan_mem` | Phần mềm | hệ điều hành, giao diện, cập nhật, ứng dụng, AI |
| `phan_cung_khac` | Phần cứng khác | bộ nhớ, SIM, 5G, wifi, vân tay, bút, cổng, **loa, mic**, phụ kiện |
| `gia` | Giá | giá bán, giá về Việt Nam, giữ giá, khuyến mãi |
| `mua_ban` | Mua bán | mua ở đâu, khi nào, trả góp, xách tay, lên đời, ý định mua |
| `bao_hanh_sua_chua` | Bảo hành & sửa chữa | bảo hành, sửa chữa, thay linh kiện, đổi trả |
| `may_chung` | Cả máy | nói cả máy, không nêu phần nào (ngoài khía cạnh) |
| `hang_nguoi_dung` | Hãng & người dùng | hãng, thương hiệu, fan, nhóm người mua (ngoài khía cạnh) |
| `khac` | Khác | phần của máy chưa có ở trên (dự phòng) |

11 dòng đầu là **khía cạnh**; Q2–Q5 báo cáo theo 11 khía cạnh này. `may_chung`, `hang_nguoi_dung` có thái độ nhưng không phải khía cạnh.

### Thái độ (`sentiment`)
`tich_cuc` (khen), `tieu_cuc` (chê, kể cả báo lỗi), `so_sanh` (so với máy khác, có bên hơn), `khong_danh_gia` (hỏi, nhắc, giải thích mà không khen chê).

### Mục đích (`purposes`) và máy được nhắc (`model_mention`)
Mục đích: 13 nhãn chiều 3 của bộ nhãn chốt (`danh_gia`, `hoi`, `bao_loi`, `quang_cao`…), tính cho cả bình luận. Trưởng nhóm giữ chiều này trong contract (quyết định 5, 26/11). Máy được nhắc: `goi_ten_may`, `chi_hang`, `khong_nhac`.

### Loại lỗi (`defect_type`)
Chưa có bộ mã. 9 loại lỗi cũ đã bỏ cùng 9 khía cạnh cũ; bộ mới làm trên mẫu riêng các bình luận báo lỗi ([kế hoạch tổng thể](ke-hoach-tong-the.md) bước 2.6). Ở v3 trường này luôn `null`.

### Mã máy (`model_id`)
Lấy đúng `name` trong [config/pipeline.yaml](../../config/pipeline.yaml) (vd `s23u`, `ip14prm`). Không dùng tên đầy đủ, không tự đặt tên mới.

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

Như mô tả trong [docs/1-thu-thap/huong-dan.md](../1-thu-thap/huong-dan.md#3-schema-v3-nguồn-sự-thật-crawlerschemapy). Khóa: `video_id`; giữ bản chụp số liệu mới nhất. Với nguồn ngoài YouTube, `video_id` hiểu là "id trang/bài gốc".

## 3. `comments`

Bản ghi raw (schema v3, [contracts/comment-event.schema.json](../../contracts/comment-event.schema.json)) cộng kết quả tiền xử lý. Khóa: `comment_id`, ghi bằng upsert.

| Trường thêm | Kiểu | Ghi chú |
|---|---|---|
| `text_clean` | string | Level 1, làm sạch kỹ thuật: dùng để hiển thị, trích dẫn, tách mệnh đề ([dac-ta-lam-sach.md](../2-tien-xu-ly/dac-ta-lam-sach.md)) |
| `text_norm` | string | Level 2, chuẩn hóa ngôn ngữ: chỉ dùng cho máy ([dac-ta-chuan-hoa.md](../2-tien-xu-ly/dac-ta-chuan-hoa.md)) |
| `emojis` | string[] | emoji trong `text_clean`, theo thứ tự xuất hiện |
| `is_spam` | bool | |
| `spam_reasons` | string[] | lý do gắn cờ |
| `is_vietnamese` | bool | tách riêng khỏi `is_spam` |
| `clauses` | object[] | `{idx, start, end, text, text_norm}` theo thứ tự trong bình luận; `idx` đếm từ 0, `text_clean[start:end] == text` ([dac-ta-tach-menh-de.md](../2-tien-xu-ly/dac-ta-tach-menh-de.md)) |
| `pipeline_version` | string | phiên bản code tiền xử lý, vd `chuan-hoa-1.0` |
| `processed_at` | datetime UTC | |

## 4. `aspect_mentions`

Collection quan trọng nhất. Mỗi dòng = một nhận xét của một bình luận về một nhãn chiều 2 của một máy. Contract: [contracts/aspect-mention.schema.json](../../contracts/aspect-mention.schema.json). Khóa: `mention_id`.

| Trường | Kiểu | Ghi chú | Ai ghi |
|---|---|---|---|
| `mention_id` | string | `<comment_id>#<clause_idx>#<aspect>` | B |
| `comment_id` | string | | B |
| `parent_id` | string/null | bình luận gốc nếu là reply (v2) | B |
| `clause_idx` | int | vị trí mệnh đề bằng chứng trong `comments.clauses`, đếm từ 0 | B |
| `clause_text` | string | `clauses[clause_idx].text`, chữ gốc, không phải `text_norm` | B |
| `source` | string | `youtube`, … | B |
| `video_id` | string | | B |
| `video_model` | string | máy của video (có thể dạng `a\|b`) | B |
| `target_model` | string/null | máy được nhắc, phải có trong `models`; `null` = không xác định | B3 |
| `author_hash` | string | từ raw, để gộp theo người viết (v2) | B |
| `author_is_creator` | bool | từ raw, chủ kênh của video (v2) | B |
| `aspect` | enum | nhãn chiều 2, xem danh mục | B1 |
| `sentiment` | enum | `tich_cuc`/`tieu_cuc`/`so_sanh`/`khong_danh_gia` | B2 |
| `confidence` | number/null | 0–1; `null` với nhãn người gán | B |
| `is_owner` | bool/null | chiều 5: `true` khi nói rõ máy của mình hay người nhà; `null` khi không rõ | B3 |
| `purposes` | string[]/null | chiều 3 của cả bình luận; `null` = chưa suy luận (thêm ở v3) | B |
| `model_mention` | enum/null | chiều 6: `goi_ten_may`/`chi_hang`/`khong_nhac` (v3) | B3 |
| `target_model_source` | enum/null | `target_model` lấy từ đâu: `menh_de`, `menh_de_truoc`, `binh_luan`, `binh_luan_cha`, `video` (đoán theo máy của video), `khong_ro`, `nguoi_gan` (v3) | B3 |
| `defect_type` | null | luôn `null` ở v3 (bộ loại lỗi chưa chốt) | B3 |
| `compare_with` | string/null | máy được so sánh cùng; khác null thì `sentiment = so_sanh` | B3 |
| `compare_winner` | enum/null | bên hơn: `target`/`other`/`tie` (phiếu ghi `@a>b`, `@a~b`) | B3 |
| `published_at` | datetime UTC | thời điểm đăng bình luận | B |
| `days_since_launch` | int/null | ngày đăng (giờ VN) trừ `launch_date` của `target_model`; có thể âm hoặc vượt cửa sổ | A |
| `label_source` | enum | `rule`/`llm`/`model`/`human` | B |
| `model_version` | string | vd `rule-v1.1`, `aspect-lr-v1` | B |
| `schema_version` | int | hiện là `3` (2026-11-26) | B |

Quy ước:
- Mọi trường phải có mặt; không biết thì ghi `null`, không bỏ trường.
- Bình luận nhắc 2 nhãn chiều 2 → 2 dòng; mỗi (máy, nhãn) có tối đa một lời khen và một lời chê.
- Bình luận không có nhãn chiều 2 nào → không có dòng.
- Bình luận spam hoặc không phải tiếng Việt → không tạo mention.
- Mention có `target_model = null` không vào Q1–Q5, nhưng được đếm để báo cáo tỷ lệ không xác định được máy.
- Mention có `author_is_creator = true` không vào `aggregates` (chủ kênh trả lời người xem, không phải ý kiến người dùng).
- `aggregates` chỉ lấy `-7 <= days_since_launch < 7 * window_weeks` (theo `config/pipeline.yaml`).
- Ràng buộc chéo (schema kiểm): `compare_with` khác null thì `sentiment = so_sanh`; `compare_with` và `compare_winner` cùng có hoặc cùng null; `target_model = null` thì `days_since_launch = null`; `label_source = human` thì `confidence = null`.

Index cần có: `target_model + aspect + days_since_launch`; `target_model + is_owner + sentiment` (Q5); `compare_with` (Q3b).

## 5. `aggregates`

Số đếm gom sẵn. Khóa:
`(target_model, aspect, week_since_launch, video_id, source, model_version)`

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `week_since_launch` | int | `days_since_launch // 7 + 1` |
| `n_pos`, `n_neg`, `n_neu`, `n_cmp` | int | số mention `tich_cuc`, `tieu_cuc`, `khong_danh_gia`, `so_sanh` (tên cột giữ từ v2; `n_cmp` thêm ở v3) |
| `n_total`, `n_opinionated` | int | tổng bốn cột; `n_pos + n_neg` (mẫu số của % khen, % chê) |
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

Nhãn gán tay/AI để huấn luyện và đánh giá. Mỗi dòng = một bộ nhãn (bình luận, máy, nhãn chiều 2) do một người gán hay người phân xử. Nhãn cấp bình luận (tiếng Việt, liên quan, mục đích) ghi ở `data/labels/nhan_binh_luan.jsonl` ([đặc tả gán nhãn mục 8](../3-gan-nhan/dac-ta.md#8-phân-xử-và-nhãn-chuẩn)).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `clause_id` | string | `<comment_id>#<clause_idx>` (mệnh đề bằng chứng) |
| `comment_id`, `clause_text`, `video_id` | | |
| `annotator` | string | mã người gán, hoặc tên mô hình nếu `llm` |
| `label_source` | enum | `human`/`llm` |
| `split` | enum | `train`/`test` (theo `video_id`, Công việc 7) |
| `aspects` | object[] | `[{aspect, sentiment}]` theo mã ở danh mục trên; rỗng nếu không có nhãn chiều 2 |
| `target_model` | string/null | |
| `is_owner`, `model_mention`, `compare_with`, `compare_winner` | | như `aspect_mentions` |
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
| Q5 | khía cạnh × tuần, `is_owner = true`, `sentiment = tieu_cuc` (chờ bộ loại lỗi) | `aspect_mentions` |

# Đặc tả tầng 2: tiền xử lý bình luận

> Mục đích: Luật chung của tầng 2 (làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ tiếng Việt và spam): các bước, đầu vào, đầu ra, trường nào dùng cho việc gì, kiểm thử, phiên bản, quyết định đang chờ; cập nhật lần cuối: 2026-11-20.

**Phạm vi:** code trong `src/processing/`. Luật chi tiết từng bước nằm ở 4 đặc tả con (mục 1). Cách chạy: [hướng dẫn](huong-dan.md). Số liệu sau khi chạy: [báo cáo](bao-cao.md). File này không chép lại những thứ đó.

**Trạng thái:** phiên bản code `processing-2.0` (20/11: thêm bước 2.4). Code, từ điển và test đã có; **chưa chạy trên dữ liệu v4**. Các điểm ở mục 7 chờ nhóm quyết.

**Từ 20/11 (phương án A):** đơn vị phân tích là **cả bình luận**, không phải mệnh đề ([muc-tieu.md mục 4](../0-chung/muc-tieu.md#4-phạm-vi)). Bước 2.3 vẫn chạy, nhưng mệnh đề chỉ còn hai vai trò: chỉ vị trí bằng chứng của mỗi nhận xét, và là đơn vị chấm của luật mốc ở bước suy luận (mục 3).

## 1. Các bước, đặc tả và code

```text
src/ingest/data/raw/comments.jsonl   (crawler, schema 3, không bao giờ sửa)
   │  Level 0: chỉ đếm, không sửa (notebook 1_raw_audit mục 2)
   ▼
2.1 Làm sạch kỹ thuật  → text_clean
   ├──▶ 2.2 Chuẩn hóa ngôn ngữ → text_norm, emojis
   ├──▶ 2.3 Tách mệnh đề       → clauses (mỗi mệnh đề có text và text_norm)
   └──▶ 2.4 Gắn cờ             → is_vietnamese, is_spam, spam_reasons
   ▼
data/processed/comments.jsonl  +  comments.manifest.json
   ▼
bước suy luận (src/models/run.py, docs/4-mo-hinh/dac-ta-suy-luan.md)
```

| Bước | Đặc tả | Code | Test |
|---|---|---|---|
| 2.1 Làm sạch kỹ thuật | [dac-ta-lam-sach.md](dac-ta-lam-sach.md) | `src/processing/clean.py` | `tests/test_processing.py` (`Level1`) |
| 2.2 Chuẩn hóa ngôn ngữ | [dac-ta-chuan-hoa.md](dac-ta-chuan-hoa.md) | `src/processing/normalize.py`, `src/processing/resources/abbreviations.tsv` | `tests/test_processing.py` (`Level2…`, `EmojiVaTachTu`) |
| 2.3 Tách mệnh đề | [dac-ta-tach-menh-de.md](dac-ta-tach-menh-de.md) | `src/processing/clauses.py` | `tests/test_processing_clauses.py` |
| 2.4 Gắn cờ tiếng Việt, spam | [dac-ta-gan-co.md](dac-ta-gan-co.md) | `src/processing/flags.py` | `tests/test_processing_flags.py` |
| Chạy cả file, manifest | mục 2, 6 của file này | `src/processing/run.py` | `tests/test_processing.py` (`LenhChay`) |
| Phiên bản | mục 6 | `PIPELINE_VERSION` trong `src/processing/__init__.py` | |

2.2, 2.3 và 2.4 cùng chạy trên `text_clean`. 2.3 dùng hàm của 2.2 để tạo `text_norm` cho từng mệnh đề; 2.4 dùng từ điển viết tắt của 2.2 để nhận chữ không dấu.

Tầng 2 tạo ra bảng `comments` trong [thiet-ke-du-lieu.md mục 3](../0-chung/thiet-ke-du-lieu.md#3-comments) (Công việc 6).

## 2. Đầu vào và đầu ra

**Đầu vào:** file raw của crawler (schema 3). Chỉ đọc trường `text`.

**Đầu ra:** `data/processed/comments.jsonl` và manifest `data/processed/comments.manifest.json`.

- Số dòng **bằng đúng** file vào, cùng thứ tự. Bình luận rỗng vẫn giữ, có `text_clean = ""` và `clauses = []`.
- Mọi trường raw giữ nguyên giá trị và thứ tự; `text` không đổi.
- Thêm hoặc điền 9 trường:

| Trường | Kiểu | Nội dung |
|---|---|---|
| `text_clean` | string | Kết quả 2.1. `""` nếu bình luận rỗng |
| `text_norm` | string | Kết quả 2.2 trên cả bình luận. Raw đã có trường này nhưng crawler để rỗng |
| `emojis` | string[] | Emoji trong `text_clean`, theo thứ tự xuất hiện |
| `clauses` | object[] | Kết quả 2.3: mỗi phần tử `{idx, start, end, text, text_norm}`; `idx` đếm từ 0; `text_clean[start:end] == text`; `text_norm` = 2.2 chạy trên `text` của mệnh đề |
| `is_vietnamese` | bool | Kết quả 2.4: `false` chỉ khi có dấu hiệu là tiếng nước ngoài |
| `is_spam` | bool | Kết quả 2.4 |
| `spam_reasons` | string[] | Kết quả 2.4: mã lý do, rỗng nếu không phải spam |
| `pipeline_version` | string | Phiên bản code, vd `processing-2.0` |
| `processed_at` | string | Thời điểm chạy, UTC, `YYYY-MM-DDTHH:MM:SSZ`; một giá trị chung cho cả lần chạy |

**Manifest** ghi:
- phiên bản code, thời điểm chạy;
- số dòng và SHA-256 của file vào và file ra;
- kiểu dấu thanh; số mục và SHA-256 của từ điển viết tắt;
- số bình luận rỗng; số bình luận mỗi bước đã sửa;
- mệnh đề: tổng số, số bình luận theo số mệnh đề (1, 2, 3, 4, 5+), số mệnh đề theo loại ranh giới;
- cờ (`co`): số bình luận `is_vietnamese = false`, `is_spam = true`, số bình luận theo từng lý do spam và từng lý do nhận tiếng Việt.

Contract `comment-event` khóa `additionalProperties: false`, nên **không** dùng nó để kiểm file đầu ra. Bảng `comments` của thiết kế dữ liệu mới là định dạng của file này.

## 3. Dùng trường nào cho việc gì

| Việc | Trường |
|---|---|
| Trích dẫn cho người đọc, bình luận mẫu trong báo cáo | `text_clean` (hoặc `text` nếu cần nguyên văn từng ký tự) |
| Gán nhãn (người, LLM): hiện cả bình luận | `text_clean`, kèm `parent_text` nếu là reply |
| Đầu vào mô hình khía cạnh, cảm xúc (theo cả bình luận) | `text_norm` |
| Luật mốc của bước suy luận: chấm từng mệnh đề | `clauses[i].text` (từ khóa, tên máy), `clauses[i].text_norm` (cảm xúc) |
| Vị trí bằng chứng: `clause_idx`, `clause_text` của contract `aspect-mention` | `clauses[i].idx`, `clauses[i].text` |
| Bỏ qua trước khi suy luận | `is_spam`, `is_vietnamese` |
| Luật cần chữ hoa (vd "AI" khác "ai") | `text_clean`, `clauses[i].text` |
| Đếm từ, đặc trưng trên cả bình luận | `text_norm` |
| Đặc trưng cảm xúc từ emoji | `emojis` |

`clause_idx` của contract `aspect-mention` là `clauses[i].idx`. Contract ghi `clause_text` là "chữ gốc của mệnh đề, không phải `text_norm`": `clauses[i].text` đúng là như vậy.

**Công việc 9:** `src/models/sentiment/extract_clauses.py` đọc được file này, nhưng phải chạy với `--index-base 0` để `clause_idx` khớp contract (mặc định của script đếm từ 1).

## 4. Notebook và code dùng chung

- Mỗi bước có một notebook: `notebooks/2_1_clean.ipynb` ↔ 2.1, `2_2_normalize.ipynb` ↔ 2.2, `2_3_clauses.ipynb` ↔ 2.3. Bước 2.4 chưa có notebook: số đếm theo lý do nằm ở manifest (mục `co`). Chúng đọc file đầu ra (mục 2) và không giữ bản sao riêng của luật: phần "trước → sau" gọi đúng các hàm trong `clean.py`, `normalize.py`, `clauses.py`.
- Mỗi notebook chạy lại các bước (trên mẫu, hoặc trên mọi bình luận có bị sửa) rồi so với cột tương ứng trong file; lệch thì in cảnh báo: file được tạo bằng code khác code hiện tại.
- Số đếm trên toàn bộ dữ liệu lấy từ manifest, nên số trong notebook và số trong manifest luôn là một.

## 5. Kiểm thử

Chạy bằng `unittest` (không cần cài thêm). Chỉ dùng câu tự soạn.

| File | Kiểm gì |
|---|---|
| `tests/test_processing.py` (21 test) | Từng bước 2.1, 2.2 và các trường hợp "không đổi"; cả chuỗi; chạy lại không đổi; từ điển; emoji; lệnh chạy: số dòng, SHA-256, raw giữ nguyên, không để file tạm, từ chối ghi đè, `--limit` |
| `tests/test_processing_clauses.py` (11 test) | Từng loại ranh giới; không cắt trong số, URL, email; gộp mẩu ngắn; vị trí `start`/`end`; không mất chữ nào; loại ranh giới |
| `tests/test_processing_flags.py` (7 test) | Từng lý do nhận tiếng Việt; từng lý do spam; các trường hợp cố ý không tính là spam; hai cờ tách riêng |

Đổi luật nào thì sửa test của luật đó trong cùng commit.

## 6. Phiên bản

- `PIPELINE_VERSION` nằm trong `src/processing/__init__.py`.
- **Tăng số sau dấu chấm** (`1.0` → `1.1`) khi đổi code hoặc từ điển làm thay đổi kết quả của dù chỉ một bình luận.
- **Tăng số trước dấu chấm** (`1.x` → `2.0`) khi đổi trường đầu ra hoặc thứ tự bước.
- Mỗi lần phát hành file đã xử lý cho nhóm dùng, ghi một dòng vào bảng dưới (số lấy từ manifest). Cả nhóm dùng chung một file, không tự chạy lại rồi dùng bản riêng.

| Phiên bản code | File vào (phiên bản, SHA-256) | File ra | Số dòng | Số mệnh đề | SHA-256 file ra | Ngày | Ghi chú |
|---|---|---|---|---|---|---|---|
| `processing-1.0` | v4, `722d0e1e…2b45` | `data/processed/comments.jsonl` | | | | | Không phát hành, thay bằng 2.0 |
| `processing-2.0` | v4, `722d0e1e…2b45` | `data/processed/comments.jsonl` | ___ | ___ | ___ | ___ | Thêm bước 2.4 (3 trường cờ). Chưa chạy. Điền sau lần chạy đầu |

`processed_at` đổi mỗi lần chạy, nên hai lần chạy cùng code vẫn cho SHA-256 file ra khác nhau. Muốn so hai lần chạy thì so `so_binh_luan_moi_buoc_sua` và `menh_de` trong manifest.

## 7. Quyết định đang chờ nhóm

| # | Quyết định | Lựa chọn | Căn cứ |
|---|---|---|---|
| 1 | Kiểu dấu thanh (2.2, N3) | Kiểu cũ (mặc định) hay kiểu mới | `2_2_normalize` mục 6.4 |
| 2 | Mục viết tắt nhập nhằng | Thêm mục nào trong bảng "cố ý chưa đưa vào" ([dac-ta-chuan-hoa.md mục 6](dac-ta-chuan-hoa.md#6-n6-viết-tắt-teencode)) | `2_2_normalize` mục 6.3, 6.5 |
| 3 | Bình luận dưới video tặng quà | Giữ, gắn cờ, hay loại khỏi phân tích | `1_raw_audit` mục 4.3 |
| 4 | `author_name` trong file đầu ra | Hiện chép nguyên từ raw. Bỏ khỏi file chia sẻ hay giữ: theo quyết định 3 của [kế hoạch](../0-chung/ke-hoach.md#3-quyết-định-đang-chờ-trưởng-nhóm) | Quyền riêng tư |
| 5 | Chữ không dấu | Giữ nguyên (hiện tại) hay thêm bước khôi phục dấu | `1_raw_audit` mục 2.7b |
| 6 | Độ kéo dài, emoticon, like | Có thêm cột đặc trưng cho mô hình không | `2_2_normalize` mục 3.4, `1_raw_audit` mục 4.5 |
| 7 | Tách mệnh đề: danh sách từ nối, ngưỡng `MIN_CHU`, có cắt ở "mà", "còn" không | Từ 20/11 mệnh đề không còn là đơn vị đếm, nên quyết định này chỉ ảnh hưởng luật mốc và vị trí bằng chứng. Giữ như [dac-ta-tach-menh-de.md](dac-ta-tach-menh-de.md) cho tới khi có lý do chỉnh | `2_3_clauses` mục 5–7, đọc mẫu |
| 8 | Luật gắn cờ 2.4 | Giữ, hay chỉnh theo kết quả đo của Công việc 11 | Nhãn mẫu A ([đặc tả gán nhãn mục 3](../3-gan-nhan/dac-ta.md#3-mẫu-a-chất-lượng-dữ-liệu)) |

## 8. Luật ↔ code

| Mục đặc tả | Code | Test |
|---|---|---|
| Mục 2 (đầu ra, manifest) | `run.py`: `xu_ly_ban_ghi`, `chay` | `LenhChay` |
| [dac-ta-lam-sach.md](dac-ta-lam-sach.md) | `clean.py` | `Level1` |
| [dac-ta-chuan-hoa.md](dac-ta-chuan-hoa.md) mục 1–7 | `normalize.py`, `resources/abbreviations.tsv` | `Level2TungBuoc`, `Level2CaChuoi` |
| [dac-ta-chuan-hoa.md](dac-ta-chuan-hoa.md) mục 8 (emoji) | `normalize.py`: `tach_emoji` | `EmojiVaTachTu` |
| [dac-ta-tach-menh-de.md](dac-ta-tach-menh-de.md) | `clauses.py` | `tests/test_processing_clauses.py` |
| [dac-ta-gan-co.md](dac-ta-gan-co.md) | `flags.py` | `tests/test_processing_flags.py` |
| Mục 6 (phiên bản) | `__init__.py`: `PIPELINE_VERSION` | `LenhChay` |

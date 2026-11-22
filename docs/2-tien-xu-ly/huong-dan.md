# Hướng dẫn tầng 2: EDA, làm sạch, chuẩn hóa, tách mệnh đề

> Mục đích: Từng bước chạy các notebook kiểm tra dữ liệu, chạy lệnh tầng 2 ra file cho các bước sau, kiểm tra kết quả, sửa từ điển hay luật, kèm các lỗi hay gặp; cập nhật lần cuối: 2026-11-20.

Luật: [đặc tả tầng 2](dac-ta.md) và 4 đặc tả con. Số liệu đã chạy: [báo cáo](bao-cao.md). Lệnh dưới đây viết cho **PowerShell trên Windows**, chạy từ **gốc repo**.

## 1. Cần có trước

| Thứ | Ở đâu | Ghi chú |
|---|---|---|
| Môi trường `.venv` | Gốc repo | Theo [cài đặt](../0-chung/cai-dat.md). Cần `pandas`, `matplotlib`. Tầng 2 không cần thêm thư viện nào |
| Dữ liệu v4 | `src/ingest/data/raw/comments.jsonl` | Kiểm số dòng và SHA-256 theo [đặc tả thu thập mục 7](../1-thu-thap/dac-ta.md#7-phiên-bản-dữ-liệu) |
| Danh sách video | `src/ingest/data/raw/videos.jsonl` | Cho `1_raw_audit` mục 2.1 và 4. Thiếu thì các mục đó tự bỏ qua |
| Danh mục máy kèm ngày ra mắt | `src/ingest/data/models.json` | Crawler sinh ra từ `config/pipeline.yaml`. `1_raw_audit` mục 3 **bắt buộc** cần. Không có thì xin trưởng nhóm cùng bộ dữ liệu |

## 2. Notebook

Mỗi bước một notebook trong `notebooks/`, đánh số theo tầng. Mở trong VS Code, chọn kernel `.venv` (góc phải trên), bấm *Run All*.

| Notebook | Nội dung | Cần có trước |
|---|---|---|
| `1_raw_audit.ipynb` | Kiểm tra dữ liệu gốc (Level 0): video, rỗng, trùng, độ dài, emoji, URL, ngôn ngữ, gõ không dấu, thời gian, đăng dồn; theo máy và tuần sau ra mắt, bộ 4 máy; kênh, loại video, video tặng quà, reply, like | Dữ liệu của crawler (mục 1) |
| `2_1_clean.ipynb` | Bước 2.1 làm sạch: số bình luận mỗi bước sửa, ví dụ trước → sau từng bước B1–B7 | File đã xử lý (mục 3) |
| `2_2_normalize.ipynb` | Bước 2.2 chuẩn hóa: số bình luận mỗi bước sửa, ví dụ trước → sau từng bước N1–N7, token, emoji, từ vựng, viết tắt chưa có trong từ điển, kiểu dấu thanh | File đã xử lý |
| `2_3_clauses.ipynb` | Bước 2.3 tách mệnh đề: số mệnh đề, độ dài, cắt ở đâu, từ nối, ví dụ, chỗ có thể bỏ sót | File đã xử lý |
| `3_aspect_keywords.ipynb` | Khía cạnh theo từ khóa; bộ 4 máy × khía cạnh | File đã xử lý |
| `4_sentiment_report.ipynb` | Hình cho báo cáo cảm xúc (Công việc 9) | Model cảm xúc, xem [hướng dẫn cảm xúc](../4-mo-hinh/huong-dan-cam-xuc.md) |

**Thứ tự chạy:** `1_raw_audit` chạy được ngay. Các notebook `2_*`, `3_*` đọc file `data/processed/comments.jsonl`, nên phải chạy lệnh ở mục 3 trước. Chúng không tự xử lý lại cả bộ dữ liệu, chỉ đọc file rồi so sánh:
- số đếm trên toàn bộ dữ liệu lấy từ manifest;
- phần "từng bước trước → sau" chạy lại trên một mẫu ngẫu nhiên (`MAU`, mặc định 100.000 bình luận). Riêng `2_1_clean` chạy lại trên mọi bình luận có bị sửa, nên số của nó là số toàn bộ.

Mỗi notebook nạp cả 473.786 bình luận vào bộ nhớ, nên cần vài GB RAM trống. Đóng bớt ứng dụng khác trước khi chạy.

**Tham số hay đổi** (sửa trong ô rồi chạy lại ô đó và các ô sau):

| Tham số | Ở đâu | Ý nghĩa |
|---|---|---|
| `N_SHOW` | `notebooks/helpers.py` | Số dòng in ra ở mỗi danh sách |
| `TRANG`, `AN_COT` | `1_raw_audit` mục 1 | Lật trang dữ liệu; cột ẩn (mặc định ẩn `author_name`) |
| `NGUONG_BINH_LUAN`, `MAY_XEM` | `1_raw_audit` mục 3.1, 3.3 | Ngưỡng đánh ⚠ máy ít dữ liệu; máy vẽ trên biểu đồ theo ngày |
| `QUA_RE` | `1_raw_audit` mục 4.3 | Từ khóa nhận video tặng quà |
| `BO_MAY`, `NGUONG_O` | `1_raw_audit` mục 3.4, `3_aspect_keywords` mục 3 | Bộ 4 máy (mặc định đọc từ `config/analysis.yaml`); ngưỡng ô thiếu dữ liệu |
| `MAU` | `2_2_normalize` mục 3, `2_3_clauses` mục 5 | Số bình luận chạy lại từng bước; `None` = cả bộ |
| `TOP` | `2_2_normalize` mục 6.2 | Số chữ, cụm chữ in ra |
| `MENH_DE_DAI` | `2_3_clauses` mục 3 | Mệnh đề từ bao nhiêu chữ thì coi là dài |

**Notebook không ghi file nào.**

**Trước khi commit notebook:** output chứa nội dung bình luận thật. Nếu không muốn đẩy lên GitHub thì chọn *Clear All Outputs* rồi mới lưu.

## 3. Chạy lệnh tầng 2 ra file

Lệnh đọc file raw từng dòng, chạy làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ tiếng Việt và spam, ghi ra `data/processed/`. File raw không bị sửa.

Muốn chạy luôn cả chuỗi (tầng 2 → suy luận → aggregates, Q1–Q5) thì dùng `python -m src.run`, xem [luồng xử lý mục 2](../0-chung/luong-xu-ly.md#2-giai-đoạn-1-theo-lô). Mục này chỉ chạy tầng 2.

**Chạy thử 2.000 bình luận** (vài giây), mở file ra xem có đúng ý không:

```powershell
.\.venv\Scripts\python.exe -m src.processing.run --limit 2000 --output data/processed/thu.jsonl
```

**Chạy thật** (khoảng 2–3 phút):

```powershell
.\.venv\Scripts\python.exe -m src.processing.run
```

Kết quả:

| File | Nội dung |
|---|---|
| `data/processed/comments.jsonl` | Mỗi dòng một bình luận: bản ghi raw + `text_clean`, `text_norm`, `emojis`, `clauses`, `is_vietnamese`, `is_spam`, `spam_reasons`, `pipeline_version`, `processed_at` |
| `data/processed/comments.manifest.json` | Số dòng, SHA-256 file vào và ra, phiên bản code, từ điển, số bình luận mỗi bước đã sửa, thống kê mệnh đề, số bình luận theo từng cờ và lý do (`co`) |

Lệnh in nội dung manifest ra màn hình khi xong. Kiểm 3 điểm:

1. `vao.sha256` bằng SHA-256 của bản v4 trong [đặc tả thu thập mục 7](../1-thu-thap/dac-ta.md#7-phiên-bản-dữ-liệu). Khác nghĩa là đang chạy trên file khác bản chung.
2. `ra.so_dong` bằng `vao.so_dong` (473.786 với bản v4).
3. `chi_chay_thu` là `false`.
4. `co`: tỷ lệ `is_spam = true` và `is_vietnamese = false` có hợp lý không. Lọc vài chục bình luận theo từng lý do (`spam_reasons`) để đọc. Luật là mốc, chưa đo, nên gắn nhầm nhiều thì ghi lại cho Công việc 11.

Lần chạy dùng để phát hành cho cả nhóm thì ghi một dòng vào bảng phiên bản ở [đặc tả mục 6](dac-ta.md#6-phiên-bản). Thư mục `data/` không vào git: chia sẻ file đã xử lý cùng chỗ với dữ liệu v4. Mọi người dùng chung file đó, không tự chạy lại để dùng bản riêng.

Đổi đường dẫn: `--input <file raw>`, `--output <file ra>`. Lệnh từ chối ghi đè lên file vào.

## 4. Kiểm tra

**Test** (vài giây, chỉ dùng câu tự soạn):

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_processing tests.test_processing_clauses tests.test_processing_flags -v
```

Đạt khi dòng cuối là `OK`.

**Notebook tự kiểm:** `2_1_clean`, `2_2_normalize`, `2_3_clauses` chạy lại các bước rồi so với cột trong file (`text_clean`, `text_norm`, `clauses`) và in "… giống hệt … trong file". Nếu in "⚠ … chạy lại lệnh tầng 2" thì file đang đọc được tạo bằng code khác code hiện tại, thường do sửa luật mà chưa chạy lại lệnh.

**Kiểm bằng mắt:**
- `2_1_clean` mục 4 và `2_2_normalize` mục 5: bình luận trước → sau;
- `2_3_clauses` mục 6: bình luận ngẫu nhiên đã tách thành nhiều mệnh đề.

Đọc xem có chỗ nào chuẩn hóa làm sai nghĩa, hay tách sai chỗ không. Gặp lỗi lặp lại thì ghi lại, sửa luật theo mục 5.

## 5. Sửa từ điển hay luật

1. Xem căn cứ trong notebook:
   - `2_2_normalize` mục 6.3: viết tắt chưa có trong từ điển;
   - `2_2_normalize` mục 6.4: kiểu dấu thanh;
   - `2_2_normalize` mục 6.5: số lần gặp từng mục từ điển;
   - `2_3_clauses` mục 5–7: từ nối, mệnh đề dài có thể bị bỏ sót.
2. Sửa:
   - **Từ điển viết tắt:** `src/processing/resources/abbreviations.tsv`, mỗi dòng `viết tắt<TAB>đầy đủ<TAB>ghi chú`. Viết tắt là một chữ, viết thường. Đọc danh sách "cố ý chưa đưa vào" ở đầu file trước khi thêm.
   - **Kiểu dấu thanh:** `KIEU_DAU` trong `src/processing/normalize.py`.
   - **Từ nối, ngưỡng gộp mệnh đề:** `CAC_TU_NOI`, `MIN_CHU` trong `src/processing/clauses.py`.
   - **Luật spam, nhận tiếng Việt:** `src/processing/flags.py` và [dac-ta-gan-co.md](dac-ta-gan-co.md).
   - **Luật khác:** hàm tương ứng trong `clean.py`, `normalize.py`, `clauses.py`, `flags.py`, đồng thời sửa đặc tả con tương ứng.
3. Thêm hoặc sửa test của luật đó trong `tests/test_processing.py`, `tests/test_processing_clauses.py` hoặc `tests/test_processing_flags.py`, chạy test.
4. Tăng `PIPELINE_VERSION` trong `src/processing/__init__.py` (vd `processing-2.0` → `processing-2.1`).
5. Chạy lại lệnh ở mục 3, rồi *Restart* kernel và chạy lại notebook; ghi dòng mới vào bảng phiên bản.

## 6. Dùng kết quả ở bước sau

Từ 20/11 đơn vị phân tích là **cả bình luận** (phương án A). Bảng mệnh đề dưới đây chỉ cần khi muốn xem vị trí bằng chứng hay chạy luật theo mệnh đề.

Đọc file đã xử lý, mỗi mệnh đề một dòng:

```python
import pandas as pd
df = pd.read_json("data/processed/comments.jsonl", lines=True, dtype=False, convert_dates=False)
menh_de = df[["comment_id", "video_id", "model", "clauses"]].explode("clauses", ignore_index=True).dropna(subset=["clauses"])
menh_de = pd.concat([menh_de.drop(columns="clauses").reset_index(drop=True),
                     pd.json_normalize(menh_de["clauses"].tolist())], axis=1)
# cột: comment_id, video_id, model, idx, start, end, text, text_norm (bình luận rỗng không có dòng nào)
```

Gọi thẳng hàm trong code Python khác:

```python
from src.processing import lam_sach, chuan_hoa, tach_menh_de, gan_co
s = lam_sach("Máy ĐẸP quáaaa, ko lag nhưng pin yếu")
chuan_hoa(s)                                  # "máy đẹp quá, không lag nhưng pin yếu"
[m["text"] for m in tach_menh_de(s)]          # ["Máy ĐẸP quáaaa", "ko lag", "nhưng pin yếu"]
gan_co(s)                                     # {"is_vietnamese": True, "is_spam": False, "spam_reasons": []}
```

Trường nào dùng cho việc gì: [đặc tả mục 3](dac-ta.md#3-dùng-trường-nào-cho-việc-gì).

**Công việc 9** (`src/models/sentiment/extract_clauses.py`) đọc được file này. Chạy với `--input data/processed/comments.jsonl --index-base 0` để `clause_idx` đếm từ 0 như contract.

## 7. Lỗi hay gặp

| Thông báo | Cách xử lý |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Chạy lệnh từ gốc repo, có `-m` như mục 3. Trong notebook thì chạy lại ô cài đặt chung |
| `FileNotFoundError: ...models.json` (`1_raw_audit` mục 3) | Thiếu file danh mục máy, xem mục 1 |
| `FileNotFoundError: Chưa có data/processed/comments.jsonl` | Chạy lệnh ở mục 3 trước khi mở các notebook `2_*`, `3_*` |
| Sửa từ điển hay luật mà notebook không đổi | Chạy lại lệnh ở mục 3, rồi *Restart* kernel: module và từ điển chỉ được đọc một lần mỗi phiên |
| "⚠ … chạy lại lệnh tầng 2" trong notebook | File được tạo bằng code khác code hiện tại: chạy lại lệnh ở mục 3 |
| `ValueError: ... khai báo hai lần` / `... cần ít nhất 2 cột` | Sai định dạng file từ điển ở dòng được báo. Kiểm tra dấu TAB giữa các cột |
| `File ra trùng file vào` | Đổi `--output` |
| Notebook chạy rất chậm hoặc treo | Máy thiếu RAM: đóng ứng dụng khác, giảm `MAU`, hoặc chạy từng mục thay vì *Run All* |

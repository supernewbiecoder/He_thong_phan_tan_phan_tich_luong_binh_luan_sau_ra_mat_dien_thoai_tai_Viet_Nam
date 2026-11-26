# Báo cáo tầng 2: EDA, làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ trên dữ liệu v4

> Mục đích: Ghi lại tầng 2 đã làm gì, đang có những gì, số liệu chính, và điều rút ra cho các bước sau; cập nhật lần cuối: 2026-11-20.

**Trạng thái:**
- Mục 1, 2: xong.
- Mục 3.1: số liệu Level 0 và bước 2.1 (làm sạch), lấy từ lần chạy notebook ngày 11/11 trên dữ liệu v4.
- Mục 3.2–3.7: **chờ chạy** notebook bản 19/11 và lệnh tầng 2 (`processing-2.0`). Chạy xong thì chép số từ bảng tổng hợp cuối mỗi notebook (`1_raw_audit` mục 5, `2_2_normalize` mục 7, `2_3_clauses` mục 8) và từ manifest (mục `co`) vào các ô `___`.

Luật: [đặc tả tầng 2](dac-ta.md). Cách chạy: [hướng dẫn](huong-dan.md).

## 1. Đã làm gì

| Ngày | Việc |
|---|---|
| 11/11 | Notebook EDA: đọc dữ liệu, xem dữ liệu gốc, Level 0 (kiểm tra dữ liệu gốc), làm sạch kỹ thuật, in danh sách, ước lượng khía cạnh theo từ khóa. Chạy trên v4 |
| 16/11 | Chuyển code làm sạch từ notebook sang module, giữ nguyên luật; notebook gọi lại module |
| 16/11 | Viết bước chuẩn hóa và từ điển viết tắt 64 mục. Thêm vào notebook mục chuẩn hóa (mỗi bước một ô có ví dụ trước → sau), mục 7 (theo máy, tuần sau ra mắt, bộ 4 máy), mục 8 (kênh, video tặng quà, reply, like), mục 9 (từ vựng, viết tắt, dấu thanh, gõ không dấu) |
| 16/11 | Lệnh chạy ra file kèm manifest có SHA-256; 21 test; đặc tả, hướng dẫn, báo cáo |
| 19/11 | Viết bước 2.3 tách mệnh đề (`clauses.py`), 11 test; lệnh chạy ghi thêm cột `clauses` và thống kê mệnh đề vào manifest; thêm mục mệnh đề vào notebook |
| 19/11 | Tách notebook gộp (123 ô) thành mỗi bước một notebook: `1_raw_audit`, `2_1_clean`, `2_2_normalize`, `2_3_clauses`, `3_aspect_keywords`; hàm dùng chung ở `notebooks/helpers.py`. Ba notebook tầng 2 đọc file đã xử lý và tự kiểm file khớp code |
| 19/11 | Tái cấu trúc repo: đặt lại tên module tiếng Anh theo việc (`clean.py`, `normalize.py`, `clauses.py`, `run.py`); tách đặc tả thành tổng quan tầng + 3 đặc tả con; đặt lại phiên bản code `processing-1.0` (chưa phát hành bản nào trước đó) |
| 20/11 | Chốt phương án A (đơn vị là cả bình luận): mệnh đề chỉ còn là vị trí bằng chứng và đơn vị chấm của luật mốc. Viết bước 2.4 gắn cờ (`flags.py`): nhận tiếng Việt và spam bằng luật mốc, 7 test, [đặc tả](dac-ta-gan-co.md); lệnh chạy ghi thêm 3 cột và thống kê cờ vào manifest; phiên bản lên `processing-2.0` |

**Đã kiểm thế nào:**
- 39/39 test tầng 2 qua; toàn bộ `tests/` của repo qua 291/291 (20/11).
- Cả notebook chạy hết, không lỗi, không cảnh báo, trên bộ dữ liệu giả 3.000 bình luận cùng định dạng v4.
- Ô tự kiểm xác nhận các bước trong notebook cho kết quả giống hệt hàm `chuan_hoa()`.
- Tốc độ đo trên 50.000 bản ghi giả: khoảng 2 phút cho 473.786 bình luận (bước 2.1–2.3), chưa tính đọc/ghi file. Bước 2.4 chưa đo riêng trên mẫu lớn.
- Bước 2.4 chạy trên 3.000 bình luận giả: 446 gắn spam (bộ giả cố ý chứa nhiều link, số điện thoại), 22 không phải tiếng Việt. Số này chỉ để thử code, không nói gì về dữ liệu thật.
- **Chưa chạy trên dữ liệu thật.**

## 2. Đang có những gì

| Thứ | Đường dẫn | Ghi chú |
|---|---|---|
| Notebook | `notebooks/1_raw_audit.ipynb`, `2_1_clean.ipynb`, `2_2_normalize.ipynb`, `2_3_clauses.ipynb`, `3_aspect_keywords.ipynb` | `1_raw_audit` còn output Level 0 của lần chạy 11/11; các notebook khác chưa có output |
| 2.1 Làm sạch | `src/processing/clean.py` | B1–B7 |
| 2.2 Chuẩn hóa | `src/processing/normalize.py` | N1–N7, tách emoji, tách chữ cho EDA |
| Từ điển viết tắt | `src/processing/resources/abbreviations.tsv` | 64 mục; đầu file có danh sách mục cố ý chưa đưa vào |
| 2.3 Tách mệnh đề | `src/processing/clauses.py` | Cắt ở xuống dòng, hết câu, dấu phẩy, từ nối tương phản; gộp mẩu ngắn |
| 2.4 Gắn cờ | `src/processing/flags.py` | `is_vietnamese`, `is_spam`, `spam_reasons` bằng luật mốc, chưa đo |
| Lệnh chạy | `src/processing/run.py` | Đầu ra `data/processed/comments.jsonl` + `comments.manifest.json` (chưa có, chờ chạy) |
| Phiên bản code | `PIPELINE_VERSION` trong `src/processing/__init__.py` | `processing-2.0` |
| Test | `tests/test_processing.py`, `tests/test_processing_clauses.py`, `tests/test_processing_flags.py` | 21 + 11 + 7 test, chạy bằng `unittest` |
| Đặc tả | `docs/2-tien-xu-ly/dac-ta.md` + `dac-ta-lam-sach.md`, `dac-ta-chuan-hoa.md`, `dac-ta-tach-menh-de.md`, `dac-ta-gan-co.md` | 8 quyết định chờ nhóm (đặc tả tổng quan mục 7) |
| Hướng dẫn | `docs/2-tien-xu-ly/huong-dan.md` | |

**Chưa có:** đo luật gắn cờ trên mẫu gán tay (Công việc 11); notebook riêng cho bước 2.4.

## 3. Số liệu

### 3.1 Level 0 và làm sạch (chạy ngày 11/11, dữ liệu v4)

Tỷ lệ tính trên 473.786 bình luận.

| Chỉ số | Giá trị |
|---|---|
| Bình luận × trường | 473.786 × 21 |
| Video có bình luận | 4.682; trong đó 1.027 video (21,9%) có dưới 10 bình luận |
| Thời gian đăng | 11/04/2014 – 20/10/2026 |
| Bình luận rỗng | 42; thêm 5 bình luận chỉ có ký tự vô hình, thành rỗng sau làm sạch (tổng 47) |
| Trùng `comment_id` | 0 |
| Trùng nội dung với bình luận khác | 19.510 (4,12%) |
| Một người đăng lại cùng nội dung | 7.584 (1,60%) |
| Độ dài trung vị | 50 ký tự, 11 từ |
| Bình luận ≤ 2 từ | 26.184 (5,53%) |
| Bình luận > 1.000 ký tự | 328 (0,07%) |
| Chỉ có emoji | 2.433 (0,51%) |
| Có URL / chỉ có URL | 10.682 (2,25%) / 169 (0,04%) |
| Ngôn ngữ (luật đơn giản) | tiếng Việt 445.150 (93,96%); tiếng Việt không dấu 7.811 (1,65%); không rõ 14.080 (2,97%); không có chữ 4.555 (0,96%); tiếng Anh 2.000 (0,42%); ngôn ngữ khác 190 (0,04%) |
| Ngày đột biến | 116 |
| Đăng dồn (≥ 3 lần cùng nội dung trong 10 phút) | 308 nhóm, 1.360 bình luận (0,29%) |
| Video tặng quà trong top 5 video đông nhất | 4/5, cộng lại 15.998 bình luận (3,38%) |
| **Làm sạch phải sửa** | **52.045 bình luận (10,99%)** |
| ↳ B2 HTML entity | 6 |
| ↳ B3 ký tự điều khiển, vô hình | 13.444 (2,84%) |
| ↳ B4 Unicode NFC | 7.506 (1,58%) |
| ↳ B5 xuống dòng | 2.885 (0,61%) |
| ↳ B6 khoảng trắng | 30.676 (6,48%) |

### 3.2 Chuẩn hóa (chờ chạy)

| Chỉ số | Giá trị |
|---|---|
| Bình luận có `<url>` / `<phone>` / `<user>` / `<email>` | ___ |
| N2 chữ thường | ___ |
| N3 dấu thanh | ___ |
| N4 tiếng cười, emoticon, ký tự lặp | ___ |
| N5 dấu câu | ___ |
| N6 viết tắt | ___ |
| Có thay đổi sau chuẩn hóa | ___ |
| Bình luận có emoji | ___ |
| Số chữ khác nhau trước / sau chuẩn hóa | ___ |

### 3.3 Theo máy và thời gian (chờ chạy)

| Chỉ số | Giá trị |
|---|---|
| Số máy có bình luận / máy trong config không có bình luận | ___ |
| Máy có < 3.000 lượt bình luận | ___ |
| % lượt bình luận tuần 1 / 2 / 3 / 4 | ___ |
| Lượt bình luận ngoài tuần 1–4 | ___ |
| Bộ 4 máy ví dụ (s26u, s25u, ip17prm, xiaomi17u): ô khía cạnh có < 30 bình luận nhắc | ___ |

### 3.4 Video, kênh, reply (chờ chạy)

| Chỉ số | Giá trị |
|---|---|
| Số kênh; % bình luận của 5 / 10 kênh lớn nhất | ___ |
| % bình luận theo loại video (review / unbox / compare / long_term) | ___ |
| Video tặng quà; bình luận dưới các video đó | ___ |
| % bình luận là reply; reply theo YouTube / reply đã crawl | ___ |
| % bình luận 0 like | ___ |

### 3.5 Nội dung (chờ chạy)

| Chỉ số | Giá trị |
|---|---|
| Trung vị số chữ / bình luận; % bình luận ≤ 3 chữ | ___ |
| Lượt chữ đặt dấu kiểu cũ / kiểu mới | ___ |
| Ứng viên viết tắt chưa có trong từ điển, gặp ≥ 100 lần | ___ |
| Mục từ điển không gặp lần nào | ___ |

### 3.6 Mệnh đề (chờ chạy)

| Chỉ số | Giá trị |
|---|---|
| Tổng số mệnh đề; trung bình mệnh đề / bình luận | ___ |
| % bình luận có 1 / 2 / 3 / 4 / 5+ mệnh đề | ___ |
| Trung vị số chữ / mệnh đề; % mệnh đề ≤ 1 chữ (gồm mệnh đề chỉ có emoji) | ___ |
| Mệnh đề theo loại ranh giới (xuống dòng / hết câu / dấu phẩy / từ nối) | ___ |
| Mệnh đề dài có chứa "mà" hoặc "còn" (có thể bỏ sót ranh giới) | ___ |

### 3.7 Gắn cờ (chờ chạy)

Lấy từ manifest, mục `co`.

| Chỉ số | Giá trị |
|---|---|
| `is_spam = true` (số, %) | ___ |
| Theo lý do: link / số điện thoại / mời liên hệ / cờ bạc, lừa đảo | ___ |
| `is_vietnamese = false` (số, %) | ___ |
| Theo lý do: có dấu / không dấu hợp lệ / không đủ chữ / chữ khác Latin / không dấu ngoại ngữ | ___ |

## 4. Điều rút ra cho các bước sau

Từ số liệu đã có (mục 3.1):

1. **Dữ liệu sạch về kỹ thuật.** Không trùng `comment_id`, rỗng không đáng kể. Bước làm sạch sửa 11% bình luận, nhưng toàn bộ là lỗi lưu trữ (khoảng trắng, ký tự vô hình, Unicode, xuống dòng): không đổi nghĩa.
2. **Bình luận trùng nội dung chiếm 4,12%, một người đăng lại cùng nội dung 1,60%.** Chưa biết bao nhiêu trong đó là câu ngắn tự nhiên ("hay", "đẹp"). Nhóm đáng ngờ hơn là 1.360 bình luận đăng dồn trong 10 phút. Bước lọc spam và câu Q6 (tài khoản ảo) cần xem riêng từng nhóm, không xóa hết bình luận trùng.
3. **Video tặng quà là nguồn nhiễu lớn nhất đã thấy.** 4/5 video đông nhất là video tặng quà, kéo về khoảng 16 nghìn bình luận "xin suất". `1_raw_audit` mục 4.3 sẽ đếm đủ; nhóm cần quyết giữ hay loại (đặc tả tổng quan, quyết định 3).
4. **Khoảng 6% không phải tiếng Việt có dấu** (không dấu, không rõ, không có chữ, tiếng Anh, khác). Đó là đầu vào cho bước `is_vietnamese`. Luật ở `1_raw_audit` mục 2.7 mới là ước lượng, cần kiểm bằng mẫu gán tay.
5. **Gõ không dấu chỉ khoảng 1,7%** số bình luận tiếng Việt. Chuẩn hóa không thêm dấu; với tỷ lệ này, bỏ qua khôi phục dấu là chấp nhận được, nhưng từ khóa và mô hình vẫn nên chịu được cả hai dạng.
6. **Bình luận rất ngắn (≤ 2 từ) chiếm 5,5%.** Khi lấy mẫu gán nhãn (Công việc 1) nên lọc bớt, vì gần như không có khía cạnh.
7. **Máy của video chưa phải máy được nhắc.** Mọi bảng theo máy (`1_raw_audit` mục 3, `3_aspect_keywords` mục 3) đều tính theo máy của video. Kết luận theo máy phải chờ Công việc 10.

Phần còn lại điền sau khi chạy các notebook.

## 5. Việc tiếp theo

1. **Chạy** lệnh tầng 2 ([hướng dẫn](huong-dan.md) mục 3) rồi các notebook (hướng dẫn mục 2), điền số vào mục 3.2–3.7, ghi dòng phiên bản vào [đặc tả tổng quan](dac-ta.md) mục 6.
2. **Chốt 8 quyết định** ở [đặc tả tổng quan mục 7](dac-ta.md#7-quyết-định-đang-chờ-nhóm): kiểu dấu thanh, mục viết tắt nhập nhằng, video tặng quà, `author_name`, chữ không dấu, cột đặc trưng phụ, luật tách mệnh đề, luật gắn cờ.
3. **Công việc 11:** đo luật gắn cờ ([đặc tả](dac-ta-gan-co.md)) bằng nhãn mẫu A ([đặc tả gán nhãn mục 3](../3-gan-nhan/dac-ta.md#3-mẫu-a-chất-lượng-dữ-liệu)); trước đó đọc mẫu theo từng lý do trong `spam_reasons`.
4. **Công việc 2:** dùng `1_raw_audit` mục 3.1, 3.4 và `3_aspect_keywords` mục 3 để chốt bộ 4 máy.
5. **Công việc 1:** lấy hai mẫu theo [đặc tả gán nhãn](../3-gan-nhan/dac-ta.md): mẫu A từ dữ liệu **chưa lọc** (để đo bộ lọc và ước lượng chất lượng), mẫu B đã lọc spam, ngoại ngữ, bình luận quá ngắn (tập test mô hình). Bản trước của mục này chỉ dặn lấy mẫu đã lọc: sai, vì như vậy không đo được bộ lọc loại nhầm bao nhiêu.
6. **Công việc 9:** nhãn LLM cũ gán theo mệnh đề; gán lại theo bình luận khi có guideline v1.

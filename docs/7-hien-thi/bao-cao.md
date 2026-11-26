# Báo cáo tầng 7: dashboard đọc từ DB qua API (Công việc 13)

> Mục đích: Báo cáo việc chuyển dashboard từ file JSON tĩnh sang đọc MongoDB qua API: đã làm gì, kiểm chứng thế nào, còn hạn chế gì; bản 17/11 và phần chuyển về `main` ngày 26/11; cập nhật lần cuối: 2026-11-26.

Người thực hiện: Nguyễn Lê Quân. Cách chạy và mô tả kỹ thuật: [hướng dẫn tầng 7](huong-dan.md).

**Ghi chú 26/11:** mục 1–5 là bản 17/11 trên nhánh `nlquan`, giữ nguyên số liệu lúc đó (dữ liệu `clean_data.jsonl` v1.0, contract v2, 9 khía cạnh cũ). Phần chuyển về `main` theo bộ nhãn chốt và contract v3 ở [mục 6](#6-chuyển-về-main-ngày-2611).

## 1. Đã làm gì

| Trước | Sau |
|---|---|
| Một file `index.html` 161 KB nhúng sẵn số liệu sinh từ luật từ khóa | Trang web gọi API; API đọc MongoDB theo [thiết kế dữ liệu](../0-chung/thiet-ke-du-lieu.md). Không còn số nào nằm trong mã nguồn trang |
| Số liệu minh họa không được đánh dấu trên từng biểu đồ | API tự xác định số liệu có phải minh họa không từ nguồn nhãn và kết quả Công việc 12; trang hiện băng cảnh báo kèm lý do và gắn chip lên từng biểu đồ |
| % khen, % chê tính ở nhiều chỗ | Một hàm duy nhất tính mọi tỷ lệ từ số đếm |
| Có "dự báo tuần 8" và phân cụm | Đã bỏ; không có ngoại suy |
| Phụ thuộc Google Fonts | Không dùng thư viện hay font ngoài, chạy được khi mất mạng lúc demo |

Bốn tab theo kế hoạch của nhóm: **Theo dõi ra mắt** (Q1, Q2, Q5, cảnh báo), **So sánh mẫu máy** (Q3a, Q3b, Q4), **Sức khỏe hệ thống**, **Tổng quan dữ liệu**.

![Tab Theo dõi ra mắt, chạy trên số liệu minh họa](hinh-dashboard/cv13-theo-doi-ra-mat.png)

![Tab So sánh mẫu máy](hinh-dashboard/cv13-so-sanh-mau-may.png)

![Tab Sức khỏe hệ thống, giao diện tối](hinh-dashboard/cv13-suc-khoe-he-thong.png)

Ba ảnh trên chụp khi DB chứa **số liệu minh họa** do `demo_data.py` (đã gỡ ngày 26/11) sinh bằng luật từ khóa. Chúng cho thấy giao diện, không phải kết quả phân tích.

## 2. Cách xử lý số liệu minh họa

Yêu cầu của công việc: chỗ nào còn số liệu minh họa phải ghi rõ. Thay vì gắn nhãn bằng tay, API quyết định từ dữ liệu. Số liệu chỉ được coi là **không** minh họa khi đủ cả bốn điều kiện:

1. mọi nhãn của phiên bản đang xem có nguồn `model` hoặc `human` (không có `rule`, `llm`, và không có mention nào thiếu nguồn);
2. có kết quả kiểm định của Công việc 12 cho máy và phiên bản đó;
3. số đếm trong kết quả đó khớp với số đếm trong DB;
4. Công việc 12 không nêu lý do chặn công bố nào và dữ liệu không phải fixture.

Thiếu điều kiện nào thì băng cảnh báo nêu đúng lý do đó; băng không bao giờ hiện mà không có lý do. Nhãn đã kiểm chứng nhưng không có khác biệt nào có ý nghĩa thống kê vẫn là số liệu thật, hiển thị với kết luận "Chưa đủ bằng chứng". Hiện chưa có bộ nhãn nào qua được điều kiện 1, nên mọi biểu đồ ở hai tab phân tích đều mang chữ "Số liệu minh họa".

## 3. Kiểm chứng

| Kiểm chứng | Kết quả |
|---|---|
| 61 test tự động cho API, script nạp DB, bộ sinh số liệu minh họa (mongomock) | Đạt |
| Chạy lại đúng 61 test đó trên MongoDB 7.0 thật | Đạt |
| Nạp dữ liệu thật vào MongoDB 7.0: 109.344 bình luận, 75.387 mention minh họa (mỗi mention được kiểm theo contract v2), 7.219 dòng aggregates | Đạt |
| Chạy code Công việc 12 (nhánh `task12`) trên cùng mentions, so với số đếm của phần này | 1.573/1.573 dòng aggregates trùng khóa và trùng số đếm |
| Nạp `business_questions.json` do code Công việc 12 sinh ra, để API đối chiếu | Khớp 56/56 ô; khoảng tin cậy và kiểm định hiển thị được |
| Số lượt so sánh trực tiếp (Q3b) và số lượt nhắc lỗi (Q5) API đếm từ `aspect_mentions` so với Công việc 12 | Trùng ở cả 9 khía cạnh và 9 loại lỗi |
| Mở 4 tab bằng Chrome, giao diện sáng và tối, rộng 1320 px và 390 px | Không có lỗi console, không tràn ngang |
| Bảng màu biểu đồ qua công cụ kiểm tra khả năng phân biệt cho người mù màu | Đạt ở cả hai giao diện |

Một test đã bắt được lỗi trong lúc làm: dữ liệu fixture có cờ "được công bố" từng không bị gắn nhãn minh họa. Đã sửa và giữ test.

Sau khi viết xong, một lượt review độc lập đọc lại toàn bộ code và tìm thêm lỗi. Những lỗi đáng kể nhất, đều đã sửa và có test riêng:

| Lỗi | Hậu quả nếu không sửa |
|---|---|
| Nạp mention của phiên bản nhãn mới ghi đè một phần mention của phiên bản cũ (vì `mention_id` không chứa phiên bản) | Chọn phiên bản cũ trên dashboard sẽ thấy Q1–Q4 đầy đủ nhưng Q5, Q3b và bình luận mẫu thiếu, không có cảnh báo |
| Nạp file chỉ gồm vài máy xóa luôn số đếm của các máy khác cùng phiên bản | Mất dữ liệu khi nạp đầu ra 4 máy của Công việc 12 đè lên bộ đầy đủ |
| Máy mặc định lấy theo lần phân tích mới nhất dù DB không có số đếm cho nó | Trang mở ra báo lỗi và không chọn lại được |
| Băng "số liệu minh họa" hiện mà không có lý do khi nhãn đã kiểm chứng nhưng không có kết quả có ý nghĩa | Số liệu thật bị gọi nhầm là minh họa |
| Thông báo lỗi 503 chứa nguyên chuỗi kết nối MongoDB | Lộ mật khẩu DB nếu chuỗi kết nối có mật khẩu |
| Giá trị không phải số trong DB được chèn thẳng vào trang | Chèn được HTML nếu ai đó ghi chuỗi vào trường số |

## 4. Phát hiện cần cả nhóm xử lý

1. **`clean_data.jsonl` v1.0 không có trường `author_is_creator`.** Contract v2 bắt buộc trường này. Code Công việc 12 từ chối cả 75.387 mention với lỗi `REFERENCE_MISMATCH` cho tới khi bình luận nguồn có trường đó. Để chạy được phép đối chiếu ở mục 3, tôi dùng một bản sao tạm của dữ liệu có thêm `author_is_creator = false`; bản sao này không nằm trong repo. Dữ liệu chuẩn cần được bổ sung trường này ở crawler hoặc tiền xử lý.
2. **Chưa có nơi chuẩn để dashboard đọc kết quả Công việc 12 từ DB.** Phần này dùng tạm collection `analysis_results`; cần đưa vào data-model.md hoặc chọn nơi khác. (26/11: đã thêm vào `src/storage/init_db.py` và thiết kế dữ liệu.)
3. **`predecessor` chưa có trong `config/pipeline.yaml`** (Công việc 2). Khi không có cấu hình phân tích cho một máy, Q4 không vẽ được và trang ghi rõ lý do.

## 5. Hạn chế

- Chưa có đầu ra mô hình thật để hiển thị; mọi số ở hai tab phân tích hiện là minh họa.
- Tab hệ thống chỉ đo độ trễ của chính API. Thông lượng, độ trễ xử lý và consumer lag thuộc luồng Kafka/Spark chưa dựng, nên trang ghi "chưa triển khai" thay vì hiện số.
- Tab cảnh báo chỉ đọc collection `alerts`; chưa có thành phần nào ghi vào đó.
- Tab tổng quan quét toàn bộ `comments` mỗi 30 giây khi có người xem (khoảng 2 giây với 109 nghìn bình luận). Dữ liệu lớn hơn nhiều thì cần bảng đếm sẵn.
- Không có word cloud vì DB không lưu tần suất từ.
- `index.html` cũ bị thay hoàn toàn. Nhánh `task12` cũng sửa file này (bỏ phần dự báo), nên khi hai nhánh cùng vào `main` sẽ có xung đột ở file đó; cách giải quyết là giữ bản mới.

## 6. Chuyển về `main` ngày 26/11

| Thay đổi | Lý do |
|---|---|
| Khía cạnh lấy từ bộ nhãn chốt (`src/labeling/final_labels.py`): 11 khía cạnh thay cho 9 khía cạnh cũ | Bộ nhãn chốt 26/11; không chép tay danh sách nhãn |
| Đếm thêm `n_cmp` (thái độ `so_sanh`), không vào mẫu số % khen, % chê | Contract v3: câu so sánh có thái độ riêng |
| Q5 theo khía cạnh (lời chê của người đã dùng máy) thay cho 9 loại lỗi | Bộ loại lỗi chưa chốt (kế hoạch tổng thể bước 2.6) |
| `load_db.py` chuyển sang `src/storage/`, đọc file tầng 2 (`processing-2.0`), giữ `pipeline_version` của tầng 2, bỏ `author_name` | Một chỗ nạp DB duy nhất; bản 17/11 ghi đè sai phiên bản tầng 2 |
| Bỏ `demo_data.py` | Bước suy luận `rule-v1.1` của chuỗi theo lô đã sinh số liệu minh họa đúng contract |
| Lý do spam trên tab hệ thống theo 4 mã của `src/processing/flags.py` | Luật `cleaner/` cũ đã gỡ |
| Thêm bước `nap_db` vào `python -m src.run` | Chạy một lệnh từ dữ liệu thô tới DB cho dashboard |

Kiểm chứng trên dữ liệu v4: ___ (chờ chạy, xem [kế hoạch mục 4](../0-chung/ke-hoach.md)).

# Hướng dẫn chạy kiểm tra cấu trúc dữ liệu

> Mục đích: Cách chạy notebook `1_raw_audit` (bước B1 của kế hoạch nhánh): cần gì, chạy thế nào, notebook đo những gì, tham số nào hay đổi, làm gì sau khi chạy, lỗi hay gặp; cập nhật lần cuối: 2026-11-22.

Lệnh viết cho **PowerShell trên Windows**, chạy từ **gốc repo**. Nhánh này dùng chung thư mục với `main`: chuyển sang nhánh `kham-pha-nhan` trong GitHub Desktop (*Current branch*) trước khi làm. Kết quả đã chạy: [báo cáo kiểm tra dữ liệu](bao-cao-kiem-tra-du-lieu.md).

## 1. Cần có trước

| Thứ | Ở đâu | Ghi chú |
|---|---|---|
| Dữ liệu v4 | `src/ingest/data/raw/comments.jsonl`, `videos.jsonl`, `src/ingest/data/models.json` | Kiểm số dòng và SHA-256 theo [đặc tả dữ liệu mục 3](dac-ta.md#3-phiên-bản) |
| Python 3.11 có pandas, numpy, matplotlib, PyYAML, ipykernel | Một trong hai cách dưới | |
| Vài GB RAM trống | | Notebook nạp cả 473.786 bình luận vào bộ nhớ |

**Môi trường Python**, chọn một trong hai cách:
- **Dùng `.venv` đã có trong thư mục repo** (nhanh nhất): `.venv` nằm ngoài git nên vẫn còn khi chuyển nhánh. Trong VS Code chọn kernel → *Python Environments* → `.venv`.
- **Tạo môi trường riêng cho nhánh:**

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

## 2. Chạy

1. Trong GitHub Desktop, chuyển *Current branch* sang `kham-pha-nhan`. VS Code đang mở thư mục repo sẽ tự hiện các file của nhánh.
2. Mở `notebooks/1_raw_audit.ipynb`, chọn kernel (mục 1), bấm *Run All*. Mất vài phút.
3. Notebook chỉ đọc và đếm, **không ghi file nào**.

## 3. Notebook đo những gì

| Mục | Nội dung |
|---|---|
| 1. Đọc dữ liệu | 21 trường, số ô trống từng trường; xem dữ liệu 100 dòng một trang |
| 2. Level 0 | 2.1 video và số bình luận mỗi video · 2.2 bình luận rỗng · 2.3 trùng lặp · 2.4 độ dài · 2.5 chỉ có emoji · 2.6 chỉ có URL · 2.7 ngôn ngữ · 2.7b gõ không dấu · 2.8 thời gian, ngày tăng đột biến · 2.9 nhiều bình luận giống nhau đăng dồn · bảng tổng hợp Level 0 |
| 3. Theo máy, thời gian | 3.1 số bình luận theo máy · 3.2 theo ngày sau ra mắt · 3.3 theo ngày, từng máy · 3.4 bộ 4 máy ứng viên |
| 4. Video, kênh, reply, like | 4.1 theo kênh · 4.2 theo loại video · 4.3 video tặng quà · 4.4 reply và chủ kênh · 4.5 like |
| 5. Tổng hợp | Các số chính của mục 3–4 trên một bảng |

Tất cả là **cấu trúc** dữ liệu: các trường có sẵn. Notebook không đo bình luận nói về cái gì. Phần đó là bước khám phá nhãn (B2–B7 của [kế hoạch](../0-chung/ke-hoach.md)).

## 4. Tham số hay đổi

Sửa trong ô rồi chạy lại ô đó và các ô sau.

| Tham số | Ở đâu | Ý nghĩa |
|---|---|---|
| `TRANG` | Mục 1 | Lật trang khi xem dữ liệu (trang 0 = dòng 0–99) |
| `AN_COT` | Mục 1 | Cột bị ẩn khi xem; mặc định ẩn `author_name` (dữ liệu cá nhân) |
| `NGUONG_BINH_LUAN` | Mục 3.1 | Máy có ít hơn số lượt này bị đánh dấu ⚠ (mặc định 3.000, ngưỡng tạm) |
| `MAY_XEM` | Mục 3.3 | Các máy vẽ trên biểu đồ theo ngày |
| `BO_MAY` | Mục 3.4 | Bộ 4 máy; mặc định đọc từ `config/analysis.yaml` |
| `QUA_RE` | Mục 4.3 | Từ khóa nhận video tặng quà theo tiêu đề |
| `N_SHOW` | `notebooks/helpers.py` | Số dòng in ra ở mỗi danh sách |

## 5. Sau khi chạy

1. Chép số từ bảng tổng hợp cuối mục 2 và mục 5 vào [báo cáo kiểm tra dữ liệu](bao-cao-kiem-tra-du-lieu.md), thay các ô `___`. Ghi ngày chạy.
2. **Trước khi commit notebook, chọn *Clear All Outputs* rồi lưu.** Output có nội dung bình luận thật, và `.gitignore` không chặn được output nằm trong notebook.

## 6. Lỗi hay gặp

| Thông báo | Cách xử lý |
|---|---|
| `FileNotFoundError: Không tìm thấy gốc repo` | Đang mở notebook ngoài thư mục nhánh, hoặc thiếu `config/pipeline.yaml` |
| `FileNotFoundError: …comments.jsonl` hoặc `…models.json` | Chưa chép dữ liệu đúng chỗ (mục 1) |
| `ModuleNotFoundError: No module named 'yaml'` (hoặc `pandas`) | Kernel đang chọn thiếu thư viện: chọn lại kernel hoặc cài `requirements.txt` |
| Notebook rất chậm hoặc treo | Thiếu RAM: đóng ứng dụng khác, hoặc chạy từng mục thay vì *Run All* |

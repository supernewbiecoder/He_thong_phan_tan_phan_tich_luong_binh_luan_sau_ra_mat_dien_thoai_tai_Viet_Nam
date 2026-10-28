# Module Tiền Xử Lý Dữ Liệu (Processing)

> **Mục đích**: Tiền xử lý dữ liệu thô từ crawler (`comments.jsonl`), chuẩn hóa văn bản (`text_norm`), lọc spam Precision-First, nhận diện tiếng Việt (`is_vietnamese`), bóc tách câu thành mệnh đề độc lập (`clauses`) và ghi vết biến đổi dữ liệu (`cleaning_trace.jsonl`).  
> **Cập nhật lần cuối**: 2026-10-28 (Hoàn thành Công việc 6 theo [docs/roadmap.md](../../docs/roadmap.md)).

---

## 1. Cấu trúc Thư mục

Theo quy định của GitHub, các tệp dữ liệu lớn (> 100MB) **không được commit trực tiếp vào Git** (đã được chặn trong `.gitignore`). Cấu trúc thư mục chuẩn của dự án:

```text
He_thong_phan_tan_phan_tich_luong_binh_luan_sau_ra_mat_dien_thoai_tai_Viet_Nam/
├── config/
│   └── pipeline.yaml               # Cấu hình danh mục máy & crawler
├── data/                           # [BẮT BUỘC] Thư mục chứa dữ liệu (được .gitignore bảo vệ)
│   ├── comments.jsonl              # [ĐẦU VÀO] Dữ liệu thô tải từ Google Drive (109.344 dòng, ~65.87 MB)
│   ├── clean_data.jsonl            # [ĐẦU RA] Dữ liệu sạch do run_cleaning sinh ra (109.344 dòng, ~116.52 MB)
│   ├── cleaning_trace.jsonl        # File diff ghi vết biến đổi từng bản ghi (~85.29 MB)
│   └── cleaning_summary.json       # Thống kê tổng kết chất lượng dữ liệu
├── src/
│   ├── ingest/                     # Module cào và Replay dữ liệu YouTube
│   ├── processing/                 # [MODULE NÀY] Code làm sạch và bóc tách dữ liệu
│   │   ├── cleaner/                # Thư viện core: chuẩn hóa, lọc spam, tách mệnh đề
│   │   │   ├── config.py           # Từ điển teencode, regex spam, từ nối mệnh đề
│   │   │   ├── text_normalizer.py  # Chuẩn hóa Unicode NFC, khoảng trắng, teencode
│   │   │   ├── spam_detector.py    # Lọc spam Precision-First và nhận diện tiếng Việt
│   │   │   ├── clause_segmenter.py # Tách mệnh đề theo dấu câu & liên từ
│   │   │   └── pipeline.py         # Hàm điều phối xử lý từng record
│   │   ├── run_cleaning.py         # SCRIPT CHẠY 1 LỆNH để làm sạch và sinh ra clean_data.jsonl
│   │   ├── test_cleaner.py         # Script kiểm thử nhanh (Unit Test)
│   │   ├── eda_smartphone_comments.ipynb # Notebook phân tích dữ liệu EDA
│   │   └── README.md               # Tài liệu hướng dẫn này
│   └── serving/                    # Dashboard hiển thị kết quả
```

---

## 2. Quy Trình Chuẩn Duy Nhất Để Sinh Dữ Liệu Sạch (`clean_data.jsonl`)

Để đảm bảo cả 11 thành viên trong nhóm dùng chung một phiên bản dữ liệu thống nhất và có thể tái lập kết quả phân tích 100%, **quy trình duy nhất** gồm 2 bước sau:

### Bước 1: Tải `raw_data` (`comments.jsonl`) vào thư mục `data/`

Tải tập dữ liệu thô `comments.jsonl` từ liên kết Google Drive chính thức của nhóm:
* **Google Drive Link**: [https://drive.google.com/file/d/1Rk5rAUm_xer0v2Hng-oPe03SKY8_oI_U/view?usp=sharing](https://drive.google.com/file/d/1Rk5rAUm_xer0v2Hng-oPe03SKY8_oI_U/view?usp=sharing)

#### Lệnh tải 1 dòng tự động bằng Terminal (tại thư mục gốc repository):

* **Windows (PowerShell)**:
  ```powershell
  # Tạo thư mục data nếu chưa có
  New-Item -ItemType Directory -Force -Path data

  # Tải trực tiếp comments.jsonl vào data/
  curl.exe -L -o data/comments.jsonl "https://drive.usercontent.google.com/download?id=1Rk5rAUm_xer0v2Hng-oPe03SKY8_oI_U&confirm=t"
  ```
  *(Hoặc dùng lệnh `Invoke-WebRequest -Uri "https://drive.usercontent.google.com/download?id=1Rk5rAUm_xer0v2Hng-oPe03SKY8_oI_U&confirm=t" -OutFile "data/comments.jsonl"`)*

* **Linux / macOS**:
  ```bash
  mkdir -p data
  curl -L -o data/comments.jsonl "https://drive.usercontent.google.com/download?id=1Rk5rAUm_xer0v2Hng-oPe03SKY8_oI_U&confirm=t"
  ```

*(Nếu tải bằng trình duyệt, sau khi tải xong bạn chỉ cần lưu tệp vào đường dẫn `<repo_root>/data/comments.jsonl`).*

---

### Bước 2: Chạy 1 lệnh để làm sạch và sinh ra `clean_data.jsonl`

Tại thư mục gốc của repository, chạy lệnh duy nhất:
```bash
python src/processing/run_cleaning.py
```

* **Cơ chế hoạt động**:
  1. Script tự động đọc `data/comments.jsonl` (chế độ Read-Only, không ghi đè dữ liệu thô).
  2. Thực thi toàn bộ luồng tiền xử lý: giải mã HTML, chuẩn hóa Unicode NFC, nén ký tự lặp, thay thế teencode, lọc spam Precision-First và bóc tách câu thành các mệnh đề độc lập.
  3. Tự động xuất kết quả sạch vào đúng vị trí: **`data/clean_data.jsonl`**.
  4. Xuất file ghi vết diff vào: **`data/cleaning_trace.jsonl`**.
  5. Xuất báo cáo thống kê vào: **`data/cleaning_summary.json`**.
* **Hiệu năng**: Xử lý toàn bộ **109.344 bản ghi** chỉ mất khoảng **~36 giây** (~3.000 dòng/giây).

---

### Bước 3: Xác thực tính toàn vẹn (Kiểm tra Checksum)

Sau khi chạy xong, hãy kiểm tra đối chiếu dữ liệu vừa tạo với phiên bản chuẩn của nhóm:
```bash
python src/processing/run_cleaning.py --verify
```
* Nếu hiển thị: `[SUCCESS] XÁC THỰC THÀNH CÔNG! Dữ liệu trùng khớp 100% với phiên bản chuẩn v1.0 của nhóm.` thì máy bạn đã sẵn sàng chạy Notebook EDA hoặc huấn luyện mô hình.

---

## 3. Bảng Phiên Bản Dữ Liệu & Checksum (Gold Dataset v1.0)

Bảng đối chiếu số dòng và mã băm SHA-256 để cả nhóm kiểm tra:

| Tên tệp | Phiên bản | Số dòng (Lines) | Dung lượng (Size) | Mã băm SHA-256 Checksum | Trạng thái & Ghi chú |
|:---|:---:|:---:|:---:|:---|:---|
| **`comments.jsonl`** | `raw-v2.0` | **109.344** | 65.871.686 bytes (~62.82 MB) | `976eb7e9686b2a91459422760bfea4a11e0f2e23f050eb78eaea1e4806e68950` | Dữ liệu thô tải từ Google Drive (Read-Only) |
| **`clean_data.jsonl`** | `v1.0 (Official)` | **109.344** | 116.522.265 bytes (~111.12 MB) | `df4c72c25a150108283fc54e7e6d1dd15a969b907088e168eb7a7405f1ea58ab` | **BẢN CHUẨN CẢ NHÓM DÙNG CHUNG**. Sinh từ `run_cleaning.py` |
| **`cleaning_trace.jsonl`**| `v1.0 (Trace)`| **109.344** | 85.285.624 bytes (~81.33 MB) | `50c38a5697e9a0564c0a2517483566158888359ba28fb0cafe4d75c40f5fabf2` | File diff ghi vết mọi thay đổi trước/sau làm sạch |
| **`cleaning_summary.json`**| `v1.0 (Report)`| 100 | 2.721 bytes (~2.66 KB) | `30dc14dc4d94de98d6a708dde9e06e741c8b468f9efade898d61fe158dc60f19` | Báo cáo chi tiết tỷ lệ spam, phân bổ mệnh đề, top teencode |

### Lệnh kiểm tra Checksum bằng công cụ hệ điều hành:
* **Windows (PowerShell)**:
  ```powershell
  Get-FileHash -Algorithm SHA256 data/clean_data.jsonl | Format-List
  ```
  *(Kỳ vọng: `DF4C72C25A150108283FC54E7E6D1DD15A969B907088E168EB7A7405F1EA58AB`)*
* **Linux / macOS**:
  ```bash
  sha256sum data/clean_data.jsonl
  ```

---

## 4. Kiểm Thử Nhanh (Unit Test)

Để kiểm tra các bộ quy tắc chuẩn hóa văn bản, từ điển teencode, lọc spam và tách mệnh đề:
```bash
python src/processing/test_cleaner.py
```

---

## 5. Thống Kê Chất Lượng Dữ Liệu (Trích xuất từ Báo cáo)

* **Tổng số bình luận xử lý**: `109.344` bình luận.
* **Bình luận hợp lệ (Non-spam)**: `106.111` (`97.04%`).
* **Bình luận Spam bị gắn cờ loại bỏ**: `3.233` (`2.96%`).
* **Tổng số từ teencode được chuẩn hóa**: `58.925` từ (`ko -> không`: 14.710 lần, `k -> không`: 7.869 lần, `ip -> iphone`: 7.634 lần, `đc -> được`: 4.979 lần, `pin trau -> pin trâu`, `sac nhanh -> sạc nhanh`...).
* **Tổng số mệnh đề bóc tách**: `235.859` mệnh đề (Trung bình `2.16` mệnh đề/bình luận).
* **Tốc độ làm sạch**: **~36.65 giây** toàn bộ tập dữ liệu (~2.983 dòng/giây).

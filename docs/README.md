# Mục lục tài liệu

> Mục đích: Danh sách mọi tài liệu của dự án, xếp theo tầng xử lý, kèm quy tắc đặt tên và chỗ để tài liệu mới; cập nhật lần cuối: 2026-11-26.

**Cách đọc:** người mới đọc mục 1 (chung) rồi tới tầng mình phụ trách. Cần biết dự án đang tới đâu, ai làm gì thì đọc [kế hoạch](0-chung/ke-hoach.md).

## 1. Tài liệu theo tầng

Mỗi tầng xử lý có một thư mục, đánh số đúng thứ tự dữ liệu đi qua, và ứng với một thư mục code.

| Thư mục | Tầng | Code | Tài liệu |
|---|---|---|---|
| `0-chung/` | Dùng chung mọi tầng | | [ke-hoach.md](0-chung/ke-hoach.md): tình hình, việc tiếp theo, quyết định đang chờ, tiến độ và yêu cầu 15 công việc · [muc-tieu.md](0-chung/muc-tieu.md): đề tài, câu hỏi Q1–Q6, quy ước thống kê · [thiet-ke-du-lieu.md](0-chung/thiet-ke-du-lieu.md): các bảng, trường, mã nhãn (contract v3) · [luong-xu-ly.md](0-chung/luong-xu-ly.md): các bước xử lý, streaming tùy chọn · [kien-truc.mmd](0-chung/kien-truc.mmd) / [.svg](0-chung/kien-truc.svg): sơ đồ · [cai-dat.md](0-chung/cai-dat.md): dựng môi trường · [ban-do-code.md](0-chung/ban-do-code.md): file code nào để làm gì · [huong-dan-su-co-streaming.md](0-chung/huong-dan-su-co-streaming.md) · [ke-hoach-tong-the.md](0-chung/ke-hoach-tong-the.md): lộ trình 7 giai đoạn từ bàn giao bộ nhãn tới báo cáo cuối (đề xuất 26/11) · [ke-hoach-kham-pha-nhan.md](0-chung/ke-hoach-kham-pha-nhan.md): kế hoạch và quyết định của nhánh khám phá nhãn B1–B8 (xong 26/11) · [bao-cao-qua-trinh.md](0-chung/bao-cao-qua-trinh.md): sổ ghi chép từng đợt của nhánh khám phá nhãn · [huong-dan-tom-tat.md](0-chung/huong-dan-tom-tat.md): giải thích dễ hiểu nhánh khám phá nhãn |
| `1-thu-thap/` | 1. Thu thập bình luận YouTube | `src/ingest/` | [dac-ta.md](1-thu-thap/dac-ta.md) · [huong-dan.md](1-thu-thap/huong-dan.md): chạy crawler · [huong-dan-crawl-2-may.md](1-thu-thap/huong-dan-crawl-2-may.md) · [dac-ta-du-lieu-v4.md](1-thu-thap/dac-ta-du-lieu-v4.md): dữ liệu v4, các trường, điều phải nhớ khi đọc · [huong-dan-kiem-tra-du-lieu.md](1-thu-thap/huong-dan-kiem-tra-du-lieu.md): chạy notebook `1_raw_audit` · [bao-cao-kiem-tra-du-lieu.md](1-thu-thap/bao-cao-kiem-tra-du-lieu.md): số liệu cấu trúc v4 (22/11) |
| `2-tien-xu-ly/` | 2. Làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ | `src/processing/` | [dac-ta.md](2-tien-xu-ly/dac-ta.md): tổng quan tầng · [dac-ta-lam-sach.md](2-tien-xu-ly/dac-ta-lam-sach.md) ↔ `clean.py` · [dac-ta-chuan-hoa.md](2-tien-xu-ly/dac-ta-chuan-hoa.md) ↔ `normalize.py` · [dac-ta-tach-menh-de.md](2-tien-xu-ly/dac-ta-tach-menh-de.md) ↔ `clauses.py` · [dac-ta-gan-co.md](2-tien-xu-ly/dac-ta-gan-co.md) ↔ `flags.py` · [huong-dan.md](2-tien-xu-ly/huong-dan.md): notebook kiểm tra dữ liệu và lệnh chạy · [bao-cao.md](2-tien-xu-ly/bao-cao.md) |
| `3-gan-nhan/` | 3. Gán nhãn: **dùng tiếp** | `src/labeling/` | [dac-ta-bo-nhan.md](3-gan-nhan/dac-ta-bo-nhan.md) ↔ `src/labeling/label_set.py`, `final_labels.py`: bộ nhãn 6 chiều, định nghĩa, ví dụ; **bộ nhãn chốt ở mục 8** · [huong-dan-gan-nhan-chinh-thuc.md](3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md): cách gán theo bộ nhãn chốt (duyệt 26/11) · [dac-ta.md](3-gan-nhan/dac-ta.md) ↔ `sheet.py`, `check_sheet.py`, `estimate.py`: hai mẫu (chất lượng dữ liệu, tập test), phiếu, gán đôi, phân xử, ước lượng |
| `3-gan-nhan/` | 3. Khám phá nhãn B2–B8 (22–26/11): **hồ sơ quá trình** | `src/labeling/` | [dac-ta-kham-pha-nhan.md](3-gan-nhan/dac-ta-kham-pha-nhan.md): thuật ngữ, lấy mẫu, HAC, mã hóa mở, bão hòa, đồng thuận, công thức phân bố, luật chốt bộ nhãn · [huong-dan-kham-pha-nhan.md](3-gan-nhan/huong-dan-kham-pha-nhan.md) · [huong-dan-gan-lo-k.md](3-gan-nhan/huong-dan-gan-lo-k.md) · [bao-cao-ma-hoa-mo.md](3-gan-nhan/bao-cao-ma-hoa-mo.md) · [bao-cao-bo-nhan.md](3-gan-nhan/bao-cao-bo-nhan.md) · [bao-cao-lo-k.md](3-gan-nhan/bao-cao-lo-k.md) · [bao-cao-phan-bo-nhan.md](3-gan-nhan/bao-cao-phan-bo-nhan.md): phân bố nhãn trên v4 có khoảng tin cậy · [bao-cao-kham-pha-nhan.md](3-gan-nhan/bao-cao-kham-pha-nhan.md): so ba nguồn, chốt bộ nhãn · [bao-cao-lo-d2.md](3-gan-nhan/bao-cao-lo-d2.md) |
| `4-mo-hinh/` | 4. Suy luận, mô hình khía cạnh, cảm xúc | `src/models/` | [dac-ta.md](4-mo-hinh/dac-ta.md): dữ liệu huấn luyện, chia tập, đánh giá · [dac-ta-suy-luan.md](4-mo-hinh/dac-ta-suy-luan.md) ↔ `run.py`: suy luận theo cả bình luận, luật mốc `rule-v1.1`, ghi `aspect_mentions` · [dac-ta-spam.md](4-mo-hinh/dac-ta-spam.md) ↔ `spam/`: so luật gắn cờ spam với mô hình ML (Công việc 11). Báo cáo mô hình cũ của Công việc 8, 9 đã gỡ khỏi `main` 26/11 (còn ở nhánh `xhquan/cong-viec-8`, `kien/cong-viec-9`) |
| `5-phan-tich/` | 5. Aggregates, trả lời Q1–Q5 | `src/analysis/` | [huong-dan.md](5-phan-tich/huong-dan.md) (Công việc 12). Đặc tả câu hỏi nằm ở `0-chung/muc-tieu.md` |
| `6-luu-tru/` | 6. Cơ sở dữ liệu MongoDB | `src/storage/` | [dac-ta.md](6-luu-tru/dac-ta.md) · [huong-dan.md](6-luu-tru/huong-dan.md) (Công việc 3; nạp DB bằng `load_db.py`) |
| `7-hien-thi/` | 7. API và dashboard 4 tab | `src/serving/` | [huong-dan.md](7-hien-thi/huong-dan.md): chạy API, dashboard, mỗi tab đọc gì · [bao-cao.md](7-hien-thi/bao-cao.md) (Công việc 13), hình ở `hinh-dashboard/` |

Contract dữ liệu (JSON Schema) nằm ở `contracts/`, cấu hình ở `config/`, không nằm trong `docs/`.

Ở gốc repo ngoài `README.md` còn [AGENTS.md](../AGENTS.md): luật bắt buộc cho trợ lý AI (và người) khi làm trong repo. `CLAUDE.md` chỉ trỏ sang nó để Claude Code tự nạp.

## 2. Quy tắc đặt tên

**Tài liệu** (`docs/`): tiếng Việt không dấu, chữ thường, nối bằng gạch ngang.

| Loại | Tên file | Nội dung |
|---|---|---|
| Đặc tả | `dac-ta.md` | Luật của cả tầng: đầu vào, đầu ra, phiên bản, quyết định đang chờ. Là nguồn chân lý: sửa đặc tả là phải sửa code, và ngược lại |
| Đặc tả một bước | `dac-ta-<bước>.md` | Khi tầng có nhiều bước, mỗi bước một file, ứng với một file code |
| Hướng dẫn | `huong-dan.md`, `huong-dan-<việc>.md` | Cách chạy, cách sửa, lỗi hay gặp. Không chép luật từ đặc tả |
| Báo cáo | `bao-cao.md`, `bao-cao-<việc>.md` | Đã làm gì, có những gì, số liệu, điều rút ra |
| Hình | `hinh-<việc>/` | Hình của báo cáo, cạnh file báo cáo |

Mọi file `.md` mở đầu bằng `# Tiêu đề` rồi dòng `> Mục đích: …; cập nhật lần cuối: YYYY-MM-DD.`

**Code:** tiếng Anh, chữ thường, nối bằng gạch dưới, đặt theo việc file làm (`clean.py`, `clauses.py`, không đặt theo số công việc như `task9`).

| Thứ | Ở đâu | Tên |
|---|---|---|
| Code một tầng | `src/<tầng>/` | `ingest`, `processing`, `labeling`, `models`, `analysis`, `storage`, `serving` (tầng 1–7) |
| Lệnh chạy | trong thư mục tầng | `run.py`, hoặc tên theo việc (`train.py`) |
| Tài nguyên code đọc | `src/<tầng>/resources/` | vd `abbreviations.tsv` |
| Test | `tests/` | `test_<tầng>.py`, `test_<tầng>_<module>.py` |
| Notebook | `notebooks/` | `<tầng>[_<bước>]_<việc>.ipynb`, vd `1_raw_audit.ipynb`, `2_2_normalize.ipynb`; mỗi bước một notebook. Hàm dùng chung ở `notebooks/helpers.py` |
| Dữ liệu, đầu ra | `data/` (không vào git) | `data/processed/comments.jsonl` |
| Model đã huấn luyện | `artifacts/` (file model không vào git) | |

Thư mục code **không** để README dài: cách chạy viết ở `docs/<tầng>/huong-dan.md`, mục đích từng file viết ở docstring đầu file.

## 3. Thêm tài liệu mới

1. Chọn tầng, đặt file vào `docs/<tầng>/` theo bảng mục 2.
2. Thêm một dòng vào bảng mục 1 của file này.
3. Code mới thì thêm vào [bản đồ code](0-chung/ban-do-code.md).
4. Tiến độ chỉ ghi ở [kế hoạch](0-chung/ke-hoach.md) mục 4, không thêm bảng trạng thái ở chỗ khác.

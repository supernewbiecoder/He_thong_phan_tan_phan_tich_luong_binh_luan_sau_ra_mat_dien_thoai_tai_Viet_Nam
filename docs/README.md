# Mục lục tài liệu

> Mục đích: Danh sách mọi tài liệu của dự án, xếp theo tầng xử lý, kèm quy tắc đặt tên và chỗ để tài liệu mới; cập nhật lần cuối: 2026-11-20.

**Cách đọc:** người mới đọc mục 1 (chung) rồi tới tầng mình phụ trách. Cần biết dự án đang tới đâu, ai làm gì thì đọc [kế hoạch](0-chung/ke-hoach.md).

## 1. Tài liệu theo tầng

Mỗi tầng xử lý có một thư mục, đánh số đúng thứ tự dữ liệu đi qua, và ứng với một thư mục code.

| Thư mục | Tầng | Code | Tài liệu |
|---|---|---|---|
| `0-chung/` | Dùng chung mọi tầng | | [ke-hoach.md](0-chung/ke-hoach.md): tình hình, việc tiếp theo, quyết định đang chờ, tiến độ và yêu cầu 15 công việc · [muc-tieu.md](0-chung/muc-tieu.md): đề tài, câu hỏi Q1–Q6, quy ước thống kê · [thiet-ke-du-lieu.md](0-chung/thiet-ke-du-lieu.md): các bảng, trường, mã khía cạnh · [luong-xu-ly.md](0-chung/luong-xu-ly.md): các bước xử lý, streaming tùy chọn · [kien-truc.mmd](0-chung/kien-truc.mmd) / [.svg](0-chung/kien-truc.svg): sơ đồ · [cai-dat.md](0-chung/cai-dat.md): dựng môi trường · [ban-do-code.md](0-chung/ban-do-code.md): file code nào để làm gì · [huong-dan-su-co-streaming.md](0-chung/huong-dan-su-co-streaming.md) |
| `1-thu-thap/` | 1. Thu thập bình luận YouTube | `src/ingest/` | [dac-ta.md](1-thu-thap/dac-ta.md) · [huong-dan.md](1-thu-thap/huong-dan.md): chạy crawler · [huong-dan-crawl-2-may.md](1-thu-thap/huong-dan-crawl-2-may.md) |
| `2-tien-xu-ly/` | 2. Làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ | `src/processing/` | [dac-ta.md](2-tien-xu-ly/dac-ta.md): tổng quan tầng · [dac-ta-lam-sach.md](2-tien-xu-ly/dac-ta-lam-sach.md) ↔ `clean.py` · [dac-ta-chuan-hoa.md](2-tien-xu-ly/dac-ta-chuan-hoa.md) ↔ `normalize.py` · [dac-ta-tach-menh-de.md](2-tien-xu-ly/dac-ta-tach-menh-de.md) ↔ `clauses.py` · [dac-ta-gan-co.md](2-tien-xu-ly/dac-ta-gan-co.md) ↔ `flags.py` · [huong-dan.md](2-tien-xu-ly/huong-dan.md): notebook kiểm tra dữ liệu và lệnh chạy · [bao-cao.md](2-tien-xu-ly/bao-cao.md) |
| `3-gan-nhan/` | 3. Gán nhãn (người và LLM) | (chưa có; dự kiến `src/labeling/`) | [dac-ta.md](3-gan-nhan/dac-ta.md): hai mẫu (A: chất lượng dữ liệu, B: tập test), phiếu, gán đôi, đồng thuận, phân xử, ước lượng · [huong-dan-gan-nhan-binh-luan.md](3-gan-nhan/huong-dan-gan-nhan-binh-luan.md): guideline v1 theo cả bình luận (nháp) · [huong-dan-gan-nhan.md](3-gan-nhan/huong-dan-gan-nhan.md): guideline v0.3 theo mệnh đề, giữ nguyên vì báo cáo Công việc 9 ghi SHA |
| `4-mo-hinh/` | 4. Suy luận, mô hình khía cạnh, cảm xúc | `src/models/` | [dac-ta.md](4-mo-hinh/dac-ta.md): dữ liệu huấn luyện, chia tập, đánh giá · [dac-ta-suy-luan.md](4-mo-hinh/dac-ta-suy-luan.md) ↔ `run.py`: suy luận theo cả bình luận, luật mốc, ghi `aspect_mentions` · [huong-dan-cam-xuc.md](4-mo-hinh/huong-dan-cam-xuc.md): gán nhãn LLM và huấn luyện cảm xúc · [bao-cao-cam-xuc.md](4-mo-hinh/bao-cao-cam-xuc.md) (Công việc 9) · [bao-cao-khia-canh.md](4-mo-hinh/bao-cao-khia-canh.md) (Công việc 8) |
| `5-phan-tich/` | 5. Aggregates, trả lời Q1–Q5 | `src/analysis/` | [huong-dan.md](5-phan-tich/huong-dan.md) (Công việc 12). Đặc tả câu hỏi nằm ở `0-chung/muc-tieu.md` |
| `6-luu-tru/` | 6. Cơ sở dữ liệu MongoDB | `src/storage/` | [dac-ta.md](6-luu-tru/dac-ta.md) · [huong-dan.md](6-luu-tru/huong-dan.md) (Công việc 3) |

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
| Code một tầng | `src/<tầng>/` | `ingest`, `processing`, `models`, `analysis`, `storage` |
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

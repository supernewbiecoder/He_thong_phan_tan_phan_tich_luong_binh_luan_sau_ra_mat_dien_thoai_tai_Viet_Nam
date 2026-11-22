# Mục lục tài liệu nhánh `kham-pha-nhan`

> Mục đích: Danh sách tài liệu của nhánh khám phá nhãn, xếp theo tầng, kèm quy tắc đặt tên; cập nhật lần cuối: 2026-11-22.

**Đọc trước:** [kế hoạch nhánh](0-chung/ke-hoach.md): vì sao có nhánh, nhánh có gì, các bước B1–B8 và lý do.

## 1. Tài liệu

| Thư mục | Tầng | Tài liệu |
|---|---|---|
| `0-chung/` | Dùng chung | [ke-hoach.md](0-chung/ke-hoach.md): tình hình, lộ trình B1–B8, việc sau nhánh, quyết định đang chờ |
| `1-thu-thap/` | 1. Dữ liệu v4 và kiểm tra cấu trúc (B1) | [dac-ta.md](1-thu-thap/dac-ta.md): dữ liệu v4 là gì, các trường, phiên bản, điều phải nhớ · [huong-dan-kiem-tra-du-lieu.md](1-thu-thap/huong-dan-kiem-tra-du-lieu.md): chạy notebook `1_raw_audit` · [bao-cao-kiem-tra-du-lieu.md](1-thu-thap/bao-cao-kiem-tra-du-lieu.md): số Level 0 đã chạy, các mục chờ chạy |
| `3-gan-nhan/` | 3. Khám phá nhãn nội dung (B2–B7) | [dac-ta-kham-pha-nhan.md](3-gan-nhan/dac-ta-kham-pha-nhan.md): lấy mẫu, mã hóa mở, bão hòa, đồng thuận, phân bố, luật chốt bộ nhãn · [huong-dan-kham-pha-nhan.md](3-gan-nhan/huong-dan-kham-pha-nhan.md): cách mã hóa, gom bộ nhãn |

Số tầng giữ như nhánh `main` (1 thu thập, 2 tiền xử lý, 3 gán nhãn…) để chép kết quả về `main` không phải đổi chỗ. Nhánh này chưa có tầng 2, 4, 5, 6.

## 2. Quy tắc đặt tên

- Tài liệu nằm trong `docs/<n-tầng>/`, tên tiếng Việt không dấu, chữ thường, nối bằng gạch ngang.
- Chỉ có ba loại file:
  - `dac-ta[-<bước>].md`: luật, là nguồn chân lý; sửa đặc tả thì phải sửa code theo;
  - `huong-dan[-<việc>].md`: cách làm, không chép luật;
  - `bao-cao[-<việc>].md`: đã làm gì, số liệu, điều rút ra.
- Mọi file `.md` mở đầu bằng `# Tiêu đề`, rồi dòng `> Mục đích: …; cập nhật lần cuối: YYYY-MM-DD.`
- Notebook đặt ở `notebooks/<tầng>[_<bước>]_<việc>.ipynb` (vd `1_raw_audit.ipynb`, `3_label_discovery.ipynb`). Hàm dùng chung ở `notebooks/helpers.py`.
- Thêm tài liệu mới thì thêm một dòng vào bảng mục 1.

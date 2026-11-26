# Mục lục tài liệu nhánh `kham-pha-nhan`

> Mục đích: Danh sách tài liệu của nhánh khám phá nhãn, xếp theo tầng, kèm quy tắc đặt tên; cập nhật lần cuối: 2026-11-26.

**Đọc trước:** [kế hoạch nhánh](0-chung/ke-hoach.md): vì sao có nhánh, nhánh có gì, các bước B1–B8 và lý do.

## 1. Tài liệu

| Thư mục | Tầng | Tài liệu |
|---|---|---|
| `0-chung/` | Dùng chung | [huong-dan-tom-tat.md](0-chung/huong-dan-tom-tat.md): giải thích dễ hiểu nhánh đã làm gì, đang ở đâu (đọc trước) · [ke-hoach.md](0-chung/ke-hoach.md): tình hình, lộ trình B1–B8, việc sau nhánh, các quyết định · [ke-hoach-tong-the.md](0-chung/ke-hoach-tong-the.md): kế hoạch đề xuất cho cả dự án sau nhánh này, 7 giai đoạn từ bàn giao bộ nhãn tới báo cáo · [bao-cao-qua-trinh.md](0-chung/bao-cao-qua-trinh.md): sổ ghi chép từng đợt 22–26/11: làm gì, số liệu, suy ra, chỗ sai, kết quả cuối |
| `1-thu-thap/` | 1. Dữ liệu v4 và kiểm tra cấu trúc (B1) | [dac-ta.md](1-thu-thap/dac-ta.md): dữ liệu v4 là gì, các trường, phiên bản, điều phải nhớ · [huong-dan-kiem-tra-du-lieu.md](1-thu-thap/huong-dan-kiem-tra-du-lieu.md): chạy notebook `1_raw_audit` · [bao-cao-kiem-tra-du-lieu.md](1-thu-thap/bao-cao-kiem-tra-du-lieu.md): số Level 0 đã chạy, các mục chờ chạy |
| `3-gan-nhan/` | 3. Gán nhãn: **bàn giao, dùng tiếp** | [dac-ta-bo-nhan.md](3-gan-nhan/dac-ta-bo-nhan.md) ↔ `src/labeling/label_set.py`: bộ nhãn 6 chiều, định nghĩa, ví dụ; bộ nhãn chốt ở mục 8 · [huong-dan-gan-nhan-chinh-thuc.md](3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md): cách gán nhãn chính thức theo bộ nhãn chốt (trưởng nhóm duyệt 26/11) |
| `3-gan-nhan/` | 3. Khám phá nhãn B2–B8: **hồ sơ quá trình** | [dac-ta-kham-pha-nhan.md](3-gan-nhan/dac-ta-kham-pha-nhan.md) ↔ `src/labeling/`: thuật ngữ (mã, nhãn, khía cạnh), ba nguồn, vai trò, lấy mẫu và vì sao 500, HAC, mã hóa mở, bão hòa, đồng thuận, công thức phân bố, luật chốt bộ nhãn · [huong-dan-kham-pha-nhan.md](3-gan-nhan/huong-dan-kham-pha-nhan.md): guideline mã hóa, gán mù lô K, kiểm nhãn · [huong-dan-gan-lo-k.md](3-gan-nhan/huong-dan-gan-lo-k.md): gán mù lô K từng bước (B6) · [bao-cao-ma-hoa-mo.md](3-gan-nhan/bao-cao-ma-hoa-mo.md): thống kê mã hóa mở (do `code_stats` sinh) · [bao-cao-bo-nhan.md](3-gan-nhan/bao-cao-bo-nhan.md): số bình luận mỗi nhãn, bão hòa (do `label_set` sinh) · [bao-cao-lo-k.md](3-gan-nhan/bao-cao-lo-k.md): so lô K hai bên gán mù, kappa (do `lot_k` sinh) · [bao-cao-phan-bo-nhan.md](3-gan-nhan/bao-cao-phan-bo-nhan.md): phân bố nhãn B7 (do `distribution` sinh; biểu đồ ở `notebooks/3_label_distribution.ipynb`) · [bao-cao-kham-pha-nhan.md](3-gan-nhan/bao-cao-kham-pha-nhan.md): B8, so ba nguồn, đề xuất chốt bộ nhãn (do `b8` sinh) · [bao-cao-lo-d2.md](3-gan-nhan/bao-cao-lo-d2.md): kiểm lại trên 50 bình luận lô D2 sau khi sửa định nghĩa (do `lot_k --lo D2` sinh) |

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

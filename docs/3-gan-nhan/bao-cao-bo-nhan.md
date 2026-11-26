# Báo cáo bộ nhãn (B5)

> Mục đích: Số bình luận có mỗi nhãn của bộ nhãn nháp, theo mã tự do của A; lô gặp lần đầu; bão hòa; cập nhật lần cuối: 2026-11-25.

**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.label_set`. Nguồn: `data/kham-pha/phieu_ma_hoa_mo.csv` (SHA-256 `f4a7922a…d170`), dữ liệu v4. Định nghĩa nhãn: [đặc tả bộ nhãn](dac-ta-bo-nhan.md); ánh xạ mã → nhãn: `src/labeling/label_set.py`.

**Cách đọc:** mỗi số là **số bình luận** có ít nhất một mã rơi vào nhãn, đếm bằng luật từ khóa trên mã tự do của A (do AI mã, chưa có người kiểm từng mã). Đây là bằng chứng nhãn có trong dữ liệu, **không phải phân bố**: không ghi phần trăm. Phân bố tính ở B7, sau khi gán lại theo bộ nhãn và có người kiểm. Chiều 5 và 6 đếm gần đúng từ mã (mã tự do không ghi đủ hai điều này).

## 1. Liên quan tới gì (một nhãn)

| Nhãn | Lô 1–5 (n = 500) | CD (n = 100) | Lô gặp lần đầu |
|---|---|---|---|
| `dien_thoai` | 369 | 92 | 1 |
| `ngu_canh` | 65 | 5 | 1 |
| `nguoi_binh_luan` | 32 | 2 | 1 |
| `khong_xac_dinh` | 24 | 0 | 1 |
| `khong_lien_quan` | 5 | 1 | 1 |
| `khong_noi_dung` | 5 | 0 | 3 |

## 2. Nói về phần nào của điện thoại (nhiều nhãn)

| Nhãn | Loại | Lô 1–5 (n = 500) | CD (n = 100) | Lô gặp lần đầu |
|---|---|---|---|---|
| `may_chung` | ngoài khía cạnh | 100 | 36 | 1 |
| `hang_nguoi_dung` | ngoài khía cạnh | 45 | 6 | 1 |
| `hieu_nang` | khía cạnh | 42 | 9 | 1 |
| `camera` | khía cạnh | 39 | 5 | 1 |
| `thiet_ke` | khía cạnh | 36 | 5 | 1 |
| `gia` | khía cạnh | 33 | 6 | 1 |
| `phan_mem` | khía cạnh | 29 | 10 | 1 |
| `man_hinh` | khía cạnh | 27 | 5 | 1 |
| `mua_ban` | khía cạnh | 25 | 16 | 1 |
| `phan_cung_khac` | khía cạnh | 24 | 1 | 1 |
| `pin_sac` | khía cạnh | 19 | 9 | 1 |
| `do_ben` | khía cạnh | 9 | 3 | 1 |
| `am_thanh` | khía cạnh | 9 | 1 | 1 |
| `nhiet_do` | khía cạnh | 4 | 2 | 1 |
| `bao_hanh_sua_chua` | khía cạnh | 3 | 9 | 1 |

Trong các bình luận có nhãn `dien_thoai` ở chiều 1:

- Lô 1–5: 369 bình luận; 260 có ít nhất một khía cạnh, 109 chỉ có nhãn ngoài khía cạnh.
- CD: 92 bình luận; 71 có ít nhất một khía cạnh, 21 chỉ có nhãn ngoài khía cạnh.

## 3. Mục đích (nhiều nhãn)

| Nhãn | Lô 1–5 (n = 500) | CD (n = 100) | Lô gặp lần đầu |
|---|---|---|---|
| `danh_gia` | 207 | 43 | 1 |
| `thong_tin` | 76 | 18 | 1 |
| `hoi` | 55 | 14 | 1 |
| `de_nghi` | 48 | 7 | 1 |
| `ban_than` | 47 | 25 | 1 |
| `tranh_luan` | 47 | 12 | 1 |
| `cong_kich` | 47 | 7 | 1 |
| `dua` | 27 | 5 | 1 |
| `khong_xac_dinh` | 15 | 0 | 1 |
| `xa_giao` | 13 | 2 | 1 |
| `minigame` | 10 | 0 | 3 |
| `bao_loi` | 2 | 10 | 1 |
| `quang_cao` | 1 | 2 | 1 |

## 4. Thái độ (nhiều nhãn, theo từng nhãn chiều 2)

Lô 1–5 (n = 500). Một bình luận có thể vừa khen vừa chê cùng một nhãn chiều 2.

| Nhãn chiều 2 | `tich_cuc` | `tieu_cuc` | `so_sanh` | `khong_danh_gia` |
|---|---|---|---|---|
| `may_chung` | 18 | 12 | 7 | 69 |
| `hang_nguoi_dung` | 5 | 8 | 3 | 30 |
| `hieu_nang` | 6 | 8 | 7 | 24 |
| `camera` | 8 | 9 | 9 | 19 |
| `thiet_ke` | 7 | 9 | 2 | 20 |
| `gia` | 0 | 4 | 1 | 28 |
| `phan_mem` | 4 | 7 | 2 | 16 |
| `man_hinh` | 4 | 5 | 1 | 17 |
| `mua_ban` | 0 | 2 | 0 | 23 |
| `phan_cung_khac` | 1 | 4 | 1 | 18 |
| `pin_sac` | 6 | 3 | 3 | 8 |
| `do_ben` | 3 | 1 | 1 | 4 |
| `am_thanh` | 2 | 1 | 3 | 3 |
| `nhiet_do` | 2 | 1 | 0 | 1 |
| `bao_hanh_sua_chua` | 0 | 0 | 0 | 3 |

## 5. Đã dùng máy (một nhãn)

| Nhãn | Lô 1–5 (n = 500) | CD (n = 100) | Lô gặp lần đầu |
|---|---|---|---|
| `khong_ro` | 467 | 67 | 1 |
| `co` | 33 | 33 | 1 |

## 6. Máy được nhắc (một nhãn)

| Nhãn | Lô 1–5 (n = 500) | CD (n = 100) | Lô gặp lần đầu |
|---|---|---|---|
| `khong_nhac` | 306 | 52 | 1 |
| `goi_ten_may` | 112 | 32 | 1 |
| `chi_hang` | 82 | 16 | 1 |

## 7. Bão hòa

Số nhãn mới ở từng lô, theo thứ tự lô 1→5, của chiều 1, 2, 3, 5, 6 (chiều 4 là cặp nhãn chiều 2 × thái độ, không tính). Luật dừng: lô 5 không có nhãn mới ([đặc tả mục 6](dac-ta-kham-pha-nhan.md#6-gom-mã-thành-bộ-nhãn-và-bão-hòa-b5)).

| Lô | Số nhãn mới | Nhãn mới |
|---|---|---|
| 1 | 37 | `da_dung/co`, `da_dung/khong_ro`, `lien_quan/dien_thoai`, `lien_quan/khong_lien_quan`, `lien_quan/khong_xac_dinh`, `lien_quan/ngu_canh`, `lien_quan/nguoi_binh_luan`, `may_nhac/chi_hang`, `may_nhac/goi_ten_may`, `may_nhac/khong_nhac`, `muc_dich/ban_than`, `muc_dich/bao_loi`, `muc_dich/cong_kich`, `muc_dich/danh_gia`, `muc_dich/de_nghi`, `muc_dich/dua`, `muc_dich/hoi`, `muc_dich/khong_xac_dinh`, `muc_dich/quang_cao`, `muc_dich/thong_tin`, `muc_dich/tranh_luan`, `muc_dich/xa_giao`, `noi_ve/am_thanh`, `noi_ve/bao_hanh_sua_chua`, `noi_ve/camera`, `noi_ve/do_ben`, `noi_ve/gia`, `noi_ve/hang_nguoi_dung`, `noi_ve/hieu_nang`, `noi_ve/man_hinh`, `noi_ve/may_chung`, `noi_ve/mua_ban`, `noi_ve/nhiet_do`, `noi_ve/phan_cung_khac`, `noi_ve/phan_mem`, `noi_ve/pin_sac`, `noi_ve/thiet_ke` |
| 2 | 0 |  |
| 3 | 2 | `lien_quan/khong_noi_dung`, `muc_dich/minigame` |
| 4 | 0 |  |
| 5 | 0 |  |

## 8. Đối tượng chưa xếp vào nhãn nào

Phiếu A (cả lô 1–5 và CD): 1 mã: `vọc vạch`.

**Độ phủ trên phiếu B** (trưởng nhóm mã độc lập; `phieu_ma_hoa_mo_B.csv`, SHA-256 `d0200472…2276`): 35/797 mã có đối tượng chưa xếp được: `đời sống`, `nhu cầu sử dụng`, `tản nhiệt`, `cảm xúc`, `trang phục reviewer`, `thời điểm bán`, `vật liệu`, `quảng cáo`, `tủ lạnh`, `lọc ồn`, `địa điểm`, `nghề review`, `chất lượng`, `review sản phẩm khác`, `sản phẩm khác`, `lỗi quảng cáo`, `thói quen dùng`, `thời gian có hàng`, `chất lượng hoàn thiện`, `tần số quét`, `thuật ngữ`, `bản quyền`, `phần cứng`, `chính trị`, `thị trường`, `thu cũ đổi mới`, `đơn hàng`, `lỗi vặt`, `lỗi phần cứng`.


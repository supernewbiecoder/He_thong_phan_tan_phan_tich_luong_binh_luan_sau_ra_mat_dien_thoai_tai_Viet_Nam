# Báo cáo phân bố nhãn (B7)

> Mục đích: EDA nhãn 6 chiều của mẫu khám phá nhãn, do A (AI) gán lại từ chữ bình luận: số đếm (tỷ lệ khi đã kiểm), thái độ, nhóm, mức chắc chắn, đối chiếu; cập nhật lần cuối: 2026-11-26.

**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.distribution`. Nguồn: `data/kham-pha/phieu_b7.csv` (SHA-256 `06d81717…b40c`), dữ liệu v4. Luật: [đặc tả khám phá nhãn](dac-ta-kham-pha-nhan.md) mục 7c, 8. Định nghĩa nhãn: [đặc tả bộ nhãn](dac-ta-bo-nhan.md).

**Trạng thái: trưởng nhóm đã kiểm 500/500 bình luận phải xem.** Nhãn do AI gán.

- **Mẫu:** 600 bình luận ngẫu nhiên (500 lô 1–5, 100 lô K), thuộc 507 video (nhiều nhất 5 bình luận một video).
- **Lô K:** hai bên gán mù, B phân xử ca lệch ([báo cáo lô K](bao-cao-lo-k.md)); nhãn lô K không cần kiểm thêm.
- **Bộ nhãn:** trưởng nhóm duyệt 25/11 (đặc tả bộ nhãn mục 7), thêm luật 8, 9 ngày 26/11 sau khi so lô K, chốt sau B8 (mục 8; bảng này dùng nhãn khám phá, chưa gộp); mọi chiều đạt κ ≥ 0,6 ở lô K.
- Mẫu lấy trên cả v4, **không** suy cho bộ 4 máy.

## 1. Liên quan tới gì (một nhãn)

| Nhãn | Số bình luận | % | KTC 95% (bootstrap video) | KTC 95% (Wilson) | deff |
|---|---|---|---|---|---|
| `dien_thoai` | 395 | 65,8 | [61,5; 69,9] | [61,9; 69,5] | 1,25 |
| `ngu_canh` | 111 | 18,5 | [14,9; 22,4] | [15,6; 21,8] | 1,45 |
| `nguoi_binh_luan` | 48 | 8,0 | [5,9; 10,3] | [6,1; 10,4] | 1,04 |
| `khong_xac_dinh` | 26 | 4,3 | [2,8; 6,1] | [3,0; 6,3] | 0,97 |
| `khong_lien_quan` | 15 | 2,5 | [1,3; 3,7] | [1,5; 4,1] | 0,87 |
| `khong_noi_dung` | 5 | 0,8 | [0,2; 1,5] | [0,4; 1,9] | 0,74 |

## 2. Nói về phần nào của điện thoại (nhiều nhãn)

Phần áp dụng: **395 bình luận `dien_thoai`**. 311 bình luận có ít nhất một khía cạnh, 84 chỉ có nhãn ngoài khía cạnh. Số nhãn chiều 2 mỗi bình luận: 1 nhãn ở 292 bình luận, 2 nhãn ở 85 bình luận, 3 nhãn ở 13 bình luận, 4 nhãn ở 2 bình luận, 5 nhãn ở 2 bình luận, 8 nhãn ở 1 bình luận.

| Nhãn | Loại | Số bình luận | % | KTC 95% (bootstrap video) | KTC 95% (Wilson) | deff |
|---|---|---|---|---|---|---|
| `may_chung` | ngoài khía cạnh | 82 | 20,8 | [16,9; 24,6] | [17,1; 25,0] | 0,94 |
| `gia` | khía cạnh | 57 | 14,4 | [10,8; 18,2] | [11,3; 18,2] | 1,13 |
| `thiet_ke` | khía cạnh | 54 | 13,7 | [10,4; 17,2] | [10,6; 17,4] | 1,01 |
| `hieu_nang` | khía cạnh | 53 | 13,4 | [10,0; 17,0] | [10,4; 17,1] | 1,10 |
| `hang_nguoi_dung` | ngoài khía cạnh | 47 | 11,9 | [8,8; 15,0] | [9,1; 15,5] | 0,95 |
| `mua_ban` | khía cạnh | 43 | 10,9 | [8,1; 14,1] | [8,2; 14,3] | 0,95 |
| `camera` | khía cạnh | 39 | 9,9 | [7,1; 13,2] | [7,3; 13,2] | 1,08 |
| `man_hinh` | khía cạnh | 32 | 8,1 | [5,6; 10,9] | [5,8; 11,2] | 0,98 |
| `phan_mem` | khía cạnh | 27 | 6,8 | [4,4; 9,5] | [4,7; 9,8] | 1,02 |
| `phan_cung_khac` | khía cạnh | 26 | 6,6 | [4,2; 9,2] | [4,5; 9,5] | 0,99 |
| `pin_sac` | khía cạnh | 23 | 5,8 | [3,6; 8,2] | [3,9; 8,6] | 0,99 |
| `do_ben` | khía cạnh | 21 | 5,3 | [3,3; 7,6] | [3,5; 8,0] | 0,92 |
| `am_thanh` | khía cạnh | 11 | 2,8 | [1,3; 4,5] | [1,6; 4,9] | 0,93 |
| `nhiet_do` | khía cạnh | 7 | 1,8 | [0,5; 3,2] | [0,9; 3,6] | 0,98 |
| `bao_hanh_sua_chua` | khía cạnh | 5 | 1,3 | [0,3; 2,5] | [0,5; 2,9] | 0,91 |
| `khac` | khía cạnh | 0 | 0,0 | ≤ 0,8 (quy tắc ba) | [0,0; 1,0] |  |

## 3. Mục đích (nhiều nhãn)

| Nhãn | Số bình luận | % | KTC 95% (bootstrap video) | KTC 95% (Wilson) | deff |
|---|---|---|---|---|---|
| `danh_gia` | 240 | 40,0 | [35,9; 44,2] | [36,2; 44,0] | 1,13 |
| `thong_tin` | 85 | 14,2 | [11,4; 16,8] | [11,6; 17,2] | 0,94 |
| `hoi` | 73 | 12,2 | [9,7; 14,8] | [9,8; 15,0] | 0,94 |
| `de_nghi` | 62 | 10,3 | [8,0; 12,9] | [8,1; 13,0] | 1,02 |
| `tranh_luan` | 59 | 9,8 | [7,4; 12,4] | [7,7; 12,5] | 1,08 |
| `cong_kich` | 57 | 9,5 | [7,2; 11,9] | [7,4; 12,1] | 0,97 |
| `dua` | 43 | 7,2 | [5,0; 9,3] | [5,4; 9,5] | 1,06 |
| `ban_than` | 41 | 6,8 | [4,9; 8,9] | [5,1; 9,1] | 0,99 |
| `xa_giao` | 19 | 3,2 | [1,8; 4,7] | [2,0; 4,9] | 1,03 |
| `minigame` | 18 | 3,0 | [0,7; 6,0] | [1,9; 4,7] | 3,67 |
| `khong_xac_dinh` | 11 | 1,8 | [0,8; 3,0] | [1,0; 3,3] | 0,92 |
| `bao_loi` | 8 | 1,3 | [0,5; 2,3] | [0,7; 2,6] | 0,88 |
| `quang_cao` | 2 | 0,3 | [0,0; 0,8] | [0,1; 1,2] | 0,58 |

Mục đích theo nhãn chiều 1 (số bình luận):

| Mục đích | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `khong_lien_quan` | `khong_noi_dung` | `khong_xac_dinh` |
|---|---|---|---|---|---|---|
| `danh_gia` | 212 | 9 | 4 | 2 | 0 | 13 |
| `thong_tin` | 63 | 13 | 2 | 5 | 0 | 2 |
| `hoi` | 56 | 9 | 4 | 4 | 0 | 0 |
| `de_nghi` | 35 | 26 | 1 | 0 | 0 | 0 |
| `tranh_luan` | 39 | 4 | 15 | 1 | 0 | 0 |
| `cong_kich` | 21 | 9 | 25 | 2 | 0 | 0 |
| `dua` | 23 | 16 | 0 | 2 | 0 | 2 |
| `ban_than` | 35 | 4 | 1 | 0 | 0 | 1 |
| `xa_giao` | 4 | 10 | 1 | 1 | 2 | 1 |
| `minigame` | 0 | 18 | 0 | 0 | 0 | 0 |
| `khong_xac_dinh` | 0 | 1 | 0 | 0 | 3 | 7 |
| `bao_loi` | 8 | 0 | 0 | 0 | 0 | 0 |
| `quang_cao` | 2 | 0 | 0 | 0 | 0 | 0 |

## 4. Thái độ (theo cặp bình luận và nhãn chiều 2)

527 cặp. Một cặp có thể có nhiều thái độ, nên tổng hàng có thể vượt số cặp.

| Nhãn chiều 2 | Số cặp | `tich_cuc` | `tieu_cuc` | `so_sanh` | `khong_danh_gia` |
|---|---|---|---|---|---|
| `may_chung` | 82 | 15 | 13 | 9 | 45 |
| `gia` | 57 | 5 | 14 | 2 | 36 |
| `thiet_ke` | 54 | 12 | 17 | 11 | 15 |
| `hieu_nang` | 53 | 14 | 11 | 10 | 18 |
| `hang_nguoi_dung` | 47 | 11 | 9 | 3 | 24 |
| `mua_ban` | 43 | 1 | 4 | 0 | 38 |
| `camera` | 39 | 7 | 11 | 11 | 11 |
| `man_hinh` | 32 | 9 | 9 | 2 | 12 |
| `phan_mem` | 27 | 4 | 8 | 3 | 13 |
| `phan_cung_khac` | 26 | 0 | 7 | 3 | 16 |
| `pin_sac` | 23 | 6 | 7 | 7 | 6 |
| `do_ben` | 21 | 4 | 6 | 2 | 9 |
| `am_thanh` | 11 | 1 | 3 | 3 | 4 |
| `nhiet_do` | 7 | 3 | 3 | 0 | 1 |
| `bao_hanh_sua_chua` | 5 | 0 | 1 | 0 | 4 |
| **Tổng** | 527 | 92 | 123 | 66 | 252 |

- Bình luận `dien_thoai` có ít nhất một lời khen: 77 (19,5%); có ít nhất một lời chê: 100 (25,3%); chỉ có `khong_danh_gia`: 185 (46,8%).
- Nhãn chiều 2 có khen + chê từ 30 trở lên: không có. Nhãn dưới ngưỡng này ít dữ liệu, chưa kết luận được khen hay chê nhiều hơn.

## 5. Đã dùng máy (một nhãn)

| Nhãn | Số bình luận | % | KTC 95% (bootstrap video) | KTC 95% (Wilson) | deff |
|---|---|---|---|---|---|
| `khong_ro` | 562 | 93,7 | [91,6; 95,7] | [91,4; 95,4] | 1,13 |
| `co` | 38 | 6,3 | [4,3; 8,5] | [4,6; 8,6] | 1,13 |

`bao_loi`: 8 bình luận, trong đó 8 có nhãn `co`. Q5 cần đúng loại này.

## 6. Máy được nhắc (một nhãn)

| Nhãn | Số bình luận | % | KTC 95% (bootstrap video) | KTC 95% (Wilson) | deff |
|---|---|---|---|---|---|
| `khong_nhac` | 342 | 57,0 | [52,7; 61,4] | [53,0; 60,9] | 1,24 |
| `goi_ten_may` | 157 | 26,2 | [22,5; 30,0] | [22,8; 29,8] | 1,14 |
| `chi_hang` | 101 | 16,8 | [13,9; 20,0] | [14,1; 20,0] | 1,05 |

Riêng 395 bình luận `dien_thoai`: `goi_ten_may` 144 (36,5%), `chi_hang` 96 (24,3%), `khong_nhac` 155 (39,2%).

## 7. Minigame

18 bình luận: 18 ở `ngu_canh`. Thái độ: không có.

## 8. Theo nhóm

Số bình luận của nhóm có nhãn đó. Nhóm dưới 30 bình luận chỉ ghi số đếm.

**Gốc hay reply**

| Nhóm | n | Video | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `danh_gia` | `hoi` | `tranh_luan` | `cong_kich` | `minigame` | có khen | có chê |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bình luận gốc | 351 | 310 | 220 (62,7%) | 89 (25,4%) | 7 (2,0%) | 151 (43,0%) | 53 (15,1%) | 8 (2,3%) | 21 (6,0%) | 18 (5,1%) | 48 (13,7%) | 58 (16,5%) |
| reply | 249 | 234 | 175 (70,3%) | 22 (8,8%) | 41 (16,5%) | 89 (35,7%) | 20 (8,0%) | 51 (20,5%) | 36 (14,5%) | 0 (0,0%) | 29 (11,6%) | 42 (16,9%) |

**Nhóm kênh**

| Nhóm | n | Video | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `danh_gia` | `hoi` | `tranh_luan` | `cong_kich` | `minigame` | có khen | có chê |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 kênh lớn | 360 | 301 | 239 (66,4%) | 61 (16,9%) | 31 (8,6%) | 155 (43,1%) | 41 (11,4%) | 38 (10,6%) | 33 (9,2%) | 15 (4,2%) | 46 (12,8%) | 71 (19,7%) |
| kênh khác | 237 | 204 | 153 (64,6%) | 50 (21,1%) | 17 (7,2%) | 83 (35,0%) | 32 (13,5%) | 21 (8,9%) | 24 (10,1%) | 3 (1,3%) | 30 (12,7%) | 28 (11,8%) |
| không rõ kênh | 3 | 2 | 3 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 1 |

**Tuần sau ra mắt**

| Nhóm | n | Video | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `danh_gia` | `hoi` | `tranh_luan` | `cong_kich` | `minigame` | có khen | có chê |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tuần 1–2 | 406 | 351 | 274 (67,5%) | 68 (16,7%) | 33 (8,1%) | 170 (41,9%) | 49 (12,1%) | 40 (9,9%) | 39 (9,6%) | 1 (0,2%) | 54 (13,3%) | 75 (18,5%) |
| tuần 3–4 | 194 | 164 | 121 (62,4%) | 43 (22,2%) | 15 (7,7%) | 70 (36,1%) | 24 (12,4%) | 19 (9,8%) | 18 (9,3%) | 17 (8,8%) | 23 (11,9%) | 25 (12,9%) |

**Loại video**

| Nhóm | n | Video | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `danh_gia` | `hoi` | `tranh_luan` | `cong_kich` | `minigame` | có khen | có chê |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| review | 339 | 285 | 209 (61,7%) | 71 (20,9%) | 27 (8,0%) | 119 (35,1%) | 40 (11,8%) | 34 (10,0%) | 35 (10,3%) | 15 (4,4%) | 45 (13,3%) | 48 (14,2%) |
| compare | 135 | 116 | 98 (72,6%) | 20 (14,8%) | 13 (9,6%) | 66 (48,9%) | 11 (8,1%) | 19 (14,1%) | 14 (10,4%) | 0 (0,0%) | 16 (11,9%) | 28 (20,7%) |
| unbox | 102 | 84 | 71 (69,6%) | 15 (14,7%) | 7 (6,9%) | 43 (42,2%) | 20 (19,6%) | 4 (3,9%) | 7 (6,9%) | 3 (2,9%) | 11 (10,8%) | 21 (20,6%) |
| long_term | 21 | 20 | 14 | 5 | 1 | 10 | 2 | 2 | 1 | 0 | 4 | 2 |
| không xác định | 3 | 2 | 3 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 1 |

**Của chủ kênh**

| Nhóm | n | Video | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `danh_gia` | `hoi` | `tranh_luan` | `cong_kich` | `minigame` | có khen | có chê |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| người xem | 582 | 494 | 387 (66,5%) | 105 (18,0%) | 45 (7,7%) | 237 (40,7%) | 73 (12,5%) | 55 (9,5%) | 57 (9,8%) | 18 (3,1%) | 75 (12,9%) | 100 (17,2%) |
| chủ kênh | 18 | 18 | 8 | 6 | 3 | 3 | 0 | 4 | 0 | 0 | 2 | 0 |

## 9. A chắc tới đâu

200/600 bình luận có ít nhất một chiều A đánh dấu `?`. Theo chiều: 1. Liên quan tới gì 81, 2. Nói về phần nào của điện thoại 45, 3. Mục đích 58, 4. Thái độ 51, 5. Đã dùng máy 6, 6. Máy được nhắc 7.

## 10. Kiểm của trưởng nhóm

- Phần ngẫu nhiên: 17/100 bình luận phải sửa, 17,0% [10,9; 25,5] (Wilson).
- Phần A đánh dấu `?`: 80/200 bình luận phải sửa.
- Số bình luận sửa, theo cột: `muc_dich` 43, `lien_quan` 41, `noi_ve_thai_do` 34, `may_nhac` 5, `da_dung` 2.

## 11. Đối chiếu với mã tự do

Nhãn bên kia suy từ mã tự do bằng luật từ khóa của `label_set.py`, nên lệch có thể do luật. Phiếu B mã **trước** khi sửa bảng hành vi. Đây là chỉ báo, không thay cho lô K mù. Cột B7 là nhãn của A trước khi B sửa.

**B7 so với mã tự do cũ của A** (n = 500). Chiều 1 như một câu 6 lựa chọn: đồng ý thô 88,6%, κ = 0,75.

| Chiều | Nhãn | B7 | Bên kia | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|---|
| lien_quan | `dien_thoai` | 356 | 369 | 342 | 0,79 | 0,94 |
| lien_quan | `ngu_canh` | 85 | 65 | 60 | 0,77 | 0,80 |
| lien_quan | `nguoi_binh_luan` | 16 | 32 | 14 | 0,56 | 0,58 |
| lien_quan | `khong_lien_quan` | 9 | 5 | 4 | 0,57 | 0,57 |
| lien_quan | `khong_noi_dung` | 5 | 5 | 5 | 1,00 | 1,00 |
| lien_quan | `khong_xac_dinh` | 29 | 24 | 18 | 0,66 | 0,68 |
| noi_ve | `pin_sac` | 17 | 19 | 15 | 0,83 | 0,83 |
| noi_ve | `man_hinh` | 25 | 27 | 22 | 0,84 | 0,85 |
| noi_ve | `hieu_nang` | 49 | 42 | 39 | 0,84 | 0,86 |
| noi_ve | `nhiet_do` | 6 | 4 | 4 | 0,80 | 0,80 |
| noi_ve | `camera` | 36 | 39 | 30 | 0,78 | 0,80 |
| noi_ve | `thiet_ke` | 42 | 36 | 32 | 0,81 | 0,82 |
| noi_ve | `do_ben` | 10 | 9 | 9 | 0,95 | 0,95 |
| noi_ve | `phan_mem` | 30 | 29 | 25 | 0,84 | 0,85 |
| noi_ve | `am_thanh` | 9 | 9 | 8 | 0,89 | 0,89 |
| noi_ve | `phan_cung_khac` | 21 | 24 | 14 | 0,60 | 0,62 |
| noi_ve | `gia` | 53 | 33 | 31 | 0,70 | 0,72 |
| noi_ve | `mua_ban` | 37 | 25 | 21 | 0,66 | 0,68 |
| noi_ve | `bao_hanh_sua_chua` | 5 | 3 | 3 | 0,75 | 0,75 |
| noi_ve | `may_chung` | 70 | 100 | 59 | 0,63 | 0,69 |
| noi_ve | `hang_nguoi_dung` | 45 | 45 | 31 | 0,66 | 0,69 |
| muc_dich | `danh_gia` | 200 | 207 | 174 | 0,76 | 0,86 |
| muc_dich | `hoi` | 63 | 55 | 53 | 0,88 | 0,90 |
| muc_dich | `thong_tin` | 73 | 76 | 53 | 0,66 | 0,71 |
| muc_dich | `de_nghi` | 43 | 48 | 37 | 0,79 | 0,81 |
| muc_dich | `ban_than` | 35 | 47 | 29 | 0,68 | 0,71 |
| muc_dich | `bao_loi` | 7 | 2 | 2 | 0,44 | 0,44 |
| muc_dich | `tranh_luan` | 45 | 47 | 32 | 0,66 | 0,70 |
| muc_dich | `dua` | 29 | 27 | 22 | 0,77 | 0,79 |
| muc_dich | `cong_kich` | 44 | 47 | 35 | 0,75 | 0,77 |
| muc_dich | `minigame` | 13 | 10 | 9 | 0,78 | 0,78 |
| muc_dich | `quang_cao` | 1 | 1 | 1 | 1,00 | 1,00 |
| muc_dich | `xa_giao` | 15 | 13 | 12 | 0,85 | 0,86 |
| muc_dich | `khong_xac_dinh` | 13 | 15 | 9 | 0,63 | 0,64 |

**B7 so với mã tự do của B (trưởng nhóm)** (n = 499). Chiều 1 như một câu 6 lựa chọn: đồng ý thô 83,6%, κ = 0,63.

| Chiều | Nhãn | B7 | Bên kia | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|---|
| lien_quan | `dien_thoai` | 355 | 377 | 339 | 0,72 | 0,93 |
| lien_quan | `ngu_canh` | 85 | 57 | 48 | 0,62 | 0,68 |
| lien_quan | `nguoi_binh_luan` | 16 | 23 | 13 | 0,65 | 0,67 |
| lien_quan | `khong_lien_quan` | 9 | 17 | 4 | 0,29 | 0,31 |
| lien_quan | `khong_noi_dung` | 5 | 8 | 5 | 0,77 | 0,77 |
| lien_quan | `khong_xac_dinh` | 29 | 17 | 8 | 0,32 | 0,35 |
| noi_ve | `pin_sac` | 17 | 19 | 15 | 0,83 | 0,83 |
| noi_ve | `man_hinh` | 25 | 25 | 19 | 0,75 | 0,76 |
| noi_ve | `hieu_nang` | 49 | 46 | 40 | 0,83 | 0,84 |
| noi_ve | `nhiet_do` | 6 | 5 | 5 | 0,91 | 0,91 |
| noi_ve | `camera` | 36 | 45 | 33 | 0,80 | 0,81 |
| noi_ve | `thiet_ke` | 42 | 39 | 34 | 0,83 | 0,84 |
| noi_ve | `do_ben` | 10 | 11 | 8 | 0,76 | 0,76 |
| noi_ve | `phan_mem` | 29 | 22 | 19 | 0,73 | 0,75 |
| noi_ve | `am_thanh` | 9 | 8 | 7 | 0,82 | 0,82 |
| noi_ve | `phan_cung_khac` | 21 | 15 | 11 | 0,60 | 0,61 |
| noi_ve | `gia` | 53 | 37 | 36 | 0,78 | 0,80 |
| noi_ve | `mua_ban` | 37 | 20 | 15 | 0,50 | 0,53 |
| noi_ve | `bao_hanh_sua_chua` | 5 | 2 | 2 | 0,57 | 0,57 |
| noi_ve | `may_chung` | 70 | 86 | 52 | 0,61 | 0,67 |
| noi_ve | `hang_nguoi_dung` | 45 | 42 | 32 | 0,71 | 0,74 |
| muc_dich | `danh_gia` | 200 | 224 | 176 | 0,71 | 0,83 |
| muc_dich | `hoi` | 63 | 58 | 55 | 0,90 | 0,91 |
| muc_dich | `thong_tin` | 72 | 60 | 51 | 0,74 | 0,77 |
| muc_dich | `de_nghi` | 43 | 52 | 36 | 0,73 | 0,76 |
| muc_dich | `ban_than` | 35 | 41 | 26 | 0,66 | 0,68 |
| muc_dich | `bao_loi` | 7 | 5 | 5 | 0,83 | 0,83 |
| muc_dich | `tranh_luan` | 45 | 43 | 31 | 0,68 | 0,70 |
| muc_dich | `dua` | 29 | 24 | 21 | 0,78 | 0,79 |
| muc_dich | `cong_kich` | 43 | 35 | 30 | 0,75 | 0,77 |
| muc_dich | `minigame` | 13 | 14 | 13 | 0,96 | 0,96 |
| muc_dich | `quang_cao` | 1 | 1 | 1 | 1,00 | 1,00 |
| muc_dich | `xa_giao` | 15 | 13 | 12 | 0,85 | 0,86 |
| muc_dich | `khong_xac_dinh` | 13 | 9 | 8 | 0,72 | 0,73 |


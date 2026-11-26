# Báo cáo gán mù lô K (B6)

> Mục đích: So nhãn lô K của A (Claude) và B (trưởng nhóm) gán mù: đồng ý thô, kappa, đồng ý dương, phân bố mỗi bên, chỗ lệch; cập nhật lần cuối: 2026-11-26.

**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.lot_k`. Nguồn: `nhan_lo_K_A.txt` (SHA-256 `8cdffc67…3d7e`), phiếu B (SHA-256 `b0e4174c…cd56`), dữ liệu v4. Luật: [đặc tả khám phá nhãn mục 7b](dac-ta-kham-pha-nhan.md#7-kiểm-b6); bộ nhãn duyệt 25/11.

- **n = 100 bình luận**, cả hai gán không xem của nhau. Ngưỡng dùng tiếp: κ ≥ 0,6.
- A là AI. B gán theo [hướng dẫn gán lô K](huong-dan-gan-lo-k.md) do A viết, nên kappa có thể cao hơn hai người độc lập thật.
- n = 100 nên kappa dao động mạnh: nhãn có dưới khoảng 10 bình luận thì xem đồng ý dương, đừng xét kappa riêng nó.
- Phiếu B có 0 dòng sai luật nhãn (mục 9); dòng sai vẫn được so như B đã gõ.
- Một bình luận lệch ở chiều 2 thì thường lệch luôn ở chiều 4, vì thái độ gắn với nhãn chiều 2.

## 1. Tóm tắt theo chiều

| Chiều | Loại | n | Đồng ý thô | κ | Ngưỡng 0,6 |
|---|---|---|---|---|---|
| 1. Liên quan tới gì | một nhãn | 100 | 87,0% | 0,72 | **đạt** |
| 5. Đã dùng máy | một nhãn | 100 | 97,0% | 0,83 | **đạt** |
| 6. Máy được nhắc | một nhãn | 100 | 95,0% | 0,92 | **đạt** |
| 2. Nói về phần nào | nhiều nhãn | 65 | 70,8% (trùng cả tập) | 0,81 (gộp) | **đạt** nếu xét theo kappa gộp |
| 3. Mục đích | nhiều nhãn | 100 | 76,0% (trùng cả tập) | 0,83 (gộp) | **đạt** nếu xét theo kappa gộp |
| 4. Thái độ | theo cặp | 79 | 86,1% (trùng cả tập) | xem mục 7 |  |

**Chiều nhiều nhãn xét ngưỡng bằng kappa gộp** (trưởng nhóm quyết 26/11): coi mỗi cặp (bình luận, nhãn) là một câu có/không và tính chung.

Chiều 2 chỉ tính trên 65 bình luận cả hai cùng gán `dien_thoai`; lệch ở chiều 1 đã tính ở chiều 1.

## 2. Chiều 1. Liên quan tới gì

Đồng ý thô 87,0%, κ = 0,72.

| Nhãn | A | B | Cả hai | κ (có/không) | Đồng ý dương |
|---|---|---|---|---|---|
| `dien_thoai` | 74 | 66 | 65 | 0,76 | 0,93 |
| `ngu_canh` | 16 | 21 | 15 | 0,77 | 0,81 |
| `nguoi_binh_luan` | 8 | 9 | 7 | 0,81 | 0,82 |
| `khong_xac_dinh` | 2 | 4 | 0 | -0,03 | 0,00 |

Ma trận (hàng: A, cột: B):

| A \ B | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `khong_xac_dinh` |
|---|---|---|---|---|
| `dien_thoai` | 65 | 4 | 1 | 4 |
| `ngu_canh` | 0 | 15 | 1 | 0 |
| `nguoi_binh_luan` | 0 | 1 | 7 | 0 |
| `khong_xac_dinh` | 1 | 1 | 0 | 0 |

## 3. Chiều 5. Đã dùng máy

Đồng ý thô 97,0%, κ = 0,83.

| Nhãn | A | B | Cả hai | κ (có/không) | Đồng ý dương |
|---|---|---|---|---|---|
| `co` | 9 | 10 | 8 | 0,83 | 0,84 |
| `khong_ro` | 91 | 90 | 89 | 0,83 | 0,98 |

## 4. Chiều 6. Máy được nhắc

Đồng ý thô 95,0%, κ = 0,92.

| Nhãn | A | B | Cả hai | κ (có/không) | Đồng ý dương |
|---|---|---|---|---|---|
| `goi_ten_may` | 30 | 32 | 29 | 0,91 | 0,94 |
| `chi_hang` | 18 | 17 | 15 | 0,83 | 0,86 |
| `khong_nhac` | 52 | 51 | 51 | 0,98 | 0,99 |

## 5. Chiều 2. Nói về phần nào (n = 65)

Trùng cả tập nhãn: 70,8%. Kappa gộp 0,81, đồng ý dương gộp 0,83.

| Nhãn | A | B | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|
| `may_chung` | 18 | 20 | 14 | 0,63 | 0,74 |
| `thiet_ke` | 10 | 11 | 10 | 0,94 | 0,95 |
| `hang_nguoi_dung` | 11 | 10 | 8 | 0,72 | 0,76 |
| `hieu_nang` | 7 | 10 | 7 | 0,80 | 0,82 |
| `mua_ban` | 8 | 8 | 5 | 0,57 | 0,62 |
| `gia` | 7 | 8 | 7 | 0,92 | 0,93 |
| `pin_sac` | 6 | 6 | 6 | 1,00 | 1,00 |
| `man_hinh` | 6 | 6 | 6 | 1,00 | 1,00 |
| `do_ben` | 4 | 8 | 4 | 0,64 | 0,67 |
| `phan_mem` | 4 | 5 | 4 | 0,88 | 0,89 |
| `camera` | 3 | 4 | 3 | 0,85 | 0,86 |
| `phan_cung_khac` | 4 | 3 | 3 | 0,85 | 0,86 |
| `nhiet_do` | 1 | 1 | 1 | 1,00 | 1,00 |
| `am_thanh` | 1 | 1 | 1 | 1,00 | 1,00 |

## 6. Chiều 3. Mục đích (n = 100)

Trùng cả tập nhãn: 76,0%. Kappa gộp 0,83, đồng ý dương gộp 0,85.

| Nhãn | A | B | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|
| `danh_gia` | 45 | 42 | 39 | 0,82 | 0,90 |
| `de_nghi` | 17 | 19 | 17 | 0,93 | 0,94 |
| `cong_kich` | 11 | 12 | 10 | 0,85 | 0,87 |
| `thong_tin` | 10 | 9 | 6 | 0,59 | 0,63 |
| `hoi` | 8 | 10 | 8 | 0,88 | 0,89 |
| `ban_than` | 5 | 8 | 5 | 0,75 | 0,77 |
| `tranh_luan` | 5 | 5 | 4 | 0,79 | 0,80 |
| `minigame` | 5 | 5 | 5 | 1,00 | 1,00 |
| `dua` | 6 | 3 | 2 | 0,42 | 0,44 |
| `xa_giao` | 1 | 2 | 1 | 0,66 | 0,67 |
| `bao_loi` | 1 | 1 | 1 | 1,00 | 1,00 |
| `quang_cao` | 1 | 1 | 1 | 1,00 | 1,00 |
| `khong_xac_dinh` | 1 | 0 | 0 | 0,00 | 0,00 |

## 7. Chiều 4. Thái độ

Trên 79 cặp (bình luận, nhãn chiều 2) mà cả hai cùng gán. Trùng cả tập thái độ: 86,1%.

| Thái độ | A | B | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|
| `tich_cuc` | 12 | 11 | 10 | 0,85 | 0,87 |
| `tieu_cuc` | 26 | 22 | 21 | 0,82 | 0,88 |
| `so_sanh` | 7 | 9 | 7 | 0,86 | 0,88 |
| `khong_danh_gia` | 36 | 37 | 32 | 0,77 | 0,88 |

## 8. Lệch ở đâu

52/100 bình luận lệch ít nhất một chiều. Theo chiều: `thai_do` 36, `noi_ve` 29, `muc_dich` 24, `lien_quan` 13, `may_nhac` 5, `da_dung` 3.

Danh sách đầy đủ kèm chữ bình luận: `data/kham-pha/lech_lo_K.csv` (ngoài git).

Chiều B đánh dấu `chua_chac`: chiều 1 26, chiều 2 28, chiều 3 25, chiều 4 16, chiều 5 2, chiều 6 3.

## 9. Dòng phiếu B sai luật nhãn

Không có.

# Báo cáo gán mù lô D2 (B6)

> Mục đích: So nhãn lô D2 của A (Claude) và B (trưởng nhóm) gán mù: đồng ý thô, kappa, đồng ý dương, phân bố mỗi bên, chỗ lệch; cập nhật lần cuối: 2026-11-26.

**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.lot_k --lo D2`. Nguồn: `nhan_lo_D2_A.txt` (SHA-256 `fcd3a848…4b8b`), phiếu B (SHA-256 `3ec53138…ce8a`), dữ liệu v4. Luật: [đặc tả khám phá nhãn mục 7b](dac-ta-kham-pha-nhan.md#7-kiểm-b6); bộ nhãn chốt 26/11, định nghĩa `dua`, `khong_xac_dinh` (chiều 1) sửa 26/11, thêm `ten_may`.

- **n = 50 bình luận**, cả hai gán không xem của nhau. Ngưỡng dùng tiếp: κ ≥ 0,6.
- A là AI. B gán theo [hướng dẫn gán lô K](huong-dan-gan-lo-k.md) do A viết, nên kappa có thể cao hơn hai người độc lập thật.
- Phiếu B (`.xlsx`) được tạo bằng công cụ, không lưu từ Excel; trưởng nhóm xác nhận đã gán tay ngày 26/11.
- n = 50 nên kappa dao động mạnh: nhãn có dưới khoảng 10 bình luận thì xem đồng ý dương, đừng xét kappa riêng nó.
- Phiếu B có 0 dòng sai luật nhãn (mục 9); dòng sai vẫn được so như B đã gõ.
- Một bình luận lệch ở chiều 2 thì thường lệch luôn ở chiều 4, vì thái độ gắn với nhãn chiều 2.

## 1. Tóm tắt theo chiều

| Chiều | Loại | n | Đồng ý thô | κ | Ngưỡng 0,6 |
|---|---|---|---|---|---|
| 1. Liên quan tới gì | một nhãn | 50 | 84,0% | 0,66 | **đạt** |
| 5. Đã dùng máy | một nhãn | 50 | 98,0% | 0,79 | **đạt** |
| 6. Máy được nhắc | một nhãn | 50 | 96,0% | 0,93 | **đạt** |
| 2. Nói về phần nào | nhiều nhãn | 34 | 70,6% (trùng cả tập) | 0,86 (gộp) | **đạt** nếu xét theo kappa gộp |
| 3. Mục đích | nhiều nhãn | 50 | 72,0% (trùng cả tập) | 0,82 (gộp) | **đạt** nếu xét theo kappa gộp |
| 4. Thái độ | theo cặp | 42 | 90,5% (trùng cả tập) | xem mục 7 |  |

**Chiều nhiều nhãn xét ngưỡng bằng kappa gộp** (trưởng nhóm quyết 26/11): coi mỗi cặp (bình luận, nhãn) là một câu có/không và tính chung.

Chiều 2 chỉ tính trên 34 bình luận cả hai cùng gán `dien_thoai`; lệch ở chiều 1 đã tính ở chiều 1.

## 2. Chiều 1. Liên quan tới gì

Đồng ý thô 84,0%, κ = 0,66.

| Nhãn | A | B | Cả hai | κ (có/không) | Đồng ý dương |
|---|---|---|---|---|---|
| `dien_thoai` | 34 | 38 | 34 | 0,80 | 0,94 |
| `ngu_canh` | 7 | 2 | 2 | 0,41 | 0,44 |
| `nguoi_binh_luan` | 1 | 4 | 1 | 0,38 | 0,40 |
| `khong_lien_quan` | 2 | 2 | 1 | 0,48 | 0,50 |
| `khong_xac_dinh` | 6 | 4 | 4 | 0,78 | 0,80 |

Ma trận (hàng: A, cột: B):

| A \ B | `dien_thoai` | `ngu_canh` | `nguoi_binh_luan` | `khong_lien_quan` | `khong_xac_dinh` |
|---|---|---|---|---|---|
| `dien_thoai` | 34 | 0 | 0 | 0 | 0 |
| `ngu_canh` | 4 | 2 | 1 | 0 | 0 |
| `nguoi_binh_luan` | 0 | 0 | 1 | 0 | 0 |
| `khong_lien_quan` | 0 | 0 | 1 | 1 | 0 |
| `khong_xac_dinh` | 0 | 0 | 1 | 1 | 4 |

## 3. Chiều 5. Đã dùng máy

Đồng ý thô 98,0%, κ = 0,79.

| Nhãn | A | B | Cả hai | κ (có/không) | Đồng ý dương |
|---|---|---|---|---|---|
| `co` | 2 | 3 | 2 | 0,79 | 0,80 |
| `khong_ro` | 48 | 47 | 47 | 0,79 | 0,99 |

## 4. Chiều 6. Máy được nhắc

Đồng ý thô 96,0%, κ = 0,93.

| Nhãn | A | B | Cả hai | κ (có/không) | Đồng ý dương |
|---|---|---|---|---|---|
| `goi_ten_may` | 14 | 12 | 12 | 0,90 | 0,92 |
| `chi_hang` | 9 | 9 | 9 | 1,00 | 1,00 |
| `khong_nhac` | 27 | 29 | 27 | 0,92 | 0,96 |

## 5. Chiều 2. Nói về phần nào (n = 34)

Trùng cả tập nhãn: 70,6%. Kappa gộp 0,86, đồng ý dương gộp 0,88.

| Nhãn | A | B | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|
| `may_chung` | 7 | 8 | 7 | 0,91 | 0,93 |
| `camera` | 7 | 7 | 6 | 0,82 | 0,86 |
| `gia` | 6 | 7 | 6 | 0,91 | 0,92 |
| `pin_sac` | 6 | 6 | 6 | 1,00 | 1,00 |
| `phan_mem` | 4 | 6 | 4 | 0,77 | 0,80 |
| `hieu_nang` | 4 | 5 | 4 | 0,87 | 0,89 |
| `mua_ban` | 2 | 6 | 2 | 0,45 | 0,50 |
| `man_hinh` | 3 | 3 | 3 | 1,00 | 1,00 |
| `thiet_ke` | 3 | 3 | 3 | 1,00 | 1,00 |
| `phan_cung_khac` | 1 | 1 | 1 | 1,00 | 1,00 |
| `hang_nguoi_dung` | 1 | 0 | 0 | 0,00 | 0,00 |

## 6. Chiều 3. Mục đích (n = 50)

Trùng cả tập nhãn: 72,0%. Kappa gộp 0,82, đồng ý dương gộp 0,83.

| Nhãn | A | B | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|
| `danh_gia` | 18 | 21 | 17 | 0,79 | 0,87 |
| `thong_tin` | 13 | 10 | 10 | 0,83 | 0,87 |
| `hoi` | 6 | 5 | 5 | 0,90 | 0,91 |
| `de_nghi` | 5 | 6 | 5 | 0,90 | 0,91 |
| `ban_than` | 5 | 6 | 5 | 0,90 | 0,91 |
| `khong_xac_dinh` | 4 | 4 | 3 | 0,73 | 0,75 |
| `tranh_luan` | 1 | 6 | 1 | 0,26 | 0,29 |
| `cong_kich` | 3 | 3 | 3 | 1,00 | 1,00 |
| `dua` | 2 | 1 | 1 | 0,66 | 0,67 |
| `xa_giao` | 0 | 1 | 0 | 0,00 | 0,00 |

## 7. Chiều 4. Thái độ

Trên 42 cặp (bình luận, nhãn chiều 2) mà cả hai cùng gán. Trùng cả tập thái độ: 90,5%.

| Thái độ | A | B | Cả hai | κ | Đồng ý dương |
|---|---|---|---|---|---|
| `tich_cuc` | 4 | 5 | 4 | 0,88 | 0,89 |
| `tieu_cuc` | 11 | 14 | 11 | 0,83 | 0,88 |
| `so_sanh` | 7 | 7 | 7 | 1,00 | 1,00 |
| `khong_danh_gia` | 20 | 18 | 18 | 0,90 | 0,95 |

## Tên máy (`ten_may`)

Trên 12 bình luận cả hai gán `goi_ten_may`: khớp đúng tập tên máy 9/12 (75,0%). Lệch ở stt: 712, 720, 743.

Mã không có trong danh mục `models.json` (gõ sai, hay máy ngoài danh mục): `11m`, `blackberryq10`, `doogees98`, `galaxya72016`, `ip11`, `ip7plus`, `ip8plus`, `ipadprom1`, `note20ultra`, `opporenoace`, `realmex2pro`, `renoace`.

## 8. Lệch ở đâu

30/50 bình luận lệch ít nhất một chiều. Theo chiều: `thai_do` 18, `noi_ve` 14, `muc_dich` 14, `lien_quan` 8, `may_nhac` 2, `da_dung` 1.

Danh sách đầy đủ kèm chữ bình luận: `data/kham-pha/lech_lo_D2.csv` (ngoài git).

Chiều B đánh dấu `chua_chac`: chiều 1 6, chiều 2 4, chiều 3 1, chiều 6 3.

## 9. Dòng phiếu B sai luật nhãn

Không có.

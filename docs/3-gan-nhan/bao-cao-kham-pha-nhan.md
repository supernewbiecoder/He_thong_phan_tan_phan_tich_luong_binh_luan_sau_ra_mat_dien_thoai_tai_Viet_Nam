# Báo cáo khám phá nhãn: so ba nguồn và đề xuất chốt bộ nhãn (B8)

> Mục đích: Áp luật chốt bộ nhãn (đặc tả khám phá nhãn mục 9) lên từng nhãn: tỷ lệ trong mẫu phân bố, nguồn, kappa lô K, đối chiếu HAC trên cả bộ dữ liệu, đề xuất giữ / thêm / gộp / bỏ để trưởng nhóm quyết; cập nhật lần cuối: 2026-11-26.

**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.b8`. Đề xuất nằm trong `src/labeling/b8.py` (`DE_XUAT`); trưởng nhóm quyết xong thì sửa đặc tả bộ nhãn, không sửa file này.

**Trạng thái: trưởng nhóm duyệt cả bảng ngày 26/11; bộ nhãn chốt ở [đặc tả bộ nhãn mục 8](dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611).** Đề xuất do A (AI) soạn. Tỷ lệ lấy từ [báo cáo phân bố](bao-cao-phan-bo-nhan.md): mẫu 600 bình luận, nhãn lô 1–5 do AI gán và trưởng nhóm đã kiểm cả 500, lô K hai bên gán mù và đã phân xử. Kappa lấy từ [báo cáo lô K](bao-cao-lo-k.md).

**Cách đọc:**
- *Luật nói*: code áp ngưỡng 3% và 1% lên tỷ lệ đo được. Chưa xét nhãn có phục vụ câu hỏi nào không.
- *Đề xuất*: A xét thêm việc nhãn phục vụ câu nào (kế hoạch mục 6) hoặc giúp đánh giá chất lượng dữ liệu.
- *Sát ngưỡng*: khoảng tin cậy 95% (bootstrap theo video) trùm lên 1% hay 3%. Vẫn quyết theo tỷ lệ đo được, nhưng nên xem lại.
- *κ lô K*: kappa có/không của riêng nhãn đó giữa A và B. Nhãn dưới khoảng 10 bình luận thì kappa dao động mạnh.

## Chiều 1. Liên quan tới gì

Phần áp dụng: 600 bình luận.

| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `dien_thoai` | đặt sẵn | Trực tiếp | 65,8 | [61,5; 69,9] | 0,76 | giữ | Q1–Q6: phần dữ liệu để phân tích | **giữ** | Luật 1 |
| `ngu_canh` | đặt sẵn | Ngữ cảnh | 18,5 | [14,9; 22,4] | 0,77 | giữ | Chất lượng dữ liệu: loại khỏi Q1–Q4 | **giữ** | Luật 1 |
| `khong_lien_quan` | đặt sẵn | Không liên quan | 2,5 | [1,3; 3,7] **sát ngưỡng** | – | giữ | Chất lượng dữ liệu | **giữ** | Luật 1 |
| `nguoi_binh_luan` | mới | – | 8,0 | [5,9; 10,3] | 0,81 | thêm | Chất lượng dữ liệu: tách cãi nhau khỏi ý kiến về máy | **thêm** | Luật 2. Là lỗi hay gặp nhất của A ở B7, nên cần nhãn riêng để người gán chú ý |
| `khong_xac_dinh` | mới | – | 4,3 | [2,8; 6,1] **sát ngưỡng** | -0,03 | thêm | Chất lượng dữ liệu | **thêm** | Luật 2. Chiều nào cũng cần nhãn "không xác định" (đặc tả mục 6) |
| `khong_noi_dung` | mới | – | 0,8 | [0,2; 1,5] **sát ngưỡng** | – | gộp (dưới 1%) | Chất lượng dữ liệu | **gộp vào `khong_xac_dinh`** | Luật 2: dưới 3%. Bình luận chỉ có emoji, dấu câu thì code nhận ra được, không cần người gán |

## Chiều 2. Nói về phần nào

Phần áp dụng: 395 bình luận `dien_thoai`.

| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `pin_sac` | đặt sẵn | Pin & sạc | 5,8 | [3,6; 8,2] | 1,00 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `man_hinh` | đặt sẵn | Màn hình | 8,1 | [5,6; 10,9] | 1,00 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `hieu_nang` | đặt sẵn | Hiệu năng (gồm nóng máy) | 13,4 | [10,0; 17,0] | 0,80 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `camera` | đặt sẵn | Camera | 9,9 | [7,1; 13,2] | 0,85 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `thiet_ke` | đặt sẵn | Thiết kế & độ bền | 13,7 | [10,4; 17,2] | 0,94 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `phan_mem` | đặt sẵn | Phần mềm | 6,8 | [4,4; 9,5] | 0,88 | giữ | Q2–Q5 | **giữ** | Luật 1 |
| `phan_cung_khac` | đặt sẵn | Phần cứng khác | 6,6 | [4,2; 9,2] | 0,85 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `gia` | đặt sẵn | Giá | 14,4 | [10,8; 18,2] | 0,92 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `bao_hanh_sua_chua` | đặt sẵn | Bảo hành & hậu mãi | 1,3 | [0,3; 2,5] **sát ngưỡng** | – | giữ | Q5 | **giữ** | Luật 1. Hiếm, ít dữ liệu cho Q5 |
| `do_ben` | tách | Thiết kế & độ bền | 5,3 | [3,3; 7,6] | 0,64 | thêm | Q2, Q5 (rơi vỡ, vào nước) | **thêm** | Luật 2: từ 3% |
| `nhiet_do` | tách | Hiệu năng (gồm nóng máy) | 1,8 | [0,5; 3,2] **sát ngưỡng** | 1,00 | gộp, trừ khi có câu hỏi cần | Q2, Q5 | **gộp vào `hieu_nang`** | Luật 2: dưới 3%; về lại như bộ đặt sẵn. Nóng máy cho Q5 thì ghi ở loại lỗi |
| `am_thanh` | tách | Phần cứng khác | 2,8 | [1,3; 4,5] **sát ngưỡng** | 1,00 | gộp, trừ khi có câu hỏi cần | Q2 | **gộp vào `phan_cung_khac`** | Luật 2: dưới 3%; về lại như bộ đặt sẵn |
| `mua_ban` | mới | – | 10,9 | [8,1; 14,1] | 0,57 | thêm | Gián tiếp: tách chuyện mua ở đâu, trả góp khỏi `gia` (Q2–Q4) | **thêm** | Luật 2: từ 3%. κ lô K 0,57: đã sửa định nghĩa (đặc tả bộ nhãn mục 2.1). Gộp vào `gia` sẽ lẫn chỗ mua, trả góp vào ý kiến về giá |
| `khac` | mới | – | 0,0 | ≤ 0,8 | – | gộp (dưới 1%) | Dự phòng | **giữ** | Chiều nào cũng có nhãn "khác" (đặc tả mục 6) |
| `may_chung` | mới | – | 20,8 | [16,9; 24,6] | 0,63 | thêm | Q1 (đón nhận chung), Q3 | **thêm** | Luật 2 |
| `hang_nguoi_dung` | mới | – | 11,9 | [8,8; 15,0] | 0,72 | thêm | Chất lượng dữ liệu: lời về hãng, fan không tính cho máy; Q6 | **thêm** | Luật 2 |

## Chiều 3. Mục đích

Phần áp dụng: 600 bình luận.

| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `danh_gia` | mới | – | 40,0 | [35,9; 44,2] | 0,82 | thêm | Q1–Q4: lọc bình luận có ý kiến | **thêm** | Luật 2 |
| `thong_tin` | mới | – | 14,2 | [11,4; 16,8] | 0,59 | thêm | Chất lượng dữ liệu | **thêm** | Luật 2 |
| `hoi` | mới | – | 12,2 | [9,7; 14,8] | 0,88 | thêm | Chất lượng dữ liệu: câu hỏi không phải ý kiến | **thêm** | Luật 2 |
| `de_nghi` | mới | – | 10,3 | [8,0; 12,9] | 0,93 | thêm | Chất lượng dữ liệu | **thêm** | Luật 2 |
| `tranh_luan` | mới | – | 9,8 | [7,4; 12,4] | 0,79 | thêm | Chất lượng dữ liệu; Q6 | **thêm** | Luật 2 |
| `cong_kich` | mới | – | 9,5 | [7,2; 11,9] | 0,85 | thêm | Lọc bình luận độc hại (quyết định 25/11); Q6 | **thêm** | Luật 2 |
| `ban_than` | mới | – | 6,8 | [4,9; 8,9] | 0,75 | thêm | Chất lượng dữ liệu; Q5 (người đã dùng kể) | **thêm** | Luật 2 |
| `dua` | mới | – | 7,2 | [5,0; 9,3] | 0,42 | thêm | Tách đùa với công kích (quyết định 25/11) | **thêm** | Luật 2. κ lô K 0,42 dưới 0,6: phải sửa định nghĩa |
| `minigame` | mới | – | 3,0 | [0,7; 6,0] **sát ngưỡng** | 1,00 | thêm | Phép thử độ nhạy (quyết định 5 của kế hoạch) | **thêm** | Luật 2, có câu hỏi cần riêng nó |
| `xa_giao` | mới | – | 3,2 | [1,8; 4,7] **sát ngưỡng** | 0,66 | thêm | Chất lượng dữ liệu | **thêm** | Luật 2 |
| `khong_xac_dinh` | mới | – | 1,8 | [0,8; 3,0] **sát ngưỡng** | 0,00 | gộp, trừ khi có câu hỏi cần | Chất lượng dữ liệu | **giữ** | Chiều nào cũng cần nhãn "không xác định" (đặc tả mục 6) |
| `bao_loi` | mới | – | 1,3 | [0,5; 2,3] **sát ngưỡng** | 1,00 | gộp, trừ khi có câu hỏi cần | Q5 | **thêm** | Luật 2: dưới 3% nhưng Q5 cần riêng nó (ví dụ có sẵn trong luật) |
| `quang_cao` | đặt sẵn | Spam: quảng cáo, mời liên hệ | 0,3 | [0,0; 0,8] | 1,00 | giữ | Chất lượng dữ liệu (spam) | **giữ** | Luật 1, 3 |

## Chiều 4. Thái độ

Phần áp dụng: 527 cặp (bình luận, nhãn chiều 2).

| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `tich_cuc` | đặt sẵn | Khen | 17,5 | – | 0,85 | giữ | Q1–Q4 | **giữ** | Luật 1 |
| `tieu_cuc` | đặt sẵn | Chê | 23,3 | – | 0,82 | giữ | Q1–Q5 | **giữ** | Luật 1 |
| `khong_danh_gia` | đặt sẵn | Trung tính | 47,8 | – | 0,77 | giữ | Q1–Q4 (không vào mẫu số Net) | **giữ** | Luật 1 |
| `so_sanh` | mới | – | 12,5 | – | 0,86 | thêm | Q3 (câu so sánh trực tiếp) | **thêm** | Luật 2 |

## Chiều 5. Đã dùng máy

Phần áp dụng: 600 bình luận.

| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `co` | đặt sẵn | Đã dùng | 6,3 | [4,3; 8,5] | 0,83 | giữ | Q5 | **giữ** | Luật 1 |
| `khong_ro` | đặt sẵn | Không rõ | 93,7 | [91,6; 95,7] | 0,83 | giữ | Q5 | **giữ** | Luật 1 |

## Chiều 6. Máy được nhắc

Phần áp dụng: 600 bình luận.

| Nhãn | Nguồn | Đặt sẵn tương ứng | % | KTC 95% | κ lô K | Luật nói | Phục vụ | **Đề xuất** | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| `goi_ten_may` | đặt sẵn | Gọi tên máy | 26,2 | [22,5; 30,0] | 0,91 | giữ | Q2–Q4: biết nhãn thuộc máy nào | **giữ** | Luật 1 |
| `khong_nhac` | đặt sẵn | Không rõ | 57,0 | [52,7; 61,4] | 0,98 | giữ | Q2–Q4 | **giữ** | Luật 1 |
| `chi_hang` | mới | – | 16,8 | [13,9; 20,0] | 0,83 | thêm | Q2–Q4: lời về hãng không gán cho một máy | **thêm** | Luật 2 |

## Nhãn đặt sẵn không có trong bộ nhãn từ dữ liệu

| Nhãn đặt sẵn | Trong mẫu | **Đề xuất** | Lý do |
|---|---|---|---|
| Spam: lừa đảo, cờ bạc | Không gặp trong mẫu (đã gán `quang_cao` nếu có) | **gộp vào `quang_cao`** | Luật 5: không câu hỏi nào bắt buộc cần riêng |
| Spam: khác | Không gặp | **bỏ** | Luật 5 |
| Đã dùng: chưa | Không tách được với "không rõ" khi gán | **bỏ (gộp vào `khong_ro`)** | Luật 5: Q5 chỉ cần biết có dùng |
| 9 loại lỗi | Chỉ 8 bình luận `bao_loi` trong 600 | **để tầng sau** | Luật 5: Q5 cần, nhưng mẫu ngẫu nhiên không đủ dữ liệu; gán loại lỗi trên mẫu riêng các bình luận báo lỗi |
| Máy được nhắc: chỉ suy được từ video | Không dùng: bộ nhãn cấm suy tên máy từ video | **bỏ** | Trái quy tắc gán theo chữ viết |

## Phân bố theo bộ nhãn chốt

Cùng mẫu, sau khi gộp theo đặc tả bộ nhãn mục 8. Chỉ ghi các nhãn có thay đổi; nhãn khác giữ số như các bảng trên.

| Chiều | Nhãn chốt | Gộp từ | % | KTC 95% (bootstrap video) |
|---|---|---|---|---|
| 1 | `khong_xac_dinh` | `khong_xac_dinh`, `khong_noi_dung` | 5,2 | [3,5; 7,0] |
| 2 | `hieu_nang` | `hieu_nang`, `nhiet_do` | 14,4 | [10,8; 18,0] |
| 2 | `phan_cung_khac` | `phan_cung_khac`, `am_thanh` | 9,1 | [6,2; 12,1] |

## Đối chiếu HAC trên cả bộ dữ liệu (đặc tả mục 4.4)

**Do AI làm, chưa có người kiểm.** Chỉ dùng để tìm khía cạnh mà mẫu 600 bỏ sót, không phải phân bố.

**1. Đếm từ khóa** trên 473.741 bình luận có nội dung của v4. Từ khóa của mỗi khía cạnh lấy từ các mã đã gom vào nó (`label_set.py`). Số này là bình luận **có nhắc từ khóa**, chưa chắc nói về khía cạnh đó (vd "cam" có thể là quả cam).

| Khía cạnh | Bình luận có nhắc | % cả bộ dữ liệu | % trong mẫu (chiều 2, trên `dien_thoai`) |
|---|---|---|---|
| `mua_ban` | 61.122 | 12,9 | 10,9 |
| `phan_mem` | 51.471 | 10,9 | 6,8 |
| `camera` | 48.438 | 10,2 | 9,9 |
| `gia` | 45.716 | 9,6 | 14,4 |
| `hieu_nang` | 42.600 | 9,0 | 13,4 |
| `man_hinh` | 29.376 | 6,2 | 8,1 |
| `thiet_ke` | 28.663 | 6,1 | 13,7 |
| `pin_sac` | 23.949 | 5,1 | 5,8 |
| `phan_cung_khac` | 16.370 | 3,5 | 6,6 |
| `nhiet_do` | 5.598 | 1,2 | 1,8 |
| `am_thanh` | 4.934 | 1,0 | 2,8 |
| `do_ben` | 4.614 | 1,0 | 5,3 |
| `bao_hanh_sua_chua` | 3.097 | 0,7 | 1,3 |

**2. Rà 100 ứng viên HAC đầu** (`hac_ung_vien.csv`): ứng viên nào là khía cạnh mà bộ nhãn chưa có.

Không có. Các ứng viên là khía cạnh đều thuộc nhãn đã có (pin, sạc, giá, game, chip, màn, cam, ảnh, thiết kế, viền, màu, loa, nhiệt, tản nhiệt, chống rung, đa nhiệm, cấu hình, phần mềm, ios, chính hãng…). Còn lại là mảnh từ ("độ", "sức", "kế", "năng"), tên hãng, tên dòng, hay từ chung.

## Tóm tắt đề xuất

- 44 nhãn: giữ 22, thêm 19, gộp 3.
- Bộ nhãn chốt: chiều 1 có 5 nhãn; chiều 2 có 11 khía cạnh + 2 nhãn ngoài khía cạnh + `khac`; chiều 3 có 13; chiều 4, 5, 6 không đổi.
- **Phải sửa định nghĩa trước khi gán chính thức** (κ lô K dưới 0,6): `dua`, `khong_xac_dinh` (chiều 1); `mua_ban` đã sửa 26/11.
- Chiều 6 chưa ghi **tên** máy: Q3, Q4 cần biết máy nào, nên guideline gán chính thức phải thêm trường tên máy.

# Báo cáo mã hóa mở (B4)

> Mục đích: Số liệu mã tự do của mã hóa mở trên mẫu khám phá nhãn: theo lô, hành vi, đối tượng, đối tượng mới từng lô; cập nhật lần cuối: 2026-11-23.

**File này do code sinh, đừng sửa tay.** Chạy lại: `python -m src.labeling.code_stats`. Nguồn: `data/kham-pha/phieu_ma_hoa_mo.csv` (SHA-256 `f4a7922a…d170`), dữ liệu v4, seed lấy mẫu `20261122`. Luật: [đặc tả khám phá nhãn](dac-ta-kham-pha-nhan.md) mục 5; cách mã: [guideline](huong-dan-kham-pha-nhan.md).

**Người mã: Claude (người mã hóa A).** Trưởng nhóm chưa kiểm từng mã. Mọi lô đã được Claude tự rà lượt 2 (lô 1 ngày 22/11, các lô khác ngày 23/11); tự rà không thay được người kiểm.

**Cách đọc:** đây là **đếm mã tự do, không phải phân bố nhãn**, nên chỉ ghi số đếm. Một bình luận có thể có nhiều mã. Phân bố, kèm khoảng tin cậy, chỉ tính ở B7 theo bộ nhãn đã kiểm.

## 1. Theo lô

| Lô | Bình luận | Mã | Mã / bình luận | Bình luận ≥ 2 mã | Mã `?` | Bình luận có mã `?` | Bình luận không hiểu, không rõ đối tượng | Bình luận có "đã/đang dùng" | Reply |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 100 | 158 | 1.58 | 37 | 11 | 10 | 4 | 5 | 42 |
| 2 | 100 | 134 | 1.34 | 25 | 17 | 17 | 4 | 9 | 40 |
| 3 | 100 | 128 | 1.28 | 21 | 17 | 17 | 11 | 2 | 38 |
| 4 | 100 | 130 | 1.30 | 23 | 8 | 8 | 1 | 4 | 40 |
| 5 | 100 | 130 | 1.30 | 22 | 8 | 8 | 8 | 3 | 41 |
| **Lô 1–5** | 500 | 680 | 1.36 | 128 | 61 | 60 | 28 | 23 | 201 |
| CD | 100 | 163 | 1.63 | 46 | 0 | 0 | 0 | 24 | 48 |

Lô `CD` là mẫu có chủ đích (tìm theo từ khóa "lỗi", "bảo hành"…): **không đại diện**, không cộng vào lô 1–5.

## 2. Hành vi (lô 1–5, 500 bình luận)

| Hành vi | Số mã | Số bình luận có |
|---|---|---|
| `chê` | 86 | 75 |
| `khen` | 79 | 69 |
| `hỏi` | 63 | 55 |
| `nhận xét` | 50 | 45 |
| `so sánh` | 45 | 37 |
| `giải thích` | 42 | 41 |
| `cà khịa` | 32 | 32 |
| `đùa` | 27 | 26 |
| `phản bác` | 26 | 26 |
| `khuyên` | 25 | 24 |
| `kể` | 21 | 20 |
| `nhắc` | 21 | 18 |
| `trả lời` | 19 | 19 |
| `mong muốn` | 16 | 16 |
| `?` | 15 | 15 |
| `chửi` | 15 | 15 |
| `yêu cầu` | 14 | 13 |
| `đồng tình` | 12 | 12 |
| `dự đoán` | 12 | 11 |
| `góp ý` | 11 | 11 |
| `dự thi` | 9 | 9 |
| `bênh` | 8 | 8 |
| `chào` | 7 | 7 |
| `than` | 6 | 6 |
| `khoe` | 4 | 4 |
| `cảm ơn` | 4 | 4 |
| `cãi nhau` | 4 | 4 |
| `lo ngại` | 2 | 2 |
| `cười` | 2 | 2 |
| `quảng cáo` | 1 | 1 |
| `trêu` | 1 | 1 |
| `xin` | 1 | 1 |

`?` là mã `không hiểu: ?`.

## 3. Đối tượng (lô 1–5)

- 680 mã, **412 đối tượng khác nhau**; 346 đối tượng chỉ gặp một lần.
- Đối tượng giữ nguyên từ của bình luận (guideline quy tắc 3), nên từ đồng nghĩa chưa gộp. Gộp ở B5.

| Đối tượng | Số mã |
|---|---|
| `bình luận cha` | 42 |
| `người review` | 41 |
| `người khác` | 18 |
| `máy (chung)` | 13 |
| `không hiểu` | 12 |
| `không rõ` | 11 |
| `máy nên mua` | 10 |
| `samsung (chung)` | 9 |
| `minigame` | 9 |
| `giá` | 8 |
| `màu máy` | 6 |
| `iphone (chung)` | 6 |
| `fan iphone` | 6 |
| `pin` | 6 |
| `tiền mua máy` | 5 |
| `trọng lượng` | 5 |
| `không nội dung` | 5 |
| `màn hình` | 5 |
| `xem sớm` | 4 |
| `điểm antutu` | 4 |
| `loa` | 4 |
| `xiaomi` | 4 |
| `ngoại hình` | 3 |
| `chip` | 3 |
| `ram` | 3 |
| `độ bền` | 3 |
| `quay phim` | 3 |
| `cửa hàng` | 3 |
| `người trong video` | 3 |
| `nhạc nền` | 3 |

## 4. Đối tượng và hành vi mới theo lô

| Lô | Đối tượng mới | Hành vi mới |
|---|---|---|
| 1 | 114 | `?`, `bênh`, `chào`, `chê`, `chửi`, `cà khịa`, `cãi nhau`, `cảm ơn`, `dự đoán`, `giải thích`, `góp ý`, `hỏi`, `khen`, `khoe`, `khuyên`, `kể`, `lo ngại`, `mong muốn`, `nhận xét`, `nhắc`, `phản bác`, `quảng cáo`, `so sánh`, `than`, `trêu`, `trả lời`, `yêu cầu`, `đùa`, `đồng tình` |
| 2 | 81 | không có |
| 3 | 72 | `cười`, `dự thi` |
| 4 | 76 | `xin` |
| 5 | 69 | không có |

Đối tượng mới chưa phải bão hòa: phần lớn là cách viết khác của cùng một ý. Bão hòa đếm theo **nhãn** sau khi gom (B5, đặc tả mục 6).

## 5. Mẫu có chủ đích

| Hành vi | Số mã |
|---|---|
| `chê` | 32 |
| `kể` | 17 |
| `giải thích` | 17 |
| `hỏi` | 15 |
| `khen` | 15 |
| `nhận xét` | 10 |
| `phản bác` | 8 |
| `mong muốn` | 7 |
| `so sánh` | 6 |
| `đùa` | 5 |
| `cà khịa` | 4 |
| `khuyên` | 4 |
| `trả lời` | 3 |
| `góp ý` | 3 |
| `chửi` | 3 |
| `cãi nhau` | 3 |
| `quảng cáo` | 2 |
| `bênh` | 2 |
| `than` | 2 |
| `chào` | 2 |
| `dự đoán` | 1 |
| `lo ngại` | 1 |
| `đồng tình` | 1 |

- 111 đối tượng chỉ gặp ở mẫu có chủ đích, không có trong lô 1–5. Đây là chỗ để B5 tìm loại hiếm (lỗi, bảo hành, trả góp…). Hay gặp nhất: `trả góp` (3), `tụt pin` (2), `iphone` (2), `xiaomi 14` (2), `bảo hành` (2), `cách sửa` (2), `ram 2gb` (1), `so sánh gaming phone với máy thường` (1), `mua theo fomo` (1), `máy xách tay` (1), `khuyến mãi cửa hàng` (1), `cửa hàng xách tay` (1), `bảo hành iphone mua ngoài apple store` (1), `thiết kế note 9` (1), `g6` (1).

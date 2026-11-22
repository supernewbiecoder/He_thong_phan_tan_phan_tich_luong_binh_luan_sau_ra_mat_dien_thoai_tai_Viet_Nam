# Đặc tả khám phá nhãn

> Mục đích: Luật của bước khám phá nhãn nội dung (B2–B7 của kế hoạch nhánh): lấy mẫu nào, mã hóa mở thế nào, gom mã thành bộ nhãn, dừng khi nào, kiểm đồng thuận, tính phân bố kèm khoảng tin cậy, và luật chốt bộ nhãn; cập nhật lần cuối: 2026-11-22.

**Trạng thái:** đặc tả nháp, chưa có code. Notebook `notebooks/3_label_discovery.ipynb` sẽ viết theo đúng file này. Sửa luật nào thì sửa file này trước, rồi mới sửa notebook. Cách làm cho người mã hóa: [hướng dẫn](huong-dan-kham-pha-nhan.md).

## 1. Trả lời câu hỏi gì

- Bình luận v4 có **những loại nội dung nào**, xếp theo từng chiều (nói về cái gì, để làm gì…)?
- Mỗi loại **chiếm bao nhiêu**, kèm khoảng tin cậy 95%?
- Bộ nhãn đã đặt sẵn trên `main` **thiếu, thừa** gì?

**Không làm ở bước này:** không huấn luyện mô hình; không đo bộ lọc spam; không cho số riêng của bộ 4 máy (mẫu lấy trên cả bộ dữ liệu).

## 2. Mẫu

### 2.1 Khung lấy mẫu

- Mọi bình luận trong `src/ingest/data/raw/comments.jsonl` bản v4 (473.786 dòng, SHA-256 `722d0e1e…2b45`), **chưa lọc gì**: giữ spam, tiếng nước ngoài, bình luận xin quà.
- Chỉ bỏ bình luận rỗng sau khi làm sạch nhẹ. Ghi lại số bị bỏ.
- **Làm sạch nhẹ** (chỉ để hiển thị trên phiếu, không đổi chữ):
  - giải HTML entity (`&amp;` → `&`);
  - chuẩn Unicode NFC;
  - bỏ ký tự điều khiển và ký tự vô hình, nhưng giữ xuống dòng và ký tự nối emoji (U+200D);
  - gộp khoảng trắng.

### 2.2 Mẫu ngẫu nhiên

- Lấy **600** bình luận ngẫu nhiên đơn, không hoàn lại, seed `20261122`.
- Giữ thứ tự ngẫu nhiên rồi chia theo vị trí:

| Lô | Vị trí | Dùng cho |
|---|---|---|
| Lô 1, 2, 3 | 1–300 | Mã hóa mở (B3) |
| Lô K | 301–400 | Kiểm bộ nhãn (B5): **không ai đọc trước B5** |
| Lô D1, D2 | 401–600 | Dự trữ: chỉ dùng khi chưa bão hòa (mục 5) hoặc phải kiểm lại bộ nhãn (mục 6) |

- Nếu trưởng nhóm chọn cỡ 500 cho mã hóa mở (quyết định 1 của kế hoạch), thì lô mở là vị trí 1–500, lô K là 501–600, và lấy thêm 200 bình luận làm dự trữ.

### 2.3 Mẫu có chủ đích

- **Mục đích:** không sót những loại hiếm mà quan trọng, như người đã dùng máy báo lỗi.
- **Cách lấy:** với mỗi từ khóa dưới đây, lấy ngẫu nhiên tối đa 10 bình luận chứa từ đó (sau làm sạch nhẹ, không phân biệt hoa thường), bỏ những bình luận đã có trong mẫu ngẫu nhiên, rồi lấy ngẫu nhiên 100 bình luận từ phần còn lại. Seed `20261122`.

  `lỗi` · `hỏng` · `bảo hành` · `đổi trả` · `mua về` · `đang dùng` · `đang xài` · `nóng máy` · `tụt pin` · `so với` · `trả góp` · `xách tay`

- Gắn `mau = chu_dich`. **Chỉ dùng ở B3–B4 để tìm thêm mã, không tính vào phân bố.**

### 2.4 Phiếu mã hóa

Mỗi người một phiếu (CSV, UTF-8), mỗi bình luận một dòng:

| Cột | Ai điền | Nội dung |
|---|---|---|
| `stt` | Notebook | Số thứ tự trong phiếu |
| `lo` | Notebook | `1`, `2`, `3`, `K`, `D1`, `D2`, `CD` (có chủ đích) |
| `mau` | Notebook | `ngau_nhien` / `chu_dich` |
| `comment_id` | Notebook | |
| `may_video` | Notebook | Trường `model` (máy của video) |
| `loai_video` | Notebook | `video_type` của video, lấy dòng mới nhất trong `videos.jsonl` |
| `la_reply` | Notebook | `co` / `khong` |
| `binh_luan` | Notebook | Chữ bình luận sau làm sạch nhẹ |
| `binh_luan_cha` | Notebook | Bình luận cha nếu là reply, sau làm sạch nhẹ, cắt ở 600 ký tự |
| `ma_tu_do` | Người mã hóa | Các mã tự do, cách nhau bằng `;` (mục 3) |
| `ghi_chu` | Người mã hóa | Ca khó, câu hỏi cho người kia |

- Phiếu **không** có `author_name`, `author_hash` hay bất cứ thông tin nào về người viết.
- **Chia việc:**
  - lô 1: **cả hai người**, độc lập;
  - lô 2: người A; lô 3: người B;
  - mẫu có chủ đích: mỗi người một nửa.

## 3. Mã hóa mở (B3)

1. Đọc bình luận, và bình luận cha nếu là reply. Ghi **một hay nhiều mã** vào `ma_tu_do`.
2. Mỗi mã là một cụm từ ngắn, mô tả bình luận **nói về cái gì** hoặc **để làm gì** ("khen pin", "hỏi giá", "xin quà", "chê người review", "kể lỗi màn hình"). Không có khuôn bắt buộc.
3. **Không dùng danh sách nhãn có sẵn** (9 khía cạnh, các mức liên quan…) khi mã hóa. **Đọc mục 7 sau khi xong B4**, không đọc trước.
4. Mã theo những gì được viết, không đoán ý người viết. Mỉa mai rõ ràng thì mã theo nghĩa thật và thêm mã "mỉa mai".
5. Không bỏ trống dòng nào. Bình luận không hiểu được thì ghi mã "không hiểu" và ghi lý do vào `ghi_chu`.
6. Không xem phiếu của người kia trước khi cả hai xong lô đó.

## 4. Gom mã thành bộ nhãn (B4)

- **Sau lô 1:** hai người đặt mã của mình cạnh nhau, gom các mã cùng nghĩa thành **nhãn**, rồi xếp các nhãn vào **chiều**.
  - Một chiều là một câu hỏi về bình luận, ví dụ "bình luận nói về cái gì?".
  - Ghi rõ mỗi chiều là **một nhãn** cho mỗi bình luận (các nhãn loại trừ nhau) hay **nhiều nhãn**.
- **Mỗi nhãn ghi:**
  - tên ngắn;
  - định nghĩa 1–2 câu;
  - 2 ví dụ thuộc nhãn, 1 ví dụ dễ nhầm nhưng không thuộc;
  - các mã tự do đã gom vào;
  - số lần gặp;
  - lô mà nhãn xuất hiện lần đầu.
- Mỗi chiều có nhãn **"khác"**, và nhãn **"không xác định"** nếu cần.
- **Sau lô 2, 3:** mã mới thì gom vào nhãn có sẵn, hoặc tạo nhãn mới (ghi lô tạo).
- Bộ nhãn viết ở `docs/3-gan-nhan/dac-ta-bo-nhan.md`, tạo file này khi bắt đầu B4.

Có những chiều nào là do **dữ liệu** quyết. Bộ nhãn đặt sẵn trên `main` (mục 7) chỉ dùng để so ở B7.

## 5. Bão hòa: khi nào là đủ (B4)

- Sau mỗi lô, ghi hai số: **số nhãn mới** (ở mức bộ nhãn) và số mã tự do mới.
- **Luật dừng:**
  - lô 3 không tạo thêm nhãn mới nào thì đủ;
  - còn nhãn mới thì mã hóa tiếp lô D1, rồi D2, cho tới khi một lô không tạo nhãn mới;
  - hết D2 mà vẫn còn nhãn mới thì báo trưởng nhóm, lấy thêm mẫu.
- Lô dự trữ đã dùng để mã hóa mở thì tính vào mẫu phân bố (mục 6), như lô 1–3.
- Nhãn chỉ gặp một lần trong cả mẫu vẫn ghi lại; B7 xét có gộp vào "khác" không.

## 6. Kiểm bộ nhãn và tính phân bố (B5, B6)

**B5: kiểm bộ nhãn trên lô K.**
- Hai người gán lô K **độc lập**, theo bộ nhãn, cho từng chiều.
- Với từng chiều, báo cả ba: tỷ lệ đồng ý thô, Cohen's kappa, phân bố nhãn của từng người.
- Kappa ≥ 0,6 thì dùng chiều đó.
- Kappa < 0,6 thì sửa định nghĩa dựa trên các ca lệch, rồi kiểm lại trên 50 bình luận dự trữ chưa ai đọc. Hai lần vẫn dưới ngưỡng thì B7 quyết bỏ hay gộp chiều đó.
- Mọi ca lệch ở lô K do hai người bàn và thống nhất. Không thống nhất được thì trưởng nhóm quyết.

**B6: gán cả mẫu theo bộ nhãn cuối.**
- **Mẫu phân bố** gồm lô 1–3, các lô dự trữ đã dùng để mã hóa mở, và lô K. Không gồm mẫu có chủ đích.
- Lô 1–3 phải gán lại theo bộ nhãn cuối (mã tự do chưa đủ). Mỗi bình luận một người gán, trừ lô K đã gán đôi.

**Cách tính:**
- Tỷ lệ của một nhãn = số bình luận có nhãn đó / số bình luận trong mẫu phân bố (`n`). Chiều nhiều nhãn thì tổng tỷ lệ có thể vượt 100%.
- Khoảng tin cậy 95% theo Wilson, với `x` là số bình luận có nhãn, `z = 1,96`:

  ```text
  tâm = (x + z²/2) / (n + z²)
  nửa độ rộng = z / (n + z²) · √( x·(n − x)/n + z²/4 )
  ```

- Nhãn chỉ áp dụng cho một phần mẫu (vd khía cạnh chỉ có ở bình luận nói về máy): báo thêm tỷ lệ **trong phần đó**, và ghi rõ mẫu số.
- Nhãn không xuất hiện lần nào trong `n` bình luận: báo cận trên ≈ `3/n` (khoảng 0,75% với `n = 400`).
- **Tách theo nhóm:** loại video, bình luận gốc hay reply, hãng của máy của video. Nhóm có dưới 30 bình luận thì chỉ ghi số đếm, không ghi phần trăm.
- Bình luận cùng video không độc lập. Nhưng 400 bình luận ngẫu nhiên rải trên 4.682 video thì rất ít video có quá 1–2 bình luận trong mẫu, nên công thức Wilson dùng được. Kiểm điều này bằng cách đếm số bình luận mỗi video trong mẫu, và ghi kết quả vào báo cáo.

## 7. So với bộ nhãn đã đặt và chốt bộ nhãn (B7)

Bộ nhãn đã đặt sẵn trên `main` (guideline v1 nháp, 20/11). **Chỉ dùng ở bước này:**

| Chiều | Nhãn đặt sẵn |
|---|---|
| Mức liên quan | Trực tiếp (nói về điện thoại) / ngữ cảnh (video, người review, quà tặng) / không liên quan |
| Spam (theo nội dung) | Không / quảng cáo, mời liên hệ / lừa đảo, cờ bạc / khác |
| Khía cạnh | Pin & sạc · Màn hình · Hiệu năng (gồm nóng máy) · Camera · Thiết kế & độ bền · Phần mềm · Phần cứng khác · Giá · Bảo hành & hậu mãi |
| Cảm xúc theo khía cạnh | Khen / chê / trung tính |
| Máy được nhắc | Gọi tên máy / chỉ suy được từ video / không rõ |
| Đã dùng máy, loại lỗi | Đã dùng / chưa / không rõ; 9 loại lỗi |

**Luật quyết** (áp cho từng nhãn, ghi lý do và số liệu cho từng quyết định):
1. **Giữ** nhãn đặt sẵn khi nó có trong dữ liệu **và** phục vụ ít nhất một câu hỏi Q1–Q6 (kế hoạch mục 6) hoặc việc đánh giá chất lượng dữ liệu.
2. **Thêm** nhãn mới khi nó chiếm **từ 3%** số bình luận của phần áp dụng trở lên (vd từ 3% số bình luận nói về máy, với chiều khía cạnh) **và** phục vụ một câu hỏi hoặc việc đánh giá chất lượng dữ liệu.
3. **Gộp** vào nhãn gần nhất hoặc "khác": nhãn chiếm dưới 1% và không phục vụ câu hỏi nào.
4. **Bỏ** hoặc gộp: nhãn hay chiều có kappa dưới 0,6 sau hai lần sửa (mục 6).
5. Nhãn đặt sẵn **không xuất hiện** lần nào: giữ chỉ khi có câu hỏi bắt buộc cần nó. Khi đó ghi rõ cận trên của tỷ lệ, và rằng khó có đủ dữ liệu cho câu hỏi đó.

## 8. Đầu ra và file

| File | Nội dung | Có chưa |
|---|---|---|
| `notebooks/3_label_discovery.ipynb` | Lấy mẫu, xuất phiếu; đọc phiếu để tính bão hòa, đồng thuận, phân bố | Chưa |
| `data/kham-pha/mau.csv` | Danh sách mẫu: `comment_id`, lô, seed, SHA-256 file nguồn | Chưa |
| `data/kham-pha/phieu_<ma_nguoi>.csv` | Phiếu mã hóa đã điền | Chưa |
| `docs/3-gan-nhan/dac-ta-bo-nhan.md` | Bộ nhãn: chiều, nhãn, định nghĩa, ví dụ | Chưa (tạo ở B4) |
| `docs/3-gan-nhan/bao-cao-kham-pha-nhan.md` | Bão hòa, đồng thuận, phân bố kèm khoảng tin cậy, so sánh, quyết định B7 | Chưa (B6–B7) |

`data/` nằm ngoài git. Phiếu có nội dung bình luận thật nên chỉ chia sẻ trong nhóm.

## 9. Giới hạn đã biết

- 300–400 bình luận chỉ đủ để thấy những loại chiếm từ khoảng 1% trở lên. Nhãn hiếm hơn có thể không xuất hiện, và nếu có thì khoảng tin cậy rất rộng.
- Mẫu lấy trên cả v4 (139 máy, 2014–2026), nên phân bố mô tả cả bộ dữ liệu, không riêng bộ 4 máy hay một giai đoạn nào.
- Người mã hóa có thiên kiến riêng. Hai người độc lập cùng phép kiểm kappa giảm bớt thiên kiến, nhưng không loại hết.
- Mẫu có chủ đích không đại diện cho dữ liệu, chỉ dùng để tìm nhãn.

# Đặc tả khám phá nhãn

> Mục đích: Luật của bước khám phá nhãn (B2–B8 của kế hoạch nhánh): ba nguồn tìm nhãn, vai trò người mã hóa, lấy mẫu và vì sao lấy 500, thuật toán HAC, mã hóa mở, gom bộ nhãn, kiểm đồng thuận, công thức tính phân bố và khoảng tin cậy, luật chốt bộ nhãn; cập nhật lần cuối: 2026-11-26.

**Quyết định của trưởng nhóm ngày 22/11:**
1. Kết hợp ba nguồn tìm nhãn (mục 1).
2. HAC dùng bản không cần tách từ (mục 4).
3. Mã hóa mở 500 bình luận (mục 3.3).
4. **Claude mã hóa, trưởng nhóm kiểm** (mục 2).

**Ngày 23/11:** trưởng nhóm không chấm danh sách HAC; HAC chỉ để Claude đối chiếu (mục 4.4).

**Ngày 23/11, sau khi so mã A–B (mục 7d):** trưởng nhóm cho sửa bảng hành vi ([guideline mục 2](huong-dan-kham-pha-nhan.md#bảng-hành-vi)); hành vi so và đếm không phân biệt chữ hoa (mục 5); che thêm tên dạng `+Tên Họ` (mục 2).

**Ngày 24/11:** trưởng nhóm yêu cầu thống nhất hai từ *nhãn* và *khía cạnh* ([Thuật ngữ](#thuật-ngữ)); chiều 2 đổi tên (đặc tả bộ nhãn), không đổi nhãn nào.

**Ngày 25/11:** trưởng nhóm duyệt bốn điểm của luật chốt bộ nhãn (mục 9): mẫu số của từng chiều; nhãn mới dưới 3%; nhãn dưới 1% mà giúp đánh giá chất lượng dữ liệu; tỷ lệ sát ngưỡng.

Code: `src/labeling/` (mục 10). Cách làm từng việc: [guideline mã hóa](huong-dan-kham-pha-nhan.md). Sửa luật nào thì sửa file này trước, rồi mới sửa code và test.

## Thuật ngữ

Mọi tài liệu và code của nhánh dùng các từ dưới đây theo **một nghĩa duy nhất**. Chỗ nào dùng khác thì sửa chỗ đó. Trưởng nhóm yêu cầu thống nhất ngày 24/11.

| Từ | Nghĩa | Ví dụ |
|---|---|---|
| **Mã** (mã tự do) | Ghi chú khi đọc bình luận ở B4, dạng `đối tượng: hành vi (ghi chú phụ)`. Không chọn từ danh sách có sẵn | `pin: khen` |
| **Đối tượng** | Phần trước dấu `:` của mã: bình luận nói về cái gì, bằng chữ của chính bình luận | `pin`, `tụt pin`, `cục sạc 67w` |
| **Hành vi** | Phần sau dấu `:` của mã: người viết làm gì. Chọn trong [bảng hành vi](huong-dan-kham-pha-nhan.md#bảng-hành-vi) | `khen`, `hỏi` |
| **Bộ nhãn** | Danh sách đóng gồm các chiều và nhãn, kèm định nghĩa, gom từ mã ở B5. Viết ở [đặc tả bộ nhãn](dac-ta-bo-nhan.md) | |
| **Chiều** | Một câu hỏi về bình luận. Mỗi chiều có danh sách nhãn riêng | chiều 3: "viết để làm gì?" |
| **Nhãn** | Một câu trả lời trong danh sách của một chiều, có định nghĩa. Mỗi nhãn thuộc đúng một chiều. Tên viết không dấu, nối bằng `_` | `pin_sac` (chiều 2), `hoi` (chiều 3), `co` (chiều 5) |
| **Khía cạnh** | Một bộ phận hay tính chất của điện thoại, hoặc một việc trong trải nghiệm mua và dùng (giá, mua bán, bảo hành). **Mỗi khía cạnh là một nhãn của chiều 2**; danh sách ở [đặc tả bộ nhãn mục 2.1](dac-ta-bo-nhan.md#21-khía-cạnh) | `pin_sac`, `camera`, `gia` |
| **Nhãn ngoài khía cạnh** | Nhãn của chiều 2 nói về điện thoại mà không nêu phần nào của nó ([đặc tả bộ nhãn mục 2.2](dac-ta-bo-nhan.md#22-ngoài-khía-cạnh)) | `may_chung` (cả máy), `hang_nguoi_dung` (hãng, fan, người mua) |
| **Khía cạnh đặt sẵn** | 9 khía cạnh trên `main`, có trước khi đọc dữ liệu. Chỉ dùng để so ở B8 | "Pin & sạc" |
| **Ứng viên khía cạnh** | Từ do HAC đề xuất (mục 4). Chưa là khía cạnh cho tới khi có trong bộ nhãn | `pin`, `sức`, `chủ` |

**Hai từ này quan hệ thế nào:**

```text
bình luận ──B4, người đọc──→ mã  (đối tượng: hành vi)      chữ tự do
mã ────────B5, gom──────────→ nhãn, xếp vào 6 chiều        danh sách đóng
                              └ chiều 2 = khía cạnh + nhãn ngoài khía cạnh
```

- **Mọi khía cạnh đều là nhãn. Không phải nhãn nào cũng là khía cạnh.** `hoi`, `co`, `tich_cuc`, `may_chung` là nhãn, không phải khía cạnh.
- Nói chung về một nhãn bất kỳ thì viết "nhãn". Chỉ viết "khía cạnh" hay "nhãn khía cạnh" khi đó đúng là một khía cạnh.
- Khi đếm thì nói rõ chiều và loại: "N nhãn của chiều 2, trong đó M khía cạnh".
- Không dùng "nhãn" cho từ loại (tính từ, danh từ) hay cho nhóm trung gian trong code.

**Vì sao `may_chung` và `hang_nguoi_dung` không phải khía cạnh:** câu "S24 Ultra đẹp vãi" hay "fan táo cay rồi" không nêu phần nào của máy, nên không biết khen chê phần nào. Guideline mục 2 ghi các câu này là "không nêu khía cạnh". Trên `main` cũng vậy: guideline gán nhãn ghi "máy ngon thật" là không nêu khía cạnh, và 9 khía cạnh đặt sẵn không có hãng.

## 1. Trả lời câu hỏi gì, bằng ba nguồn nào

Câu hỏi:
- bình luận v4 có **những loại nội dung nào**, xếp theo từng chiều (nói về cái gì, để làm gì…);
- mỗi loại **chiếm bao nhiêu**, kèm khoảng tin cậy 95%;
- mỗi bình luận **cần đánh dấu những trường nào** để trả lời Q1–Q6.

Không nguồn nào trả lời đủ một mình, nên dùng ba nguồn rồi so với nhau (B8):

| Nguồn | Làm trên | Cho được | Không cho được |
|---|---|---|---|
| 1. HAC (mục 4) | Cả 473 nghìn bình luận | **Ứng viên khía cạnh**, cả khía cạnh hiếm. Từ 23/11 chỉ để đối chiếu, không ai chấm | Các chiều khác (mục đích, đã dùng máy, máy được nhắc…); phân bố theo bình luận |
| 2. Mã hóa mở (mục 5–8) | Mẫu ngẫu nhiên 600 bình luận | **Các chiều và nhãn**, kèm **phân bố** và khoảng tin cậy | Nhãn quá hiếm (dưới khoảng 0,5%) |
| 3. Bộ nhãn đặt sẵn trên `main` (mục 9) | | Giả định ban đầu để so | Không phải bằng chứng từ dữ liệu |

**Không làm ở bước này:** không huấn luyện mô hình; không đo bộ lọc spam; không cho số riêng của bộ 4 máy (mẫu lấy trên cả bộ dữ liệu).

## 2. Vai trò và quy tắc mù

| Vai trò | Ai | Làm gì |
|---|---|---|
| Người mã hóa A | **Claude** (trợ lý AI trong Claude Code, phiên của trưởng nhóm) | Mã hóa mở lô 1–5 và mẫu có chủ đích; gom mã thành bộ nhãn; gán lô K theo bộ nhãn; gán lại cả mẫu ở B7; đối chiếu HAC (mục 4.4) |
| Người kiểm B | **Trưởng nhóm** | Gán **mù** lô K; kiểm nhãn của A; duyệt bộ nhãn |

**Quy tắc mù**, để mọi số đồng thuận đo được thật:
1. Không ai đọc chữ bình luận của lô K và lô dự trữ trước B6. Code chỉ xuất phiếu lô 1–5 và mẫu có chủ đích; phiếu lô K xuất riêng ở B6.
2. Ở lô K, A và B gán độc lập. Cả hai nộp xong mới so.

**Dữ liệu đưa cho Claude:** chỉ chữ bình luận và bình luận cha đã làm sạch nhẹ, cùng vài trường mô tả (máy của video, loại video, nhóm kênh, tuần, gốc hay reply, của chủ kênh hay không). **Không** có `author_name`, `author_hash` hay bất cứ thông tin định danh người viết nào.

Tên người dùng được nhắc trong chữ bình luận được che thành `@[người dùng]` (hàm `an_nhac_ten`), ở hai dạng:
- `@tên`: YouTube tự chèn khi reply.
- `+Tên Họ`: kiểu nhắc tên cũ, thời YouTube gắn với Google+. Thêm ngày 23/11; phiếu lô 1–5 và CD xuất trước đó nên còn 3 tên dạng này. Che dấu `+` cùng các chữ viết hoa chữ cái đầu liền sau, tối đa 4 chữ. Chữ đầu không viết hoa thì giữ nguyên, để không che nhầm `+1`.

Tên viết không có `@` hay `+` thì code không che được; người mã hóa không chép tên đó vào mã hay ghi chú. Trưởng nhóm đồng ý cho Claude đọc bình luận để mã hóa ngày 22/11 (quyết định 3 của kế hoạch). Dịch vụ AI khác vẫn phải hỏi trước.

**Hạn chế phải ghi trong báo cáo:**
- A đã soạn bộ nhãn đặt sẵn trên `main`, nên dễ bị bộ nhãn đó dẫn dắt khi mã hóa mở (hiệu ứng mỏ neo).
- B kiểm nhãn của A thì dễ đồng ý theo (thiên lệch tự động hóa).
- Đo hai rủi ro này bằng kappa giữa A và B trên lô K mù, và bằng tỷ lệ nhãn B phải sửa khi kiểm (mục 7).

## 3. Mẫu

### 3.1 Khung lấy mẫu và làm sạch nhẹ

- Mọi bình luận trong `src/ingest/data/raw/comments.jsonl` bản v4 (473.786 dòng, SHA-256 `722d0e1e…2b45`), **chưa lọc gì**: giữ spam, tiếng nước ngoài, bình luận minigame.
- Chỉ bỏ bình luận rỗng sau khi làm sạch nhẹ. Ghi lại số bị bỏ.
- **Làm sạch nhẹ** (hàm `lam_sach_nhe`; chỉ để hiển thị và cho HAC đọc, không đổi chữ):
  - giải HTML entity (`&amp;` → `&`);
  - chuẩn Unicode NFC;
  - bỏ ký tự điều khiển và ký tự vô hình (loại Unicode `Cc`, `Cf`), nhưng giữ xuống dòng và ký tự nối emoji (U+200D);
  - gộp khoảng trắng, gộp từ 3 dòng trống trở lên thành 2.

### 3.2 Mẫu ngẫu nhiên

- Lấy **800** bình luận ngẫu nhiên đơn, không hoàn lại, seed `20261122`.
- Giữ thứ tự ngẫu nhiên rồi chia theo vị trí:

| Lô | Vị trí | Dùng cho |
|---|---|---|
| Lô 1–5 | 1–500 | Mã hóa mở (B4) |
| Lô K | 501–600 | Kiểm bộ nhãn (B6). **Không ai đọc trước B6** |
| Lô D1, D2 | 601–800 | Dự trữ: chỉ dùng khi chưa bão hòa (mục 6) hoặc phải kiểm lại bộ nhãn (mục 7) |

- **Mẫu phân bố** gồm lô 1–5 và lô K, tức **n = 600** (mục 8).

### 3.3 Vì sao mã hóa mở 500 bình luận

Ký hiệu: `n` là cỡ mẫu, `p` là tỷ lệ thật của một nhãn trong cả bộ dữ liệu, `z = 1,96` (ứng với độ tin cậy 95%).

**(a) Thấy được nhãn hiếm.** Xác suất một nhãn chiếm tỷ lệ `p` xuất hiện ít nhất một lần trong `n` bình luận ngẫu nhiên:

```text
P(gặp ≥ 1 lần) = 1 − (1 − p)^n
```

| Tỷ lệ thật của nhãn | n = 300 | n = 500 |
|---|---|---|
| 0,5% | 78% | 92% |
| 1% | 95% | 99,3% |
| 2% | 99,8% | gần 100% |

Với 500, một nhãn chiếm từ 0,5% trở lên hầu như chắc chắn xuất hiện, nên không bị sót khi gom bộ nhãn. Với 300, cứ khoảng 5 nhãn cỡ 0,5% thì sót 1.

**(b) Tỷ lệ đủ chính xác.** Nửa độ rộng khoảng tin cậy 95% của một tỷ lệ xấp xỉ:

```text
E ≈ z · √( p · (1 − p) / n )
```

Đảo lại, cỡ mẫu cần để sai số không quá `E`:

```text
n = z² · p · (1 − p) / E²
```

Trường hợp xấu nhất là `p = 0,5`. Muốn `E = 4%` thì `n = 1,96² · 0,25 / 0,04² = 600,25`, tức khoảng **600**. Mẫu phân bố gồm 500 bình luận mã hóa mở cộng 100 của lô K là đúng 600:

| Tỷ lệ thật của nhãn | n = 400 (nếu chọn 300 + 100) | n = 600 (500 + 100) |
|---|---|---|
| 50% | ±4,9% | **±4,0%** |
| 10% | ±2,9% | **±2,4%** |
| 3% | ±1,7% | **±1,4%** |

**(c) Đủ để tách nhóm.** Kiểm tra cấu trúc (B1) cho thấy cần so theo nhóm. Mẫu 600 thật (seed `20261122`, đếm từ `mau.csv`) có:
- 249 reply và 351 bình luận gốc;
- 360 bình luận của 5 kênh lớn, 237 của các kênh còn lại, 3 không rõ kênh;
- 406 bình luận ở tuần 1–2 và 194 ở tuần 3–4;
- 18 bình luận của chủ kênh. Nhóm này dưới 30 nên chỉ ghi số đếm (mục 8).

Nhóm nhỏ nhất của ba cách tách đầu (194, tuần 3–4) vẫn cho sai số ±7,0% ở `p = 50%`. Với n = 400, nhóm đó chỉ khoảng 130 bình luận, sai số khoảng ±8,6%.

**(d) Không cần hiệu chỉnh tổng thể hữu hạn.** `n / N = 600 / 473.786 ≈ 0,13%`, nên hệ số hiệu chỉnh `√(1 − n/N) ≈ 0,9994`, không đáng kể.

**(e) Chi phí.** Claude mã hóa mở; người chỉ làm các việc ở mục 2. Tăng từ 300 lên 500 gần như không tốn thêm công người.

**(f) Lưu ý:** các sai số ở (b), (c) tính như thể mỗi bình luận độc lập. Bình luận cùng video thì không độc lập, nên khoảng tin cậy chính tính bằng bootstrap theo video (mục 8). Khoảng đó có thể rộng hơn bảng trên.

### 3.4 Mẫu có chủ đích

- **Mục đích:** không sót những loại hiếm mà quan trọng, như người đã dùng máy báo lỗi.
- **Cách lấy:** với mỗi từ khóa dưới đây, lấy ngẫu nhiên tối đa 10 bình luận chứa từ đó (sau làm sạch nhẹ, chữ thường), bỏ những bình luận đã có trong mẫu ngẫu nhiên. Gộp lại; nếu quá 100 thì lấy ngẫu nhiên 100. Seed như mục 3.2.

  `lỗi` · `hỏng` · `bảo hành` · `đổi trả` · `mua về` · `đang dùng` · `đang xài` · `nóng máy` · `tụt pin` · `so với` · `trả góp` · `xách tay`

- Gắn `lo = CD`, `mau = chu_dich`. **Chỉ dùng để tìm thêm mã ở B4–B5, không tính vào phân bố.**

### 3.5 Phiếu mã hóa

| Cột | Ai điền | Nội dung |
|---|---|---|
| `stt` | Code | Số thứ tự trong phiếu |
| `lo` | Code | `1`–`5`, `K`, `D1`, `D2`, `CD` |
| `mau` | Code | `ngau_nhien` / `chu_dich` |
| `comment_id` | Code | |
| `may_video` | Code | Trường `model` (máy của video) |
| `loai_video` | Code | `video_type`, lấy dòng mới nhất của video trong `videos.jsonl` |
| `nhom_kenh` | Code | `5_kenh_lon` (5 kênh có nhiều bình luận nhất) / `kenh_khac` / `khong_ro` |
| `tuan` | Code | Tuần sau ra mắt (1–4), theo máy của video có cửa sổ chứa bình luận; trống nếu không xác định |
| `la_reply` | Code | `co` / `khong` |
| `chu_kenh` | Code | `co` nếu người viết là chủ kênh của video (`author_is_creator`) |
| `binh_luan` | Code | Chữ bình luận sau làm sạch nhẹ; tên dạng `@…` và `+Tên Họ` che thành `@[người dùng]` (mục 2) |
| `binh_luan_cha` | Code | Bình luận cha nếu là reply: làm sạch nhẹ, cắt ở 600 ký tự, che tên như `binh_luan` |
| `nguoi_ma_hoa` | Người mã hóa | Mã người mã hóa (`claude`, hoặc mã của trưởng nhóm) |
| `ma_tu_do` | Người mã hóa | Các mã, cách nhau bằng `;` ([guideline mục 2](huong-dan-kham-pha-nhan.md#2-ghi-mã-tự-do)) |
| `ghi_chu` | Người mã hóa | Ca khó, câu hỏi cho người kiểm |

Phiếu là CSV, mã hóa UTF-8 có BOM để Excel mở đúng tiếng Việt. Không có thông tin định danh người viết. Cột `nhom_kenh`, `tuan`, `chu_kenh` thêm theo kết quả B1.

**Phiếu lô K** (B6, thêm 25/11) gán theo bộ nhãn nên khác phiếu mã hóa mở: thay `nguoi_ma_hoa`, `ma_tu_do`, `ghi_chu` bằng `nguoi_gan`, năm cột nhãn `lien_quan`, `noi_ve_thai_do` (chiều 2 và 4), `muc_dich`, `da_dung`, `may_nhac`, rồi `chua_chac`, `ghi_chu`. Ô nhãn nhận tên đầy đủ hoặc chữ viết tắt ([guideline mục 5](huong-dan-kham-pha-nhan.md#5-gán-mù-lô-k-b6)). Phiếu của B là `phieu_lo_K.csv`; nhãn của A ở file riêng `nhan_lo_K_A.txt`, B không mở cho tới khi nộp.

**Không ghi đè phần người đã điền.** Phiếu đã có chữ ở cột của người điền (`nguoi_ma_hoa`, `ma_tu_do`, `ghi_chu`, hay cột thêm sau như `ghi_chu_kiem`) thì chạy lại lấy mẫu sẽ giữ nguyên phiếu. Code chỉ kiểm mẫu chạy lại có cùng `stt` và `comment_id` với phiếu không; khác thì dừng, không ghi file nào. Muốn lấy mẫu lại thật thì thêm `--ghi-de`, và phần đã điền sẽ mất.

## 4. HAC: tìm ứng viên khía cạnh trên cả bộ dữ liệu (B3)

### 4.1 Ý tưởng

HAC (*High Adjective Count*, Eirinaki và cộng sự, 2012) là thuật toán mà Wiegard và cộng sự (ECIS 2017) dùng trên bình luận YouTube. Ý tưởng: khía cạnh thường là **danh từ** được **tính từ đánh giá** mô tả. Trong mỗi câu, mỗi tính từ được gán cho danh từ gần nó nhất, rồi danh từ đó được cộng 1 điểm. Danh từ nhiều điểm là ứng viên khía cạnh.

### 4.2 Bản tiếng Việt không cần tách từ (hàm `trich_ung_vien`)

Bản gốc cần công cụ gán từ loại. Công cụ tiếng Việt học trên văn báo chí, dễ sai với teencode và chữ không dấu. Bản này thay bằng hai điều quan sát được:
- tiếng Việt đặt danh từ **trước** từ đánh giá ("pin trâu", "màn hình đẹp");
- một **danh sách từ đánh giá cố định** (`TU_DANH_GIA`) thay cho từ loại "tính từ".

Các bước:
1. Làm sạch nhẹ, chữ thường; tách câu ở `. ! ? … ;` và xuống dòng; tách âm tiết theo khoảng trắng và dấu câu.
2. Với mỗi lần gặp một từ đánh giá (khớp cụm 2 âm tiết trước, rồi mới khớp 1 âm tiết), nhìn ngược lại tối đa 4 âm tiết trong cùng câu:
   - bỏ qua từ đệm, từ chỉ mức độ, phủ định (`TU_BO_QUA`: quá, rất, hơi, khá, cũng, vẫn, thì, là, không…);
   - dừng nếu gặp một từ đánh giá khác.
3. Âm tiết nội dung gần nhất là **ứng viên 1 âm tiết**. Hai âm tiết nội dung liền nhau gần nhất là **ứng viên 2 âm tiết** ("màn hình"). Âm tiết nằm trong `TU_DUNG` (đại từ, loại từ, hư từ, từ đánh giá) hay chỉ gồm chữ số thì không thành ứng viên.
4. **Điểm HAC** của một ứng viên = tổng số lần nó được gắn với một từ đánh giá. Ghi thêm:
   - số bình luận khác nhau có ứng viên đó;
   - số từ đánh giá khác nhau đi kèm. Đây là ý của Eirinaki: khía cạnh thật được mô tả bằng nhiều tính từ khác nhau, còn từ nhiễu thường chỉ đi với một vài.

Danh sách `TU_DANH_GIA`, `TU_BO_QUA`, `TU_DUNG` nằm trong `src/labeling/hac.py`. Sửa danh sách là đổi kết quả: ghi lại trong báo cáo.

### 4.3 Đầu ra

- `data/kham-pha/hac_ung_vien.csv`: **300** ứng viên điểm cao nhất (gộp 1 và 2 âm tiết). Mỗi dòng có hạng, ứng viên, số âm tiết, điểm HAC, số bình luận, số từ đánh giá khác nhau, 5 từ đánh giá hay gặp nhất, 3 câu ví dụ (che tên như mục 3.5, cắt ở 120 ký tự). Thêm 3 cột trống cho người chấm: `la_khia_canh`, `nhom`, `ghi_chu` (từ 23/11 để trống, mục 4.4).
- Ba cột đó đã có chữ thì chạy lại HAC sẽ dừng, không ghi đè phần đã chấm. Thêm `--ghi-de` nếu thật sự muốn chạy lại.
- `data/kham-pha/hac_ung_vien.manifest.json`: tham số, số bình luận đã đọc, SHA-256 file nguồn.

### 4.4 Đối chiếu, không có người chấm

**Ngày 23/11 trưởng nhóm quyết không chấm danh sách HAC.** Lý do: danh sách nhiễu (mảnh từ, teencode, bỏ sót mẫu câu "pin con này trâu"), chấm 300 dòng tốn công mà thu được ít. Hệ quả: không có precision@N, không biết HAC đúng tới đâu.

HAC chỉ còn một việc: **bắt khía cạnh hiếm mà mẫu 600 bình luận sót** (mục 11). Sau khi có bộ nhãn (B5), A làm hai việc trên cả bộ dữ liệu:
1. **Đếm từ khóa:** với mỗi nhãn khía cạnh, đếm số bình luận chứa ít nhất một từ khóa của nhãn. Từ khóa lấy từ các mã đã gom vào nhãn đó. Đây là số bình luận **có nhắc từ khóa**, không phải tỷ lệ của nhãn: có nhắc chưa chắc là nói về khía cạnh đó.
2. **Rà 100 ứng viên HAC đầu:** ứng viên nào là khía cạnh mà bộ nhãn chưa có thì ghi lại, kèm điểm HAC và số bình luận.

Kết quả ghi rõ **"do AI làm, chưa có người kiểm"**. Chỉ dùng để đề xuất thêm khía cạnh ở B8 (mục 9), không dùng làm phân bố. Hàm `precision_at_n` giữ lại, phòng khi sau này có người chấm.

### 4.5 Giới hạn

- Bỏ sót khía cạnh không đi kèm từ đánh giá trong danh sách ("dùng 2 ngày mới sạc"), và khía cạnh được nói bằng động từ ("lag", "giật" không có danh từ đứng trước).
- Danh sách từ đánh giá do người soạn, nên kết quả nghiêng theo danh sách đó.
- Không có tách từ, nên ứng viên 1 âm tiết có thể là mảnh của từ 2 âm tiết ("hình" trong "màn hình"). A gom lại khi đối chiếu.
- Điểm HAC là số lần nhắc, **không phải tỷ lệ bình luận**. Không dùng điểm HAC làm phân bố.

## 5. Mã hóa mở (B4)

- A mã hóa lô 1–5 (500 bình luận) và mẫu có chủ đích (100). **Thí điểm:** mã lô 1 xong thì dừng để B xem cách mã, rồi mới làm tiếp lô 2–5.
- Mỗi bình luận có ít nhất một mã, dạng `đối tượng: hành vi` (vd `pin: khen`, `giá: hỏi`, `quà: xin`). Quy ước đầy đủ: [guideline mục 2](huong-dan-kham-pha-nhan.md#2-ghi-mã-tự-do).
- **Ghi đối tượng ở mức cụ thể nhất**, bằng từ của chính bình luận ("sạc", "chip", "nóng máy"). **Không** dùng tên của 9 khía cạnh đặt sẵn. Gom thành nhãn là việc của B5.
- Mã theo những gì được viết, không đoán ý người viết. Chưa chắc thì thêm `?` vào cuối mã.
- **Tách mã** (hàm `tach_ma`, dùng chung cho thống kê và mục 7d): chữ được chuẩn Unicode NFC, hành vi được viết thường. Nhờ vậy `Khen`, `khen`, và `khen` gõ bằng bảng mã Unicode tổ hợp đều là một hành vi.
- **Thống kê mã hóa mở** (hàm `thong_ke`, ghi ra `bao-cao-ma-hoa-mo.md`):
  - theo lô: số mã, số mã trung bình mỗi bình luận, mã `?`, bình luận không hiểu được;
  - hành vi và đối tượng hay gặp; đối tượng mới ở từng lô;
  - mẫu có chủ đích tính riêng.

  Đây chỉ là **đếm mã tự do, không phải phân bố nhãn**. Vì vậy chỉ ghi số đếm, không ghi phần trăm. Phân bố chỉ tính ở B7, theo bộ nhãn đã kiểm (mục 8). Đối tượng mới theo lô chỉ là dấu hiệu sớm, chưa phải bão hòa: bão hòa đếm theo nhãn sau khi gom (mục 6).

## 6. Gom mã thành bộ nhãn và bão hòa (B5)

- A gom các mã cùng nghĩa thành **nhãn**, rồi xếp nhãn vào **chiều**. Một chiều là một câu hỏi về bình luận. Ghi rõ mỗi chiều cho **một** nhãn hay **nhiều** nhãn mỗi bình luận.
- **Mỗi nhãn ghi:** tên ngắn, định nghĩa 1–2 câu, 2 ví dụ thuộc, 1 ví dụ dễ nhầm nhưng không thuộc, các mã đã gom vào, số lần gặp, lô xuất hiện lần đầu.
- Mỗi chiều có nhãn "khác", và "không xác định" nếu cần.
- Bộ nhãn viết ở `docs/3-gan-nhan/dac-ta-bo-nhan.md`. B duyệt.
- **Đếm bằng code, không gom tay.** Ánh xạ mã → nhãn (luật từ khóa trên đối tượng, bảng hành vi → mục đích) nằm trong `src/labeling/label_set.py`. Code đếm số bình luận có mỗi nhãn, lô gặp lần đầu, bão hòa, và ghi `bao-cao-bo-nhan.md`. Số đó là bằng chứng nhãn có trong dữ liệu, không phải phân bố (mục 8).
- **Kiểm độ phủ trên phiếu B:** áp cùng ánh xạ cho mã của B. Mã nào không xếp được vào nhãn nào thì liệt kê. Không thêm từ của B vào ánh xạ, để con số này còn là phép thử độc lập.
- **Bão hòa:** đếm **số nhãn mới** của từng lô 1–5, theo thứ tự lô.
  - Lô 5 không tạo nhãn mới nào thì đủ.
  - Còn nhãn mới thì mã hóa tiếp lô D1, rồi D2. Lô dự trữ đã dùng để mã hóa mở thì tính vào mẫu phân bố.
  - Hết D2 mà vẫn còn nhãn mới thì báo trưởng nhóm, lấy thêm mẫu.

## 7. Kiểm (B6)

**(a) Bỏ từ 23/11:** trưởng nhóm không chấm danh sách HAC (mục 4.4). Người kiểm AI chỉ còn (b) và (c), nên (b) và (c) là bắt buộc.

**(b) Lô K: A và B gán mù.** Mỗi người gán lô K theo bộ nhãn, cho từng chiều, không xem của nhau. Với từng chiều, báo cả ba: tỷ lệ đồng ý thô, Cohen's kappa, phân bố nhãn của mỗi người.

```text
tỷ lệ đồng ý thô  p_o = (số bình luận hai người gán giống nhau) / (số bình luận)
đồng ý do may rủi p_e = Σ_k  p_A(k) · p_B(k)
kappa             κ   = (p_o − p_e) / (1 − p_e)
```

`p_A(k)`, `p_B(k)` là tỷ lệ bình luận mà A, B gán nhãn `k`. Kappa trừ đi phần đồng ý do may rủi: hai người cùng gán "không phải spam" cho 95% bình luận thì đồng ý thô rất cao dù chưa chắc hiểu giống nhau.
- Với chiều nhiều nhãn, tính riêng cho từng nhãn như một câu có/không.
- Với nhãn hiếm, kappa dao động mạnh, nên báo thêm **tỷ lệ đồng ý dương**. Gọi `a` là số bình luận cả hai gán nhãn đó, `b` và `c` là số bình luận chỉ một người gán:

  ```text
  đồng ý dương = 2a / (2a + b + c)
  ```

- **Ngưỡng:** κ ≥ 0,6 thì dùng chiều đó.
- κ < 0,6 thì sửa định nghĩa dựa trên các ca lệch, rồi kiểm lại trên 50 bình luận của lô D2 chưa ai đọc. Hai lần vẫn dưới ngưỡng thì B8 quyết bỏ hay gộp chiều đó.
- **Lô D2 (thêm 26/11):** sau B8, sửa định nghĩa `dua`, `khong_xac_dinh` (chiều 1) và thêm trường `ten_may`. Lấy **50 bình luận đầu** của D2 (vị trí 701–750 của mẫu ngẫu nhiên). Phiếu như lô K, thêm cột `ten_may` sau `may_nhac`. A gán trước, ghi `nhan_lo_D2_A.txt` (ô thứ 9 là tên máy); B gán mù `phieu_lo_D2.csv`, lưu `phieu_lo_D2_B.xlsx` hay `.csv`. Code so như lô K (`lot_k --lo D2`), thêm tỷ lệ khớp đúng tập tên máy trên các bình luận cả hai gán `goi_ten_may`. **Giới hạn:** 50 bình luận chỉ có vài bình luận `dua`, `khong_xac_dinh`, nên kappa riêng hai nhãn này dao động rất mạnh; báo kèm số đếm và đồng ý dương, trưởng nhóm đọc cả ca lệch trước khi kết luận.
- Ca lệch ở lô K do B quyết, ghi lý do.

**Cách so lô K (thêm 26/11):**
- Phiếu B là `phieu_lo_K_B.xlsx` (hay `.csv`); ô nhãn gõ tắt hay gõ đủ đều được. Dòng sai luật nhãn (mục 8) vẫn được so như B đã gõ, và được liệt kê trong báo cáo.
- Chiều 1, 5, 6: đồng ý thô và kappa trên 6, 2, 3 lựa chọn; kèm kappa, đồng ý dương từng nhãn như câu có/không; chiều 1 thêm ma trận A × B.
- Chiều 2: chỉ trên các bình luận **cả hai** gán `dien_thoai` (lệch chiều 1 đã tính ở chiều 1). Chiều 3: trên mọi bình luận.
- Chiều 4: chỉ trên các cặp (bình luận, nhãn chiều 2) mà cả hai cùng gán; từng thái độ là một câu có/không.
- Chiều 2, 3, 4 báo thêm **tỷ lệ trùng cả tập nhãn** và **kappa gộp** (mọi cặp bình luận × nhãn coi là một câu có/không). **Chiều nhiều nhãn xét ngưỡng 0,6 bằng kappa gộp** (trưởng nhóm quyết 26/11).
- Đầu ra: `bao-cao-lo-k.md` (chỉ số, tên nhãn, `stt`), `lech_lo_K.csv` (ngoài git: mọi bình luận lệch, nhãn hai bên).
- **Phân xử:** code ghi `phan_xu_lo_K.md` (ngoài git, có chữ bình luận). Mỗi ca lệch một mục, chỉ hỏi các chiều lệch; B ghi `A`, `B`, hay nhãn khác (gõ tắt được), và lý do. Code đọc lại, kiểm luật nhãn, ghi `nhan_lo_K_phan_xu.csv`; chiều hai bên đã khớp giữ nguyên. Ca chưa điền thì báo, không đoán. Kappa vẫn tính trên nhãn trước phân xử.

**(c) B kiểm nhãn của A trên lô 1–5** (sau khi A gán lại theo bộ nhãn ở B7):
- xem ngẫu nhiên ít nhất 100 bình luận, và **mọi** bình luận A đánh dấu `?`;
- sửa thì ghi lại nhãn cũ, nhãn mới, lý do.

Báo cáo **tỷ lệ nhãn phải sửa**: tỷ lệ cao nghĩa là nhãn của A không tin được, phải kiểm toàn bộ.

**Phiếu và cách kiểm (thêm 25/11):**
- Code chọn 100 bình luận ngẫu nhiên của lô 1–5 (seed `20261122`) và mọi bình luận có `?`, ghi `phieu_kiem_b7.csv`. Cột `vi_sao_chon` ghi `ngau_nhien`, `chua_chac` hay cả hai.
- B ghi `x` vào `da_kiem` cho **mọi** dòng đã xem, kể cả dòng đồng ý. Muốn sửa chiều nào thì ghi nhãn đúng vào cột `sua_…` của chiều đó, lý do vào `ghi_chu_kiem`. Ô `sua_…` trống nghĩa là giữ nhãn của A.
- Nhãn cuối = nhãn B sửa, không có thì nhãn A. Sửa chiều 1 thành nhãn khác `dien_thoai` thì nhãn chiều 2 và 4 tự bỏ.
- **Tỷ lệ phải sửa** tính theo bình luận, **chỉ trên phần ngẫu nhiên**, kèm khoảng Wilson. Phần `?` báo riêng, vì đó là các ca khó được chọn có chủ ý.
- **Đợt 2 (thêm 26/11):** đợt 1 có 17% phải sửa (Wilson [10,9; 25,5]), lỗi có quy luật. Trưởng nhóm quyết kiểm **toàn bộ** lô 1–5: code xuất mọi bình luận chưa kiểm vào `phieu_kiem_b7_phan_2.csv`, cách điền như đợt 1. Đã mở đợt 2 thì báo cáo chỉ có tỷ lệ khi cả hai đợt kiểm xong. Tỷ lệ phải sửa vẫn chỉ tính trên phần ngẫu nhiên của đợt 1.
- Phần ngẫu nhiên có khoảng trùng với phần `?`; một bình luận thuộc cả hai thì tính ở cả hai.

**(d) Đồng thuận mã hóa mở** (thêm 23/11 theo yêu cầu trưởng nhóm, làm trước B5):
- Code xuất phiếu trống `phieu_ma_hoa_mo_B.csv`: cùng các dòng với phiếu của A, nhưng **không có mã của A**. B tự mã một phần theo guideline mục 2, không xem mã của A cho tới khi nộp.
- **Chỉ tính kappa trên hành vi**, vì hành vi chọn trong bảng hành vi cố định. Với mỗi hành vi, mỗi bình luận là một câu có/không: "bình luận có mã nào với hành vi này không". Báo đồng ý thô, kappa, đồng ý dương và số bình luận mỗi người gán. Chỉ tính trên các bình luận B đã mã; hành vi không ai dùng thì bỏ. Hành vi so không phân biệt chữ hoa (mục 5).
- **Đối tượng là chữ tự do, nên không tính kappa.** Code xuất danh sách bình luận lệch hành vi, kèm mã của hai bên, để bàn. Chữ bình luận trong danh sách lấy từ phiếu A, vì phiếu B đã qua tay người và Excel có thể làm hỏng ô (ô bắt đầu bằng `+` thành `#NAME?`).
- Phần này **không thay cho (b)**. (d) đo hai người mã tự do giống nhau tới đâu; (b) đo bộ nhãn trên lô chưa ai đọc.
- **Hạn chế:** B đã mở phiếu có mã của A trước đó. Bình luận nào B đã xem mã của A thì không còn mù, nên báo cáo ghi rõ B mã những lô nào.

## 8. Tính phân bố (B7)

**Nhãn B7 của A (thêm 25/11).** A đọc lại chữ bình luận và gán cả 6 chiều theo [đặc tả bộ nhãn](dac-ta-bo-nhan.md), không nhìn mã cũ của mình hay mã của B. Nhãn viết tắt nằm ở `nhan_b7_A.txt`, mỗi dòng một bình luận; code kiểm tính hợp lệ rồi ghi `phieu_b7.csv` (mỗi chiều một cột, chiều 2 và 4 chung một cột `nhãn chiều 2:thái độ`). Luật kiểm: đủ 500 bình luận, không trùng; nhãn nào cũng có trong bộ nhãn; `dien_thoai` thì có ít nhất một nhãn chiều 2, nhãn khác thì không có.

**Khóa tỷ lệ.** Chưa kiểm xong phiếu ở mục 7(c) thì báo cáo **chỉ ghi số đếm**, không ghi phần trăm hay khoảng tin cậy. Kiểm xong, chạy lại cùng lệnh thì có tỷ lệ. Lô K chưa phân xử thì báo cáo ghi n = 500 và nói rõ còn thiếu lô K.

**Đối chiếu không cần chờ kiểm:** kappa và đồng ý dương giữa nhãn B7 của A và (i) nhãn suy từ mã tự do cũ của A, (ii) nhãn suy từ mã tự do của B, trên chiều 1, 2, 3. Cả hai suy bằng luật từ khóa của `label_set.py`, nên lệch có thể do luật. Phiếu B mã trước khi sửa bảng hành vi. Vì vậy đây chỉ là chỉ báo, **không thay** cho lô K mù hay mục 7(c).

**Mẫu phân bố:** lô 1–5, các lô dự trữ đã dùng để mã hóa mở, và lô K (n = 600 nếu không dùng dự trữ). Không gồm mẫu có chủ đích. Mỗi bình luận dùng nhãn sau khi B kiểm (lô K dùng nhãn đã phân xử).

**Tỷ lệ của một nhãn:**

```text
p̂ = x / n
```

`x` là số bình luận có nhãn. Chiều nhiều nhãn thì tổng các tỷ lệ có thể vượt 100%. Nhãn chỉ áp dụng cho một phần mẫu (vd nhãn chiều 2 chỉ gán cho bình luận có nhãn `dien_thoai` ở chiều 1) thì báo thêm tỷ lệ **trong phần đó**, và ghi rõ mẫu số (phần áp dụng của từng chiều: bảng ở mục 9).

**Khoảng tin cậy 95%: báo cả hai cách.**

1. **Wilson** (coi các bình luận độc lập):

   ```text
   tâm         = (x + z²/2) / (n + z²)
   nửa độ rộng = z / (n + z²) · √( x·(n − x)/n + z²/4 )
   khoảng      = tâm ± nửa độ rộng
   ```

   Wilson tốt hơn công thức quen thuộc `p̂ ± z·√(p̂(1−p̂)/n)` khi `p̂` nhỏ: không bao giờ ra số âm, và không cho khoảng rỗng khi `x = 0`.

2. **Bootstrap theo video (cách chính).** Bình luận cùng video giống nhau hơn bình luận ngẫu nhiên. Ví dụ dưới một video minigame thì gần như mọi bình luận đều là xin quà. Video lớn nhất chiếm 1,22% bình luận, nên trung bình có khoảng 7 bình luận của nó trong mẫu 600. Cách làm:
   - gọi `V` là số video khác nhau có trong mẫu;
   - lặp `B = 2.000` lần: chọn ngẫu nhiên **có hoàn lại** `V` video trong số đó, lấy mọi bình luận trong mẫu của các video được chọn, tính tỷ lệ;
   - khoảng tin cậy là phân vị 2,5% và 97,5% của 2.000 tỷ lệ đó. Seed `20261122`.

**Hệ số thiết kế** cho biết việc bình luận dồn theo video làm khoảng rộng ra bao nhiêu:

```text
deff ≈ (nửa độ rộng bootstrap / nửa độ rộng Wilson)²
cỡ mẫu hiệu dụng = n / deff
```

Lý thuyết: `deff = 1 + (m̄ − 1)·ρ`, với `m̄` là số bình luận trung bình mỗi video trong mẫu và `ρ` là mức giống nhau của bình luận cùng video. `deff` gần 1 thì hai khoảng như nhau. `deff` lớn (nhãn dồn vào vài video, như xin quà) thì dùng khoảng bootstrap và ghi `deff`. Mẫu 600 thật thuộc 507 video, nhiều nhất 5 bình luận một video, nên `m̄ ≈ 1,18`: với phần lớn nhãn, `deff` dự kiến gần 1.

**Nhãn không xuất hiện lần nào** trong n bình luận: báo cận trên 95% theo quy tắc ba, `≈ 3/n` (0,5% với n = 600).

**Tách theo nhóm:** gốc hay reply; 5 kênh lớn hay kênh khác; tuần 1–2 hay 3–4; loại video; có phải của chủ kênh. Nhóm dưới 30 bình luận thì chỉ ghi số đếm, không ghi phần trăm.

## 9. So ba nguồn và chốt bộ nhãn (B8)

Bộ nhãn đặt sẵn trên `main` (guideline v1 nháp, 20/11). **Chỉ dùng ở bước này:**

| Chiều | Nhãn đặt sẵn |
|---|---|
| Mức liên quan | Trực tiếp (nói về điện thoại) / ngữ cảnh (video, người review, quà tặng) / không liên quan |
| Spam (theo nội dung) | Không / quảng cáo, mời liên hệ / lừa đảo, cờ bạc / khác |
| Khía cạnh | Pin & sạc · Màn hình · Hiệu năng (gồm nóng máy) · Camera · Thiết kế & độ bền · Phần mềm · Phần cứng khác · Giá · Bảo hành & hậu mãi |
| Cảm xúc theo khía cạnh | Khen / chê / trung tính |
| Máy được nhắc | Gọi tên máy / chỉ suy được từ video / không rõ |
| Đã dùng máy, loại lỗi | Đã dùng / chưa / không rõ; 9 loại lỗi |

**So:**
- khía cạnh: các khía cạnh của bộ nhãn, khía cạnh mà A đối chiếu HAC thấy bộ nhãn chưa có (mục 4.4, do AI làm), và 9 khía cạnh đặt sẵn. Đánh dấu từng khía cạnh có ở nguồn nào;
- nhãn ngoài khía cạnh và các chiều khác: bộ nhãn mã hóa mở so với bộ đặt sẵn.

**Nhãn đặt sẵn** là nhãn có trong bảng trên. **Nhãn mới** là nhãn rút từ dữ liệu (B5) mà bảng trên không có.

**Tỷ lệ dùng trong luật** (trưởng nhóm duyệt 25/11) là số bình luận có nhãn đó **trong mẫu phân bố** (mục 8), chia cho số bình luận thuộc **phần áp dụng**, tức những bình luận mà nhãn đó có thể được gán. Chiều 4 thì đếm cặp thay cho bình luận. Không chia cho cả bộ dữ liệu, không tính mẫu có chủ đích.

| Nhãn thuộc chiều | Phần áp dụng (mẫu số) |
|---|---|
| 1, 3, 5, 6 | Mọi bình luận của mẫu phân bố |
| 2 | Những bình luận có nhãn `dien_thoai` ở chiều 1 |
| 4 | Các cặp (bình luận, nhãn chiều 2): bình luận nói về camera và pin là 2 cặp. Một cặp có thể có nhiều thái độ, nên tổng có thể vượt 100% |

So với ngưỡng bằng **tỷ lệ đo được**. Khoảng tin cậy 95% (bootstrap theo video, mục 8) mà trùm lên ngưỡng thì vẫn quyết theo tỷ lệ đo được, nhưng ghi "sát ngưỡng" để trưởng nhóm xem lại.

**Luật quyết** (áp cho từng nhãn, ghi lý do và số liệu cho từng quyết định):
1. **Giữ** nhãn đặt sẵn khi nó có trong dữ liệu **và** phục vụ ít nhất một câu hỏi Q1–Q6 (kế hoạch mục 6) hoặc việc đánh giá chất lượng dữ liệu.
2. **Thêm** nhãn mới khi nó chiếm **từ 3%** phần áp dụng trở lên, **và** phục vụ một câu hỏi hoặc việc đánh giá chất lượng dữ liệu. Nhãn mới **dưới 3%** thì gộp vào nhãn gần nhất, trừ khi có câu hỏi cần riêng nó (vd `bao_loi` cho Q5). Khía cạnh mà chỉ HAC tìm ra (hiếm trong mẫu) cũng theo luật này.
3. **Gộp** vào nhãn gần nhất hoặc "khác": nhãn chiếm **dưới 1%** phần áp dụng, không phục vụ câu hỏi nào **và** không giúp đánh giá chất lượng dữ liệu. Nhãn đặt sẵn hiếm nhưng giúp đánh giá chất lượng dữ liệu (vd `quang_cao`) thì giữ theo luật 1.
4. **Bỏ** hoặc gộp: nhãn hay chiều có kappa dưới 0,6 sau hai lần sửa (mục 7).
5. Nhãn đặt sẵn **không xuất hiện** lần nào trong mẫu: giữ chỉ khi có câu hỏi bắt buộc cần nó. Khi đó ghi cận trên của tỷ lệ, và ghi rằng khó có đủ dữ liệu cho câu hỏi đó.

## 10. Code, đầu ra và file

| Luật | Code | Test (`tests/test_labeling.py`) |
|---|---|---|
| Làm sạch nhẹ (3.1), che tên `@…` (2) | `src/labeling/light_clean.py`: `lam_sach_nhe`, `an_nhac_ten` | `LamSachNhe` |
| Lấy mẫu, chia lô, phiếu, không ghi đè (3.2, 3.4, 3.5) | `src/labeling/sample.py`: `chia_lo`, `giu_phieu_cu`, `chay` | `LayMau` |
| HAC (4) | `src/labeling/hac.py`: `trich_ung_vien`, `chay` | `Hac` |
| Thống kê mã hóa mở (5) | `src/labeling/code_stats.py`: `tach_ma`, `thong_ke`, `chay` | `ThongKeMa` |
| Đồng thuận mã hóa mở (7d) | `src/labeling/agreement.py`: `xuat_phieu_trong`, `dong_thuan_hanh_vi`, `so_sanh` | `DongThuanMa` |
| Bộ nhãn: ánh xạ mã → nhãn, đếm, bão hòa (6; định nghĩa nhãn ở `dac-ta-bo-nhan.md`) | `src/labeling/label_set.py`: `KHIA_CANH`, `NGOAI_KHIA_CANH`, `nhom_doi_tuong`, `gan_nhan`, `thong_ke_nhan`, `do_phu`, `chay` | `BoNhan` |
| Nhãn B7, phiếu kiểm, áp phần sửa (7c, 8) | `src/labeling/b7_labels.py`: `doc_nhan_a`, `kiem_tra`, `chon_kiem`, `nhan_cuoi` | `NhanB7` |
| Đối chiếu HAC, so ba nguồn, đề xuất B8 (4.4, 9) | `src/labeling/b8.py`: `tu_khoa`, `dem_tu_khoa`, `ty_le`, `luat_noi`, `DE_XUAT` | `B8` |
| So lô K A và B, phân xử (7b) | `src/labeling/lot_k.py`: `doc_xlsx`, `nhan_b`, `so_sanh`, `viet_bao_cao`, `viet_phan_xu`, `doc_phan_xu` | `LoK` |
| EDA nhãn B7, đối chiếu, báo cáo (8) | `src/labeling/distribution.py`: `khoang`, `thong_ke`, `doi_chieu`, `viet_bao_cao` | `PhanBo` |
| Công thức (3.3, 4.4, 7, 8) | `src/labeling/stats.py`: `xac_suat_gap`, `co_mau_can`, `wilson`, `quy_tac_ba`, `kappa`, `dong_y_duong`, `bootstrap_theo_cum`, `he_so_thiet_ke`, `precision_at_n` | `CongThuc` |

Lệnh, chạy từ gốc repo:

```powershell
.\.venv\Scripts\python.exe -m src.labeling.sample           # lấy mẫu, xuất phiếu lô 1–5 và mẫu có chủ đích (phiếu đã điền thì giữ, mục 3.5)
.\.venv\Scripts\python.exe -m src.labeling.sample --xuat-lo K   # chỉ chạy ở B6: xuất phiếu trống lô K
.\.venv\Scripts\python.exe -m src.labeling.sample --xuat-lo D2  # sau B8: phiếu 50 bình luận đầu lô D2, có cột ten_may
.\.venv\Scripts\python.exe -m src.labeling.hac              # HAC trên cả bộ dữ liệu
.\.venv\Scripts\python.exe -m src.labeling.code_stats       # thống kê mã hóa mở → bao-cao-ma-hoa-mo.md
.\.venv\Scripts\python.exe -m src.labeling.agreement xuat   # phiếu trống cho người kiểm B (7d)
.\.venv\Scripts\python.exe -m src.labeling.agreement so-sanh  # kappa theo hành vi, danh sách lệch (7d)
.\.venv\Scripts\python.exe -m src.labeling.label_set        # đếm bộ nhãn, bão hòa → bao-cao-bo-nhan.md (6)
.\.venv\Scripts\python.exe -m src.labeling.b7_labels nap           # nhan_b7_A.txt → phieu_b7.csv (8)
.\.venv\Scripts\python.exe -m src.labeling.b7_labels phieu-kiem    # phiếu cho B kiểm (7c)
.\.venv\Scripts\python.exe -m src.labeling.distribution            # EDA → bao-cao-phan-bo-nhan.md (8)
.\.venv\Scripts\python.exe -m src.labeling.b8                 # B8: so ba nguồn, đề xuất → bao-cao-kham-pha-nhan.md (4.4, 9)
.\.venv\Scripts\python.exe -m src.labeling.lot_k              # so lô K A, B → bao-cao-lo-k.md, lech_lo_K.csv (7b)
.\.venv\Scripts\python.exe -m src.labeling.lot_k phan-xu      # phiếu phân xử phan_xu_lo_K.md (không ghi đè phần đã điền)
.\.venv\Scripts\python.exe -m src.labeling.lot_k nhap         # đọc phân xử → nhan_lo_K_phan_xu.csv
.\.venv\Scripts\python.exe -m src.labeling.lot_k --lo D2      # so lô D2 → bao-cao-lo-d2.md (thêm phan-xu, nhap như lô K)
.\.venv\Scripts\python.exe -m unittest tests.test_labeling  # test
```

| File (trong `data/kham-pha/`, ngoài git) | Nội dung |
|---|---|
| `mau.csv`, `mau.manifest.json` | Mọi bình luận được chọn: lô, các trường mô tả (không có chữ bình luận); seed, SHA-256 nguồn, số đếm |
| `phieu_ma_hoa_mo.csv` | Phiếu lô 1–5 và mẫu có chủ đích, có chữ bình luận |
| `phieu_lo_K.csv` | Phiếu lô K của B, chỉ xuất ở B6 |
| `nhan_lo_K_A.txt` | Nhãn lô K của A, viết tắt như `nhan_b7_A.txt`. **B không mở trước khi nộp** |
| `phieu_lo_K_B.xlsx` | Phiếu lô K B đã gán |
| `phieu_lo_D2.csv`, `nhan_lo_D2_A.txt`, `phieu_lo_D2_B.xlsx` | Lô D2 (50 bình luận): phiếu của B, nhãn của A (B không mở trước khi nộp), phiếu B đã gán (7b) |
| `lech_lo_K.csv` | Các bình luận lô K lệch (7b) |
| `phan_xu_lo_K.md` | Phiếu B phân xử ca lệch lô K, có chữ bình luận (7b) |
| `nhan_lo_K_phan_xu.csv` | Nhãn lô K sau phân xử, vào mẫu phân bố (7b, 8) |
| `phieu_ma_hoa_mo_B.csv` | Phiếu trống để B tự mã hóa mở (7d), không có mã của A |
| `nhan_b7_A.txt`, `phieu_b7.csv` | Nhãn B7 của A: bản viết tắt và bản đầy đủ kèm chữ bình luận (8) |
| `phieu_kiem_b7.csv`, `phieu_kiem_b7_da_dien.csv`, `phieu_kiem_b7_phan_2.csv` (+ `_da_dien`) | Phiếu B kiểm nhãn B7 (7c): bản code xuất và bản B đã điền; có bản đã điền thì code dùng bản đó |
| `dong_thuan_ma_hoa_mo.csv`, `lech_ma_hoa_mo.csv` | Kappa theo hành vi; các bình luận lệch, kèm chữ bình luận và mã hai bên (7d) |
| `hac_ung_vien.csv`, `.manifest.json` | 300 ứng viên khía cạnh; tham số |
| `docs/3-gan-nhan/bao-cao-ma-hoa-mo.md` (trong git) | Thống kê mã hóa mở, do `code_stats` sinh; chỉ có số đếm và chữ của mã, không có chữ bình luận |
| `docs/3-gan-nhan/dac-ta-bo-nhan.md` (trong git) | Bộ nhãn, tạo ở B5 |
| `docs/3-gan-nhan/bao-cao-bo-nhan.md` (trong git) | Số bình luận mỗi nhãn, lô gặp lần đầu, bão hòa, độ phủ trên phiếu B; do `label_set` sinh, chỉ có số và tên nhãn |
| `docs/3-gan-nhan/bao-cao-lo-d2.md` (trong git) | So lô D2 A và B, do `lot_k --lo D2` sinh |
| `docs/3-gan-nhan/bao-cao-lo-k.md` (trong git) | So lô K A và B (7b), do `lot_k` sinh; chỉ có số, tên nhãn, `stt` |
| `docs/3-gan-nhan/bao-cao-phan-bo-nhan.md` (trong git) | EDA nhãn B7 (8), do `distribution` sinh; chỉ có số và tên nhãn |
| `docs/3-gan-nhan/bao-cao-kham-pha-nhan.md` (trong git) | HAC, bão hòa, đồng thuận, phân bố, so sánh, quyết định B8 |

`data/` nằm ngoài git. Phiếu có nội dung bình luận thật nên chỉ chia sẻ trong nhóm.

## 11. Giới hạn đã biết

- 600 bình luận chỉ đủ để thấy những loại chiếm từ khoảng 0,5% trở lên. Nhãn hiếm hơn có khoảng tin cậy rất rộng. HAC đối chiếu bù một phần cho khía cạnh, nhưng do AI làm, không ai chấm.
- Từ 23/11 trưởng nhóm không chấm HAC: phần người kiểm AI chỉ còn lô K mù và kiểm nhãn (mục 7).
- Mẫu lấy trên cả v4 (139 máy, 2014–2026), nên phân bố mô tả cả bộ dữ liệu, không riêng bộ 4 máy hay một giai đoạn nào.
- Người mã hóa A là AI và đã biết bộ nhãn đặt sẵn; người kiểm B xem nhãn của A khi kiểm. Hai rủi ro này đo bằng kappa trên lô K mù và tỷ lệ nhãn phải sửa (mục 7), không loại hết được.
- Mẫu có chủ đích không đại diện cho dữ liệu, chỉ dùng để tìm nhãn.

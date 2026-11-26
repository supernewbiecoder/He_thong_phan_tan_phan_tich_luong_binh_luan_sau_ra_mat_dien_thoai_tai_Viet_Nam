# Hướng dẫn gán mù lô K (B6)

> Mục đích: Cách gán 100 bình luận lô K theo bộ nhãn, từng bước: mở phiếu, gán từng cột, ví dụ, bài tập, kiểm lại và nộp; cho trưởng nhóm (người kiểm B); cập nhật lần cuối: 2026-11-25.

**Cách dùng file này:**

1. Đọc mục 1, mở phiếu theo mục 2.
2. Đọc mục 4 và 5, làm bài tập ở mục 8.
3. Khi gán, mở mục 3 bên cạnh Excel. Vướng thì tra mục 5, 6, 7.
4. Xong thì kiểm và nộp theo mục 9.

**Phạm vi:**

- **Định nghĩa nhãn nằm ở [đặc tả bộ nhãn](dac-ta-bo-nhan.md).** File này chỉ nói cách làm, kèm bảng tóm tắt để tra nhanh. Hai file lệch nhau thì theo đặc tả, rồi báo lại.
- **File này không thêm luật.** A (Claude) đã gán xong lô K theo đặc tả trước khi có file này. Thêm luật cho riêng B thì hai người gán theo hai bộ luật, và kappa không còn đo được bộ nhãn. Chỗ đặc tả chưa nói rõ thì file này cũng không quyết (mục 7).
- **Ví dụ** lấy từ đặc tả, guideline, hoặc tự soạn rồi suy thẳng từ đặc tả. Không ví dụ nào lấy từ lô K.
- **Hạn chế:** file do Claude viết, mà Claude cũng là A. Ví dụ tự soạn có thể kéo B về cách hiểu của A. Khi viết báo cáo B6 nên ghi điều này.

## 1. Việc cần làm và quy tắc mù

**Việc:** đọc 100 bình luận trong `data/kham-pha/phieu_lo_K.csv` (`stt` 501–600). Với mỗi bình luận, chọn nhãn cho sáu chiều. Sáu chiều nằm trong **năm cột nhãn**, vì chiều 2 và chiều 4 chung một cột.

**Để làm gì:** A và B gán độc lập cùng 100 bình luận, rồi code so hai bên. Hai bên giống nhau nhiều thì bộ nhãn rõ, và nhãn của AI đáng tin hơn ([đặc tả mục 7b](dac-ta-kham-pha-nhan.md#7-kiểm-b6)). **Gán khác A không có nghĩa là sai.** Chỗ khác nhau chính là thứ cần tìm, nên cứ gán theo cách mình hiểu.

**Cho tới khi nộp:**

1. Không mở `data/kham-pha/nhan_lo_K_A.txt` (nhãn của A). Lỡ thấy thì ghi lại đã thấy những `stt` nào: các dòng đó không còn mù.
2. Không hỏi ai, kể cả Claude, về một bình luận cụ thể của lô K. Vướng thì đọc đặc tả. Vẫn vướng thì ghi vào `ghi_chu`, nộp xong mới bàn.
3. Nên gán lô K **trước** khi mở `phieu_b7.csv` và `phieu_kiem_b7.csv`. Hai file đó có nhãn của A ở lô 1–5, xem trước thì dễ gán theo.
4. Không dán chữ bình luận vào AI khác, công cụ dịch hay trang web nào.
5. Không chép tên người, số điện thoại, link vào `ghi_chu`.

## 2. Mở phiếu

**Không double-click file CSV.** Excel sẽ hiểu ô bắt đầu bằng `=`, `+`, `-` là công thức và làm hỏng chữ bình luận.

### 2.1 Các bước (Excel tiếng Anh)

1. Mở Excel trống. **Data → From Text/CSV**, chọn `data/kham-pha/phieu_lo_K.csv`.
2. Trong hộp xem trước:
   - *File Origin*: `65001: Unicode (UTF-8)`;
   - *Data Type Detection*: `Do not detect data types`;
   - bấm **Transform Data** (chưa bấm *Load*).
3. Trong Power Query: **Home → Use First Row as Headers**. Tên cột phải thành `stt`, `lo`, `mau`…
4. Khung *Applied Steps* bên phải có bước **Changed Type** thì bấm `X` để xóa. Giữ bước *Promoted Headers*.
5. **Home → Close & Load**. Khung bên phải phải ghi **100 rows loaded**. Dòng 1 là tên cột, cột A chạy từ 501 tới 600.
6. Bấm vào bảng → **Table Design → Convert to Range → OK**. Bước này cắt phiếu khỏi file gốc: lỡ bấm *Refresh* cũng không mất nhãn đã gõ.
7. Lưu ngay: **File → Save As**, kiểu *Excel Workbook (.xlsx)*, thư mục `data/kham-pha/`, tên `phieu_lo_K_dang_lam.xlsx`. Làm trên file này và lưu thường xuyên.

| Gặp | Làm |
|---|---|
| Đã bấm *Load*, cột tên là `Column1`, `Column2`… | Double-click `phieu_lo_K` ở khung *Queries & Connections*, làm tiếp từ bước 3. Làm **trước khi gõ nhãn** |
| Số dòng khác 100 | Có bình luận xuống dòng bị tách thành hai dòng. Trong Power Query, bấm bánh răng ở bước *Source*, *Line breaks* chọn *Ignore quoted line breaks* |
| Chữ tiếng Việt bị lỗi | *File Origin* chưa phải `65001: Unicode (UTF-8)`. Sửa cũng ở bánh răng của bước *Source* |

### 2.2 Chỉnh cho dễ làm

Các cột của phiếu: A `stt` · B–J thông tin (máy của video, loại video, kênh…) · K `binh_luan` · L `binh_luan_cha` · M `nguoi_gan` · **N `lien_quan` · O `noi_ve_thai_do` · P `muc_dich` · Q `da_dung` · R `may_nhac`** · S `chua_chac` · T `ghi_chu`.

- **Ẩn cột B–J:** bôi đen → chuột phải → *Hide*. Ẩn `may_video` để khỏi suy tên máy từ video. Ẩn thôi, **không xóa**.
- **Cột K, L:** chọn *Wrap Text* và kéo rộng.
- **Giữ dòng tên cột:** *View → Freeze Panes → Freeze Top Row*.
- **Cột M:** chọn M2:M101, gõ `B`, bấm **Ctrl+Enter**. Cả 100 dòng được điền.
- **Tắt tự điền:** *File → Options → Advanced*, bỏ chọn *Enable AutoComplete for cell values*.
- **Tắt bộ gõ tiếng Việt** khi gõ cột N–S. Bật lại khi viết `ghi_chu`.
- **Gõ nhanh:** bắt đầu ở cột N, gõ xong một ô thì bấm **Tab**. Hết dòng bấm **Enter**, con trỏ về cột N của dòng sau.

### 2.3 Tránh làm hỏng phiếu

| Đừng | Vì sao |
|---|---|
| Bấm đúp vào ô `binh_luan` rồi Enter | Excel đọc lại ô: `=…` thành công thức, `+1` thành `1` |
| Sắp xếp; thêm hay xóa dòng, cột | Nhãn lệch khỏi bình luận |
| Để AutoComplete bật | Gõ `dg` rồi Enter có thể thành `dg, hoi` của dòng trên |
| Gõ `2-4` hay `2/4` ở `chua_chac` | Excel đổi thành ngày tháng. Gõ liền `24` |
| Bắt đầu `ghi_chu` bằng `=`, `+`, `-` | Excel hiểu là công thức |

## 3. Tra nhanh

Mở phần này bên cạnh Excel khi gán. Gõ chữ viết tắt, hoa hay thường đều được.

```text
lien_quan        D điện thoại · N video, người làm video, quà · B người bình luận khác
(một)            L không liên quan · E không nội dung · X không rõ nói về gì

noi_ve_thai_do   pin pin, sạc     man màn hình      hn hiệu năng       nd nhiệt độ      cam camera
(nhiều;          tk thiết kế      db độ bền         pm phần mềm        at âm thanh      pc phần cứng khác
 chỉ khi D)      gia giá          mua mua bán       bh bảo hành, sửa   khac phần khác
                 mc cả máy        hang hãng, fan, người mua
                 dấu viết liền:  + khen   - chê, báo lỗi   = so với máy khác   0 không đánh giá
                 ví dụ:  cam+-, gia0

muc_dich         dg đánh giá   hoi hỏi   tt thông tin   dn đề nghị   bt bản thân   bl báo lỗi máy mình
(nhiều)          tl tranh luận   dua đùa, trêu   ck công kích   mg minigame   qc quảng cáo   xg xã giao
                 x không rõ           ví dụ:  dg, hoi

da_dung          c nói rõ là máy của mình hay người nhà · k không rõ
(một)

may_nhac         t gọi tên máy cụ thể · h chỉ hãng hay dòng chung · k không nhắc
(một)

chua_chac        số của chiều còn phân vân, gõ liền (24); chắc thì để trống
                 1 lien_quan · 2 nói về phần nào · 3 muc_dich · 4 thái độ · 5 da_dung · 6 may_nhac
```

Dòng nào cũng phải đủ năm cột N–R. Chỉ cột O được trống, khi `lien_quan` không phải `D`.

## 4. Gán một dòng

Làm như mã hóa mở ở B4, thêm bước dịch sang nhãn:

1. **Đọc** `binh_luan`. Có `binh_luan_cha` thì đọc để hiểu "nó", "cái đó", "đúng rồi".
2. **Tách ý.** Mỗi ý là một cặp `đối tượng: hành vi`, nghĩ trong đầu, không cần ghi ra. Hành vi lấy theo [bảng hành vi](huong-dan-kham-pha-nhan.md#bảng-hành-vi).
3. **Đối tượng** của các ý cho biết `lien_quan` (chiều 1) và nhãn chiều 2.
4. **Hành vi** của từng ý cho biết dấu thái độ (chiều 4) và `muc_dich` (chiều 3).
5. **Đọc lại chữ** để điền `da_dung` (chiều 5) và `may_nhac` (chiều 6).
6. **Còn phân vân** thì ghi số chiều vào `chua_chac`, lý do vào `ghi_chu`.

Ví dụ: "S22 của mình sọc màn rồi, thay màn hết bao nhiêu"

| Ý | Nhãn chiều 2 | Dấu thái độ | `muc_dich` |
|---|---|---|---|
| `sọc màn: báo lỗi` | `man` | `-` | `bl` |
| `thay màn: hỏi` | `bh` | `0` | `hoi` |

Gõ: `D` | `man-, bh0` | `bl, hoi` | `c` (có "của mình") | `t` (có "S22").

**Nguyên tắc chung:**

- **Theo chữ được viết.** Không đoán ý, không suy từ tên video.
- **Nhãn là của chính bình luận.** Reply chỉ viết "đúng rồi" thì không nhận nhãn `cam` của bình luận cha. Tên máy trong bình luận cha cũng không tính vào `may_nhac`.
- **Mỉa mai rõ** thì gán theo nghĩa thật.
- **Mỗi chiều là một câu hỏi riêng.** Bình luận `N` (về video) vẫn có `muc_dich`: "video hay" là `dg`.
- **Không có nhãn nào vừa** thì chọn nhãn gần nhất, ghi `chua_chac` và lý do. Không tự đặt nhãn mới. Riêng chiều 2 có `khac` cho phần của điện thoại chưa có trong danh sách.
- **Bình luận của chủ kênh, bình luận tiếng nước ngoài:** gán như thường.

## 5. Từng cột

### 5.1 `lien_quan` (chiều 1, một nhãn)

Hỏi lần lượt, gặp câu đầu tiên trả lời "có" thì dừng ([đặc tả mục 1](dac-ta-bo-nhan.md#1-liên-quan-tới-gì-một-nhãn)):

```text
1. Có ít nhất một ý về điện thoại (điền được một nhãn chiều 2)?              có → D
2. Về video, người làm video, người trong video, bài test trong video,
   minigame, quà?                                                           có → N
3. Chỉ nói với hay về một người bình luận khác (đồng ý, cãi, chửi)?          có → B
4. Về chuyện khác: chính trị, lịch sử, chuyện đời, máy tính bảng?            có → L
5. Chỉ có dấu câu, emoji, tiếng cười?                                       có → E
6. Còn lại: có chữ mà không biết nói về cái gì                                  → X
```

| Bình luận | Gán | Vì sao |
|---|---|---|
| "cảm ơn anh, mà pin máy này sao ạ" | `D` | Một ý về điện thoại là đủ, dù còn ý cảm ơn |
| "cảm ơn anh, video hay" | `N` | Không có ý nào về điện thoại |
| "quay video máy này rung quá" | `D` | Nói về camera của máy, không phải video của kênh |
| "anh test thử dưới nước đi" | `N` | Bài test trong video |
| "đúng rồi bạn" | `B` | Chỉ đồng ý với người khác |
| "đúng rồi, pin nó yếu thật" | `D` | Đồng ý, và có ý về pin |
| "tư vấn máy tính bảng 4 triệu" | `L` | Máy tính bảng không tính là điện thoại |
| "tai nghe tặng kèm xịn" | `D` | Phụ kiện của điện thoại tính là điện thoại |
| "kkk pin trâu thật" | `D` | Có ý về pin |
| "đẹp quá", "đỉnh thật" (không rõ cái gì) | `X` | Có chữ, không biết nói về cái gì |

### 5.2 `noi_ve_thai_do` (chiều 2 và chiều 4, nhiều nhãn)

Chỉ điền khi `lien_quan` là `D`. Khi đó phải có **ít nhất một** nhãn.

**Bước 1: chọn nhãn chiều 2** ([đặc tả mục 2](dac-ta-bo-nhan.md#2-nói-về-phần-nào-của-điện-thoại-nhiều-nhãn)). Bình luận nói nhiều phần thì gán đủ.

| Gõ | Nhãn | Khi nói về | Dễ nhầm |
|---|---|---|---|
| `pin` | `pin_sac` | Pin, thời lượng, tụt pin, sạc, củ sạc, công suất sạc | Nóng khi sạc → `nd` |
| `man` | `man_hinh` | Màn, độ sáng, tần số quét, màu màn, độ phân giải, tai thỏ, lỗ khoét, sọc, xanh, kẻ màn | Miếng dán màn → `pc`; hỏi thay màn → `bh` |
| `hn` | `hieu_nang` | Chip, RAM, điểm số, chơi game, độ mượt, đa nhiệm, độ ổn định | Nóng khi chơi game → `nd`; bộ nhớ 128g → `pc` |
| `nd` | `nhiet_do` | Nóng, ấm, quá nhiệt, tản nhiệt | Tụt pin → `pin` |
| `cam` | `camera` | Chụp, quay, zoom, chống rung, cảm biến, màu ảnh, app camera | Cụm camera lồi xấu → `tk` |
| `tk` | `thiet_ke` | Ngoại hình, màu máy, chất liệu, nặng nhẹ, to nhỏ, viền, mặt lưng, hình dáng cụm camera; một máy đẹp hay xấu mà không chỉ phần nào | Rơi bung lưng → `db` |
| `db` | `do_ben` | Độ bền, chống nước, rơi vỡ, bung, nứt | Khung titan nhìn sang → `tk` |
| `pm` | `phan_mem` | Hệ điều hành, giao diện, cập nhật, ứng dụng, AI, thông báo, ngôn ngữ, quảng cáo hiện trong máy | Quảng cáo chèn trong video → không gán chiều 2 (`N`) |
| `at` | `am_thanh` | Loa, mic, thu âm, khử ồn | Tai nghe → `pc` |
| `pc` | `phan_cung_khac` | Bộ nhớ, SIM, 5G, wifi, rung, vân tay, Face ID, bút, cổng; phụ kiện (ốp, miếng dán, cường lực, tai nghe, đồng hồ) | RAM → `hn` |
| `gia` | `gia` | Giá bán, giá về Việt Nam, tiền mua máy, rớt giá, giữ giá, khuyến mãi | Mua trả góp ở đâu → `mua` |
| `mua` | `mua_ban` | Mua ở đâu, khi nào, trả góp, xách tay hay chính hãng, đổi máy, lên đời, bản theo thị trường | Nên mua con nào → `mc` |
| `bh` | `bao_hanh_sua_chua` | Bảo hành, sửa, thay linh kiện, đổi trả, hoàn tiền | Giá máy chính hãng → `gia` |
| `khac` | `khac` | Phần của điện thoại chưa có ở trên | |
| `mc` | `may_chung` | Cả máy, không nêu phần nào: máy nên mua, đời máy, nâng cấp, trải nghiệm chung, chỉ gọi tên máy; "ngon", "đỉnh", "tốt" | "S24 Ultra chụp đẹp" → `cam`; "S24 Ultra đẹp vãi" → `tk` |
| `hang` | `hang_nguoi_dung` | Hãng nói chung, thương hiệu, fan, nhóm người mua, chuyện công ty | "Xiaomi 14 ngon" (gọi tên một máy) → `mc` |

Đã nêu một phần thì **không** thêm `mc` hay `hang` chỉ vì có tên máy, tên hãng: tên đó đã ghi ở `may_nhac`. "S24 Ultra chụp đẹp" chỉ là `cam+`.

**"Đẹp", "xấu", "ngon", "đỉnh", "tốt":** xem chữ đó tả cái gì.

| Bình luận | Gán |
|---|---|
| "S24 Ultra **đẹp** vãi" (một máy, không chỉ phần nào) | `tk+` |
| "S24 Ultra **ngon, đỉnh**" (một máy, không chỉ phần nào) | `mc+` |
| "Xiaomi **đỉnh** thật" (hãng) | `hang+` |
| "S24 Ultra chụp **đẹp**" (ảnh chụp) | `cam+` |
| "27 triệu là **đẹp**" (giá) | `gia+` |
| "**đẹp** quá" (không rõ cái gì) | `lien_quan` là `X`, cột này trống |

**Bước 2: thêm dấu thái độ** cho từng nhãn vừa chọn ([đặc tả mục 4](dac-ta-bo-nhan.md#4-thái-độ-nhiều-nhãn-theo-từng-nhãn-chiều-2)).

| Dấu | Khi | Ví dụ | Dễ nhầm |
|---|---|---|---|
| `+` | Khen | "pin trâu" → `pin+` | "pin trâu hơn iPhone" → `pin=` |
| `-` | Chê, kể cả nói nhẹ; báo lỗi | "pin hơi yếu nhưng chấp nhận được" → `pin-`; "máy mình sọc màn" → `man-` | Cà khịa fan, hãng ("fan iPhone lỏ") → `hang0` |
| `=` | So với máy khác. Ghi bên hơn vào `ghi_chu` | "pin S26U trâu hơn iPhone 17" → `pin=` | "pin trâu, iPhone cũng vậy" (không nói bên nào hơn) → `pin+` |
| `0` | Hỏi, nhắc, giải thích… mà không nói tốt hay xấu về phần đó | "pin bao nhiêu mAh vậy" → `pin0` | "pin được bao lâu, chắc yếu" → `pin-` |

Vừa hỏi vừa chê cùng một phần thì chỉ ghi `-`, không ghi `-0` (ví dụ "chắc yếu" ở trên).

**Cách gõ:**

- Nhãn và dấu viết liền: `pin+`. Nhãn nào cũng phải có dấu.
- Nhiều nhãn thì cách nhau bằng dấu phẩy: `cam+, gia-`.
- Một nhãn có nhiều thái độ thì **viết liền các dấu**: `cam+-`. Không viết `cam+, cam-`: code chỉ giữ dấu sau, mất dấu trước mà không báo.

### 5.3 `muc_dich` (chiều 3, nhiều nhãn)

Xét **mọi ý** của bình luận, kể cả ý về video hay về người khác. Nhiều mục đích thì cách nhau bằng dấu phẩy: `dg, hoi`. Định nghĩa: [đặc tả mục 3](dac-ta-bo-nhan.md#3-mục-đích-nhiều-nhãn).

| Gõ | Người viết đang | Ví dụ | Dễ nhầm |
|---|---|---|---|
| `dg` | Khen, chê, nhận xét, so sánh, dự đoán | "pin trâu, cam đêm hơi nhòe"; "chắc về VN giá gấp đôi" | Hỏi giá → `hoi` |
| `hoi` | Hỏi, kể cả xin link | "có bản 5G chưa"; "ai cho xin link mua" | Xin quà, xin máy → `mg` |
| `tt` | Giải thích, trả lời, chỉ nhắc tới | "ngày 23 ra mắt bạn ạ" | Chỉ đồng ý ("đúng rồi bạn") → `tl`; trả lời kèm khen chê → `dg` |
| `dn` | Khuyên người khác; góp ý, yêu cầu người làm video hay hãng | "đi đường dài thì chọn iPhone"; "anh test thử dưới nước đi" | "mình đang định mua" → `bt` |
| `bt` | Kể về mình, khoe, than, mong muốn (cả định mua), lo ngại | "cuối năm lên 16 pro max"; "chưa có lúa để mua" | Kể để khen chê → `dg`; kể lỗi máy mình → `bl` |
| `bl` | Kể lỗi, hỏng của máy mình hay người nhà đang dùng | "máy tao xanh màn, đang chờ bảo hành" | "nghe nói máy này hay lỗi" → `dg` |
| `tl` | Đồng tình, phản bác, bênh, cãi nhau | "chuẩn, mình cũng thấy vậy"; "chưa chắc đâu, bản nội địa còn mạnh hơn" | "fan táo cay rồi" (khích) → `ck` |
| `dua` | Đùa không nhắm vào ai; trêu nhẹ một người | "màu này hợp rơi tự do"; "ông hoàng phá máy" (gọi người review) | "nhận tiền nên khen" → `ck` |
| `ck` | Cà khịa, mỉa, khích một nhóm, hãng, fan, người review; chửi | "fan táo lúc nào cũng vậy"; "suy nghĩ chẳng ra gì" | Mỉa một phần của máy → `dg` theo nghĩa thật |
| `mg` | Dự thi (đáp án, số may mắn); xin quà, xin máy | "đáp án C, số may mắn 123" | "cảm ơn anh vì minigame" → `xg` |
| `qc` | Quảng cáo bán hàng; mời liên hệ ngoài | "ib zalo nhận máy free" | Người dùng chỉ chỗ mua → `tt` |
| `xg` | Chào, chúc, cảm ơn; chỉ cười mà không có nội dung | "cảm ơn anh"; "=)))" | "cảm ơn, nhưng pin yếu quá" → `xg, dg`; "kkk pin trâu thật" → chỉ `dg` |
| `x` | Không hiểu người viết muốn gì | "@[người dùng] bup" | |

Hai hành vi phải **có chữ** mới tính:

- **Đồng tình, phản bác** (`tl`): có "đúng", "chuẩn", "công nhận" hay "sai", "không phải", "chưa chắc", "làm gì có". Chỉ nói tiếp hay nói khác ý thì không thêm `tl`.
- **Lo ngại** (`bt`): có "sợ", "lo", "ngại". "Máy hở thế này chống nước có sao không" chỉ là `hoi`.

Các hành vi cùng một dòng của bảng thì không cần phân biệt: nhận xét hay dự đoán đều là `dg`.

### 5.4 `da_dung` (chiều 5, một nhãn)

| Gõ | Khi | Ví dụ |
|---|---|---|
| `c` | Bình luận **nói rõ** là máy của mình hay người nhà: "máy mình", "đang xài", "mua về", "dùng 2 năm" | "đang xài S23U, pin ổn"; "con em mua chưa được tháng đã chết màn" |
| `k` | Không nói rõ; nghe người khác kể; mới định mua. Bình luận không nhắc chuyện dùng máy cũng là `k` | "pin máy này yếu"; "nghe bạn bảo máy này nóng" |

Không đoán: "chơi game 30 phút nóng lắm" nghe như đã dùng, nhưng không có chữ nói máy của mình, nên là `k`.

### 5.5 `may_nhac` (chiều 6, một nhãn)

| Gõ | Khi | Ví dụ |
|---|---|---|
| `t` | Có tên một máy cụ thể: hãng hay dòng kèm số đời | "S23U", "14 pro max", "Note 10", "Redmi Note 13 Pro" |
| `h` | **Chỉ** nhắc hãng hay dòng chung, không có đời máy | "Samsung", "iPhone", "Xiaomi" |
| `k` | Không nhắc máy hay hãng nào | "con này", "máy này" |

- Có cả tên máy và tên hãng thì là `t`.
- Viết tắt, biệt danh tính theo nghĩa: "ss" là Samsung, "táo" là iPhone (guideline mục 2 hiểu như vậy).
- Không suy từ `may_video`, tên video hay bình luận cha.

### 5.6 `chua_chac` và `ghi_chu`

- `chua_chac`: số của chiều còn phân vân, gõ liền. Phân vân nhãn chiều 2 và thái độ thì gõ `24`. Chắc thì để trống.
- `ghi_chu`: vì sao phân vân, bên nào hơn (khi có `=`), điều cần bàn. Không chép tên người, số điện thoại, link.
- **Vẫn phải chọn một nhãn.** `chua_chac` không thay cho nhãn.

## 6. Ví dụ đủ năm cột

| # | Bình luận | `lien_quan` | `noi_ve_thai_do` | `muc_dich` | `da_dung` | `may_nhac` | Vì sao |
|---|---|---|---|---|---|---|---|
| 1 | S24 Ultra chụp đẹp nhưng đắt | `D` | `cam+, gia-` | `dg` | `k` | `t` | "Đẹp" tả ảnh chụp. Đã nêu phần nên không thêm `mc` |
| 2 | cam này chụp sáng đẹp nhưng tối xấu | `D` | `cam+-` | `dg` | `k` | `k` | Một nhãn, hai thái độ: viết liền dấu |
| 3 | pin S26U trâu hơn iPhone 17 | `D` | `pin=` | `dg` | `k` | `t` | So sánh; `ghi_chu`: S26U hơn |
| 4 | iPhone giữ giá hơn | `D` | `gia=` | `dg` | `k` | `h` | Giữ giá là `gia`; chỉ nhắc hãng; `ghi_chu`: iPhone hơn |
| 5 | anh ơi máy này về VN giá bao nhiêu | `D` | `gia0` | `hoi` | `k` | `k` | Hỏi, không nói đắt hay rẻ |
| 6 | pin được bao lâu, chắc yếu | `D` | `pin-` | `hoi, dg` | `k` | `k` | Hỏi, và đoán là yếu |
| 7 | nên mua con nào giờ | `D` | `mc0` | `hoi` | `k` | `k` | Hỏi về cả máy, không nêu phần nào |
| 8 | iphone 7 plus (cả bình luận chỉ có vậy) | `D` | `mc0` | `tt` | `k` | `t` | Chỉ nhắc tên máy |
| 9 | máy mình đang dùng là con note 9 | `D` | `mc0` | `bt` | `c` | `t` | Kể về mình, không đánh giá |
| 10 | đang xài S23U, pin ổn | `D` | `pin+` | `dg` | `c` | `t` | Kể để khen: `dg`, không thêm `bt` |
| 11 | mình dùng 2 tháng, sạc hay bị nóng | `D` | `nd-` | `bl` | `c` | `k` | Nóng lúc sạc vẫn là `nd`; lỗi máy mình là `bl` |
| 12 | S22 của mình sọc màn rồi, thay màn hết bao nhiêu | `D` | `man-, bh0` | `bl, hoi` | `c` | `t` | Hai ý, hai nhãn |
| 13 | nghe bạn bảo máy này nóng | `D` | `nd-` | `dg` | `k` | `k` | Không phải máy mình nên không phải `bl` |
| 14 | Tuyệt vời ông mặt trời, 3 tiếng hết pin | `D` | `pin-` | `dg` | `k` | `k` | Mỉa mai: nghĩa thật là chê pin |
| 15 | đắt quá, chưa có tiền | `D` | `gia-` | `dg, bt` | `k` | `k` | Chê giá, và than |
| 16 | fan iPhone lỏ | `D` | `hang0` | `ck` | `k` | `h` | Cà khịa người, không phải chê máy |
| 17 | Xiaomi đỉnh thật | `D` | `hang+` | `dg` | `k` | `h` | Khen hãng |
| 18 | đúng rồi, pin nó yếu thật (reply) | `D` | `pin-` | `tl, dg` | `k` | `k` | "Đúng rồi" là đồng tình; có ý về pin nên là `D` |
| 19 | bật chế độ đêm là đỡ (cha: "cam đêm nhòe quá") | `D` | `cam0` | `dn` | `k` | `k` | Khuyên. Không có chữ đồng ý nên không thêm `tl` |
| 20 | đúng rồi (cha: "camera chụp đẹp ghê") | `B` | (trống) | `tl` | `k` | `k` | Chính reply không nói về camera |
| 21 | video dài quá, tua mỏi tay | `N` | (trống) | `dg` | `k` | `k` | Chê video vẫn là đánh giá |
| 22 | cảm ơn anh, video hay | `N` | (trống) | `xg, dg` | `k` | `k` | Cảm ơn, và khen video |
| 23 | anh test thử dưới nước đi | `N` | (trống) | `dn` | `k` | `k` | Yêu cầu người làm video |
| 24 | nhận tiền nên khen | `N` | (trống) | `ck` | `k` | `k` | Mỉa người review |
| 25 | đáp án C, số may mắn 123 | `N` | (trống) | `mg` | `k` | `k` | Dự thi |
| 26 | tư vấn máy tính bảng 4 triệu | `L` | (trống) | `hoi` | `k` | `k` | Máy tính bảng |
| 27 | =))) | `E` | (trống) | `xg` | `k` | `k` | Chỉ cười |
| 28 | đỉnh thật (không rõ cái gì) | `X` | (trống) | `dg` | `k` | `k` | Biết là khen, không biết khen cái gì |
| 29 | @[người dùng] bup | `X` | (trống) | `x` | `k` | `k` | Không hiểu |

## 7. Chỗ bộ nhãn chưa nói rõ

Đặc tả chưa có luật cho các ca dưới đây. **Chọn theo cách mình hiểu, ghi số chiều vào `chua_chac` và lý do vào `ghi_chu`.** Hai bên lệch nhiều ở đây thì sửa định nghĩa sau khi so ([đặc tả mục 7b](dac-ta-kham-pha-nhan.md#7-kiểm-b6)).

| Ca | Phân vân giữa |
|---|---|
| "Lên đời" và "nâng cấp" gần nghĩa nhau, đặc tả để ở hai nhãn | Chiều 2: `mua` hay `mc` |
| Một phần chỉ được nêu làm lý do hay chi tiết: "chip mạnh lên, ram khan hiếm nên giá tăng". Guideline mục 2 không tách lý do thành mã riêng; đặc tả bộ nhãn không nhắc lại | Chiều 2: chỉ `gia`, hay thêm `hn` |
| Khen hãng đẹp: "Samsung đẹp" | Chiều 2: `tk` hay `hang` |
| Nói về video nhưng có tên máy: "anh review iPhone 15 hay quá" | Chiều 1: `N`, hay `D` với `mc0` |
| Khen máy này, chê máy kia ở cùng một phần, không có chữ so: "pin S24 trâu, pin ip16 yếu" | Chiều 4: `+-` hay `=` |
| Đoán một điều nghe có vẻ xấu hay tốt: "chắc về VN giá gấp đôi" | Chiều 4: `0` hay `-` |
| Dùng thử, mượn máy; hay đang dùng máy khác máy đang hỏi: "đang dùng 11 pro max, có nên lên 15 không" | Chiều 5: `c` hay `k` |
| Báo lỗi mà không có chữ nói máy của mình: "lên bản mới tụt pin nhanh" | Chiều 5: `c` hay `k` |
| Chỉ có emoji hay dấu câu | Chiều 3: `xg` hay `x` |

## 8. Tự tập trước khi gán

Gán thử 12 câu, rồi mới mở đáp án. Sai câu nào thì đọc lại phần của cột đó. Câu 5 và câu 12 là reply, bình luận cha ghi trong ngoặc.

1. màn sáng đẹp mà viền dày
2. pin 5000 mà tụt nhanh, được cái sạc lẹ
3. S24 với ip15 con nào pin trâu hơn
4. máy ba mình rơi một lần là bung lưng
5. sai rồi bạn, con này chụp đêm còn thua S22 (cha: "máy này chụp đêm số một")
6. áo anh đẹp thế
7. chúc anh sức khỏe
8. Apple dạo này làm ăn chán
9. bao giờ có hàng chính hãng vậy anh
10. máy tính bảng chơi game ngon
11. kkk quay video máy này rung như động đất
12. chuẩn luôn (cha: "pin máy này yếu")

<details>
<summary><b>Đáp án</b> (bấm để mở)</summary>

| # | `lien_quan` | `noi_ve_thai_do` | `muc_dich` | `da_dung` | `may_nhac` | Vì sao |
|---|---|---|---|---|---|---|
| 1 | `D` | `man+, tk-` | `dg` | `k` | `k` | Viền là thiết kế |
| 2 | `D` | `pin+-` | `dg` | `k` | `k` | Pin và sạc chung một nhãn: viết liền dấu |
| 3 | `D` | `pin0` | `hoi` | `k` | `t` | Hỏi, chưa nói bên nào hơn |
| 4 | `D` | `db-` | `bl` | `c` | `k` | Máy người nhà hỏng: `bl`, `c` |
| 5 | `D` | `cam=` | `tl, dg` | `k` | `t` | "Sai rồi" là phản bác; so với S22. `ghi_chu`: S22 hơn |
| 6 | `N` | (trống) | `dg` | `k` | `k` | Người trong video; khen áo vẫn là `dg` |
| 7 | `N` | (trống) | `xg` | `k` | `k` | Chúc người làm video |
| 8 | `D` | `hang-` | `dg` | `k` | `h` | Chê hãng, chuyện công ty |
| 9 | `D` | `mua0` | `hoi` | `k` | `k` | Khi nào có hàng, chính hãng: `mua` |
| 10 | `L` | (trống) | `dg` | `k` | `k` | Máy tính bảng không tính là điện thoại |
| 11 | `D` | `cam-` | `dg` | `k` | `k` | Quay là camera của máy. Có nội dung nên không thêm `xg` |
| 12 | `B` | (trống) | `tl` | `k` | `k` | Chỉ đồng tình, không nói về pin |

</details>

## 9. Làm và nộp

**Khi làm:** gán theo thứ tự `stt`, chia vài lượt cho đỡ mỏi. Đổi cách hiểu giữa chừng thì quay lại sửa các dòng trước: chưa nộp thì vẫn sửa được.

**Kiểm lại:** *Data → Filter*, bấm mũi tên ở từng cột:

| Cột | Phải thấy |
|---|---|
| `nguoi_gan` | Chỉ `B`, không có *(Blanks)* |
| `lien_quan` | Chỉ `D`, `N`, `B`, `L`, `E`, `X`; không có *(Blanks)* |
| `noi_ve_thai_do` | Lọc `lien_quan` là `D`: không có *(Blanks)*, nhãn nào cũng có dấu, không nhãn nào lặp trong một ô. Lọc các nhãn còn lại: chỉ có *(Blanks)* |
| `muc_dich` | Không có *(Blanks)*. Hai mục đích phải cách nhau bằng dấu phẩy: gõ `dg hoi` là sai |
| `da_dung` | Chỉ `c`, `k` |
| `may_nhac` | Chỉ `t`, `h`, `k` |

Đừng dựa vào số *Count* ở góc dưới Excel: ô trống nạp từ CSV vẫn bị đếm là có chữ.

Xem lại thêm: các dòng có `chua_chac`; các dòng đầu, lúc chưa quen tay; dòng có `=` đã ghi bên hơn chưa; dòng có `bl` mà `da_dung` là `k`.

**Nộp:**

1. **Bỏ hết lọc** (*Data → Clear*), rồi lưu file `.xlsx`.
2. **File → Save As**, kiểu *CSV UTF-8 (Comma delimited)*, thư mục `data/kham-pha/`, tên **`phieu_lo_K.csv`**, đồng ý ghi đè. Excel hỏi về mất định dạng thì vẫn lưu. Cột ẩn vẫn được lưu. Rồi **đóng Excel** (hỏi lưu lần nữa thì chọn *Don't Save*).
3. Mở `phieu_lo_K.csv` bằng VS Code: dòng đầu phải bắt đầu bằng `stt,lo,mau` (hoặc `stt;lo;mau`). Thấy `Column1` thì phiếu sai tên cột: mở lại file `.xlsx`, xóa dòng 1 (`Column1`, `Column2`…) để dòng `stt`, `lo`, `mau`… lên đầu, rồi lưu lại.
4. Báo đã nộp. Từ lúc này **không sửa nhãn nữa**.

## 10. Sau khi nộp

- Code so hai phiếu: đồng ý thô, kappa, đồng ý dương cho từng chiều.
- B phân xử các ca lệch, ghi lý do. Nhãn đã phân xử mới vào mẫu phân bố.
- Chiều có kappa dưới 0,6 thì sửa định nghĩa theo các ca lệch, rồi kiểm lại trên 50 bình luận của lô D2.

Luật đầy đủ: [đặc tả khám phá nhãn mục 7b](dac-ta-kham-pha-nhan.md#7-kiểm-b6). Kiểm nhãn của A ở lô 1–5 là việc khác, làm theo [guideline mục 6](huong-dan-kham-pha-nhan.md#6-kiểm-nhãn-của-claude-b6b7).

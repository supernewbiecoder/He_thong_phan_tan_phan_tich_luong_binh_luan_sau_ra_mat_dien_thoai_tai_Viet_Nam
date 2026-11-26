# Guideline mã hóa (khám phá nhãn)

> Mục đích: Quy ước ghi mã khi mã hóa mở, cách gom mã thành bộ nhãn, cách gán mù lô K và kiểm nhãn; dùng cho Claude (người mã hóa A) và trưởng nhóm (người kiểm B); cập nhật lần cuối: 2026-11-26.

Luật (lấy mẫu, vai trò, quy tắc mù, công thức, luật chốt bộ nhãn) nằm ở [đặc tả khám phá nhãn](dac-ta-kham-pha-nhan.md). File này chỉ nói **cách làm**, không chép lại luật. Các từ *mã*, *đối tượng*, *nhãn*, *khía cạnh* dùng theo [bảng thuật ngữ](dac-ta-kham-pha-nhan.md#thuật-ngữ).

## 1. Ai làm gì

| Bước | Claude (A) | Trưởng nhóm (B) |
|---|---|---|
| B2 lấy mẫu, B3 HAC | Viết code, chạy | |
| B4 mã hóa mở | Mã hóa lô 1, **dừng** để B xem; rồi lô 2–5 và mẫu có chủ đích | Xem cách mã ở lô 1 (20–30 phút): đọc bình luận, tự nghĩ mã, rồi mới nhìn mã của A (mục 6, bước 3); góp ý cả [bảng hành vi](#bảng-hành-vi). Tùy chọn: tự mã một lô trong `phieu_ma_hoa_mo_B.csv` theo mục 2, không mở phiếu của A, để tính kappa theo hành vi ([đặc tả mục 7d](dac-ta-kham-pha-nhan.md#7-kiểm-b6)) |
| B5 gom bộ nhãn | Gom mã, viết bộ nhãn, đếm bão hòa | Duyệt bộ nhãn |
| B6 kiểm | Gán lô K theo bộ nhãn | **Gán mù lô K** (mục 5), kiểm nhãn của A (mục 6) |
| B7 phân bố | Gán lại lô 1–5 theo bộ nhãn, tính phân bố | Kiểm |
| B8 chốt | Đối chiếu HAC trên cả bộ dữ liệu, đề xuất | Quyết |

Phần của B tính gộp khoảng 3 giờ. Đó là phần **không thay được bằng AI**: không có nó thì không biết nhãn của AI đúng tới đâu.

## 2. Ghi mã tự do

Mỗi bình luận ghi **ít nhất một mã** vào cột `ma_tu_do`, các mã cách nhau bằng `;`. Mỗi mã có dạng:

```text
đối tượng: hành vi (ghi chú phụ)?
```

- **đối tượng:** bình luận nói về cái gì. Ghi **cụ thể nhất có thể, bằng từ của chính bình luận**: `pin`, `sạc`, `chip`, `nóng máy`, `cam đêm`, `giá`, `người review`, `video`, `quà`, `fan táo`, `máy (chung)`. **Không** dùng tên 9 khía cạnh đặt sẵn ("Hiệu năng", "Thiết kế & độ bền"…). Gom lại là việc của B5.
- **hành vi:** người viết làm gì với đối tượng đó. Chọn trong [bảng hành vi](#bảng-hành-vi). Được thêm hành vi mới, nhưng phải thêm vào bảng kèm định nghĩa.
- **(ghi chú phụ):** chỉ ghi khi có. Ví dụ `(so với ip17prm)`, `(mỉa mai)`, `(về máy khác)`. Lý do, ví dụ, chi tiết của ý đó cũng ghi ở đây, không tách thành mã `nhắc` riêng (xem `nhắc` trong [bảng hành vi](#bảng-hành-vi)).
- **`?` ở cuối mã:** chưa chắc. Người kiểm sẽ xem mọi mã có `?`.

| Bình luận (tự soạn) | Mã | Vì sao |
|---|---|---|
| "pin trâu, cam đêm hơi nhòe" | `pin: khen; cam đêm: chê` | Hai ý, hai mã |
| "cam này chụp sáng đẹp nhưng tối xấu" | `cam chụp sáng: khen; cam chụp tối: chê` | Cùng camera nhưng hai điều kiện, hai thái độ: tách thành hai mã, không gộp thành một |
| "anh ơi máy này về VN giá bao nhiêu" | `giá: hỏi; người review: hỏi` | Hỏi giá, hỏi người làm video |
| "em xin 1 suất ạ" | `quà: xin` | Ghi đúng việc người viết làm, chưa phán là spam |
| "táo thì đỉnh rồi, ss toàn copy" | `iphone (chung): khen; samsung (chung): chê; fan hãng: cà khịa` | Không nêu khía cạnh, có thái độ với hãng |
| "đúng rồi" (cha: "camera chụp đẹp ghê") | `bình luận cha: đồng tình` | Chính bình luận không nói về camera; ghi `(cha khen camera)` nếu cần |
| "bật chế độ đêm là đỡ" (cha: "cam đêm nhòe quá") | `chế độ đêm: khuyên` | Nói tiếp ý cha nhưng không có chữ tỏ đồng ý hay phản đối: không thêm `bình luận cha: …` |
| "ib zalo nhận máy free" | `máy miễn phí: quảng cáo; liên hệ ngoài: mời` | |
| "video dài quá, tua mỏi tay" | `video: chê` | Đối tượng là video, không phải máy |
| "mình dùng 2 tháng, sạc hay bị nóng" | `nóng khi sạc: báo lỗi` | Lỗi của máy mình: `báo lỗi`, không phải `chê` hay `kể` |
| "dùng thử rồi, cam xấu lắm" | `cam: chê` | Kể để chê: mã `chê`, không thêm `kể` |
| "cuối năm mình sẽ lên 16 pro max" | `16 pro max: mong muốn (định lên đời)` | Định mua là `mong muốn`, không phải `kể` |
| "máy mình đang dùng là con note 9" | `máy đang dùng: kể (note 9)` | Chỉ kể về mình, không đánh giá: `kể` |
| "chip mạnh lên, ram khan hiếm nên giá tăng" | `giá tăng: giải thích (chip mạnh lên, ram khan hiếm)` | Chip, ram chỉ là lý do: ghi trong ngoặc, không tách thành `chip: nhắc`, `ram: nhắc` |
| "máy hở thế này chống nước có sao không" | `chống nước: hỏi (máy hở)` | Câu hỏi không có chữ "sợ", "lo", "ngại": chỉ `hỏi`, không thêm `lo ngại` |
| "pin s26u trâu hơn ip17" | `pin: so sánh (s26u hơn ip17)` | So sánh, ghi bên thắng |
| "kkk" | `không nội dung: cười` | Không bỏ trống |
| "Tuyệt vời ông mặt trời, 3 tiếng hết pin" | `pin: chê (mỉa mai)` | Mỉa mai rõ: mã theo nghĩa thật |
| "ai cho xin link mua với" | `chỗ mua: hỏi` | |

### Bảng hành vi

Rút ra từ lô 1 (22/11). Trưởng nhóm cho làm tiếp lô 2–5 cùng ngày (chưa xem từng mã lô 1).

**Sửa ngày 23/11**, sau khi so mã của A và B ([đặc tả mục 7d](dac-ta-kham-pha-nhan.md#7-kiểm-b6)):
- `kể`: theo quyết định của trưởng nhóm. `kể` chỉ là kể; không ghi người viết đã dùng máy hay chưa trong mã tự do. Chiều "đã dùng máy" vẫn giữ, nhưng gán ở bộ nhãn (B5–B7).
- Trưởng nhóm quyết thêm: định mua là `mong muốn`; báo lỗi máy của mình là hành vi riêng `báo lỗi`.
- `nhắc`, `nhận xét`, `lo ngại`, `đồng tình` / `phản bác`, ghi chú "Không liên quan điện thoại": Claude đề xuất, trưởng nhóm cho sửa.
- `trêu`, `cà khịa`: chỉ thêm chữ cho rõ, không đổi luật.

Phiếu của A và B (lô 1–5, CD) mã theo bản trước khi sửa. Bộ nhãn (B5) dựa trên bản này.

| Hành vi | Dùng khi | Ví dụ mã |
|---|---|---|
| `khen` / `chê` | Đánh giá tốt / xấu | `pin: khen` |
| `nhận xét` | Có nhận định nhưng không rõ tốt hay xấu. **Chỉ dùng khi không hành vi nào khác hợp:** rõ tốt hay xấu, kể cả nói nhẹ ("nhiệt độ cũng không cao lắm"), thì `khen` / `chê`; đoán ("chắc", "có khi", "sẽ") thì `dự đoán`; trả lời câu hỏi thì `trả lời`; đùa thì `đùa` | `điểm số: nhận xét (không quan trọng)` |
| `nhắc` | Chỉ nhắc tới, không đánh giá, và là **một ý riêng** (vd cả bình luận chỉ có tên một máy). Thứ được nêu làm lý do, ví dụ, chi tiết cho ý khác thì ghi trong ngoặc của mã đó, không tách thành `nhắc` | `iphone 7 plus: nhắc` |
| `giải thích` | Nói nguyên nhân, cách hoạt động | `giá tăng: giải thích` |
| `so sánh` | So hai thứ, ghi bên hơn | `chụp đêm: so sánh (android hơn iphone)` |
| `hỏi` | Hỏi thông tin, kể cả xin link | `nhạc nền: hỏi (xin link)` |
| `yêu cầu` | Đề nghị người làm video làm gì (test, quay) | `speedtest: yêu cầu` |
| `xin` | Xin được cho (quà, máy) | `quà: xin` |
| `khuyên` | Khuyên người khác mua, đừng mua, đợi | `máy nên mua: khuyên (s22u cũ)` |
| `góp ý` | Chỉ lỗi hay điều nên làm cho người làm video, cho hãng | `người review: góp ý (nói nhầm)` |
| `dự đoán` | Đoán giá, đoán đời máy sau | `giá: dự đoán (sẽ giảm)` |
| `mong muốn` | Muốn có, muốn mua, định mua, định lên đời, ước giá như | `camera trước ẩn: mong muốn` |
| `kể` | Kể về chính mình (máy đang dùng, việc mình làm), **không kèm đánh giá**. Kể để khen, chê, hỏi thì mã `khen`, `chê`, `hỏi`, không thêm `kể`; báo lỗi máy của mình thì mã `báo lỗi`. Không cần ghi người viết đã dùng máy hay chưa | `máy đang dùng: kể (note 9)` |
| `báo lỗi` | Kể lỗi, hỏng hóc của máy mình hay người nhà đang dùng. Đối tượng là chính cái lỗi. Báo lỗi để hỏi cách sửa thì thêm `hỏi` | `xanh màn: báo lỗi (iphone 14 promax, chờ bảo hành)` |
| `khoe` | Khoe (xem sớm, mua được máy) | `xem sớm: khoe` |
| `than` | Than hoàn cảnh của mình (không đủ tiền, phải bù tiền) | `trade lên: than (phải bù 9tr)` |
| `lo ngại` | Lo một rủi ro. Phải có chữ tỏ lo: "sợ", "lo", "ngại". Câu hỏi "có sao không", "có bị… không" mà không có chữ đó thì chỉ `hỏi` | `chống nước: lo ngại (sợ vào nước)` |
| `bênh` | Bênh hãng, máy trước lời chê | `iphone (chung): bênh` |
| `đồng tình` / `phản bác` | Đồng ý / cãi lại một bình luận khác. Chỉ mã khi có chữ tỏ thái độ: đồng ý ("đúng", "chuẩn", "công nhận"), phản đối ("sai", "không phải", "chưa chắc", "làm gì có"). Nói tiếp hay nói khác ý mà không có chữ đó thì chỉ mã nội dung | `bình luận cha: phản bác` |
| `trả lời` | Trả lời câu hỏi, không thêm thái độ | `màu máy: trả lời (mỗi người một gu)` |
| `đùa` | Đùa, không nhắm vào ai | `số camera: đùa` |
| `trêu` | Trêu nhẹ một người cụ thể, kể cả người review (gọi đùa, đặt biệt danh) | `người review: trêu (thánh phá hoại)` |
| `cà khịa` | Mỉa, khích một nhóm, một hãng, fan. Mỉa một bộ phận, tính năng của máy thì không phải `cà khịa`: mã theo nghĩa thật kèm `(mỉa mai)`, như `pin: chê (mỉa mai)` | `fan iphone: cà khịa` |
| `chửi` | Chửi, lăng mạ | `người khác: chửi` |
| `cãi nhau` | Cãi qua lại với người khác, không về máy | `người khác: cãi nhau` |
| `quảng cáo` | Quảng cáo bán hàng, dịch vụ | `cửa hàng: quảng cáo (trả góp, có link)` |
| `dự thi` | Gửi đáp án, số may mắn, hashtag để dự minigame (thêm ở lô 4) | `minigame: dự thi` |
| `chào`, `cảm ơn` | Chào, chúc, cảm ơn | `người review: cảm ơn` |
| `cười` | Chỉ cười, không có nội dung ("kkk", ":)))") | `không nội dung: cười` |

**Đối tượng hay dùng** (cũng rút ra từ lô 1):
- `máy (chung)`: nói về cả máy, không nêu khía cạnh. Máy được gọi tên thì ghi tên làm đối tượng (`s8: chê`) hoặc trong ghi chú phụ (`(iphone)`). Không suy tên máy từ video.
- `bình luận cha`: thái độ với bình luận cha (`đồng tình`, `phản bác`, `hỏi`). `đồng tình`, `phản bác` chỉ ghi khi có chữ tỏ thái độ (bảng trên).
- `người review`, `người khác` (một người bình luận khác), `fan …`, `người mua …`.
- **Ghi chú "Không liên quan điện thoại"** chỉ dùng khi bình luận không nói về điện thoại, **và** cũng không nói về video, người làm video, quà hay minigame của video. Ví dụ: chính trị, lịch sử, chuyện đời, chửi nhau không về máy. Khi đó đối tượng là chủ đề (`lịch sử`). Không ghi chú này cho:
  - bình luận về người review hay về video: đối tượng `người review`, `video` đã cho biết điều đó;
  - bình luận không có nội dung: đã có `không nội dung`.

**Quy tắc:**
1. Reply thì đọc kèm bình luận cha. Nhưng mã là về **chính bình luận**: cha chỉ để hiểu "nó", "cái đó", "đúng rồi".
2. Mã theo **những gì được viết**, không đoán ý người viết, không suy từ tên video.
3. Bình luận có nhiều ý thì ghi đủ các ý. **Hành vi** luôn lấy đúng chữ trong bảng hành vi: đã có `hỏi` thì không viết `thắc mắc`. **Đối tượng** giữ từ của bình luận, kể cả khi chỗ khác đã dùng từ đồng nghĩa (`chụp đêm`, `chụp tối` đều giữ); gom ở B5. Riêng chữ do người mã tự diễn giải, khi bình luận không có danh từ (như "xấu hơn ip11" → `ngoại hình`), thì dùng lại đúng chữ đã dùng.
4. Không hiểu thì ghi `không hiểu: ?` và ghi lý do vào `ghi_chu`.
5. Tiếng nước ngoài: vẫn mã nội dung, thêm `(tiếng anh)` hay ngôn ngữ khác vào ghi chú phụ.
6. Bình luận của chủ kênh (cột `chu_kenh = co`): mã bình thường. Cột đó đã ghi sẵn nên không cần thêm mã.
7. **Không** chép tên người viết, số điện thoại, link vào mã hay ghi chú. Phiếu che tên dạng `@tên` và `+Tên Họ`; phiếu lô 1–5 và CD xuất trước 23/11 nên còn 3 tên dạng `+Tên`. Tên viết không có `@` hay `+` vẫn còn, cũng không chép.
8. Điền `nguoi_ma_hoa`: Claude ghi `claude`.

## 3. Gom mã thành bộ nhãn (B5, A làm, B duyệt)

1. Đếm mọi mã theo đối tượng và theo hành vi.
2. Gom đối tượng cùng nghĩa: `pin`, `sạc`, `mah`, `thời lượng` có thể thành một nhãn "pin và sạc". Gom hay tách thì ghi lý do. Dữ liệu cho thấy người ta nói riêng về sạc nhiều thì tách.
3. Xếp nhãn vào chiều. Mỗi chiều là một câu hỏi về bình luận, ví dụ "nói về cái gì?", "để làm gì?", "khen hay chê?". Có những chiều nào là do dữ liệu quyết.
4. Viết cho mỗi nhãn đủ các phần ở [đặc tả mục 6](dac-ta-kham-pha-nhan.md#6-gom-mã-thành-bộ-nhãn-và-bão-hòa-b5). Ví dụ lấy từ phiếu, sửa vài chữ cho khỏi lộ bình luận thật.
5. Đếm số nhãn mới theo từng lô 1→5 để biết đã bão hòa chưa.

## 4. Danh sách HAC: không chấm

Ngày 23/11 trưởng nhóm quyết không chấm danh sách HAC. Không cần làm gì với `hac_ung_vien.csv`. Claude dùng HAC để đối chiếu ở B8 ([đặc tả mục 4.4](dac-ta-kham-pha-nhan.md#44-đối-chiếu-không-có-người-chấm)).

## 5. Gán mù lô K (B6)

**Làm từng bước, có ví dụ và bài tập: [hướng dẫn gán mù lô K](huong-dan-gan-lo-k.md).** Mục này chỉ giữ quy trình và bảng viết tắt.

1. Chạy `python -m src.labeling.sample --xuat-lo K` để có phiếu trống lô K. Mỗi người một bản.
2. **Mở phiếu bằng Excel qua Data → From Text/CSV**, lưu bằng *CSV UTF-8*. Các bước: [hướng dẫn gán mù lô K mục 2.1](huong-dan-gan-lo-k.md#21-các-bước-excel-tiếng-anh). Đừng bỏ bước *Use First Row as Headers*: thiếu nó thì tên cột thành `Column1`, code không tìm thấy cột.

   **Không** double-click file CSV. Mở kiểu đó, Excel hiểu ô bắt đầu bằng `+`, `=`, `-` là công thức và làm hỏng chữ: phiếu B ngày 23/11 có một ô thành `#NAME?`.
3. Gán theo **bộ nhãn** đã duyệt (không phải mã tự do), cho từng chiều. Bình luận nào cũng phải đủ năm cột, trừ `noi_ve_thai_do` để trống khi `lien_quan` không phải `dien_thoai`. Gõ tên đầy đủ hoặc chữ viết tắt:

   | Cột | Viết tắt |
   |---|---|
   | `lien_quan` (một) | `D` dien_thoai · `N` ngu_canh · `B` nguoi_binh_luan · `L` khong_lien_quan · `E` khong_noi_dung · `X` khong_xac_dinh |
   | `noi_ve_thai_do` (nhiều) | Nhãn chiều 2: `pin` · `man` màn hình · `hn` hiệu năng · `nd` nhiệt độ · `cam` · `tk` thiết kế · `db` độ bền · `pm` phần mềm · `at` âm thanh · `pc` phần cứng khác · `gia` · `mua` mua bán · `bh` bảo hành, sửa chữa · `khac` · `mc` máy chung · `hang` hãng, người dùng. Viết liền thái độ: `+` khen · `-` chê · `=` so sánh · `0` không đánh giá. Ví dụ `cam+-, gia0` |
   | `muc_dich` (nhiều) | `dg` đánh giá · `hoi` · `tt` thông tin · `dn` đề nghị · `bt` bản thân · `bl` báo lỗi · `tl` tranh luận · `dua` · `ck` công kích · `mg` minigame · `qc` quảng cáo · `xg` xã giao · `x` không rõ |
   | `da_dung` (một) | `c` co · `k` khong_ro |
   | `may_nhac` (một) | `t` gọi tên máy · `h` chỉ hãng · `k` không nhắc |

   Chưa chắc chiều nào thì ghi số chiều vào `chua_chac` (vd `24`). Ví dụ một dòng: "S24 Ultra chụp đẹp nhưng đắt" → `D` | `cam+, gia-` | `dg` | `k` | `t`.
4. **Không** xem phiếu của người kia, không bàn với nhau, cho tới khi cả hai nộp.
5. Nộp xong mới so. Code tính đồng ý thô, kappa, đồng ý dương.
6. B quyết các ca lệch, ghi lý do. Lệch vì định nghĩa chưa rõ thì sửa bộ nhãn.

### Lô D2: kiểm lại sau khi sửa định nghĩa (26/11)

Làm như lô K (các bước trên và [hướng dẫn gán lô K](huong-dan-gan-lo-k.md)), khác ba điểm:
1. Phiếu là `data/kham-pha/phieu_lo_D2.csv`, chỉ **50 bình luận**. Lưu bản đã gán là `phieu_lo_D2_B.xlsx`. Không mở `nhan_lo_D2_A.txt`.
2. **Đọc lại hai định nghĩa vừa sửa** trước khi gán: `khong_xac_dinh` ở chiều 1 và `dua` ở chiều 3 ([đặc tả bộ nhãn mục 1, 3](dac-ta-bo-nhan.md)). Dùng **bộ nhãn chốt** (mục 8): không dùng `nhiet_do`, `am_thanh`, `khong_noi_dung` nữa; thay bằng `hieu_nang`, `phan_cung_khac`, `khong_xac_dinh`.
3. Có thêm cột **`ten_may`**: khi `may_nhac` là `t`, ghi mọi máy được gọi tên, cách nhau bằng `;`, theo mã máy trong `config/pipeline.yaml` (trường `name`, vd `s24u`, `ip15prm`). Không có trong danh mục thì ghi tên như bình luận viết. `may_nhac` khác `t` thì để trống.

## 6. Kiểm nhãn của Claude (B6–B7)

1. Xem ngẫu nhiên ít nhất 100 bình luận của lô 1–5 (code sẽ chọn sẵn), và **mọi** bình luận có mã `?`.
2. Đồng ý thì bỏ qua. Không đồng ý thì sửa, ghi nhãn cũ, nhãn mới, lý do vào cột `ghi_chu_kiem`.
3. **Cẩn thận thiên lệch "thấy sẵn thì gật":** đọc bình luận trước, tự nghĩ nhãn, rồi mới nhìn nhãn của A.

**Cách điền `phieu_kiem_b7.csv`** (luật: [đặc tả mục 7c](dac-ta-kham-pha-nhan.md#7-kiểm-b6)):
1. Mở như mục 5, bước 2. **Ẩn các cột từ `lien_quan` tới `ghi_chu_a`** trước khi đọc, rồi mới mở ra so.
2. Dòng nào xem xong thì ghi `x` ở `da_kiem`, kể cả khi đồng ý.
3. Sai chiều nào thì ghi nhãn đúng vào cột `sua_…` của chiều đó, ghi đủ cả ô chứ không chỉ phần khác. Gõ tên đầy đủ hoặc viết tắt như mục 5:
   - `sua_lien_quan`, `sua_da_dung`, `sua_may_nhac`: một nhãn;
   - `sua_muc_dich`: các nhãn cách nhau bằng `;`;
   - `sua_noi_ve_thai_do`: `nhãn chiều 2:thái độ`, cách nhau bằng `;`, nhiều thái độ nối bằng `+`. Ví dụ `camera:tich_cuc+tieu_cuc; gia:khong_danh_gia`.
4. Lưu đúng tên file, rồi chạy `python -m src.labeling.distribution`. Nhãn gõ sai thì code dừng và nói dòng nào.

## 7. Lỗi hay gặp

| Lỗi | Vì sao hỏng | Cách tránh |
|---|---|---|
| Ghi đối tượng bằng tên 9 khía cạnh đặt sẵn | Chỉ xác nhận lại giả định, không tìm được cái thiếu | Ghi bằng từ của chính bình luận |
| Mã quá chung (`tích cực`, `liên quan`, `khác`) | Không gom được thành nhãn có nghĩa | Luôn có cả đối tượng lẫn hành vi |
| Bỏ trống bình luận khó | Mất đúng những ca cần cho định nghĩa | Ghi `không hiểu: ?` kèm ghi chú |
| Đọc lô K trước B6 | Kappa bị thổi phồng, không còn đo được độ rõ của nhãn | Code không xuất lô K tới B6 |
| B xem nhãn của A trước khi tự nghĩ | Gật theo AI | Mục 6, bước 3 |
| Chép tên người viết hay số điện thoại | Lộ dữ liệu cá nhân | Phiếu chỉ có nội dung bình luận |
| Mở phiếu CSV bằng double-click | Ô bắt đầu bằng `+`, `=`, `-` bị Excel biến thành công thức, chữ bình luận mất (`#NAME?`) | Mở qua Data → From Text/CSV (mục 5) |

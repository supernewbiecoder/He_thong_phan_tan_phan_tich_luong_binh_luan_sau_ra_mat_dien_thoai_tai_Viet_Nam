# Đặc tả bộ nhãn (B5)

> Mục đích: Bộ nhãn rút từ mã hóa mở 600 bình luận: 6 chiều, định nghĩa từng nhãn, ví dụ thuộc và dễ nhầm, mã đã gom vào; dùng để gán mù lô K (B6) và gán lại cả mẫu (B7); bộ nhãn chốt sau B8 (mục 8); cập nhật lần cuối: 2026-11-26.

**Trạng thái: CHỐT ngày 26/11 (B8, mục 8).** Mục 1–6 là bộ nhãn dùng để gán ở B6, B7 (bộ khám phá); **bộ nhãn chốt** là bộ khám phá sau khi gộp theo mục 8. Nhãn đã gán ở B6, B7 giữ nguyên; code đổi sang bộ chốt khi báo cáo. Claude (người mã hóa A) gom từ mã tự do của A, theo [đặc tả khám phá nhãn mục 6](dac-ta-kham-pha-nhan.md#6-gom-mã-thành-bộ-nhãn-và-bão-hòa-b5) và [guideline mục 3](huong-dan-kham-pha-nhan.md#3-gom-mã-thành-bộ-nhãn-b5-a-làm-b-duyệt).

- **Ánh xạ mã → nhãn:** `src/labeling/label_set.py`. Sửa nhãn ở file này thì sửa ánh xạ và test trong cùng lần sửa.
- **Số đếm, lô gặp lần đầu, bão hòa:** [báo cáo bộ nhãn](bao-cao-bo-nhan.md), do code sinh. File này không chép số, để hai nơi không lệch nhau.
- **Bão hòa đạt:** lô 2, 4, 5 không có nhãn mới; lô 3 có 2 (`khong_noi_dung`, `minigame`). Theo luật mục 6, không cần mã thêm lô dự trữ.
- Ví dụ trong file này đã sửa chữ, không chép nguyên bình luận thật.

## 0. Cách dùng

- *Nhãn*, *khía cạnh*, *đối tượng* dùng theo [bảng thuật ngữ](dac-ta-kham-pha-nhan.md#thuật-ngữ): mọi khía cạnh là nhãn của chiều 2, nhưng không phải nhãn nào cũng là khía cạnh.
- Mỗi **chiều** là một câu hỏi về bình luận. Chiều ghi rõ **một nhãn** hay **nhiều nhãn** mỗi bình luận.
- Gán theo **những gì được viết**: không suy từ tên video, không đoán ý người viết (guideline quy tắc 2).
- Reply thì đọc kèm bình luận cha để hiểu "nó", "cái đó", nhưng nhãn là của chính bình luận.
- Mỉa mai rõ thì gán theo nghĩa thật ("tuyệt vời, 3 tiếng hết pin" là chê pin).
- Chưa chắc thì đánh dấu `?`. Người kiểm xem mọi nhãn có `?`.

## 1. Liên quan tới gì (một nhãn)

Câu hỏi: bình luận nói về điện thoại, hay về thứ khác? Xét theo thứ tự trong bảng, gặp dòng đầu tiên đúng thì dừng.

| Nhãn | Định nghĩa | Ví dụ thuộc | Dễ nhầm, không thuộc | Mã đã gom |
|---|---|---|---|---|
| `dien_thoai` | Có ít nhất một ý về điện thoại, tức là có ít nhất một nhãn của chiều 2 | "pin máy này trâu ghê"; "về VN giá bao nhiêu anh" | "anh review nói dễ hiểu ghê" → `ngu_canh` | Mọi mã có đối tượng thuộc chiều 2 |
| `ngu_canh` | Không có ý về điện thoại; nói về video, người làm video, người trong video, bài test trong video, minigame, quà | "cảm ơn anh, video hay"; "đáp án C, số may mắn 123" | "quay video máy này rung quá" → `dien_thoai` (camera) | `người review`, `video`, `kênh`, `bài test…`, `speedtest`, `xem sớm`, `nhạc nền`, `minigame` |
| `nguoi_binh_luan` | Chỉ nói với hay về một người bình luận khác (đồng ý, cãi, chửi), không có ý về máy | "đúng rồi bạn"; "suy nghĩ kiểu gì vậy" | "đúng rồi, pin nó yếu thật" → `dien_thoai` | `bình luận cha`, `người khác` |
| `khong_lien_quan` | Không về điện thoại, video hay người bình luận: chính trị, lịch sử, chuyện đời; **máy tính bảng** | "tủ lạnh nhà mình cũng chỉnh kiểu đó"; "10k mua được 2 ổ bánh mì"; "tư vấn máy tính bảng 4 triệu" | "áo anh mặc trong video đẹp" → `ngu_canh`; phụ kiện của điện thoại (ốp, tai nghe) → `dien_thoai` | `lịch sử`, `tủ đá`, `giá bánh mì`, ghi chú "Không liên quan điện thoại" |
| `khong_noi_dung` | Chỉ có dấu câu, emoji, tiếng cười | "."; "=)))" | "kkk pin trâu thật" → `dien_thoai` | `không nội dung` |
| `khong_xac_dinh` | Có chữ nhưng không biết nói về cái gì. **Phép thử (sửa 26/11):** hỏi "nói về cái gì?"; nếu câu trả lời không nằm trong chữ của bình luận (hay của bình luận cha, khi bình luận này nói tiếp đúng chuyện đó) thì là `khong_xac_dinh`. **Không đoán** từ tên video hay từ chuyện hay gặp. Câu cụt một tính từ ("xấu", "nhìn tù vãi"), một danh từ ("Sliver rồi"), một cảm thán ("ngồi nhìn load từng giây") mà không chỉ ra máy, video hay người thì thuộc nhãn này | "@[người dùng] chưa"; "đỉnh thật"; "nhìn tù vãi"; "chỉ một từ: xấu" | "máy này đỉnh thật" → `dien_thoai`; reply "đúng rồi bạn" → `nguoi_binh_luan` | `không hiểu`, `không rõ` |

## 2. Nói về phần nào của điện thoại (nhiều nhãn)

Câu hỏi: bình luận nói về phần nào của điện thoại? Chỉ gán khi chiều 1 là `dien_thoai`. Một bình luận nói nhiều phần thì gán đủ.

Nhãn của chiều này có hai loại ([thuật ngữ](dac-ta-kham-pha-nhan.md#thuật-ngữ)): **khía cạnh** (mục 2.1) và **nhãn ngoài khía cạnh** (mục 2.2).

### 2.1 Khía cạnh

13 nhãn, và nhãn dự phòng `khac` (chưa gặp lần nào).

| Nhãn | Định nghĩa | Ví dụ thuộc | Dễ nhầm, không thuộc | Mã đã gom (ví dụ) |
|---|---|---|---|---|
| `pin_sac` | Pin, thời lượng dùng, tụt pin, sạc, củ sạc, công suất sạc | "pin trâu, dùng 2 ngày mới sạc"; "củ 67w mà sạc chậm" | "sạc một lúc là máy nóng ran" → `nhiet_do` | `pin`, `tụt pin`, `sạc nhanh`, `cục sạc 67w` |
| `man_hinh` | Màn hình: độ sáng, tần số quét, màu màn, độ phân giải, tai thỏ, lỗ khoét, lỗi màn (sọc, xanh, kẻ) | "màn 120hz lướt mượt"; "tai thỏ to quá" | "miếng dán màn bị rộp" → `phan_cung_khac` | `màn hình`, `kẻ màn`, `tai thỏ`, `viên thuốc`, `màn oled` |
| `hieu_nang` | Chip, RAM, điểm số, chơi game, độ mượt, đa nhiệm, độ ổn định | "chip này chơi game ổn"; "antutu cao mà vẫn giật" | "chơi game lâu nóng" → `nhiet_do` | `chip`, `exynos`, `ram`, `điểm antutu`, `chơi game`, `đa nhiệm` |
| `nhiet_do` | Máy nóng, quá nhiệt, tản nhiệt | "chơi game 30 phút nóng lắm"; "dùng 4G máy ấm lên" | "pin tụt nhanh" → `pin_sac` | `nóng máy`, `nhiệt độ`, `quá nhiệt` |
| `camera` | Chụp, quay, zoom, chống rung, cảm biến, màu ảnh, app camera | "chụp đêm đẹp"; "quay video rung" | "cụm camera lồi xấu" → `thiet_ke` | `camera`, `chụp đêm`, `quay phim`, `zoom`, `cảm biến` |
| `thiet_ke` | Ngoại hình, màu máy, chất liệu, trọng lượng, kích thước, viền, mặt lưng, hình dáng cụm camera. Nói một máy **đẹp, xấu** mà không chỉ phần nào cũng là ngoại hình | "màu tím đẹp"; "S24 Ultra đẹp vãi"; "nhìn xấu hơn ip11" | "rơi một lần là bung lưng" → `do_ben`; "S24 Ultra chụp đẹp" → `camera`; "27 triệu là đẹp" → `gia` | `màu máy`, `trọng lượng`, `ngoại hình`, `cụm cam to`, `khung viền titan` |
| `do_ben` | Độ bền, chống nước, rơi vỡ, bung, nứt | "rơi mấy lần vẫn không sao"; "IP68 mà vẫn vào nước" | "khung titan nhìn sang" → `thiet_ke` | `độ bền`, `kháng nước ip68`, `chống nước` |
| `phan_mem` | Hệ điều hành, giao diện, cập nhật, ứng dụng, AI, thông báo, ngôn ngữ, quảng cáo hiện trong máy | "lên bản mới bị giật"; "không có tiếng Việt" | "quảng cáo chèn trong video dài" → không gán nhãn chiều 2 (`ngu_canh`) | `hệ điều hành`, `ios`, `hyper 2`, `cập nhật`, `thông báo`, `ai trên iphone` |
| `am_thanh` | Loa, mic, thu âm, khử ồn | "loa to, rõ"; "mic thu tiếng rè" | "tai nghe tặng kèm xịn" → `phan_cung_khac` | `loa`, `mic`, `khử ồn khi thu âm` |
| `phan_cung_khac` | Bộ nhớ, SIM, 5G, wifi, rung, vân tay, Face ID, bút, cổng; phụ kiện (ốp, miếng dán, cường lực, tai nghe, đồng hồ) | "bản 128g là đủ"; "có 5G chưa anh" | "RAM 12GB chạy mượt" → `hieu_nang` | `bộ nhớ`, `5g`, `face id`, `bút s pen`, `ốp`, `dán màn hình` |
| `gia` | Giá bán, giá về Việt Nam, tiền mua máy, rớt giá, giữ giá, khuyến mãi | "về VN giá bao nhiêu"; "đắt quá, chưa có tiền" | "mua trả góp ở đâu" → `mua_ban` | `giá`, `tiền mua máy`, `giá xách tay`, `giá máy cũ` |
| `mua_ban` | Việc mua, đổi máy của người dùng: mua ở đâu, khi nào, trả góp, xách tay hay chính hãng, bán máy cũ, lên đời sang máy khác, bản theo thị trường. Nói đời máy mới **nâng cấp gì** so với đời trước thì là `may_chung` (sửa 26/11, vì κ lô K 0,57). **Ý định mua, chọn mua** ("chắc chắn lấy Oppo", "chắc mua lấy le", "đợi giảm giá rồi mua") cũng là `mua_ban` (thêm 26/11, sau lô D2) | "mua chỗ nào uy tín"; "xách tay hay chính hãng thì hơn" | "nên mua con nào" → `may_chung` | `chỗ mua`, `trả góp`, `xách tay`, `thời điểm mua`, `bản mỹ` |
| `bao_hanh_sua_chua` | Bảo hành, sửa chữa, thay linh kiện, đổi trả, hoàn tiền | "thay màn hết mấy triệu"; "có được đổi trả không" | "giá máy chính hãng" → `gia` | `bảo hành`, `thay màn`, `đổi trả`, `cách sửa` |
| `khac` | Phần của điện thoại chưa có ở trên | Chưa gặp trong lô 1–5 | | |

### 2.2 Ngoài khía cạnh

2 nhãn. Bình luận nói về điện thoại mà **không nêu phần nào** của nó: nói cả máy, hay nói về hãng và người dùng. Hai nhãn này vẫn có thái độ ở chiều 4, nhưng **không gọi là khía cạnh**.

| Nhãn | Định nghĩa | Ví dụ thuộc | Dễ nhầm, không thuộc | Mã đã gom (ví dụ) |
|---|---|---|---|---|
| `may_chung` | Nói về cả máy mà không nêu phần nào: máy nên mua, đời máy, nâng cấp, trải nghiệm chung, gọi tên máy | "S24 Ultra ngon, đỉnh"; "nên mua con nào giờ" | "S24 Ultra đẹp vãi" → `thiet_ke`; "đẹp quá" (không rõ cái gì) → chiều 1 `khong_xac_dinh` | `máy (chung)`, `máy nên mua`, `nâng cấp`, tên máy (`s23u`, `14prm`) |
| `hang_nguoi_dung` | Hãng nói chung, thương hiệu, fan, nhóm người mua, chuyện công ty. Không tách hãng và fan | "Xiaomi đỉnh thật"; "fan táo lại cay rồi" | "Xiaomi 14 ngon" (gọi tên một máy) → `may_chung` | `samsung (chung)`, `fan iphone`, `thương hiệu`, `người mua`, `máy trung quốc` |

## 3. Mục đích (nhiều nhãn)

Câu hỏi: người viết bình luận để làm gì? Suy từ **hành vi** của mã ([bảng hành vi](huong-dan-kham-pha-nhan.md#bảng-hành-vi)). Ánh xạ đóng: mỗi hành vi thuộc đúng một mục đích.

| Nhãn | Hành vi gom vào | Ví dụ thuộc | Dễ nhầm, không thuộc |
|---|---|---|---|
| `danh_gia` | `khen`, `chê`, `nhận xét`, `so sánh`, `dự đoán` | "pin trâu, cam đêm hơi nhòe"; "chắc về VN giá gấp đôi" | "giá về VN bao nhiêu" → `hoi` |
| `hoi` | `hỏi` (kể cả xin link) | "có bản 5G chưa"; "ai cho xin link mua" | "chỗ mua uy tín là X nhé" (trả lời) → `thong_tin` |
| `thong_tin` | `giải thích`, `trả lời`, `nhắc` | "xách tay nên không có bảo hành hãng"; "ngày 23 ra mắt bạn ạ" | "đúng rồi bạn" (chỉ đồng ý) → `tranh_luan` |
| `de_nghi` | `khuyên`, `góp ý`, `yêu cầu` | "đi đường dài thì chọn iPhone"; "anh test thử dưới nước đi" | "mình đang định mua" → `ban_than` |
| `ban_than` | `kể`, `khoe`, `than`, `mong muốn` (cả định mua), `lo ngại` | "cuối năm lên 16 pro max"; "chưa có lúa để mua" | "máy mình bị sọc màn" → `bao_loi` |
| `bao_loi` | `báo lỗi`: lỗi, hỏng hóc của máy mình hay người nhà đang dùng | "máy tao xanh màn, đang chờ bảo hành"; "lên bản mới tụt pin nhanh" | "nghe nói máy này hay lỗi" (không phải máy mình) → `danh_gia` |
| `tranh_luan` | `đồng tình`, `phản bác`, `bênh`, `cãi nhau`. **Giữ luật (26/11, sau lô D2):** chỉ gán khi có chữ tỏ đồng ý hay phản đối ("đúng", "chuẩn", "công nhận", "sai", "không phải", "chưa chắc", "làm gì có", "thì sao"). Reply nói khác ý cha mà không có chữ đó thì gán theo nội dung (`thong_tin`, `danh_gia`…) | "chuẩn, mình cũng thấy vậy"; "chưa chắc đâu, bản nội địa còn mạnh hơn" | "fan táo cay rồi" (khích) → `cong_kich` |
| `dua` | `đùa`, `trêu`. **Sửa 26/11:** chỉ gán khi câu **cố ý gây cười**: chơi chữ ("Ốc pồ"), nói quá, ví von để cười, đặt biệt danh, kể chuyện để cười. Emoji cười, ":))" một mình **không đủ**. Câu có ý chính khác (đánh giá, kể, đề nghị) mà có thêm ý đùa rõ thì gán cả hai | "màu này hợp rơi tự do"; "ông hoàng phá máy"; "sang năm bảo đảm dời nút xuống 1cm, hốt tiền nâng cấp" (cùng `danh_gia`) | "nhận tiền nên khen" (mỉa người review) → `cong_kich`; "đố anh trên tay được máy Việt nào" (thách người review làm gì) → `de_nghi`; "pin trâu :))" → chỉ `danh_gia` |
| `cong_kich` | `cà khịa`, `chửi` | "fan táo lúc nào cũng vậy"; "suy nghĩ chẳng ra gì" | "trêu anh review tí thôi" → `dua` |
| `minigame` | `dự thi`, `xin` (quà, máy) | "đáp án C, số may mắn 123"; "cho em xin một suất" | "cảm ơn anh vì minigame" → `xa_giao` |
| `quang_cao` | `quảng cáo`, `mời` (liên hệ ngoài) | "lên đời trợ giá 5 triệu, link…"; "ib zalo nhận máy free" | "mua ở cửa hàng X rẻ hơn" (người dùng chỉ chỗ) → `thong_tin` |
| `xa_giao` | `chào`, `cảm ơn`, `cười` | "cảm ơn anh"; "=)))" | "cảm ơn, nhưng pin yếu quá" → thêm cả `danh_gia` |
| `khong_xac_dinh` | `không hiểu: ?` | "ao"; "@[người dùng] bup" | |

## 4. Thái độ (nhiều nhãn, theo từng nhãn chiều 2)

Câu hỏi: với mỗi nhãn chiều 2 của bình luận (khía cạnh, và cả `may_chung`, `hang_nguoi_dung`), người viết nghĩ tốt hay xấu? Gán cho từng cặp (bình luận, nhãn chiều 2). Một bình luận có thể khen camera chụp ngày, chê camera chụp đêm: cặp `camera` có cả hai.

| Nhãn | Định nghĩa | Ví dụ thuộc | Dễ nhầm, không thuộc |
|---|---|---|---|
| `tich_cuc` | Khen (`khen`) | "pin trâu" | "pin trâu hơn iPhone" → `so_sanh` |
| `tieu_cuc` | Chê (`chê`), hay báo lỗi (`báo lỗi`) | "máy nặng quá"; "máy mình sọc màn" | "pin hơi yếu nhưng chấp nhận được" → vẫn `tieu_cuc` |
| `so_sanh` | So với máy khác (`so sánh`); bên hơn ghi trong ghi chú | "pin S26U trâu hơn iPhone 17" | "pin trâu, iPhone cũng vậy" (không nói bên nào hơn) → `tich_cuc` |
| `khong_danh_gia` | Hỏi, nhắc, giải thích… về phần đó mà không nói tốt hay xấu. Cà khịa, bênh một hãng hay nhóm người mà không kèm lời khen, chê thì cũng ở đây | "pin bao nhiêu mAh vậy" | "pin được bao lâu, chắc yếu" → `tieu_cuc` |

## 5. Đã dùng máy (một nhãn)

Câu hỏi: người viết (hay người nhà) có đang dùng, đã dùng máy mình nói tới không? Phục vụ Q5 ("người đã dùng X báo lỗi gì"). Trưởng nhóm quyết giữ chiều này ngày 23/11.

| Nhãn | Định nghĩa | Ví dụ thuộc | Dễ nhầm, không thuộc |
|---|---|---|---|
| `co` | Bình luận nói rõ là máy của mình hay người nhà: "máy mình", "đang xài", "mua về", "dùng 2 năm" | "đang xài S23U, pin ổn"; "con em mua chưa được tháng đã chết màn" | "nghe bạn bảo máy này nóng" → `khong_ro` |
| `khong_ro` | Không nói rõ | "pin máy này yếu" | |

Ở B5, chiều này đếm gần đúng từ mã của A, vì mã tự do không ghi đủ (hành vi `kể`, `báo lỗi`, hay ghi chú "đã dùng"). Ở B7 gán lại từ chữ bình luận.

## 6. Máy được nhắc (một nhãn)

Câu hỏi: bình luận có gọi tên máy cụ thể không? Để biết nhãn ở chiều 2–5 thuộc về máy nào. Không suy tên máy từ video.

**Trường `ten_may` (thêm 26/11, cho Q3, Q4):** khi chiều 6 là `goi_ten_may`, ghi **mọi máy được gọi tên**, cách nhau bằng `;`, theo mã máy trong danh mục (trường `name` của `config/pipeline.yaml`, vd `s24u`, `ip15prm`, `xiaomi14`). Máy không có trong danh mục thì ghi tên như bình luận viết, chữ thường. Nhãn khác `goi_ten_may` thì để trống. Trường này **chưa** ghi nhận xét nào thuộc máy nào; nối từng khía cạnh với máy là việc của guideline gán chính thức.

| Nhãn | Định nghĩa | Ví dụ thuộc | Dễ nhầm, không thuộc |
|---|---|---|---|
| `goi_ten_may` | Có tên một máy cụ thể: hãng hay dòng kèm số đời ("S23U", "14 pro max", "Note 10", "Redmi Note 13 Pro") | "S24 Ultra đẹp" | "Samsung đẹp" → `chi_hang` |
| `chi_hang` | Chỉ nhắc hãng hay dòng chung, không có đời máy ("Samsung", "iPhone", "Xiaomi") | "iPhone giữ giá hơn" | "iPhone 15 giữ giá" → `goi_ten_may` |
| `khong_nhac` | Không nhắc máy hay hãng nào ("con này", "máy này") | "con này pin trâu" | |

Ở B5, chiều này cũng đếm gần đúng từ mã (đối tượng và ghi chú phụ).

## 7. Trưởng nhóm đã quyết khi duyệt (25/11)

1. **Nhãn hiếm:** để riêng tới B8 (`nhiet_do`, `bao_hanh_sua_chua`, `bao_loi`, `quang_cao`, `khong_lien_quan`, `khong_noi_dung`). Gộp về sau thì chỉ cần đổi tên nhãn; gộp bây giờ mà sau mới muốn tách thì phải gán lại cả mẫu.
2. **`hang_nguoi_dung`:** không tách hãng và fan. Đề tài nói về máy, không nói về hãng.
3. **Bài test trong video:** giữ `ngu_canh`, không gán thêm khía cạnh.
4. **`dua` và `cong_kich`:** tách, để sau lọc bình luận độc hại.
5. **Cà khịa hãng, fan** ("fan iPhone lỏ"): không tính là chê, giữ `khong_danh_gia`, vì nhắm vào người, không vào máy.
6. **Máy tính bảng:** không tính là `dien_thoai`, xếp `khong_lien_quan`.
7. **"Đẹp", "xấu":** xem chữ đó tả cái gì (máy, ảnh chụp, màn, giá). Nói một máy đẹp hay xấu mà không chỉ phần nào thì là `thiet_ke`; nói "ngon", "đỉnh", "tốt" thì là `may_chung`.


**Sau khi so lô K (26/11):**

8. **Câu mẫu dự minigame** (câu viết theo mẫu kèm số may mắn, đáp án, hashtag) là `ngu_canh` với mục đích `minigame`, **kể cả khi câu mẫu khen một tính năng máy** ("Mình thích màn hình 120Hz, SMM 572"). Không gán chiều 2, 4: câu mẫu không phải ý kiến thật.
9. **Yêu cầu làm bài test kèm một thông tin hay nhận xét riêng về máy** ("test xuất màn hình đi, con này USB 3.0 xuất được HDMI") là `dien_thoai`, gán nhãn chiều 2 của phần đó, mục đích có `de_nghi`. Chỉ yêu cầu test, không nói gì về máy, thì vẫn `ngu_canh` (điều 3). **Làm rõ 26/11 (sau lô D2):** chỉ **nêu tên** máy, chip hay phần cần test ("thử với snap650 đi", "thách drop test doogee s98") chưa phải thông tin về máy, vẫn là `ngu_canh`; phải có một nhận xét hay một thông tin về máy đó ("con này USB 3.0 xuất được HDMI") mới là `dien_thoai`.

**Ánh xạ mã cũ không theo hết được điều 7:** mã `s24 ultra: khen` không ghi là khen đẹp hay khen ngon, nên `label_set.py` vẫn xếp `may_chung`. Nhãn B7 gán từ chữ bình luận nên theo đúng điều 7.

## 8. Bộ nhãn chốt (B8, 26/11)

Trưởng nhóm duyệt đề xuất ở [báo cáo khám phá nhãn](bao-cao-kham-pha-nhan.md) ngày 26/11. Luật quyết: [đặc tả khám phá nhãn mục 9](dac-ta-kham-pha-nhan.md#9-so-ba-nguồn-và-chốt-bộ-nhãn-b8). Tỷ lệ, kappa và lý do từng nhãn nằm trong báo cáo đó, file này không chép số.

**Gộp** (nhãn cũ → nhãn chốt; code đổi theo bảng `GOP` trong `src/labeling/b8.py`):

| Nhãn khám phá | Gộp vào | Định nghĩa nhãn chốt thêm |
|---|---|---|
| `nhiet_do` | `hieu_nang` | máy nóng, quá nhiệt, tản nhiệt (như bộ đặt sẵn "Hiệu năng, gồm nóng máy") |
| `am_thanh` | `phan_cung_khac` | loa, mic, thu âm, khử ồn |
| `khong_noi_dung` | `khong_xac_dinh` (chiều 1) | bình luận chỉ có emoji, dấu câu, tiếng cười; code nhận ra được |
| Spam đặt sẵn "lừa đảo, cờ bạc" | `quang_cao` | lừa đảo, cờ bạc, kiếm tiền online |

**Các nhãn còn lại giữ hay thêm, không đổi tên.** `mua_ban` được thêm, định nghĩa sửa ở mục 2.1.

**Bộ nhãn chốt:**

| Chiều | Nhãn |
|---|---|
| 1. Liên quan tới gì (một) | `dien_thoai` · `ngu_canh` · `nguoi_binh_luan` · `khong_lien_quan` · `khong_xac_dinh` |
| 2. Nói về phần nào (nhiều): 11 khía cạnh | `pin_sac` · `man_hinh` · `hieu_nang` · `camera` · `thiet_ke` · `do_ben` · `phan_mem` · `phan_cung_khac` · `gia` · `mua_ban` · `bao_hanh_sua_chua` |
| 2. Nói về phần nào: ngoài khía cạnh, dự phòng | `may_chung` · `hang_nguoi_dung` · `khac` |
| 3. Mục đích (nhiều) | `danh_gia` · `hoi` · `thong_tin` · `de_nghi` · `ban_than` · `bao_loi` · `tranh_luan` · `dua` · `cong_kich` · `minigame` · `quang_cao` · `xa_giao` · `khong_xac_dinh` |
| 4. Thái độ (theo cặp) | `tich_cuc` · `tieu_cuc` · `so_sanh` · `khong_danh_gia` |
| 5. Đã dùng máy (một) | `co` · `khong_ro` |
| 6. Máy được nhắc (một) | `goi_ten_may` · `chi_hang` · `khong_nhac` |

**Nhãn đặt sẵn không đưa vào:** "spam khác", "chưa dùng" (gộp vào `khong_ro`), "chỉ suy được máy từ video" (trái quy tắc gán theo chữ viết). **9 loại lỗi** để tầng sau: mẫu 600 chỉ có 8 bình luận `bao_loi`, nên gán loại lỗi trên một mẫu riêng các bình luận báo lỗi.

**Phải làm trước khi gán chính thức:**
- Sửa định nghĩa `dua` và `khong_xac_dinh` (chiều 1): κ lô K 0,42 và gần 0. **Đã sửa 26/11** (mục 1, 3), theo các ca lệch ở lô K. `mua_ban` đã sửa ở mục 2.1. **Đã kiểm lại trên 50 bình luận lô D2 (26/11, [báo cáo](bao-cao-lo-d2.md)):** mọi chiều đạt κ ≥ 0,6 (chiều 1: 0,66). `khong_xac_dinh` chiều 1 lên 0,78 (lô K gần 0); `dua` 0,66 nhưng chỉ 1–2 ca. Lô D2 lộ ba chỗ còn lệch; trưởng nhóm quyết 26/11 theo đề xuất: luật 9 làm rõ (chỉ nêu tên máy, chip khi yêu cầu test vẫn là `ngu_canh`); `tranh_luan` giữ luật phải có chữ tỏ thái độ; ý định mua là `mua_ban`.
- Thêm trường **tên máy** cho chiều 6. **Đã thêm 26/11** (`ten_may`, mục 6); thử lần đầu ở lô D2. Nối từng khía cạnh với máy (Q3) còn chờ guideline gán chính thức.

### 8.1 Cách ghi nhãn khi gán chính thức (trưởng nhóm duyệt 26/11)

Ba điểm bộ nhãn khám phá không cần nhưng gán chính thức cần, để tổng hợp theo máy và lọc dữ liệu. **Nhánh này chỉ quy định cách ghi; code đọc và kiểm phiếu là việc của nhánh gán nhãn.**

1. **Nối nhận xét với máy.** Bình luận gọi tên **từ hai máy trở lên** thì mỗi nhãn chiều 2 ghi thêm `@` và mã máy: `camera:tich_cuc@s24u; pin_sac:tieu_cuc@ip15prm` (viết tắt `cam+@s24u, pin-@ip15prm`). Mã sau `@` phải có trong `ten_may`. Gọi tên **một máy** thì không cần `@`: mọi nhãn chiều 2 thuộc máy đó. **Không gọi tên máy nào** (`may_nhac` là `khong_nhac` hay `chi_hang`) thì không ghi máy và không đoán theo video; lúc phân tích, nhóm quyết có coi là máy của video hay không.
2. **So sánh ghi bên hơn.** Thái độ `so_sanh` có hai máy thì ghi máy hơn đứng trước: `pin_sac:so_sanh@s24u>ip15prm`; ngang nhau thì dùng `~`: `@s24u~ip15prm`. Không ghi bên hơn ở `ghi_chu` nữa.
3. **Cờ tiếng Việt.** Thêm cột `tieng_viet`: `co` hay `khong`, gán trước chiều 1. Bình luận không phải tiếng Việt vẫn gán đủ các chiều nếu hiểu được.

**Để sau:** loại lỗi (cho Q5). Mẫu 600 chỉ có 8 bình luận `bao_loi`, chưa chia loại được; làm trên một mẫu riêng các bình luận báo lỗi, bằng mã hóa mở như B4–B5.

**Bỏ so với guideline v1 trên `main`:** số mệnh đề bằng chứng, và mã `video` ở cột máy (thay bằng điểm 1).

## 9. Hạn chế

- **Mỏ neo:** người gom (Claude) đã soạn bộ nhãn đặt sẵn trên `main`, nên chiều 2 có thể bị nó dẫn dắt. Ba nhãn không có trong bộ đặt sẵn (`mua_ban`, `hang_nguoi_dung`, `may_chung`), và `nhiet_do`, `am_thanh`, `do_ben` được tách khỏi nhóm đặt sẵn. Việc so với bộ đặt sẵn để ở B8.
- **Số đếm từ mã của A,** do AI mã, chưa ai kiểm từng mã. Ánh xạ là luật từ khóa nên có thể xếp nhầm vài mã.
- **Độ phủ trên phiếu B:** áp cùng ánh xạ cho mã của trưởng nhóm thì 36/797 mã chưa xếp được (xem [báo cáo](bao-cao-bo-nhan.md) mục 8). Phần lớn là từ đồng nghĩa của nhãn đã có: "tản nhiệt" → `nhiet_do`, "tần số quét" → `man_hinh`, "trang phục reviewer" → `ngu_canh`, "chính trị" → `khong_lien_quan`. Không thấy loại nội dung nào bộ nhãn thiếu.
- **Chiều 5, 6** đếm gần đúng ở B5. Số thật chỉ có ở B7.

## 10. Sau khi duyệt

- **B6:** A và B gán mù lô K theo bộ nhãn này, mỗi chiều một cột ([guideline mục 5](huong-dan-kham-pha-nhan.md#5-gán-mù-lô-k-b6)). Phiếu lô K có sẵn cột cho từng chiều ([đặc tả khám phá nhãn mục 3.5](dac-ta-kham-pha-nhan.md#35-phiếu-mã-hóa)).
- **B7:** A gán lại 600 bình luận theo bộ nhãn, B kiểm, rồi tính phân bố.

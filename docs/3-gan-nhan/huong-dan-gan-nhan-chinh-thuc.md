# Hướng dẫn gán nhãn chính thức

> Mục đích: Cách gán một bình luận theo bộ nhãn chốt (B8): thứ tự quyết, bảng tra nhanh, từng chiều, ví dụ đủ cột, lỗi hay gặp rút từ lô K, lô D2 và B7; cách ghi máy, so sánh, cờ tiếng Việt ở mục 9; cập nhật lần cuối: 2026-11-26.

**Trạng thái:** trưởng nhóm duyệt ngày 26/11, cả mục 9. Đây là đầu ra của nhánh khám phá nhãn để bàn giao; việc gán nhãn, kiểm phiếu bằng code và mô hình làm ở nhánh khác.

**Phạm vi:**
- **Định nghĩa nhãn nằm ở [đặc tả bộ nhãn](dac-ta-bo-nhan.md) (nguồn chân lý)**, nhất là mục 7 (các luật đã quyết) và mục 8 (bộ nhãn chốt). File này chỉ nói cách làm. Hai file lệch nhau thì theo đặc tả, rồi báo lại.
- Lấy mẫu nào, ai gán, gán đôi, phân xử: theo đặc tả gán nhãn trên `main` (`docs/3-gan-nhan/dac-ta.md`), file này không chép lại.
- Khi chép về `main`, file này đề xuất **thay** guideline v1 (`huong-dan-gan-nhan-binh-luan.md`). Nhóm quyết.
- Ví dụ trong file đều tự soạn, không chép bình luận thật.

## 1. Gán một bình luận: thứ tự quyết

1. **Đọc bình luận.** Là reply thì đọc thêm bình luận cha, **chỉ để hiểu** "nó", "cái đó", "con số đó". Nhãn là của chính bình luận: lời khen, chê, so sánh nằm ở bình luận cha thì không tính cho bình luận con.
2. **Chiều 1** (một nhãn): bình luận nói về cái gì? Xét theo thứ tự ở mục 3, gặp cái đúng đầu tiên thì dừng.
3. **Chiều 2 và 4** (chỉ khi chiều 1 là `D`): nói về phần nào của máy, và với từng phần đó thì khen, chê, so sánh hay không đánh giá.
4. **Chiều 3** (nhiều nhãn): người viết viết để làm gì.
5. **Chiều 5:** người viết có nói rõ là máy của mình (hay người nhà) không.
6. **Chiều 6 và `ten_may`:** có gọi tên máy cụ thể không; có thì ghi tên máy.
7. **Chưa chắc chiều nào** thì ghi số chiều vào `chua_chac`, lý do vào `ghi_chu`. Đừng bỏ trống để "tính sau".

**Hai quy tắc chung:**
- **Gán theo chữ viết, không đoán.** Không suy từ tên video, không suy từ chuyện hay gặp.
- **Mỉa mai rõ thì gán theo nghĩa thật**: "tuyệt vời, 3 tiếng hết pin" là chê pin.

## 2. Bảng tra nhanh

Gõ chữ viết tắt hay tên đầy đủ đều được, chữ hoa hay thường đều được.

| Cột | Một hay nhiều | Viết tắt |
|---|---|---|
| `lien_quan` (chiều 1) | một | `D` điện thoại · `N` video, kênh, minigame · `B` người bình luận khác · `L` không liên quan · `X` không xác định |
| `noi_ve_thai_do` (chiều 2 và 4) | nhiều | Phần nói tới viết liền với thái độ: `+` khen · `-` chê · `=` so sánh · `0` không đánh giá. Ví dụ `cam+-, gia0` |
| `muc_dich` (chiều 3) | nhiều | `dg` đánh giá · `hoi` hỏi · `tt` thông tin · `dn` đề nghị · `bt` bản thân · `bl` báo lỗi · `tl` tranh luận · `dua` đùa · `ck` công kích · `mg` minigame · `qc` quảng cáo, lừa đảo · `xg` xã giao · `x` không xác định |
| `da_dung` (chiều 5) | một | `c` nói rõ đã dùng · `k` không rõ |
| `may_nhac` (chiều 6) | một | `t` gọi tên máy · `h` chỉ nhắc hãng, dòng · `k` không nhắc |
| `ten_may` | nhiều | Mã máy, cách nhau bằng `;`. Chỉ điền khi `may_nhac` là `t` |

**Phần nói tới (chiều 2):**

| Viết tắt | Nhãn | Gồm |
|---|---|---|
| `pin` | `pin_sac` | pin, thời lượng, tụt pin, sạc, củ sạc |
| `man` | `man_hinh` | màn hình, tần số quét, độ sáng, tai thỏ, lỗ khoét, lỗi màn |
| `hn` | `hieu_nang` | chip, RAM, điểm số, game, độ mượt, đa nhiệm, **nóng máy, tản nhiệt** |
| `cam` | `camera` | chụp, quay, zoom, chống rung, màu ảnh, app camera |
| `tk` | `thiet_ke` | ngoại hình, màu máy, chất liệu, trọng lượng, kích thước; **máy đẹp, xấu nói chung** |
| `db` | `do_ben` | độ bền, rơi vỡ, chống nước, bung, nứt |
| `pm` | `phan_mem` | hệ điều hành, giao diện, cập nhật, ứng dụng, AI, thông báo, bản đồ |
| `pc` | `phan_cung_khac` | bộ nhớ, SIM, 5G, wifi, vân tay, Face ID, bút, cổng, **loa, mic**, phụ kiện |
| `gia` | `gia` | giá bán, giá về Việt Nam, giữ giá, rớt giá, khuyến mãi |
| `mua` | `mua_ban` | mua ở đâu, khi nào, trả góp, xách tay, bán máy cũ, lên đời, **ý định mua** |
| `bh` | `bao_hanh_sua_chua` | bảo hành, sửa chữa, thay linh kiện, đổi trả |
| `mc` | `may_chung` | cả máy, không nêu phần nào ("ngon", "đỉnh"); máy nên mua; đời mới nâng cấp gì |
| `hang` | `hang_nguoi_dung` | hãng, thương hiệu, fan, nhóm người mua |
| `khac` | `khac` | phần của máy chưa có ở trên (rất hiếm; ghi rõ ở `ghi_chu`) |

## 3. Chiều 1: nói về cái gì

Xét theo thứ tự, gặp cái đúng đầu tiên thì dừng.

| Thứ tự | Nhãn | Khi nào |
|---|---|---|
| 1 | `D` `dien_thoai` | Có ít nhất một ý về điện thoại, tức là gán được ít nhất một nhãn chiều 2 |
| 2 | `N` `ngu_canh` | Nói về video, người làm video, người trong video, bài test trong video, minigame, quà |
| 3 | `B` `nguoi_binh_luan` | Chỉ nói với hay về một người bình luận khác (đồng ý, cãi, chửi), không có ý về máy |
| 4 | `L` `khong_lien_quan` | Chính trị, lịch sử, chuyện đời; **máy tính bảng, máy tính** |
| 5 | `X` `khong_xac_dinh` | Không biết nói về cái gì; chỉ có emoji, dấu câu, tiếng cười |

**Phép thử cho `X`:** tự hỏi "bình luận nói về cái gì?". Nếu câu trả lời không nằm trong chữ của bình luận (hay của bình luận cha, khi bình luận này nói tiếp đúng chuyện đó) thì là `X`.

**Ba bẫy hay gặp:**

| Bẫy | Ví dụ tự soạn | Đúng | Sai hay gặp |
|---|---|---|---|
| Reply chỉ đồng ý hay cãi, cha nói về máy | cha: "pin máy này trâu"; con: "chuẩn bạn ơi" | `B`, mục đích `tl` | `D` vì lấy chủ đề của cha. **Lỗi nhiều nhất của B7** |
| Câu cụt, không rõ đối tượng | "nhìn chán thật"; "chỉ một từ: xấu" | `X` | `D` vì đoán là nói về máy |
| Yêu cầu test chỉ nêu tên cái cần test | "thử với chip X đi anh"; "thách drop test máy Y" | `N`, `dn` | `D`. Phải có nhận xét hay thông tin về máy mới là `D` ("test xuất màn hình đi, con này xuất được HDMI") |

**Thêm:**
- **Câu mẫu dự minigame**, kể cả khi khen tính năng máy ("Mình thích màn 120Hz, số may mắn 123"), là `N` với `mg`. Không gán chiều 2 và 4.
- **Bài test trong video** ("test pin kiểu này không thực tế") là `N`, không gán khía cạnh.

## 4. Chiều 2 và 4: phần nào, thái độ ra sao

**Chiều 2:**
- **Gán đủ mọi phần bình luận tự nói tới**, mỗi phần một nhãn.
- **Phần chỉ nêu làm lý do hay ví dụ thì không tách.** "Chip mạnh lên, RAM khan hiếm nên giá tăng" chỉ là `gia`.
- **"Đẹp", "xấu":** xem chữ đó tả cái gì. "Máy này đẹp" là `tk`, "chụp đẹp" là `cam`, "giá này đẹp" là `gia`. Nói "ngon", "đỉnh", "tốt" mà không nêu phần nào thì là `mc`.
- **`mua` hay `mc`:** việc mua hay đổi máy của người dùng (chỗ mua, lúc mua, lên đời, định mua) là `mua`. Đời máy mới **nâng cấp gì** so với đời trước là `mc`.
- **`hang` hay `mc`:** nói hãng, fan, người mua nói chung là `hang`. Gọi một máy cụ thể là `mc` (hay phần cụ thể của nó).

**Chiều 4** (cho từng nhãn chiều 2):

| Ký hiệu | Khi nào | Không phải |
|---|---|---|
| `+` khen | Nói phần đó tốt, kể cả nói nhẹ | |
| `-` chê | Nói phần đó xấu; báo lỗi | "pin hơi yếu nhưng chấp nhận được" vẫn là `-` |
| `=` so sánh | So với máy khác và **nói rõ bên nào hơn**; ghi bên hơn ở `ghi_chu` | "pin trâu, iPhone cũng vậy" (không nói bên nào hơn) là `+` |
| `0` không đánh giá | Hỏi, nhắc, giải thích, dự đoán mà không nói tốt xấu; **cà khịa, bênh hãng mà không có lời khen chê** | "pin được bao lâu, chắc yếu" là `-` |

Một phần vừa khen vừa chê ("cam ngày đẹp, đêm kém") thì ghi cả hai: `cam+-`.

## 5. Chiều 3: viết để làm gì

Nhiều nhãn. Gán mọi mục đích có trong bình luận.

| Nhãn | Khi nào | Bẫy |
|---|---|---|
| `dg` đánh giá | Khen, chê, nhận xét, so sánh, dự đoán | Không gán chỉ vì có tên máy. Câu chỉ hỏi thì là `hoi` |
| `hoi` | Hỏi thông tin, xin link | |
| `tt` thông tin | Giải thích, trả lời câu hỏi, nhắc thông tin | |
| `dn` đề nghị | Khuyên, góp ý, yêu cầu, **thách người review làm gì** | Thách người review không phải `dua` |
| `bt` bản thân | Kể chuyện mình, khoe, than, mong muốn, định mua, lo ngại | Kể để khen chê thì chỉ `dg`. Lỗi máy của mình thì `bl` |
| `bl` báo lỗi | Lỗi, hỏng hóc của máy mình hay người nhà | Nghe nói máy hay lỗi thì là `dg` |
| `tl` tranh luận | Đồng ý, phản bác, bênh, cãi. **Phải có chữ tỏ thái độ**: "đúng", "chuẩn", "công nhận", "sai", "không phải", "chưa chắc", "làm gì có", "thì sao" | Nói khác ý cha mà không có chữ đó thì gán theo nội dung (`tt`, `dg`) |
| `dua` đùa | **Cố ý gây cười**: chơi chữ, nói quá, ví von, đặt biệt danh, kể để cười | Emoji cười hay ":))" một mình không đủ. Có ý chính khác thì gán cả hai |
| `ck` công kích | Cà khịa, chửi, mỉa nhắm vào người, nhóm người | Trêu nhẹ, vô hại thì là `dua` |
| `mg` minigame | Dự thi, xin quà, xin suất | Cảm ơn vì minigame thì là `xg` |
| `qc` quảng cáo | Quảng cáo bán hàng, mời liên hệ ngoài, **lừa đảo, cờ bạc, kiếm tiền online** | Người dùng chỉ chỗ mua rẻ thì là `tt` |
| `xg` xã giao | Chào, cảm ơn, chúc, chỉ cười | |
| `x` không xác định | Không hiểu viết để làm gì | |

## 6. Chiều 5, 6 và tên máy

**Chiều 5 `da_dung`:**
- `c` khi bình luận **nói rõ** là máy của mình hay người nhà: "máy mình", "đang xài", "mua về", "dùng 2 năm".
- Còn lại là `k`, kể cả khi đoán được người viết có dùng.

**Chiều 6 `may_nhac`:**

| Nhãn | Khi nào | Ví dụ |
|---|---|---|
| `t` | Có tên một máy cụ thể: hãng hay dòng **kèm số đời** | "S24 Ultra", "14 pro max", "Note 10", "Redmi Note 13 Pro" |
| `h` | Chỉ hãng hay dòng chung, không có đời | "Samsung", "iPhone", "dòng Pro Max", "Redmi" |
| `k` | Không nhắc máy hay hãng nào | "con này", "máy này" |

**`ten_may`:**
- Khi `may_nhac` là `t`, ghi **mọi máy được gọi tên**, cách nhau bằng `;`.
- Dùng mã trong danh mục, là trường `name` của `config/pipeline.yaml` (vd `s24u`, `ip15prm`, `note10plus`, `xiaomi14`). Máy không có trong danh mục thì ghi tên như bình luận viết, chữ thường.
- **Không suy tên máy từ video.**
- Ở lô D2, hai người chỉ khớp tên máy 9/12 lần, phần lớn do cách viết khác nhau ("note20ultra" với `note20u`). Vì vậy **chọn mã từ danh sách**, đừng gõ tự do (mục 10).

## 7. Ví dụ đủ cột

Đều tự soạn. Cột theo thứ tự: `lien_quan` | `noi_ve_thai_do` | `muc_dich` | `da_dung` | `may_nhac` | `ten_may`.

| Bình luận | Nhãn | Vì sao |
|---|---|---|
| "S24 Ultra chụp đêm đẹp nhưng giá chát quá" | `D` \| `cam+, gia-` \| `dg` \| `k` \| `t` \| `s24u` | Hai phần, hai thái độ |
| "pin S24U trâu hơn ip15 pro max nhiều" | `D` \| `pin=` \| `dg` \| `k` \| `t` \| `s24u; ip15prm` | So sánh có bên hơn; ghi "s24u hơn" ở `ghi_chu` |
| "máy mình dùng 2 tháng, sạc là nóng ran" | `D` \| `hn-` \| `bl` \| `c` \| `k` \| | Nóng máy thuộc `hn`; lỗi máy của mình là `bl` |
| "con này bao nhiêu tiền vậy shop" | `D` \| `gia0` \| `hoi` \| `k` \| `k` \| | Hỏi giá, không đánh giá |
| "cuối năm chắc lên đời 16 pro max" | `D` \| `mua0` \| `bt` \| `k` \| `t` \| `ip16prm` | Ý định mua, lên đời là `mua` |
| "máy này đẹp thật" | `D` \| `tk+` \| `dg` \| `k` \| `k` \| | Máy đẹp nói chung là `tk` |
| "fan táo lúc nào cũng vậy" | `D` \| `hang0` \| `ck` \| `k` \| `h` \| | Cà khịa người: thái độ `0` |
| cha: "cam máy này xấu"; con: "chuẩn, đồng ý" | `B` \| \| `tl` \| `k` \| `k` \| | Con không tự nói về máy |
| "nhìn chán ghê" | `X` \| \| `dg` \| `k` \| `k` \| | Không rõ cái gì chán |
| "anh test drop máy X đi" | `N` \| \| `dn` \| `k` \| `t` \| (mã máy X) | Yêu cầu test, chỉ nêu tên máy |
| "Mình thích camera 108MP, số may mắn 456" | `N` \| \| `mg` \| `k` \| `k` \| | Câu mẫu minigame |
| "ib zalo nhận máy free" | `N` \| \| `qc` \| `k` \| `k` \| | Quảng cáo, lừa đảo |
| "kkk =)))" | `X` \| \| `xg` \| `k` \| `k` \| | Chỉ cười |
| "tư vấn máy tính bảng tầm 5 triệu" | `L` \| \| `hoi` \| `k` \| `k` \| | Máy tính bảng là `L` |

## 8. Lỗi hay gặp

Rút từ lần kiểm B7 (500 bình luận), lô K (100) và lô D2 (50).

| Lỗi | Gặp ở | Cách tránh |
|---|---|---|
| Reply chỉ đồng ý hay cãi mà gán `D` | B7: 21 lần, lỗi nhiều nhất | Hỏi: chính bình luận này có tự nói gì về máy không? |
| Đoán đối tượng cho câu cụt | Lô K: κ `khong_xac_dinh` gần 0 | Phép thử "nói về cái gì?" (mục 3) |
| Gán `dg` thừa | B7: 12 lần | Hỏi, kể, giải thích mà không khen chê thì không phải `dg` |
| Gán `dua` vì có emoji cười | Lô K: κ 0,42 | Phải cố ý gây cười |
| Gán `tl` không có chữ tỏ thái độ | Lô D2: κ 0,26 | Phải có chữ đồng ý hay phản đối |
| Thiếu `mua` khi người viết định mua | Lô D2: κ 0,45 | Ý định mua là `mua` |
| Gán `hang`, `mc`, `pm` thừa ở chiều 2 | B7: 7–8 lần mỗi nhãn | Chỉ gán phần bình luận tự nói tới; lý do, ví dụ không tách |
| Lấy lời khen chê của cha gán cho con | Lô K | Cha chỉ để hiểu "nó", "cái đó" |
| Tên máy gõ mỗi người một kiểu | Lô D2: khớp 9/12 | Chọn mã từ danh sách |

## 9. Ghi máy, so sánh, cờ tiếng Việt (duyệt 26/11)

Luật nằm ở [đặc tả bộ nhãn mục 8.1](dac-ta-bo-nhan.md#81-cách-ghi-nhãn-khi-gán-chính-thức-trưởng-nhóm-duyệt-2611). Tóm tắt để tra:

| Trường hợp | Ghi | Ví dụ |
|---|---|---|
| Gọi tên một máy | Không cần `@` | "S24U chụp đẹp" → `cam+`, `ten_may`: `s24u` |
| Gọi tên từ hai máy | Mỗi nhãn chiều 2 thêm `@mã máy` | "cam S24U đẹp, pin ip15 yếu" → `cam+@s24u, pin-@ip15prm` |
| So sánh có bên hơn | `=@máy hơn>máy kém` | "pin S24U trâu hơn ip15" → `pin=@s24u>ip15prm` |
| So sánh ngang nhau | `=@máy~máy` | "pin hai con như nhau" → `pin=@s24u~ip15prm` |
| Không gọi tên máy nào | Không ghi máy, không đoán theo video | "con này pin trâu" → `pin+` |
| Cờ tiếng Việt | Cột `tieng_viet`: `co` hay `khong`, gán đầu tiên | "nice phone bro" → `khong` |

**Loại lỗi để sau:** chưa gán ở đợt này.

## 10. Phiếu và cách làm

**Cột người gán điền:**
- `nguoi_gan`
- `lien_quan`, `noi_ve_thai_do`, `muc_dich`, `da_dung`, `may_nhac`, `ten_may`
- `chua_chac`, `ghi_chu`
- `tieng_viet` (mục 9).

**Mở phiếu:** như [hướng dẫn gán lô K mục 2](huong-dan-gan-lo-k.md#2-mở-phiếu). Không double-click file CSV. Mở qua *Data → From Text/CSV*, chọn UTF-8 và *Do not detect data types*.

**Đề xuất cho phiếu chính thức:**
- cột `ten_may` dùng danh sách thả xuống từ danh mục máy, để tránh mỗi người gõ một kiểu;
- cột `lien_quan`, `da_dung`, `may_nhac` dùng danh sách thả xuống;
- phiếu xuất sẵn dạng `.xlsx` có các danh sách đó (người làm code tầng 3 trên `main` làm).

**Trước khi nộp, tự kiểm:**
- `lien_quan` là `D` thì phải có `noi_ve_thai_do`; khác `D` thì để trống.
- Phần nào ở `noi_ve_thai_do` cũng có ký hiệu thái độ.
- `muc_dich` không trống; nhiều mục đích cách nhau bằng dấu phẩy.
- `may_nhac` là `t` thì phải có `ten_may`; khác `t` thì để trống.
- Dòng có `bl` thì xem lại `da_dung`: thường là `c`.

**Gán đôi:** hai người gán độc lập, không bàn với nhau trước khi nộp. Ca lệch do người thứ ba phân xử, theo đặc tả gán nhãn trên `main`.

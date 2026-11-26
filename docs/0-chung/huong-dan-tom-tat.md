# Tóm tắt nhánh khám phá nhãn: từ lúc có dữ liệu tới giờ

> Mục đích: Giải thích dễ hiểu nhánh `kham-pha-nhan` đã làm gì, vì sao, đang ở đâu, việc tiếp theo; cho trưởng nhóm và thành viên mới đọc trước khi vào đặc tả; cập nhật lần cuối: 2026-11-24.

Chi tiết luật nằm ở [đặc tả khám phá nhãn](../3-gan-nhan/dac-ta-kham-pha-nhan.md). File này chỉ kể lại cho dễ hiểu, không thay đặc tả.

## 1. Nhánh này để làm gì

Đề tài muốn trả lời các câu như: người Việt khen chê gì ở điện thoại mới ra mắt, người đã dùng máy báo lỗi gì (Q1–Q6, [kế hoạch mục 6](ke-hoach-kham-pha-nhan.md#6-câu-hỏi-của-đề-tài-tóm-tắt)).

Có 473.786 bình luận, không ai đọc hết được. Phải cho máy (mô hình, LLM) **gán nhãn** cho từng bình luận, ví dụ "nói về pin, chê". Nhưng muốn máy gán nhãn thì trước hết phải có **bộ nhãn**: danh sách nhãn, mỗi nhãn có định nghĩa rõ.

Trên `main` đã có một bộ nhãn, do người nghĩ ra trước (9 khía cạnh: pin, màn hình, camera…). Đó mới là **giả định**: chưa ai kiểm xem dữ liệu thật có đúng những loại đó không, có thiếu loại nào không.

**Nhánh này đi tìm bộ nhãn từ chính dữ liệu**, rồi so với bộ giả định. **Khía cạnh là phần chính của bộ nhãn:** phần lớn nhãn của chiều 2 là khía cạnh (mục B5 bên dưới). Ngoài chiều 2, nhánh còn tìm các chiều khác mà bộ giả định chưa tách rõ: viết để làm gì, khen hay chê, đã dùng máy chưa, có gọi tên máy không. Nó **chưa** gán nhãn cho cả 473 nghìn bình luận. Việc đó làm sau, trên `main`.

Ví dụ dễ hình dung: muốn xếp một kho quần áo lộn xộn. Không đặt sẵn ngăn tủ theo phỏng đoán, mà bốc ngẫu nhiên vài trăm món ra xem có những loại gì, rồi mới đóng ngăn.

## 2. Các bước, theo thứ tự

```text
B1 kiểm cấu trúc dữ liệu
 → B2 bốc mẫu ngẫu nhiên, chia lô
 → B3 HAC: thuật toán tìm ứng viên khía cạnh trên cả bộ dữ liệu
 → B4 mã hóa mở: đọc 600 bình luận, ghi tự do "nói về gì, làm gì"
 → (7d) trưởng nhóm mã độc lập để so, sửa luật mơ hồ
 → B5 gom mã thành bộ nhãn                    ← ĐANG Ở ĐÂY (chờ duyệt)
 → B6 hai người gán mù lô K: đo bộ nhãn có rõ, AI có đúng
 → B7 gán lại cả mẫu, tính tỷ lệ mỗi nhãn
 → B8 so ba nguồn, chốt bộ nhãn
```

### B1. Kiểm cấu trúc dữ liệu (xong 22/11)

Chưa đọc nội dung, chỉ xem dữ liệu "hình dạng" thế nào: bao nhiêu bình luận, của bao nhiêu máy, video nào nhiều bình luận nhất, bình luận gốc hay trả lời. Phát hiện chính ([báo cáo](../1-thu-thap/bao-cao-kiem-tra-du-lieu.md)):
- 5 kênh chiếm 62,7% bình luận;
- 2,84% là bình luận của chính chủ kênh;
- nhiều video đông bình luận là video tặng quà, nên có rất nhiều bình luận dự thi.

Mấy điều này quyết định cách bốc mẫu và cách tách nhóm khi tính tỷ lệ.

### B2. Bốc mẫu (xong 22/11)

Bốc **ngẫu nhiên 800 bình luận** bằng một "hạt giống" cố định (`seed 20261122`), nên ai chạy lại cũng ra đúng 800 bình luận đó. Chia theo thứ tự bốc:

| Lô | Số bình luận | Dùng để |
|---|---|---|
| 1–5 | 500 | Đọc và ghi mã (B4) |
| K | 100 | **Giấu kín**, không ai đọc tới B6. Dùng làm bài kiểm tra "đề chưa ai xem" |
| D1, D2 | 200 | Dự trữ, dùng khi chưa đủ |
| CD (có chủ đích) | 100 | Tìm theo từ khóa "lỗi", "bảo hành"… để không sót loại hiếm mà quan trọng. **Không** tính vào tỷ lệ |

**Vì sao 500:** với 500 bình luận, loại nào chiếm từ 0,5% trở lên gần như chắc chắn gặp ít nhất một lần. Cộng 100 của lô K thành 600, đủ để mọi tỷ lệ sai không quá ±4% ([đặc tả 3.3](../3-gan-nhan/dac-ta-kham-pha-nhan.md#33-vì-sao-mã-hóa-mở-500-bình-luận)).

### B3. HAC (xong 22/11)

Một thuật toán từ bài báo nhóm đã đọc. Trên cả 473 nghìn bình luận, nó tìm danh từ hay đi với từ đánh giá ("pin **trâu**", "màn hình **đẹp**"), nên bắt được cả khía cạnh hiếm mà mẫu 600 có thể sót.

Ngày 23/11 bạn quyết **không chấm** danh sách này, vì nó nhiễu (mảnh từ, teencode). HAC chỉ để Claude đối chiếu ở B8.

### B4. Mã hóa mở (xong 23/11)

Claude đọc 600 bình luận (lô 1–5 và CD). Với mỗi bình luận, ghi một hay nhiều **mã** dạng `đối tượng: hành vi`:

| Bình luận (tự soạn) | Mã |
|---|---|
| "pin trâu, cam đêm hơi nhòe" | `pin: khen; cam đêm: chê` |
| "anh ơi về VN giá bao nhiêu" | `giá: hỏi` |
| "em xin 1 suất ạ" | `quà: xin` |

"Mở" nghĩa là **không** chọn từ danh sách có sẵn. Đối tượng ghi bằng chính chữ của bình luận, để thấy được dữ liệu thật có gì, kể cả loại không ai ngờ tới.

Kết quả: 843 mã, 523 đối tượng khác nhau ([thống kê](../3-gan-nhan/bao-cao-ma-hoa-mo.md)). Claude tự rà 2 lượt. Nhưng tự rà không thay được người kiểm.

### 7d. Bạn mã độc lập để so (xong 23/11)

Bạn mã lại cả 600 bình luận mà không nhìn mã của Claude. Rồi code so hai người theo **hành vi** (khen, chê, hỏi…).

**Kappa** là con số đo hai người đồng ý tới đâu, **sau khi trừ phần trùng do may rủi**. Ví dụ: hai người gần như không bao giờ dùng `nhắc`, nên "đồng ý" tới 97% chỉ vì cùng không dùng. Kappa trừ phần đó đi, chỉ còn 0,18. Kappa 1 là trùng hoàn toàn, 0 là trùng ngang may rủi. Từ 0,6 trở lên coi là dùng được.

Kết quả trên 599 bình luận (bỏ 1 dòng Excel làm hỏng ô): **21/32 hành vi có kappa ≥ 0,6**. Khen, chê, hỏi, giải thích khớp tốt. `nhắc`, `kể`, `nhận xét`, `lo ngại`, `trêu` lệch nhiều.

Đọc các ca lệch thì phần lớn là **luật mơ hồ**, không phải ai sai. Ví dụ guideline cho phép ghi "đã dùng máy" theo hai cách. Nên đã sửa luật ([guideline, bảng hành vi](../3-gan-nhan/huong-dan-kham-pha-nhan.md#bảng-hành-vi)). Bạn quyết:
- `kể` chỉ là kể;
- định mua là `mong muốn`;
- `báo lỗi` thành hành vi riêng;
- giữ chiều "đã dùng máy".

Tiện thể sửa 3 lỗi kỹ thuật:
- Excel biến ô bắt đầu bằng `+` thành `#NAME?`. Giờ guideline hướng dẫn mở phiếu bằng Data → From Text/CSV.
- Tên người dạng `+Tên Họ` chưa được che. Code giờ che.
- `Khen` viết hoa bị đếm khác `khen`. Code giờ không phân biệt chữ hoa.

### B5. Gom mã thành bộ nhãn (nháp xong 23/11, chờ bạn duyệt)

523 đối tượng khác nhau là quá vụn: `pin`, `tụt pin`, `cục sạc 67w` thực ra cùng một loại. B5 **gom** chúng lại:
- đối tượng gom thành **nhãn của chiều 2**, phần lớn là **khía cạnh**: `pin`, `tụt pin`, `cục sạc 67w` → "pin & sạc". Nói chung về cả máy hay về hãng thì vào hai nhãn không phải khía cạnh;
- hành vi gom thành **mục đích**: `khen`, `chê`, `so sánh` → "đánh giá";
- các nhãn xếp vào **chiều**. Mỗi chiều là một câu hỏi về bình luận.

| Chiều | Câu hỏi | Ví dụ nhãn |
|---|---|---|
| 1 | Liên quan tới gì? | điện thoại · video, người review · cãi nhau với người khác · không liên quan |
| 2 | Nói về phần nào của điện thoại? | pin & sạc · màn hình · camera · giá · mua bán… (15 nhãn, trong đó 13 khía cạnh) |
| 3 | Viết để làm gì? | đánh giá · hỏi · báo lỗi · minigame · quảng cáo… (13 nhãn) |
| 4 | Khen hay chê phần đó? | tích cực · tiêu cực · so sánh · không đánh giá |
| 5 | Người viết đã dùng máy chưa? | có · không rõ |
| 6 | Có gọi tên máy cụ thể không? | gọi tên máy · chỉ nhắc hãng · không nhắc |

Việc gom **làm bằng code** ([label_set.py](../../src/labeling/label_set.py)), không làm tay. Code là một danh sách luật kiểu "đối tượng có chữ `pin` hay `sạc` thì vào nhãn pin & sạc". Nhờ vậy số đếm chạy lại được, và ai cũng đọc được luật để cãi.

Hai phép kiểm ([báo cáo bộ nhãn](../3-gan-nhan/bao-cao-bo-nhan.md)):
- **Bão hòa:** đếm số nhãn **mới** xuất hiện ở từng lô. Lô 1 cho 37 nhãn, lô 3 thêm 2, lô 2, 4, 5 không thêm. Đọc thêm không ra loại mới nữa, tức đã đủ. Như bốc quần áo: bốc thêm mấy chục món mà không ra loại mới thì thôi.
- **Phủ mã của bạn:** áp cùng luật cho mã của bạn. 36/797 mã chưa xếp được, và đều là từ đồng nghĩa ("tản nhiệt", "tần số quét"). Tức bộ nhãn không thiếu loại nào mà bạn thấy.

**Số đếm ở B5 chưa phải tỷ lệ thật.** Đó là đếm trên mã do AI ghi, chỉ để chứng minh nhãn có trong dữ liệu.

## 3. Đang chờ gì

Bạn đọc [đặc tả bộ nhãn](../3-gan-nhan/dac-ta-bo-nhan.md), sửa nhãn nào thấy sai hoặc thừa, rồi trả lời 4 câu ở mục 7 của file đó:
1. nhãn hiếm giữ riêng hay gộp;
2. có tách "fan, chiến hãng" không;
3. bài test trong video có gán thêm nhãn khía cạnh không;
4. có tách "đùa" khỏi "công kích" không.

## 4. Sắp tới

| Bước | Ai | Làm gì | Vì sao quan trọng |
|---|---|---|---|
| B6 | Bạn và Claude | Mỗi người tự gán 100 bình luận lô K theo bộ nhãn, không xem của nhau, rồi so kappa | Lô K chưa ai đọc. Đây là phép đo **duy nhất** cho biết bộ nhãn có rõ với người mới, và nhãn AI gán có tin được không |
| B7 | Claude gán, bạn kiểm ≥ 100 | Gán lại 600 bình luận theo bộ nhãn, rồi tính tỷ lệ mỗi nhãn kèm khoảng tin cậy | Trả lời "bình luận có những loại gì, mỗi loại bao nhiêu" |
| B8 | Claude đề xuất, bạn quyết | So ba nguồn (mã hóa mở, HAC, bộ đặt sẵn), giữ, thêm, gộp hay bỏ từng nhãn theo luật viết sẵn | Chốt bộ nhãn cuối để mang về `main` |

Trước B6 còn một việc kỹ thuật: phiếu lô K cần thêm một cột cho mỗi chiều.

## 5. Từ ngữ

Bảng đầy đủ, và cách phân biệt *nhãn* với *khía cạnh*: [đặc tả khám phá nhãn, Thuật ngữ](../3-gan-nhan/dac-ta-kham-pha-nhan.md#thuật-ngữ).

| Từ | Nghĩa |
|---|---|
| Mã | Ghi chú tự do khi đọc, dạng `đối tượng: hành vi` |
| Đối tượng | Phần trước dấu `:` của mã: bình luận nói về cái gì, bằng chữ của bình luận |
| Chiều | Một câu hỏi về bình luận; mỗi chiều có một danh sách nhãn |
| Nhãn | Một câu trả lời trong danh sách của một chiều, có định nghĩa, dùng để gán thống nhất |
| Khía cạnh | Một phần, một tính chất của điện thoại, hoặc một việc khi mua và dùng (giá, mua bán, bảo hành). Mỗi khía cạnh là một nhãn của chiều 2. **Mọi khía cạnh là nhãn, không phải nhãn nào cũng là khía cạnh** (vd `hoi`, `may_chung`) |
| Bộ nhãn | Tất cả các chiều và nhãn, kèm định nghĩa |
| Kappa | Mức hai người đồng ý, đã trừ phần trùng do may rủi; ≥ 0,6 là dùng được |
| Bão hòa | Đọc thêm không ra nhãn mới nữa |
| Gán mù | Hai người gán độc lập, không xem của nhau |
| Lô K | 100 bình luận giấu kín tới B6, làm "đề chưa ai xem" |
| Mẫu có chủ đích (CD) | Bình luận tìm theo từ khóa để bắt loại hiếm; không tính vào tỷ lệ |
| Khoảng tin cậy | Khoảng mà tỷ lệ thật có thể nằm trong; mẫu càng lớn thì càng hẹp |

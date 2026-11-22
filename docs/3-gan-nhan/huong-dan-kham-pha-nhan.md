# Hướng dẫn mã hóa mở và gom bộ nhãn

> Mục đích: Cách làm từng việc của người mã hóa trong bước khám phá nhãn (B3–B6): đọc gì trước, ghi mã tự do thế nào, gom mã thành bộ nhãn, kiểm bộ nhãn, gán cả mẫu, lỗi hay gặp; cập nhật lần cuối: 2026-11-22.

Luật (lấy mẫu, luật dừng, cách tính, luật chốt bộ nhãn) nằm ở [đặc tả khám phá nhãn](dac-ta-kham-pha-nhan.md). File này chỉ nói **cách làm**, không chép lại luật.

**Công cụ:** notebook `notebooks/3_label_discovery.ipynb` (lấy mẫu, xuất phiếu, tính bão hòa, kappa, phân bố) **chưa có**. Nó là việc tiếp theo trong [kế hoạch](../0-chung/ke-hoach.md).

## 1. Trước khi bắt đầu

1. Đọc [kế hoạch](../0-chung/ke-hoach.md) mục 1 và 3, và [đặc tả](dac-ta-kham-pha-nhan.md) mục 2–6.
2. **Chưa đọc mục 7 của đặc tả** (bộ nhãn đặt sẵn trên `main`). Đọc trước thì sẽ vô tình mã hóa theo danh sách đó. Đọc sau khi xong B4.
3. Nhận phiếu của mình. Mở bằng Excel hoặc Google Sheets, và nhớ chọn mã hóa UTF-8 khi mở CSV, không thì chữ tiếng Việt bị lỗi.
4. Người làm cùng lô 1 với mình: không bàn với nhau trước khi cả hai xong lô.

## 2. Ghi mã tự do (B3)

Mỗi bình luận ghi **một hay nhiều mã** vào cột `ma_tu_do`, cách nhau bằng `;`. Mỗi mã là một cụm từ ngắn trả lời: bình luận **nói về cái gì**, hoặc **để làm gì**.

| Bình luận (tự soạn) | Mã tốt | Mã chưa tốt và vì sao |
|---|---|---|
| "pin trâu, cam đêm hơi nhòe" | khen pin; chê camera chụp đêm | "tích cực": không biết nói về cái gì |
| "anh ơi máy này về VN giá bao nhiêu" | hỏi giá; hỏi người review | "giá": không biết là hỏi, khen hay chê |
| "em xin 1 suất ạ" | xin quà | "spam": chưa chắc là spam, hãy ghi đúng việc người viết làm |
| "táo thì đỉnh rồi, ss toàn copy" | khen iPhone chung chung; chê Samsung; cà khịa giữa fan các hãng | "so sánh": mất phần thái độ |
| "đúng rồi" (bình luận cha: "camera chụp đẹp ghê") | đồng tình với bình luận cha (cha khen camera) | "khen camera": chính bình luận không nói về camera |
| "ib zalo nhận máy free" | mời liên hệ ngoài; hứa tặng máy | (bỏ trống): không được bỏ trống |
| "video dài quá, tua mỏi tay" | chê video | "chê máy": nhầm đối tượng |
| "mình dùng 2 tháng, sạc hay bị nóng" | kể trải nghiệm đã dùng; chê nóng khi sạc | "nóng": mất ý đã dùng máy |
| "kkk" | cười, không có nội dung | |

**Quy tắc:**
- Ghi theo **những gì được viết**, không đoán ý người viết. Mỉa mai rõ ràng thì ghi theo nghĩa thật và thêm mã "mỉa mai".
- Một bình luận có nhiều ý thì ghi đủ các ý.
- Dùng lại cách diễn đạt của mình cho cùng một ý. Ví dụ đã viết "hỏi giá" thì đừng lúc viết "hỏi giá", lúc viết "thắc mắc giá bán". Như vậy gom mã sẽ dễ hơn.
- Không hiểu bình luận thì ghi "không hiểu", và ghi lý do vào `ghi_chu`.
- Ca khó, chỗ phân vân thì ghi vào `ghi_chu`. Những ghi chú này là nguyên liệu để viết định nghĩa nhãn.
- **Không** chép tên người viết hay bất cứ thông tin cá nhân nào vào phiếu.

## 3. Gom mã thành bộ nhãn (B4)

Làm sau khi cả hai người xong lô 1. Một buổi làm việc chung, khoảng 1–2 giờ.

1. **Liệt kê** mọi mã của cả hai người, kèm số lần gặp.
2. **Gom** các mã cùng nghĩa thành một nhãn. Ví dụ "hỏi giá", "giá bao nhiêu vậy", "hỏi giá bán VN" gom thành nhãn "hỏi giá".
3. **Xếp nhãn vào chiều.** Mỗi chiều là một câu hỏi về bình luận, ví dụ "nói về cái gì?", "để làm gì?", "khen hay chê?". Với mỗi chiều, quyết một bình luận được mang **một** nhãn hay **nhiều** nhãn.
4. **Viết cho mỗi nhãn:** định nghĩa 1–2 câu, 2 ví dụ thuộc, 1 ví dụ dễ nhầm nhưng không thuộc. Lấy ví dụ từ chính phiếu; có thể sửa vài chữ cho khỏi lộ bình luận thật.
5. **Thêm nhãn "khác"** cho mỗi chiều, và "không xác định" nếu cần.
6. **So hai phiếu lô 1:** chỗ nào hai người ghi mã khác hẳn nhau thì đó là chỗ định nghĩa phải viết rõ nhất.
7. Ghi bộ nhãn vào `docs/3-gan-nhan/dac-ta-bo-nhan.md`.

**Sau lô 2, 3:** mã mới thì gom vào nhãn có sẵn, hoặc tạo nhãn mới và ghi lô tạo ra nó. Ghi số nhãn mới của từng lô: đó là số liệu để biết đã bão hòa chưa ([đặc tả mục 5](dac-ta-kham-pha-nhan.md#5-bão-hòa-khi-nào-là-đủ-b4)).

Xong B4 rồi mới đọc mục 7 của đặc tả. Thấy nhãn đặt sẵn nào mà dữ liệu không có, hay dữ liệu có mà danh sách đặt sẵn thiếu, thì ghi lại cho B7.

## 4. Kiểm bộ nhãn (B5)

1. Hai người gán **lô K** độc lập, theo bộ nhãn. Đây là những bình luận chưa ai đọc.
2. Gán xong mới so. Tính đồng ý thô và kappa cho từng chiều; notebook sẽ tính khi có.
3. Bàn từng ca lệch: lệch vì định nghĩa chưa rõ thì sửa định nghĩa, thêm ví dụ.
4. Chiều nào kappa dưới 0,6 thì sửa rồi kiểm lại trên 50 bình luận dự trữ, theo đặc tả mục 6.

## 5. Gán cả mẫu (B6)

1. Gán lại lô 1–3 (và các lô dự trữ đã mã hóa mở) theo **bộ nhãn cuối**, không dùng mã tự do cũ.
2. Mỗi bình luận một người gán, chia đều cho hai người. Lô K giữ kết quả đã thống nhất ở B5.
3. Nộp phiếu. Notebook tính phân bố kèm khoảng tin cậy.

## 6. Lỗi hay gặp

| Lỗi | Vì sao hỏng | Cách tránh |
|---|---|---|
| Mã hóa theo danh sách 9 khía cạnh có sẵn | Chỉ xác nhận lại giả định, không tìm được cái thiếu | Không đọc mục 7 của đặc tả trước khi xong B4 |
| Mã quá chung ("tích cực", "liên quan", "khác") | Không gom được thành nhãn có nghĩa | Ghi cả **nói về gì** lẫn **thái độ** |
| Bỏ trống bình luận khó | Mất đúng những ca cần cho định nghĩa | Ghi "không hiểu" kèm ghi chú |
| Xem phiếu người kia khi đang làm lô 1 hay lô K | Đồng thuận bị thổi phồng, không còn đo được độ rõ của nhãn | Làm xong cả lô mới so |
| Sửa phiếu sau khi đã so | Số đồng thuận không còn đúng | Sửa ở bản mới, giữ bản đã nộp |
| Chép tên người viết hay thông tin cá nhân vào phiếu | Lộ dữ liệu cá nhân | Phiếu chỉ có nội dung bình luận |

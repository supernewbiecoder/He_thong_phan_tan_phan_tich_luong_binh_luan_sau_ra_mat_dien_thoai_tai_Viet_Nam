# Từ câu hỏi nghiên cứu đến bộ nhãn

*Cập nhật lần cuối: 25/11/2026*

Tài liệu này ghi lại quá trình nhóm xây dựng hướng nghiên cứu: bắt đầu từ những câu hỏi muốn trả lời, tìm bài báo tham khảo, xem xét dữ liệu hiện có, lựa chọn cách phân tích và mô hình, rồi thiết kế bộ nhãn để chuẩn bị cho giai đoạn huấn luyện.

Nội dung được viết lại từ bản ghi chép của trưởng nhóm. Số liệu lấy từ nhánh `kham-pha-nhan`, trên **bộ dữ liệu v4**: 473.786 bình luận, thu thập từ ngày 19/10 đến ngày 01/11/2026.

Một số từ dùng xuyên suốt tài liệu ([bảng thuật ngữ đầy đủ](docs/3-gan-nhan/dac-ta-kham-pha-nhan.md#thuật-ngữ)):

- **Hai bên:** Claude (AI, bên A) và trưởng nhóm (bên B).
- **Mã:** ghi chú tự do khi đọc một bình luận, dạng `đối tượng: hành vi`. Ví dụ: `pin: khen`.
- **Chiều:** một câu hỏi đặt ra cho bình luận. Ví dụ: “viết để làm gì?”.
- **Nhãn:** một câu trả lời trong danh sách của một chiều. Ví dụ: `hoi` (hỏi).
- **Khía cạnh:** nhãn chỉ một phần của điện thoại (pin, camera) hoặc một việc khi mua và dùng máy (giá, bảo hành). Khía cạnh nào cũng là nhãn, nhưng không phải nhãn nào cũng là khía cạnh.

## Nhìn tổng thể: nhóm đang làm đến đâu?

Hiện tại, nhóm có **473.786 bình luận nằm dưới các video YouTube về điện thoại**. Đây vẫn là dữ liệu thô: nhóm chưa biết bình luận nào là spam, bình luận nào thực sự nói về điện thoại, người viết nhắc đến khía cạnh nào và có thái độ ra sao.

Mục tiêu của dự án là dùng các bình luận tiếng Việt trong đó để trả lời sáu câu hỏi xoay quanh một mẫu điện thoại vừa ra mắt. Khó khăn là không thể đọc và gán nhãn toàn bộ gần nửa triệu bình luận bằng tay. Hơn nữa, nếu tự đặt sẵn danh sách khía cạnh ngay từ đầu, nhóm có thể bỏ sót những điều người dùng thực sự quan tâm.

Vì vậy, hướng làm hiện tại gồm năm bước: (1) lấy một mẫu bình luận ngẫu nhiên; (2) hai bên đọc độc lập và ghi mã cho từng bình luận, rồi so mã với nhau để đo mức độ nhất quán; (3) gom mã thành bộ nhãn; (4) thử bộ nhãn trên 100 bình luận chưa ai đọc; (5) tính xem mỗi nhãn chiếm bao nhiêu phần trăm bình luận. Sau đó mới chốt bộ nhãn và tiến tới huấn luyện mô hình.

Đến ngày 25/11/2026, nhóm đã có **bộ nhãn nháp gồm 6 chiều, 43 nhãn, trong đó 13 nhãn là khía cạnh**, đang chờ trưởng nhóm duyệt. Nhóm **chưa biết mỗi nhãn chiếm bao nhiêu phần trăm bình luận** (mới có số đếm trên mẫu, chưa được người kiểm), và **chưa chấm điểm mô hình nào bằng nhãn do người gán** trên bình luận YouTube.

Quy trình hiện tại có thể hình dung như sau:

```text
6 câu hỏi nghiên cứu
        ↓
Xác định thông tin cần lấy từ mỗi bình luận:
có nói về điện thoại không – máy nào – phần nào của máy – thái độ – đã dùng máy chưa
        ↓
473.786 bình luận thô → kiểm tra cấu trúc dữ liệu (EDA)
        ↓
Lấy mẫu ngẫu nhiên → hai bên đọc và ghi mã độc lập
        ↓
Gom mã thành bộ nhãn nháp                      ← NHÓM ĐANG Ở ĐÂY (chờ duyệt)
        ↓
Hai bên gán nhãn 100 bình luận chưa ai đọc, không xem của nhau → đo độ nhất quán
        ↓
Tính mỗi nhãn chiếm bao nhiêu % trong mẫu 600 bình luận, kèm khoảng tin cậy → chốt bộ nhãn
        ↓
Gán nhãn chính thức → huấn luyện và đánh giá mô hình
        ↓
Sử dụng kết quả để trả lời Q1–Q6
```

---

## 1. Những câu hỏi nghiên cứu nhóm muốn trả lời

Gọi **X** là mẫu điện thoại vừa ra mắt, **P** là thế hệ trước của X, **R1** và **R2** là hai đối thủ cùng phân khúc (bộ bốn máy cụ thể chưa chốt). Nhóm muốn tìm hiểu người dùng Việt Nam nói gì về X, và phản hồi về X khác thế nào so với phản hồi về P và hai đối thủ.

Cụ thể, dự án đặt ra sáu câu hỏi:

| Mã | Câu hỏi nghiên cứu | Thông tin cần lấy từ bình luận |
|---|---|---|
| Q1 | Người dùng đón nhận X tích cực hay tiêu cực? Phản ứng thay đổi thế nào trong bốn tuần đầu sau khi ra mắt? | Bình luận đang nói về máy nào, thái độ ra sao và được đăng vào tuần thứ mấy sau ngày công bố. |
| Q2 | X có những ưu điểm và nhược điểm gì? | Ngoài thái độ, cần biết người viết đang khen hoặc chê khía cạnh nào của máy. |
| Q3 | Khi so sánh với đối thủ, X mạnh và yếu ở những điểm nào? | Cần nhận ra câu so sánh, máy nào được đánh giá cao hơn và hơn ở khía cạnh nào. |
| Q4 | Những điểm từng bị chê ở thế hệ trước đã được cải thiện trên X chưa? | Cần xác định khía cạnh được nhắc đến và thái độ đối với cả X lẫn P. |
| Q5 | Người đã sử dụng X gặp những lỗi gì? Lỗi nào cần được ưu tiên xử lý? | Cần biết người bình luận đã thực sự sử dụng máy hay chưa và họ phản ánh vấn đề gì. |
| Q6 *(đề xuất, chưa chốt)* | Có dấu hiệu tài khoản ảo hoặc hoạt động seeding hay không? Chúng làm kết quả Q1–Q5 lệch bao nhiêu? (*Seeding*: bình luận do người được thuê hoặc tài khoản giả viết để tạo ấn tượng có lợi cho một sản phẩm.) | Cần xem xét dấu hiệu phối hợp giữa các tài khoản, thời điểm đăng và nội dung lặp lại. |

Từ các câu hỏi trên có thể thấy, **chỉ phân loại cảm xúc tích cực hay tiêu cực là chưa đủ**. Với mỗi bình luận, nhóm cần xác định ít nhất: bình luận có nói về điện thoại không, nói về máy nào, nhắc đến phần nào của máy và thể hiện thái độ gì. Riêng Q5 còn cần biết người viết đã sử dụng chiếc điện thoại đó hay chưa.

### Phạm vi dữ liệu

Nghiên cứu hiện tập trung vào **bình luận dạng văn bản bằng tiếng Việt** dưới video của 44 kênh đã được lựa chọn. Nhóm chỉ lấy các bình luận **được đăng trong bốn tuần kể từ ngày công bố của từng máy**. Ngày công bố là ngày ra mắt đầu tiên (toàn cầu, hoặc Trung Quốc với máy ra mắt ở đó trước), không phải ngày bán ở Việt Nam. Bộ dữ liệu chưa lọc gì, nên vẫn lẫn bình luận không phải tiếng Việt (mục 5).

Nhóm không phân tích hình ảnh, âm thanh hay nội dung video. Nhóm cũng không lấy bình luận đăng trước ngày công bố, vì vậy **không thể dùng bộ dữ liệu hiện tại để so sánh phản ứng trước và sau khi ra mắt**.

### Vì sao vẫn cần quan tâm đến spam và seeding trên YouTube?

YouTube có chính sách ngăn chặn spam, lừa đảo và thao túng tương tác. Trong [chính sách về spam](https://support.google.com/youtube/answer/2801973?hl=en), nền tảng đề cập đến những hành vi như spam bình luận, lừa đảo, thao túng tương tác và sản xuất nội dung hàng loạt. YouTube cũng có [chính sách riêng về tương tác giả](https://support.google.com/youtube/answer/3399767?hl=en), bao gồm lượt xem, lượt thích, bình luận và lượt đăng ký không xác thực.

Tuy nhiên, việc một nền tảng có chính sách và hệ thống lọc không đồng nghĩa với việc mọi dữ liệu còn lại đều sạch. Có một số lý do khiến nhóm vẫn cần tự kiểm tra:

- **Số bình luận bị gỡ không cho biết hệ thống đã bỏ sót bao nhiêu.** [Báo cáo minh bạch](https://support.google.com/transparencyreport/answer/9198203?hl=en) của YouTube ghi rằng 99,5% số bình luận bị gỡ trong quý III/2023 do hệ thống tự động gắn cờ (báo cáo đưa hai con số tổng cho cùng quý này, 842,8 triệu và 893,6 triệu bình luận, đều kèm tỷ lệ 99,5%). Mẫu số của 99,5% là **số bình luận đã bị gỡ**, không phải số bình luận vi phạm. Ví dụ, nếu có 1.000 bình luận spam mà YouTube chỉ gỡ 200, trong đó 199 do hệ thống phát hiện, thì tỷ lệ vẫn là 99,5% dù 800 bình luận còn lọt. Báo cáo không công bố *precision* (trong số bị gỡ, bao nhiêu phần đúng là vi phạm) và *recall* (trong số vi phạm, bao nhiêu phần bị gỡ).
- **Một nghiên cứu độc lập cho thấy nhiều tài khoản lừa đảo không bị xử lý.** Nghiên cứu [*Like, Comment, Get Scammed*](https://www.securitee.org/files/likecomment_ndss2024.pdf) (NDSS 2024) theo dõi bình luận ở 20 kênh YouTube và tìm được 10.541 tài khoản đăng bình luận lừa đảo. Trong sáu tháng theo dõi, chỉ 3.312 tài khoản (31,42% của 10.541) bị vô hiệu hóa.
- **Seeding cho thương hiệu không được nêu đích danh trong chính sách spam.** Đây cũng là nhóm hành vi mà Q6 muốn tìm hiểu. Một tài khoản seeding có thể viết bình luận tự nhiên, không nhất thiết sử dụng những mẫu câu spam dễ nhận ra.
- **Nhóm chỉ thấy những bình luận còn tồn tại lúc thu thập**, và trong đó vẫn có dấu hiệu cần chú ý (tỷ lệ tính trên 473.786 bình luận): 1.360 bình luận *đăng dồn* (0,29%), tức cùng một nội dung từ 10 ký tự trở lên được đăng ít nhất 3 lần trong 10 phút; và 7.584 bình luận (1,60%) thuộc trường hợp một người đăng cùng một nội dung từ 2 lần trở lên.

Vì thế, nếu thực hiện Q6, nhóm chỉ nên kết luận về **dấu hiệu bất thường hoặc dấu hiệu phối hợp**, không nên khẳng định một thương hiệu cụ thể đã thuê bot hay tổ chức seeding. Dữ liệu hiện tại không chứng minh được mối liên hệ giữa các tài khoản và một công ty nào đó.

## 2. Bài toán này thuộc lĩnh vực nào?

Dự án có thể được nhìn từ hai góc độ: cách tiếp cận nghiên cứu và kỹ thuật xử lý ngôn ngữ.

**Về cách tiếp cận nghiên cứu, đây là Social Media Monitoring (SMM) – theo dõi mạng xã hội.** Theo Branthwaite và Patterson (2011), được dẫn lại trong bài báo ở mục 3, SMM là cách nghiên cứu mang tính quan sát, thụ động và định lượng. Nhà nghiên cứu thu thập dữ liệu từ mạng xã hội rồi phân tích những gì người dùng thể hiện, thay vì trực tiếp can thiệp vào hành vi của họ.

**Về kỹ thuật, bài toán có liên quan đến Aspect-Based Sentiment Analysis (ABSA) – phân tích cảm xúc theo khía cạnh.** Khác với cách phân loại cảm xúc thông thường, ABSA không gán một nhãn tích cực hoặc tiêu cực cho toàn bộ bình luận. Thay vào đó, phương pháp này xác định người viết đang nói đến khía cạnh nào của sản phẩm, rồi phân tích thái độ của họ đối với từng khía cạnh.

Ví dụ, trong câu “Camera chụp ngày đẹp nhưng chụp đêm lại tệ”, người viết đang đề cập đến cùng một khía cạnh là camera, nhưng thể hiện hai thái độ khác nhau tùy điều kiện sử dụng.

Theo Hu và Liu (2004), được dẫn trong bài báo tham khảo ở mục 3, phân tích cảm xúc theo khía cạnh gồm ba công việc chính:

1. **Tìm khía cạnh:** xác định những đặc điểm của sản phẩm được người dùng nhắc đến.
2. **Phân tích thái độ:** xem người dùng đang khen, chê hay thể hiện một thái độ khác đối với khía cạnh đó.
3. **Tổng hợp kết quả:** thống kê và trình bày những khía cạnh được quan tâm, cùng với phản hồi của người dùng.

Ba công việc này chưa đủ cho dự án. Nhóm còn phải xác định bình luận nói về máy nào (cần cho Q1–Q5) và người viết đã sử dụng máy hay chưa (cần cho Q5).

## 3. Bài báo được dùng làm tài liệu tham khảo

Bài báo chính mà nhóm tham khảo là:

Wiegard, Eilers và Gercke (2017), *What Does YouTube Say About Your Product? An Aspect Based Approach*, công bố tại hội nghị ECIS 2017.

- [Trang bài báo](https://aisel.aisnet.org/ecis2017_rp/28)
- [Bản PDF](https://aisel.aisnet.org/cgi/viewcontent.cgi?article=1027&context=ecis2017_rp)

### 3.1. Bài báo đã làm gì và khác gì so với dự án của nhóm?

Bài báo nghiên cứu bình luận YouTube để tìm hiểu những khía cạnh sản phẩm mà người dùng quan tâm. Tuy nhiên, phạm vi và mục tiêu của họ hẹp hơn dự án hiện tại.

| Nội dung | Nghiên cứu của bài báo | Dự án của nhóm |
|---|---|---|
| Ngôn ngữ | Tiếng Anh | Tiếng Việt |
| Sản phẩm | Ba điện thoại: iPhone 6S, Galaxy S7 và LG G5 | Có dữ liệu của 127 mẫu máy; bộ bốn máy chính dùng để phân tích vẫn chưa chốt. |
| Dữ liệu | 3.631 bình luận YouTube dưới video đánh giá và đập hộp; thêm 750 đánh giá Amazon để đối chiếu | 473.786 bình luận YouTube |
| Mục tiêu | Tìm những khía cạnh sản phẩm được khách hàng nhắc đến | Tìm khía cạnh, thái độ, sản phẩm được nhắc đến và thông tin người viết đã sử dụng máy hay chưa |
| Cách tìm khía cạnh | HAC (*High Adjective Count*), thuật toán dựa trên luật: mỗi tính từ được gán cho danh từ gần nó nhất trong câu; danh từ nào được gán nhiều tính từ thì coi là khía cạnh. Danh từ và tính từ được nhận ra bằng một bộ gán từ loại có sẵn | HAC (bản viết lại cho tiếng Việt) chỉ dùng để đối chiếu; bộ khía cạnh chính rút ra từ việc đọc và ghi mã một mẫu bình luận (mục 7) |
| Kiểm chứng | Hai người đọc bình luận rồi chấm khía cạnh nào đúng. Tính *precision*: trong N khía cạnh thuật toán xếp đầu (N = 10, 20, 30, 40, 50), bao nhiêu phần là đúng | Hai bên ghi mã độc lập; đo mức độ nhất quán bằng Cohen's kappa (mục 7.4 và 8) |

Điểm quan trọng cần nhớ là bài báo tập trung vào **việc tìm khía cạnh**, chứ không giải quyết toàn bộ bài toán phân tích cảm xúc theo khía cạnh mà nhóm đang hướng tới.

### 3.2. Kết quả chính của bài báo

Bài báo đưa ra một số kết quả đáng chú ý:

- Khi chưa sắp xếp lại danh sách, precision trung bình (của 3 máy và của N = 10 đến 50) là 0,43 với YouTube và 0,45 với Amazon, tức YouTube thấp hơn hai điểm phần trăm. Bài báo kết luận: nhiễu trong bình luận YouTube không làm việc tìm khía cạnh kém đi nhiều so với Amazon. Tuy vậy, 0,43 cũng có nghĩa là hơn một nửa số khía cạnh thuật toán xếp đầu là sai.
- Khi sắp xếp lại danh sách khía cạnh theo lượng tìm kiếm trên Google Trends, precision trung bình tăng từ 0,45 lên 0,58 với Amazon và từ 0,43 lên 0,57 với YouTube. Tính trung bình thì hai nguồn gần bằng nhau; riêng ở N = 50, YouTube vẫn thấp hơn Amazon 8,76 điểm phần trăm.
- Số khía cạnh liên quan đến **máy của đối thủ** mà thuật toán tìm được từ YouTube gần gấp đôi số tìm được từ Amazon.
- Nhóm tác giả cũng thừa nhận phương pháp còn hạn chế. Nghiên cứu chỉ xét ba mẫu điện thoại, cách lựa chọn video còn đơn giản, và phương pháp chưa xử lý tốt những khía cạnh được diễn đạt gián tiếp. Chẳng hạn, các từ “to” hoặc “nhỏ” có thể ám chỉ kích thước, còn cụm “battery life” có thể khó được nhận diện nếu thuật toán chỉ dựa vào từng từ riêng lẻ. Việc xác định một câu đang nói về chiếc điện thoại nào cũng là một vấn đề chưa được giải quyết triệt để.

### 3.3. Kết quả này giúp ích cho dự án đến mức nào?

Điều bài báo hỗ trợ là: **bình luận YouTube có thể cung cấp thông tin về những khía cạnh sản phẩm mà người dùng quan tâm**. Đây là cơ sở để nhóm tiếp tục xem xét nguồn dữ liệu YouTube cho bài toán của mình.

Tuy nhiên, không nên suy rộng kết quả của bài báo quá mức:

- Bài báo chưa đánh giá bài toán phân tích cảm xúc. Các tác giả xem đây là bước nghiên cứu tiếp theo. Vì vậy, không thể lấy kết quả của bài báo để khẳng định rằng mô hình cảm xúc sẽ hoạt động chính xác trên bình luận YouTube.
- Nghiên cứu chỉ thực hiện trên ba mẫu điện thoại và dữ liệu tiếng Anh. Khi chuyển sang các mẫu máy khác hoặc bình luận tiếng Việt, nhóm vẫn phải tự đánh giá lại phương pháp.

Một tài liệu gần hơn với ngôn ngữ và lĩnh vực của dự án là bộ dữ liệu **UIT-ViSFD**, gồm 11.122 nhận xét tiếng Việt về điện thoại trên trang thương mại điện tử, do người gán nhãn ([arXiv 2105.15079](https://arxiv.org/abs/2105.15079)). Mô hình tốt nhất của nghiên cứu này đạt F1 84,48% cho nhiệm vụ tìm khía cạnh, nhưng chỉ 63,06% cho nhiệm vụ cảm xúc. (F1 là điểm kết hợp precision và recall; càng gần 100% càng tốt.)

Kết quả đó gợi ý rằng việc xác định người dùng đang nói về khía cạnh nào có thể dễ hơn việc xác định đúng thái độ của họ. Dù vậy, UIT-ViSFD là nhận xét trên trang thương mại điện tử, không phải bình luận YouTube, nên không thể lấy các con số này làm kết quả dự kiến của dự án.

### 3.4. Bốn hạn chế cần tính đến khi dùng dữ liệu mạng xã hội

Nhóm rút ra bốn vấn đề sau từ bài báo và từ dữ liệu của mình. Bài báo bàn nhiều nhất về vấn đề thứ ba; vấn đề thứ nhất và thứ tư cũng có chỗ dựa trong bài (ghi ở từng mục); vấn đề thứ hai là nhóm tự nhận ra. Ngoài ra, bài báo còn đặt câu hỏi liệu ý kiến trong video có ảnh hưởng đến bình luận hay không.

**Thứ nhất, bình luận không đại diện cho toàn bộ người dùng.** Một nghìn bình luận không đồng nghĩa với một nghìn khách hàng đã mua và sử dụng sản phẩm: có người chỉ xem video, tham khảo thông tin hoặc tham gia tranh luận. Bài báo cũng lưu ý rằng người bình luận có thể nêu ý kiến về tính năng mà họ chưa từng trải nghiệm. Ngoài ra, dữ liệu của nhóm dồn vào ít kênh: 5 trong 44 kênh chiếm 62,7% tổng số bình luận.

**Thứ hai, một bình luận có thể cần ngữ cảnh mới hiểu đúng.** Nếu chỉ đọc riêng một câu trả lời, ta có thể nghĩ người viết đang khen sản phẩm, nhưng khi xem bình luận cha thì mới nhận ra đó là lời mỉa mai hoặc phản bác. Trong dữ liệu hiện tại, reply (bình luận trả lời một bình luận khác) chiếm 42,7% tổng số bình luận, vì vậy khi đọc reply phải xem kèm bình luận cha.

**Thứ ba, dữ liệu có thể chứa nhiều loại nhiễu.** Những trường hợp cần chú ý gồm spam, quảng cáo, bình luận trùng lặp, nội dung không liên quan và tài khoản có dấu hiệu tự động. Chẳng hạn, bốn trong năm video có nhiều bình luận nhất là video tặng quà; riêng bốn video này có tổng cộng 15.998 bình luận, tương đương 3,38% của 473.786 bình luận.

**Thứ tư, thuật toán và mô hình có thể hiểu sai.** Kết quả của bài báo cho thấy điều này: precision 0,43 nghĩa là hơn một nửa số khía cạnh thuật toán xếp đầu là sai. Vì vậy, nhóm cần có dữ liệu kiểm tra do người gán nhãn, người đánh giá độc lập và các chỉ số đo lường sai số.

### 3.5. Năm câu hỏi cần trả lời trước khi tin vào kết quả

| Câu hỏi | Tình hình tại ngày 25/11/2026 |
|---|---|
| Nhóm có thu thập được đủ nhiều bình luận không? | Có 473.786 bình luận. |
| Bình luận có thực sự liên quan đến câu hỏi nghiên cứu không? | Chưa biết tỷ lệ. Trong 500 bình luận ngẫu nhiên đã đọc (lô 1–5, mục 7), 371 bình luận có mã về điện thoại theo Claude; con số này chưa được người kiểm. |
| Người viết bình luận có đại diện cho nhóm người mà nghiên cứu muốn tìm hiểu không? | Chưa thể khẳng định. Không thể suy ra người bình luận là người đã mua hoặc sử dụng điện thoại. |
| Phương pháp có hiểu đúng nội dung bình luận không? | Mới biết một phần: khi ghi mã, hai bên khớp nhau (κ ≥ 0,6) ở 21 trong 32 hành vi. Bộ nhãn thì chưa kiểm (mục 7 và 8). |
| Kết quả đã đủ tin cậy để đưa ra kết luận chưa? | Chưa. Chưa có tỷ lệ của nhãn nào được người kiểm và kèm khoảng tin cậy. |

**Điều cần rút ra:** SMM giúp chúng ta khai thác dữ liệu từ mạng xã hội, nhưng bản thân cách tiếp cận này không bảo đảm dữ liệu thu thập được đại diện cho nhận thức của toàn bộ người dùng. Muốn đưa ra kết luận đáng tin cậy, nhóm vẫn phải kiểm tra chất lượng dữ liệu và đánh giá sai số của phương pháp.

## 4. Vì sao dự định thử PhoBERT trước, và vì sao vẫn cần mô hình đối chứng?

Trước khi chọn mô hình, cần phân biệt một số khái niệm. **BERT không phải LLM sinh văn bản theo cách thường được nhắc đến hiện nay.** BERT (2018) là mô hình ngôn ngữ thuộc kiến trúc *encoder*: mô hình đọc văn bản và tạo ra biểu diễn ngữ nghĩa của văn bản đó. Biểu diễn này có thể được sử dụng cho các nhiệm vụ như phân loại cảm xúc hoặc nhận diện khía cạnh.

Trong khi đó, những mô hình như GPT, Claude hay Gemini thường được biết đến với khả năng sinh văn bản. BERT thường nhẹ hơn nhiều so với các LLM sinh văn bản cỡ lớn, nhưng vẫn có chi phí tính toán cao hơn các phương pháp truyền thống như TF-IDF kết hợp SVM.

Đối với tiếng Việt, nhóm có thể cân nhắc **PhoBERT**, một mô hình cùng họ với BERT, được huấn luyện trước trên tiếng Việt ([arXiv 2003.00744](https://arxiv.org/abs/2003.00744)). Một bài tổng quan về ABSA ([arXiv 2203.01054](https://arxiv.org/abs/2203.01054)) ghi nhận các mô hình ngôn ngữ huấn luyện trước như BERT đã cải thiện kết quả ở nhiều bài toán ABSA.

Tuy nhiên, điều đó không có nghĩa PhoBERT chắc chắn là lựa chọn tốt nhất cho dữ liệu của nhóm. Các phương pháp đơn giản hơn vẫn có thể hoạt động tốt, nhất là khi có ít bình luận đã gán nhãn. Vì thế, nhóm dự kiến so ba mức mô hình từ đơn giản đến phức tạp (luật từ khóa, TF-IDF + SVM, PhoBERT) thay vì chỉ huấn luyện một mô hình lớn rồi mặc định đó là phương án tốt nhất.

| Vấn đề | Hướng thực hiện hiện tại |
|---|---|
| **Sử dụng mô hình nào?** | Thử PhoBERT trước cho kịp tiến độ, kèm hai mốc đối chứng đơn giản hơn là luật từ khóa và TF-IDF + SVM. Cuối cùng chọn **mô hình đơn giản nhất mà kết luận Q1–Q5 không khác kết luận của mô hình tốt nhất**. (Thử PhoBERT trước là đề xuất của trưởng nhóm; quy ước trên `main` ghi “không mặc định dùng PhoBERT”. Nhóm còn phải chốt.) |
| **Lấy dữ liệu huấn luyện ở đâu?** | Theo đặc tả gán nhãn trên `main`: phần huấn luyện do LLM gán, người kiểm lại khoảng 200 bình luận để biết LLM đúng bao nhiêu; cộng thêm những bình luận người đã gán thuộc các video dùng để huấn luyện. Có thể bổ sung UIT-ViSFD và UIT-ViSD4SA (nhận xét trên trang thương mại điện tử), nhưng phải đo xem chúng làm kết quả trên YouTube tốt lên hay kém đi. |
| **Huấn luyện theo cách nào?** | Học có giám sát: mô hình học từ các bình luận đã gán nhãn. Dữ liệu chia thành phần để học (train), phần để chọn tham số (validation) và phần để chấm điểm (test). Phải chia **theo video**, để bình luận của cùng một video không nằm ở hai phần khác nhau. |
| **Chấm điểm mô hình bằng dữ liệu nào?** | Chỉ dùng nhãn do người gán, mỗi bình luận hai người gán độc lập. Không dùng nhãn do LLM tạo làm đáp án. |

Trước khi huấn luyện, nhóm cần hiểu rõ dữ liệu đang có những đặc điểm gì. Đó là lý do phải thực hiện EDA ở phần tiếp theo.

## 5. Dữ liệu hiện tại: kết quả khám phá dữ liệu (EDA)

Bộ dữ liệu hiện tại vẫn là dữ liệu thô, **chưa được gán nhãn nội dung**. Nói cách khác, nhóm chưa biết chính xác có bao nhiêu bình luận là spam, bao nhiêu bình luận thực sự nói về điện thoại, hay mỗi khía cạnh và thái độ xuất hiện với tỷ lệ bao nhiêu.

EDA trên nhánh này chạy ngày 22/11 (bước B1 của kế hoạch); các số tổng quát trùng với lần chạy ngày 11/11 trên `main`. Các phép đo ở đây mô tả **cấu trúc** của dữ liệu, chưa cho biết nội dung của từng bình luận. Nếu không ghi khác, phần trăm trong bảng tính trên 473.786 bình luận.

| Nội dung kiểm tra | Kết quả | Ý nghĩa đối với dự án |
|---|---|---|
| **Quy mô dữ liệu** | 473.786 bình luận, 4.682 video, 127 mẫu điện thoại và 44 kênh | Có lượng dữ liệu lớn để khai thác, nhưng số lượng lớn không tự động đồng nghĩa với dữ liệu phù hợp. |
| **Bình luận gốc và reply** | 271.375 bình luận gốc (57,3%); 202.411 reply (42,7%) | Cần đọc reply cùng bình luận cha để tránh hiểu sai ngữ cảnh. |
| **Ngôn ngữ** *(ước lượng bằng luật đơn giản)* | Tiếng Việt có dấu: 93,96%; tiếng Việt không dấu: 1,65%; không rõ: 2,97%; không có chữ: 0,96%; tiếng Anh: 0,42%; ngôn ngữ khác: 0,04% | Khoảng 6% không được nhận là tiếng Việt có dấu. Đây là ước lượng bằng luật, chưa được người kiểm. |
| **Độ dài bình luận** | Một nửa số bình luận dài không quá 11 từ (trung vị); 5,53% không quá hai từ | Có những bình luận quá ngắn, khó biết nói về cái gì và thái độ ra sao. |
| **Trùng lặp** *(ba số chồng lên nhau, không cộng lại)* | Nội dung giống hệt ít nhất một bình luận khác: 4,12%; một người đăng cùng nội dung từ 2 lần: 1,60%; đăng dồn (cùng nội dung, từ 3 lần trong 10 phút): 0,29% | Chưa thể kết luận đây là hoạt động phối hợp, vì những câu ngắn như “hay”, “đẹp” trùng nhau một cách tự nhiên. |
| **Mức độ tập trung theo kênh** | Năm kênh lớn nhất chiếm 62,7%; riêng kênh lớn nhất chiếm 22,85% | Kết quả có thể bị ảnh hưởng nhiều bởi một số kênh lớn. |
| **Phân bố theo thời gian** *(tính trên 480.873 lượt: một bình luận dưới video về 2 máy tính là 2 lượt)* | Tuần 1 sau ngày công bố: 38,3%; tuần 2: 27,7%; tuần 3: 20,6%; tuần 4: 13,3% | Các tuần sau có ít dữ liệu hơn nhiều; nội dung và thái độ cũng có thể khác giữa các tuần. |
| **Video tặng quà** | Bốn trong năm video có nhiều bình luận nhất là video tặng quà; tổng cộng 15.998 bình luận (3,38%) | Đây là một nguồn có khả năng tạo nhiễu đáng chú ý trong dữ liệu. |
| **Bình luận của chủ kênh** | 2,84% bình luận do chính chủ kênh đăng | Không nên xem những bình luận này là ý kiến của người xem thông thường. |

Có thể xem chi tiết trong [báo cáo kiểm tra dữ liệu](docs/1-thu-thap/bao-cao-kiem-tra-du-lieu.md).

Những con số trên giúp nhóm hiểu dữ liệu được tổ chức như thế nào và phát hiện một số rủi ro ban đầu. Nhưng chúng **chưa trả lời được** câu hỏi quan trọng nhất: người dùng thực sự đang nói gì về sản phẩm? Để trả lời, nhóm phải đọc một mẫu bình luận và tiến hành mã hóa nội dung.

## 6. Nên chia khía cạnh và cảm xúc như thế nào?

Một trong những quyết định khó nhất là xác định mức độ chi tiết của bộ khía cạnh. Nếu chia quá nhỏ, mỗi nhãn chỉ có vài ví dụ, khiến việc thống kê và huấn luyện mô hình trở nên khó khăn. Nhưng nếu gom quá nhiều nội dung vào một nhãn lớn, kết quả lại không đủ chi tiết để trả lời câu hỏi nghiên cứu.

Ví dụ:

- **Chia quá nhỏ:** trong 500 bình luận ngẫu nhiên đã đọc (lô 1–5), khía cạnh “nhiệt độ” chỉ gặp ở 4 bình luận, “bảo hành, sửa chữa” ở 3 bình luận (theo mã của Claude). Ít như vậy thì mô hình khó học, và cũng khó đánh giá riêng từng khía cạnh.
- **Chia quá rộng:** nếu chỉ ghi nhận chung rằng “camera bị chê”, nhóm sẽ không biết người dùng không hài lòng với camera trước, camera sau, khả năng chụp đêm hay quay video. Kết quả đó chưa đủ cụ thể để đưa ra nhận định hữu ích.

Vì vậy, nhóm không muốn quyết định toàn bộ danh sách khía cạnh ngay từ đầu. Các khía cạnh được rút ra từ quá trình đọc dữ liệu và ghi mã ở mục 7. Sau khi tính được tỷ lệ của từng nhãn, nhóm quyết từng nhãn theo [luật ở mục 9 của đặc tả](docs/3-gan-nhan/dac-ta-kham-pha-nhan.md#9-so-ba-nguồn-và-chốt-bộ-nhãn-b8):

| Nhãn | Điều kiện | Quyết định |
|---|---|---|
| **Nhãn đặt sẵn:** đã có trên `main` trước khi đọc dữ liệu | Có xuất hiện trong mẫu, **và** phục vụ ít nhất một câu hỏi Q1–Q6 hoặc việc đánh giá chất lượng dữ liệu | Giữ, không xét tỷ lệ |
| **Nhãn đặt sẵn** | Không xuất hiện lần nào trong mẫu | Chỉ giữ khi có câu hỏi bắt buộc cần nó |
| **Nhãn mới:** rút ra từ dữ liệu, chưa có trên `main` (ví dụ `mua_ban`) | Tỷ lệ **từ 3%** trở lên, **và** phục vụ ít nhất một câu hỏi Q1–Q6 hoặc việc đánh giá chất lượng dữ liệu | Thêm vào bộ nhãn |
| **Nhãn mới** | Tỷ lệ **dưới 3%** | Gộp vào nhãn gần nhất, trừ khi có câu hỏi cần riêng nó (ví dụ `bao_loi` cho Q5) |
| **Nhãn bất kỳ** | Tỷ lệ **dưới 1%**, không phục vụ câu hỏi nào **và** không giúp đánh giá chất lượng dữ liệu | Gộp vào nhãn gần nhất, hoặc vào nhãn “khác” |
| **Nhãn hoặc chiều bất kỳ** | κ dưới 0,6 sau hai lần sửa định nghĩa (mục 7.4) | Bỏ hoặc gộp |

**3% và 1% là của cái gì?** Là tỷ lệ của một nhãn trong mẫu:

```text
tỷ lệ của một nhãn = số bình luận có nhãn đó / số bình luận mà nhãn đó có thể được gán
```

Đếm trong **mẫu 600 bình luận ngẫu nhiên** (lô 1–5 và lô K, mục 7.3), sau khi nhãn đã được người kiểm. Không đếm trên cả 473.786 bình luận, và không tính 100 bình luận có chủ đích. Mẫu số tùy chiều (riêng chiều 4 đếm cặp thay cho bình luận):

| Nhãn thuộc chiều | Mẫu số | “Từ 3%” nghĩa là | “Dưới 1%” nghĩa là |
|---|---|---|---|
| 1 (nói về cái gì), 3 (viết để làm gì), 5 (đã dùng máy chưa), 6 (có gọi tên máy không) | Cả 600 bình luận | Từ 18 bình luận trở lên | Từ 5 bình luận trở xuống |
| 2 (nói về phần nào của điện thoại, gồm 13 khía cạnh) | Chỉ những bình luận **nói về điện thoại** trong 600 đó; số này chưa biết vì lô K chưa gán | Giả sử mẫu số là 450: từ 14 bình luận trở lên | Giả sử mẫu số là 450: từ 4 bình luận trở xuống |
| 4 (thái độ) | Các **cặp** (bình luận, nhãn chiều 2): bình luận nói về camera và pin là 2 cặp | Giả sử có 500 cặp: từ 15 cặp trở lên | Giả sử có 500 cặp: từ 4 cặp trở xuống |

- **Vì sao chiều 2 có mẫu số nhỏ hơn:** nhãn chiều 2 chỉ gán cho bình luận nói về điện thoại. Bình luận chỉ khen người review thì không thể mang nhãn `camera`.
- **“Phục vụ một câu hỏi”:** ví dụ `bao_loi` (báo lỗi) cần cho Q5. **“Việc đánh giá chất lượng dữ liệu”:** ví dụ `quang_cao`, `minigame` cho biết dữ liệu lẫn bao nhiêu bình luận không phải ý kiến về máy.
- **3% và 1% là ngưỡng đặt ra trong đặc tả** (Claude đề xuất ngày 22/11), để mọi nhãn được quyết theo cùng một luật. Đó không phải kết quả thống kê, và đặc tả không ghi vì sao chọn đúng hai con số này.
- **Tỷ lệ sát ngưỡng:** tỷ lệ đo trên mẫu có sai số. Ví dụ nhãn đo được đúng 3% (18/600) có khoảng tin cậy 95% là 1,9%–4,7% (Wilson), tức trùm lên ngưỡng. Khi đó vẫn quyết theo tỷ lệ đo được, nhưng ghi “sát ngưỡng” để trưởng nhóm xem lại.
- Mẫu số của từng chiều và cách xử lý nhãn mới dưới 3%, nhãn dưới 1%, tỷ lệ sát ngưỡng do trưởng nhóm chốt ngày 25/11.

Bộ nhãn đặt sẵn trên `main` có chín khía cạnh: Pin & sạc, Màn hình, Hiệu năng (gồm nóng máy), Camera, Thiết kế & độ bền, Phần mềm, Phần cứng khác, Giá, Bảo hành & hậu mãi. Nhóm chỉ dùng chúng để so ở bước cuối, không dùng làm khuôn khi đọc và ghi mã.

### Cảm xúc không phải lúc nào cũng chỉ là khen hoặc chê

Một bình luận có thể thể hiện mong muốn, kể lại trải nghiệm hoặc cung cấp thông tin mà không trực tiếp đánh giá sản phẩm. Ngược lại, cùng một khía cạnh cũng có thể nhận cả phản hồi tích cực lẫn tiêu cực trong một bình luận.

Hai ví dụ dưới đây cho thấy vì sao không nên ép mọi nội dung vào hai nhãn “tích cực” và “tiêu cực”:

| Bình luận | Điểm cần chú ý | Cách bộ nhãn nháp xử lý |
|---|---|---|
| “Muốn mua, nhưng giá không vừa túi tiền” | Người viết muốn có máy, nhưng chưa chắc đang chê giá đắt. Câu này có thể là mong muốn, cũng có thể là than về khả năng chi trả. | Chiều 2: `gia` (khía cạnh) và `may_chung` (nói về cả máy, không phải khía cạnh). Chiều 3 (viết để làm gì): `ban_than` (mong muốn, than). Chiều 4 (thái độ với giá): `khong_danh_gia`, không ép thành khen hay chê. |
| “Cam ban ngày đẹp, nhưng cam ban đêm xấu” | Cùng một khía cạnh, nhưng đánh giá khác nhau tùy điều kiện chụp. | Chiều 2: `camera`. Chiều 4: cả `tich_cuc` và `tieu_cuc`. Điều kiện ngày hay đêm vẫn nằm trong mã (`cam ban ngày: khen; cam ban đêm: chê`). |

Trong bộ nhãn nháp, chiều 4 (thái độ) có bốn nhãn: `tich_cuc` (khen), `tieu_cuc` (chê, hoặc báo lỗi), `so_sanh` (so với máy khác) và `khong_danh_gia` (hỏi, kể, giải thích… mà không nói tốt hay xấu). Thái độ được gán cho từng phần của điện thoại mà bình luận nhắc tới, nên một bình luận có thể có nhiều thái độ với cùng một khía cạnh, như ví dụ về camera ở trên.

## 7. Cách xây dựng bộ nhãn: lấy mẫu và sử dụng thống kê

### 7.1. Vì sao không gán nhãn toàn bộ dữ liệu bằng tay?

Bỏ các bình luận rỗng thì còn 473.741 bình luận. Giả sử mỗi bình luận mất một phút để đọc và gán nhãn, nhóm sẽ cần khoảng 7.900 giờ làm việc, tương đương gần 1.000 ngày làm việc tám tiếng.

Đây là khối lượng không thực tế, nên nhóm đọc một mẫu nhỏ hơn. Nếu mẫu được chọn **ngẫu nhiên** và nhãn được kiểm cẩn thận, kết quả trên mẫu có thể dùng để ước lượng cho toàn bộ dữ liệu, kèm khoảng tin cậy cho biết ước lượng đó có thể lệch bao nhiêu.

### 7.2. Quy trình lấy mẫu và xây dựng nhãn

Quy trình gồm chín bước. Bước 1–5 đã xong; bước 6 có bản nháp; bước 7 đã chạy thuật toán nhưng chưa đối chiếu; bước 8 và 9 chưa làm.

| Bước | Công việc | Cách thực hiện và mục đích |
|---|---|---|
| **1. Lấy mẫu ngẫu nhiên** | Chọn 800 bình luận | Lấy ngẫu nhiên đơn, không hoàn lại. Cố định số khởi tạo (seed) `20261122` để ai chạy lại cũng thu được đúng 800 bình luận đó. |
| **2. Chia mẫu thành các lô** | Chia 800 bình luận thành lô 1–5, lô K, D1 và D2 | Lô 1–5 (500 bình luận, mỗi lô 100) để đọc và tìm nhãn. Lô K (100 bình luận) giữ kín, không ai đọc trước, để thử bộ nhãn. D1 và D2 (200 bình luận) dự trữ. |
| **3. Bổ sung mẫu có chủ đích (CD)** | Chọn thêm 100 bình luận theo 12 từ khóa | Để không sót nội dung hiếm mà quan trọng, ví dụ bình luận chứa “lỗi”, “bảo hành”, “trả góp”. Mẫu này không ngẫu nhiên, nên **chỉ dùng để tìm nhãn, không dùng để tính tỷ lệ**. |
| **4. Đọc và ghi mã** | Mã hóa mở (*open coding*) | Claude đọc lô 1–5 và CD (600 bình luận), ghi mã dạng `đối tượng: hành vi` bằng chính chữ của bình luận, không chọn từ danh sách có sẵn. Ví dụ “pin trâu, cam đêm hơi nhòe” ghi là `pin: khen; cam đêm: chê`. |
| **5. Kiểm tra mã hóa độc lập** | Trưởng nhóm ghi mã lại 600 bình luận đó | Không xem mã của Claude. Mức độ nhất quán đo bằng Cohen's kappa trên **hành vi** (khen, chê, hỏi…), vì hành vi chọn trong một bảng cố định, còn đối tượng là chữ tự do. |
| **6. Tổng hợp thành bộ nhãn** | Gom các mã cùng nghĩa | Gom mã của Claude thành nhãn, xếp vào sáu chiều; mã của trưởng nhóm để dành làm phép kiểm. Theo dõi **bão hòa**: lô cuối không có nhãn nào xuất hiện lần đầu thì không cần đọc thêm. |
| **7. Đối chiếu bằng HAC** | Chạy HAC trên 473.741 bình luận không rỗng | Đã chạy ngày 22/11. Sau khi bộ nhãn được duyệt, dùng kết quả để tìm khía cạnh mà mẫu nhỏ có thể sót. Phần này do AI đối chiếu, không có người chấm, và không dùng để tính tỷ lệ. |
| **8. Kiểm tra mù trên lô K** *(chưa làm)* | Hai bên gán nhãn 100 bình luận của lô K | Gán theo bộ nhãn, không xem của nhau, rồi tính kappa cho từng chiều (chiều cho phép nhiều nhãn thì tính cho từng nhãn). Từ 0,6 trở lên thì dùng; dưới 0,6 thì sửa định nghĩa rồi kiểm lại. |
| **9. Ước lượng tỷ lệ** *(chưa làm)* | Tính mỗi nhãn chiếm bao nhiêu phần trăm | Tính trong mẫu 600 (mẫu số như mục 6), kèm khoảng tin cậy 95% bằng hai cách: Wilson và bootstrap theo video (mục 7.3). |

### 7.3. Vì sao chọn 500 bình luận để khám phá và 600 bình luận để ước lượng?

**500 bình luận cho giai đoạn khám phá nhãn.** Mục tiêu là không sót những nhãn hiếm. Nếu một nhãn chiếm tỷ lệ `p` trong **toàn bộ dữ liệu**, xác suất gặp nhãn đó ít nhất một lần khi đọc `n` bình luận ngẫu nhiên là:

```text
P(gặp ít nhất một lần) = 1 − (1 − p)^n
```

Xác suất gặp ít nhất một lần trong một vài trường hợp:

| Tỷ lệ của nhãn trong toàn bộ dữ liệu (p) | Đọc 300 bình luận | Đọc 500 bình luận |
|---|---:|---:|
| 0,5% | 78% | 92% |
| 1% | 95% | 99,3% |

Như vậy, với 500 bình luận ngẫu nhiên, khả năng bắt gặp một nhãn có tỷ lệ 0,5% đã vào khoảng 92%. Đây là cơ sở để nhóm chọn 500 bình luận cho bước khám phá ban đầu. Tuy nhiên, điều này không bảo đảm rằng mọi nhãn hiếm đều sẽ xuất hiện trong mẫu.

**600 bình luận cho giai đoạn ước lượng tỷ lệ.** Mẫu này gồm 500 bình luận ở lô 1–5 và 100 bình luận ở lô K. Cả 600 đều là bình luận ngẫu nhiên; 100 bình luận có chủ đích không nằm trong mẫu này.

Với mức tin cậy 95%, sai số của một tỷ lệ (nửa độ rộng khoảng tin cậy) xấp xỉ:

```text
E = z × √( p × (1 − p) / n )        với z = 1,96
```

Trong đó `p` là tỷ lệ cần ước lượng, `n` là số bình luận ở mẫu số.

Với `n = 600`:

| Tỷ lệ của nhãn | Sai số gần đúng (điểm phần trăm) |
|---|---:|
| 50% | ±4,0% |
| 10% | ±2,4% |
| 3% | ±1,4% |

Với nhãn chiều 2, mẫu số nhỏ hơn 600 nên sai số lớn hơn. Ví dụ, nếu mẫu số là 450 thì nhãn chiếm 10% có sai số khoảng ±2,8 điểm, nhãn chiếm 3% khoảng ±1,6 điểm.

Nếu một nhãn không xuất hiện lần nào trong 600 bình luận thì vẫn chưa thể nói nó không tồn tại. Theo quy tắc ba (*rule of three*), tỷ lệ thật vẫn có thể lên tới khoảng 3/600 = 0,5% (cận trên 95%, coi các bình luận là độc lập).

**Khoảng tin cậy sẽ được tính như thế nào?** Nhóm sẽ báo cả hai cách:

- **Wilson:** coi các bình luận là độc lập với nhau. Cách này tốt hơn công thức xấp xỉ ở trên khi tỷ lệ nhỏ: không cho ra số âm, và không cho khoảng rỗng khi nhãn không xuất hiện lần nào.
- **Bootstrap theo video (cách chính):** bốc lại ngẫu nhiên *cả video*, có hoàn lại, 2.000 lần; mỗi lần tính lại tỷ lệ; khoảng tin cậy lấy từ phân vị 2,5% đến 97,5% của 2.000 kết quả đó. Lý do: bình luận dưới cùng một video có thể giống nhau, nếu coi là độc lập thì khoảng tin cậy sẽ hẹp hơn mức hợp lý.

### 7.4. Đánh giá mức độ nhất quán giữa hai bên bằng Cohen's kappa

Cohen's kappa đo mức độ đồng thuận giữa hai bên, sau khi trừ phần giống nhau do ngẫu nhiên:

```text
κ = (p_o − p_e) / (1 − p_e)
```

Trong đó:

- `p_o` là tỷ lệ bình luận mà hai bên ghi giống nhau;
- `p_e` là tỷ lệ giống nhau nếu hai bên chỉ trùng nhau do ngẫu nhiên.

Kappa bằng 1 nghĩa là hai bên giống nhau hoàn toàn; bằng 0 nghĩa là mức giống nhau không cao hơn trùng hợp ngẫu nhiên. Ví dụ, với hành vi `nhắc`, hai bên ghi giống nhau ở 97% số bình luận, nhưng chủ yếu vì cả hai hiếm khi dùng hành vi này; kappa chỉ đạt 0,18.

Nhóm đặt ngưỡng **κ ≥ 0,6** để quyết định một chiều có được dùng tiếp hay không. Đây là ngưỡng nhóm tự chọn; đạt ngưỡng không bảo đảm rằng nhãn đã đúng.

## 8. Kết quả hiện tại đến ngày 25/11/2026

Các kết quả trong phần này chủ yếu là **số đếm trên mẫu đã đọc**, chưa phải tỷ lệ đại diện cho toàn bộ 473.786 bình luận. Cần phân biệt rõ số lượng quan sát được trong mẫu với tỷ lệ ước lượng cho tổng thể.

### Kết quả nằm ở đâu, trông như thế nào

| Kết quả | File | Nội dung |
|---|---|---|
| **Danh sách khía cạnh, nhãn thái độ (cảm xúc) và các nhãn khác** | [đặc tả bộ nhãn](docs/3-gan-nhan/dac-ta-bo-nhan.md): khía cạnh ở mục 2.1, nhãn ngoài khía cạnh 2.2, thái độ mục 4, các chiều còn lại ở mục 1, 3, 5, 6. Bản rút gọn kèm số đếm ở phần “Bộ nhãn nháp” bên dưới | Mỗi nhãn một dòng: tên, định nghĩa, ví dụ thuộc, ví dụ dễ nhầm, các mã đã gom vào |
| **Đầu ra của mã hóa mở** | `data/kham-pha/phieu_ma_hoa_mo.csv` (Claude) và `phieu_ma_hoa_mo_B.csv` (trưởng nhóm) | 600 dòng, mỗi dòng một bình luận; mã nằm ở cột `ma_tu_do`. Ví dụ: `chụp đêm: so sánh (android hơn iphone); quay phim: so sánh (iphone hơn android)` |
| Thống kê mã hóa mở | [báo cáo mã hóa mở](docs/3-gan-nhan/bao-cao-ma-hoa-mo.md) | Số mã theo lô, hành vi và đối tượng hay gặp |
| So hai bên | `data/kham-pha/dong_thuan_ma_hoa_mo.csv`, `lech_ma_hoa_mo.csv` | Kappa của 32 hành vi; 248 bình luận hai bên ghi hành vi khác nhau |
| Số đếm của từng nhãn | [báo cáo bộ nhãn](docs/3-gan-nhan/bao-cao-bo-nhan.md) | Số bình luận có mỗi nhãn, lô gặp lần đầu, bão hòa |
| **Đầu ra của HAC** | `data/kham-pha/hac_ung_vien.csv` | 300 dòng, mỗi dòng một ứng viên khía cạnh: hạng, điểm HAC, số bình luận, 5 từ đánh giá hay đi kèm, 3 câu ví dụ. Ví dụ hạng 1: `pin`, 4.759 điểm, 4.540 bình luận, hay đi với trâu (2.260), yếu (505), tốt (299) |

Các file trong `data/` nằm ngoài git vì có chữ bình luận thật, nên chỉ có trên máy của trưởng nhóm.

### Mẫu đã chọn và phần đã đọc

Nhóm đã chọn tổng cộng 900 bình luận, gồm:

- 800 bình luận lấy ngẫu nhiên;
- 100 bình luận bổ sung có chủ đích theo từ khóa.

Trong số này, **600 bình luận đã được cả hai bên đọc và ghi mã**: 500 bình luận thuộc lô 1–5 và 100 bình luận trong mẫu có chủ đích. Lô K cùng hai lô dự trữ D1, D2, tổng cộng 300 bình luận, chưa ai đọc.

Cần phân biệt hai con số 600:

- **600 bình luận đã đọc** = 500 bình luận lô 1–5 + 100 bình luận có chủ đích.
- **600 bình luận để tính tỷ lệ** = 500 bình luận lô 1–5 + 100 bình luận lô K. Cả 600 đều là bình luận ngẫu nhiên, nằm dưới 507 video khác nhau.

### Kết quả mã hóa mở

Từ 600 bình luận, Claude ghi được 843 mã, với 523 đối tượng khác nhau; 444 đối tượng trong số đó chỉ gặp đúng một lần. Nếu giữ nguyên từng đối tượng thì quá vụn, nên phải gom những mã có ý nghĩa gần nhau thành nhãn.

### Mức độ đồng thuận giữa hai bên mã hóa

Trưởng nhóm và Claude đều ghi mã cả 600 bình luận, không xem mã của nhau; so được 599 bình luận (một dòng bị Excel làm hỏng). Với mỗi *hành vi* (người viết làm gì: khen, chê, hỏi…), mỗi bình luận là một câu hỏi có/không: “bình luận này có hành vi đó không?”. Trong 32 hành vi có ít nhất một bên dùng, 21 hành vi đạt κ ≥ 0,6. Đây là mức đồng thuận giữa **một người và một AI**, chưa phải giữa hai người.

| Nhóm | Hành vi và kappa |
|---|---|
| **κ ≥ 0,6** (21 hành vi) | quảng cáo 1,00 · cảm ơn 1,00 · cười 1,00 · khoe 0,89 · hỏi 0,88 · dự thi 0,85 · yêu cầu 0,85 · than 0,82 · chửi 0,80 · khen 0,77 · khuyên 0,77 · trả lời 0,75 · chê 0,74 · cãi nhau 0,72 · giải thích 0,72 · xin 0,67 · không hiểu (`?`) 0,66 · đùa 0,65 · mong muốn 0,64 · chào 0,62 · góp ý 0,61 |
| **κ < 0,6** (11 hành vi) | phản bác 0,59 · so sánh 0,58 · cà khịa 0,55 · bênh 0,51 · đồng tình 0,47 · dự đoán 0,41 · nhận xét 0,38 · kể 0,37 · lo ngại 0,35 · trêu 0,22 · nhắc 0,18 |

Những hành vi rất hiếm thì kappa không ổn định, kể cả khi cao: quảng cáo, cảm ơn, cười chỉ gặp 2–4 lần; `trêu`, `lo ngại` thì Claude chỉ dùng 1 và 3 lần. Các hành vi còn lại có kappa thấp chủ yếu vì định nghĩa chưa đủ rõ. Bảng định nghĩa hành vi đã được sửa ngày 23/11, còn mã của hai bên ở đây ghi theo bảng **trước khi sửa**, nên kết quả này chưa phải đánh giá cho bản đã sửa.

### Bộ nhãn nháp: danh sách nhãn và số đếm

Từ kết quả khám phá ban đầu, nhóm đã hình thành bộ nhãn nháp gồm **6 chiều và 43 nhãn**, trong đó **13 nhãn là khía cạnh**. Bộ nhãn này đang chờ trưởng nhóm xem xét và phê duyệt.

Bảng dưới đây cho biết **số bình luận** có mỗi nhãn trong 500 bình luận thuộc lô 1–5, theo mã của Claude. Các số này **chưa được người kiểm** và **không phải tỷ lệ**. Ở chiều 2, 3 và 4, một bình luận có thể có nhiều nhãn, nên cộng lại không bằng 500. Chữ dạng `ten_nhan` là tên nhãn dùng trong file và code; định nghĩa từng nhãn ở [đặc tả bộ nhãn](docs/3-gan-nhan/dac-ta-bo-nhan.md).

| Chiều | Số bình luận có mỗi nhãn |
|---|---|
| **1. Bình luận nói về cái gì** (6 nhãn) | điện thoại `dien_thoai` 371 · video, người review `ngu_canh` 64 · người bình luận khác `nguoi_binh_luan` 32 · không rõ `khong_xac_dinh` 24 · không có nội dung `khong_noi_dung` 5 · không liên quan `khong_lien_quan` 4 |
| **2. Nói về phần nào của điện thoại** (15 nhãn, chỉ gán cho 371 bình luận về điện thoại) | **13 khía cạnh:** hiệu năng `hieu_nang` 42 · camera `camera` 39 · thiết kế `thiet_ke` 36 · giá `gia` 33 · phần mềm `phan_mem` 29 · màn hình `man_hinh` 27 · mua bán `mua_ban` 25 · phần cứng khác `phan_cung_khac` 24 · pin và sạc `pin_sac` 19 · độ bền `do_ben` 9 · âm thanh `am_thanh` 9 · nhiệt độ `nhiet_do` 4 · bảo hành, sửa chữa `bao_hanh_sua_chua` 3. **2 nhãn không phải khía cạnh:** nói chung về cả máy `may_chung` 102 · hãng, fan `hang_nguoi_dung` 45 |
| **3. Viết để làm gì** (13 nhãn) | đánh giá `danh_gia` 207 · cung cấp thông tin `thong_tin` 76 · hỏi `hoi` 55 · đề nghị `de_nghi` 48 · nói về bản thân (kể, mong muốn, than) `ban_than` 47 · tranh luận `tranh_luan` 47 · công kích `cong_kich` 47 · đùa `dua` 27 · không rõ `khong_xac_dinh` 15 · xã giao `xa_giao` 13 · dự thi, xin quà `minigame` 10 · báo lỗi `bao_loi` 2 · quảng cáo `quang_cao` 1 |
| **4. Thái độ, tức cảm xúc** (4 nhãn, gán cho từng cặp bình luận và nhãn chiều 2) | khen `tich_cuc` 43 · chê `tieu_cuc` 54 · so sánh `so_sanh` 30 · không đánh giá `khong_danh_gia` 184. Đây là 311 lượt của riêng 13 khía cạnh; một bình luận vừa khen vừa chê một khía cạnh thì tính 2 lượt. |
| **5. Người viết đã dùng máy chưa** (2 nhãn, đếm gần đúng) | nói rõ là đã dùng `co` 33 · không rõ `khong_ro` 467 |
| **6. Có gọi tên máy không** (3 nhãn, đếm gần đúng) | gọi tên một mẫu máy `goi_ten_may` 112 · chỉ nhắc hãng `chi_hang` 82 · không nhắc máy hay hãng nào `khong_nhac` 306 |

Trong 371 bình luận về điện thoại, 260 bình luận nêu ít nhất một khía cạnh; 111 bình luận chỉ nói chung về cả máy hoặc về hãng.

### Kiểm tra mức độ bão hòa

Số nhãn **xuất hiện lần đầu** ở lô 1, 2, 3, 4, 5 lần lượt là **37, 0, 2, 0, 0**, tính trên 39 nhãn của chiều 1, 2, 3, 5, 6 (bốn nhãn thái độ của chiều 4 không tính). Lô 4 và lô 5 không có thêm nhãn nào. Theo luật dừng của nhóm, lô 5 không có nhãn nào xuất hiện lần đầu thì chưa cần đọc các lô dự trữ để tìm thêm nhãn.

### Kết quả đối chiếu bằng HAC

HAC xếp hạng những từ hay đi kèm từ đánh giá (trâu, đẹp, xấu…). Mười từ có điểm cao nhất, gọi là ứng viên khía cạnh, là: **pin, giá, sạc, game, độ, hình, máy, iPhone, dùng, chơi game**.

Một số ứng viên đúng là khía cạnh (pin, giá, sạc), nhưng một số chỉ là mảnh từ hoặc từ chung (“độ”, “hình”, “dùng”). Vì vậy, HAC chỉ đóng vai trò đối chiếu để gợi ý những nội dung có thể cần xem lại, không tự động quyết định danh sách khía cạnh cuối cùng.

### Những việc nhóm vẫn chưa hoàn thành

Tại thời điểm 25/11/2026, nhóm vẫn chưa có:

- Tỷ lệ của từng nhãn, đã được người kiểm và kèm khoảng tin cậy;
- Kết quả gán nhãn mù trên lô K;
- Kết quả chấm mô hình bằng nhãn do người gán trên bình luận YouTube. (Trên `main` đã có một mô hình khía cạnh chấm trên dữ liệu ngoài và một mô hình cảm xúc chấm trên nhãn do LLM gán; hai kết quả này chưa nói được mô hình đúng hay sai trên bình luận YouTube.)

Vì vậy, **không được xem các số đếm trong phần này là tỷ lệ của toàn bộ dữ liệu**. Chúng mới mô tả những gì nhóm quan sát được trong mẫu đã đọc.

## 9. Những việc cần làm tiếp theo

Trước khi gán nhãn chính thức và huấn luyện mô hình, nhóm cần hoàn thành các việc sau:

1. **Trưởng nhóm duyệt bộ nhãn nháp** và trả lời [bốn câu hỏi còn mở](docs/3-gan-nhan/dac-ta-bo-nhan.md#7-cần-trưởng-nhóm-quyết-khi-duyệt).
2. **Hai bên gán nhãn độc lập trên lô K** (100 bình luận chưa ai đọc). Chiều nào κ ≥ 0,6 thì dùng tiếp; chiều dưới 0,6 thì sửa định nghĩa rồi kiểm lại trên 50 bình luận khác chưa ai đọc (lấy từ lô D2).
3. **Gán lại lô 1–5 theo bộ nhãn:** Claude gán, trưởng nhóm kiểm ít nhất 100 bình luận và mọi chỗ Claude đánh dấu chưa chắc. Cộng với lô K thành mẫu 600, rồi tính tỷ lệ từng nhãn cùng khoảng tin cậy.
4. **Chốt bộ nhãn** theo bảng ở mục 6 (giữ, thêm, gộp, bỏ). Nhãn nào cũng phải ghi lý do.
5. **Viết hướng dẫn gán nhãn**, rồi gán nhãn chính thức hai mẫu: một mẫu lấy từ dữ liệu chưa lọc để đo chất lượng dữ liệu, và một tập test để chấm mô hình (mỗi bình luận hai người gán độc lập). Sau đó huấn luyện, chấm mô hình và trả lời Q1–Q5 (thêm Q6 nếu nhóm chốt) trong phạm vi dữ liệu cho phép.

## Tài liệu đọc thêm

- [Tóm tắt dễ hiểu từ đầu](docs/0-chung/huong-dan-tom-tat.md)
- [Kế hoạch và các quyết định của nhóm](docs/0-chung/ke-hoach.md)
- [Bộ nhãn nháp](docs/3-gan-nhan/dac-ta-bo-nhan.md)
- [Báo cáo số đếm của bộ nhãn](docs/3-gan-nhan/bao-cao-bo-nhan.md)
- [Quy tắc, công thức và giới hạn trong quá trình khám phá nhãn](docs/3-gan-nhan/dac-ta-kham-pha-nhan.md)

---

## Những điểm còn phải quyết

1. **Luật ở mục 6 còn hai chỗ đặc tả chưa nói:**
   - Nhãn từ 1% trở lên mà không phục vụ câu hỏi nào và không giúp đánh giá chất lượng dữ liệu thì làm gì. [Kế hoạch mục 6](docs/0-chung/ke-hoach.md#6-câu-hỏi-của-đề-tài-tóm-tắt) chỉ ghi “không cần gán”. Nếu cũng gộp thì ngưỡng 1% không còn tác dụng.
   - Nhãn tách ra từ một nhãn đặt sẵn (ví dụ `nhiet_do` tách từ Hiệu năng) có tính là nhãn mới hay không.
2. **Thử PhoBERT trước** (đề xuất của trưởng nhóm) **hay mô hình đơn giản trước** (quy ước trên `main`: không mặc định dùng PhoBERT).
3. **Chiều 6 chưa ghi tên máy.** Chiều này chỉ cho biết bình luận có gọi tên máy hay không, chưa ghi là máy nào, trong khi Q3 và Q4 cần biết điều đó.

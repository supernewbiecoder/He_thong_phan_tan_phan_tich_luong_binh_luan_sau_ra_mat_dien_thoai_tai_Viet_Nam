# Mục tiêu và câu hỏi của đề tài

> Mục đích: Nói rõ đề tài làm để làm gì, phải giao ra cái gì, và từng câu hỏi cần trả lời: đo bằng gì, cần dữ liệu gì, ra kết quả gì, khi nào được kết luận; cập nhật lần cuối: 2026-11-20.

**Trạng thái:** bản đề xuất, nhóm chưa chốt đề tài. Câu Q6 và bộ 4 máy đang chờ nhóm quyết. Tiến độ và các quyết định đang chờ: [kế hoạch](ke-hoach.md).

## 1. Bài toán

Một hãng điện thoại vừa ra mắt **máy X** và muốn biết người dùng Việt Nam đánh giá X thế nào so với đời trước và các đối thủ. Nhóm lấy bình luận tiếng Việt dưới các video review, đập hộp, so sánh trên YouTube để trả lời.

## 2. Mục đích

Kết quả phải giúp người làm sản phẩm và marketing của hãng trả lời được:

- X đang được đón nhận tốt hay dở, và đang tốt lên hay xấu đi qua từng tuần;
- người dùng thích gì, ghét gì ở X;
- X hơn, kém đối thủ ở điểm nào;
- điểm yếu của đời trước đã được sửa chưa;
- lỗi nào cần sửa trước;
- phần bình luận có bị tài khoản ảo làm méo hay không, để không ra quyết định dựa trên số liệu đã bị thao túng.

## 3. Mục tiêu (phải giao ra)

1. Trả lời Q1–Q5 cho **một bộ 4 máy**. Mỗi kết luận kèm khoảng tin cậy, và chỉ đưa ra khi chênh lệch có ý nghĩa thống kê.
2. Mô hình gắn nhãn cho từng bình luận: các bộ (máy được nhắc, khía cạnh, khen/chê). Đo độ chính xác trên tập test gán tay, so với luật từ khóa làm mốc.
3. Q6 (nếu nhóm chốt): tỷ lệ bình luận có dấu hiệu phối hợp, và kết quả Q1–Q5 lệch bao nhiêu khi bỏ chúng.
4. Dashboard và báo cáo. Mọi con số chạy lại được từ code trong repo, ghi rõ phiên bản dữ liệu.

## 4. Phạm vi

- **Bốn máy:**
  - **X**: máy vừa ra mắt;
  - **P**: đời trước của X;
  - **R1, R2**: hai đối thủ cùng phân khúc, ra mắt gần cùng thời điểm.

  Ví dụ: X = Galaxy S26 Ultra, P = Galaxy S25 Ultra, R1 = iPhone 17 Pro Max, R2 = Xiaomi 17 Ultra. Bộ chính thức chốt ở Công việc 2.
- **Cửa sổ:** 4 tuần kể từ `launch_date` của từng máy. `launch_date` là ngày công bố đầu tiên (toàn cầu, hoặc Trung Quốc với máy ra mắt ở đó trước), không phải ngày bán ở Việt Nam.
- **Nguồn:** YouTube. Nguồn khác là Công việc 15.
- **9 khía cạnh:** Pin & sạc, Màn hình, Hiệu năng (gồm nóng máy), Camera, Thiết kế & độ bền, Phần mềm, Phần cứng khác, Giá, Bảo hành & hậu mãi. Định nghĩa ở [data-model.md](thiet-ke-du-lieu.md#danh-mục-mã).
- **Đơn vị đếm:** bộ (bình luận, máy, khía cạnh): một bình luận nói về một khía cạnh của một máy. Chốt 20/11 (phương án A); trước đó đơn vị là mệnh đề.
  - "Cam đẹp nhưng pin yếu" là 2 đơn vị: Camera–khen, Pin–chê.
  - "Pin tốt, pin trâu, sạc nhanh" là **1** đơn vị Pin–khen, không phải 3: người viết nhiều dấu phẩy không được nhiều phiếu hơn.
  - Vừa khen vừa chê cùng khía cạnh ("cam ngày đẹp, đêm kém") tính 1 khen và 1 chê.
- **Máy được tính:** máy mà nhận xét nhắc tới, xét cả bình luận, không phải máy của video. Dưới video S26 Ultra, "iPhone thì pin trâu, camera đẹp" tính cả pin lẫn camera cho iPhone.
- **Ngoài phạm vi:**
  - hình ảnh, âm thanh, nội dung của video;
  - bình luận không phải tiếng Việt;
  - tên thật người bình luận (chỉ dùng `author_hash`).

## 5. Các câu hỏi

| # | Câu hỏi | Đầu ra chính |
|---|---|---|
| Q1 | X được đón nhận tốt hay dở? | Net cảm xúc theo tuần, 4 máy |
| Q2 | X có ưu, nhược điểm gì? | % khen/chê theo 9 khía cạnh của X, kèm bình luận thật |
| Q3 | So với đối thủ, X mạnh, yếu ở đâu? | Ma trận khía cạnh × máy; tỷ lệ thắng trong câu so sánh trực tiếp |
| Q4 | Đời trước bị chê gì, đời này đã sửa chưa? | % chê từng khía cạnh, P → X |
| Q5 | Lỗi gì cần sửa, sửa cái nào trước? | Bảng lỗi do người đã dùng báo, xếp ưu tiên |
| Q6 | Có tài khoản ảo seeding, quậy phá không, và nó làm lệch kết quả bao nhiêu? (đề xuất) | Tỷ lệ bình luận nghi vấn; Q1–Q5 khi giữ và khi bỏ chúng |

### Q1. X được đón nhận tốt hay dở?

| | |
|---|---|
| **Ý nghĩa** | Nhìn tổng thể, người dùng khen hay chê X nhiều hơn, so với P, R1, R2, và thay đổi qua từng tuần |
| **Đo bằng** | Net cảm xúc theo (máy, tuần 1–4), gộp mọi khía cạnh |
| **Đầu ra** | Biểu đồ đường 4 tuần, mỗi máy một đường, có dải khoảng tin cậy; bảng Net cả 4 tuần |
| **Kết luận khi** | "X được đón nhận tốt/kém hơn R1" chỉ khi chênh lệch có ý nghĩa; không thì ghi "chưa đủ bằng chứng" |

### Q2. X có ưu, nhược điểm gì?

| | |
|---|---|
| **Ý nghĩa** | Trong 9 khía cạnh của X, cái nào được khen nhiều (ưu), cái nào bị chê nhiều (nhược). Chỉ xét X |
| **Đo bằng** | % khen, % chê theo khía cạnh, với máy được nhắc là X |
| **Đầu ra** | Thanh hai chiều (chê bên trái, khen bên phải), sắp theo Net; 2–3 bình luận mẫu mỗi khía cạnh, có người duyệt trước khi đưa vào báo cáo |
| **Kết luận khi** | Nhược điểm là khía cạnh có % chê cao hơn mức chê chung của X một cách có ý nghĩa; ưu điểm thì ngược lại |

### Q3. So với đối thủ, X mạnh, yếu ở đâu?

| | |
|---|---|
| **Ý nghĩa** | X hơn hay kém từng đối thủ ở khía cạnh nào |
| **Đo bằng** | (a) % khen của 9 khía cạnh × 4 máy. (b) Câu so sánh trực tiếp, vd "S26U chụp đêm hơn iPhone": % X thắng theo khía cạnh |
| **Đầu ra** | Bảng tô màu khía cạnh × máy; thanh 100% "X thắng / đối thủ thắng" kèm số câu |
| **Kết luận khi** | Ô tốt nhất chỉ in đậm khi hơn có ý nghĩa; không có ý nghĩa thì ghi "chưa phân định" |

### Q4. Đời trước bị chê gì, đời này đã sửa chưa?

| | |
|---|---|
| **Ý nghĩa** | Điểm yếu của P có còn ở X không |
| **Đo bằng** | % chê từng khía cạnh của P và của X, cùng công thức với Q2 |
| **Đầu ra** | Biểu đồ dốc: mỗi khía cạnh một đường P → X, đường có ý nghĩa vẽ đậm |
| **Kết luận khi** | Chỉ dùng 3 nhãn: "Đã cải thiện" (giảm có ý nghĩa), "Tệ hơn" (tăng có ý nghĩa), "Chưa đủ bằng chứng" |
| **Đối chứng** | So thêm một cặp đời máy khác (vd iPhone 16 → 17). Cặp đối chứng thay đổi y hệt thì đó là xu hướng chung, không phải công riêng của X |

### Q5. Lỗi gì cần sửa, sửa cái nào trước?

| | |
|---|---|
| **Ý nghĩa** | Lỗi kỹ thuật do **người đã dùng X** báo, xếp ưu tiên cho đội kỹ thuật |
| **Đo bằng** | Mỗi loại lỗi: số lần nhắc, và tỷ lệ lỗi nửa đầu so với nửa sau cửa sổ |
| **Đầu ra** | Bảng: loại lỗi · số lần nhắc · tăng/giảm · mức ưu tiên · bình luận mẫu |
| **Luật ưu tiên** | P1: từ 20 lần nhắc và tăng có ý nghĩa. P2: từ 20 lần nhắc, xu hướng không có ý nghĩa. P3: dưới 20 lần ("theo dõi, chưa đủ dữ liệu"). Ngưỡng 20 chốt lại sau khi biết số thật |
| **Rủi ro** | Cửa sổ tính từ ngày công bố toàn cầu, nên trong 4 tuần đầu có thể rất ít người ở Việt Nam đã dùng máy |

### Q6. Có tài khoản ảo seeding, quậy phá không? (đề xuất, chờ nhóm chốt)

| | |
|---|---|
| **Ý nghĩa** | Phần bình luận có dấu hiệu phối hợp chiếm bao nhiêu, và nó làm méo kết quả Q1–Q5 tới đâu |
| **Đo bằng** | Bình luận gắn cờ khi: cùng một câu từ nhiều tài khoản; đăng dồn trong vài phút; tài khoản tạo ngay trước ngày ra mắt; một tài khoản dán cùng câu lên nhiều video. Tỷ lệ gắn cờ theo máy, tuần; Net của X khi giữ và khi bỏ chúng |
| **Đầu ra** | Bảng tỷ lệ nghi vấn; phép thử độ nhạy của Q1–Q5; độ chính xác của luật gắn cờ, đo bằng cách duyệt tay các trường hợp bị gắn cờ |
| **Kết luận khi** | Chỉ dùng từ "dấu hiệu". Không ghi hãng nào "thuê bot": dữ liệu không nối được tài khoản với công ty, viết vậy là cáo buộc không có căn cứ |

## 6. Quy ước dùng chung cho mọi câu

- Chỉ đếm các đơn vị có máy được nhắc thuộc 4 máy, nằm trong cửa sổ, của bình luận không phải spam.
- **% khen** = khen / (khen + chê); **% chê** = chê / (khen + chê); **Net** = % khen − % chê, từ −100 tới +100. Nhận xét trung tính không vào mẫu số, chỉ báo cáo số lượng kèm theo.
- Ô có khen + chê dưới 30 thì ghi "ít dữ liệu", không kết luận.
- Mọi tỷ lệ kèm khoảng tin cậy 95%, tính bằng cách rút lại theo video (bootstrap theo video), vì các bình luận cùng video không độc lập.
- Một câu hỏi có nhiều phép kiểm định thì hiệu chỉnh Holm trong câu đó; mức ý nghĩa 0,05 sau hiệu chỉnh.
- Không có ý nghĩa thì viết "chưa đủ bằng chứng", **không** viết "bằng nhau". Không ngoại suy, không dự báo từ vài điểm dữ liệu.
- **Sai số của mô hình (thêm 20/11).** Bootstrap theo video chỉ tính sai số do lấy mẫu; nó coi nhãn của mô hình là đúng. Vì vậy:
  - Công việc 7 đo ma trận nhầm lẫn trên tập test người gán, **theo từng máy × khía cạnh**;
  - mỗi kết luận Q2–Q4 phải qua phép kiểm: chỉnh tỷ lệ khen/chê theo ma trận đó, kết luận còn đứng không;
  - không đứng thì ghi "chưa đủ bằng chứng". Mô hình bắt chê ở máy này kém hơn ở máy kia sẽ làm lệch Q3 một cách có hệ thống.
- **Độ nhạy (thêm 20/11).** Mỗi kết luận chạy lại khi:
  - bỏ video lớn nhất, kênh lớn nhất;
  - mỗi tác giả chỉ tính một phiếu;
  - chỉ lấy bình luận gốc, bỏ reply;
  - bỏ video tặng quà;
  - bỏ bình luận bị gắn cờ Q6.

  Kết luận đổi chiều ở phép nào thì ghi rõ trong báo cáo. Riêng Q6: thêm bình luận giả lập để biết cần bao nhiêu bình luận seeding thì kết luận đảo chiều.
- **Chọn mô hình (thêm 20/11).** Chọn mô hình **đơn giản nhất** mà kết luận Q1–Q5 không khác kết luận của mô hình tốt nhất. F1 cao hơn mà kết luận không đổi thì không cần mô hình phức tạp hơn.

Dữ liệu mỗi câu cần lấy từ bảng nào: [data-model.md mục 8](thiet-ke-du-lieu.md#8-câu-hỏi--dữ-liệu). Số liệu mô tả dữ liệu (số bình luận, độ dài, ngôn ngữ, thời gian…) không phải câu hỏi chính. Chúng nằm ở bước kiểm tra dữ liệu gốc (`notebooks/1_raw_audit.ipynb`) và đưa vào phụ lục báo cáo.

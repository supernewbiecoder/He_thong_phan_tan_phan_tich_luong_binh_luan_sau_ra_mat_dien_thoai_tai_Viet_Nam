Bối cảnh: công ty vừa ra mắt máy X và muốn biết X có ưu, nhược điểm gì, so với các dòng khác thì thế nào.
Phạm vi: 4 máy, gồm X, đời trước của X, và 2 đối thủ cùng phân khúc ra mắt cùng thời điểm. Mọi so sánh tính trong cùng một cửa sổ, ví dụ 8 tuần đầu kể từ ngày ra mắt của từng máy.
Thuật ngữ dùng thống nhất: **Aspect** = nhóm tính năng/chủ đề (Camera, Pin & sạc, Nhiệt độ, Hiệu năng, Màn hình, Thiết kế, Giá bán, Phần mềm); **Sentiment** = khen/chê; **Brand** = hãng; **Model** = dòng máy.
Dữ liệu cần gán nhãn cho cả 4 máy: Model được nhắc, Aspect, Sentiment, có phải lỗi kỹ thuật không, người viết đã dùng máy chưa.
5 câu hỏi sếp sẽ hỏi → bằng chứng → biểu đồ
1. X được đón nhận tốt hay dở?
Bằng chứng: tỷ lệ khen trừ tỷ lệ chê của X, so với đời trước và đối thủ.
Biểu đồ: line theo tuần kể từ ngày ra mắt, 4 đường cho 4 máy, cùng mốc ngày 0.
2. Ưu điểm và nhược điểm của X là gì?
Bằng chứng: tỷ lệ khen/chê theo từng Aspect, kèm 2–3 bình luận thật cho mỗi Aspect.
Biểu đồ: bar 2 chiều, chê kéo sang trái màu đỏ, khen sang phải màu xanh.
3. So với đối thủ, X mạnh/yếu ở đâu?
Bằng chứng:
Tỷ lệ khen từng Aspect của 4 máy.
Bình luận so sánh trực tiếp (“X chụp đêm thua Y”): bên nào thắng bao nhiêu %.
Biểu đồ: bảng Aspect × Model, ô tô màu theo tỷ lệ khen, ô tốt nhất mỗi hàng được in đậm.
4. Đời trước bị chê gì, đời này đã sửa được chưa?
Bằng chứng: tỷ lệ chê từng Aspect, đời trước so với X.
Biểu đồ: slope chart, mỗi Aspect một đường nối từ đời trước sang X; đi xuống là đã cải thiện.
5. Lỗi gì cần sửa, ưu tiên cái nào?
Bằng chứng: chỉ tính lỗi do người đã dùng báo; xếp theo số lần nhắc và xu hướng tăng/giảm.
Biểu đồ: bảng ưu tiên gồm: lỗi | số lần nhắc | ↑/↓ | bình luận mẫu.
Kiểm định giả thiết (phần “mô hình thống kê”)
Mỗi kết luận phát biểu thành một giả thiết rồi kiểm định, ví dụ:
“Tỷ lệ chê pin của X thấp hơn đời trước” → z-test hai tỷ lệ.
“Tỷ lệ khen Aspect Camera khác nhau giữa 4 máy” → chi-square.
“Lỗi nóng máy đang tăng theo tuần” → kiểm định xu hướng (Mann-Kendall).
Chỉ đưa vào báo cáo những khác biệt có ý nghĩa thống kê. Đây chính là bằng chứng để sếp tin: kết luận không phải chênh lệch ngẫu nhiên.
Không show cho sếp
Số lượng comment, độ dài comment, wordcloud, phân bố theo năm. Mấy thứ này là EDA, để ở phụ lục để chứng minh dữ liệu đủ dùng.

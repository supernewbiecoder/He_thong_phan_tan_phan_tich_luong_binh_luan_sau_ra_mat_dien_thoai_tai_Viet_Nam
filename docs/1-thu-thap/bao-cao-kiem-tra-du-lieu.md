# Báo cáo kiểm tra cấu trúc dữ liệu v4

> Mục đích: Số liệu cấu trúc của dữ liệu v4 (bước B1 của kế hoạch nhánh): Level 0, theo máy, thời gian, kênh, video, reply, và điều rút ra cho bước khám phá nhãn; cập nhật lần cuối: 2026-11-22.

**Trạng thái:** B1 xong. Chạy `notebooks/1_raw_audit.ipynb` (bản 22/11 trên nhánh) ngày 22/11/2026, trên v4: 473.786 dòng, SHA-256 `722d0e1e…2b45`. Hết 24 ô code, không lỗi, khoảng 42 giây.

Số Level 0 (mục 1) **trùng khớp từng con số** với lần chạy ngày 11/11 trên `main`, nên kết quả tái lập được. Cách chạy lại: [hướng dẫn](huong-dan-kiem-tra-du-lieu.md).

Dữ liệu là gì: [đặc tả dữ liệu](dac-ta-du-lieu-v4.md).

## 1. Level 0

Tỷ lệ tính trên 473.786 bình luận.

| Chỉ số | Giá trị |
|---|---|
| Bình luận × trường | 473.786 × 21 |
| Bình luận gốc / reply | 271.375 (57,3%) / 202.411 (42,7%) |
| Video có bình luận | 4.682; trong đó 1.027 video (21,9%) có dưới 10 bình luận |
| Thời gian đăng | 11/04/2014 – 20/10/2026 |
| Bình luận rỗng | 42; thêm 5 bình luận chỉ có ký tự vô hình (tổng 47) |
| Trùng `comment_id` | 0 |
| Trùng nội dung với bình luận khác | 19.510 (4,12%) |
| Một người đăng lại cùng nội dung | 7.584 (1,60%) |
| Độ dài trung vị | 50 ký tự, 11 từ |
| Bình luận ≤ 2 từ | 26.184 (5,53%) |
| Bình luận > 1.000 ký tự | 328 (0,07%) |
| Chỉ có emoji | 2.433 (0,51%) |
| Có URL / chỉ có URL | 10.682 (2,25%) / 169 (0,04%) |
| Ngôn ngữ (luật đơn giản) | tiếng Việt 445.150 (93,96%); tiếng Việt không dấu 7.811 (1,65%); không rõ 14.080 (2,97%); không có chữ 4.555 (0,96%); tiếng Anh 2.000 (0,42%); ngôn ngữ khác 190 (0,04%) |
| Ngày tăng đột biến | 116 |
| Đăng dồn (≥ 3 lần cùng nội dung trong 10 phút) | 308 nhóm, 1.360 bình luận (0,29%) |
| Video tặng quà trong top 5 video đông nhất | 4/5, cộng lại 15.998 bình luận (3,38%), đọc tiêu đề bằng mắt (xem mục 2, dòng video tặng quà) |
| Video trong `videos.jsonl` | 5.167; 507 video không có bình luận nào; 22 video có bình luận nhưng thiếu trong `videos.jsonl` (1.312 bình luận) |

## 2. Theo máy, thời gian, kênh, video

"Lượt": một bình luận dưới video so sánh 2 máy tính cho cả 2 máy, nên tổng là 480.873 lượt cho 473.786 bình luận.

| Chỉ số | Giá trị |
|---|---|
| Số máy có bình luận / máy trong config không có bình luận | 127 / 12 |
| Máy có dưới 3.000 lượt bình luận | 81 trên 127 |
| % lượt bình luận tuần 1 / 2 / 3 / 4 sau ra mắt | 38,3 / 27,7 / 20,6 / 13,3 |
| Lượt bình luận ngoài tuần 1–4 | 673. Gặp ở vài máy (s26u 280, s24u 57, note8 36, ip16prm 27…). Chưa kiểm vì sao; nhiều khả năng là video so sánh nhiều máy, bình luận nằm trong cửa sổ của máy kia |
| Bộ 4 máy ứng viên (bộ cũ, chưa chốt): bình luận / video | s23u 17.021 / 178 · s22u 3.962 / 58 · ip14prm 22.140 / 160 · xiaomi13u 2.356 / 32 |
| Số kênh; % bình luận của 5 / 10 kênh lớn nhất | 44 kênh; 62,7% / 86,8%. Kênh lớn nhất (Vật Vờ Studio) chiếm 22,85% |
| % bình luận theo loại video (đoán từ tiêu đề) | review 53,16 · compare 25,44 · unbox 16,80 · long_term 4,33 · không rõ 0,28 |
| Video tặng quà theo `QUA_RE` | 53 video, 6.865 bình luận (1,45%). **Không dùng được**: `QUA_RE` sai cả hai chiều (mục 3, điểm 3) |
| Reply | 42,72% bình luận; 24,72% bình luận gốc có ít nhất 1 reply lấy được; reply theo YouTube 234.071, lấy được 202.411 (86,5%); 171 reply mồ côi (không có bình luận gốc trong dữ liệu) |
| Bình luận của chủ kênh | 13.462 (2,84%): 1.793 bình luận gốc, 11.669 reply |
| % bình luận 0 like | 70,8%; trung vị 0 like, cao nhất 2.829 |

## 3. Điều rút ra cho bước khám phá nhãn

1. **Dữ liệu sạch về kỹ thuật.** Không trùng `comment_id`, bình luận rỗng không đáng kể. Có thể lấy mẫu trực tiếp từ file raw, chỉ cần làm sạch nhẹ trên mẫu (bỏ ký tự vô hình, giải HTML entity).
2. **Bình luận trùng nội dung chiếm 4,12%.** Chưa biết bao nhiêu trong đó là câu ngắn tự nhiên ("hay", "đẹp"), bao nhiêu là spam hay đăng phối hợp. Khi mã hóa, gặp bình luận trùng thì vẫn mã hóa bình thường, không bỏ.
3. **Video tặng quà là nguồn nhiễu lớn nhất đã thấy, nhưng chưa đếm đúng được.** 4/5 video đông nhất là giveaway (15.998 bình luận). Từ khóa `QUA_RE` của mục 4.3 sai theo hai chiều:
   - **bỏ sót** hai video đông nhất, 5.803 và 5.543 bình luận: tiêu đề dùng "[GA]", "nhận … miễn phí", không có chữ nào trong `QUA_RE`;
   - **bắt nhầm** "giá trừ quà", "quà đặt trước", "tai nghe tặng kèm", "được gửi tặng", "kiểm chứng: tặng iPhone… có phải lừa đảo".

   Vì vậy 6.865 bình luận (1,45%) **không phải** số bình luận dưới video tặng quà; số thật ít nhất là 15.998 (3,38%). Hướng xử lý: không sửa từ khóa ngay, để B7 đo bằng nhãn (bình luận xin quà có nhãn `minigame`, chiều 3); khi cần lọc theo video thì duyệt tay danh sách video. Đây là đầu vào cho quyết định 5 của kế hoạch.
4. **Khoảng 6% không phải tiếng Việt có dấu** (không dấu, không rõ, không có chữ, tiếng Anh, khác). Luật ngôn ngữ ở mục 2.7 chỉ là ước lượng. Mẫu khám phá sẽ cho tỷ lệ do người đọc.
5. **Bình luận rất ngắn (≤ 2 từ) chiếm 5,5%.** Mẫu ngẫu nhiên sẽ có khoảng 15–20 bình luận như vậy trên 300. Không bỏ chúng khỏi mẫu, vì chúng là một phần thật của dữ liệu.
6. **42,7% là reply.** Nhiều reply chỉ hiểu được khi đọc bình luận cha, nên phiếu mã hóa phải hiện kèm bình luận cha.
7. **Máy của video chưa phải máy được nhắc.** Mọi bảng theo máy ở mục 2 đều tính theo máy của video.
8. **Dữ liệu dồn vào ít kênh.** 5 kênh chiếm 62,7% bình luận, riêng một kênh 22,85%. Mẫu ngẫu nhiên sẽ có tỷ lệ tương tự, phản ánh đúng dữ liệu, nhưng phân bố ở B7 tách theo nhóm kênh lớn và kênh còn lại để thấy một kênh có làm lệch kết quả không.
9. **2,84% là bình luận của chủ kênh**, phần lớn là reply cho khán giả. Đó là ý kiến của người làm video, không phải người dùng. Phiếu mã hóa đã có cột `chu_kenh` (đặc tả khám phá nhãn mục 3.5).
10. **Bình luận dồn vào tuần đầu** (38,3% lượt ở tuần 1, 13,3% ở tuần 4). Phân bố nội dung có thể khác giữa các tuần; mẫu 400 bình luận đủ để tách theo tuần 1–2 và 3–4, không đủ cho từng tuần.
11. **Bộ 4 máy cũ không cân:** xiaomi13u chỉ có 2.356 bình luận (32 video), s22u 3.962. Chốt bộ máy thì nên xem bảng mục 3.1 của notebook trước.

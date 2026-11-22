# Báo cáo kiểm tra cấu trúc dữ liệu v4

> Mục đích: Số liệu cấu trúc của dữ liệu v4 (bước B1 của kế hoạch nhánh): Level 0 đã chạy, các mục còn chờ chạy, và điều rút ra cho bước khám phá nhãn; cập nhật lần cuối: 2026-11-22.

**Trạng thái:**
- Mục 1 (Level 0): số lấy từ lần chạy notebook ngày 11/11/2026 trên v4 (SHA-256 `722d0e1e…2b45`), chép từ báo cáo tầng 2 trên `main`.
- Mục 2: **chờ chạy** lại `1_raw_audit` trên nhánh ([hướng dẫn](huong-dan-kiem-tra-du-lieu.md)).

Dữ liệu là gì: [đặc tả dữ liệu](dac-ta.md).

## 1. Level 0 (chạy 11/11/2026)

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
| Video tặng quà trong top 5 video đông nhất | 4/5, cộng lại 15.998 bình luận (3,38%) |

## 2. Theo máy, thời gian, kênh, video (chờ chạy)

| Chỉ số | Giá trị |
|---|---|
| Số máy có bình luận / máy trong config không có bình luận | ___ |
| Máy có dưới 3.000 lượt bình luận | ___ |
| % lượt bình luận tuần 1 / 2 / 3 / 4 sau ra mắt | ___ |
| Lượt bình luận ngoài tuần 1–4 | ___ |
| Bộ 4 máy ứng viên: số bình luận, số video mỗi máy | ___ |
| Số kênh; % bình luận của 5 / 10 kênh lớn nhất | ___ |
| % bình luận theo loại video (review / unbox / compare / long_term) | ___ |
| Video tặng quà (theo `QUA_RE`); số bình luận dưới các video đó | ___ |
| % reply; reply theo YouTube / reply lấy được | ___ |
| Bình luận của chủ kênh | ___ |
| % bình luận 0 like | ___ |

## 3. Điều rút ra cho bước khám phá nhãn

Từ số đã có ở mục 1:

1. **Dữ liệu sạch về kỹ thuật.** Không trùng `comment_id`, bình luận rỗng không đáng kể. Có thể lấy mẫu trực tiếp từ file raw, chỉ cần làm sạch nhẹ trên mẫu (bỏ ký tự vô hình, giải HTML entity).
2. **Bình luận trùng nội dung chiếm 4,12%.** Chưa biết bao nhiêu trong đó là câu ngắn tự nhiên ("hay", "đẹp"), bao nhiêu là spam hay đăng phối hợp. Khi mã hóa, gặp bình luận trùng thì vẫn mã hóa bình thường, không bỏ.
3. **Video tặng quà là nguồn nhiễu lớn nhất đã thấy**: 4/5 video đông nhất, khoảng 16 nghìn bình luận "xin suất". Bộ nhãn nên có cách nhận ra loại này. B6 sẽ cho biết chúng chiếm bao nhiêu trong cả bộ.
4. **Khoảng 6% không phải tiếng Việt có dấu** (không dấu, không rõ, không có chữ, tiếng Anh, khác). Luật ngôn ngữ ở mục 2.7 chỉ là ước lượng. Mẫu khám phá sẽ cho tỷ lệ do người đọc.
5. **Bình luận rất ngắn (≤ 2 từ) chiếm 5,5%.** Mẫu ngẫu nhiên sẽ có khoảng 15–20 bình luận như vậy trên 300. Không bỏ chúng khỏi mẫu, vì chúng là một phần thật của dữ liệu.
6. **42,7% là reply.** Nhiều reply chỉ hiểu được khi đọc bình luận cha, nên phiếu mã hóa phải hiện kèm bình luận cha.
7. **Máy của video chưa phải máy được nhắc.** Mọi bảng theo máy ở mục 2 đều tính theo máy của video.

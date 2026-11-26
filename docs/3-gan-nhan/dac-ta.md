# Đặc tả tầng 3: gán nhãn

> Mục đích: Quy định gán nhãn người cho cả dự án: lấy hai mẫu nào, lấy thế nào, phiếu gán có gì, gán đôi, đo đồng thuận, phân xử, và tính tỷ lệ spam, không liên quan… kèm khoảng tin cậy từ nhãn người; cập nhật lần cuối: 2026-11-26.

**Trạng thái:** đặc tả nháp ngày 20/11, chưa có code. Các script ở mục 9 còn phải viết. Cách gán từng bình luận nằm ở [hướng dẫn gán chính thức](huong-dan-gan-nhan-chinh-thuc.md), file này không chép lại.

**Cập nhật 26/11:** bộ nhãn đã chốt ([đặc tả bộ nhãn mục 8](dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611)). Phần quy trình (hai mẫu, gán đôi, phân xử) vẫn dùng; phần nhãn, phiếu và bộ 4 máy trong file này còn theo bản cũ, sửa ở bước 0.5 của [kế hoạch tổng thể](../0-chung/ke-hoach-tong-the.md).

## 1. Vì sao cần nhãn người

Code đã chạy được cả chuỗi bằng luật mốc `rule-v1`, nhưng chưa biết đúng hay sai. Nhãn người là **mốc độc lập** để:
1. trả lời "dữ liệu có bao nhiêu spam, bao nhiêu bình luận không liên quan, bao nhiêu không phải tiếng Việt" (mẫu A);
2. đo luật và mô hình: khía cạnh, cảm xúc, máy được nhắc, đã dùng máy, loại lỗi, so sánh (mẫu B);
3. đo sai số của mô hình **theo từng máy, từng khía cạnh**, để biết sai số đó có làm lệch kết luận Q1–Q5 không ([muc-tieu.md mục 6](../0-chung/muc-tieu.md#6-quy-ước-dùng-chung-cho-mọi-câu)).

Không dùng kết quả của luật hay mô hình để chứng minh chính nó đúng. Nhãn LLM chỉ dùng để huấn luyện, **không bao giờ** dùng làm tập test.

## 2. Hai mẫu

| | Mẫu A: chất lượng dữ liệu | Mẫu B: tập test mô hình |
|---|---|---|
| Trả lời | Bao nhiêu spam, không liên quan, không phải tiếng Việt; luật gắn cờ đúng bao nhiêu | Luật, mô hình đúng bao nhiêu, theo máy × khía cạnh |
| Lấy từ | **Toàn bộ** file tầng 2, chưa lọc gì (trừ bình luận rỗng) | Bình luận của 4 máy, đã lọc, chỉ trong **video test** |
| Chia tầng theo | Cờ của luật 2.4 | Máy của video × khía cạnh theo từ khóa |
| Cỡ | ~850 | ~800 |
| Gán đôi | ~200 | Toàn bộ |
| Cần có trước | File tầng 2 trên v4 | Bộ 4 máy (CV2), danh sách video test (CV7), guideline v1 đã hiệu chỉnh |

**Vì sao phải có hai mẫu:** mẫu B lấy sau khi đã bỏ spam và tiếng nước ngoài theo luật. Bình luận thật bị luật loại nhầm không bao giờ có mặt trong mẫu B, nên mẫu B không đo được bộ lọc. Mẫu A lấy từ dữ liệu chưa lọc để đo phần đó.

Cả hai mẫu gán theo **cùng một guideline, cùng một phiếu**. Bình luận mẫu A thuộc video train được dùng thêm làm dữ liệu huấn luyện. Bình luận thuộc video test thì không bao giờ dùng để huấn luyện.

## 3. Mẫu A: chất lượng dữ liệu

**Khung:** mọi bình luận trong `data/processed/comments.jsonl` có `text_clean` khác rỗng. Ghi riêng số bình luận rỗng.

**Chia tầng theo cờ của bước 2.4:**

| Tầng | Điều kiện | Cỡ mẫu | Đo được |
|---|---|---|---|
| A1 | `is_spam = true` | 150 | Precision của luật spam |
| A2 | `is_spam = false`, `is_vietnamese = false` | 100 | Precision của luật nhận ngoại ngữ |
| A3 | Còn lại | 600 | Spam bị sót, không liên quan, có khía cạnh, ngoại ngữ bị sót |

- Tầng nào có ít bình luận hơn cỡ mẫu thì lấy hết.
- Lấy ngẫu nhiên đơn trong từng tầng, seed cố định `20261120`, ghi seed và SHA-256 file nguồn vào file mẫu.
- **Gán đôi:** 200 bình luận lấy ngẫu nhiên tỷ lệ theo tầng, hai người gán độc lập. Phần còn lại một người gán.
- Nhãn cần cho mẫu A: `tieng_viet`, `spam`, `lien_quan`, và bộ nhãn nếu có (guideline mục 2, 3).

**Ước lượng tỷ lệ cho cả dữ liệu.** Với mỗi đại lượng (tỷ lệ spam, không liên quan, ngoại ngữ, có ít nhất một bộ nhãn):

```text
p̂ = Σ_h W_h · p̂_h                          W_h = N_h / N  (N_h: số bình luận của tầng h trong khung)
Var(p̂) = Σ_h W_h² · p̂_h (1 − p̂_h) / n_h · (1 − n_h / N_h)
khoảng tin cậy 95%: p̂ ± 1,96 · √Var(p̂)
```

- Tầng có `p̂_h` bằng 0 hoặc 1, hay dưới 5 ca, thì tính khoảng tin cậy bằng bootstrap trong từng tầng (2.000 lần), không dùng công thức xấp xỉ.
- Số lượng cho cả dữ liệu: `N · p̂`, kèm khoảng tin cậy nhân `N`.

**Đo luật gắn cờ:**
- Precision luật spam = tỷ lệ spam thật trong A1.
- Recall luật spam = `N_1 · P̂ / (N_1 · P̂ + N_3 · m̂ + N_2 · m̂_2)`, với `m̂`, `m̂_2` là tỷ lệ spam thật trong A3, A2. Khoảng tin cậy bằng bootstrap phân tầng.
- **Nói trước:** spam bị sót trong A3 hiếm, nên recall sẽ có khoảng tin cậy rộng. Báo cáo đúng như vậy, không thu hẹp bằng cách bỏ khoảng tin cậy.

**Báo cáo:** bảng tỷ lệ kèm khoảng tin cậy cho từng đại lượng; precision và recall của luật; phân bố nhãn; mức đồng thuận (mục 7); 20–30 ví dụ luật sai, chia theo nguyên nhân.

## 4. Mẫu B: tập test mô hình

**Cần có trước:** bộ 4 máy (CV2) và file chia video `data/labels/split.json` (CV7: chia theo `video_id`, phân tầng theo máy của video, khoảng 20–25% số video vào test).

**Khung:** bình luận
- thuộc video test của 4 máy (trường `model` chứa một trong 4 mã);
- `is_vietnamese = true`, `is_spam = false`, có ít nhất 3 chữ;
- đăng trong cửa sổ `[0, 28)` ngày tính từ `launch_date` của máy của video.

**Chia tầng:**
- Theo máy của video × khía cạnh theo từ khóa (`src/models/aspect/keywords.py`).
- Bình luận khớp nhiều khía cạnh thì xếp vào khía cạnh **hiếm nhất** mà nó khớp.
- Thêm một tầng "không khớp từ khóa nào" cho mỗi máy, chiếm khoảng **20%** cỡ mẫu. Thiếu tầng này thì không đo được những khía cạnh mà từ khóa bỏ sót.

**Phân bổ 800 bình luận:**
- mỗi ô (máy × khía cạnh) ít nhất 20 bình luận nếu ô có đủ;
- tầng "không khớp" ~160;
- phần còn lại chia theo tỷ lệ cỡ ô;
- **mỗi video tối đa 15 bình luận** trong mẫu, để không dồn vào vài video lớn.

**Trọng số:** ghi xác suất được chọn của từng bình luận. Chỉ số mô hình báo cáo cả bản không trọng số (theo ô) và bản có trọng số (đại diện cho khung).

**Gán:** toàn bộ 800 bình luận gán đôi, rồi phân xử (mục 8). Sau phân xử, tập test **đóng băng**: ghi SHA-256. Sửa nhãn sau đó thì mọi mô hình phải chấm lại.

**Dữ liệu huấn luyện:** lấy từ **video train**, theo cùng cách chia tầng. Gán bằng LLM theo guideline v1, `label_source = "llm"`. Người kiểm ~200 bình luận LLM đã gán và báo cáo tỷ lệ đúng. Nhãn người của mẫu A thuộc video train được gộp vào.

## 5. Phiếu gán nhãn

Một phiếu là một bảng tính (Google Sheets hoặc CSV, mã hóa UTF-8). Mỗi bình luận một dòng, mỗi người gán một phiếu riêng. Người gán **không xem** phiếu của người kia cho tới khi cả hai xong.

| Cột | Ai điền | Nội dung |
|---|---|---|
| `mau`, `tang`, `trong_so` | Script lấy mẫu | `A`/`B`, tầng, nghịch đảo xác suất được chọn |
| `comment_id`, `video_id`, `may_video` | Script | `may_video` là trường `model` (máy của video) |
| `binh_luan` | Script | `text_clean`, mệnh đề đánh số `[0] … [1] …` |
| `binh_luan_cha` | Script | `parent_text` nếu là reply, cắt ở 600 ký tự |
| `nguoi_gan` | Người gán | Mã người gán (không dùng tên thật) |
| `tieng_viet` | Người gán | `co` / `khong` |
| `spam` | Người gán | `khong` / `quang_cao` / `lua_dao` / `khac` |
| `lien_quan` | Người gán | `truc_tiep` / `ngu_canh` / `khong` |
| `nhan` | Người gán | Các nhãn theo cách ghi ở [hướng dẫn gán chính thức mục 10](huong-dan-gan-nhan-chinh-thuc.md#10-phiếu-và-cách-làm) |
| `ghi_chu` | Người gán | Chỗ khó, đề xuất sửa guideline |

Phiếu **không** có `author_name`, `author_hash` hay bất cứ thông tin nào về người viết.

## 6. Quy trình

1. **Chuẩn bị:** guideline v1 được người viết guideline duyệt; viết xong script lấy mẫu và kiểm phiếu (mục 9).
2. **Hiệu chỉnh:** 50 bình luận (25 lấy từ mẫu A, 25 từ video train), **cả nhóm** cùng gán. Tính đồng thuận, họp về các chỗ lệch, sửa guideline, đổi `guideline_version` thành `v1.0`. Đồng thuận dưới ngưỡng (mục 7) thì làm thêm một vòng 50 bình luận khác.
3. **Mẫu A:** gán, kiểm phiếu, phân xử 200 bình luận gán đôi, tính các ước lượng ở mục 3.
4. **Mẫu B:** gán đôi 800 bình luận, kiểm phiếu, phân xử, đóng băng.
5. **Dữ liệu huấn luyện:** LLM gán theo `v1.0`; người kiểm 200 bình luận.
6. **Báo cáo** vào `docs/3-gan-nhan/bao-cao.md`: số bình luận mỗi người gán, mức đồng thuận, các ước lượng ở mục 3, các chỗ guideline đã sửa.

Mỗi người gán khoảng như nhau. Thời gian gán một bình luận đo ở vòng hiệu chỉnh, rồi dùng số đó chia việc.

## 7. Đo đồng thuận

Trên phần gán đôi, với từng loại nhãn, báo cáo **cả ba**: tỷ lệ đồng ý thô, Cohen's kappa, phân bố nhãn của từng người. Riêng nhãn hiếm như spam, kappa dao động mạnh, nên báo cáo thêm tỷ lệ đồng ý dương: số ca cả hai cùng gán, chia cho số ca có ít nhất một người gán.

| Loại nhãn | Đơn vị so | Chỉ số |
|---|---|---|
| `tieng_viet`, `spam`, `lien_quan` | bình luận | đồng ý thô, kappa |
| Có khía cạnh hay không | (bình luận, khía cạnh), bỏ qua máy | kappa từng khía cạnh và gộp; đồng ý dương |
| Cảm xúc | (bình luận, khía cạnh) mà cả hai cùng gán; giá trị `pos`/`neg`/`neu`/`ca hai` | kappa |
| Máy | bộ nhãn khớp nhau theo khía cạnh và cảm xúc | đồng ý thô |
| Đã dùng máy, loại lỗi, so sánh | bộ nhãn khớp | đồng ý thô (thường ít ca, chỉ báo cáo số) |

**Ngưỡng:** kappa ≥ 0,6 cho có khía cạnh và cảm xúc. Dưới ngưỡng thì dừng, sửa guideline, hiệu chỉnh lại, không gán tiếp. Kappa cao chỉ cho thấy hai người **nhất quán**, không chứng minh nhãn đúng: vẫn đọc các ví dụ lệch.

## 8. Phân xử và nhãn chuẩn

- Mọi bình luận gán đôi có chỗ lệch thì người thứ ba (không phải một trong hai người gán) đọc cả hai phiếu và quyết. Kết quả phân xử là **nhãn chuẩn**.
- Ghi lại từng chỗ lệch và cách quyết vào sổ phân xử. Lệch lặp lại từ 3 lần thì thêm ví dụ vào guideline.
- **Ghi ra bảng `gold_labels`** ([thiết kế dữ liệu mục 7](../0-chung/thiet-ke-du-lieu.md#7-gold_labels), giữ nguyên định dạng):
  - mỗi bộ nhãn một dòng: `clause_id = <comment_id>#<mệnh đề bằng chứng>`, `aspects = [{aspect, sentiment}]`, cùng `target_model`, `is_owner`, `defect_type`, `compare_with`, `compare_winner`;
  - `split` theo video;
  - `label_source = "human"`, `annotator` là người phân xử hoặc người gán.
- `target_model`:
  - `video` trên phiếu → ghi máy của video, cộng một cột phụ `may_tu_video = true`;
  - `?` → `null`.

  Cột phụ này cho Công việc 10 biết bao nhiêu nhận xét chỉ dựa vào máy của video (quyết định 2 của kế hoạch).
- Ba nhãn cấp bình luận (`tieng_viet`, `spam`, `lien_quan`) không có trong `gold_labels`. Ghi riêng ở `data/labels/nhan_binh_luan.jsonl`, mỗi bình luận một dòng.

## 9. File và script

| File | Nội dung | Có chưa |
|---|---|---|
| `data/labels/mau_a.jsonl`, `mau_b_test.jsonl`, `mau_b_train.jsonl` | Danh sách bình luận được chọn, tầng, trọng số, seed, SHA-256 nguồn | Chưa |
| `data/labels/phieu/<mau>_<nguoi_gan>.csv` | Phiếu đã gán | Chưa |
| `data/labels/so_phan_xu.csv` | Chỗ lệch và cách quyết | Chưa |
| `data/labels/gold_labels.jsonl`, `nhan_binh_luan.jsonl` | Nhãn chuẩn sau phân xử | Chưa |
| `data/labels/split.json` | Video train/test (CV7) | Chưa |
| Script lấy mẫu A, B và xuất phiếu | Đọc file tầng 2, `split.json`; ghi file mẫu và phiếu trống | Chưa viết |
| Script kiểm phiếu | Bắt lỗi cú pháp `nhan`, mã khía cạnh, mã máy, số mệnh đề không tồn tại, cột bỏ trống | Chưa viết |
| Script đồng thuận | Tính các chỉ số ở mục 7 | Chưa viết |
| Script ước lượng | Tính các ước lượng, khoảng tin cậy ở mục 3 | Chưa viết |

`data/` không vào git: chia sẻ phiếu và nhãn qua kho chung của nhóm, ghi SHA-256 vào báo cáo. Code các script đặt trong thư mục code mới `src/labeling/` (thêm vào quy tắc đặt tên khi tạo).

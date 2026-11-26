# Đặc tả tầng 3: gán nhãn

> Mục đích: Quy định gán nhãn người cho cả dự án: lấy hai mẫu nào, lấy thế nào, phiếu gán có gì, gán đôi, đo đồng thuận, phân xử, và tính tỷ lệ spam, không liên quan… kèm khoảng tin cậy từ nhãn người; cập nhật lần cuối: 2026-11-26.

**Trạng thái:** đặc tả nháp ngày 20/11. Từ 26/11 có code cho mẫu A và đợt hiệu chỉnh (mục 9); mẫu B chưa có code. Cách gán từng bình luận nằm ở [hướng dẫn gán chính thức](huong-dan-gan-nhan-chinh-thuc.md), file này không chép lại.

**Cập nhật 26/11:** bộ nhãn đã chốt ([đặc tả bộ nhãn mục 8](dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611)). Phần quy trình (hai mẫu, gán đôi, phân xử) vẫn dùng. Phiếu, nhãn mẫu A và đợt hiệu chỉnh đã sửa theo bộ nhãn chốt ngày 26/11 (bước 0.5 của [kế hoạch tổng thể](../0-chung/ke-hoach-tong-the.md)). Mẫu B (mục 4) còn viết theo bộ 4 máy và từ khóa cũ, chờ Công việc 7 chia video.

## 1. Vì sao cần nhãn người

Code đã chạy được cả chuỗi bằng luật mốc `rule-v1.1`, nhưng chưa biết đúng hay sai. Nhãn người là **mốc độc lập** để:
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
- Nhãn cần cho mẫu A: đủ các cột của phiếu (mục 5). **Spam thật** là bình luận có mục đích `quang_cao` (`qc`): bộ nhãn chốt gộp lừa đảo, cờ bạc vào đây.
- Code: `python -m src.labeling.sheet` lấy mẫu và chia việc cho 11 người (mã `n01`…`n11`, đổi bằng `--nguoi`), mỗi người khoảng như nhau. Ước lượng ở mục này: `python -m src.labeling.estimate`.

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

Một phiếu là một bảng tính, xuất sẵn hai dạng: CSV (UTF-8 có BOM) và Excel (`.xlsx`) có danh sách thả xuống cho `tieng_viet`, `lien_quan`, `da_dung`, `may_nhac` và gợi ý mã máy cho `ten_may` ([hướng dẫn gán chính thức mục 10](huong-dan-gan-nhan-chinh-thuc.md#10-phiếu-và-cách-làm)). Mỗi bình luận một dòng, mỗi người gán một phiếu riêng. Người gán **không xem** phiếu của người kia cho tới khi cả hai xong. Excel có thêm trang `danh_sach_nhan` (mọi nhãn, chữ viết tắt, ý nghĩa) và `danh_muc_may`; hai trang này cũng xuất thành `danh_sach_nhan.csv`, `danh_muc_may.csv`.

| Cột | Ai điền | Nội dung |
|---|---|---|
| `stt` | Script | Số thứ tự trong mẫu |
| `comment_id`, `video_id`, `may_video` | Script | `may_video` là trường `model` (máy của video) |
| `la_reply` | Script | `co` nếu là reply |
| `binh_luan` | Script | `text_clean`, đã che tên người được nhắc (`@[người dùng]`) |
| `binh_luan_cha` | Script | `parent_text` nếu là reply, cắt ở 600 ký tự, đã che tên |
| `nguoi_gan` | Người gán | Mã người gán (không dùng tên thật); phiếu riêng đã điền sẵn |
| `tieng_viet` | Người gán | `co` / `khong` (gán đầu tiên) |
| `lien_quan` | Người gán | Chiều 1: `D` `N` `B` `L` `X` |
| `noi_ve_thai_do` | Người gán | Chiều 2 và 4, vd `cam+-, gia0`; hai máy thì `@mã máy`; so sánh `pin=@s24u>ip15prm` |
| `muc_dich` | Người gán | Chiều 3, nhiều nhãn, vd `dg, hoi`; spam là `qc` |
| `da_dung`, `may_nhac`, `ten_may` | Người gán | Chiều 5, 6 và mã máy |
| `chua_chac`, `ghi_chu` | Người gán | Số chiều còn phân vân; chỗ khó, đề xuất sửa guideline |

Phiếu **không** có `author_name`, `author_hash` hay bất cứ thông tin nào về người viết. Phiếu cũng **không** có tầng, trọng số hay cờ của luật, để người gán không bị dẫn dắt; các cột đó chỉ nằm trong `data/labels/mau_a.jsonl`. Bỏ so với bản 20/11: cột `mau`, `tang`, `trong_so`, `spam`, `nhan`, số mệnh đề trong `binh_luan`.

## 6. Quy trình

1. **Chuẩn bị:** guideline v1 được người viết guideline duyệt; viết xong script lấy mẫu và kiểm phiếu (mục 9).
2. **Hiệu chỉnh:** 50 bình luận, **cả nhóm** cùng gán. Đặc tả gốc lấy 25 từ mẫu A, 25 từ video train; vì chưa có `split.json` (Công việc 7), bản 26/11 lấy cả 50 từ mẫu A (10 ở A1, 5 ở A2, 35 ở A3) và không đưa 50 bình luận này vào phiếu riêng (nhãn đợt hiệu chỉnh dùng luôn cho mẫu A). Tính đồng thuận, họp về các chỗ lệch, sửa guideline, đổi `guideline_version` thành `v1.0`. Đồng thuận dưới ngưỡng (mục 7) thì làm thêm một vòng 50 bình luận khác.
3. **Mẫu A:** gán, kiểm phiếu, phân xử 200 bình luận gán đôi, tính các ước lượng ở mục 3.
4. **Mẫu B:** gán đôi 800 bình luận, kiểm phiếu, phân xử, đóng băng.
5. **Dữ liệu huấn luyện:** LLM gán theo `v1.0`; người kiểm 200 bình luận.
6. **Báo cáo** vào `docs/3-gan-nhan/bao-cao.md`: số bình luận mỗi người gán, mức đồng thuận, các ước lượng ở mục 3, các chỗ guideline đã sửa.

Mỗi người gán khoảng như nhau. Thời gian gán một bình luận đo ở vòng hiệu chỉnh, rồi dùng số đó chia việc.

## 7. Đo đồng thuận

Trên phần gán đôi, với từng loại nhãn, báo cáo **cả ba**: tỷ lệ đồng ý thô, Cohen's kappa, phân bố nhãn của từng người. Riêng nhãn hiếm như spam, kappa dao động mạnh, nên báo cáo thêm tỷ lệ đồng ý dương: số ca cả hai cùng gán, chia cho số ca có ít nhất một người gán.

| Loại nhãn | Đơn vị so | Chỉ số |
|---|---|---|
| `tieng_viet`, spam (`muc_dich` có `quang_cao`), `lien_quan`, `da_dung`, `may_nhac` | bình luận | đồng ý thô, kappa; spam thêm đồng ý dương |
| Có nhãn chiều 2 hay không | (bình luận, nhãn chiều 2), bỏ qua máy | kappa từng nhãn; đồng ý dương |
| Thái độ | (bình luận, nhãn chiều 2) mà cả hai cùng gán; giá trị `tich_cuc`/`tieu_cuc`/`so_sanh`/`khong_danh_gia` (có thể nhiều) | kappa |
| Máy | bộ nhãn khớp nhau theo khía cạnh và cảm xúc | đồng ý thô |
| So sánh (bên hơn) | bộ nhãn khớp | đồng ý thô (thường ít ca, chỉ báo cáo số) |

**Ngưỡng:** kappa ≥ 0,6 cho có nhãn chiều 2 và thái độ. Dưới ngưỡng thì dừng, sửa guideline, hiệu chỉnh lại, không gán tiếp. Kappa cao chỉ cho thấy hai người **nhất quán**, không chứng minh nhãn đúng: vẫn đọc các ví dụ lệch.

## 8. Phân xử và nhãn chuẩn

- `python -m src.labeling.check_sheet gop` gộp mọi phiếu: hai người khớp nhau thì thành nhãn chuẩn; lệch thì ghi vào `data/labels/so_phan_xu.csv`.
- Mọi bình luận gán đôi có chỗ lệch thì người thứ ba (không phải một trong hai người gán) đọc cả hai phiếu và quyết, điền các cột `px_*` trong sổ phân xử rồi chạy lại `gop`. Kết quả phân xử là **nhãn chuẩn**.
- Ghi lại từng chỗ lệch và cách quyết vào sổ phân xử. Lệch lặp lại từ 3 lần thì thêm ví dụ vào guideline.
- **Ghi ra bảng `gold_labels`** ([thiết kế dữ liệu mục 7](../0-chung/thiet-ke-du-lieu.md#7-gold_labels), giữ nguyên định dạng):
  - mỗi bộ nhãn một dòng: `clause_id = <comment_id>#<mệnh đề bằng chứng>`, `aspects = [{aspect, sentiment}]` theo mã của contract v3, cùng `target_model`, `is_owner`, `model_mention`, `compare_with`, `compare_winner` (từ cách ghi `@a>b`, `@a~b`);
  - `split` theo video;
  - `label_source = "human"`, `annotator` là người phân xử hoặc người gán.
- `target_model`: theo `ten_may` và `@mã máy` trên phiếu. Bình luận không gọi tên máy nào thì để `null`; người gán không đoán theo video (hướng dẫn gán mục 9). Lúc phân tích, nhóm quyết có coi là máy của video hay không (quyết định 2 của kế hoạch).
- Nhãn cấp bình luận (`tieng_viet`, `lien_quan`, `muc_dich`, `da_dung`, `may_nhac`, `ten_may`) không có trong `gold_labels`. Ghi riêng ở `data/labels/nhan_binh_luan.jsonl`, mỗi bình luận một dòng (cả `noi_ve` để dựng `gold_labels`).

## 9. File và script

| File | Nội dung | Có chưa |
|---|---|---|
| `data/labels/mau_a.jsonl`, `mau_a.manifest.json` | Bình luận mẫu A được chọn, tầng, `N_h`, `n_h`, trọng số, ai gán, cờ của luật; seed, SHA-256 nguồn | Có code (`sheet.py`), chờ chạy trên v4 |
| `data/labels/mau_b_test.jsonl`, `mau_b_train.jsonl` | Mẫu B | Chưa (chờ `split.json`) |
| `data/labels/phieu/hieu_chinh_50.csv\|.xlsx`, `mau_a_<nguoi_gan>.csv\|.xlsx`, `danh_sach_nhan.csv`, `danh_muc_may.csv` | Phiếu trống, danh sách nhãn, danh mục máy | Có code (`sheet.py`) |
| `data/labels/so_phan_xu.csv` | Chỗ lệch, cột `px_*` cho người phân xử | Có code (`check_sheet.py gop`) |
| `data/labels/nhan_binh_luan.jsonl`, `dong_thuan.json` | Nhãn chuẩn sau phân xử; đồng thuận mục 7 | Có code (`check_sheet.py gop`) |
| `data/labels/gold_labels.jsonl` | Bảng `gold_labels` | Chưa |
| `data/labels/uoc_luong_mau_a.json` | Các ước lượng mục 3, precision và recall của luật | Có code (`estimate.py`) |
| `data/labels/split.json` | Video train/test (CV7) | Chưa |
| `src/labeling/sheet.py` | Lấy mẫu A, đợt hiệu chỉnh, xuất phiếu; không ghi đè phiếu đã có người điền | Đã viết 26/11 |
| `src/labeling/check_sheet.py` | `kiem`: bắt lỗi cú pháp, mã nhãn, `@mã máy`, luật tự kiểm của hướng dẫn gán mục 10. `gop`: gộp, sổ phân xử, đồng thuận | Đã viết 26/11 |
| `src/labeling/estimate.py`, `weighted_metrics.py` | Ước lượng mục 3 (công thức phân tầng; bootstrap phân tầng theo video khi tầng có tỷ lệ 0, 1 hay dưới 5 ca), đo luật | Đã viết 26/11 |
| Script lấy mẫu B | Đọc file tầng 2, `split.json` | Chưa viết |

`data/` không vào git: chia sẻ phiếu và nhãn qua kho chung của nhóm, ghi SHA-256 vào báo cáo. Code các script ở `src/labeling/`; test ở `tests/test_labeling_sheet.py`.

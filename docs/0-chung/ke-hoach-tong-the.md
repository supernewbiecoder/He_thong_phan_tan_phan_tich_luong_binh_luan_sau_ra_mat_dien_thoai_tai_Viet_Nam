# Kế hoạch tổng thể: từ bộ nhãn tới báo cáo cuối

> Mục đích: Kế hoạch đề xuất cho cả dự án sau khi nhánh `kham-pha-nhan` xong: 7 giai đoạn từ bàn giao bộ nhãn tới báo cáo cuối, mỗi giai đoạn làm trên nhánh nào, làm gì, ai làm, đầu ra, khi nào xong, phụ thuộc, rủi ro, và các quyết định trưởng nhóm phải chốt trước; cập nhật lần cuối: 2026-11-26.

**Trạng thái: đề xuất, trưởng nhóm chưa duyệt.** Claude soạn từ kế hoạch trên `main` (20/11) và kết quả nhánh khám phá nhãn (26/11). Cột hạn để trống vì chưa biết hạn nộp đồ án. Đã chép về `main` ngày 26/11; duyệt xong thì thay mục 2 (lộ trình) của [kế hoạch](ke-hoach.md).

**Cập nhật 26/11 (refactor trên nhánh `nlquan`, Nguyễn Lê Quân, theo giao việc của trưởng nhóm):** đã làm 0.4, 0.5 (phần phiếu và mẫu A), 0.6; một phần 1.4 (DB v3), 2.1 (script mẫu A, phiếu, kiểm, gộp), 5.2, 5.3. Ghi chi tiết ở các bảng dưới và ở [kế hoạch](ke-hoach.md) mục 1.

## 1. Đang đứng ở đâu (26/11)

| Phần | Đã có | Còn thiếu |
|---|---|---|
| Dữ liệu | v4: 473.786 bình luận, 127 máy, 44 kênh, có SHA-256 | |
| Tiền xử lý (tầng 2) | Code đủ bước trên `main` | **Chưa chạy trên v4**, chưa có file chung cho cả nhóm |
| Bộ nhãn | **Chốt 26/11**: 6 chiều, 41 nhãn, 11 khía cạnh; [hướng dẫn gán chính thức](../3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md) đã duyệt. Đã về `main`; dạng code ở `src/labeling/final_labels.py`; contract v3 và thiết kế dữ liệu theo bộ này (26/11) | Chưa gán chính thức |
| Nhãn người | 600 bình luận ngẫu nhiên đã gán và kiểm (dùng để tính phân bố); lô K, lô D2 gán mù | **Chưa có tập test** để chấm mô hình |
| Mô hình | Luật mốc `rule-v1`; mô hình khía cạnh (CV8) và cảm xúc (CV9) | Chưa mô hình nào được chấm trên nhãn người của bình luận YouTube |
| Phân tích Q1–Q5 | Code CV12: aggregates, bootstrap theo video, Holm | Viết cho bộ 4 máy, mà 26/11 đã quyết **không chọn bộ 4 máy** |
| DB, dashboard, streaming | MongoDB theo contract v3, nạp bằng bước `nap_db` (26/11); API + dashboard 4 tab đọc DB, số liệu minh họa (26/11); Kafka 1 node để dev | Spark, cụm Kafka chưa dựng |
| Git | | `main` và `kham-pha-nhan` **chưa push**; nhánh khám phá **chưa commit** |

**Nhánh khám phá đổi những gì cho các bước sau** (số từ [báo cáo phân bố](../3-gan-nhan/bao-cao-phan-bo-nhan.md), mẫu 600 bình luận ngẫu nhiên của v4, khoảng tin cậy 95% bootstrap theo video):

1. **Bộ nhãn khác bộ đặt sẵn.** Tách `do_ben` khỏi thiết kế, thêm `mua_ban`, thêm `may_chung`, `hang_nguoi_dung`, chiều mục đích, thái độ `so_sanh`, trường `ten_may`, cờ `tieng_viet`. Contract, DB, luật mốc và code phân tích đều phải theo.
2. **Phải lọc trước khi chấm cảm xúc.** Chỉ 65,8% [61,5; 69,9] bình luận nói về điện thoại. Phần còn lại nói về video, người review, hoặc cãi nhau.
3. **Gán máy là chỗ rủi ro nhất.** 57,0% [52,7; 61,4] bình luận không gọi tên máy nào. Gán nhầm máy thì lời chê iPhone sẽ bị tính cho Samsung.
4. **Khía cạnh hiếm cần mẫu riêng.** Trong 395 bình luận về điện thoại, không khía cạnh nào có đủ 30 lượt khen và chê cộng lại. `bao_hanh_sua_chua` chỉ chiếm 1,3%, cả mẫu chỉ có 8 bình luận báo lỗi.

## 2. Đích cuối

1. **Mô hình gắn nhãn** cho từng bình luận theo bộ nhãn chốt, chấm trên tập test do người gán, so với luật mốc.
2. **Trả lời Q1–Q6.** Mỗi kết luận kèm khoảng tin cậy, phép kiểm sai số mô hình và phép kiểm độ nhạy.
3. **Hệ thống chạy lại được:** chuỗi theo lô từ dữ liệu thô tới Q1–Q6, có DB và dashboard. Streaming làm nếu môn học yêu cầu (quyết định 2).
4. **Báo cáo và slide.** Số nào cũng chạy lại được từ code và phiên bản dữ liệu ghi rõ.

## 3. Lộ trình

Mỗi giai đoạn làm trên một hay vài nhánh tách từ `main`, xong thì mở PR vào `main`. Giai đoạn sau chỉ bắt đầu khi điều kiện "xong khi" của giai đoạn trước đã đạt, trừ các việc ghi là làm song song được.

```text
GĐ0 Bàn giao bộ nhãn về main        (trưởng nhóm)
 ├─ GĐ1 Dữ liệu nền                  (nhóm A)     ─┐
 └─ GĐ2 Gán nhãn chính thức          (cả nhóm)    ─┤ chạy song song một phần
        └─ GĐ3 Mô hình               (nhóm B, C)   │
               └─ GĐ4 Suy luận + Q1–Q6 (nhóm C)    │
GĐ5 Hệ thống, dashboard              (nhóm A, C)  ─┘ dựng song song, cắm mô hình thật ở cuối
GĐ6 Báo cáo                          (mọi người)
```

**Đường găng** (chậm một việc là chậm cả dự án): GĐ0 → chia video train/test (1.2) → tập test (2.4) → chấm mô hình (3.1–3.3) → Q1–Q6 (4.2) → báo cáo (6.2).

### GĐ0. Bàn giao bộ nhãn về `main`

**Nhánh:** `ban-giao-nhan`, tách từ `main`. **Ai:** trưởng nhóm. **Hạn:** ___

| # | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| 0.1 | Commit nhánh `kham-pha-nhan`; push `main` và `kham-pha-nhan` | Hai nhánh trên GitHub | Cả nhóm clone được |
| 0.2 | Chép về `main` bằng cách chép file (không merge): đặc tả bộ nhãn, hướng dẫn gán chính thức, các báo cáo, `src/labeling/` và test | Thư mục `docs/3-gan-nhan/`, `src/labeling/` trên `main` | Test của `main` và của `src/labeling/` đều qua |
| 0.3 | Sửa `muc-tieu.md`: bỏ bộ 4 máy, viết lại Q1–Q6 theo mục 5 dưới đây | `muc-tieu.md` mới | Trưởng nhóm duyệt |
| 0.4 | Contract `aspect-mention` lên v3 và sửa thiết kế dữ liệu theo bộ nhãn chốt: 11 mã khía cạnh, `may_chung`, `hang_nguoi_dung`, thái độ `so_sanh` kèm bên hơn, `ten_may`, `tieng_viet`; có giữ mục đích hay không thì theo quyết định 5 | Contract v3, `thiet-ke-du-lieu.md` | Tăng `schema_version`, báo cả nhóm. **Xong 26/11:** v3 giữ mục đích (`purposes`), thêm `model_mention`, `target_model_source`; `defect_type` luôn `null`; `ten_may` ghi qua `target_model`/`compare_with`, `tieng_viet` qua cờ `is_vietnamese` của bình luận |
| 0.5 | Sửa đặc tả gán nhãn trên `main` theo bộ nhãn chốt; thay guideline v1 bằng hướng dẫn gán chính thức | `docs/3-gan-nhan/dac-ta.md` mới | Không còn hai bộ nhãn song song. **Xong phần phiếu và mẫu A 26/11** (mục 5, 9 của đặc tả gán nhãn); phần mẫu B còn theo bộ 4 máy |
| 0.6 | Sửa từ khóa của luật mốc `rule-v1` theo 11 khía cạnh (lấy từ ánh xạ trong `label_set.py`) | `rule-v1.1` | Luật mốc và bộ nhãn dùng cùng mã. **Xong 26/11** ([đặc tả suy luận](../4-mo-hinh/dac-ta-suy-luan.md)) |

**Vì sao làm trước:** mọi việc sau (gán nhãn, mô hình, DB, phân tích) đều đọc bộ nhãn. Làm khi `main` còn hai bộ nhãn thì mỗi nhóm theo một bộ.

### GĐ1. Dữ liệu nền

**Nhánh:** `du-lieu-v4`. **Ai:** nhóm A (3 người). **Hạn:** ___. Làm song song với 2.1–2.3.

| # | Việc | CV | Đầu ra | Xong khi |
|---|---|---|---|---|
| 1.1 | Chạy tầng 2 trên v4, phát hành file chung kèm SHA-256 | 6 | `data/processed/comments.jsonl`, manifest | Bảng phiên bản tầng 2 có dòng v4; cả nhóm dùng chung một file |
| 1.2 | Chia video train/test theo `video_id`, seed cố định, phân tầng theo nhóm kênh. **Phải xong trước khi lấy tập test** | 7 | `data/labels/split.json` | Khoảng 20–25% video vào test; không video nào ở cả hai bên |
| 1.3 | Danh mục máy: ghi nguồn cho `launch_date`, thêm đời trước (`predecessor`), kiểm nhóm đối thủ (`rival_of`) | 2 | `config/pipeline.yaml` đã sửa | Q3, Q4 tra được đối thủ và đời trước của mọi máy |
| 1.4 | DB theo contract v3 | 3 | `init_db.py`, script nạp | Nạp được, chạy lại không sinh bản trùng |

### GĐ2. Gán nhãn chính thức

**Nhánh:** `gan-nhan-chinh-thuc`. **Ai:** cả nhóm gán; trưởng nhóm điều phối và phân xử. **Hạn:** ___

| # | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| 2.1 | Script lấy mẫu, xuất phiếu, kiểm luật nhãn trên phiếu, so hai người, phân xử. Dùng lại `src/labeling/` (`sample.py`, `lot_k.py`, `stats.py`) | Script và test | Chạy được trên dữ liệu giả |
| 2.2 | **Hiệu chỉnh:** cả nhóm gán cùng 50 bình luận theo hướng dẫn chính thức, tính kappa từng cặp người, họp bàn các ca lệch, sửa hướng dẫn | Hướng dẫn bản 1.0 | Mọi chiều κ ≥ 0,6 (chiều nhiều nhãn xét bằng kappa gộp) |
| 2.3 | **Mẫu chất lượng dữ liệu:** dùng lại 600 bình luận của nhánh khám phá để có tỷ lệ (đã có), chỉ gán thêm `tieng_viet`. Lấy thêm một tầng theo cờ của luật để đo precision, recall của luật spam và luật tiếng Việt | Tỷ lệ spam, không liên quan, ngoại ngữ; điểm của hai luật | Có tỷ lệ kèm khoảng tin cậy |
| 2.4 | **Tập test:** chỉ lấy từ video test (1.2), dồn vào bình luận về điện thoại, phân tầng theo khía cạnh bằng từ khóa và ghi trọng số. Mỗi bình luận hai người gán độc lập, phân xử, rồi đóng băng | `gold_labels` kèm SHA-256 | κ ≥ 0,6; mọi ca lệch đã phân xử |
| 2.5 | **Nhãn để huấn luyện:** LLM gán theo hướng dẫn chính thức trên video train; người kiểm 200 bình luận | Nhãn train; tỷ lệ LLM gán đúng, kèm khoảng Wilson | Nhãn LLM không bao giờ vào tập test |
| 2.6 | **Loại lỗi cho Q5:** lấy mẫu riêng các bình luận báo lỗi bằng từ khóa, mã hóa mở như B4–B5, chốt bộ loại lỗi, rồi gán | Bộ loại lỗi, nhãn | Như B4–B8 của nhánh khám phá |

**Vì sao tập test phải phân tầng.** Lấy ngẫu nhiên thì muốn có khoảng 30 bình luận của một khía cạnh chiếm tỷ lệ `p` trong số bình luận về điện thoại, phải lấy:

```text
n ≈ 30 / p
pin_sac            (p ≈ 5,8%)  →  khoảng 520 bình luận về điện thoại
bao_hanh_sua_chua  (p ≈ 1,3%)  →  khoảng 2.300 bình luận về điện thoại
```

Lấy ngẫu nhiên 800 bình luận thì không đủ khía cạnh hiếm. Lấy theo từ khóa cho từng khía cạnh, rồi dùng trọng số (nghịch đảo xác suất được chọn) khi tính điểm đại diện, như đặc tả gán nhãn trên `main` mục 4 đã viết.

### GĐ3. Mô hình

**Nhánh:** `mo-hinh-<bài toán>`, mỗi bài toán một nhánh. **Ai:** nhóm B (6 người, chia B1–B3); khung đánh giá do nhóm C. **Hạn:** ___

| # | Việc | Ai | Đầu ra | Xong khi |
|---|---|---|---|---|
| 3.1 | `evaluate.py` dùng chung; chấm `rule-v1.1` trước để làm mốc | C | Bảng điểm luật mốc | Chấm trên tập test đã đóng băng; F1 kèm khoảng tin cậy bootstrap theo video; ma trận nhầm lẫn theo máy × khía cạnh |
| 3.2 | **Lọc:** chiều 1 (`dien_thoai` hay không), cờ tiếng Việt, spam | B3 | Mô hình hay luật đã đo | Precision, recall trên tập test |
| 3.3 | **Khía cạnh:** chiều 2, đa nhãn, 13 nhãn | B1 | Mô hình, bảng so với luật mốc | Theo luật chọn mô hình (dưới bảng) |
| 3.4 | **Thái độ (cảm xúc)** theo cặp (bình luận, nhãn chiều 2). Ưu tiên cao nhất theo quyết định 26/11 | B2 | Như trên | Như trên; có phân tích lỗi trên phủ định, mỉa mai, so sánh |
| 3.5 | **Máy được nhắc:** chiều 6, `ten_may`, nối nhận xét với máy (`@`), bên hơn trong câu so sánh | B3 | Luật đã đo | Precision, recall; tỷ lệ bình luận không xác định được máy |
| 3.6 | Đã dùng máy (chiều 5), mục đích (chiều 3) | B1, B2 | Mô hình hay luật | Làm sau 3.2–3.5 |

**Thang mô hình:** luật mốc → TF-IDF + Logistic Regression hay SVM → PhoBERT. Làm theo thứ tự nào thì theo quyết định 4.

**Luật chọn mô hình** (quy ước trên `main`): chọn mô hình **đơn giản nhất** mà kết luận Q1–Q5 không khác kết luận của mô hình tốt nhất.

### GĐ4. Suy luận toàn bộ và trả lời Q1–Q6

**Nhánh:** `phan-tich`. **Ai:** nhóm C (2 người). **Hạn:** ___

| # | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| 4.1 | Thay luật mốc bằng các mô hình đã chọn; suy luận trên toàn bộ v4 | `aspect_mentions` theo contract v3, ghi `model_version` | Chạy lại ra cùng kết quả |
| 4.2 | Q1–Q5 theo mục 5 dưới đây, sửa code CV12 cho hết phụ thuộc bộ 4 máy | `business_questions.json` | Mỗi kết luận có khoảng tin cậy bootstrap theo video và hiệu chỉnh Holm |
| 4.3 | Kiểm sai số mô hình bằng ma trận nhầm lẫn của 3.1; kiểm độ nhạy (bỏ video tặng quà, bỏ kênh lớn nhất, chỉ bình luận gốc, mỗi tác giả một phiếu, bỏ bình luận có cờ Q6) | Bảng: kết luận × phép kiểm | Kết luận nào đổi chiều thì ghi rõ |
| 4.4 | Q6 (nếu nhóm chốt): gắn cờ dấu hiệu phối hợp, duyệt tay các ca bị gắn cờ | Tỷ lệ nghi vấn, độ chính xác luật gắn cờ | Chỉ dùng chữ "dấu hiệu" |

### GĐ5. Hệ thống và hiển thị

**Nhánh:** `he-thong`. **Ai:** nhóm A và C. **Hạn:** ___. Dựng song song từ GĐ1 bằng số liệu minh họa; cắm mô hình thật khi GĐ4 xong.

| # | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| 5.1 | Chuỗi theo lô hằng ngày (`python -m src.run`) với mô hình thật | Lịch chạy, log, manifest | Chạy hết chuỗi trên v4 |
| 5.2 | Nạp DB | Các collection theo contract v3 | Chạy lại không sinh bản trùng |
| 5.3 | Dashboard đọc kết quả GĐ4 | Dashboard | Chỗ nào còn số minh họa thì ghi rõ |
| 5.4 | Streaming bằng Kafka và Spark, nếu môn yêu cầu: phát lại dữ liệu, ghi đè theo khóa (không sinh bản trùng), cảnh báo theo cửa sổ thời gian | Cụm chạy được, số đo độ trễ và độ trễ hàng đợi Kafka | Theo [luồng xử lý mục 3](luong-xu-ly.md#3-giai-đoạn-2-streaming-để-sau) |

### GĐ6. Báo cáo

**Nhánh:** `bao-cao`. **Ai:** mọi người viết phần của mình; trưởng nhóm ghép. **Hạn:** ___

| # | Việc | Xong khi |
|---|---|---|
| 6.1 | Kiểm tái lập: một người không làm phần đó chạy lại từ dữ liệu v4 và SHA-256, ra đúng số trong báo cáo | Mọi số khớp |
| 6.2 | Báo cáo tổng và slide | Mỗi kết luận kèm khoảng tin cậy, phép kiểm sai số mô hình, phép kiểm độ nhạy |
| 6.3 | Báo cáo quá trình cho các giai đoạn sau, theo mẫu [báo cáo quá trình khám phá nhãn](bao-cao-qua-trinh.md) | Mỗi giai đoạn một mục |

## 4. Phân công đề xuất

Theo cách chia nhóm trên `main` (11 người):

| Nhóm | Số người | GĐ chính |
|---|---|---|
| Trưởng nhóm | 1 | GĐ0; điều phối GĐ2; review mọi PR |
| A. Dữ liệu và DB | 3 | GĐ1, GĐ5 (DB, chuỗi theo lô, streaming) |
| B. Mô hình | 6 | B1: khía cạnh, đã dùng máy · B2: thái độ, mục đích · B3: lọc, máy được nhắc |
| C. Tích hợp và đánh giá | 2 | 3.1 (khung đánh giá), GĐ4, dashboard |
| Cả nhóm | 11 | GĐ2: hiệu chỉnh và gán tập test |

## 5. Q1–Q6 khi không có bộ 4 máy (đề xuất)

Ngày 26/11 trưởng nhóm quyết không chọn bộ 4 máy, dòng máy nào có trong dữ liệu thì phân tích hết. Đề xuất cách đặt lại câu hỏi:

| Câu | Cách đo mới |
|---|---|
| Q1 | Với **mỗi máy đủ dữ liệu**: tỷ lệ khen trừ tỷ lệ chê (Net) theo tuần 1–4, gộp mọi khía cạnh |
| Q2 | Với mỗi máy: % khen, % chê theo 11 khía cạnh |
| Q3 | Với mỗi máy: so với các máy trong `rival_of` của nó theo từng khía cạnh; câu so sánh trực tiếp dùng thái độ `so_sanh` kèm bên hơn |
| Q4 | Với mỗi máy có đời trước (`predecessor`, 1.3): % chê từng khía cạnh, đời trước → đời này |
| Q5 | Loại lỗi (2.6) do người đã dùng máy báo (chiều 5 `co`, mục đích `bao_loi`) |
| Q6 | Như cũ: dấu hiệu phối hợp, và kết quả Q1–Q5 lệch bao nhiêu khi bỏ chúng |

**"Đủ dữ liệu"** giữ quy ước trên `main`: ô nào có khen + chê dưới 30 thì ghi "ít dữ liệu", không kết luận. Ở EDA, 81 trên 127 máy có dưới 3.000 lượt bình luận, nên nhiều máy sẽ chỉ trả lời được Q1, chưa đủ cho Q2–Q4 theo từng khía cạnh. Báo cáo nên chọn vài máy nhiều dữ liệu nhất để trình bày sâu.

## 6. Quyết định trưởng nhóm cần chốt trước khi bắt đầu

| # | Quyết định | Ảnh hưởng tới |
|---|---|---|
| 1 | Hạn nộp đồ án, và hạn của từng giai đoạn | Mọi cột hạn |
| 2 | Môn học có bắt buộc phần hệ thống phân tán (Kafka, Spark streaming) không | Làm hay bỏ 5.4; nhóm A cần bao nhiêu người |
| 3 | Dùng LLM nào để gán phần huấn luyện, và có được gửi chữ bình luận ra dịch vụ ngoài không (hiện chỉ cho Claude trong phiên của trưởng nhóm) | 2.5 |
| 4 | Thử PhoBERT trước, hay đi từ mô hình đơn giản lên | Thứ tự trong GĐ3 |
| 5 | Contract v3 có giữ chiều mục đích không (giúp lọc bình luận có ý kiến, nhưng thêm việc gán). **Đã chốt 26/11: giữ** | 0.4, 2.4, 3.6 |
| 6 | Cách đặt lại Q1–Q6 ở mục 5 | 0.3, GĐ4 |
| 7 | Dùng lại 600 bình luận của nhánh khám phá làm mẫu chất lượng dữ liệu (2.3) | Bớt khoảng 850 bình luận phải gán |
| 8 | Ai nhận việc nào (điền tên vào mục 4) | Mọi giai đoạn |

Còn mở từ kế hoạch trên `main`: cửa sổ 7 ngày trước ra mắt (crawler hiện không lấy), `author_name` trong dữ liệu chia sẻ, crawl bằng hai khóa API ở hai project.

## 7. Rủi ro

| Rủi ro | Dấu hiệu | Cách giảm |
|---|---|---|
| Gán nhầm máy làm lệch Q2–Q4 | 57% bình luận không gọi tên máy | Đo riêng 3.5; bình luận không xác định được máy thì để trống, không đoán theo video |
| Tập test không đủ khía cạnh hiếm | `bao_hanh_sua_chua` 1,3% | Phân tầng theo từ khóa, có trọng số (2.4) |
| Nhãn LLM sai có quy luật | Ở B7, trưởng nhóm phải sửa nhãn của Claude ở 17,0% [10,9; 25,5] số bình luận | Kiểm 200 (2.5); không dùng nhãn LLM để chấm điểm |
| Gán nhãn tốn công hơn dự tính | Mỗi bình luận gán đôi | Hiệu chỉnh trước (2.2); chia đều cho 11 người |
| Q5 thiếu dữ liệu | 8/600 bình luận báo lỗi | Mẫu riêng các bình luận báo lỗi (2.6) |
| Streaming chưa dựng gì | Chỉ có Kafka 1 node | Chốt quyết định 2 sớm; dựng song song từ GĐ1 |
| Hai nhánh chưa push | Chỉ có trên máy trưởng nhóm | Làm 0.1 ngay |

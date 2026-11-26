# Đặc tả phát hiện spam: đo luật gắn cờ và so với mô hình ML (Công việc 11)

> Mục đích: Quy định cách đo luật gắn cờ spam và tiếng Việt của tầng 2 bằng nhãn người mẫu A, cách so luật với một mô hình ML, và luật chọn phương án; cập nhật lần cuối: 2026-11-26.

**Người làm:** Nguyễn Lê Quân. **Trạng thái:** code xong và có test trên dữ liệu tự soạn; **chờ nhãn người mẫu A** nên chưa có số đo. Chưa có số thì mọi ô kết quả để `___`.

## 1. Bài toán

- Luật cần đo: `src/processing/flags.py` (bước 2.4, [đặc tả gắn cờ](../2-tien-xu-ly/dac-ta-gan-co.md)), cho hai cờ độc lập `is_spam` và `is_vietnamese`.
- **Nhãn spam thật** là nhãn người: bình luận có mục đích `quang_cao` (bộ nhãn chốt gộp quảng cáo, mời liên hệ, lừa đảo, cờ bạc vào đây, [đặc tả bộ nhãn mục 8](../3-gan-nhan/dac-ta-bo-nhan.md)). Minigame (`minigame`) không phải spam.
- **Nhãn "không phải tiếng Việt" thật** là cột `tieng_viet = khong` trên phiếu. Không gộp vào spam.
- Spam hiếm, nên báo precision, recall, F1 của lớp spam, **không dùng accuracy**.

## 2. Dữ liệu nhãn

Mẫu A theo [đặc tả gán nhãn mục 3](../3-gan-nhan/dac-ta.md): lấy từ toàn bộ file tầng 2, chia tầng theo chính cờ của luật (A1 luật nói spam, A2 luật nói ngoại ngữ, A3 còn lại), ghi trọng số `N_h / n_h`. Lấy mẫu và xuất phiếu bằng `python -m src.labeling.sheet`; gộp phiếu, phân xử bằng `python -m src.labeling.check_sheet gop`.

Nhãn LLM không dùng ở đây. 640 nhãn LLM của bản 17/11 (dữ liệu `clean_data.jsonl` v1.0) đã gỡ khỏi `main`; xem lại ở commit `f26bd6b` nếu cần.

## 3. Đo luật (`python -m src.labeling.estimate`)

- Tỷ lệ spam, không phải tiếng Việt, từng nhãn chiều 1, có nhãn chiều 2, cho cả dữ liệu, kèm khoảng tin cậy 95%. Cách tính: [đặc tả gán nhãn mục 3](../3-gan-nhan/dac-ta.md) (công thức phân tầng; tầng có tỷ lệ 0, 1 hay dưới 5 ca thì bootstrap phân tầng theo video, 2.000 lần).
- Precision, recall, F1 của luật spam và luật tiếng Việt, trên mẫu và quy về cả dữ liệu bằng trọng số tầng; khoảng tin cậy bootstrap phân tầng theo video.
- **Cận dưới của recall:** tầng không thấy spam nào vẫn có thể có spam. Coi mỗi tầng như vậy có spam ở mức cận trên 95% (quy tắc `1 − 0,05^(1/n)`) rồi tính lại recall (`recall_can_duoi`). Báo cáo cả hai số.
- Thư viện tính: `src/labeling/weighted_metrics.py`.

## 4. So với mô hình ML (`python -m src.models.spam.train`)

Theo đề bài: mô hình ML chỉ là phương án so sánh, và chỉ thay luật khi luật kém rõ rệt.

1. **Chia train/test theo `video_id`.** Dùng `data/labels/split.json` của Công việc 7 (trường `test_video_ids`). Chưa có file đó thì tạm chia bằng băm `video_id`, 25% video vào test; kết quả ghi rõ cách chia đã dùng.
2. **Đủ nhãn mới huấn luyện:** cần ít nhất 20 bình luận spam (nhãn người) trong video train; thiếu thì lệnh dừng và chỉ báo cáo luật.
3. **Chọn mô hình trên train:** cross-validation gom nhóm theo video (tối đa 5 phần), 5 ứng viên (`src/models/spam/model.py`: Naive Bayes và Logistic Regression trên TF-IDF từ; LR trên TF-IDF ký tự; LR và SVM trên từ + ký tự + đặc trưng hình thức). Chọn theo average precision có trọng số tầng; ngưỡng theo F0,5 có trọng số (ưu tiên precision).
4. **Chấm một lần trên test:** luật, ML, và kết hợp (luật gắn cờ VÀ ML xác nhận). Báo precision, recall, F1 quy về cả dữ liệu, khoảng tin cậy, và kiểm định McNemar chính xác giữa luật và ML.
5. Đầu ra `data/labels/spam_ml_eval.json`; mô hình `artifacts/spam/spam-ml.joblib` (không vào git).

## 5. Luật chọn phương án

- Giữ luật nếu khoảng tin cậy precision và recall của ML (hay kết hợp) chồng lên khoảng của luật: chưa đủ bằng chứng ML tốt hơn.
- Chỉ chọn ML hay kết hợp khi tốt hơn luật có ý nghĩa (McNemar p < 0,05, và F1 quy về cả dữ liệu cao hơn) **và** không làm giảm precision quá 5 điểm phần trăm.
- Ghi quyết định và số đo vào [kế hoạch mục 4](../0-chung/ke-hoach.md). Đổi luật thì sửa `flags.py`, đặc tả gắn cờ và test, tăng `PIPELINE_VERSION`.

## 6. Kết quả

| Đại lượng | Ước lượng | KTC 95% |
|---|---|---|
| Tỷ lệ spam (cả dữ liệu) | ___ | ___ |
| Tỷ lệ không phải tiếng Việt | ___ | ___ |
| Precision luật spam | ___ | ___ |
| Recall luật spam (cận dưới) | ___ (___) | ___ |
| Precision, recall luật tiếng Việt | ___ | ___ |
| ML so với luật | ___ | ___ |

Chờ chạy: cần nhãn người mẫu A.

# Báo cáo Công việc STT 8: Xây dựng Mô hình Phân loại Khía cạnh (Aspect Classification)

**Người thực hiện:** Nguyễn Xuân Hồng Quân (Nhánh: `xhquan/cong-viec-8`)  
**Đầu vào:**
- Tập dữ liệu miền nguồn đã quy đổi: `data/uit_visd4sa/` (`train.jsonl`, `dev.jsonl`, `test.jsonl` — 11.122 mẫu).
- Tập dữ liệu miền đích YouTube gán nhãn: `data/gold_labels_train.jsonl` (3.000 mệnh đề) và `data/gold_labels_test.jsonl` (800 mệnh đề).
- Dữ liệu bình luận YouTube đã làm sạch & tách mệnh đề từ Công việc 6: `data/clean_data.jsonl` (473.786 bình luận).
- Hợp đồng dữ liệu chuẩn: `contracts/aspect-mention.schema.json` (Schema v2).

**Đầu ra bàn giao:** Mã nguồn huấn luyện (`src/models/aspect_baseline.py`, `src/models/train_aspect.py`), mô hình tốt nhất đã đóng gói (`artifacts/aspect_models/best_aspect_model.pkl` — `aspect-student-lr-v2`) và bảng đối sánh F1 theo từng khía cạnh (`aspect_f1_comparison.md`, `aspect_f1_comparison.csv`).

---

## 1. Định nghĩa Bài toán & Chuẩn hóa Hợp đồng Dữ liệu (Schema v2)

Bài toán phân loại khía cạnh được thiết kế dưới dạng **Phân loại đa nhãn (Multi-label Classification)** ở cấp độ mệnh đề (`clause_text`). Một mệnh đề có thể đồng thời nhắc tới một, nhiều hoặc không nhắc tới khía cạnh nào (`[]`) trong 9 khía cạnh chuẩn theo `contracts/aspect-mention.schema.json`:

- `BATTERY` (Pin & sạc)
- `DISPLAY` (Màn hình)
- `PERFORMANCE` (Hiệu năng & cấu hình)
- `CAMERA` (Máy ảnh & quay chụp)
- `DESIGN` (Thiết kế & ngoại hình)
- `SOFTWARE` (Phần mềm & hệ điều hành)
- `HARDWARE_OTHER` (Phần cứng khác: loa, mic, sóng, wifi, cảm biến, nhiệt độ...)
- `PRICE` (Giá bán & khuyến mãi)
- `WARRANTY` (Bảo hành, hậu mãi & nơi bán)

Khi tích hợp vào Pipeline chung (phục vụ Công việc 12), phương thức `predict_mentions(clause_text)` của mô hình trả về danh sách các gói tin JSON tuân thủ nghiêm ngặt Schema v2:
- `aspect`: Mã khía cạnh dự đoán.
- `confidence`: Xác suất dự đoán từ mô hình (`0.0` – `1.0`).
- `label_source`: `"rule"` (đối với Baseline) hoặc `"model"` (đối với Machine Learning).
- `model_version`: `"rule-v0"`, `"aspect-teacher-svm-v1"`, `"aspect-student-lr-v2"` hoặc `"aspect-student-svm-v2"`.

---

## 2. Phương pháp & Quy trình Huấn luyện (Teacher – Student Pipeline)

### 2.1. Mô hình Cơ sở — Baseline (`rule-v0`)
- Bóc tách bộ luật biểu thức chính quy (Regex trên văn bản chuẩn hóa không dấu `text_ascii`) từ `eda_smartphone_comments.ipynb` sang module độc lập `src/models/aspect_baseline.py` và ánh xạ về đúng 9 nhãn tiếng Anh của Schema v2.

### 2.2. Lượt 1 — Huấn luyện Teacher trên miền nguồn `UIT-ViSD4SA`
- **Khôi phục nhãn `SOFTWARE`:** Do bộ dữ liệu gốc `UIT-ViSD4SA` gộp nhận xét về phần mềm/hệ điều hành vào nhãn `PERFORMANCE` hoặc `FEATURES` (`HARDWARE_OTHER`), pipeline áp dụng bộ lọc ngữ cảnh trên từng tọa độ span `text[start:end]` để tách và khôi phục chính xác nhãn `SOFTWARE` (thu được 692 mẫu Train, 100 mẫu Dev và 193 mẫu Test).
- **Trích xuất đặc trưng & Huấn luyện:** Sử dụng `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=35000)` kết hợp `OneVsRestClassifier` với `LogisticRegression(class_weight="balanced")` và `CalibratedClassifierCV(LinearSVC(class_weight="balanced"))`.
- **Tối ưu ngưỡng (Threshold Tuning):** Dò tìm ngưỡng xác suất tối ưu riêng cho từng khía cạnh trên tập `dev.jsonl` (1.112 mẫu), sau đó huấn luyện lại trên tập gộp `Train + Dev` (8.897 mẫu).

### 2.3. Lượt 2 — Thích nghi miền YouTube & Huấn luyện Student (`aspect-student-lr-v2`)
Khi đánh giá trực tiếp Teacher lên bình luận YouTube, mô hình gặp hiện tượng lệch miền (**Domain Shift**) do văn phong YouTube ngắn, nhiều tiếng lóng, tỷ lệ mệnh đề không chứa khía cạnh (`[]`) cao (~64,5%) và khác biệt định nghĩa nhãn `WARRANTY`. Để xử lý triệt để, pipeline Student áp dụng 5 kỹ thuật tinh chỉnh:

1. **Chuẩn hóa dữ liệu YouTube Train:** Quy đổi các nhãn ngoài Schema phát sinh từ LLM (`AUDIO`, `SPEAKER` -> `HARDWARE_OTHER`; `STORAGE` -> `PERFORMANCE`) trong tập Train (3.000 mệnh đề), đồng thời giữ nguyên chuẩn gốc ở tập Test (800 mệnh đề) để đánh giá khách quan.
2. **Đặc trưng lai Word + Char N-gram:** Kết hợp `TfidfVectorizer` theo từ `ngram_range=(1, 2)` và theo ký tự `char_wb (3, 5)` qua `FeatureUnion` để xử lý tốt viết tắt, tiếng lóng và lỗi chính tả trên YouTube.
3. **Giảm nhiễu miền nguồn UIT:** Lược bỏ nhãn `WARRANTY` kiểu *"nhân viên nhiệt tình, giao hàng nhanh"* từ UIT, lấy mẫu gọn 4.000 dòng UIT và nhân trọng số Oversampling 4x cho tập YouTube Train.
4. **Sinh nhãn giả cân bằng (Balanced Pseudo-labeling):** Dùng Teacher quét qua `data/clean_data.jsonl` để trích xuất tối đa 2.000 mệnh đề dương độ tin cậy cao (`confidence >= 0.92`) kết hợp 2.000 mệnh đề âm (`max_prob <= 0.12`, nhãn `[]`) nhằm tránh thiên lệch đoán thừa nhãn.
5. **Mở rộng dải dò ngưỡng trên `YT Dev`:** Tách 20% `gold_labels_train.jsonl` làm tập `YT Dev` để tối ưu ngưỡng xác suất riêng cho từng khía cạnh trong khoảng `[0.15, 0.90]`, chặn hiệu quả các dự đoán sai (False Positive) trên câu rỗng.

---

## 3. Kết quả Thực nghiệm & So sánh F1 từng Khía cạnh

### 3.1. Giai đoạn 1: Đánh giá Teacher trên Miền nguồn `UIT-ViSD4SA` (`test.jsonl` — 2.225 mẫu)

Sau khi tích hợp cơ chế tự động khôi phục nhãn `SOFTWARE`, mô hình Teacher đạt kết quả cao đồng đều trên đủ 9/9 khía cạnh:

| Khía cạnh / Chỉ số | Baseline (`rule-v0`) | TF-IDF + LogReg (`aspect-lr-v1`) | TF-IDF + LinearSVM (`aspect-svm-v1`) | Cải thiện (SVM vs Baseline) |
| :--- | :---: | :---: | :---: | :---: |
| **BATTERY** | 0.9492 | 0.9488 | **0.9574** | +0.0082 |
| **DISPLAY** | 0.6713 | 0.7260 | **0.7312** | +0.0599 |
| **PERFORMANCE** | 0.8092 | **0.8311** | 0.8272 | +0.0180 |
| **CAMERA** | 0.7473 | 0.8964 | **0.9139** | +0.1666 |
| **DESIGN** | 0.5233 | 0.7811 | **0.8093** | +0.2860 |
| **SOFTWARE** | 0.4156 | 0.6514 | **0.6684** | +0.2528 |
| **HARDWARE_OTHER** | 0.0201 | **0.6441** | 0.6154 | +0.5953 |
| **PRICE** | 0.4404 | **0.6469** | 0.6109 | +0.1705 |
| **WARRANTY** | 0.4061 | **0.8112** | 0.8110 | +0.4049 |
| **MACRO_F1 (9 nhãn)** | 0.5536 | 0.7708 | **0.7716** | **+0.2180 (+21.80%)** |
| **MICRO_F1** | 0.6757 | 0.8322 | **0.8391** | **+0.1634 (+16.34%)** |

### 3.2. Giai đoạn 2: Đánh giá cuối cùng trên Miền đích YouTube (`gold_labels_test.jsonl` — 800 mệnh đề)

Để kiểm chứng khả năng thích nghi miền (Domain Adaptation) trên dữ liệu thực tế của hệ thống, 5 cấu hình mô hình được đánh giá độc lập trên cùng tập `gold_labels_test.jsonl` (800 mệnh đề YouTube, gồm 284 mệnh đề mang nhãn và 516 mệnh đề rỗng):

| Khía cạnh | 1. Baseline (`rule-v0`) | 2. Teacher SVM (Chỉ học UIT) | 3. Pure YT LogReg (Chỉ học Kiệt) | 4. Student LogReg (`aspect-student-lr-v2`) | 5. Student SVM (`aspect-student-svm-v2`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **BATTERY** | 0.8333 | 0.8667 | **0.8667** | 0.8475 | 0.8387 |
| **DISPLAY** | 0.5417 | 0.6441 | 0.5769 | **0.7119** | 0.6667 |
| **PERFORMANCE** | 0.5476 | 0.4752 | 0.5750 | **0.5773** | 0.5370 |
| **CAMERA** | 0.6078 | 0.8101 | 0.6944 | 0.7475 | **0.8261** |
| **DESIGN** | 0.4490 | 0.4409 | 0.4348 | **0.4510** | 0.4000 |
| **SOFTWARE** | 0.3721 | 0.2692 | 0.4151 | **0.5965** | 0.4706 |
| **HARDWARE_OTHER** | 0.0339 | 0.0714 | 0.1667 | **0.2388** | 0.1667 |
| **PRICE** | 0.5000 | 0.5567 | 0.6316 | **0.6842** | 0.6753 |
| **WARRANTY** | 0.4615 | 0.0784 | 0.7500 | **0.8000** | 0.0000 |
| **MACRO_F1** | 0.4830 | 0.4681 | 0.5679 | **0.6283** | 0.5090 |

### 3.3. Nhận xét & Đánh giá
- **Chứng minh hiện tượng Domain Shift:** Dù Teacher SVM đạt `Macro-F1 = 0.7716` trên `UIT-ViSD4SA`, khi áp trực tiếp sang bình luận YouTube điểm tụt xuống `0.4681` (thấp hơn Baseline `0.4830`), đặc biệt ở `WARRANTY` (`0.0784`) và `SOFTWARE` (`0.2692`) do khác biệt văn phong và ngữ nghĩa nhãn giữa hai miền.
- **Hiệu quả cộng hưởng của Pipeline Student (`aspect-student-lr-v2`):**
  - Đạt **`Macro-F1 = 0.6283`**, vượt Baseline **`+14.53%`**, vượt Teacher UIT **`+16.02%`**, và vượt cả mô hình chỉ huấn luyện trên dữ liệu YouTube (`Pure YT LogReg = 0.5679`) thêm **`+6.04%`**.
  - Dẫn đầu trên **7/9 khía cạnh**, cải thiện vượt bậc ở các nhãn khó như `WARRANTY` (`0.8000`), `DISPLAY` (`0.7119`), `PRICE` (`0.6842`), `SOFTWARE` (`0.5965`) và `HARDWARE_OTHER` (`0.2388`).
- **Lựa chọn mô hình bàn giao:** Mô hình **`Student LogReg (aspect-student-lr-v2)`** đạt hiệu năng cao và ổn định nhất trên miền đích YouTube nên được chọn đóng gói thành `artifacts/aspect_models/best_aspect_model.pkl` để bàn giao cho pipeline tổng hợp (STT 12).

---

## 4. Hướng dẫn Tái lập Kết quả & Sử dụng Model (Cho STT 7 & STT 12)

### 4.1. Lệnh chạy huấn luyện và xuất bảng điểm F1:
```bash
python src/models/train_aspect.py \
  --ext_train data/uit_visd4sa/train.jsonl \
  --ext_dev data/uit_visd4sa/dev.jsonl \
  --ext_test data/uit_visd4sa/test.jsonl \
  --yt_train data/gold_labels_train.jsonl \
  --yt_test data/gold_labels_test.jsonl \
  --clean_data data/clean_data.jsonl \
  --output_dir artifacts/aspect_models
```

### 4.2. Cách nạp mô hình đã lưu để dự đoán trong Pipeline (Dành cho STT 12):
```python
import sys
from pathlib import Path
import joblib

sys.path.append(str(Path("src/models").resolve()))
model = joblib.load("artifacts/aspect_models/best_aspect_model.pkl")

clause_text = "pin thì trâu thật nhưng màn hình hơi ám vàng"
mentions = model.predict_mentions(clause_text)
print(mentions)
# Kết quả trả về khớp chuẩn Schema v2:
# [
#   {'aspect': 'BATTERY', 'confidence': 0.9412, 'label_source': 'model', 'model_version': 'aspect-student-lr-v2'},
#   {'aspect': 'DISPLAY', 'confidence': 0.8835, 'label_source': 'model', 'model_version': 'aspect-student-lr-v2'}
# ]
```
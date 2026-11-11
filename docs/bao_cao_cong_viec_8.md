# Báo cáo Công việc STT 8: Xây dựng Mô hình Phân loại Khía cạnh (Aspect Classification)

**Người thực hiện:** Nguyễn Xuân Hồng Quân (Nhánh: `xhquan/cong-viec-8`)  
**Đầu vào:** Tập dữ liệu ngoài đã quy đổi (`data/uit_visd4sa/`), tập dữ liệu YouTube gán nhãn (`data/youtube_labeled/gold_labels_train.jsonl`) và hợp đồng dữ liệu `contracts/aspect-mention.schema.json` (Schema v2).  
**Đầu ra bàn giao:** Mã nguồn huấn luyện (`src/models/aspect_baseline.py`, `src/models/train_aspect.py`), mô hình đã huấn luyện (`artifacts/aspect_models/best_aspect_model.pkl`) và bảng đối sánh F1 theo từng khía cạnh.

---

## 1. Định nghĩa Bài toán & Chuẩn hóa Hợp đồng Dữ liệu (Schema v2)

Bài toán phân loại khía cạnh được thiết kế dưới dạng **Phân loại đa nhãn (Multi-label Classification)** ở cấp độ mệnh đề (`clause_text`). Một mệnh đề có thể đồng thời nhắc tới một, nhiều hoặc không nhắc tới khía cạnh nào (`[]` - không có khía cạnh) trong 9 khía cạnh chuẩn theo `contracts/aspect-mention.schema.json`:

* `BATTERY` (Pin & sạc)
* `DISPLAY` (Màn hình)
* `PERFORMANCE` (Hiệu năng & cấu hình)
* `CAMERA` (Máy ảnh & quay chụp)
* `DESIGN` (Thiết kế & ngoại hình)
* `SOFTWARE` (Phần mềm & hệ điều hành)
* `HARDWARE_OTHER` (Phần cứng khác: nhiệt độ, loa, sóng, cảm biến...)
* `PRICE` (Giá bán & khuyến mãi)
* `WARRANTY` (Bảo hành, hậu mãi & nơi bán)

Khi tích hợp vào Pipeline chung (phục vụ Công việc 12), phương thức `predict_mentions(clause_text)` của mô hình trả về danh sách các gói tin JSON tuân thủ nghiêm ngặt Schema v2:
* `aspect`: Mã khía cạnh dự đoán.
* `confidence`: Xác suất dự đoán từ mô hình (`0.0` – `1.0`).
* `label_source`: `"rule"` (đối với Baseline) hoặc `"model"` (đối với Machine Learning).
* `model_version`: `"rule-v0"`, `"aspect-lr-v1"` hoặc `"aspect-svm-v1"`.

---

## 2. Phương pháp & Quy trình Huấn luyện (Teacher – Student Pipeline)

1. **Mô hình Cơ sở — Baseline (`rule-v0`):**
   * Bóc tách bộ luật biểu thức chính quy (Regex trên văn bản chuẩn hóa không dấu `text_ascii`) từ `eda_smartphone_comments.ipynb` sang module độc lập `src/models/aspect_baseline.py` và ánh xạ về đúng 9 nhãn tiếng Anh của Schema v2.
2. **Mô hình Học máy Đa nhãn (Lượt 1 — Teacher trên `UIT-ViSD4SA`):**
   * **Trích xuất đặc trưng:** Sử dụng `TfidfVectorizer` với `ngram_range=(1, 2)`, `sublinear_tf=True`, `max_features=30000`.
   * **Mã hóa nhãn:** Dùng `MultiLabelBinarizer` chuyển đổi danh sách khía cạnh về vector nhị phân 9 chiều.
   * **Thuật toán thử nghiệm:**
     * `TF-IDF + OneVsRestClassifier(LogisticRegression(class_weight="balanced"))` (`aspect-lr-v1`).
     * `TF-IDF + OneVsRestClassifier(CalibratedClassifierCV(LinearSVC(class_weight="balanced")))` (`aspect-svm-v1`) — bọc Calibration để trích xuất xác suất `confidence` chuẩn xác cho từng nhãn.
   * **Tối ưu ngưỡng (Threshold Tuning trên tập Dev):** Thay vì dùng ngưỡng cố định `0.5`, mô hình sử dụng tập `dev.jsonl` (1.112 mẫu) để dò tìm ngưỡng xác suất tối ưu riêng cho từng khía cạnh trong khoảng `[0.20, 0.70]`, sau đó huấn luyện lại trên tập gộp `Train + Dev` (8.897 mẫu).
3. **Thích nghi miền YouTube (Lượt 2 — Student với `gold_labels_train.jsonl` & `clean_data.jsonl`):**
   * Hỗ trợ dùng mô hình Teacher quét qua `data/clean_data.jsonl` (từ Công việc 6) để lọc các mệnh đề có độ tự tin `confidence >= 0.90` làm nhãn giả (Pseudo-labels).
   * Kết hợp dữ liệu miền nguồn (`UIT-ViSD4SA`) với dữ liệu YouTube gán nhãn (`gold_labels_train.jsonl` từ Công việc 1, nhân trọng số Oversampling 3x cho miền đích) để huấn luyện mô hình Student. *(Hiện tại tập `gold_labels_train.jsonl` đã được tích hợp vào pipeline huấn luyện; ngay khi Công việc 1 & 7 chốt xong file `gold_labels_test.jsonl` độc lập, script sẽ tự động cập nhật bảng điểm trên tập Test YouTube).*

---

## 3. Kết quả Thực nghiệm & So sánh F1 từng Khía cạnh

Kết quả đánh giá độc lập trên tập Test chuẩn (`test.jsonl` — 2.225 mẫu, sau khi huấn luyện trên 7.785 mẫu Train và tinh chỉnh ngưỡng trên 1.112 mẫu Dev của bộ dữ liệu `UIT-ViSD4SA`):

| Khía cạnh / Chỉ số | Baseline (`rule-v0`) | TF-IDF + LogReg (`aspect-lr-v1`) | TF-IDF + LinearSVM (`aspect-svm-v1`) | Mức cải thiện (SVM so với Baseline) |
| :--- | :---: | :---: | :---: | :---: |
| **BATTERY** | 0.9492 | 0.9488 | **0.9574** | +0.0082 |
| **DISPLAY** | 0.6713 | 0.7260 | **0.7312** | +0.0599 |
| **PERFORMANCE** | 0.8247 | 0.8647 | **0.8651** | +0.0404 |
| **CAMERA** | 0.7473 | 0.8964 | **0.9139** | +0.1666 |
| **DESIGN** | 0.5233 | 0.7811 | **0.8093** | +0.2860 |
| **SOFTWARE** *(1)* | 0.0000 | 0.0000 | **0.0000** | — |
| **HARDWARE_OTHER** | 0.0199 | 0.6769 | **0.7143** | +0.6944 |
| **PRICE** | 0.4404 | **0.6469** | 0.6109 | +0.1705 |
| **WARRANTY** | 0.4061 | **0.8112** | 0.8110 | +0.4049 |
| **MACRO_F1 (9 nhãn)** | 0.5091 | 0.7058 | **0.7126** | **+0.2035 (+20.35%)** |
| **MICRO_F1** | 0.6812 | 0.8498 | **0.8580** | **+0.1768 (+17.68%)** |

> *(1) Ghi chú về khía cạnh `SOFTWARE`:* Trong bộ dữ liệu gốc `UIT-ViSD4SA` (cào từ Thế Giới Di Động), các nhận xét về hệ điều hành và ứng dụng được gộp chung vào nhãn `PERFORMANCE` hoặc `FEATURES`, dẫn tới số mẫu mang nhãn `SOFTWARE` trong tập gốc là 0. Nếu tính trung bình trên 8 khía cạnh hiện hữu trong tập dữ liệu này, **Macro-F1 thực tế của `TF-IDF + LinearSVM` đạt `0.8004`**. Khi kết hợp thêm tập `gold_labels_train.jsonl` trên miền YouTube của Kiệt (STT 1), khía cạnh `SOFTWARE` sẽ được bổ sung đầy đủ mẫu huấn luyện.

### Nhận xét & Đánh giá:
* **Hiệu quả vượt trội so với bộ luật từ khóa:** Mô hình `TF-IDF + LinearSVM` giúp tăng **Macro-F1 thêm +20.35%** (từ `0.5091` lên `0.7126`) và **Micro-F1 thêm +17.68%** (từ `0.6812` lên `0.8580`) so với Baseline `rule-v0`.
* **Khắc phục điểm mù từ vựng của Rule-based:** 
  * Ở khía cạnh **`HARDWARE_OTHER`**, bộ luật từ khóa chỉ bắt được 3 từ khóa về nhiệt độ nên F1 chỉ đạt `0.0199`; trong khi mô hình `LinearSVM` tự học được các cụm từ về loa, mic, sóng, wifi, vân tay, cảm biến... giúp F1 tăng vọt lên **`0.7143`**.
  * Các khía cạnh có cách diễn đạt đa dạng như **`WARRANTY`** (`0.4061` $\rightarrow$ `0.8110`), **`DESIGN`** (`0.5233` $\rightarrow$ `0.8093`), và **`CAMERA`** (`0.7473` $\rightarrow$ `0.9139`) đều ghi nhận mức tăng trưởng lớn nhờ khả năng nắm bắt ngữ cảnh n-gram `(1, 2)` của TF-IDF và tối ưu ngưỡng xác suất trên tập Dev.
* **Lựa chọn mô hình bàn giao:** Mô hình **`TF-IDF + LinearSVM` (`aspect-svm-v1`)** đạt điểm Macro-F1 và Micro-F1 cao nhất nên được chọn đóng gói thành file `artifacts/aspect_models/best_aspect_model.pkl` để bàn giao cho pipeline tổng hợp.

---

## 4. Hướng dẫn Tái lập Kết quả & Sử dụng Model (Cho STT 7 & STT 12)

### 4.1. Lệnh chạy huấn luyện và xuất bảng điểm F1:
```bash
python src/models/train_aspect.py \
  --ext_train data/uit_visd4sa/train.jsonl \
  --ext_dev data/uit_visd4sa/dev.jsonl \
  --ext_test data/uit_visd4sa/test.jsonl \
  --yt_train data/youtube_labeled/gold_labels_train.jsonl \
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
#   {'aspect': 'BATTERY', 'confidence': 0.9412, 'label_source': 'model', 'model_version': 'aspect-svm-v1'},
#   {'aspect': 'DISPLAY', 'confidence': 0.8835, 'label_source': 'model', 'model_version': 'aspect-svm-v1'}
# ]
```
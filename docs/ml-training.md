# Vòng đời mô hình học máy

> Mục đích: Mô tả các nhiệm vụ ML, nguồn dữ liệu có nhãn, cách gán nhãn, huấn luyện, đánh giá và đưa mô hình vào aspect_mentions; cập nhật lần cuối: 2026-10-28.

## 1. Các nhiệm vụ

| Nhiệm vụ | Đầu vào | Đầu ra | Loại bài toán | Công việc |
|---|---|---|---|---|
| Khía cạnh | mệnh đề | 0..n mã khía cạnh | phân loại **đa nhãn** có giám sát | 8 |
| Cảm xúc | (mệnh đề, khía cạnh) | `pos`/`neg`/`neu` | phân loại 3 lớp | 9 |
| Máy được nhắc | mệnh đề + comment cha + máy của video | `target_model`, `compare_with`, `compare_winner` | luật alias → có thể nâng lên ML | 10 |
| Spam | bình luận | `spam`/`not_spam` | phân loại nhị phân, lệch lớp | 11 |
| Đã dùng máy, loại lỗi | mệnh đề | `is_owner`, `defect_type` | luật (`label_source = "rule"`), nâng cấp nếu còn thời gian | 10 |

Mã nhãn theo [data-model.md](data-model.md#danh-mục-mã).

**Phân cụm không phải mô hình khía cạnh.** Phân cụm không bảo đảm các cụm khớp với 9 khía cạnh định trước, và chỉ gán mỗi bình luận vào một cụm. Bản nháp EDA cho silhouette ~0,17–0,20 với mọi k, tức gần như không có cấu trúc cụm. Phân cụm chỉ dùng để khám phá chủ đề mới hoặc hỗ trợ gán nhãn.

**Baseline bắt buộc:** luật từ khóa hiện có trong notebook EDA (`rule-v0`). Mọi mô hình phải báo cáo so với baseline này.

## 2. Nguồn dữ liệu

| Nguồn | Vai trò | Dùng để train? | Dùng để test? |
|---|---|---|---|
| Gold YouTube (`gold_labels`, `label_source = human`) | Ground truth đúng miền | Phần `train` | **Có, tập test chính** |
| Nhãn AI trên YouTube (`label_source = llm`) | Tăng dữ liệu train | Có | Không |
| UIT-ViSD4SA | Train span ABSA, đo chuyển miền | Có | Chỉ tập test riêng của dataset đó |
| UIT-ViSFD | Tham khảo để duyệt taxonomy; không có span | Không cho span task | Không cho span task |
| YouTube raw chưa nhãn | Inference, pseudo-label | Chỉ qua Teacher–Student | Không |

## 3. Dữ liệu có nhãn từ bên ngoài

### UIT-ViSFD

Khoảng 11 nghìn đánh giá smartphone trên trang thương mại điện tử, nhãn dạng `{CAMERA#Positive};{BATTERY#Negative}` (kiểm tra lại số liệu trên bài báo/trang gốc). Ánh xạ về bộ khía cạnh của dự án:

| UIT-ViSFD | Dự án | Ghi chú |
|---|---|---|
| BATTERY | `BATTERY` | khớp |
| CAMERA | `CAMERA` | khớp |
| SCREEN | `DISPLAY` | khớp |
| PERFORMANCE | `PERFORMANCE` | khớp |
| DESIGN | `DESIGN` | khớp |
| PRICE | `PRICE` | khớp |
| STORAGE | `HARDWARE_OTHER` | gộp |
| FEATURES | `HARDWARE_OTHER` / `SOFTWARE` | **mơ hồ**: đọc ~50 mẫu rồi chốt luật tách |
| SER&ACC | `WARRANTY` | gần khớp; phần phụ kiện lệch |
| GENERAL | — | bỏ, hoặc chỉ dùng cho cảm xúc chung |
| — | `SOFTWARE` | dataset ngoài không đủ, **phải tự gán** |

### UIT-ViSD4SA

UIT-ViSD4SA có nhãn span×sentiment ở đúng dạng cần cho ABSA. UIT-ViSFD chỉ gán aspect×sentiment cho toàn review, không có offsets; vì vậy **không đưa ViSFD vào tập span** và không tự suy diễn vị trí span. Script [`src/processing/normalize_external_absa.py`](../src/processing/normalize_external_absa.py) chỉ xuất ViSD4SA theo đúng hai trường:

```json
{"text": "Máy đẹp, pin trâu.", "labels": [[0, 7, "DESIGN#pos"], [9, 17, "BATTERY#pos"]]}
```

`labels` dùng `[start, end, "ASPECT#sentiment"]`, offsets theo chỉ số ký tự Python, sentiment là `pos`/`neg`/`neu`. Các nhóm đã thống nhất `SER&ACC → WARRANTY`, `STORAGE → HARDWARE_OTHER`; `FEATURES` chưa ánh xạ và không được xuất trong nhãn huấn luyện cho tới khi duyệt mẫu. `GENERAL` cũng bị loại vì không thuộc taxonomy. Span có offset không hợp lệ bị bỏ khỏi nhãn đầu ra và đếm trong `report.json`; không tự sửa.

Script tạo thêm `features_review.html` với 50 mẫu (tối đa 25 mẫu từ mỗi bộ) để nhóm phân loại `FEATURES` là phần cứng, phần mềm, tùy ngữ cảnh hay khác/không rõ. UI chạy cục bộ trên trình duyệt, không gửi dữ liệu ra ngoài; nút xuất JSON cho phép tải kết quả hoặc sao chép từ ô hiển thị nếu trình duyệt chặn tải file, rồi nhóm tổng hợp để chốt quy tắc ánh xạ. Mẫu ViSFD trong UI chỉ phục vụ xem xét taxonomy, không phải dữ liệu span đã gán.

Chạy từ thư mục gốc repo:

```powershell
python src/processing/normalize_external_absa.py
python -m unittest discover -s tests -p "test_normalize_external_absa.py"
```

Mặc định script đọc hai thư mục dataset nằm cạnh repo và ghi `uit_visd4sa/{train,dev,test}.jsonl`, `report.json` và UI vào `data/external/normalized/` (được `.gitignore` loại trừ). Mở `features_review.html` trong trình duyệt để duyệt mẫu. Có thể truyền `--visfd-dir`, `--visd4sa-dir` và `--output-dir` để đổi đường dẫn. Script đọc lại và kiểm tra đầu ra: chỉ có `text`/`labels`, span hợp lệ và thống kê nhãn sau ánh xạ.

Giới hạn:
- **Khác miền:** đánh giá của người mua trên sàn ngắn gọn; bình luận YouTube nhiều teencode, mỉa mai, so sánh, nói về người review. Mô hình học từ dataset ngoài sẽ giảm độ chính xác trên YouTube → luôn đo trên gold YouTube.
- **Khác đơn vị:** dataset gán nhãn cả bình luận; dự án cần nhãn mệnh đề.
- **Không có `target_model`.**
- **Giấy phép:** thường chỉ cho nghiên cứu; ghi nguồn trích dẫn trong báo cáo.

### ViSpamReviews

Đánh giá trên sàn thương mại điện tử gán nhãn spam/không spam. Định nghĩa spam ("đánh giá giả, không liên quan sản phẩm") khác với spam YouTube (link, cờ bạc, seeding) nên chỉ dùng tham khảo.

### Thí nghiệm chuyển miền (nên có trong báo cáo)

1. Train trên UIT-ViSD4SA span hợp lệ → chấm trên gold YouTube test.
2. Train trên UIT-ViSD4SA + gold YouTube train → chấm lại cùng tập test.
3. So sánh để thấy dữ liệu ngoài giúp được bao nhiêu và mất bao nhiêu khi chuyển miền.

## 4. Gán nhãn

- **Guideline trước, gán sau.** Guideline (`docs/labeling-guideline.md`) có: định nghĩa từng khía cạnh và ví dụ biên, ví dụ `pos`/`neg`/`neu`, cách xử lý phủ định ("không lag chút nào" = khen), mỉa mai, so sánh 2 máy, reply (đọc `parent_text`), mệnh đề không có khía cạnh.
- **Hiệu chỉnh:** cả nhóm gán thử 50 mệnh đề giống nhau, so kết quả, sửa guideline, rồi mới gán thật. Ghi `guideline_version`.
- **Chọn mẫu:** rải đều theo `video_id` và theo máy trong phạm vi; không lấy dồn vào vài video lớn.
- **Tập test (~800 mệnh đề):** chỉ người gán; mỗi mệnh đề 2 người độc lập; tính **Cohen's kappa** cho khía cạnh và cảm xúc (mục tiêu ≥ 0,6). Mệnh đề lệch nhau do người thứ ba quyết định.
- **Nhãn AI:** được dùng cho phần train, ghi `label_source = "llm"` và `annotator` = tên mô hình. Lấy ngẫu nhiên ~200 mệnh đề AI đã gán cho người kiểm tra, báo cáo tỷ lệ đúng. **Không** dùng nhãn AI để chấm điểm mô hình.

## 5. Chia tập và đánh giá

Khung chung (Công việc 7), mọi mô hình dùng chung:

- Chia theo `video_id`: không có hai mệnh đề cùng video nằm ở cả train và test.
- Test set cố định từ đầu, không dùng để chọn siêu tham số; chọn tham số bằng cross-validation trên train (gom nhóm theo video).
- Metric:
  - Khía cạnh: precision/recall/F1 từng khía cạnh, micro-F1, macro-F1.
  - Cảm xúc: macro-F1, F1 từng lớp, confusion matrix.
  - Máy được nhắc: precision/recall, tỷ lệ `null`.
  - Spam: precision/recall/F1 lớp `spam` (không dùng accuracy).
- Báo cáo kèm phân tích lỗi: 20–30 ví dụ sai, phân loại nguyên nhân.

Cấu trúc thư mục đề xuất (không commit dữ liệu, chỉ commit script):

```text
data/
├── clean_data.jsonl                # đầu ra tiền xử lý (Công việc 6)
├── external/
│   └── uit_visfd/                  # dữ liệu gốc + bản đã map (Công việc 5)
└── labels/
    ├── gold_labels.jsonl           # người + AI gán (Công việc 1)
    └── split.json                  # danh sách video_id train/test (Công việc 7)
```

## 6. Huấn luyện và lưu mô hình

Baseline: TF-IDF + Logistic Regression/Linear SVM. Nâng cấp: PhoBERT nếu đủ tài nguyên. Chọn mô hình cuối theo kết quả cross-validation, báo cáo trên test.

Mỗi mô hình lưu kèm:
- phiên bản dữ liệu (số dòng + checksum) và `guideline_version`;
- cách tiền xử lý/tokenizer;
- danh sách nhãn;
- siêu tham số;
- metric trên test;
- file mô hình + checksum;
- ngày huấn luyện, `model_version`.

## 7. Đưa mô hình vào dữ liệu

```text
comments (đã tiền xử lý, không spam)
   └─ mỗi mệnh đề
        ├─ mô hình khía cạnh      → 0..n aspect
        ├─ mô hình cảm xúc        → sentiment cho từng aspect
        └─ nhận diện máy          → target_model, compare_with, compare_winner
             └─ ghi aspect_mentions (label_source = "model", model_version, confidence)
                  └─ tính aggregates → Q1–Q5
```

Chạy lại toàn bộ khi đổi `model_version`. Không ghi đè dữ liệu raw.

## 8. Teacher–Student (tùy chọn)

Teacher (mô hình tốt nhất) gán pseudo-label cho YouTube chưa nhãn, chỉ giữ dự đoán có `confidence` cao; mẫu confidence thấp đưa vào hàng đợi người duyệt. Student (nhẹ hơn) học từ pseudo-label. Student chỉ được dùng nếu trên gold YouTube test không kém Teacher đáng kể. Pseudo-label không bao giờ vào tập test.

## 9. Nguyên tắc chống rò rỉ dữ liệu

- Không chia mệnh đề cùng một video vào cả train và test.
- Không dùng tập test để chọn siêu tham số.
- Không coi nhãn luật, nhãn AI hay pseudo-label là ground truth.
- Không train trên dữ liệu đã dùng để báo cáo kết quả Q1–Q5 nếu chưa có nhãn người.
- Đổi tiền xử lý hoặc mô hình → tăng phiên bản, chạy lại đánh giá.

## 10. Liên kết

- Thiết kế dữ liệu: [data-model.md](data-model.md)
- Đặc tả Q1–Q5: [EDA_requirement.md](EDA_requirement.md)
- Kế hoạch: [roadmap.md](roadmap.md)
- Notebook EDA (bản nháp): [eda_smartphone_comments.ipynb](../src/processing/eda_smartphone_comments.ipynb)

# Phát hiện spam (Công việc 11)

> Mục đích: Hướng dẫn chạy lại việc lấy mẫu, gán nhãn, huấn luyện, đánh giá và áp dụng bộ lọc spam; cập nhật lần cuối: 2026-11-17.

Kết quả và kết luận: [docs/reports/cv11-spam.md](../../../docs/reports/cv11-spam.md). Định nghĩa nhãn: [docs/spam-labeling-guideline.md](../../../docs/spam-labeling-guideline.md).

**Trạng thái:** code, mẫu, nhãn và kết quả đã có. Nhãn hiện do AI gán; tập test **chờ người duyệt** (bước 3) trước khi số liệu được coi là chính thức.

## Cần có

- Python 3.10 trở lên: `python -m pip install -r src/processing/spam/requirements.txt`
- `data/clean_data.jsonl` đúng bản chuẩn v1.0 (xem [src/processing/README.md](../README.md)). Mọi lệnh dưới đây kiểm tra SHA-256 và dừng nếu sai phiên bản.

Chạy mọi lệnh từ thư mục gốc repo.

## Các bước

| # | Lệnh | Kết quả |
|---|---|---|
| 1 | `python -m src.processing.spam.sampling --export-batches` | Mẫu 640 bình luận theo tầng: `labels/spam_sample_v1.tsv`, `labels/spam_strata_v1.json`; file văn bản để gán nhãn trong `data/labels/spam/` |
| 2 | `python -m src.processing.spam.labels merge --annotator-ids "<mã người gán>"` | Gộp `annotator_A.tsv` và `annotator_B.tsv`, in Cohen's kappa. Còn dòng lệch thì ghi `disagreements.txt` và dừng; điền `adjudication.tsv` rồi chạy lại. Xong thì ghi `labels/spam_labels_v1.tsv` |
| 3 | `python -m src.processing.spam.labels export-review` rồi `import-review --reviewer <mã>` | Người duyệt tập test bằng Excel; dòng đã duyệt chuyển `label_source = human`; in tỷ lệ AI gán đúng |
| 4 | `python -m src.processing.spam.train` | Chọn mô hình bằng cross-validation trên train, chấm trên test, ghi `results/spam_eval_v1.json` và mô hình `data/models/spam-lr-v1.joblib` |
| 5 | `python -m src.processing.spam.report` | Sinh lại `docs/reports/cv11-spam.md` từ file kết quả |
| 6 | `python -m src.processing.spam.predict` | Áp dụng phương án đã chọn lên `clean_data.jsonl`, ghi `data/spam_predictions.jsonl` (mỗi dòng một `comment_id`) |

Bước 1 và 2 đã làm xong; chỉ chạy lại khi đổi thiết kế mẫu hoặc gán lại. Sau khi sửa nhãn (bước 3) phải chạy lại bước 4 và 5; test `test_committed_results_match_committed_labels` sẽ báo nếu quên.

### Duyệt nhãn tập test (bước 3)

1. `python -m src.processing.spam.labels export-review` tạo `data/labels/spam/review_test.csv` (272 dòng).
2. Mở bằng Excel. Mỗi dòng có nội dung bình luận và nhãn AI đã gán (`label`, `spam_type`, `lang`).
   - Nhãn đúng: gõ `x` vào cột `ok`.
   - Nhãn sai: để trống `ok`, điền `human_label` (`spam`/`ham`), `human_spam_type` nếu là spam, `human_lang` nếu ngôn ngữ cũng sai.
3. Lưu lại dưới dạng CSV UTF-8, rồi `python -m src.processing.spam.labels import-review --reviewer nlquan`.

Dòng nào để trống cả `ok` và `human_label` được coi là chưa duyệt và giữ `label_source = llm`.

## Dùng trong code

```python
from src.processing.spam.predict import SpamDetector

detector = SpamDetector.load()            # chế độ "hybrid": luật gắn cờ VÀ mô hình xác nhận
detector.predict(["Mua tại https://… giảm giá sốc", "Great phone!", "😂😂😂"])
# [{'is_spam': True,  'spam_score': 0.93, 'spam_reasons': ['contains_url'], 'lang': 'vi',    'is_vietnamese': True,  ...},
#  {'is_spam': False, 'spam_score': 0.05, 'spam_reasons': [],               'lang': 'other', 'is_vietnamese': False, ...},
#  {'is_spam': False, 'spam_score': 0.01, 'spam_reasons': [],               'lang': 'none',  'is_vietnamese': False, ...}]
```

Điểm số trong ví dụ chỉ để minh họa định dạng. `is_spam` và `is_vietnamese` là hai kết quả độc lập, đúng như [data-model.md](../../../docs/data-model.md#3-comments). Mỗi kết quả kèm `label_source` và `model_version`.

## File

| File | Vai trò |
|---|---|
| [config.py](config.py) | Đường dẫn, phiên bản dữ liệu, seed, cỡ mẫu từng tầng, tỷ lệ test |
| [data.py](data.py) | Kiểm tra checksum dữ liệu, chia train/test theo `video_id`, nối nội dung vào file nhãn |
| [baseline.py](baseline.py) | Gọi lại `rule-v0` của `cleaner` (không sửa), tách lý do thành nhóm |
| [sampling.py](sampling.py) | Chia tầng và rút mẫu |
| [labels.py](labels.py) | Gộp hai lượt gán, phân giải, vòng người duyệt |
| [language.py](language.py) | Nhận diện `vi` / `other` / `none`, tách khỏi spam |
| [model.py](model.py) | Tiền xử lý và các mô hình ứng viên |
| [evaluate.py](evaluate.py) | Precision/recall/F1 có trọng số tầng, bootstrap, McNemar, kappa |
| [train.py](train.py), [report.py](report.py), [predict.py](predict.py) | Huấn luyện + đánh giá, sinh báo cáo, áp dụng |
| `labels/`, `results/` | Mẫu, nhãn, kết quả. Chỉ có ID và số liệu, **không có nội dung bình luận** |

Nội dung bình luận, file làm việc của người gán và file mô hình nằm trong `data/` và không vào git.

## Kiểm thử

```powershell
python -m pytest tests/test_spam_detection.py -q
```

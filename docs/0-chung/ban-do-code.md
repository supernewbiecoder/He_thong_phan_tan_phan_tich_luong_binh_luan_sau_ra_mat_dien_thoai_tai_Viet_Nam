# Bản đồ code: file nào để làm gì

> Mục đích: Giải thích từng thư mục và file code để làm gì, đọc gì, ghi gì, khi nào phải sửa; cập nhật lần cuối: 2026-11-20.

**Đọc theo thứ tự này:** mục 1 để thấy dữ liệu đi qua những thư mục nào; mục 2 để tra một file cụ thể; mục 4 khi cần sửa một thứ mà không biết sửa ở đâu.

Tài liệu (docs) có mục lục riêng ở [docs/README.md](../README.md), kèm quy tắc đặt tên. File này chỉ nói về **code và dữ liệu**.

## 1. Dữ liệu đi qua những thư mục nào

| Tầng | Làm gì | Code | Đọc | Ghi | Trạng thái |
|---|---|---|---|---|---|
| 1. Thu thập | Tìm video trên các kênh trong config, cào bình luận | `src/ingest/` | YouTube API, `config/pipeline.yaml` | `src/ingest/data/raw/comments.jsonl` (v4), `videos.jsonl`, `state.db`, `models.json` | Chạy được |
| 2. Tiền xử lý | Làm sạch, chuẩn hóa, tách mệnh đề, gắn cờ tiếng Việt và spam | `src/processing/` | file raw của tầng 1 | `data/processed/comments.jsonl` + manifest | Chạy được (`processing-2.0`), chưa chạy trên v4 |
| 3. Gán nhãn | Người gán theo guideline; LLM gán phần train | `src/models/sentiment/llm_label.py` | mệnh đề (guideline v0.3); từ 20/11 phải chuyển sang cả bình luận | `data/task9/` | Nhãn LLM có trên máy người làm Công việc 9; chưa có nhãn người |
| 4. Suy luận, mô hình | Suy luận theo cả bình luận → `aspect_mentions`; huấn luyện mô hình khía cạnh, cảm xúc | `src/models/` | `data/processed/comments.jsonl`; dataset ngoài, nhãn LLM | `data/aspect_mentions.jsonl` (+ `.comments.jsonl`, manifest); `artifacts/`, `data/task9/model/` | Suy luận chạy được bằng luật mốc `rule-v1`, chưa đo. Mô hình mới đo trên dataset ngoài hoặc nhãn LLM |
| 5. Phân tích | Đếm khen/chê, khoảng tin cậy, kiểm định Q1–Q5 | `src/analysis/` | `data/aspect_mentions.jsonl`, `data/aspect_mentions.comments.jsonl` | `data/aggregates/` | Chạy được; `config/analysis.yaml` còn là bộ máy cũ |

**Cả chuỗi 2 → 4 → 5** chạy bằng `python -m src.run` (file `src/run.py`), mỗi ngày một lần: [luồng xử lý mục 2](luong-xu-ly.md#2-giai-đoạn-1-theo-lô).
| 6. Lưu trữ | MongoDB 7 collection | `src/storage/` | dữ liệu đã xử lý | MongoDB | Theo contract v1; dữ liệu mẫu là giả |

Ba thứ **không phải code** nhưng code đọc trực tiếp, nên sửa chúng là đổi hành vi của code:

| File | Chứa gì | Ai đọc |
|---|---|---|
| `config/pipeline.yaml` | Danh mục máy (mã, tên gọi, `launch_date`, đối thủ), danh sách kênh, cửa sổ thời gian, hạn mức API | Crawler; bước suy luận (nhận tên máy, tính `days_since_launch`); `src/analysis/` |
| `config/analysis.yaml` | Bộ 4 máy, cửa sổ, phiên bản nhãn cần phân tích | `src/analysis/` |
| `contracts/*.schema.json` | Định dạng bắt buộc của một bình luận raw (`comment-event` v3) và một mention (`aspect-mention` v2); `aspect-mention.example.json` là ví dụ | Crawler (`crawler/schema.py` phải khớp), `src/analysis/validation.py`, mọi nhóm ghi/đọc dữ liệu |
| `src/ingest/.env` (tự tạo từ `.env.example`, không commit) | API key YouTube, salt băm tác giả, địa chỉ Kafka, tên máy crawl (`CRAWLER_WORKER`) | Crawler |

## 2. Từng thư mục

### `src/ingest/`: tầng 1, crawler YouTube

Chạy từ `src/ingest/` bằng `python -m crawler.main <lệnh>`. Hướng dẫn: [docs/1-thu-thap/huong-dan.md](../1-thu-thap/huong-dan.md). Đặc tả: [docs/1-thu-thap/dac-ta.md](../1-thu-thap/dac-ta.md).

| File | Để làm gì |
|---|---|
| `crawler/main.py` | Cửa vào: nhận lệnh `discover` (tìm video), `crawl` (cào bình luận), `run` (chạy liên tục theo lịch), `status` (đếm video, hạn mức), `models` (in cửa sổ thời gian từng máy), `snapshot-videos` (cập nhật lượt xem, like), `replay`, `dedupe`, `relabel`, `repair-missing`, các lệnh `*-authors`, `worker-init`, `resolve-names`, `find-channels` |
| `crawler/discover.py` | Quét danh sách video đã đăng của từng kênh trong config (không dùng tìm kiếm YouTube), giữ video có tiêu đề chứa tên gọi của máy và đăng trong khoảng ngày cho phép; đoán loại video (`video_type`) từ tiêu đề |
| `crawler/models.py` | Đọc danh mục máy từ config: tên gọi, `launch_date`, cửa sổ thời gian của từng máy; ghi `data/models.json` |
| `crawler/crawl.py` | Cào bình luận của từng video, dừng/tiếp tục được bất cứ lúc nào (nhớ trang đang dở), chỉ giữ bình luận trong cửa sổ, băm tác giả thành `author_hash` |
| `crawler/youtube.py` | Gọi YouTube Data API (kênh, video, bình luận, reply, tìm kênh), xử lý lỗi và thử lại |
| `crawler/quota.py` | Đếm đơn vị hạn mức API trước mỗi lần gọi, dừng khi gần hết hạn mức ngày |
| `crawler/store.py` | Tạo cơ sở dữ liệu trạng thái `data/state.db`: kênh, mọi video của kênh (`uploads`), video được chọn và trạng thái crawl (`videos`), bình luận đã thấy, tài khoản người bình luận, hạn mức đã dùng |
| `crawler/sinks.py` | Ghi bình luận ra file JSONL (và Kafka nếu bật) |
| `crawler/schema.py` | Danh sách trường của một bình luận, một video và `SCHEMA_VERSION` mà crawler ghi ra |
| `crawler/config.py` | Đọc `config/pipeline.yaml` và `.env`, chỉ đường dẫn `data/` |
| `crawler/lock.py` | Không cho hai crawler cùng ghi một lúc |
| `crawler/timeutil.py` | Đọc/ghi thời gian, bỏ dấu tiếng Việt khi so tiêu đề |
| `crawler/authors.py` | Lấy 6 trường `author_*` (schema v3): tra ngược kênh người viết, rồi ngày tạo kênh, số video, số người đăng ký |
| `crawler/replay.py` | Phát lại bình luận đã lưu vào Kafka theo đúng thứ tự thời gian (phần streaming, tùy chọn) |
| `crawler/dedupe.py`, `crawler/relabel.py` | Dọn dữ liệu đã cào: bỏ bình luận trùng; đổi nhãn máy của dữ liệu cũ |
| `crawler/repair_labels.py`, `crawler/repair_missing.py` | Sửa dữ liệu cũ sau khi đổi config: gắn lại nhãn máy cho video; cào lại bình luận "mồ côi" (đã đánh dấu là đã thấy nhưng không có trong file) |
| `check_data.py` | Kiểm tra nhanh dữ liệu vừa cào: dòng hỏng, trùng, sai schema, ngoài cửa sổ, phân bố theo máy |
| `docker-compose.dev.yml` | Dựng Kafka (streaming, tùy chọn) và MongoDB (tầng 6) trên máy |
| `requirements.txt`, `.env.example`, `.gitignore` | Thư viện cho crawler; mẫu file bí mật; file không đưa lên git của riêng crawler |

### `src/processing/`: tầng 2, tiền xử lý

Đặc tả: [docs/2-tien-xu-ly/dac-ta.md](../2-tien-xu-ly/dac-ta.md). Hướng dẫn: [docs/2-tien-xu-ly/huong-dan.md](../2-tien-xu-ly/huong-dan.md). Chạy từ gốc repo bằng `python -m src.processing.run`.

| File | Để làm gì | Đặc tả |
|---|---|---|
| `__init__.py` | Gom các hàm dùng chung (`lam_sach`, `chuan_hoa`, `tach_menh_de`, `gan_co`, `tach_emoji`, `tach_tu`) và giữ `PIPELINE_VERSION` | `dac-ta.md` mục 6 |
| `clean.py` | 2.1 làm sạch kỹ thuật, bước B1–B7 → `text_clean` | `dac-ta-lam-sach.md` |
| `normalize.py` | 2.2 chuẩn hóa, bước N1–N7 → `text_norm`; tách emoji; tách chữ cho EDA | `dac-ta-chuan-hoa.md` |
| `clauses.py` | 2.3 tách mệnh đề → `clauses` (vị trí bằng chứng, đơn vị chấm của luật mốc) | `dac-ta-tach-menh-de.md` |
| `flags.py` | 2.4 gắn cờ → `is_vietnamese`, `is_spam`, `spam_reasons` (luật mốc) | `dac-ta-gan-co.md` |
| `resources/abbreviations.tsv` | Từ điển viết tắt cho N6; đầu file ghi các mục cố ý chưa đưa vào | `dac-ta-chuan-hoa.md` mục 6 |
| `run.py` | Lệnh chạy cả file raw, ghi `data/processed/comments.jsonl` và `comments.manifest.json` | `dac-ta.md` mục 2 |

### `src/models/`: tầng 4, mô hình

Đặc tả: [docs/4-mo-hinh/dac-ta.md](../4-mo-hinh/dac-ta.md), bước suy luận: [dac-ta-suy-luan.md](../4-mo-hinh/dac-ta-suy-luan.md). Chạy bước suy luận từ gốc repo bằng `python -m src.models.run`.

| File | Để làm gì | Lưu ý |
|---|---|---|
| `run.py` | Bước suy luận theo cả bình luận: đọc file tầng 2, ghi `data/aspect_mentions.jsonl` (đúng contract v2), `aspect_mentions.comments.jsonl` (cho Công việc 12) và manifest; giữ `MODEL_VERSION` | Hiện dùng luật mốc `rule-v1`; thay từng phần bằng mô hình theo đặc tả mục 9 |
| `aspect/keywords.py` | Bộ từ khóa 9 khía cạnh và hàm `khia_canh`; dùng chung với notebook `3_aspect_keywords` | Chuyển từ notebook 19/11; khác `rule_baseline.py` |
| `sentiment/rules.py` | Luật cảm xúc mốc: cụm khen/chê, phủ định, câu hỏi | Chưa đo trên nhãn người |
| `target_model.py` | Nhận tên máy theo danh mục, xác định máy được nhắc cho từng nhận xét (xét cả bình luận, comment cha, máy của video), tính `days_since_launch` | Chưa nhận câu so sánh (`compare_with`) |
| `owner_defect.py` | Luật mốc `is_owner`, `defect_type` cho Q5 | Không thấy dấu hiệu thì `null` |
| `external_absa.py` | Công việc 5: chuẩn hóa UIT-ViSD4SA (nhãn theo đoạn) về 9 khía cạnh; tạo trang duyệt nhãn `FEATURES`. Đọc dataset đặt cạnh repo, ghi `data/external/normalized/` | `FEATURES` chưa chốt |
| `aspect/rule_baseline.py` | Công việc 8: luật từ khóa `rule-v0` cho 9 khía cạnh, chạy trên chữ bỏ dấu | Xếp nóng máy vào `HARDWARE_OTHER`, trái thiết kế dữ liệu (`PERFORMANCE`) |
| `aspect/train.py` | Công việc 8: TF-IDF + Logistic Regression / LinearSVC đa nhãn, dò ngưỡng trên dev; ghi `artifacts/aspect_models/` | Đọc `data/uit_visd4sa/`, không khớp chỗ `external_absa.py` ghi ra; dữ liệu không có `SOFTWARE`. Báo cáo: [bao-cao-khia-canh.md](../4-mo-hinh/bao-cao-khia-canh.md) |
| `sentiment/extract_clauses.py` | Công việc 9: lấy mệnh đề từ file đã xử lý ra `data/task9/clauses.jsonl` | Với file của tầng 2, chạy kèm `--index-base 0` |
| `sentiment/llm_label.py` | Gán khía cạnh + cảm xúc bằng LLM theo [guideline](../3-gan-nhan/huong-dan-gan-nhan.md); lưu vết đủ prompt, model, SHA | Nhãn LLM chỉ để train, không làm test |
| `sentiment/build_sentiment_dataset.py` | Làm phẳng nhãn LLM thành cặp (mệnh đề, khía cạnh, cảm xúc); chia train/val theo video | |
| `sentiment/train_baseline.py` | TF-IDF + Logistic Regression cho cảm xúc; đường cong học | Đo trên nhãn LLM. Báo cáo: [bao-cao-cam-xuc.md](../4-mo-hinh/bao-cao-cam-xuc.md) |
| `sentiment/review_sample.py`, `review_sentiment.py`, `eval_labels.py` | Xuất mẫu cho người kiểm tra nhãn, chấm lại; so hai bộ nhãn | |
| `sentiment/make_report_figures.py` | Vẽ hình báo cáo cảm xúc vào `docs/4-mo-hinh/hinh-cam-xuc/` | |

Hướng dẫn chạy phần cảm xúc: [huong-dan-cam-xuc.md](../4-mo-hinh/huong-dan-cam-xuc.md).

### `src/analysis/`: tầng 5, aggregates và Q1–Q5

Hướng dẫn: [docs/5-phan-tich/huong-dan.md](../5-phan-tich/huong-dan.md). Chạy từ gốc repo bằng `python -m src.analysis.build_aggregates` (thêm `--demo` để chạy bằng dữ liệu mẫu trong `tests/fixtures/`).

| File | Để làm gì |
|---|---|
| `validation.py` | Kiểm tra mention theo contract `aspect-mention` v2 và đối chiếu với bình luận nguồn |
| `validate_inputs.py` | Lệnh chẩn đoán đầu vào, chỉ chạy phần kiểm tra |
| `aggregation.py` | Đếm theo máy × khía cạnh × tuần × video × nguồn × phiên bản; đối soát số đếm |
| `questions.py` | Q1–Q5: tỷ lệ, khoảng tin cậy bootstrap theo cụm video, kiểm định, hiệu chỉnh Holm, điều kiện được kết luận |
| `build_aggregates.py` | Lệnh chạy cả luồng, ghi `aggregates.jsonl`, `business_questions.json`, `aggregation_manifest.json` vào `data/aggregates/` |
| `requirements.txt` | Thư viện riêng của tầng 5 |

### `src/storage/`: tầng 6, MongoDB

Đặc tả: [docs/6-luu-tru/dac-ta.md](../6-luu-tru/dac-ta.md). Hướng dẫn: [docs/6-luu-tru/huong-dan.md](../6-luu-tru/huong-dan.md).

| File | Để làm gì | Lưu ý |
|---|---|---|
| `init_db.py` | Tạo 7 collection, validator, index | Theo contract v1 |
| `seed_db.py` | Nạp dữ liệu mẫu | Video, aggregates, alerts, gold_labels viết tay; chỉ dùng để demo DB, không dùng để phân tích |
| `verify_db.py` | 8 phép kiểm tra; `--mock` chạy bằng mongomock và tự nạp dữ liệu mẫu | |

### `notebooks/`

| File | Để làm gì |
|---|---|
| `helpers.py` | Hàm dùng chung cho mọi notebook: tìm gốc repo, đường dẫn dữ liệu, đọc JSONL và manifest, đọc bộ 4 máy từ `config/analysis.yaml`, in bảng trước → sau |
| `1_raw_audit.ipynb` | Tầng 1: kiểm tra dữ liệu gốc (Level 0); theo máy, tuần sau ra mắt, bộ 4 máy; kênh, loại video, video tặng quà, reply, like. Đọc file raw |
| `2_1_clean.ipynb`, `2_2_normalize.ipynb`, `2_3_clauses.ipynb` | Tầng 2: từng bước làm sạch, chuẩn hóa, tách mệnh đề, trước → sau. Đọc `data/processed/comments.jsonl` và tự kiểm file khớp code |
| `3_aspect_keywords.ipynb` | Khía cạnh theo từ khóa; bộ 4 máy × khía cạnh. Đọc file đã xử lý; bộ từ khóa lấy từ `src/models/aspect/keywords.py` |
| `4_sentiment_report.ipynb` | Tầng 4: vẽ hình báo cáo cảm xúc từ `data/task9/model/metrics.json` |

Notebook không ghi file nào. Cách chạy, thứ tự chạy: [hướng dẫn tầng 2 mục 2](../2-tien-xu-ly/huong-dan.md#2-notebook).

### `tests/`

Chạy hết: `python -m pytest tests -q` (cần `pytest` và `src/analysis/requirements.txt`). Riêng tầng 2 chạy được bằng `python -m unittest tests.test_processing tests.test_processing_clauses tests.test_processing_flags`.

| File | Kiểm tra gì |
|---|---|
| `test_processing.py` | Tầng 2: làm sạch, chuẩn hóa, từ điển, emoji, lệnh chạy (21 test) |
| `test_processing_clauses.py` | Tầng 2: tách mệnh đề (11 test) |
| `test_processing_flags.py` | Tầng 2: gắn cờ tiếng Việt và spam (7 test) |
| `test_models_run.py` | Bước suy luận: từng luật mốc, quy tắc gộp, đúng contract, chạy thông tới aggregates của Công việc 12 (13 test) |
| `test_models_external_absa.py` | Công việc 5: chuẩn hóa UIT-ViSD4SA |
| `test_analysis_validation.py`, `test_analysis_aggregation.py`, `test_analysis_questions.py` + `fixtures/` | Công việc 12: kiểm tra đầu vào, đếm aggregates, khoảng tin cậy, Holm. `fixtures/` cũng là dữ liệu cho `--demo` |

Kiểm tra dữ liệu crawl dùng `src/ingest/check_data.py`.

### `artifacts/`

| File | Nội dung |
|---|---|
| `aspect_models/aspect_f1_comparison.csv`, `.md` | Bảng F1 của Công việc 8. File model `.pkl` do `aspect/train.py` sinh ra, không đưa lên git |

## 3. Thư mục không vào git (`.gitignore`)

| Thư mục / file | Chứa gì | Xóa được không |
|---|---|---|
| `.venv/` | Môi trường Python | Được; tạo lại theo [cai-dat.md](cai-dat.md) |
| `src/ingest/data/` | Dữ liệu raw bản v4 (`raw/comments.jsonl`, `raw/videos.jsonl`), `state.db` của crawler (có cả tên thật người bình luận), `models.json` | **Không**: đây là bản dữ liệu duy nhất trên máy; nếu xóa phải xin lại |
| `src/ingest/.env` | API key YouTube và `AUTHOR_SALT` của nhóm | **Không**, và không gửi cho ai ngoài nhóm: mất salt thì `author_hash` của lần crawl sau không khớp dữ liệu cũ |
| `data/processed/` | Đầu ra tầng 2 và manifest, do `src/processing/run.py` ghi | Được; chạy lại lệnh để tạo lại (bản phát hành chung thì giữ, xem [đặc tả tầng 2 mục 6](../2-tien-xu-ly/dac-ta.md#6-phiên-bản)) |
| `data/task9/` | Mệnh đề, nhãn LLM, model cảm xúc của Công việc 9 | Hỏi người làm Công việc 9 trước: nhãn LLM tốn hạn mức API để tạo lại |
| `data/external/`, `data/uit_visd4sa/` | Dataset ngoài đã chuẩn hóa (Công việc 5, 8) | Được; chạy lại `src/models/external_absa.py` |
| `data/aspect_mentions.jsonl`, `.comments.jsonl`, `.manifest.json` | Đầu ra bước suy luận | Được; chạy lại `python -m src.models.run` |
| `data/aggregates/` | Đầu ra tầng 5 | Được |
| `data/` (phần còn lại) | `comments.jsonl` cùng kích thước với bản v4 (có lẽ là bản sao), danh sách video đã crawl | Hỏi trưởng nhóm trước |
| `artifacts/**/*.pkl`, `*.joblib` | File model đã huấn luyện | Được; huấn luyện lại để tạo |
| `__pycache__/` | File Python tự sinh | Được, tự sinh lại |

## 4. Muốn làm việc này thì sửa ở đâu

| Muốn | Sửa ở | Rồi |
|---|---|---|
| Thêm cách gọi tên một máy ("táo", "s26u") | `aliases` của máy đó trong `config/pipeline.yaml` | Crawler dùng danh sách này để chọn video (chạy lại `discover`); bước suy luận dùng các tên **có chữ số** để nhận máy được nhắc (chạy lại `python -m src.run --tu suy_luan`) |
| Sửa `launch_date`, thêm máy, thêm đối thủ | `config/pipeline.yaml` (Công việc 2) | Dữ liệu đã crawl theo ngày cũ không tự đổi; xem `crawler/repair_labels.py` |
| Thêm kênh để crawl | Mục `channels` trong `config/pipeline.yaml` | Chạy `discover` rồi `crawl` |
| Kiểm tra một video đã crawl chưa | Tìm `video_id` trong `src/ingest/data/raw/videos.jsonl` | Không có thì đối chiếu 3 điều kiện chọn video ở [đặc tả thu thập mục 2](../1-thu-thap/dac-ta.md#2-chọn-video) |
| Đổi định dạng dữ liệu | `contracts/*.schema.json` + `src/ingest/crawler/schema.py`, tăng `schema_version` | Báo cả nhóm |
| Thêm, bỏ một viết tắt | `src/processing/resources/abbreviations.tsv` | Tăng `PIPELINE_VERSION`, chạy test, chạy lại lệnh tầng 2 ([hướng dẫn tầng 2 mục 5](../2-tien-xu-ly/huong-dan.md#5-sửa-từ-điển-hay-luật)) |
| Đổi kiểu dấu thanh, luật làm sạch, chuẩn hóa, tách mệnh đề | `clean.py`, `normalize.py`, `clauses.py` + đặc tả con tương ứng + test | Như trên |
| Sửa luật spam, nhận tiếng Việt | `src/processing/flags.py` + [dac-ta-gan-co.md](../2-tien-xu-ly/dac-ta-gan-co.md) + test | Tăng `PIPELINE_VERSION`, chạy lại cả chuỗi |
| Sửa từ khóa khía cạnh, luật cảm xúc, luật nhận máy, luật Q5 | `src/models/aspect/keywords.py`, `sentiment/rules.py`, `target_model.py`, `owner_defect.py` + [dac-ta-suy-luan.md](../4-mo-hinh/dac-ta-suy-luan.md) + `tests/test_models_run.py` | Đổi `MODEL_VERSION` trong `src/models/run.py`, chạy lại `python -m src.run --tu suy_luan` |
| Đổi bộ 4 máy cho phân tích | `config/analysis.yaml` | Chạy lại `python -m src.run --tu phan_tich` |
| Đổi quy tắc gán nhãn | [huong-dan-gan-nhan.md](../3-gan-nhan/huong-dan-gan-nhan.md), tăng `guideline_version` ở đầu file | File này được nhúng vào prompt của `llm_label.py`: nhãn LLM gán bằng bản cũ phải gán lại |

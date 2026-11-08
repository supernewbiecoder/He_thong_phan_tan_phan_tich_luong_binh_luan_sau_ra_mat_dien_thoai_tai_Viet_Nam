# Công việc 9, Giai đoạn 1: dữ liệu huấn luyện cảm xúc theo khía cạnh (nhãn LLM)

> Mục đích: từ `data/clean_data.jsonl` tạo bộ dữ liệu (mệnh đề, khía cạnh, cảm xúc) do LLM gán (Gemini hoặc NVIDIA, gói miễn phí), dùng huấn luyện mô hình cảm xúc; cập nhật lần cuối: 2026-11-04.

**Nhãn ở đây là nhãn LLM (`label_source = "llm"`), không phải gold.** Chỉ dùng để huấn luyện và validate nội bộ. Tập test phải do người gán (xem `docs/ml-training.md`).

## 1. Cấu trúc

```text
docs/labeling-guideline.md                     # quy tắc gán nhãn (v0.3, cần cả nhóm hiệu chỉnh 50 mệnh đề)
src/processing/task9/
├── extract_clauses.py         # Bước 2: clean_data.jsonl -> clauses.jsonl
├── llm_label.py               # Bước 3: clauses.jsonl    -> llm_labels*.jsonl   (Gemini / NVIDIA / Anthropic / OpenAI-compatible)
├── build_sentiment_dataset.py # Bước 4: llm_labels*.jsonl -> sentiment_{train,val,uncertain}.jsonl
├── train_baseline.py          # Bước 4b: huấn luyện baseline TF-IDF + Logistic Regression cho cảm xúc
├── review_sample.py           # Bước 5: người kiểm tra ~200 mẫu nhãn LLM (cả khía cạnh lẫn cảm xúc)
├── review_sentiment.py        # Bước 5b: 1 người kiểm tra ~120 cặp trên tập val; chấm nhãn LLM và mô hình so với người
├── eval_labels.py             # so hai file nhãn (vd Gemini với NVIDIA, hoặc LLM với nhãn người)
└── README.md
data/task9/                    # không commit dữ liệu và API key
```

## 2. Chuẩn bị (một lần)

**Cài thư viện** (trong terminal của VS Code, tại thư mục gốc repo):
```bash
pip install openai
```

**Lấy API key** (đều miễn phí, không cần thẻ; điều kiện và hạn mức có thể thay đổi, kiểm tra trên trang của họ):
- **Gemini:** vào Google AI Studio, tạo API key (`https://aistudio.google.com/apikey`). Xem hạn mức của bạn ở trang quota trong AI Studio.
- **NVIDIA:** vào `https://build.nvidia.com/settings/api-keys`, đăng nhập NVIDIA Developer Program, bấm Generate Key. Key bắt đầu bằng `nvapi-` và chỉ hiện một lần. Hạn mức nằm trong trang tài khoản.

**Đặt key thành biến môi trường** (không ghi key vào code, không commit):

| Hệ điều hành | Gemini | NVIDIA |
|---|---|---|
| Windows PowerShell (VS Code terminal) | `$env:GEMINI_API_KEY="AIza..."` | `$env:NVIDIA_API_KEY="nvapi-..."` |
| Linux / macOS | `export GEMINI_API_KEY="AIza..."` | `export NVIDIA_API_KEY="nvapi-..."` |

Lệnh trên chỉ có hiệu lực trong cửa sổ terminal đang mở; mở terminal mới thì đặt lại.

**Lưu ý dữ liệu:** gói miễn phí của Gemini có thể cho phép Google dùng nội dung gửi lên để cải thiện sản phẩm (kiểm tra điều khoản hiện hành). Dữ liệu của nhóm là bình luận YouTube công khai, `author_hash` đã băm; nên báo trưởng nhóm trước khi gửi lượng lớn.

## 3. Bước 2: trích xuất mệnh đề

```bash
python src/processing/task9/extract_clauses.py
```
Bỏ bình luận `is_spam = true`; mỗi phần tử `clauses` thành một dòng. `text_norm` là văn bản gán nhãn, `text` để đối chiếu, có `parent_text` nếu có. `clause_id = <comment_id>#<clause_idx>`.
`clause_idx` mặc định **1-based** (theo `clause_id` trong file nguồn). Nếu nhóm quy ước 0-based thì thêm `--index-base 0`.
Đầu ra: `data/task9/clauses.jsonl`, `data/task9/clauses_summary.json`.

## 4. Bước 3: gán nhãn bằng LLM

### 4a. Xem trước, chưa gọi API, chưa tốn hạn mức
```bash
python src/processing/task9/llm_label.py --provider gemini --model gemini-3.5-flash-lite --limit 200 --max-per-video 3 --dry-run
```

### 4b. Chạy thử 200 mệnh đề, đọc khoảng 50 dòng kết quả
```bash
# Gemini
python src/processing/task9/llm_label.py --provider gemini --model gemini-3.5-flash-lite \
    --limit 200 --max-per-video 3 --batch-size 20 --rpm 8 --output data/task9/llm_labels_gemini.jsonl

# NVIDIA
python src/processing/task9/llm_label.py --provider nvidia --model meta/llama-3.3-70b-instruct \
    --limit 200 --max-per-video 3 --batch-size 20 --rpm 20 --output data/task9/llm_labels_nvidia.jsonl
```
(Trên PowerShell, thay dấu `\` cuối dòng bằng dấu backtick `` ` `` hoặc viết lệnh trên một dòng.)
Đọc `llm_labels_*.jsonl` (hoặc `review_sample.py`, mục 6), chú ý mệnh đề có phủ định, mỉa mai, teencode, so sánh máy, câu hỏi. Nếu model gán sai lặp lại thì sửa guideline trước khi chạy lớn.

**Tên model Gemini:** Google đã giới hạn các model đời 2.5 cho tài khoản mới, nên dùng `gemini-3.5-flash-lite` hoặc `gemini-3.8-flash`. Nếu báo 404, liệt kê model key của bạn dùng được rồi dùng đúng tên trong danh sách.

**Chọn model:** chạy cùng `--limit`, `--max-per-video`, `--seed` cho cả hai provider, rồi so:
```bash
python src/processing/task9/eval_labels.py --pred data/task9/llm_labels_nvidia.jsonl --ref data/task9/llm_labels_gemini.jsonl
```
Độ khớp giữa hai model chỉ cho biết hai bên giống nhau đến đâu, không cho biết ai đúng; nên người kiểm tra mẫu (mục 6) quyết định cuối cùng. Cả bộ dữ liệu chính nên dùng **một** model để nhãn nhất quán.

### 4b'. Lặp lại cho đến khi nhãn ổn (guideline v0.2, v0.3)
Lần thử 200 mệnh đề đầu cho thấy Gemini hay **gán thừa khía cạnh** (từ đệm, tên người, tai nghe, từ khóa "game"). Guideline v0.2 đã thêm quy tắc "bằng chứng rõ ràng". Vòng lặp:
1. Chạy 200 mệnh đề với guideline hiện tại ra một file mới (`--output data/task9/llm_labels_v02.jsonl`).
2. Đọc, hoặc dùng `review_sample.py` để người kiểm tra; ghi lại kiểu sai lặp lại.
3. Sửa guideline, tăng `guideline_version`, đổi tên file đầu ra, chạy lại bước 1.
Chỉ chuyển sang 4c khi kiểu sai lớn đã hết và nhóm đã gán thử 50 mệnh đề thống nhất (yêu cầu của roadmap).

### 4c. Chạy lượng thật, mỗi ngày một ít

Dùng **một file đầu ra riêng** cho lượng thật, và chỉ dùng khi guideline đã chốt (nhóm hiệu chỉnh xong, `guideline_version` ghi ở đầu file guideline):
```bash
python src/processing/task9/llm_label.py --provider gemini --model gemini-3.5-flash-lite \
    --limit 3000 --max-per-video 3 --batch-size 30 --rpm 5 --output data/task9/llm_labels_gemini_main.jsonl
```
- `--limit` là số mệnh đề **mới** gán trong lần chạy này. Chạy lại đúng lệnh thì script tự bỏ qua mệnh đề đã gán và gán tiếp.
- Gói miễn phí giới hạn lượt gọi mỗi phút và mỗi ngày, nên dùng `--batch-size` 20 đến 40 (mỗi lượt gán nhiều mệnh đề) và `--rpm` thấp hơn hạn mức trong trang quota của bạn.
- Nếu hết hạn mức ngày, script dừng sau 5 batch lỗi liên tiếp (`--stop-after-failures`), in thông báo và thoát với mã 2. Hôm sau chạy lại đúng lệnh đó.
- **Ctrl+C** dừng an toàn: nhãn đã gán được giữ lại, lần chạy ghi vào `llm_run_meta.jsonl`; chạy lại đúng lệnh để tiếp tục.
- Muốn lấy nhiều hơn từ mỗi video, tăng `--max-per-video` (ví dụ 5) rồi chạy lại cùng `--output`.
- Đổi guideline, model hoặc prompt thì **không** ghi tiếp vào file cũ; dùng `--output` mới (script từ chối trộn).

**Bù khía cạnh hiếm.** Lấy ngẫu nhiên sẽ ít `BATTERY` và `WARRANTY` (200 mệnh đề đầu chỉ có 4 và 3 cặp). Chạy thêm vào **cùng file** với lọc từ khóa; script bỏ qua mệnh đề đã gán:
```bash
python src/processing/task9/llm_label.py --provider gemini --model gemini-3.5-flash-lite \
    --aspect-focus BATTERY,WARRANTY --limit 500 --max-per-video 5 --batch-size 30 --rpm 5 --output data/task9/llm_labels_gemini_main.jsonl
```
Số mệnh đề có từ khóa trong dữ liệu hiện tại: `BATTERY` khoảng 14.300, `WARRANTY` khoảng 4.400, `HARDWARE_OTHER` khoảng 9.400. Sau khi gán, xem `sentiment_stats.json` (mục 5) để biết ô nào còn thiếu rồi bù tiếp. Báo cáo phải ghi rõ phần dữ liệu lấy ngẫu nhiên và phần lấy theo từ khóa (`clauses_by_selection_filter` trong `sentiment_stats.json`, và trường `selection_filter` trong từng dòng nhãn).

### Tùy chọn của `llm_label.py`

| Tùy chọn | Ý nghĩa |
|---|---|
| `--provider` | `gemini`, `nvidia`, `anthropic`, hoặc `openai-compatible` (cần thêm `--base-url`, `--api-key-env`) |
| `--model` | tên model của provider; ghi vào `annotator` dạng `provider:model` |
| `--limit`, `--max-per-video`, `--seed` | lấy mẫu rải đều theo video, tái lập được. `--limit` là số mệnh đề **mới** gán trong lần chạy này; `--max-per-video` là **tổng** tối đa mỗi video trong file đầu ra (đã tính các lần chạy trước). Không đặt `--limit` thì gán cả 444.969 mệnh đề, nên luôn đặt |
| `--aspect-focus BATTERY,WARRANTY` | chỉ lấy mệnh đề có từ khóa của các khía cạnh đó (để bù khía cạnh hiếm). Mẫu lệch về mệnh đề có từ khóa nên **ghi rõ trong báo cáo**; lưu ở trường `selection_filter` |
| `--keyword-regex 'pin\|sạc'` | lọc theo regex tùy ý (không phân biệt hoa thường), dùng riêng hoặc cùng `--aspect-focus` |
| `--batch-size` (10), `--workers` (2), `--rpm` (0 = không giới hạn) | tốc độ; chỉnh theo hạn mức của gói miễn phí |
| `--retries` (2), `--stop-after-failures` (5) | độ bền và dừng sớm |
| `--max-tokens` (8000) | để lớn vì model "suy nghĩ" (Gemini) cũng tính vào đầu ra |
| `--reasoning-effort none` | tùy chọn: tắt "suy nghĩ" cho nhanh; bỏ đi nếu API báo lỗi 400 (không cần với Gemini 3.x) |
| `--json-mode` | gửi `response_format=json_object` nếu provider hỗ trợ (dùng khi hay gặp "JSON không hợp lệ") |
| `--no-system-role` | gộp system prompt vào tin nhắn user (một số model không nhận role system) |
| `--no-temperature` | không gửi `temperature` nếu model không hỗ trợ |
| `--output` | file đầu ra; mỗi model/provider dùng một file riêng |

### Đầu ra trong `data/task9/`
- `llm_labels*.jsonl`: mỗi dòng một mệnh đề; `annotations` là danh sách (rỗng nếu không có khía cạnh).
- `llm_labels_errors.jsonl`: mệnh đề model trả sai định dạng sau khi thử lại; lần chạy sau sẽ tự thử gán lại.
- `llm_run_meta.jsonl`: mỗi lần chạy một dòng gồm toàn văn prompt, provider, model, URL, tham số sinh, thời điểm, SHA-256 guideline và đầu vào, số token, thống kê nhãn, lý do dừng sớm (nếu có).

Script từ chối trộn nhãn của các model/prompt/guideline khác nhau trong cùng một file; dùng `--output` khác cho mỗi cấu hình.
`guideline_version` lấy từ dòng `guideline_version` đầu `labeling-guideline.md` (hiện `v0.3`). Sau khi cả nhóm hiệu chỉnh xong, đổi thành `v1` và gán lại phần đã gán bằng bản cũ.

### Gặp lỗi?

| Thông báo | Cách xử lý |
|---|---|
| `chưa đặt biến môi trường ...` | đặt key theo mục 2 trong cùng cửa sổ terminal |
| `HTTP 401/403` | key sai hoặc bị khóa; tạo key mới |
| `HTTP 404` | sai tên model; xem danh sách model trong AI Studio hoặc `build.nvidia.com/models` |
| `HTTP 400` | tham số không được hỗ trợ: thử `--no-temperature`, bỏ `--reasoning-effort`, hoặc thêm `--no-system-role` |
| chờ lâu, nhiều lần 429 | giảm `--rpm`, tăng `--batch-size`, giảm `--workers` |
| nhiều `JSON không hợp lệ` | thêm `--json-mode`, giảm `--batch-size`, tăng `--max-tokens` |
| `đã có nhãn từ cấu hình khác` | dùng `--output` khác cho model này |

## 5. Bước 4: làm phẳng thành dữ liệu huấn luyện

```bash
python src/processing/task9/build_sentiment_dataset.py --input data/task9/llm_labels_gemini_main.jsonl
# gộp nhiều file nhãn (cùng label_source = llm; cặp trùng thì lấy bản gặp đầu tiên):
python src/processing/task9/build_sentiment_dataset.py --input data/task9/llm_labels_gemini_main.jsonl data/task9/llm_labels_v03_seed7.jsonl
```
- Mỗi cặp (mệnh đề, khía cạnh) thành một dòng. Mệnh đề không có khía cạnh bị bỏ khỏi bộ cảm xúc nhưng vẫn nằm trong `llm_labels*.jsonl` để dùng cho mô hình khía cạnh (Công việc 8).
- Cặp `uncertain = true` tách ra `sentiment_uncertain.jsonl`, trừ khi có `--include-uncertain`.
- Chia train/val **theo `video_id`** bằng băm (`--val-frac`, mặc định 15% video), ổn định khi gán thêm dữ liệu; script kiểm tra không có video ở cả hai tập.
- `sentiment_stats.json` và bảng in ra cho biết phân bố khía cạnh × cảm xúc, cảnh báo khi một ô trong train ít hơn `--min-cell` (50) mẫu; gặp cảnh báo thì quay lại 4c tăng `--limit`.

Đầu ra: `sentiment_train.jsonl`, `sentiment_val.jsonl`, `sentiment_uncertain.jsonl`, `sentiment_stats.json`.

## 5b. Bước 4b: huấn luyện baseline cảm xúc (TF-IDF + Logistic Regression)

```bash
pip install scikit-learn joblib
python src/processing/task9/train_baseline.py --learning-curve
```
- `--learning-curve` huấn luyện thêm trên 25%, 50%, 75%, 100% số video của train để xem thêm dữ liệu có còn giúp không (đưa vào báo cáo).
- Đọc `sentiment_train.jsonl` và `sentiment_val.jsonl`; đầu vào là "mã khía cạnh + mệnh đề"; chọn tham số `C` bằng cross-validation gom nhóm theo `video_id` trên train (không đụng val).
- In macro-F1, F1 từng lớp, confusion matrix, macro-F1 theo khía cạnh, so với baseline "luôn đoán lớp đa số".
- Lưu `data/task9/model/model.joblib`, `metrics.json` và `val_errors.csv` (phân loại 20 đến 30 lỗi trong file này để làm phân tích lỗi trong báo cáo).
- **Điểm này đo độ khớp với nhãn LLM, không phải độ đúng thật.** Báo cáo cuối cùng phải đo trên tập test do người gán. Dữ liệu ít (dưới khoảng 1.000 cặp) thì điểm sẽ thấp và dao động mạnh; đừng kết luận gì từ đó.
- Dùng thử mô hình: `joblib.load("data/task9/model/model.joblib")["model"].predict(["ASP_BATTERY pin tụt nhanh quá"])`.

## 6. Bước 5: người kiểm tra chất lượng nhãn LLM (~200 mẫu)

```bash
python src/processing/task9/review_sample.py export --labels data/task9/llm_labels_gemini_main.jsonl --n 200 --blind
# Người kiểm tra mở data/task9/review_sample.csv, điền cột human_labels:
#   PERFORMANCE:neg;BATTERY:neg   |   NONE (không có khía cạnh)   |   để trống = chưa kiểm tra
python src/processing/task9/review_sample.py score --labels data/task9/llm_labels_gemini_main.jsonl
```
In tỷ lệ khớp hoàn toàn, precision/recall theo cặp và độ khớp cảm xúc; đưa con số này vào báo cáo. `--blind` ẩn nhãn LLM khỏi file CSV để người kiểm tra không bị ảnh hưởng.

## 6b. Khi nhóm không có người gán tập test: kiểm tra nhanh bằng 1 người

Nếu không có tập test do hai người gán (kappa), ước lượng sơ bộ độ đúng bằng **một** người xem khoảng 120 cặp trong tập **val** (video val không nằm trong train, nên chấm mô hình trên đó không rò rỉ):
```bash
python src/processing/task9/review_sentiment.py export --n 120      # -> data/task9/review_sentiment.csv
# Người kiểm tra điền aspect_ok (y/n) và human_sentiment (pos/neg/neu; chỉ khi aspect_ok = y), mất khoảng 30-40 phút
python src/processing/task9/review_sentiment.py score --model data/task9/model/model.joblib
```
In: tỷ lệ khía cạnh LLM gán đúng, độ đúng và macro-F1 cảm xúc của LLM so với người, và của mô hình so với người trên cùng các cặp. Ghi vào báo cáo: một người kiểm tra, số cặp, chưa có kappa, ước lượng sơ bộ. Lưu ý: lấy mẫu từ val nên mô hình huấn luyện chỉ trên train; nếu bạn huấn luyện lại trên cả train + val thì đừng dùng số này để báo cáo mô hình đó.

## 7. Quy tắc dùng bộ dữ liệu

- Train mô hình trên `sentiment_train.jsonl`; `sentiment_val.jsonl` chỉ để chọn mô hình và tham số.
- Báo cáo kết quả cuối cùng trên tập test do người gán (kappa ≥ 0,6), không báo cáo trên nhãn LLM.
- Mô hình cảm xúc nhận đầu vào (mệnh đề, khía cạnh), không chấm cả bình luận.
- Đổi guideline, prompt hoặc model thì tăng phiên bản và gán lại.
- Trong báo cáo ghi rõ: model nào gán nhãn, qua dịch vụ nào, ngày nào, `guideline_version` nào (có sẵn trong `llm_run_meta.jsonl`).

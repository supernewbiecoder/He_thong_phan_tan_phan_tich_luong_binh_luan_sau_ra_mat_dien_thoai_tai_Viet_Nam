## 1. Chuẩn bị đầu vào

| File từ thư mục gốc project | Nội dung cần có |
|---|---|
| `data/aspect_mentions.jsonl` | Nhãn khía cạnh, cảm xúc, máy được nhắc; thêm thông tin so sánh cho Q3 và chủ sở hữu/loại lỗi cho Q5. Phải đúng [contract v2](../../contracts/aspect-mention.schema.json). |
| `data/clean_data.jsonl` | Bình luận nguồn, mệnh đề gốc, ID, nguồn/video, thời gian, cờ spam và tiếng Việt để đối chiếu mention. |
| `config/pipeline.yaml` | Danh mục máy và ngày ra mắt. |
| [config/analysis.yaml](../../config/analysis.yaml) | Chọn X, đời trước, hai đối thủ và phiên bản nhãn cần phân tích. |

Các điểm cần kiểm tra trước khi chạy:

- Mention phải đủ trường theo contract, kể cả trường có giá trị `null`. `parent_id`, `author_hash`, `author_is_creator` phải khớp bình luận nguồn; không tự điền khi thiếu dữ liệu.
- `clause_idx` là vị trí trong mảng `clauses`, bắt đầu từ **0**; `clause_text` lấy từ `text` gốc. Không dùng `clause_id` hoặc `text_norm` thay thế.
- Cấu hình hiện tại: X=`s23u`, đời trước=`s22u`, đối thủ=`ip14prm` và `xiaomi13u`, phiên bản=`rule-v0`. Đổi phiên bản cho khớp dữ liệu bàn giao.

## 2. Cách chạy

Chạy PowerShell tại **thư mục gốc project**, dùng Python 3.10 trở lên. Nếu đã có `.venv`, bỏ lệnh tạo môi trường.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src/analysis/requirements.txt
$env:PYTHONDONTWRITEBYTECODE = '1'
```

**Chạy demo** bằng fixture có sẵn, không cần dữ liệu thật:

```powershell
.\.venv\Scripts\python.exe -m src.analysis.build_aggregates --demo
```

Kết quả ở `data/aggregates/demo/`. Kỳ vọng: **15 mention → 12 dòng aggregates**; X có 4 khen, 4 chê, 3 trung tính, tỷ lệ khen 50%, Net=0.

**Chạy dữ liệu thật** sau khi chuẩn bị đủ đầu vào và sửa cấu hình:

```powershell
.\.venv\Scripts\python.exe -m src.analysis.build_aggregates
```

Kết quả ở `data/aggregates/current/`. Mặc định bootstrap 1.000 lần, seed=42; có thể thêm `--bootstrap-resamples 5000 --seed 42`. Xem các tùy chọn đường dẫn bằng `--help`.

Exit 0 và `status: passed` nghĩa là xử lý/đối soát đạt, **chưa đồng nghĩa được phép kết luận**. Exit 2: đọc lỗi JSON, sửa đầu vào rồi chạy lại; output cũ không đại diện cho lần chạy lỗi. Chạy thành công sẽ thay kết quả, không cộng dồn.

## 3. Các file kết quả

Mỗi lần chạy thành công giữ **3 file**; validation tạm và các bảng đếm phụ được xử lý nội bộ.

| File | Mục đích |
|---|---|
| `aggregates.jsonl` | Số đếm theo máy × khía cạnh × tuần × video × nguồn × phiên bản. |
| `business_questions.json` | `answers.Q1`–`answers.Q5` tóm tắt câu trả lời; `q1`, `q2`, `q3a`, `q3b`, `q4`, `q5` chứa số liệu, CI, p-value và điều kiện kết luận. |
| `aggregation_manifest.json` | Cấu hình, phiên bản, seed, checksum; báo cáo kiểm tra đầu vào trong `validation`, đối soát số đếm trong `aggregation_report`. |

## 4. Cách tính aggregates và Q1–Q5

Đơn vị đếm là **mệnh đề × khía cạnh**, không phải số người hay bình luận. Một mệnh đề nói về pin và camera có thể tạo 2 mention; mỗi mention được đếm 1 lần.

```text
n_total = n_pos + n_neg + n_neu
% khen  = 100 × n_pos / (n_pos + n_neg)
% chê   = 100 × n_neg / (n_pos + n_neg)
Net     = 100 × (n_pos − n_neg) / (n_pos + n_neg)
```

Gộp video bằng cách **cộng tử số và mẫu số rồi chia**. Mẫu số bằng 0 trả `null`.

| Câu hỏi | Cách tính |
|---|---|
| **Q1. X được đón nhận tốt hay dở?** | % khen/chê và Net tổng thể, theo tuần. Kiểm định % khen X so với 50% và so với từng máy còn lại. |
| **Q2. Ưu điểm, nhược điểm của X?** | `% chê khía cạnh − % chê chung X`. Dương có ý nghĩa: nhược điểm tương đối; âm có ý nghĩa: ưu điểm tương đối. |
| **Q3. So với đối thủ, X mạnh/yếu ở đâu?** | Q3a: so % khen theo khía cạnh giữa 4 máy, kiểm định tổng thể rồi so từng cặp với X. Q3b: `100 × X thắng / (X thắng + X thua)`, kiểm định so với 50%; hòa báo riêng. |
| **Q4. Đời này đã sửa điểm bị chê của đời trước chưa?** | `% chê đời trước − % chê X` theo khía cạnh. Dương có ý nghĩa: cải thiện; âm có ý nghĩa: tệ hơn. |
| **Q5. Lỗi nào cần sửa, ưu tiên cái nào?** | Tỷ lệ lỗi = `100 × mention owner=true, neg, đúng loại lỗi / mọi mention hợp lệ về X`. So tỷ lệ gộp tuần 3–4 với tuần 1–2. |

Q5 xếp **P1** khi ≥20 lượt nhắc lỗi và tăng có ý nghĩa; **P2** khi ≥20, kiểm định được nhưng chưa có bằng chứng tăng (gồm cả giảm có ý nghĩa); **P3** khi <20. Nếu ≥20 nhưng không kiểm định được thì chưa xếp ưu tiên. `priority_candidate` là gợi ý; `priority` chỉ có khi nhãn đủ điều kiện. Đây là tỷ lệ lượt nhắc lỗi, không phải tỷ lệ máy bị hỏng.

## 5. Điều kiện kết luận

- **CI 95%:** bootstrap theo cụm `(source, video_id)`, giữ các mention cùng video trong một cụm. CI dùng phân vị, là CI riêng từng chỉ số.
- **Kiểm định:** bootstrap-t theo cụm; Q3a tổng thể dùng Wald bootstrap. Hiệu chỉnh **Holm riêng từng câu hỏi**: Q1=4, Q2=9, Q3=45, Q4=9, Q5=9 phép dự kiến.
- **Đủ dữ liệu:** mỗi tỷ lệ cần mẫu số ≥30, ít nhất 20 video đóng góp và 20 video hiệu dụng. Thiếu mẫu hoặc bootstrap suy biến/không ổn định thì CI/p-value là `null`, kèm lý do.
- **Được kết luận:** kiểm định hợp lệ, `p_adjusted < 0.05`, nhãn đã được đánh giá và `conclusion_allowed=true`. Q3a so cặp còn phải qua kiểm định tổng thể. Demo và nhãn baseline luật chưa đủ điều kiện công bố.
- Trong `business_questions.json`, đọc `answers`, `publication_blockers` và `reasons`. Không có ý nghĩa thống kê chỉ cho phép viết **“chưa đủ bằng chứng”**, không suy ra các máy bằng nhau. Khi có kết luận, báo ước lượng/chênh lệch + CI 95% + p sau Holm + cỡ mẫu/video; duyệt bình luận mẫu trước khi trích dẫn.

Chi tiết đặc tả: [EDA_requirement.md](../../docs/EDA_requirement.md).

## 6. Code và kiểm tra

| File | Vai trò |
|---|---|
| [build_aggregates.py](build_aggregates.py) | Điểm chạy toàn bộ luồng, ghi 3 file kết quả. |
| [validation.py](validation.py), [validate_inputs.py](validate_inputs.py) | Kiểm tra đầu vào; đọc/ghi và CLI chẩn đoán validation. |
| [aggregation.py](aggregation.py) | Nhóm, đếm và đối soát aggregates. |
| [questions.py](questions.py) | Tính Q1–Q5, CI, Holm và điều kiện kết luận. |
| [tests](../../tests/) và [fixtures](../../tests/fixtures/) | Kiểm tra input đúng/sai, số đếm, thống kê, xuất file; fixture cũng là đầu vào demo nên cần giữ. |

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_analysis_validation.py tests/test_analysis_aggregation.py tests/test_analysis_questions.py -q
```

Đạt khi tất cả test pass; số đếm demo khớp mục 2.

## 7. Kết quả chạy

Pipeline trả `status: passed`: **15 mention → 12 dòng aggregates**, 4 cụm nguồn/video; mọi đối soát đều đạt. Toàn mẫu có 5 khen, 6 chê và 4 trung tính.

### 7.1. Aggregates tổng hợp và Q1: X được đón nhận tốt hay dở?

| Máy | Tổng mention | Khen | Chê | Trung tính | % khen | % chê | Net |
|---|---:|---:|---:|---:|---:|---:|---:|
| Galaxy S23 Ultra (X) | 11 | 4 | 4 | 3 | 50,00 | 50,00 | 0,00 |
| Galaxy S22 Ultra | 1 | 0 | 1 | 0 | 0,00 | 100,00 | -100,00 |
| iPhone 14 Pro Max | 2 | 1 | 1 | 0 | 50,00 | 50,00 | 0,00 |
| Xiaomi 13 Ultra | 1 | 0 | 0 | 1 | `null` | `null` | `null` |

X có tỷ lệ khen 50%, Net=0 trong mẫu. Đây là số liệu mô tả; chưa đủ bằng chứng kết luận X được đón nhận tốt hay dở.

| Tuần của X | Tổng mention | Khen | Chê | Trung tính | % khen | Net |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 5 | 3 | 1 | 1 | 75,00 | 50,00 |
| 2 | 4 | 1 | 1 | 2 | 50,00 | 0,00 |
| 3 | 1 | 0 | 1 | 0 | 0,00 | -100,00 |
| 4 | 1 | 0 | 1 | 0 | 0,00 | -100,00 |

### 7.2. Q2: Ưu điểm, nhược điểm của X?

| Khía cạnh | Khen | Chê | Trung tính | % chê | Chênh so với % chê chung X (điểm %) |
|---|---:|---:|---:|---:|---:|
| Pin | 2 | 1 | 1 | 33,33 | -16,67 |
| Camera | 1 | 1 | 1 | 50,00 | 0,00 |
| Hiệu năng | 1 | 1 | 1 | 50,00 | 0,00 |
| Phần mềm | 0 | 1 | 0 | 100,00 | +50,00 |

Các khía cạnh còn lại không có mention trong demo. Chênh lệch ở pin/phần mềm chưa được kiểm định, nên chưa xác nhận ưu điểm hay nhược điểm.

### 7.3. Q3: So với đối thủ, X mạnh/yếu ở đâu?

**Q3a:** % khen camera của S23U là 50% (1/2), S22U là 0% (0/1), iPhone 14 Pro Max là 50% (1/2). Xiaomi 13 Ultra chỉ có 1 mention trung tính nên tỷ lệ là `null`. Các máy còn lại chưa có dữ liệu khía cạnh pin, hiệu năng, phần mềm để đối chiếu với X.

**Q3b — mệnh đề so sánh trực tiếp, quy chiều thắng/thua về X:**

| Khía cạnh | X thắng | X thua | Hòa | % thắng, bỏ hòa |
|---|---:|---:|---:|---:|
| Camera | 1 | 2 | 0 | 33,33 |
| Hiệu năng | 1 | 0 | 1 | 100,00 |

Mẫu so sánh quá nhỏ; chưa kết luận X mạnh/yếu hơn đối thủ ở khía cạnh nào.

### 7.4. Q4: Đời trước bị chê gì, đời này đã sửa chưa?

Camera: S22U có % chê **100,00%** (1/1), S23U **50,00%** (1/2); chênh đời trước − X là **+50,00 điểm %**. Các khía cạnh khác thiếu dữ liệu đời trước. Chưa đủ bằng chứng thống kê để nói đời này đã sửa được vấn đề.

### 7.5. Q5: Lỗi gì cần sửa, ưu tiên cái nào?

Có **4 lượt nhắc lỗi từ owner**, mẫu số là **11 mention về X**. Mẫu số tuần 1–4 lần lượt là 5, 4, 1, 1; gộp tuần 1–2 là 9 và tuần 3–4 là 2.

| Loại lỗi | Lượt nhắc | % tuần 1–2 | % tuần 3–4 | Chênh cuối − đầu (điểm %) |
|---|---:|---:|---:|---:|
| Hao pin (`BATTERY_DRAIN`) | 1 | 11,11 | 0,00 | -11,11 |
| Nóng máy (`OVERHEAT`) | 1 | 11,11 | 0,00 | -11,11 |
| Lỗi camera (`CAMERA_DEFECT`) | 1 | 0,00 | 50,00 | +50,00 |
| Lỗi phần mềm (`SOFTWARE_BUG`) | 1 | 0,00 | 50,00 | +50,00 |

Năm loại lỗi còn lại có 0 lượt trong demo. Các loại lỗi đều có `priority_candidate=P3` do <20 lượt, nhưng **`priority=null`** vì nhãn chưa đủ điều kiện; chưa công bố thứ tự ưu tiên hay kết luận lỗi tăng/giảm.

### 7.6. CI, kiểm định và kết luận dùng báo cáo

**Q1–Q5 đều có trạng thái `insufficient_data`.** CI 95%, `p_value` và `p_adjusted` đều là `null`; chưa thực hiện được phép nào trong 76 phép kiểm định dự kiến. Vì vậy chưa có p-value hợp lệ để hiệu chỉnh Holm. Mẫu chỉ có 4 cụm nguồn/video, dưới ngưỡng suy luận ở mục 5; thêm giới hạn dữ liệu nhân tạo, nhãn luật và chất lượng nhãn chưa được xác nhận.

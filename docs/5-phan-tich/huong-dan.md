# Hướng dẫn tầng 5: tính aggregates và trả lời Q1–Q5

> Mục đích: Cách chuẩn bị đầu vào, chạy, đọc kết quả và điều kiện kết luận của Công việc 12 (`src/analysis/`); cập nhật lần cuối: 2026-11-26.

Đặc tả các câu hỏi và quy ước thống kê: [muc-tieu.md](../0-chung/muc-tieu.md) mục 5–6. Viết bởi người làm Công việc 12; trưởng nhóm chỉ thêm tiêu đề này khi chuyển file từ `src/analysis/README.md` sang (19/11), và ngày 20/11 sửa dòng file bình luận ở mục 1 theo bước suy luận mới. Ngày 26/11 (Nguyễn Lê Quân) sửa theo contract v3 và bộ nhãn chốt: mã khía cạnh, thái độ, `n_cmp`, Q5 theo khía cạnh, bootstrap mặc định 2.000 lần, chạy lại demo ở mục 7.

## 1. Chuẩn bị đầu vào

| File từ thư mục gốc project | Nội dung cần có |
|---|---|
| `data/aspect_mentions.jsonl` | Nhãn chiều 2 (11 khía cạnh của [bộ nhãn chốt](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611) và `may_chung`, `hang_nguoi_dung`, `khac`), thái độ, máy được nhắc; thông tin so sánh cho Q3 và đã dùng máy cho Q5. Phải đúng [contract v3](../../contracts/aspect-mention.schema.json) (`defect_type` luôn `null`). |
| `data/aspect_mentions.comments.jsonl` (từ 20/11; trước đó là `data/clean_data.jsonl`) | Bình luận nguồn, mệnh đề gốc, ID, nguồn/video, thời gian, cờ spam và tiếng Việt để đối chiếu mention. Bước suy luận ghi ra, chỉ gồm bình luận có mention ([dac-ta-suy-luan.md mục 1](../4-mo-hinh/dac-ta-suy-luan.md#1-vị-trí-trong-chuỗi-đầu-vào-đầu-ra)). Lệnh `python -m src.run` tự truyền đường dẫn này cùng `--mentions` và `--model-version`. |
| `config/pipeline.yaml` | Danh mục máy và ngày ra mắt. |
| [config/analysis.yaml](../../config/analysis.yaml) | Chọn X, đời trước, hai đối thủ và phiên bản nhãn cần phân tích. |

Các điểm cần kiểm tra trước khi chạy:

- Mention phải đủ trường theo contract, kể cả trường có giá trị `null`. `parent_id`, `author_hash`, `author_is_creator` phải khớp bình luận nguồn; không tự điền khi thiếu dữ liệu.
- `clause_idx` là vị trí trong mảng `clauses`, bắt đầu từ **0**; `clause_text` lấy từ `text` gốc. Không dùng `clause_id` hoặc `text_norm` thay thế.
- Cấu hình hiện tại: X=`s23u`, đời trước=`s22u`, đối thủ=`ip14prm` và `xiaomi13u`, phiên bản=`rule-v0` (chỉ dùng cho `--demo` và test; `python -m src.run` luôn truyền `--model-version` bằng phiên bản suy luận, hiện `rule-v1.1`).

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

Kết quả ở `data/aggregates/demo/`. Kỳ vọng: **15 mention → 12 dòng aggregates**; X có 3 khen, 3 chê, 2 không đánh giá, 3 so sánh, tỷ lệ khen 50%, Net=0.

**Chạy dữ liệu thật** sau khi chuẩn bị đủ đầu vào và sửa cấu hình:

```powershell
.\.venv\Scripts\python.exe -m src.analysis.build_aggregates
```

Kết quả ở `data/aggregates/current/`. Mặc định bootstrap **2.000** lần, seed=42; có thể thêm `--bootstrap-resamples 5000 --seed 42`. Không dùng dưới 2.000: p nhỏ nhất của bootstrap là 1/(B+1), Holm nhân nó với số phép của câu hỏi; Q3 có 55 phép (11 khía cạnh), nên với B=1.000 thì 55/1.001 > 0,05 và không phép Q3 nào có thể có ý nghĩa. Xem các tùy chọn đường dẫn bằng `--help`.

Exit 0 và `status: passed` nghĩa là xử lý/đối soát đạt, **chưa đồng nghĩa được phép kết luận**. Exit 2: đọc lỗi JSON, sửa đầu vào rồi chạy lại; output cũ không đại diện cho lần chạy lỗi. Chạy thành công sẽ thay kết quả, không cộng dồn.

## 3. Các file kết quả

Mỗi lần chạy thành công giữ **3 file**; validation tạm và các bảng đếm phụ được xử lý nội bộ.

| File | Mục đích |
|---|---|
| `aggregates.jsonl` | Số đếm theo máy × khía cạnh × tuần × video × nguồn × phiên bản: `n_pos` (`tich_cuc`), `n_neg` (`tieu_cuc`), `n_neu` (`khong_danh_gia`), `n_cmp` (`so_sanh`). |
| `business_questions.json` | `answers.Q1`–`answers.Q5` tóm tắt câu trả lời; `q1`, `q2`, `q3a`, `q3b`, `q4`, `q5` chứa số liệu, CI, p-value và điều kiện kết luận. |
| `aggregation_manifest.json` | Cấu hình, phiên bản, seed, checksum; báo cáo kiểm tra đầu vào trong `validation`, đối soát số đếm trong `aggregation_report`. |

## 4. Cách tính aggregates và Q1–Q5

Đơn vị đếm là **(bình luận, máy, nhãn chiều 2)** (phương án A), không phải số người. Một bình luận nói về pin và camera tạo 2 mention; mỗi mention được đếm 1 lần.

```text
n_total = n_pos + n_neg + n_neu + n_cmp
% khen  = 100 × n_pos / (n_pos + n_neg)
% chê   = 100 × n_neg / (n_pos + n_neg)
Net     = 100 × (n_pos − n_neg) / (n_pos + n_neg)
```

Gộp video bằng cách **cộng tử số và mẫu số rồi chia**. Mẫu số bằng 0 trả `null`.

| Câu hỏi | Cách tính |
|---|---|
| **Q1. X được đón nhận tốt hay dở?** | % khen/chê và Net tổng thể, theo tuần. Kiểm định % khen X so với 50% và so với từng máy còn lại. |
| **Q2. Ưu điểm, nhược điểm của X?** | Với từng khía cạnh trong 11 khía cạnh: `% chê khía cạnh − % chê chung X`. Dương có ý nghĩa: nhược điểm tương đối; âm có ý nghĩa: ưu điểm tương đối. |
| **Q3. So với đối thủ, X mạnh/yếu ở đâu?** | Q3a: so % khen theo khía cạnh giữa 4 máy, kiểm định tổng thể rồi so từng cặp với X. Q3b: `100 × X thắng / (X thắng + X thua)`, kiểm định so với 50%; hòa báo riêng. |
| **Q4. Đời này đã sửa điểm bị chê của đời trước chưa?** | `% chê đời trước − % chê X` theo khía cạnh. Dương có ý nghĩa: cải thiện; âm có ý nghĩa: tệ hơn. |
| **Q5. Lỗi nào cần sửa, ưu tiên cái nào?** | Theo khía cạnh (bộ loại lỗi chưa chốt): `100 × mention về khía cạnh đó có is_owner=true, tieu_cuc / mọi mention hợp lệ về X`. So tỷ lệ gộp tuần 3–4 với tuần 1–2. Bảng `q5_defects` có cột `aspect`, `n_defect` là số lời chê đó. |

Q5 xếp **P1** khi ≥20 lượt nhắc lỗi và tăng có ý nghĩa; **P2** khi ≥20, kiểm định được nhưng chưa có bằng chứng tăng (gồm cả giảm có ý nghĩa); **P3** khi <20. Nếu ≥20 nhưng không kiểm định được thì chưa xếp ưu tiên. `priority_candidate` là gợi ý; `priority` chỉ có khi nhãn đủ điều kiện. Đây là tỷ lệ lượt nhắc lỗi, không phải tỷ lệ máy bị hỏng.

## 5. Điều kiện kết luận

- **CI 95%:** bootstrap theo cụm `(source, video_id)`, giữ các mention cùng video trong một cụm. CI dùng phân vị, là CI riêng từng chỉ số.
- **Kiểm định:** bootstrap-t theo cụm; Q3a tổng thể dùng Wald bootstrap. Hiệu chỉnh **Holm riêng từng câu hỏi**: Q1=4, Q2=11, Q3=55, Q4=11, Q5=11 phép dự kiến.
- **Đủ dữ liệu:** mỗi tỷ lệ cần mẫu số ≥30, ít nhất 20 video đóng góp và 20 video hiệu dụng. Thiếu mẫu hoặc bootstrap suy biến/không ổn định thì CI/p-value là `null`, kèm lý do.
- **Được kết luận:** kiểm định hợp lệ, `p_adjusted < 0.05`, nhãn đã được đánh giá và `conclusion_allowed=true`. Q3a so cặp còn phải qua kiểm định tổng thể. Demo và nhãn baseline luật chưa đủ điều kiện công bố.
- Trong `business_questions.json`, đọc `answers`, `publication_blockers` và `reasons`. Không có ý nghĩa thống kê chỉ cho phép viết **“chưa đủ bằng chứng”**, không suy ra các máy bằng nhau. Khi có kết luận, báo ước lượng/chênh lệch + CI 95% + p sau Holm + cỡ mẫu/video; duyệt bình luận mẫu trước khi trích dẫn.

Chi tiết đặc tả: [muc-tieu.md](../0-chung/muc-tieu.md).

## 6. Code và kiểm tra

| File | Vai trò |
|---|---|
| [build_aggregates.py](../../src/analysis/build_aggregates.py) | Điểm chạy toàn bộ luồng, ghi 3 file kết quả. |
| [validation.py](../../src/analysis/validation.py), [validate_inputs.py](../../src/analysis/validate_inputs.py) | Kiểm tra đầu vào; đọc/ghi và CLI chẩn đoán validation. |
| [aggregation.py](../../src/analysis/aggregation.py) | Nhóm, đếm và đối soát aggregates. |
| [questions.py](../../src/analysis/questions.py) | Tính Q1–Q5, CI, Holm và điều kiện kết luận. |
| [tests](../../tests) và [fixtures](../../tests/fixtures) | Kiểm tra input đúng/sai, số đếm, thống kê, xuất file; fixture cũng là đầu vào demo nên cần giữ. |

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_analysis_validation.py tests/test_analysis_aggregation.py tests/test_analysis_questions.py -q
```

Đạt khi tất cả test pass; số đếm demo khớp mục 2.

## 7. Kết quả chạy

Demo (`--demo`) chạy lại ngày 26/11 với fixture theo contract v3. Pipeline trả `status: passed`: **15 mention → 12 dòng aggregates**, 4 cụm nguồn/video; mọi đối soát đều đạt. Toàn mẫu có 3 khen, 4 chê, 3 không đánh giá và 5 so sánh (5 mention có `compare_with`, nay mang thái độ `so_sanh` nên không vào % khen, % chê).

### 7.1. Aggregates tổng hợp và Q1: X được đón nhận tốt hay dở?

| Máy | Tổng mention | Khen | Chê | Không đánh giá | So sánh | % khen | % chê | Net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Galaxy S23 Ultra (X) | 11 | 3 | 3 | 2 | 3 | 50,00 | 50,00 | 0,00 |
| Galaxy S22 Ultra | 1 | 0 | 1 | 0 | 0 | 0,00 | 100,00 | -100,00 |
| iPhone 14 Pro Max | 2 | 0 | 0 | 0 | 2 | `null` | `null` | `null` |
| Xiaomi 13 Ultra | 1 | 0 | 0 | 1 | 0 | `null` | `null` | `null` |

X có tỷ lệ khen 50%, Net=0 trong mẫu. Đây là số liệu mô tả; chưa đủ bằng chứng kết luận X được đón nhận tốt hay dở.

| Tuần của X | Tổng mention | Khen | Chê | Không đánh giá | So sánh | % khen | Net |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5 | 2 | 1 | 1 | 1 | 66,67 | 33,33 |
| 2 | 4 | 1 | 1 | 1 | 1 | 50,00 | 0,00 |
| 3 | 1 | 0 | 0 | 0 | 1 | `null` | `null` |
| 4 | 1 | 0 | 1 | 0 | 0 | 0,00 | -100,00 |

### 7.2. Q2: Ưu điểm, nhược điểm của X?

% chê chung của X là 50,00% (3/6).

| Khía cạnh | Khen | Chê | Không đánh giá | So sánh | % chê | Chênh so với % chê chung X (điểm %) |
|---|---:|---:|---:|---:|---:|---:|
| Pin & sạc (`pin_sac`) | 2 | 1 | 1 | 0 | 33,33 | -16,67 |
| Camera (`camera`) | 1 | 0 | 1 | 1 | 0,00 | -50,00 |
| Hiệu năng (`hieu_nang`) | 0 | 1 | 0 | 2 | 100,00 | +50,00 |
| Phần mềm (`phan_mem`) | 0 | 1 | 0 | 0 | 100,00 | +50,00 |

Các khía cạnh còn lại không có mention trong demo. Các chênh lệch chưa được kiểm định, nên chưa xác nhận ưu điểm hay nhược điểm.

### 7.3. Q3: So với đối thủ, X mạnh/yếu ở đâu?

**Q3a:** % khen camera của S23U là 100% (1/1), S22U là 0% (0/1). iPhone 14 Pro Max chỉ có mention so sánh, Xiaomi 13 Ultra chỉ có 1 mention không đánh giá, nên tỷ lệ là `null`. Các máy còn lại chưa có dữ liệu khía cạnh pin, hiệu năng, phần mềm để đối chiếu với X.

**Q3b, mention so sánh trực tiếp, quy chiều thắng/thua về X:**

| Khía cạnh | X thắng | X thua | Hòa | % thắng, bỏ hòa |
|---|---:|---:|---:|---:|
| Camera | 1 | 2 | 0 | 33,33 |
| Hiệu năng | 1 | 0 | 1 | 100,00 |

Mẫu so sánh quá nhỏ; chưa kết luận X mạnh/yếu hơn đối thủ ở khía cạnh nào.

### 7.4. Q4: Đời trước bị chê gì, đời này đã sửa chưa?

Camera: S22U có % chê **100,00%** (1/1), S23U **0,00%** (0/1); chênh đời trước − X là **+100,00 điểm %**. Các khía cạnh khác thiếu dữ liệu đời trước. Chưa đủ bằng chứng thống kê để nói đời này đã sửa được vấn đề.

### 7.5. Q5: Lỗi gì cần sửa, ưu tiên cái nào?

Có **3 lời chê của người đã dùng máy** (`is_owner = true`, `tieu_cuc`), mẫu số là **11 mention về X**. Mẫu số tuần 1–4 lần lượt là 5, 4, 1, 1; gộp tuần 1–2 là 9 và tuần 3–4 là 2.

| Khía cạnh | Lượt nhắc | % tuần 1–2 | % tuần 3–4 | Chênh cuối − đầu (điểm %) |
|---|---:|---:|---:|---:|
| Pin & sạc (`pin_sac`) | 1 | 11,11 | 0,00 | -11,11 |
| Hiệu năng (`hieu_nang`) | 1 | 11,11 | 0,00 | -11,11 |
| Phần mềm (`phan_mem`) | 1 | 0,00 | 50,00 | +50,00 |

Tám khía cạnh còn lại có 0 lượt trong demo. Các dòng đều có `priority_candidate=P3` do <20 lượt, nhưng **`priority=null`** vì nhãn chưa đủ điều kiện; chưa công bố thứ tự ưu tiên hay kết luận tăng/giảm. (Bản demo v2 có 4 lượt: một mention so sánh từng mang nhãn chê và loại lỗi; ở v3 nó là `so_sanh`.)

### 7.6. CI, kiểm định và kết luận dùng báo cáo

**Q1–Q5 đều có trạng thái `insufficient_data`.** CI 95%, `p_value` và `p_adjusted` đều là `null`; chưa thực hiện được phép nào trong 92 phép kiểm định dự kiến. Vì vậy chưa có p-value hợp lệ để hiệu chỉnh Holm. Mẫu chỉ có 4 cụm nguồn/video, dưới ngưỡng suy luận ở mục 5; thêm giới hạn dữ liệu nhân tạo, nhãn luật và chất lượng nhãn chưa được xác nhận.

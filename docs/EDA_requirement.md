# Đặc tả phân tích: 5 câu hỏi nghiệp vụ

> Mục đích: Định nghĩa thống nhất cách tính, biểu đồ, kiểm định và điều kiện kết luận cho Q1–Q5; cập nhật lần cuối: 2026-10-28.

**Bối cảnh:** công ty vừa ra mắt máy X và muốn biết X có ưu, nhược điểm gì, so với các dòng khác thì thế nào.

## 1. Quy ước chung

### 1.1 Phạm vi

- **Bốn máy:** X (máy chính), P (đời trước của X), R1 và R2 (đối thủ cùng phân khúc, ra mắt cùng thời điểm). Danh sách chốt ở Công việc 2. Bản nháp dashboard đang dùng X = Galaxy S23 Ultra, P = Galaxy S22 Ultra, R1 = iPhone 14 Pro Max, R2 = Xiaomi 13 Ultra.
- **Cửa sổ:** 4 tuần đầu kể từ `launch_date` của **từng máy** (ngày 0 khác nhau, giai đoạn so sánh như nhau). Muốn đổi sang 8 tuần phải crawl lại vì dữ liệu hiện có được thu với `window_weeks: 4`.

### 1.2 Thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| Aspect (khía cạnh) | Một trong 9 nhóm chủ đề, mã trong [data-model.md](data-model.md#danh-mục-mã) |
| Sentiment | `pos` (khen), `neg` (chê), `neu` (trung tính) |
| Model | Dòng máy, mã như `s23u`, `ip14prm` |
| Brand | Hãng |
| Mention | Một dòng `aspect_mentions` = một cặp (mệnh đề, khía cạnh) |

### 1.3 Đơn vị đếm

Mọi câu hỏi đếm trên `aspect_mentions`, chỉ lấy dòng:
- `target_model` thuộc 4 máy trong phạm vi (máy **được nhắc trong mệnh đề**, không phải máy của video);
- `days_since_launch` nằm trong cửa sổ;
- bình luận gốc không bị đánh dấu spam;
- `model_version` là phiên bản mô hình đã chốt cho báo cáo.

### 1.4 Công thức dùng cho mọi câu

```
% khen = pos / (pos + neg)        trung tính không vào mẫu số
% chê  = neg / (pos + neg)
Net    = % khen − % chê           từ −100 đến +100
```

Chỉ dùng **một** định nghĩa này. Số mệnh đề trung tính vẫn báo cáo kèm nhưng không vào mẫu số.

### 1.5 Ngưỡng tối thiểu

Ô nào có `pos + neg < 30` thì hiển thị mờ, ghi "ít dữ liệu", không kết luận.

### 1.6 Thống kê

- **Khoảng tin cậy 95%** cho mọi tỷ lệ, tính bằng **bootstrap theo video**: rút có hoàn lại các `video_id`, tính lại chỉ số, lặp 1.000 lần, lấy phân vị 2,5% và 97,5%. Lý do: các mệnh đề cùng video/tác giả không độc lập, công thức thông thường cho khoảng quá hẹp.
- **Hiệu chỉnh đa so sánh:** Holm, áp dụng riêng cho từng câu hỏi (các phép kiểm định của một câu là một nhóm).
- **Mức ý nghĩa:** α = 0,05 sau hiệu chỉnh.
- **Cách viết kết luận:** có ý nghĩa → "X tốt hơn/kém hơn…"; không có ý nghĩa → "chưa đủ bằng chứng", **không** viết "bằng nhau".
- **Không dùng** ngoại suy/dự báo từ vài điểm dữ liệu.

## 2. Năm câu hỏi

### Q1. X được đón nhận tốt hay dở?

| | |
|---|---|
| **Ý nghĩa** | Nhìn tổng thể người dùng khen hay chê X nhiều hơn, so với P, R1, R2, và thay đổi qua từng tuần |
| **Số liệu** | Net theo (máy, tuần kể từ ra mắt), gộp mọi khía cạnh. Nguồn: `aggregates` |
| **Biểu đồ** | Đường theo tuần 1–4, mỗi máy một đường, dải mờ = khoảng tin cậy. Kèm bảng Net tổng cả cửa sổ |
| **Kiểm định** | z-test hai tỷ lệ cho % khen tổng: X vs P, X vs R1, X vs R2 (3 phép, Holm) |
| **Kết luận được phép** | "X được đón nhận tốt/kém hơn R1" chỉ khi có ý nghĩa |

### Q2. Ưu điểm và nhược điểm của X là gì?

| | |
|---|---|
| **Ý nghĩa** | Trong các khía cạnh của X, cái nào được khen nhiều (ưu), cái nào bị chê nhiều (nhược). Chỉ xét X |
| **Số liệu** | % khen, % chê, n theo khía cạnh, `target_model = X`. Nguồn: `aggregates` |
| **Biểu đồ** | Thanh hai chiều: chê sang trái màu đỏ, khen sang phải màu xanh, sắp theo Net |
| **Bình luận mẫu** | 2–3 bình luận/khía cạnh từ `aspect_mentions` (`target_model = X`, `confidence` cao). **Phải có người duyệt** trước khi đưa vào báo cáo |
| **Kiểm định** | Mỗi khía cạnh: % chê có khác % chê chung của X không (kiểm định nhị thức; 9 phép, Holm) |
| **Kết luận được phép** | Nhược điểm = % chê cao hơn mức chung của X có ý nghĩa; ưu điểm thì ngược lại |

### Q3. So với đối thủ, X mạnh/yếu ở đâu?

**3a. Ma trận khía cạnh × máy**

| | |
|---|---|
| **Số liệu** | % khen của 9 khía cạnh × 4 máy. Nguồn: `aggregates` |
| **Biểu đồ** | Bảng tô màu theo % khen. Ô tốt nhất mỗi hàng chỉ in đậm khi tốt hơn **có ý nghĩa** |
| **Kiểm định** | Mỗi khía cạnh 1 phép chi-square trên 4 máy (9 phép, Holm). Khía cạnh có ý nghĩa thì so tiếp X với từng máy (z-test, Holm trong khía cạnh đó) |

**3b. So sánh trực tiếp**

| | |
|---|---|
| **Số liệu** | Chỉ mention có `compare_with` khác null (vd "S23U chụp đêm thua iPhone"). % X thắng theo khía cạnh, bỏ `tie`. Nguồn: `aspect_mentions` |
| **Biểu đồ** | Thanh ngang 100%: X thắng / đối thủ thắng, ghi n |
| **Kiểm định** | Kiểm định nhị thức so với 50% (Holm theo số khía cạnh) |
| **Kết luận được phép** | Không có ý nghĩa → "chưa phân định" |

### Q4. Đời trước bị chê gì, đời này đã sửa được chưa?

| | |
|---|---|
| **Ý nghĩa** | Điểm yếu của P có còn ở X không. P lấy từ `models.predecessor_id` |
| **Số liệu** | % chê theo khía cạnh của P và X, **cùng định nghĩa với Q2**. Nguồn: `aggregates` |
| **Biểu đồ** | Slope chart: mỗi khía cạnh một đường P → X; đi xuống = bớt chê. Đường có ý nghĩa vẽ đậm, không có ý nghĩa vẽ mờ |
| **Kiểm định** | z-test hai tỷ lệ mỗi khía cạnh (9 phép, Holm) |
| **Kết luận được phép** | Chỉ 3 nhãn: "Đã cải thiện" (giảm có ý nghĩa), "Tệ hơn" (tăng có ý nghĩa), "Chưa đủ bằng chứng" |
| **Mở rộng** | So thêm một cặp đời máy đối chứng (vd iPhone 13 → 14). Nếu cặp đối chứng thay đổi giống hệt thì đó có thể là xu hướng chung, không phải riêng X |

### Q5. Lỗi gì cần sửa, ưu tiên cái nào?

| | |
|---|---|
| **Ý nghĩa** | Lỗi kỹ thuật do **người đã dùng X** báo, xếp ưu tiên cho đội kỹ thuật |
| **Số liệu** | Lọc `target_model = X`, `is_owner = true`, `defect_type` khác null. Mỗi loại lỗi: số lần nhắc; tỷ lệ lỗi mỗi tuần = số mention lỗi / tổng mention về X trong tuần. Nguồn: `aspect_mentions` |
| **Biểu đồ** | Bảng: lỗi \| số lần nhắc \| ↑/↓ \| mức ưu tiên \| bình luận mẫu |
| **Kiểm định xu hướng** | Cửa sổ 4 tuần: z-test tỷ lệ lỗi nửa đầu vs nửa sau. Mann-Kendall chỉ khi có ≥ 6–8 điểm thời gian |
| **Luật ưu tiên** | P1: ≥ 20 lần nhắc **và** tăng có ý nghĩa. P2: ≥ 20 lần nhắc, xu hướng không có ý nghĩa. P3: < 20 lần nhắc ("theo dõi, chưa đủ dữ liệu") |

Ngưỡng 20 là đề xuất; chốt lại sau khi biết số lượng thực tế.

## 3. Số liệu mỗi câu cần

| Câu | Nhóm theo | Nguồn |
|---|---|---|
| Q1 | máy × tuần | `aggregates` |
| Q2 | X × khía cạnh | `aggregates` + mẫu từ `aspect_mentions` |
| Q3a | máy × khía cạnh | `aggregates` |
| Q3b | khía cạnh, mention so sánh | `aspect_mentions` |
| Q4 | {P, X} × khía cạnh | `aggregates` |
| Q5 | loại lỗi × tuần, người đã dùng | `aspect_mentions` |

## 4. Những gì không đưa vào phần chính

Số lượng bình luận, độ dài, wordcloud, phân bố theo năm/giờ, tương tác like/reply: là EDA, đưa vào **phụ lục** để chứng minh dữ liệu đủ dùng. Lưu ý các phân bố theo tháng/năm chủ yếu phản ánh cách chọn video để crawl (cửa sổ 4 tuần sau ra mắt), không phải hành vi người xem.

## 5. Lỗi đã gặp ở bản nháp (tránh lặp lại)

| Lỗi | Quy tắc tương ứng |
|---|---|
| Lời chê iPhone tính cho S23U | 1.3: dùng `target_model` |
| Q2 và Q4 ra hai % chê khác nhau cho cùng khía cạnh | 1.4: một công thức |
| Q4 ghi "Đã cải thiện" dù p = 0,07–0,37 | Q4: chỉ 3 nhãn theo kiểm định |
| Xu hướng "+663%" từ n = 4 | 1.5 và luật ưu tiên Q5 |
| "không giật hay lag chút nào" bị đếm là lỗi | Q2: duyệt bình luận mẫu; mô hình phải xử lý phủ định |
| Dự báo tuần 8 từ 4 điểm | 1.6: không ngoại suy |
| Ngày 0 = comment đầu tiên | 1.1: ngày 0 = `launch_date` |

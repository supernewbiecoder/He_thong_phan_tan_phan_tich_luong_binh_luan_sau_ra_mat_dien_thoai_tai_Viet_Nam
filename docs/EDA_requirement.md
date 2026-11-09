# Đặc tả phân tích: 5 câu hỏi nghiệp vụ

> Mục đích: Định nghĩa thống nhất cách tính, biểu đồ, kiểm định và điều kiện kết luận cho Q1–Q5; cập nhật lần cuối: 2026-11-09, bổ sung suy luận theo cụm video cho CV12.

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

CV12 dùng contract aspect-mention v2: đủ trường bắt buộc; `clause_idx` là vị trí mảng từ 0, `clause_text` lấy chữ gốc; `parent_id`, `author_hash`, `author_is_creator` khớp comment nguồn. Cửa sổ Q1–Q5 là `[0, 28)` theo bốn tuần sau ra mắt, một tập con của miền lưu trữ `[-7, 28)` trong data-model; không gộp mention trước ra mắt vào các tỷ lệ sau ra mắt.

### 1.4 Công thức dùng cho mọi câu

```
% khen = 100 * pos / (pos + neg)  trung tính không vào mẫu số
% chê  = 100 * neg / (pos + neg)
Net    = % khen − % chê           từ −100 đến +100
```

Chỉ dùng **một** định nghĩa này. Số mệnh đề trung tính vẫn báo cáo kèm nhưng không vào mẫu số.

### 1.5 Ngưỡng tối thiểu

Ô nào có `pos + neg < 30` thì hiển thị mờ, ghi "ít dữ liệu", không kết luận.

Triển khai hiện tại còn yêu cầu ít nhất 20 video có mẫu số dương và 20 video hiệu dụng cho từng tỷ lệ cần suy luận. Số video hiệu dụng = `(tổng mẫu số)^2 / tổng(mẫu số từng video^2)` để chặn trường hợp một video chiếm gần hết dữ liệu. Đây là ngưỡng vận hành thận trọng, không bảo đảm tự động tính hợp lệ của bootstrap. Q3b áp ngưỡng số đếm trên `win + loss`; Q5 áp trên tổng mention về X. Mẫu số 0 trả `null`.

### 1.6 Thống kê

- **Khoảng tin cậy 95%**: bootstrap có hoàn lại các cụm `(source, video_id)`, tính lại tỷ lệ từ tổng số đếm, mặc định 1.000 lần; lấy phân vị 2,5%–97,5%. CI này là CI riêng từng chỉ số, không phải CI đồng thời đã hiệu chỉnh Holm.
- **Kiểm định theo cụm:** dùng pairs cluster bootstrap-t, lấy phân phối `(ước lượng bootstrap − ước lượng gốc) / SE bootstrap`; SE theo cụm từ delta method của tỷ lệ tổng. Q3a omnibus dùng Wald bootstrap trên 3 tương phản X với các máy khác. Thay các z-test/chi-square/nhị thức coi mention độc lập trong bản trước. Phương pháp bootstrap-t và giới hạn khi ít cụm được trình bày trong [Cameron & Miller (2015), mục VI.C](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).
- **Q2:** tính lại đồng thời tỷ lệ chê của khía cạnh và tỷ lệ chê chung của X trong cùng mẫu bootstrap, giữ hiệp phương sai vì hai tập chồng lấp; không xem tỷ lệ chung ước lượng là p0 cố định của kiểm định nhị thức.
- **Hiệu chỉnh đa so sánh:** Holm riêng từng câu hỏi. Nhóm được chốt trước: Q1=4; Q2=9; Q3=45 (9 omnibus + 27 so sánh X/máy + 9 so sánh trực tiếp); Q4=9; Q5=9. Phép chưa đủ điều kiện được giữ trong số phép dự kiến, coi p=1 nội bộ khi hiệu chỉnh; output p-value vẫn là `null`. Tham khảo [R p.adjust](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html).
- **Bootstrap lỗi/không ổn định:** SE bằng 0, ma trận suy biến hoặc dưới 95% số lần lấy mẫu hợp lệ thì không xuất p-value để kết luận; CI không tính được ghi `null` cùng lý do. Không coi thiếu kiểm định là không có khác biệt.
- **Mức ý nghĩa:** α = 0,05 sau hiệu chỉnh.
- **Cách viết kết luận:** có ý nghĩa → "X tốt hơn/kém hơn…"; không có ý nghĩa → "chưa đủ bằng chứng", **không** viết "bằng nhau".
- **Không dùng** ngoại suy/dự báo từ vài điểm dữ liệu.

Kết luận nghiệp vụ còn cần bàn giao nhãn đã được đánh giá. Dữ liệu demo hoặc nhãn `rule` chỉ dùng thăm dò; p-value có ý nghĩa không xác nhận mô hình gán nhãn đúng. Bình luận mẫu luôn cần người duyệt. Lưu ý: cụm video chưa xử lý hết phụ thuộc của cùng tác giả xuất hiện ở nhiều video.

## 2. Năm câu hỏi

### Q1. X được đón nhận tốt hay dở?

| | |
|---|---|
| **Ý nghĩa** | Nhìn tổng thể người dùng khen hay chê X nhiều hơn, so với P, R1, R2, và thay đổi qua từng tuần |
| **Số liệu** | Net theo (máy, tuần kể từ ra mắt), gộp mọi khía cạnh. Nguồn: `aggregates` |
| **Biểu đồ** | Đường theo tuần 1–4, mỗi máy một đường, dải mờ = khoảng tin cậy. Kèm bảng Net tổng cả cửa sổ |
| **Kiểm định** | Bootstrap-t theo cụm: % khen tổng X so với 50%, X vs P, X vs R1, X vs R2 (4 phép, Holm chung) |
| **Kết luận được phép** | "X được đón nhận tốt/kém hơn R1" chỉ khi có ý nghĩa |

### Q2. Ưu điểm và nhược điểm của X là gì?

| | |
|---|---|
| **Ý nghĩa** | Trong các khía cạnh của X, cái nào được khen nhiều (ưu), cái nào bị chê nhiều (nhược). Chỉ xét X |
| **Số liệu** | % khen, % chê, n theo khía cạnh, `target_model = X`. Nguồn: `aggregates` |
| **Biểu đồ** | Thanh hai chiều: chê sang trái màu đỏ, khen sang phải màu xanh, sắp theo Net |
| **Bình luận mẫu** | 2–3 bình luận/khía cạnh từ `aspect_mentions` (`target_model = X`, `confidence` cao). **Phải có người duyệt** trước khi đưa vào báo cáo |
| **Kiểm định** | Mỗi khía cạnh: hiệu % chê khía cạnh − % chê chung X; bootstrap-t ghép theo cụm, tính lại cả hai tỷ lệ (9 phép, Holm) |
| **Kết luận được phép** | Nhược điểm = % chê cao hơn mức chung của X có ý nghĩa; ưu điểm thì ngược lại |

### Q3. So với đối thủ, X mạnh/yếu ở đâu?

**3a. Ma trận khía cạnh × máy**

| | |
|---|---|
| **Số liệu** | % khen của 9 khía cạnh × 4 máy. Nguồn: `aggregates` |
| **Biểu đồ** | Bảng tô màu theo % khen. Ô tốt nhất mỗi hàng chỉ in đậm khi tốt hơn **có ý nghĩa** |
| **Kiểm định** | Mỗi khía cạnh 1 phép Wald bootstrap trên 4 máy và 3 tương phản X với máy khác. Tính đủ các phép dự kiến trước khi Holm chung nhóm Q3; so sánh cặp còn phải qua gate omnibus của khía cạnh |

**3b. So sánh trực tiếp**

| | |
|---|---|
| **Số liệu** | Chỉ mention có `compare_with` khác null (vd "S23U chụp đêm thua iPhone"). % X thắng theo khía cạnh, bỏ `tie`. Nguồn: `aspect_mentions` |
| **Biểu đồ** | Thanh ngang 100%: X thắng / đối thủ thắng, ghi n |
| **Kiểm định** | Bootstrap-t theo cụm cho tỷ lệ X thắng so với 50%; bỏ tie khỏi mẫu số, vẫn giữ video có tie khi lấy mẫu. Hiệu chỉnh trong nhóm Q3 chung |
| **Kết luận được phép** | Không có ý nghĩa → "chưa phân định" |

### Q4. Đời trước bị chê gì, đời này đã sửa được chưa?

| | |
|---|---|
| **Ý nghĩa** | Điểm yếu của P có còn ở X không. P lấy từ `models.predecessor_id` |
| **Số liệu** | % chê theo khía cạnh của P và X, **cùng định nghĩa với Q2**. Nguồn: `aggregates` |
| **Biểu đồ** | Slope chart: mỗi khía cạnh một đường P → X; đi xuống = bớt chê. Đường có ý nghĩa vẽ đậm, không có ý nghĩa vẽ mờ |
| **Kiểm định** | Bootstrap-t theo cụm cho hiệu % chê P − % chê X mỗi khía cạnh (9 phép, Holm) |
| **Kết luận được phép** | Chỉ 3 nhãn: "Đã cải thiện" (giảm có ý nghĩa), "Tệ hơn" (tăng có ý nghĩa), "Chưa đủ bằng chứng" |
| **Mở rộng** | So thêm một cặp đời máy đối chứng (vd iPhone 13 → 14). Nếu cặp đối chứng thay đổi giống hệt thì đó có thể là xu hướng chung, không phải riêng X |

### Q5. Lỗi gì cần sửa, ưu tiên cái nào?

| | |
|---|---|
| **Ý nghĩa** | Lỗi kỹ thuật do **người đã dùng X** báo, xếp ưu tiên cho đội kỹ thuật |
| **Số liệu** | Lọc `target_model = X`, `is_owner = true`, `defect_type` khác null. Mỗi loại lỗi: số lần nhắc; tỷ lệ lỗi mỗi tuần = số mention lỗi / tổng mention về X trong tuần. Nguồn: `aspect_mentions` |
| **Biểu đồ** | Bảng: lỗi \| số lần nhắc \| ↑/↓ \| mức ưu tiên \| bình luận mẫu |
| **Kiểm định xu hướng** | Bootstrap-t theo cụm cho (tổng lỗi tuần 3–4 / tổng mention X tuần 3–4) − (tổng lỗi tuần 1–2 / tổng mention X tuần 1–2); Holm theo 9 loại lỗi. Không trung bình các tỷ lệ tuần |
| **Luật ưu tiên** | P1: ≥20 lần nhắc và tăng có ý nghĩa. P2: ≥20 lần nhắc và kiểm định hợp lệ nhưng chưa có bằng chứng tăng, gồm cả giảm có ý nghĩa. P3: <20 lần nhắc. Nếu ≥20 nhưng không kiểm định được thì chưa xếp ưu tiên; nhãn chưa được xác nhận chỉ có priority_candidate, không có ưu tiên chính thức |

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

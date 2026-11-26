# Kế hoạch nhánh `kham-pha-nhan`: từ dữ liệu v4 tới bộ nhãn

> Mục đích: Nhánh này làm gì và vì sao; đang có gì; các bước B1–B8 (làm gì, ai làm, ra gì, khi nào là xong, vì sao làm vậy); việc sau nhánh; quyết định đang chờ; cập nhật lần cuối: 2026-11-25.

**Cách đọc:**
- Mục 1–2: vì sao có nhánh và nhánh đang có gì.
- Mục 3: lộ trình và lý do từng bước.
- Mục 5: những việc trưởng nhóm cần quyết.

Cách chạy notebook, cách mã hóa: xem các file hướng dẫn trong [mục lục tài liệu](../README.md).

## 1. Vì sao có nhánh này

- **Đề tài:** phân tích bình luận YouTube tiếng Việt sau khi một điện thoại ra mắt, để trả lời 6 câu hỏi (mục 6).
- **Nhánh `main` đã xây khá nhiều:** tiền xử lý, luật mốc, phân tích thống kê, guideline gán nhãn. Nhưng **bộ nhãn** (9 khía cạnh, 3 mức liên quan, các loại spam…) được đặt **trước khi đọc nội dung dữ liệu**. EDA trên `main` mới đo cấu trúc (định dạng, trùng lặp, độ dài, ngôn ngữ, thời gian), chưa đo bình luận nói về cái gì.
- Vì vậy chưa ai trả lời được: trong 473.786 bình luận v4, **có những loại nội dung nào, mỗi loại chiếm bao nhiêu**, và bộ nhãn đã đặt có thiếu hay thừa không.
- Nhánh này **bắt đầu lại từ dữ liệu**. Nó chỉ có dữ liệu v4 và notebook kiểm tra cấu trúc. Mục tiêu là rút ra bộ nhãn từ chính dữ liệu, kèm phân bố có khoảng tin cậy.
- Trong lúc làm, **tạm không xét contract** và các thiết kế đã có trên `main` (trưởng nhóm quyết ngày 22/11).

**Vì sao là nhánh mồ côi** (không chung lịch sử với `main`):
- **Không ai vô tình merge được nhánh này vào `main`.** Merge sẽ xóa sạch `main`, nhưng git từ chối merge hai nhánh không chung lịch sử nếu không cố ý.
- Nhánh này và `main` dùng chung một thư mục, chuyển bằng GitHub Desktop. Dữ liệu và `.venv` nằm ngoài git nên dùng chung. Trước khi chuyển nhánh phải commit hoặc bỏ thay đổi đang dở.
- Kết quả của nhánh (bộ nhãn, báo cáo, notebook) đưa về `main` bằng cách **chép file**, không merge.

## 2. Nhánh đang có gì

| Thứ | Ở đâu | Ghi chú |
|---|---|---|
| Dữ liệu v4 | `src/ingest/data/` (**ngoài git**) | 473.786 bình luận, 4.682 video, 139 máy. Chi tiết ở [đặc tả dữ liệu](../1-thu-thap/dac-ta.md) |
| Cấu hình đã dùng để crawl v4 | `config/pipeline.yaml` | Danh mục máy, kênh, cửa sổ thời gian. `helpers.py` cũng dựa vào file này để tìm gốc repo |
| Bộ 4 máy ứng viên | `config/analysis.yaml` | Bộ cũ, chưa chốt; chỉ notebook mục 3.4 dùng |
| Kiểm tra cấu trúc dữ liệu (EDA) | `notebooks/1_raw_audit.ipynb`, `notebooks/helpers.py` | Chép từ `main` ngày 22/11. Ô code giữ nguyên; đã xóa output vì output chứa bình luận thật |
| Code khám phá nhãn | `src/labeling/` (lấy mẫu, HAC, công thức thống kê), `tests/test_labeling.py` | Theo [đặc tả khám phá nhãn](../3-gan-nhan/dac-ta-kham-pha-nhan.md) mục 10 |
| Tài liệu | `docs/` | [Mục lục](../README.md) |
| Luật cho trợ lý AI | `AGENTS.md` | Claude Code đọc qua `CLAUDE.md` |

**Cố ý không có:** code crawler, tiền xử lý, luật mốc, mô hình, phân tích Q1–Q6, DB. Chúng vẫn ở `main`. Thiếu chúng không cản các bước của nhánh, vì khám phá nhãn chỉ cần đọc bình luận.

## 3. Lộ trình

Từ 22/11 tìm nhãn bằng **ba nguồn rồi so với nhau**: HAC trên cả bộ dữ liệu, mã hóa mở trên mẫu ngẫu nhiên, và bộ nhãn đặt sẵn trên `main`. Từ 23/11 HAC chỉ để đối chiếu, không ai chấm. **Claude mã hóa, trưởng nhóm kiểm.** Luật chi tiết: [đặc tả khám phá nhãn](../3-gan-nhan/dac-ta-kham-pha-nhan.md).

| Bước | Làm gì | Ai | Đầu ra | Xong khi | Trạng thái |
|---|---|---|---|---|---|
| B1 | Kiểm tra cấu trúc dữ liệu: chạy `1_raw_audit` | Trưởng nhóm (Claude chạy) | [Báo cáo kiểm tra dữ liệu](../1-thu-thap/bao-cao-kiem-tra-du-lieu.md) | Điền hết các ô "chờ chạy" | **Xong 22/11.** Phát hiện: từ khóa nhận video tặng quà sai cả hai chiều; 5 kênh chiếm 62,7% bình luận; 2,84% là bình luận của chủ kênh |
| B2 | Lấy mẫu: 800 ngẫu nhiên (lô 1–5, K, D1, D2), 100 có chủ đích; xuất phiếu lô 1–5 | Claude | `data/kham-pha/mau.csv`, `phieu_ma_hoa_mo.csv` | Đúng đặc tả mục 3 | **Xong 22/11** |
| B3 | HAC trên cả bộ dữ liệu → 300 ứng viên khía cạnh | Claude | `data/kham-pha/hac_ung_vien.csv` | Đúng đặc tả mục 4 | **Xong 22/11** |
| B4 | Mã hóa mở lô 1–5 và mẫu có chủ đích. **Thí điểm:** xong lô 1 thì dừng cho trưởng nhóm xem | Claude | Phiếu có mã | Bình luận nào cũng có ít nhất một mã | **Xong 23/11** (600 bình luận, Claude tự rà 2 lượt; [thống kê](../3-gan-nhan/bao-cao-ma-hoa-mo.md)). Trưởng nhóm chưa kiểm từng mã. Cùng ngày trưởng nhóm tự mã tay cả 600 bình luận để đo đồng thuận ([đặc tả 7d](../3-gan-nhan/dac-ta-kham-pha-nhan.md#7-kiểm-b6)); đã so 599 bình luận (bỏ 1 dòng bị Excel làm hỏng ô), kết quả ở `data/kham-pha/dong_thuan_ma_hoa_mo.csv`; bảng hành vi trong guideline sửa theo kết quả này |
| B5 | Gom mã thành bộ nhãn; đếm bão hòa | Claude; trưởng nhóm duyệt | `docs/3-gan-nhan/dac-ta-bo-nhan.md` | Lô 5 không thêm nhãn mới | **Xong 25/11:** nháp 23/11, trưởng nhóm duyệt 25/11: 6 chiều; bão hòa đạt (lô 4, 5 không có nhãn mới; [báo cáo](../3-gan-nhan/bao-cao-bo-nhan.md)) |
| B6 | Kiểm: gán mù lô K; kiểm nhãn của Claude | **Trưởng nhóm** (Claude gán lô K) | Kappa; tỷ lệ nhãn phải sửa | Kappa ≥ 0,6 ở mọi chiều dùng tiếp | **Xong 26/11:** [so lô K](../3-gan-nhan/bao-cao-lo-k.md): mọi chiều κ ≥ 0,6 (chiều 1: 0,72; chiều 2, 3 xét kappa gộp: 0,81, 0,83). 52 ca lệch: Claude đề xuất, trưởng nhóm duyệt. Thêm luật 8, 9 của bộ nhãn |
| B7 | Gán cả mẫu (600) theo bộ nhãn cuối → phân bố | Claude; trưởng nhóm kiểm | Bảng phân bố, khoảng tin cậy Wilson và bootstrap theo video | Đủ mọi chiều, đủ các nhóm | **Xong 26/11:** mẫu 600 (lô 1–5 Claude gán, trưởng nhóm kiểm cả 500, phải sửa 17% [10,9; 25,5] ở phần ngẫu nhiên; lô K đã phân xử). [Báo cáo](../3-gan-nhan/bao-cao-phan-bo-nhan.md) có tỷ lệ và KTC |
| B8 | So ba nguồn (HAC: Claude đối chiếu trên cả bộ dữ liệu); chốt bộ nhãn | Claude đề xuất, trưởng nhóm quyết | Bộ nhãn chốt, kèm lý do | Nhãn nào cũng có lý do giữ, thêm, gộp hay bỏ | **Xong 26/11:** trưởng nhóm duyệt [đề xuất](../3-gan-nhan/bao-cao-kham-pha-nhan.md); [bộ nhãn chốt](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611): gộp `nhiet_do`, `am_thanh`, `khong_noi_dung`; thêm `mua_ban` (sửa định nghĩa) |

**Vì sao từng bước:**

- **B1. Kiểm tra cấu trúc trước khi đọc nội dung.**
  - Biết dữ liệu hỏng hay lệch ở đâu: rỗng, trùng, tiếng nước ngoài, đăng dồn.
  - Các trường có sẵn (gốc hay reply, kênh, tuần, của chủ kênh) là **nhóm** để tách phân bố ở B7.
  - Thấy sớm nguồn nhiễu lớn: 4 trong 5 video đông nhất là video tặng quà, cộng lại 15.998 bình luận.
- **B2. Lấy mẫu, vì không ai đọc nổi 473 nghìn bình luận.**
  - Mẫu **ngẫu nhiên** cho phân bố không thiên lệch.
  - **Vì sao 500 bình luận mã hóa mở** (đặc tả mục 3.3):
    - nhãn chiếm 0,5% có 92% khả năng xuất hiện (với 300 chỉ 78%);
    - cộng 100 của lô K thành n = 600, đúng cỡ mẫu để sai số mọi tỷ lệ không quá ±4%;
    - mỗi nhóm cần so (reply, kênh lớn, tuần 3–4) có từ 194 bình luận trở lên (nhỏ nhất là tuần 3–4), sai số khoảng ±7%.
  - Lô K để riêng, **không ai đọc trước B6**, để đo đồng thuận trên bình luận chưa ai bàn.
  - Mẫu có chủ đích (tìm theo "lỗi", "bảo hành"…) chỉ để không sót loại hiếm mà quan trọng. Nó **không tính vào phân bố**.
- **B3. HAC trên cả bộ dữ liệu.** Thuật toán của bài báo nhóm đã đọc (Wiegard và cộng sự, ECIS 2017), bản tiếng Việt không cần tách từ. Nó tìm được khía cạnh hiếm mà mẫu 600 bình luận có thể sót. Nhưng nó chỉ ra **ứng viên khía cạnh**, không ra các chiều khác, và không cho phân bố. Ngay ở bài gốc chỉ 35–50% ứng viên là đúng. Ngày 23/11 trưởng nhóm quyết không chấm, vì danh sách nhiễu (mảnh từ, teencode); HAC chỉ dùng để đối chiếu ở B8.
- **B4. Mã hóa mở**, ghi đối tượng bằng từ của chính bình luận, không dùng tên 9 khía cạnh đặt sẵn. Thí điểm lô 1 để trưởng nhóm sửa cách mã sớm, trước khi làm 500 bình luận.
- **B5. Bão hòa là luật dừng có căn cứ.** Nó trả lời câu "bao nhiêu nhãn là đủ" bằng dữ liệu.
- **B6. Phần không thay được bằng AI** (khoảng 3 giờ của trưởng nhóm). Nhãn do Claude gán là nhãn của AI. Chỉ có gán mù lô K và kiểm nhãn mới đo được AI đúng tới đâu.
- **B7. Câu trả lời trực tiếp** cho câu hỏi "dữ liệu có những nhãn nào, phân bố ra sao". Khoảng tin cậy chính tính bằng bootstrap theo video, vì bình luận cùng video giống nhau (đặc tả mục 8).
- **B8. So và quyết theo luật viết sẵn** ([đặc tả mục 9](../3-gan-nhan/dac-ta-kham-pha-nhan.md#9-so-ba-nguồn-và-chốt-bộ-nhãn-b8)) để không quyết theo cảm tính.

## 4. Sau nhánh này

Thứ tự dự kiến. Kế hoạch chi tiết cho cả dự án sau nhánh này (đề xuất, chờ duyệt): [kế hoạch tổng thể](ke-hoach-tong-the.md).

1. **Viết guideline gán nhãn** theo bộ nhãn chốt ở B8. **Xong 26/11:** [huong-dan-gan-nhan-chinh-thuc.md](../3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md), trưởng nhóm duyệt cả mục 9 ngày 26/11 (nối nhận xét với máy, so sánh có bên thắng, cờ tiếng Việt). Loại lỗi để sau, làm trên mẫu riêng các bình luận báo lỗi.
2. **Gán nhãn chính thức**, hai mẫu:
   - mẫu chất lượng dữ liệu, lấy từ dữ liệu **chưa lọc**, để đo bộ lọc spam và tiếng Việt;
   - tập test cho mô hình, gán đôi và phân xử.
3. **Tiền xử lý, luật mốc, mô hình**, đo trên tập test. Chọn mô hình đơn giản nhất mà kết luận không đổi.
4. **Trả lời Q1–Q6**, kèm khoảng tin cậy, phép kiểm sai số mô hình và phép kiểm độ nhạy.
5. **Đưa kết quả về `main`** bằng cách chép file. Contract và thiết kế dữ liệu trên `main` sửa theo bộ nhãn mới nếu cần.

## 5. Quyết định

**Đã chốt (22–25/11):**

| # | Quyết định | Chốt |
|---|---|---|
| 1 | Cỡ mẫu | Mã hóa mở **500**; mẫu phân bố 600 (cộng lô K). Lý do ở đặc tả mục 3.3 |
| 2 | Ai mã hóa | **Claude** mã hóa; trưởng nhóm kiểm (gán mù lô K, kiểm nhãn, duyệt bộ nhãn) |
| 3 | Dùng AI đọc bình luận | Chỉ Claude, trong phiên Claude Code của trưởng nhóm; chỉ gửi chữ bình luận, không gửi thông tin người viết |
| 4 | Khám phá trên cả bộ dữ liệu | Làm ngay bằng HAC bản không cần tách từ, kết hợp với mã hóa mở |
| 5 | Bình luận minigame | **Giữ** trong dữ liệu. Về sau đánh dấu các video giveaway lớn để kiểm độ nhạy (bình luận có thưởng dễ khen quá tay) |
| 6 | Lượt bình luận ngoài tuần 1–4 | Để đó, giữ nguyên dữ liệu |
| 9 | Từ dùng trong tài liệu (chốt 24/11) | *Nhãn* và *khía cạnh* theo một nghĩa: mọi khía cạnh là nhãn của chiều 2, không phải nhãn nào cũng là khía cạnh ([thuật ngữ](../3-gan-nhan/dac-ta-kham-pha-nhan.md#thuật-ngữ)). Chiều 2 đổi tên thành "Nói về phần nào của điện thoại" |
| 8 | Chấm danh sách HAC (chốt 23/11) | **Không chấm.** HAC chỉ để Claude đối chiếu ở B8, kết quả ghi là AI làm (đặc tả mục 4.4) |
| 10 | Luật chốt bộ nhãn (chốt 25/11) | Ngưỡng 3% và 1% tính trên phần áp dụng của từng chiều, trong mẫu phân bố; nhãn mới dưới 3% thì gộp, trừ khi có câu hỏi cần riêng nó; nhãn dưới 1% chỉ gộp khi không phục vụ câu hỏi nào và không giúp đánh giá chất lượng dữ liệu; quyết theo tỷ lệ đo được, sát ngưỡng thì ghi để xem lại ([đặc tả mục 9](../3-gan-nhan/dac-ta-kham-pha-nhan.md#9-so-ba-nguồn-và-chốt-bộ-nhãn-b8)) |
| 11 | Duyệt bộ nhãn (chốt 25/11) | Nhãn hiếm để riêng tới B8; không tách hãng và fan; bài test trong video là `ngu_canh`; tách `dua` và `cong_kich`; cà khịa không tính là chê; máy tính bảng là `khong_lien_quan`; máy đẹp, xấu chung chung là `thiet_ke` ([đặc tả bộ nhãn mục 7](../3-gan-nhan/dac-ta-bo-nhan.md#7-trưởng-nhóm-đã-quyết-khi-duyệt-2511)) |
| 12 | Chốt bộ nhãn B8 (chốt 26/11) | Duyệt cả đề xuất của Claude: 5 chiều 1, 11 khía cạnh + `may_chung`, `hang_nguoi_dung`, `khac`, 13 mục đích; `mua_ban` thêm (Claude chọn khi trưởng nhóm giao: "như đề xuất"). Trước khi gán chính thức: sửa định nghĩa `dua`, `khong_xac_dinh`; thêm trường tên máy ([đặc tả bộ nhãn mục 8](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611)) |
| 13 | Trước khi gán chính thức (26/11) | Sửa định nghĩa `dua`, `khong_xac_dinh` (chiều 1) theo ca lệch lô K; thêm trường `ten_may`. Kiểm lại trên 50 bình luận đầu lô D2: xong 26/11, mọi chiều κ ≥ 0,6 ([báo cáo](../3-gan-nhan/bao-cao-lo-d2.md)); ba chỗ luật còn lệch đã làm rõ 26/11 ([đặc tả khám phá nhãn mục 7b](../3-gan-nhan/dac-ta-kham-pha-nhan.md#7-kiểm-b6)) |
| 7 | Bộ 4 máy (chốt 26/11) | **Không chọn bộ 4 máy.** Dòng máy nào có trong dữ liệu thì phân tích hết. Trước mắt lấy nhãn để làm mô hình phân loại cảm xúc. Hệ quả: đặc tả mục tiêu và đặc tả gán nhãn trên `main` (đang dựa trên X, đời trước, 2 đối thủ) phải sửa khi chép kết quả về; mẫu gán chính thức nên dồn vào bình luận `dien_thoai`, đủ cặp (bình luận, khía cạnh) cho từng khía cạnh |

**Còn chờ:** không còn.

## 6. Câu hỏi của đề tài (tóm tắt)

| # | Câu hỏi |
|---|---|
| Q1 | Máy X được đón nhận tốt hay dở, thay đổi qua 4 tuần đầu thế nào? |
| Q2 | X có ưu, nhược điểm gì (khen, chê theo khía cạnh)? |
| Q3 | So với đối thủ, X mạnh, yếu ở đâu? |
| Q4 | Đời trước bị chê gì, đời này đã sửa chưa? |
| Q5 | Người đã dùng X báo lỗi gì, lỗi nào cần sửa trước? |
| Q6 | Có tài khoản ảo seeding không, và nó làm lệch kết quả bao nhiêu? (đề xuất) |

Bộ nhãn chốt ở B8 phải đủ để trả lời các câu này. Nhãn không phục vụ câu nào và không giúp đánh giá chất lượng dữ liệu thì không cần gán.

## 7. Quy tắc của nhánh

- Không commit dữ liệu, file mẫu, phiếu mã hóa, hay output notebook có bình luận thật ([AGENTS.md](../../AGENTS.md)).
- **Chưa push.** Trưởng nhóm quyết khi nào push.
- Không merge vào `main`. Đưa kết quả về `main` bằng cách chép file.
- Tiến độ chỉ ghi ở cột "Trạng thái" của mục 3 trong file này.

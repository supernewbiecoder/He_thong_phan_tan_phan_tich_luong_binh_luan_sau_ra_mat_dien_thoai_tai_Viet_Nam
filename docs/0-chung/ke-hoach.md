# Kế hoạch nhánh `kham-pha-nhan`: từ dữ liệu v4 tới bộ nhãn

> Mục đích: Nhánh này làm gì và vì sao; đang có gì; các bước B1–B8 (làm gì, ai làm, ra gì, khi nào là xong, vì sao làm vậy); việc sau nhánh; quyết định đang chờ; cập nhật lần cuối: 2026-11-22.

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
| Tài liệu | `docs/` | [Mục lục](../README.md) |
| Luật cho trợ lý AI | `AGENTS.md` | Claude Code đọc qua `CLAUDE.md` |

**Cố ý không có:** code crawler, tiền xử lý, luật mốc, mô hình, phân tích Q1–Q6, DB. Chúng vẫn ở `main`. Thiếu chúng không cản các bước của nhánh, vì khám phá nhãn chỉ cần đọc bình luận.

## 3. Lộ trình

| Bước | Làm gì | Ai | Đầu ra | Xong khi | Trạng thái |
|---|---|---|---|---|---|
| B1 | Kiểm tra cấu trúc dữ liệu: chạy lại `1_raw_audit` trên nhánh | Trưởng nhóm | [Báo cáo kiểm tra dữ liệu](../1-thu-thap/bao-cao-kiem-tra-du-lieu.md) đủ số | Điền hết các ô "chờ chạy" | Level 0 đã có số (chạy 11/11); mục 3–5 chờ chạy |
| B2 | Lấy mẫu khám phá: 300 bình luận ngẫu nhiên (lô 1–3), 100 để kiểm bộ nhãn (lô 4), ~100 chọn có chủ đích | Notebook `3_label_discovery` (**chưa có**) | File mẫu, phiếu mã hóa | Đúng [đặc tả khám phá nhãn](../3-gan-nhan/dac-ta-kham-pha-nhan.md) mục 2 | Chưa làm |
| B3 | Mã hóa mở lô 1–3 | 2 người | Phiếu có mã tự do | Bình luận nào cũng có ít nhất một mã | Chưa làm |
| B4 | Gom mã thành bộ nhãn; theo dõi bão hòa | 2 người | Bộ nhãn nháp; bảng số nhãn mới theo lô | Lô cuối không thêm nhãn mới | Chưa làm |
| B5 | Kiểm bộ nhãn trên lô 4 | 2 người | Kappa từng chiều | Kappa ≥ 0,6 ở mọi chiều dùng tiếp | Chưa làm |
| B6 | Gán cả mẫu ngẫu nhiên theo bộ nhãn cuối | 2 người | Bảng phân bố, khoảng tin cậy 95% | Đủ mọi chiều, đủ các nhóm | Chưa làm |
| B7 | So với bộ nhãn đã đặt trên `main`; chốt bộ nhãn | Trưởng nhóm | Bộ nhãn chốt, kèm lý do | Nhãn nào cũng có lý do giữ, thêm, gộp hay bỏ | Chưa làm |
| B8 (tùy chọn) | Khám phá trên cả 473 nghìn bình luận, không cần nhãn | ___ | Danh sách gợi ý mã | | Chưa làm |

**Vì sao từng bước:**

- **B1. Kiểm tra cấu trúc trước khi đọc nội dung.**
  - Biết dữ liệu hỏng hay lệch ở đâu: rỗng, trùng, tiếng nước ngoài, đăng dồn.
  - Các trường có sẵn (máy của video, loại video, gốc hay reply, kênh) sẽ là **nhóm** để tách phân bố ở B6.
  - Thấy sớm nguồn nhiễu lớn: 4 trong 5 video đông nhất là video tặng quà, cộng lại 15.998 bình luận.
- **B2. Lấy mẫu, vì không ai đọc nổi 473 nghìn bình luận.**
  - Mẫu **ngẫu nhiên** cho phân bố không thiên lệch.
  - 300 là đủ để thấy: một loại chiếm 1% số bình luận có 95% khả năng xuất hiện ít nhất một lần trong mẫu.
  - Lô 4 tách riêng để kiểm bộ nhãn trên những bình luận **chưa ai đọc**. Kiểm trên bình luận đã đem ra bàn thì mức đồng thuận bị thổi phồng.
  - Mẫu có chủ đích (tìm theo "lỗi", "bảo hành"…) chỉ để không sót những loại hiếm mà quan trọng. Nó **không tính vào phân bố**, vì chọn theo từ khóa là thiên lệch.
- **B3. Mã hóa mở, không cầm danh sách nhãn có sẵn.**
  - Cầm danh sách thì chỉ xác nhận lại cái mình đã nghĩ sẵn, không phát hiện được cái thiếu.
  - Hai người mã hóa độc lập ở lô 1 thì thấy ngay chỗ hai người hiểu khác nhau.
- **B4. Bão hòa là luật dừng có căn cứ.** Nó trả lời câu "bao nhiêu nhãn là đủ" bằng dữ liệu, không bằng cảm tính.
- **B5. Kiểm đồng thuận.** Nhãn mà hai người không thống nhất được thì không đếm tin được, và cũng không dùng được để dạy mô hình.
- **B6. Đây là câu trả lời trực tiếp** cho câu hỏi "dữ liệu có những nhãn nào, phân bố ra sao". Cần khoảng tin cậy vì 400 bình luận chỉ là mẫu.
- **B7. So và quyết theo luật viết sẵn** ([đặc tả khám phá nhãn mục 7](../3-gan-nhan/dac-ta-kham-pha-nhan.md#7-so-với-bộ-nhãn-đã-đặt-và-chốt-bộ-nhãn-b7)) để không quyết theo cảm tính. Kết quả cho biết thiết kế trên `main` đúng, thiếu hay thừa ở đâu.
- **B8. Chỉ để gợi ý mã.** Lần thử phân cụm trên `main` cho silhouette chỉ khoảng 0,17–0,20, tức gần như không có cụm rõ. Vì vậy kết quả B8 không dùng làm phân bố.

## 4. Sau nhánh này

Thứ tự dự kiến. Chi tiết viết khi tới bước đó.

1. **Viết guideline gán nhãn** theo bộ nhãn chốt ở B7.
2. **Gán nhãn chính thức**, hai mẫu:
   - mẫu chất lượng dữ liệu, lấy từ dữ liệu **chưa lọc**, để đo bộ lọc spam và tiếng Việt;
   - tập test cho mô hình, gán đôi và phân xử.
3. **Tiền xử lý, luật mốc, mô hình**, đo trên tập test. Chọn mô hình đơn giản nhất mà kết luận không đổi.
4. **Trả lời Q1–Q6**, kèm khoảng tin cậy, phép kiểm sai số mô hình và phép kiểm độ nhạy.
5. **Đưa kết quả về `main`** bằng cách chép file. Contract và thiết kế dữ liệu trên `main` sửa theo bộ nhãn mới nếu cần.

## 5. Quyết định đang chờ trưởng nhóm

| # | Quyết định | Lựa chọn | Ảnh hưởng tới |
|---|---|---|---|
| 1 | Cỡ mẫu khám phá | 300 (đề xuất) hay 500 bình luận cho lô 1–3 | Độ rộng khoảng tin cậy, công đọc |
| 2 | Ai mã hóa | Trưởng nhóm + 1 người (đề xuất): đây là bước định nghĩa bài toán | Chất lượng bộ nhãn |
| 3 | Cho LLM gợi ý mã trên mẫu lớn hơn | Có hay không. Có thì phải gửi bình luận ra dịch vụ bên ngoài; nhãn LLM vẫn phải có người kiểm và không dùng làm phân bố | B4, B8 |
| 4 | B8 làm khi nào | Ngay, hay sau B7 | Công sức |
| 5 | Bình luận dưới video tặng quà | Giữ, gắn cờ, hay loại khỏi phân tích. B6 cho biết chúng chiếm bao nhiêu | Phân bố, các câu hỏi |
| 6 | Bộ 4 máy | Chốt sau | Notebook mục 3.4 |

## 6. Câu hỏi của đề tài (tóm tắt)

| # | Câu hỏi |
|---|---|
| Q1 | Máy X được đón nhận tốt hay dở, thay đổi qua 4 tuần đầu thế nào? |
| Q2 | X có ưu, nhược điểm gì (khen, chê theo khía cạnh)? |
| Q3 | So với đối thủ, X mạnh, yếu ở đâu? |
| Q4 | Đời trước bị chê gì, đời này đã sửa chưa? |
| Q5 | Người đã dùng X báo lỗi gì, lỗi nào cần sửa trước? |
| Q6 | Có tài khoản ảo seeding không, và nó làm lệch kết quả bao nhiêu? (đề xuất) |

Bộ nhãn chốt ở B7 phải đủ để trả lời các câu này. Nhãn không phục vụ câu nào và không giúp đánh giá chất lượng dữ liệu thì không cần gán.

## 7. Quy tắc của nhánh

- Không commit dữ liệu, file mẫu, phiếu mã hóa, hay output notebook có bình luận thật ([AGENTS.md](../../AGENTS.md)).
- **Chưa push.** Trưởng nhóm quyết khi nào push.
- Không merge vào `main`. Đưa kết quả về `main` bằng cách chép file.
- Tiến độ chỉ ghi ở cột "Trạng thái" của mục 3 trong file này.

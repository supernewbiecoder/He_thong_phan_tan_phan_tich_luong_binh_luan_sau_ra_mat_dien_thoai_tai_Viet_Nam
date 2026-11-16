# Sổ tay dự án: đang ở đâu, làm gì tiếp

> Mục đích: Nơi duy nhất ghi tiến độ từng công việc, việc cần làm tiếp và quyết định đang chờ; cập nhật lần cuối: 2026-11-11.

**Cách dùng:** đọc mục 1 để nắm tình hình trong 1 phút, tìm dòng công việc của mình ở mục 2, việc tiếp theo ở mục 4.

**Ranh giới với các tài liệu khác:**
- Yêu cầu và đầu ra của từng công việc nằm ở [roadmap.md](roadmap.md).
- Luật thu thập dữ liệu nằm ở [docs/spec/thu-thap.md](../spec/thu-thap.md).
- File này **chỉ ghi tiến độ**, không chép yêu cầu hay số liệu sang đây.

Trạng thái lấy từ `main` và các nhánh trên `origin` ngày 10/11/2026.

## 1. Tóm tắt

- **Giai đoạn 0 chưa đóng.** Contract đã chốt, dữ liệu crawl v4 đã có kèm checksum. Repo hiện chỉ có crawler và dữ liệu: code tiền xử lý, dashboard nháp và đặc tả Q1–Q5 đã gỡ khỏi `main` ngày 11/11 (còn trong lịch sử git). Trong khi đó 6 nhánh đã làm sang giai đoạn 1–3 (DB, dataset ngoài, cảm xúc, spam, Q1–Q5, dashboard), **chưa nhánh nào merge**.
- **Ba việc đang chặn cả dự án:**
  1. Chưa có tập test gán tay (Công việc 1). Mọi điểm F1 hiện có đều đo trên nhãn LLM hoặc nhãn luật, chưa nói được mô hình đúng hay sai.
  2. Chưa có quy tắc gán máy cho bình luận không nêu tên (Công việc 10). Phần lớn bình luận không gọi tên máy nào, nên Q3 và Q4 có làm được hay không phụ thuộc vào quy tắc này.
  3. Các nhánh đụng nhau. `nlquan` và `task12` cùng sửa `src/serving/dashboard/index.html`; `task12` sửa `docs/EDA_requirement.md`; cả hai file đã bị xóa trên `main`. Nhánh DB vẫn theo contract v1.
- **Rủi ro chung:** nhiều phần được xây trên đầu vào chưa kiểm chứng: nhãn LLM, dữ liệu seed giả của DB, dữ liệu cũ 109 nghìn dòng. Merge vội thì các lỗi này đi thẳng vào kết quả Q1–Q5.

## 2. Tiến độ từng công việc

Ký hiệu: ✅ đã merge vào `main` · 🔀 có trên nhánh, chưa merge · ⚠️ có nhưng còn vấn đề phải sửa · ❌ chưa bắt đầu.

| CV | Việc | Trạng thái | Đã có (ai, ở đâu) | Còn thiếu / vấn đề |
|---|---|---|---|---|
| 1 | Gán nhãn | 🔀 ⚠️ | Guideline v0.3 `docs/labeling-guideline.md` (Kiên, nhánh `kien/cong-viec-9`), đã chỉnh qua 2 lần thử với Gemini | Chưa hiệu chỉnh 50 mệnh đề cả nhóm. Chưa có tập test người gán, chưa có kappa. Guideline đang nằm trong nhánh CV9, cần PR riêng |
| 2 | Danh mục máy | ⚠️ | `config/pipeline.yaml` là đúng config đã dùng để crawl bản v4 (gộp từ yt-crawler 11/11): 139 mã máy, 50 kênh; mọi máy trong dữ liệu đều có `launch_date` | Chưa ghi nguồn cho `launch_date`. Chưa có `predecessor`. 12 máy khai trong config nhưng không có dữ liệu. Bộ 4 máy chưa chốt |
| 3 | DB | 🔀 ⚠️ | MongoDB 7 collection, `init_db`/`seed_db`/`verify_db`, `docs/database_design.md` (Việt / davebui306, nhánh `feature/eda-dashboard-database-design`, 07/11) | Theo contract **v1**, trong khi contract đã lên v2 (08/11). `seed_db.py` sinh mention giả (xem ghi chú dưới bảng), chỉ dùng được làm dữ liệu demo cho DB. Nhánh lệch `main` 3 commit |
| 4 | Contract | ✅ | `aspect-mention` v2 (08/11); `comment-event` v3 (11/11), khớp từng trường với crawler và dữ liệu v4 | `author_name` vẫn nằm trong dữ liệu và contract, trái README (quyết định 3) |
| 5 | Dataset ngoài | 🔀 | Chuẩn hóa UIT-ViSD4SA (có span) + test + trang duyệt `FEATURES` (phudatdam, nhánh `feat/map-external-data`, 09/11). Bỏ ViSFD vì không có span | Chờ nhóm duyệt 50 mẫu `FEATURES`. Roadmap CV5 còn ghi ViSFD, cần sửa khi merge |
| 6 | Tiền xử lý | ❌ | Bản cũ `cleaner/` + `run_cleaning.py` (Nhan Nguyen, 28/10) đã gỡ khỏi `main` ngày 11/11; còn trong lịch sử git (commit `59e2d16`) | Chưa có code tiền xử lý cho dữ liệu v4, chưa có `clean_data` v4 |
| 7 | Khung đánh giá | ❌ | | Không có file chia tập chung hay `evaluate.py`. CV9 tự chia theo video, CV11 có `evaluate_spam.py` riêng, nên điểm các mô hình không so được với nhau |
| 8 | Mô hình khía cạnh | ❌ | | Chưa chốt baseline luật (`rule-v0`): ml-training trỏ tới luật trong notebook EDA cũ (đã xóa); `seed_db.py` của CV3 có một bộ luật khác cùng tên |
| 9 | Mô hình cảm xúc | 🔀 ⚠️ | Nhãn LLM (Gemini/NVIDIA), tập train/val chia theo video, baseline TF-IDF + LR, báo cáo + hình (Kiên, nhánh `kien/cong-viec-9`, 09/11) | Điểm mới đo trên nhãn LLM. `extract_clauses.py` mặc định `clause_idx` đếm từ 1. File báo cáo `.md` nằm trong `data/task9/` (thư mục bị `.gitignore`), nên chuyển sang `docs/reports/task9/` |
| 10 | Máy được nhắc | ❌ | | Quy tắc cho bình luận không nêu tên; tên gọi tắt ("táo", "ss", "14prm"); mệnh đề so sánh |
| 11 | Spam | 🔀 ⚠️ | Luật + LinearSVC, 500 nhãn (50 spam), tách `is_vietnamese` khỏi `is_spam` (Nguyễn Lê Quân, nhánh `nlquan`, 28/10) | Làm trên dữ liệu cũ 109 nghìn dòng và `main` cũ. Commit ghi F1 0,958, nhưng `model_card.json` ghi luật 0,89, ML 0,77: phải thống nhất. Chưa ghi ai gán 500 nhãn. Nhánh gộp cả CV13 |
| 12 | Aggregates + Q1–Q5 | 🔀 | `src/analysis/`: kiểm tra đầu vào, aggregates, Q1–Q5, bootstrap-t theo cụm video, Holm, test + dữ liệu demo (Hải Minh, nhánh `task12`, 09/11). Có sửa `docs/EDA_requirement.md` (1.3–1.6, bảng kiểm định), file này đã bị xóa trên `main` | Chờ `aspect_mentions` thật. Tham số để ở `config/analysis.yaml`. `expected_model_version: rule-v0` đang trỏ tới dữ liệu seed giả của CV3 |
| 13 | Dashboard | 🔀 | API REST + dashboard 4 tab (nhánh `nlquan`, 28/10) | Bản nháp `src/serving/` trên `main` đã xóa ngày 11/11, nhưng `nlquan` và `task12` vẫn sửa `src/serving/dashboard/index.html`: merge sẽ xung đột |
| 14 | Báo cáo | ⚠️ | File "Đánh giá tính khả thi" (Claude Docs, 08/11). Bản báo cáo 21/10 đã bỏ (11/11) | Chưa có báo cáo nào trong repo |
| 15 | Nguồn ngoài YouTube | ❌ | | |
| — | Crawler | ✅ ⚠️ | Code, config và dữ liệu của lần crawl ra bản v4 (gộp từ yt-crawler 11/11): schema v3 với 6 trường `author_*`, 50 kênh, chia việc cho 2 máy (`docs/huong-dan/crawl-2-may.md`), `state.db` và `videos.jsonl` để tra từng video; đặc tả [thu-thap.md](../spec/thu-thap.md) | Cửa sổ crawl bắt đầu từ `launch_date`, không phải 7 ngày trước như data-model. README crawler cấm dùng nhiều project để tăng hạn mức, nhưng cách chia 2 máy dùng 2 khóa ở 2 project (quyết định 8) |

**Vì sao `seed_db.py` (CV3) không dùng được làm dữ liệu phân tích:**
- Mệnh đề không khớp từ khóa nào bị gán mặc định `PERFORMANCE`, nên khía cạnh này phồng lên.
- Mỗi mệnh đề chỉ lấy khía cạnh khớp đầu tiên.
- Mọi mệnh đề chê đều có `defect_type`.
- `clause_idx` đếm từ 1; `target_model` = máy của video.
- `compare_with` gán cứng `ip14prm`/`s22u`; `days_since_launch` gán cứng 8; `confidence` là hằng số.

## 3. Giai đoạn

Điều kiện chuyển giai đoạn lấy từ [roadmap.md](roadmap.md#2-thứ-tự-và-phụ-thuộc).

| Giai đoạn | Điều kiện để sang giai đoạn sau | Đạt chưa |
|---|---|---|
| 0. Nền móng (4, 6) | Contract đã merge; cả nhóm chạy tiền xử lý ra cùng một file dữ liệu | ❌ Contract và dữ liệu raw v4 có; code tiền xử lý chưa có |
| 1. Dữ liệu & nhãn (1, 2, 3, 5, 15) | Có tập test gán tay với kappa ≥ 0,6; DB nạp được dữ liệu | ❌ |
| 2. Mô hình (7–11) | Mỗi mô hình có bảng F1 so với baseline luật | ❌ CV9 và CV11 có bảng, nhưng không trên tập test chung |
| 3. Kết quả (12–14) | Q1–Q5 chạy lại được từ code; báo cáo hoàn chỉnh | Code CV12 có, chờ đầu vào |

## 4. Việc tiếp theo, theo thứ tự

1. **Gộp nhánh theo thứ tự, mỗi nhánh một PR** (trưởng nhóm review):
   1. `feat/map-external-data` (CV5): độc lập, merge trước.
   2. `task12` (CV12). Nhánh này sửa `docs/EDA_requirement.md` và `src/serving/dashboard/index.html`, cả hai đã bị xóa trên `main`: quyết định giữ hay bỏ khi merge.
   3. `kien/cong-viec-9` (CV9): tách guideline sang PR của CV1; chuyển báo cáo ra khỏi `data/`.
   4. `feature/eda-dashboard-database-design` (CV3): lên contract v2; sửa `seed_db.py` hoặc ghi rõ "dữ liệu giả, chỉ để demo DB" và đổi `model_version` để không trùng `rule-v0`.
   5. `nlquan` (CV11, CV13): rebase lên `main` mới, tách 2 PR, chạy lại trên dữ liệu v4, giải quyết chỗ đụng dashboard với `task12` và với việc `main` đã xóa `src/serving/`.
2. **CV6:** viết code tiền xử lý cho dữ liệu v4, phát hành `clean_data` v4 + checksum. Xong việc này là đóng giai đoạn 0.
3. **CV1:** cả nhóm hiệu chỉnh 50 mệnh đề, chốt guideline; gán tập test ~800 mệnh đề (2 người, kappa). Lấy mẫu phân tầng theo (máy × khía cạnh), ưu tiên ô hiếm.
4. **CV7:** một file chia tập theo `video_id` + `evaluate.py` dùng chung; CV9 và CV11 chấm lại trên đó.
5. **CV10:** viết quy tắc `target_model` cho bình luận không nêu tên vào đặc tả trước, rồi mới code; thêm tên gọi tắt vào config.
6. **CV2:** ghi nguồn cho `launch_date`, bổ sung `predecessor`, chốt bộ 4 máy.
7. **CV8:** chốt một baseline luật duy nhất, rồi làm mô hình.

## 5. Quyết định đang chờ trưởng nhóm

| # | Quyết định | Lựa chọn | Ảnh hưởng tới |
|---|---|---|---|
| 1 | Cửa sổ trước ra mắt | Q1–Q5 dùng `[0, 28)` (`task12`). Phần `-7` ngày: sửa crawler rồi crawl lại, hoặc bỏ khỏi data-model | data-model, crawler |
| 2 | Bình luận không nêu tên máy | Theo comment cha → máy của video → `null` (roadmap CV10), hay để `null` ngay | Cỡ mẫu Q1–Q5, nhất là Q3, Q4 |
| 3 | `author_name` trong dữ liệu chia sẻ | Bỏ khỏi file chia sẻ, hoặc sửa yêu cầu trong README | Contract `comment-event` v3, quyền riêng tư |
| 4 | Baseline luật khía cạnh (`rule-v0`) | Chốt một bộ luật, đổi tên bộ còn lại | CV8, `seed_db`, `task12` |
| 5 | Bộ 4 máy chính thức | Chốt (CV2) | CV12 và mọi phân tích |
| 6 | Nhãn `FEATURES` của dataset ngoài | Phần cứng / phần mềm / tùy ngữ cảnh / bỏ | CV5, CV8 |
| 7 | Câu khen chê chung ("máy quá ngon") | Thêm nhãn cảm xúc chung, hay bỏ khỏi Q1 | Contract, Q1 |
| 8 | Crawl bằng 2 khóa API ở 2 project (`crawl-2-may.md`) | Tiếp tục, hay về 1 khóa và xin tăng hạn mức | Chính sách YouTube API (mục III.D), tốc độ crawl |

## 6. Số liệu và chỗ lệch đặc tả

- **Phiên bản dữ liệu** (số dòng, checksum): [thu-thap.md mục 7](../spec/thu-thap.md#7-phiên-bản-dữ-liệu). Không chép số vào sổ tay này.
- **Chỗ code chưa khớp đặc tả:** crawler ở [thu-thap.md](../spec/thu-thap.md) mục 3–5.

## 7. Cách cập nhật sổ tay

- Ai mở PR thì sửa dòng công việc của mình ở mục 2 **trong cùng PR**: trạng thái, "đã có", "còn thiếu".
- Trưởng nhóm cập nhật mục 1, 3, 4, 5 sau mỗi lần merge, ít nhất mỗi tuần một lần, và đổi ngày ở dòng "Mục đích".
- Không thêm bảng tiến độ ở chỗ khác. Thấy chỗ khác ghi trạng thái thì thay bằng link tới file này.

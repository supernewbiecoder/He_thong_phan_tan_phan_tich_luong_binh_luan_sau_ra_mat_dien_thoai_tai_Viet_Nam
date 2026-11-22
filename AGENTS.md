# Quy tắc cho trợ lý AI làm việc trong repo

> Mục đích: Luật bắt buộc cho mọi trợ lý AI (Claude Code, Codex, Cursor, Copilot, ChatGPT, Gemini…) khi đọc, sửa code, tài liệu hay dữ liệu của dự án; người trong nhóm cũng theo; cập nhật lần cuối: 2026-11-20.

Claude Code đọc file này qua `CLAUDE.md`. Codex, Cursor, Copilot tự đọc `AGENTS.md`. Dùng ChatGPT hay Gemini trên web thì dán file này vào đầu cuộc trò chuyện.

## 0. Trước khi làm

1. Đọc [README.md](README.md), [mục lục tài liệu](docs/README.md), [kế hoạch](docs/0-chung/ke-hoach.md) mục 1–3, và **đặc tả của tầng sắp sửa**.
2. Việc được giao nằm trong "quyết định đang chờ" ([kế hoạch mục 3](docs/0-chung/ke-hoach.md#3-quyết-định-đang-chờ-trưởng-nhóm), [đặc tả tầng 2 mục 7](docs/2-tien-xu-ly/dac-ta.md#7-quyết-định-đang-chờ-nhóm)) thì **dừng và hỏi người giao việc**, không tự chọn.
3. Yêu cầu mơ hồ, hay mâu thuẫn với đặc tả thì hỏi trước khi làm.

## 1. Đặc tả là nguồn chân lý

Mỗi tầng có đặc tả, ánh xạ thẳng tới code và test:

| Tầng | Đặc tả | Code | Test | Hằng phiên bản |
|---|---|---|---|---|
| 1. Thu thập | `docs/1-thu-thap/dac-ta.md` | `src/ingest/` | | `SCHEMA_VERSION` (`crawler/schema.py`) |
| 2. Tiền xử lý | `docs/2-tien-xu-ly/dac-ta*.md` | `src/processing/` | `tests/test_processing*.py` | `PIPELINE_VERSION` (`src/processing/__init__.py`) |
| 3. Gán nhãn | `docs/3-gan-nhan/dac-ta.md`, guideline | (chưa có) | | `guideline_version` (đầu file guideline) |
| 4. Suy luận, mô hình | `docs/4-mo-hinh/dac-ta*.md` | `src/models/` | `tests/test_models_*.py` | `MODEL_VERSION` (`src/models/run.py`) |
| 5. Phân tích | `docs/0-chung/muc-tieu.md`, `docs/5-phan-tich/huong-dan.md` | `src/analysis/` | `tests/test_analysis_*.py` | `AGGREGATOR_VERSION`, `ANALYSIS_VERSION` |
| Định dạng dữ liệu | `contracts/*.schema.json`, `docs/0-chung/thiet-ke-du-lieu.md` | | | `schema_version` |

- **Đổi một luật là đổi cả bốn thứ trong cùng một commit hay PR:** đặc tả, code, test, hằng phiên bản. Thiếu một thứ là chưa xong.
- Không thêm hành vi mà đặc tả không ghi. Cần hành vi mới thì viết vào đặc tả trước.
- Thấy code và đặc tả lệch nhau thì **báo lại**, không tự chọn bên nào đúng.
- Tăng phiên bản: đổi kết quả của dù chỉ một bản ghi thì tăng số nhỏ (`2.0` → `2.1`); đổi trường đầu ra hay thứ tự bước thì tăng số lớn (`2.x` → `3.0`).

## 2. Những thứ không được sửa

| Thứ | Vì sao |
|---|---|
| `docs/3-gan-nhan/huong-dan-gan-nhan.md` (guideline v0.3) | Báo cáo Công việc 9 ghi SHA-256 của nó; sửa một byte là báo cáo sai. Bản mới viết ở file khác |
| `contracts/aspect-mention.schema.json`, `docs/0-chung/thiet-ke-du-lieu.md` | Trưởng nhóm chốt giữ nguyên (20/11). Cần đổi thì đề xuất, không tự sửa |
| File raw `src/ingest/data/raw/*` | Dữ liệu gốc duy nhất. Mọi bước ghi ra file mới |
| Báo cáo đã phát hành (`docs/*/bao-cao*.md`) của người khác | Là bản ghi lịch sử; muốn đính chính thì ghi chú, không sửa số |

## 3. Dữ liệu và bí mật

- **Không commit:** `data/`, `src/ingest/data/`, `src/ingest/.env`, `*.pkl`, `*.joblib`, `state.db`. Kiểm `git status` trước khi commit.
- **Không in, không chép ra ngoài:** nội dung `.env` (API key, `AUTHOR_SALT`), `author_name`, tên kênh thật của người bình luận trong `state.db`. Báo cáo, notebook, phiếu gán chỉ dùng `author_hash`, hoặc không dùng gì.
- **Không chạy trên dữ liệu thật** khi chưa được giao. Thử code bằng `--limit` hoặc dữ liệu giả tự sinh.
- Không gửi dữ liệu bình luận cho dịch vụ ngoài (API LLM…) nếu việc được giao không yêu cầu. Khi gửi thì ghi lại model, prompt, `guideline_version`.

## 4. Số liệu và kết luận

- **Không bịa số.** Mọi con số trong tài liệu phải chạy lại được từ code trong repo, với phiên bản dữ liệu ghi rõ (số dòng, SHA-256). Chưa chạy thì để `___` và ghi "chờ chạy".
- Số ra từ luật mốc `rule-v1`, nhãn LLM, hay mô hình chưa đo trên nhãn người là **số liệu minh họa**, và phải ghi đúng chữ đó.
- Theo [muc-tieu.md mục 6](docs/0-chung/muc-tieu.md#6-quy-ước-dùng-chung-cho-mọi-câu):
  - kết luận chỉ khi có ý nghĩa thống kê sau hiệu chỉnh;
  - không có ý nghĩa thì viết "chưa đủ bằng chứng", không viết "bằng nhau";
  - kết luận phải đứng được qua các phép kiểm sai số mô hình và độ nhạy.
- Không dùng kết quả của một mô hình để chứng minh chính mô hình đó đúng.

## 5. Nhãn

- Tập test chỉ chứa nhãn người (`label_source = "human"`), gán đôi, đã phân xử ([đặc tả gán nhãn](docs/3-gan-nhan/dac-ta.md)). Nhãn LLM và nhãn luật **không bao giờ** vào tập test.
- Không huấn luyện trên bình luận thuộc video test (chia theo `video_id`).
- Gán nhãn bằng LLM thì theo guideline hiện hành ([v1](docs/3-gan-nhan/huong-dan-gan-nhan-binh-luan.md)) và ghi `label_source = "llm"`, `annotator`, `guideline_version`.

## 6. Thiết kế đã chốt (không quay lại nếu chưa có quyết định mới)

- **Đơn vị phân tích là cả bình luận** (phương án A, 20/11). Đếm theo (bình luận, máy, khía cạnh). Mỗi bộ có tối đa một lời khen và một lời chê. Mệnh đề chỉ là vị trí bằng chứng (`clause_idx`) và đơn vị chấm của luật mốc.
- **Máy được nhắc** xét cả bình luận: mệnh đề → mệnh đề trước → cả bình luận → bình luận cha → máy của video ([đặc tả suy luận mục 5](docs/4-mo-hinh/dac-ta-suy-luan.md#5-máy-được-nhắc)).
- **Chạy theo lô mỗi ngày** bằng `python -m src.run`. Streaming để sau.
- **Mô hình** chọn bằng số đo trên tập test chung. Chọn mô hình đơn giản nhất mà kết luận Q1–Q5 không khác mô hình tốt nhất. Không mặc định dùng PhoBERT.

## 7. Code

- Python 3.11. Chạy từ **gốc repo** bằng `python -m <module>` (vd `python -m src.processing.run`).
- Test: `python -m pytest tests -q`. Mọi luật mới có test dùng **câu tự soạn**, không dùng dữ liệu thật. Trước khi báo xong, chạy toàn bộ test và báo đúng kết quả.
- Đặt tên theo [quy tắc](docs/README.md#2-quy-tắc-đặt-tên):
  - code tiếng Anh, `snake_case`, đặt theo việc file làm (không đặt `task9.py`);
  - thư mục code theo tầng (`ingest`, `processing`, `models`, `analysis`, `storage`);
  - notebook `notebooks/<tầng>[_<bước>]_<việc>.ipynb`.
- Đầu mỗi file code có docstring `Mục đích: …; cập nhật lần cuối: YYYY-MM-DD.` Không để README dài trong thư mục code.
- Ghi file theo kiểu file tạm rồi đổi tên, để chạy lỗi giữa chừng không để lại file dở. Chạy lại phải ra cùng kết quả (ghi đè, không cộng dồn).

## 8. Tài liệu

- Tiếng Việt, câu ngắn, rõ. Thuật ngữ tiếng Anh chỉ dùng khi không có từ Việt quen hơn, và giải thích lần đầu dùng.
- Mỗi file `.md` mở đầu bằng `# Tiêu đề` rồi dòng `> Mục đích: …; cập nhật lần cuối: YYYY-MM-DD.` Sửa file thì đổi ngày.
- Đặt file theo [quy tắc đặt tên](docs/README.md#2-quy-tắc-đặt-tên): `docs/<n-tầng>/`, chỉ ba loại `dac-ta`, `huong-dan`, `bao-cao`. Thêm file thì thêm dòng vào [docs/README.md](docs/README.md); thêm code thì thêm vào [bản đồ code](docs/0-chung/ban-do-code.md).
- **Tiến độ chỉ ghi ở [kế hoạch mục 4](docs/0-chung/ke-hoach.md#4-tiến-độ).** Không tạo bảng trạng thái ở chỗ khác.
- Đổi tên tiêu đề thì sửa mọi link trỏ tới nó.

## 9. Git

- Làm trên branch riêng, mở PR vào `main`, có ít nhất một người review. Không push thẳng `main`. Không commit khi người giao việc chưa yêu cầu.
- Không thêm dòng ghi công AI (`Co-Authored-By: …`) vào commit hay PR.
- Không dùng lệnh phá hủy (`reset --hard`, `push --force`, xóa branch) khi chưa được đồng ý.

## 10. Khi báo cáo lại

Nói đúng: đã sửa file nào, đã chạy gì, test nào qua hay hỏng (dán kết quả), cái gì **chưa làm** hay **chưa kiểm được**. Không viết "đã xong" cho phần chưa chạy thử.

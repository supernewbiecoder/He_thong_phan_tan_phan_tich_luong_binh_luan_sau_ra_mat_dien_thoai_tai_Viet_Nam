# Quy tắc cho trợ lý AI làm việc trên nhánh `kham-pha-nhan`

> Mục đích: Luật bắt buộc cho mọi trợ lý AI (Claude Code, Codex, Cursor, Copilot, ChatGPT, Gemini…) khi làm trên nhánh khám phá nhãn; người trong nhóm cũng theo; cập nhật lần cuối: 2026-11-22.

Claude Code đọc file này qua `CLAUDE.md`. Codex, Cursor, Copilot tự đọc `AGENTS.md`. Dùng ChatGPT hay Gemini trên web thì dán file này vào đầu cuộc trò chuyện. Đây là bản rút gọn cho nhánh này. Nhánh `main` có bản đầy đủ hơn.

## 0. Trước khi làm

1. Đọc [README.md](README.md), [kế hoạch nhánh](docs/0-chung/ke-hoach.md), và đặc tả của việc sắp làm.
2. Việc nằm trong "quyết định đang chờ" ([kế hoạch mục 5](docs/0-chung/ke-hoach.md#5-quyết-định-đang-chờ-trưởng-nhóm)) thì **dừng và hỏi** người giao việc, không tự chọn.
3. Yêu cầu mơ hồ, hay mâu thuẫn với đặc tả thì hỏi trước khi làm.

## 1. Nhánh này chỉ có dữ liệu v4, EDA cấu trúc và tài liệu

- **Không thêm** code tiền xử lý, mô hình, phân tích vào nhánh này, trừ khi trưởng nhóm yêu cầu. Chúng ở nhánh `main`.
- **Không merge** nhánh này vào `main`, và không merge `main` vào nhánh này. Đây là nhánh mồ côi; đưa kết quả về `main` bằng cách chép file.
- **Đặc tả là nguồn chân lý.** [Đặc tả khám phá nhãn](docs/3-gan-nhan/dac-ta-kham-pha-nhan.md) quy định notebook `3_label_discovery`. Sửa luật thì sửa đặc tả trước, rồi mới sửa code, trong cùng commit. Thấy code và đặc tả lệch nhau thì báo lại, không tự chọn bên nào đúng.

## 2. Khám phá nhãn là việc của người

- **Mã hóa mở, gom bộ nhãn, gán nhãn là việc người làm.** AI không tự mã hóa hay gán nhãn bình luận khi chưa được yêu cầu rõ.
- Được yêu cầu gợi ý mã thì:
  - ghi rõ đó là gợi ý của AI;
  - không trộn vào phiếu của người;
  - **không bao giờ** dùng nhãn của AI để tính phân bố.
- **Không gợi ý danh sách nhãn có sẵn** (9 khía cạnh…) cho người đang mã hóa mở. Làm vậy là phá đúng mục đích của bước này.

## 3. Dữ liệu và quyền riêng tư

- **Không commit:**
  - `src/ingest/data/`, `data/`;
  - file mẫu, phiếu mã hóa;
  - output notebook có bình luận thật (chọn *Clear All Outputs* trước khi commit).

  Kiểm `git status` trước khi commit.
- **Không in, không chép ra ngoài** `author_name` và mọi thông tin định danh người viết. Phiếu mã hóa và báo cáo không có thông tin người viết.
- **Không gửi bình luận cho dịch vụ bên ngoài** (API LLM…) khi trưởng nhóm chưa đồng ý (quyết định 3 của kế hoạch).
- Chỉ chạy trên dữ liệu thật khi người giao việc yêu cầu. Thử code bằng dữ liệu giả tự sinh.

## 4. Số liệu

- **Không bịa số.** Mọi con số trong tài liệu phải chạy lại được từ code và dữ liệu của nhánh, với phiên bản dữ liệu ghi rõ. Chưa chạy thì để `___` và ghi "chờ chạy".
- Tỷ lệ tính từ mẫu thì luôn kèm khoảng tin cậy và cỡ mẫu.
- Không suy số của mẫu thành số của bộ 4 máy: mẫu lấy trên cả bộ dữ liệu.

## 5. Code và tài liệu

- Python 3.11. Notebook chạy từ thư mục `notebooks/`; `helpers.py` tự tìm gốc repo theo `config/pipeline.yaml`.
- Code tiếng Anh, `snake_case`. Đầu file code có docstring `Mục đích: …; cập nhật lần cuối: YYYY-MM-DD.`
- Tài liệu theo [quy tắc đặt tên](docs/README.md#2-quy-tắc-đặt-tên). Tiếng Việt, câu ngắn. Thêm file thì thêm dòng vào [mục lục](docs/README.md).
- Tiến độ chỉ ghi ở cột "Trạng thái" của [kế hoạch mục 3](docs/0-chung/ke-hoach.md#3-lộ-trình).

## 6. Git

- **Không push** khi trưởng nhóm chưa quyết. Không commit khi người giao việc chưa yêu cầu.
- Không thêm dòng ghi công AI (`Co-Authored-By: …`) vào commit.
- Không dùng lệnh phá hủy (`reset --hard`, `push --force`, xóa nhánh) khi chưa được đồng ý.

## 7. Khi báo cáo lại

Nói đúng: đã sửa file nào, đã chạy gì, kết quả ra sao, cái gì **chưa làm** hay **chưa kiểm được**. Không viết "đã xong" cho phần chưa chạy thử.

# Cài đặt môi trường

> Mục đích: Từng bước dựng môi trường để chạy crawler và kiểm tra dữ liệu trên máy mình, kèm các lỗi hay gặp; cập nhật lần cuối: 2026-11-11.

Làm theo thứ tự. Lệnh viết cho **PowerShell trên Windows**, chạy từ gốc repo; dùng macOS/Linux thì xem ghi chú ở từng bước.

## 1. Python

Cần **Python 3.11** (bản nhóm đã chạy thử). Kiểm tra:

```powershell
python --version
```

## 2. Môi trường ảo `.venv` (cho crawler)

`.venv/` đã có trong `.gitignore`, không bao giờ commit.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r src/ingest/requirements.txt
```

- PowerShell báo "running scripts is disabled" khi kích hoạt thì chạy một lần `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, rồi kích hoạt lại.
- `confluent-kafka` chỉ cần khi bật Kafka. Cài lỗi thì bỏ qua; crawler vẫn ghi file JSONL.

## 3. Dữ liệu

Dữ liệu không nằm trong git. Xin trưởng nhóm bộ crawl **v4** rồi đặt đúng chỗ crawler ghi ra (chi tiết: [docs/1-thu-thap/dac-ta.md mục 6](../1-thu-thap/dac-ta.md#6-nơi-lưu)):

```text
src/ingest/data/raw/comments.jsonl    bình luận (bắt buộc)
src/ingest/data/raw/videos.jsonl      tên video, kênh, ngày đăng
src/ingest/data/state.db              trạng thái crawl, để tra vì sao một video không được crawl
```

`state.db` chứa channel ID và tên thật của người bình luận: **không gửi tiếp cho ai, không đưa lên mạng**.

Kiểm tra đúng bản: số dòng và SHA-256 phải khớp bảng ở [thu-thap.md mục 7](../1-thu-thap/dac-ta.md#7-phiên-bản-dữ-liệu).

## 4. File bí mật `.env` (chỉ người chạy crawler)

```powershell
Copy-Item src/ingest/.env.example src/ingest/.env
```

Mở `src/ingest/.env` và điền:

- `YOUTUBE_API_KEY`: khóa YouTube Data API v3 của mình.
- `AUTHOR_SALT`: **xin trưởng nhóm**. Cả nhóm dùng chung một giá trị; sai thì `author_hash` không gộp được với dữ liệu cũ.
- `CRAWLER_WORKER`: `p1` hoặc `p2`, xem [huong-dan-crawl-2-may.md](../1-thu-thap/huong-dan-crawl-2-may.md).

`.env` đã bị `.gitignore` chặn. Không dán nội dung file này vào chat, issue hay PR.

## 5. Kiểm tra cài đặt

```powershell
cd src/ingest; python -m crawler.main status; cd ../..     # crawler: số video, hạn mức
cd src/ingest; python check_data.py; cd ../..              # dữ liệu ở bước 3: dòng hỏng, trùng, sai schema
```

Chạy không lỗi là xong.

## 6. Lỗi hay gặp

| Hiện tượng | Cách sửa |
|---|---|
| `UnicodeEncodeError: 'charmap' codec…` khi chạy script trong terminal Windows | Chạy `$env:PYTHONIOENCODING="utf-8"` trong cửa sổ đó rồi chạy lại |
| `ModuleNotFoundError: crawler` | Phải `cd src/ingest` trước, rồi `python -m crawler.main …` |
| `ModuleNotFoundError: requests` (hay `yaml`, `dotenv`) | Chưa kích hoạt `.venv` hoặc chưa cài ở bước 2 |
| Sơ đồ Mermaid trong Markdown preview của VS Code biến mất | `Ctrl+Shift+P` → **Markdown: Refresh Preview**, hoặc đóng rồi mở lại preview (`Ctrl+Shift+V`). Trên GitHub thì tải lại trang |

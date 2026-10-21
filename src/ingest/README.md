# yt-crawler — Crawler, lịch cào, quản lý hạn mức và Replay

Phần việc của vai trò **DE: Crawler và Replay**. Đầu ra: comment YouTube đúng schema đã chốt, đẩy vào Kafka topic `raw_comments` (khóa `video_id`) và lưu archive JSONL trong `src/ingest/data/raw/` làm nguồn cho Replay.

> **Thư mục chạy lệnh:** các lệnh `python -m src.main ...` bên dưới phải được chạy từ `src/ingest`. Code tự đọc cấu hình chung tại `config/pipeline.yaml` ở root repository, còn `.env`, SQLite và dữ liệu runtime nằm trong `src/ingest`.

## 1. Chuẩn bị (làm 1 lần)

1. **API key**: vào https://console.cloud.google.com → tạo project → *APIs & Services → Library* → bật **YouTube Data API v3** → *Credentials → Create credentials → API key*. Nên *Restrict key* chỉ cho YouTube Data API v3. Không cần OAuth vì chỉ đọc comment công khai.
2. **Môi trường** (Python 3.11+, Docker):
   ```bash
   cd src/ingest                         # PowerShell: cd src\ingest
   python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env        # điền YOUTUBE_API_KEY, AUTHOR_SALT
   docker compose -f docker-compose.dev.yml up -d        # Kafka 1 node để dev (bỏ qua nếu chưa cần Kafka)
   docker exec kafka-dev /opt/kafka/bin/kafka-topics.sh --create --topic raw_comments \
       --partitions 3 --bootstrap-server localhost:9092
   ```
   Trên PowerShell, dùng `Copy-Item .env.example .env` thay cho `cp`. Để trống `KAFKA_BOOTSTRAP` trong `.env` thì crawler chỉ ghi JSONL, vẫn dùng được.
3. **AUTHOR_SALT**: cả nhóm dùng chung một giá trị, đặt 1 lần, không commit. Đổi muối giữa chừng sẽ làm `author_hash` không khớp nhau.

## 2. Quy trình chạy

```bash
# (a) Chốt kênh: tìm ứng viên (mỗi lần search tốn 100 đơn vị, mặc định tối đa 3 lần)
python -m src.main find-channels "review <tên máy>" "so sánh <máy A> <máy B>"
#     → hoặc dùng danh sách tên ứng viên có sẵn trong config/pipeline.yaml rồi tìm ID tự động (~100 đơn vị/kênh):
python -m src.main resolve-names      # ghi gợi ý ra config/channels.suggested.yaml, PHẢI mở link kiểm tra từng kênh
#     → điền channel_id (UC... hoặc @handle), name, enabled, tags vào config/pipeline.yaml; điền models + aliases + launch_date

# (b) Tìm video (đi qua playlist uploads của kênh, KHÔNG dùng search.list)
python -m src.main discover
python -m src.main models       # kiểm tra danh sách mẫu, cửa sổ thời gian và số video mỗi mẫu
python -m src.main status       # xem số video mỗi mẫu máy → chốt mục còn mở "≥ 20 video review"

# (c) Cào thử 1 lần, rồi chạy tự động
python -m src.main crawl
python -m src.main snapshot-videos      # chụp view/like/comment của video
python -m src.main run          # scheduler: discover 6h, snapshot video 7h (giờ VN), crawl mỗi 30 phút

# (d) Replay cho demo / đo hệ thống
python -m src.main replay --speed 10 --dry-run          # in thử, không đẩy Kafka
python -m src.main replay --speed 1   --model ip15prm  # đo độ trễ p50/p95 ở 1x
python -m src.main replay --speed 10                    # đo consumer lag ở 10x
python -m src.main replay --speed 10 --strip-stats      # demo: bỏ like/reply của "tương lai"
```
Chạy bền trên Linux/macOS (không tắt khi đóng terminal): `nohup python -m src.main run > crawler.log 2>&1 &` hoặc dùng `tmux`. Trên Windows, chạy `python -m src.main run` trong PowerShell/Windows Terminal còn mở, hoặc cấu hình Task Scheduler/Windows service.

## 3. Schema v2 (nguồn sự thật: `src/schema.py`)

**`comments`** (Kafka `raw_comments`, Mongo `comments`; khóa upsert là `comment_id`)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| comment_id | string | khóa chính; consumer ghi Mongo bằng **upsert** theo trường này để xử lý lại không sinh bản sao |
| video_id | string | khóa Kafka |
| parent_id | string/null | luôn trỏ về comment gốc (YouTube chỉ có 2 tầng; trả lời ai nằm ở `@tên` trong text) |
| parent_text | string/null | **mới.** Nội dung comment gốc, làm ngữ cảnh cho reply, đỡ phải join trong Spark |
| model | string | tên mẫu theo video, lấy từ `models[].name` trong config (ví dụ `ip15prm`). Mẫu chính và đối thủ đều là một giá trị `model`; quan hệ giữa chúng nằm trong `data/models.json`. Video nhắc nhiều mẫu thì nối bằng `\|`, ví dụ `ip15prm\|ip16prm`. Luật nhận diện tên máy trong comment để ghi đè là việc của Data Science |
| source | string | **mới.** Hiện luôn là `youtube` |
| text, text_norm | string | `text_norm` do Data Science ghi |
| author_hash | string | SHA-256(salt + channel ID tác giả) |
| published_at | datetime UTC | thời gian sự kiện |
| like_count | int | số like **tại `fetched_at`** |
| reply_count | int/null | **mới.** `totalReplyCount`, chỉ có ở comment gốc |
| fetched_at | datetime UTC | **mới.** Lúc API trả số liệu |
| ingested_at | datetime UTC | lúc vào Kafka (Replay ghi đè), dùng đo độ trễ |
| schema_version | int | **mới.** Hiện là 2 |

**`videos`** (Mongo `videos`, file `src/ingest/data/raw/videos-YYYY-MM-DD.jsonl` khi dùng layout `daily`, hoặc `src/ingest/data/raw/videos.jsonl` khi dùng layout `single`): mỗi lần chụp là một dòng gồm video_id, channel_id, channel_title, title, published_at, model (cùng quy ước như trên), video_type (heuristic từ tiêu đề: review/unbox/compare/long_term), source, view_count, like_count, comment_count, fetched_at, schema_version. Dùng để chuẩn hóa (ví dụ comment trên 1.000 lượt xem), không gắn vào từng comment. Dislike đã bị ẩn khỏi API.

Lưu ý khi dùng: `like_count` và `reply_count` là ảnh chụp lúc cào lần đầu, crawler không cập nhật lại. Khi phát lại dữ liệu cũ, hai số này là số của "tương lai" so với thời điểm phát; demo dùng `replay --strip-stats` hoặc chỉ dùng chúng cho bảng xếp hạng cuối kỳ.

## 4. Hạn mức (quota)

| Phương thức | Chi phí | Dùng để |
|---|---|---|
| `commentThreads.list` | 1 / trang 100 comment | cào comment chính |
| `comments.list` | 1 / trang | lấy đủ reply của một comment |
| `playlistItems.list`, `videos.list`, `channels.list` | 1 | tìm video, lấy commentCount, giải mã kênh |
| `search.list` | **100** | chỉ để tìm kênh ứng viên |

Mặc định 10.000 đơn vị/ngày/project, reset lúc **nửa đêm giờ Thái Bình Dương** (≈ 14h hoặc 15h giờ VN tùy mùa). Ước tính: 20.000 comment ≈ 200-400 đơn vị; discover 20 kênh < 100 đơn vị. Hạn mức dư rất nhiều **nếu tránh `search.list`**.

Cơ chế trong code (`src/quota.py`):
- Đếm đơn vị **trước** mỗi request (request lỗi cũng tốn ≥ 1), lưu SQLite nên restart không mất.
- 3 lớp chặn: ngưỡng ngày (85% của 10.000), ngân sách mỗi lần chạy (600), trần số lần `search.list`/ngày (80).
- Gặp lỗi `quotaExceeded` từ API thì đánh dấu hết hạn mức cả ngày PT.
- Crawl dừng giữa chừng được: lưu `page_token` sau mỗi trang, lần sau làm tiếp; `seen` chống trùng.

Không tạo nhiều project để lách hạn mức (vi phạm điều khoản). Nếu thiếu, điền form xin tăng quota của Google.

## 5. Các điểm cần báo lại nhóm

- **Schema `model` đã đổi giá trị**: trước là `main`/`rival`/`both`, nay là tên mẫu trong config (`ip15prm`) hoặc `a|b` cho video nhiều mẫu. Kiểu vẫn là string nhưng cần báo cả 3 team; dashboard so sánh 2 mẫu thì chọn cặp mẫu cần so.
- `text` lấy từ `textDisplay` (plain text) vì API key không đọc được `textOriginal`. Có thể còn `@tên` ở đầu reply.
- `ingested_at` do Sink điền lúc ghi, Replay ghi đè khi phát lại; `fetched_at` giữ nguyên.
- Video có commentCount = 0 vẫn được cào (video mới đăng); chỉ video tắt bình luận mới bị loại.
- Giới hạn: theo dõi live chỉ bắt comment cấp 1 mới; reply mới dưới comment cũ sẽ không được bắt. Với đề tài này chấp nhận được.
- Chính sách YouTube API có yêu cầu về lưu trữ/làm mới dữ liệu; nên đọc YouTube API Services Developer Policies trước khi công bố bộ dữ liệu.

## 6. Mẫu chính, nhiều đối thủ và thêm mẫu mới (tự động, không sửa code)

```yaml
models:
  - name: ip15prm                      # nhãn ghi vào trường `model`
    aliases: ["iPhone 15 Pro Max", "ip15 pro max"]
    launch_date: "2023-09-12"
    rivals:                            # mỗi mẫu chính có thể có NHIỀU đối thủ
      - name: s24u
        aliases: ["Galaxy S24 Ultra", "S24 Ultra"]
        launch_date: "2024-01-10"      # bỏ trống thì dùng ngày của mẫu chính
      - name: xiaomi14u
        aliases: ["Xiaomi 14 Ultra"]
  - name: ip16prm
    aliases: ["iPhone 16 Pro Max"]
    launch_date: "2024-09-20"
    rivals: [s24u, {name: p9pro, aliases: ["Pixel 9 Pro"]}]   # s24u dùng lại cho mẫu chính thứ hai
```
- Thêm mẫu chính hoặc đối thủ bằng cách sửa `config/pipeline.yaml`. Nếu `run` đang chạy thì **không cần khởi động lại**: mỗi job nạp lại config, discover (6h sáng) tìm video mới rồi crawl (mỗi 30 phút) cào. Muốn chạy ngay: `discover` rồi `crawl`.
- `python -m src.main models` in cây mẫu chính, đối thủ, cửa sổ thời gian, số video đã có; đồng thời ghi **`data/models.json`** (danh sách nhóm `main -> rivals`, vai trò `roles`, `rival_of`) để dashboard biết cặp nào so với cặp nào. Quan hệ main/rival nằm trong file này chứ không nằm trong từng comment.
- Trường `model` của comment/video là tên một mẫu (`s24u`), hoặc nhiều mẫu nối bằng `|` (`ip15prm|s24u`) khi video nhắc nhiều mẫu.
- Video chỉ được nhận khi đăng trong cửa sổ của mẫu (ngày ra mắt trừ `video_window_before_days` đến hết `window_weeks` tuần), nên video so sánh đăng sau cửa sổ của mẫu cũ chỉ gắn nhãn mẫu mới. Muốn đối thủ cùng cửa sổ với mẫu chính, bỏ trống `launch_date` của đối thủ.
- Video đã cào giữ nguyên nhãn cũ khi bạn thêm alias hoặc mẫu mới (chỉ video còn `pending` mới được gắn lại nhãn).
- Thiếu `launch_date` thì quét video 365 ngày gần nhất và không giới hạn 4 tuần; nên điền để dữ liệu đúng phạm vi đề tài.
- Phát lại theo nhóm: `python -m src.main replay --group ip15prm --speed 10` (mẫu chính cùng mọi đối thủ), hoặc `--model s24u`.
- Đổi nhãn dữ liệu cũ (nhãn `main`/`rival` từ trước): `python -m src.main relabel main=ip15prm rival=s24u "both=ip15prm|s24u" --files comments-2026-10-19.jsonl videos-20261019.jsonl --dry-run`. **Luôn chỉ rõ `--files`**: các lần cào với cấu hình khác nhau cùng dùng nhãn `main`/`rival`, nên đổi hàng loạt sẽ gắn nhầm. File gốc được sao lưu vào `data/raw_backup/`.

## 7. File dữ liệu, trùng comment và `database is locked`

- **File dữ liệu không bao giờ bị ghi đè**: crawler chỉ ghi nối (append) vào cuối file. Mọi mẫu máy cào trong cùng ngày dùng chung một file, phân biệt bằng trường `model`. Tên file `comments-YYYY-MM-DD.jsonl` tính theo ngày giờ `timezone` trong config (bản cũ tính theo UTC).
- `output.layout: single` trong `config/pipeline.yaml` ghi mọi thứ vào **một** file `src/ingest/data/raw/comments.jsonl` (và `videos.jsonl`); `daily` là mỗi ngày một file theo múi giờ trong config.
- **Chỉ một tiến trình ghi tại một thời điểm.** Các lệnh `discover`, `crawl`, `run`, `snapshot-videos`, `relabel`, `dedupe`... xin khóa `src/ingest/data/crawler.lock`; nếu đã có tiến trình khác, lệnh dừng ngay và báo PID. `status`, `models`, `replay` không cần khóa. Trong `run`, các job chạy lần lượt.
- **Mỗi comment chỉ được ghi một lần.** Trước khi ghi, crawler "xí chỗ" comment_id trong bảng `seen` bằng một lệnh nguyên tử; chỉ comment xí được mới được ghi, và mọi thứ nằm trong một transaction (Kafka lỗi thì rollback, không sinh bản trùng). Kafka được gửi trước, file archive ghi sau.
- Dọn dữ liệu cũ đã bị trùng: `python -m src.main dedupe --dry-run`, rồi `python -m src.main dedupe` (hoặc `dedupe --merge` để gộp tất cả vào một file `comments.jsonl`). File gốc được sao lưu vào `data/raw_backup/`.

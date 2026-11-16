# Đặc tả thu thập dữ liệu (crawler YouTube)

> Mục đích: Quy định crawler lấy video nào, bình luận nào, ghi trường gì, lưu ở đâu, và các phiên bản dữ liệu đã phát hành; cập nhật lần cuối: 2026-11-11.

**Phạm vi:** luật mà crawler `src/ingest/crawler/` phải tuân theo. Cách chạy lệnh nằm ở [src/ingest/README.md](../../src/ingest/README.md); định dạng từng trường nằm ở contract [comment-event](../../contracts/comment-event.schema.json). File này không lặp lại hai thứ đó.

**Tham số** (`window_weeks`, `video_window_before_days`, danh sách máy, kênh, hạn mức) đều nằm trong [config/pipeline.yaml](../../config/pipeline.yaml). Đặc tả này chỉ nêu tên tham số, không chép giá trị.

## 1. Nguồn

- Chỉ YouTube, qua YouTube Data API v3. Nguồn khác: Công việc 15.
- Chỉ các kênh khai ở mục `channels` của config, có `enabled: true`.
- Mỗi kênh có thể ghi `owner`. Máy crawl có `CRAWLER_WORKER` (trong `.env`) bằng `owner` thì mới quét kênh đó; kênh không ghi `owner` thuộc `workers.default_owner`. Cách chia 2 máy: [docs/huong-dan/crawl-2-may.md](../huong-dan/crawl-2-may.md).
- **Không dùng tìm kiếm YouTube** (`search.list`, 100 đơn vị/lần) để tìm video. Tìm kiếm chỉ dùng để gợi ý kênh (`find-channels`, `resolve-names`).

## 2. Chọn video

Crawler quét danh sách video đã đăng (playlist `uploads`) của từng kênh và lưu **mọi** video quét được vào bảng `uploads` của `state.db`. Một video được chọn khi thỏa cả 3 điều kiện:

1. **Tiêu đề chứa một tên gọi** ở `aliases` của máy (không có `aliases` thì dùng `title` và mã máy). So sánh sau khi bỏ dấu, chữ thường, theo kiểu chứa chuỗi con.
2. **Tiêu đề không chứa** cụm nào ở `exclude` của máy đó.
3. **Ngày đăng video** nằm trong khoảng từ `launch_date − video_window_before_days` ngày tới `launch_date + window_weeks` tuần của máy.

Khớp nhiều máy thì `model` = các mã máy xếp A–Z nối bằng `|` (vd `ip15prm|s24u`). Máy không có `launch_date` thì quét video 365 ngày gần nhất; config phải điền đủ để tránh trường hợp này. `video_type` (`review`/`unbox`/`compare`/`long_term`) đoán từ tiêu đề, **chỉ để thống kê**, không dùng làm nhãn.

## 3. Chọn bình luận

- Lấy bình luận gốc và **toàn bộ reply** của video được chọn; reply mang `parent_id` và `parent_text` của bình luận gốc.
- Chỉ giữ bình luận đăng từ `launch_date` tới `launch_date + window_weeks` tuần của máy (video nhiều máy: hợp các khoảng). Khoảng này **bắt đầu từ ngày ra mắt**: không có bình luận nào trước `launch_date` (trong khi [data-model](data-model.md#4-aspect_mentions) cho `aggregates` lấy từ ngày −7, nên tuần trước ra mắt sẽ trống).
- Mỗi `comment_id` chỉ ghi một lần (bảng `seen`). Video tắt bình luận bị bỏ.
- `like_count`, `reply_count` là ảnh chụp lúc lấy (`fetched_at`), không cập nhật lại.

## 4. Trường ghi ra và quyền riêng tư

- Mỗi bình luận ghi đúng các trường của [contracts/comment-event.schema.json](../../contracts/comment-event.schema.json) (hiện là **v3**). Danh sách trường trong code: `crawler/schema.py`. Đổi trường thì đổi cả hai, tăng `schema_version`, báo cả nhóm.
- Mỗi video ghi một dòng vào `videos.jsonl` mỗi lần chụp số liệu (`VIDEO_FIELDS` trong `crawler/schema.py`).
- `author_hash = SHA-256(AUTHOR_SALT + channel ID người viết)`. Cả nhóm dùng **một** `AUTHOR_SALT`; đổi salt thì không gộp được người viết giữa các lần crawl.
- 6 trường `author_*` (schema v3) lấy từ tài khoản người viết. `author_is_creator = true` khi người viết là chủ kênh của video; luôn tính được từ `author_hash`.
- Channel ID và tên thật của người viết **chỉ** nằm trong `state.db` (bảng `comment_authors`, `authors`), không chia sẻ ra ngoài máy crawl. Riêng `author_name` hiện vẫn nằm trong dữ liệu chia sẻ, trái README: chờ [quyết định 3](../ke-hoach/so-tay.md#5-quyết-định-đang-chờ-trưởng-nhóm).

## 5. Hạn mức API

- Đếm đơn vị **trước** mỗi lần gọi (lỗi cũng tính), lưu trong `state.db`; ngày tính theo giờ Thái Bình Dương (giờ YouTube reset hạn mức).
- 3 lớp chặn: tổng ngày `quota.daily_limit × quota.safety_ratio`; ngân sách mỗi lần chạy `discover.run_budget_units`, `crawl.run_budget_units`; số lần tìm kiếm mỗi ngày `quota.search_daily_cap`.
- Chính sách YouTube: dữ liệu API làm mới hoặc xóa sau 30 ngày; không mở nhiều project để tăng hạn mức. Cách chia 2 máy hiện dùng 2 khóa ở 2 project: chờ [quyết định 8](../ke-hoach/so-tay.md#5-quyết-định-đang-chờ-trưởng-nhóm).

## 6. Nơi lưu

Mọi dữ liệu crawl nằm trong `src/ingest/data/` (ngoài git). Đây là **chỗ duy nhất** mọi code khác đọc dữ liệu raw:

| File | Chứa gì |
|---|---|
| `raw/comments.jsonl` | Bình luận (bố cục `output.layout: single`; `daily` thì mỗi ngày một file `comments-YYYY-MM-DD.jsonl`) |
| `raw/videos.jsonl` | Ảnh chụp số liệu video: tiêu đề, kênh, ngày đăng, lượt xem |
| `state.db` | Trạng thái crawl: kênh, mọi video của kênh, video được chọn, bình luận đã ghi, hạn mức, tài khoản người viết |
| `models.json` | Quan hệ máy chính – đối thủ, do lệnh `models` ghi ra |

## 7. Phiên bản dữ liệu

Một phiên bản = số dòng + SHA-256 của `comments.jsonl`. Cách tính (Git Bash, từ gốc repo):

```bash
wc -l src/ingest/data/raw/comments.jsonl
sha256sum src/ingest/data/raw/comments.jsonl
```

PowerShell: `Get-FileHash src/ingest/data/raw/comments.jsonl -Algorithm SHA256`.

| Phiên bản | File | Số dòng | SHA-256 | Ghi chú |
|---|---|---|---|---|
| v1.0 (cũ) | raw `comments.jsonl` | 109.344 | `976eb7e9686b2a91459422760bfea4a11e0f2e23f050eb78eaea1e4806e68950` | schema 2 |
| **v4 (hiện hành)** | raw `comments.jsonl` | 473.786 | `722d0e1e8547566b0462ccff78b17c9ce43bac3960dc4170e6f4fa3df0652b45` | schema 3; crawl 19/10–01/11/2026 bằng đúng `config/pipeline.yaml` hiện tại |

Phát hành phiên bản mới thì thêm một dòng vào bảng này, kèm config đã dùng.

## 8. Luật ↔ code

| Luật | File | Hàm / chỗ |
|---|---|---|
| Kênh và chia máy (mục 1) | `crawler/discover.py` | `resolve_channels`, `my_channel_ids` |
| Quét `uploads`, chọn video (mục 2) | `crawler/discover.py`, `crawler/models.py` | `run_discover`; `classify`, `specs` |
| Khoảng ngày video và bình luận (mục 2–3) | `crawler/models.py` | `specs` (`start`, `end`), `window` |
| Lấy bình luận, reply, chống trùng (mục 3) | `crawler/crawl.py` | `crawl_video`, `make_record` |
| Danh sách trường (mục 4) | `crawler/schema.py` | `COMMENT_FIELDS`, `VIDEO_FIELDS`, `check` |
| `author_hash`, `author_*` (mục 4) | `crawler/crawl.py`, `crawler/authors.py` | `author_hash`; `attach`, `backfill-authors` … `apply-authors` |
| Hạn mức (mục 5) | `crawler/quota.py`, `crawler/youtube.py` | `QuotaLedger` |
| Nơi lưu (mục 6) | `crawler/config.py`, `crawler/sinks.py`, `crawler/store.py` | `RAW_DIR`, `raw_path`; `Sink`; `connect` |

# Đặc tả dữ liệu v4

> Mục đích: Dữ liệu v4 là gì: lấy từ đâu, theo luật nào, gồm những file và trường nào, phiên bản, những điều phải nhớ khi đọc, và quyền riêng tư; cập nhật lần cuối: 2026-11-22.

Viết ở nhánh khám phá nhãn, chép về `main` ngày 26/11. Luật thu thập đầy đủ ở [đặc tả thu thập](dac-ta.md), code ở `src/ingest/`. Luật dưới đây tóm tắt để hiểu dữ liệu, không phải để chạy lại.

## 1. Nguồn và cách lấy

- **Nguồn:** YouTube, qua YouTube Data API v3. Chỉ các kênh khai trong mục `channels` của [config/pipeline.yaml](../../config/pipeline.yaml).
- **Chọn video:** một video được chọn khi thỏa cả 3 điều kiện:
  1. tiêu đề chứa một tên gọi trong `aliases` của máy (so sau khi bỏ dấu, chữ thường);
  2. tiêu đề không chứa cụm nào trong `exclude` của máy đó;
  3. ngày đăng video nằm trong khoảng từ `launch_date − video_window_before_days` ngày tới `launch_date + window_weeks` tuần.

  Video khớp nhiều máy thì trường `model` ghi các mã máy xếp A–Z, nối bằng `|` (vd `ip15prm|s24u`).
- **Chọn bình luận:** lấy bình luận gốc và **toàn bộ reply** của video được chọn. Chỉ giữ bình luận đăng từ `launch_date` tới `launch_date + 4 tuần` của máy (video nhiều máy thì lấy hợp các khoảng). **Không có bình luận nào trước ngày ra mắt.**
- `launch_date` là ngày công bố đầu tiên (toàn cầu, hoặc Trung Quốc với máy ra mắt ở đó trước), không phải ngày bán ở Việt Nam.
- **Thời gian crawl:** 19/10–01/11/2026, dùng đúng file `config/pipeline.yaml` trên nhánh này.

## 2. File

Mọi file dữ liệu nằm **ngoài git**, giữ đúng đường dẫn như trên `main` để notebook và `helpers.py` không phải sửa:

| File | Nội dung | Cỡ |
|---|---|---|
| `src/ingest/data/raw/comments.jsonl` | Mỗi dòng một bình luận (mục 4) | 473.786 dòng, ~388 MB |
| `src/ingest/data/raw/videos.jsonl` | Mỗi lần chụp số liệu một video là một dòng (mục 5) | ~2,2 MB |
| `src/ingest/data/models.json` | Danh mục máy và cửa sổ thời gian (mục 6) | ~80 KB |

- `state.db` của crawler (trạng thái crawl, có channel ID và tên thật người bình luận) **không có trên nhánh** và không cần cho phân tích.
- Muốn có dữ liệu: xin trưởng nhóm, đặt đúng các đường dẫn trên, rồi kiểm phiên bản theo mục 3.

## 3. Phiên bản

| Phiên bản | File | Số dòng | SHA-256 | Schema |
|---|---|---|---|---|
| **v4** | `comments.jsonl` | 473.786 | `722d0e1e8547566b0462ccff78b17c9ce43bac3960dc4170e6f4fa3df0652b45` | 3 |

Kiểm, từ gốc repo:

```bash
wc -l src/ingest/data/raw/comments.jsonl
sha256sum src/ingest/data/raw/comments.jsonl
```

PowerShell: `Get-FileHash src/ingest/data/raw/comments.jsonl -Algorithm SHA256`.

Số dòng hoặc SHA-256 khác bảng trên nghĩa là đang dùng file khác bản chung của nhóm. Mọi con số tính ra từ file đó **không** so được với số trong tài liệu.

## 4. Trường của một bình luận (`comments.jsonl`, 21 trường)

| Trường | Nghĩa | Lưu ý khi phân tích |
|---|---|---|
| `comment_id` | ID bình luận | Không trùng (Level 0) |
| `video_id` | Video chứa bình luận | Nối với `videos.jsonl` |
| `parent_id` | ID bình luận gốc nếu là reply; `null` nếu là bình luận gốc | 271.375 bình luận gốc (57,3%), 202.411 reply (42,7%) |
| `parent_text` | Nội dung bình luận gốc, chỉ có ở reply | Cần khi đọc reply: "đúng rồi" chỉ hiểu được khi xem bình luận cha |
| `model` | Mã máy **của video**; video nhiều máy nối bằng `\|` | **Không phải máy được nhắc trong bình luận** (mục 7) |
| `source` | Nguồn | Hiện luôn là `youtube` |
| `text` | Nội dung chữ | Chưa làm sạch: còn ký tự vô hình, HTML entity, khoảng trắng thừa (Level 0) |
| `text_norm` | Crawler để rỗng | Bỏ qua trên nhánh này |
| `author_hash` | SHA-256(salt + channel ID người viết) | Dùng để gộp theo người viết. Cả nhóm dùng chung một salt |
| `published_at` | Thời điểm đăng, UTC | Ngày theo giờ Việt Nam = UTC+7 |
| `like_count` | Số like lúc lấy dữ liệu | Ảnh chụp, không cập nhật lại |
| `reply_count` | Tổng số reply theo YouTube, chỉ có ở bình luận gốc | Có thể lớn hơn số reply lấy được, vì reply ngoài cửa sổ bị bỏ |
| `fetched_at` | Lúc API trả số liệu | |
| `ingested_at` | Lúc ghi vào file | |
| `schema_version` | Phiên bản định dạng | `3` |
| `author_name` | Tên hiển thị người viết (thường là `@handle`) | **Dữ liệu cá nhân** (mục 8). Notebook ẩn mặc định (`AN_COT`) |
| `author_channel_created_at` | Ngày tạo kênh của người viết | Dùng cho Q6 (tài khoản tạo sát ngày ra mắt) |
| `author_video_count` | Số video công khai của kênh người viết | |
| `author_subscriber_count` | Số người đăng ký; `null` nếu người đó ẩn | |
| `author_is_creator` | `true` nếu người viết là chủ kênh của video | Chủ kênh trả lời khán giả, không phải ý kiến người dùng |
| `author_fetched_at` | Lúc lấy các trường `author_*` | |

Số bình luận gốc và reply lấy từ output của notebook `1_raw_audit` mục 1 khi chạy trên v4.

## 5. Trường của một video (`videos.jsonl`, 13 trường)

`video_id`, `channel_id`, `channel_title`, `title`, `published_at`, `model`, `video_type`, `source`, `view_count`, `like_count`, `comment_count`, `fetched_at`, `schema_version`.

- Một video có thể có nhiều dòng (mỗi lần chụp số liệu một dòng). Dùng dòng có `fetched_at` mới nhất.
- `video_type` (`review`, `unbox`, `compare`, `long_term`) **đoán từ tiêu đề**, chỉ để thống kê, có thể sai.

## 6. Danh mục máy (`models.json`)

- `groups`: 63 nhóm, mỗi nhóm gồm một máy chính và các đối thủ.
- `models`: 139 máy. Mỗi máy có `name` (mã), `title`, `roles`, `rival_of`, `rivals`, `aliases`, `exclude`, `launch_date`, `window_start`, `window_end`.
- `window_start` là 00:00 giờ Việt Nam của ngày ra mắt, ghi theo UTC. `window_end` là 4 tuần sau đó.
- File do crawler sinh ra từ `config/pipeline.yaml`.

## 7. Điều phải nhớ khi đọc dữ liệu

1. **`model` là máy của video, không phải máy được nhắc.** Dưới video S26 Ultra, một bình luận có thể đang nói về iPhone. Muốn biết máy được nhắc thì phải đọc nội dung.
2. **Cửa sổ bắt đầu từ ngày ra mắt.** Không có bình luận trước ra mắt, nên không so trước/sau ra mắt được.
3. **Dữ liệu trải từ 11/04/2014 tới 20/10/2026 và 139 máy.** Phân bố tính trên cả bộ không đại diện riêng cho bộ 4 máy nào. Muốn số cho bộ 4 máy thì phải lọc trước.
4. **Dữ liệu chưa lọc gì:** có spam, bình luận tiếng nước ngoài, bình luận chỉ có emoji, bình luận xin quà dưới video tặng quà ([báo cáo kiểm tra dữ liệu](bao-cao-kiem-tra-du-lieu.md)).
5. **Bình luận không độc lập.** Bình luận cùng video, cùng người viết (`author_hash`) giống nhau hơn bình luận ngẫu nhiên. Tính khoảng tin cậy phải nhớ điều này.
6. `like_count`, `reply_count` là ảnh chụp lúc lấy dữ liệu, không phải số cuối cùng.

## 8. Quyền riêng tư

- `author_name` là dữ liệu cá nhân. Không in ra báo cáo, không đưa vào phiếu mã hóa, không commit output notebook có trường này.
- Dữ liệu không vào git; chia sẻ qua kho chung của nhóm, kèm SHA-256 ở mục 3.
- Chính sách YouTube API: dữ liệu lấy qua API phải làm mới hoặc xóa sau 30 ngày. Kết thúc đồ án thì xóa các bản sao không cần nữa.

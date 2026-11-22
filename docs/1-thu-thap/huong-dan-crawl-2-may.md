# Hướng dẫn cho người thứ hai (máy p2)

> Mục đích: Cách chia việc crawl cho 2 máy (2 khóa API) và gộp dữ liệu về máy tổng hợp; mọi lệnh chạy từ `src/ingest`; cập nhật lần cuối: 2026-11-11.

Mục tiêu: chia khối lượng cho 2 khóa API. Người 1 (p1) là máy **tổng hợp**: giữ dữ liệu chính, nhận dữ liệu của p2 và ghi vào dataset.

## 0. Những thứ PHẢI giống nhau giữa 2 máy
| Thứ | Vì sao |
|---|---|
| Phiên bản code (cùng commit trên git) | cùng schema v3, cùng cách xử lý |
| `config/pipeline.yaml` ở gốc repo (cùng file, lấy từ git) | cùng `models`/aliases/launch_date -> cùng nhãn `model`, cùng cửa sổ thời gian |
| `AUTHOR_SALT` trong `.env` | **bắt buộc**. Salt khác -> `author_hash` khác -> không gộp được người bình luận giữa 2 máy, `apply-authors` báo "hash lệch salt". p1 gửi salt cho p2 qua kênh riêng (không commit) |
| Múi giờ, `window_weeks`, `output.layout: single` | file đầu ra cùng dạng |

## 1. Những thứ KHÁC nhau
| Thứ | p1 | p2 |
|---|---|---|
| `YOUTUBE_API_KEY` | khóa của p1 | khóa của p2 (project Google Cloud riêng, bật YouTube Data API v3) |
| `CRAWLER_WORKER` | `p1` | `p2` |
| Kênh phụ trách | kênh không ghi `owner` (33 kênh gốc) | kênh có `owner: p2` (17 kênh bổ sung 31/10) |
| `KAFKA_BOOTSTRAP` | theo pipeline của nhóm | để trống (chỉ ghi file), p1 đẩy Kafka sau khi gộp |
| Thư mục `data/` | dữ liệu chính | bản sao `state.db` của p1 + thư mục `data/raw/` riêng |

Muốn đổi cách chia: sửa `owner:` trong `config/pipeline.yaml`, commit, cả hai `git pull`. Một kênh chỉ được có MỘT owner.

## 2. Cài đặt máy p2 (một lần)
```bash
git clone <repo của nhóm> && cd <thư mục repo>/src/ingest
python -m venv .venv && .venv\Scripts\activate          # Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env    # rồi sửa: YOUTUBE_API_KEY=<khóa p2>, AUTHOR_SALT=<salt của nhóm>, CRAWLER_WORKER=p2, KAFKA_BOOTSTRAP=
mkdir data
# chép data/state.db từ máy p1 sang (đã có sẵn video/kênh/comment đã cào -> p2 không cào lại từ đầu)
python -m crawler.main worker-init      # xóa sổ quota của p1 trong bản sao, in danh sách kênh p2 phụ trách
python -m crawler.main status
```

## 3. Việc A: tra tài khoản cho 473k comment cũ (chia đôi, mỗi máy ~6.800 đơn vị, xong trong 1 ngày)
p1 gửi p2 file `data/raw/comments.jsonl` (chỉ để đọc comment_id; KHÔNG để vào `data/raw/` của p2, ví dụ để ở `share/comments_p1.jsonl`).
```bash
# máy p2
python -m crawler.main backfill-authors --part 2/2 --ids-from share/comments_p1.jsonl
python -m crawler.main enrich-authors
python -m crawler.main authors-export                 # -> data/raw/authors-export-p2.jsonl, gửi file này cho p1
# máy p1 (song song)
python -m crawler.main backfill-authors --part 1/2
python -m crawler.main enrich-authors
python -m crawler.main authors-import <đường dẫn>/authors-export-p2.jsonl
python -m crawler.main apply-authors --dry-run && python -m crawler.main apply-authors
```
Hết quota giữa chừng: chạy lại đúng lệnh đó hôm sau, nó làm tiếp. Hai máy sẽ cùng tra khoảng 1/4 số kênh (người bình luận ở cả hai nửa), tốn thêm ~900 đơn vị nhưng không phải gửi file qua lại thêm lần nào.

## 4. Việc B: cào tiếp các kênh của p2 (hằng ngày)
`discover`, `crawl`, `snapshot-videos` trên máy p2 chỉ đụng tới video của kênh `owner: p2` (bản sao state.db có cả video của p1 nhưng bị bỏ qua).
```bash
python -m crawler.main discover          # chỉ quét 17 kênh owner: p2
python -m crawler.main crawl             # comment mới đã có sẵn 6 trường author_*
# hoặc để chạy tự động: python -m crawler.main run
```

## 5. Gộp dữ liệu về máy p1 (mỗi tuần hoặc trước khi phân tích)
```bash
# p2 gửi p1: data/raw/comments.jsonl và data/raw/videos.jsonl của p2
# máy p1: đặt tên có hậu tố để không đè file chính
copy <p2>\comments.jsonl data\raw\comments-p2.jsonl
copy <p2>\videos.jsonl   data\raw\videos-p2.jsonl
python -m crawler.main dedupe --merge     # gộp comments*.jsonl thành một comments.jsonl, bỏ comment trùng (giữ bản đầu), có sao lưu
python check_data.py
```
`videos-p2.jsonl` được đọc kèm (apply-authors và check_data đọc mọi `videos*.jsonl`; `status` chỉ thống kê video trong state.db của máy đó). Vì 2 máy cào 2 nhóm kênh khác nhau nên comment không trùng; `dedupe` chỉ là lưới an toàn. Sau khi gộp, p2 xóa `data/raw/comments.jsonl` của mình hoặc đổi tên, để lần gộp sau chỉ gửi phần mới.

## 6. Lưu ý
- **Chính sách YouTube API:** mỗi ứng dụng (API client) chỉ được dùng một project, và muốn hạn mức cao hơn thì phải xin qua quy trình audit chứ không phải mở thêm project. Chạy cùng một crawler bằng 2 project để nhân đôi hạn mức là vùng xám theo mục III.D; nhóm tự cân nhắc. Phương án tuân thủ: 1 khóa, kéo dài thời gian (việc A mất ~2 ngày thay vì 1), hoặc xin tăng quota.
- **Dữ liệu tài khoản:** chính sách yêu cầu làm mới hoặc xóa dữ liệu API sau 30 ngày (`enrich-authors --refresh-days 30`). Tên người bình luận là dữ liệu cá nhân: chỉ dùng trong nhóm, không công bố kèm kết quả.
- **Chỉ máy p1 chạy `apply-authors`, `dedupe --merge`, `repair-missing`, `relabel`** trên dữ liệu chính.

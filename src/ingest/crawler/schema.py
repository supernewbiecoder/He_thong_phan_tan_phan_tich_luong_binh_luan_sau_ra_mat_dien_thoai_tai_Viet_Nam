"""Nguồn sự thật duy nhất cho schema. Đổi trường phải tăng SCHEMA_VERSION và báo cả 3 team.
v3: thêm 6 trường tài khoản người bình luận (author_*). Dữ liệu cũ: `backfill-authors` -> `enrich-authors` -> `apply-authors`.
  author_name                tên hiển thị lúc lấy (từ 2023 YouTube thường trả về @handle)
  author_channel_created_at  ngày tạo KÊNH của người bình luận (channels.snippet.publishedAt)
  author_video_count         số video công khai của kênh đó
  author_subscriber_count    số người đăng ký; None nếu người đó ẩn
  author_is_creator          True nếu người bình luận chính là chủ kênh của video (creator/hãng/shop trả lời)
  author_fetched_at          thời điểm lấy các thông tin trên (chính sách YouTube: làm mới hoặc xóa sau 30 ngày)
Không lấy được (comment đã bị xóa, kênh bị khóa, chưa backfill) thì các trường author_* = None, riêng
author_is_creator luôn tính được từ author_hash."""
SCHEMA_VERSION = 3
AUTHOR_FIELDS = ("author_name", "author_channel_created_at", "author_video_count", "author_subscriber_count",
                 "author_is_creator", "author_fetched_at")

# Kafka topic raw_comments + Mongo collection comments (khóa upsert: comment_id)
COMMENT_FIELDS = (
    "comment_id", "video_id", "parent_id", "parent_text", "model", "source",
    "text", "text_norm", "author_hash", "published_at",
    "like_count", "reply_count", "fetched_at", "ingested_at", "schema_version",
) + AUTHOR_FIELDS

# Mongo collection videos (mỗi lần chụp số liệu là một dòng; lấy dòng fetched_at mới nhất)
VIDEO_FIELDS = (
    "video_id", "channel_id", "channel_title", "title", "published_at", "model",
    "video_type", "source", "view_count", "like_count", "comment_count",
    "fetched_at", "schema_version",
)


def check(rec, fields):
    got, want = set(rec), set(fields)
    if got != want:
        raise ValueError(f"Sai schema: thiếu {sorted(want - got)}, thừa {sorted(got - want)}")

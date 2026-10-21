"""Nguồn sự thật duy nhất cho schema. Đổi trường phải tăng SCHEMA_VERSION và báo cả 3 team."""
SCHEMA_VERSION = 2

# Kafka topic raw_comments + Mongo collection comments (khóa upsert: comment_id)
COMMENT_FIELDS = (
    "comment_id", "video_id", "parent_id", "parent_text", "model", "source",
    "text", "text_norm", "author_hash", "published_at",
    "like_count", "reply_count", "fetched_at", "ingested_at", "schema_version",
)

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

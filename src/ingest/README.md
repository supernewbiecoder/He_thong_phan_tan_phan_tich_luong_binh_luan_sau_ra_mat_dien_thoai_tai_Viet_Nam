# Ingest boundary

> Mục đích: Xác định phạm vi các collector/adapter thu thập và phát sự kiện bình luận; cập nhật lần cuối: 2026-10-21.

Đặt collector/adapters cho từng nguồn tại đây. Mỗi adapter phải:

- phát event theo `contracts/comment-event.schema.json`;
- giữ `source_comment_id` và `event_id` ổn định;
- có retry/backoff, rate-limit và metric cho request/reject;
- không ghi credential vào code hoặc log.

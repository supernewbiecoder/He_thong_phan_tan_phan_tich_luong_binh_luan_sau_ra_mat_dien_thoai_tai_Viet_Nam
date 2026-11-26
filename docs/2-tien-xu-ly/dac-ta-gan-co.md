# Đặc tả bước 2.4: gắn cờ tiếng Việt và spam

> Mục đích: Quy định cách gắn `is_vietnamese`, `is_spam`, `spam_reasons` cho từng bình luận bằng luật: dấu hiệu nào, ngưỡng nào, cái gì cố ý không tính; cập nhật lần cuối: 2026-11-20.

**Code:** `src/processing/flags.py`, hàm `gan_co` (gồm `nhan_tieng_viet`, `ly_do_spam`). **Test:** `tests/test_processing_flags.py`. Đầu vào, đầu ra và phiên bản chung của tầng 2: [dac-ta.md](dac-ta.md).

## 1. Để làm gì

Bước suy luận bỏ qua bình luận spam và bình luận không phải tiếng Việt ([thiết kế dữ liệu mục 4](../0-chung/thiet-ke-du-lieu.md#4-aspect_mentions)). Công việc 12 cũng bắt buộc file bình luận có hai cờ này. Hai cờ **tách riêng**: bình luận tiếng nước ngoài không bị tính là spam, để tỷ lệ spam báo cáo ra không lẫn chuyện ngôn ngữ.

Đây là **luật mốc, chưa đo độ chính xác.** Công việc 11 đo precision/recall bằng nhãn người của mẫu A ([đặc tả gán nhãn mục 3](../3-gan-nhan/dac-ta.md#3-mẫu-a-chất-lượng-dữ-liệu)): mẫu lấy từ dữ liệu chưa lọc, chia tầng theo chính các cờ này. Kết quả đo quyết định giữ luật hay đổi.

## 2. Đầu vào, đầu ra

- **Đầu vào:** `text_clean` (bước 2.1).
- **Đầu ra:** ba trường. Bình luận rỗng có `is_vietnamese = true`, `is_spam = false`, `spam_reasons = []`.

| Trường | Kiểu | Nội dung |
|---|---|---|
| `is_vietnamese` | bool | `false` chỉ khi có dấu hiệu là tiếng nước ngoài (mục 3) |
| `is_spam` | bool | `true` khi có ít nhất một lý do ở mục 4 |
| `spam_reasons` | string[] | Mã lý do theo thứ tự ở mục 4; rỗng nếu không phải spam |

## 3. Nhận tiếng Việt

Xét lần lượt, gặp điều kiện nào trước thì dừng. Lý do (cột 3) được đếm trong manifest.

| # | Điều kiện | Lý do | `is_vietnamese` |
|---|---|---|---|
| 1 | Có chữ cái có dấu của tiếng Việt (`à á ả … ă â đ ê ô ơ ư …`) | `co_dau_tieng_viet` | true |
| 2 | Có chữ cái không thuộc bảng chữ Latin (Hán, Hàn, Nhật, Thái, Kirin, Ả Rập…) | `chu_khac_latin` | false |
| 3 | Dưới 2 chữ "đếm được" | `khong_du_chu` | true |
| 4 | Dưới 50% chữ đếm được là âm tiết tiếng Việt gõ không dấu | `khong_dau_ngoai_ngu` | false |
| 5 | Còn lại | `khong_dau_hop_le` | true |

- **Chữ đếm được:** chữ chỉ gồm chữ cái, không có chữ số, không nằm trong danh sách từ mượn và tên hãng hay gặp (`TU_TRUNG_TINH`: iphone, samsung, camera, video, review, game, ok…).
- **Âm tiết tiếng Việt không dấu:** khớp mẫu *phụ âm đầu (có thể không có) + 1–3 nguyên âm + phụ âm cuối (có thể không có)* (`AM_TIET_RE`), hoặc là một mục trong từ điển viết tắt của bước N6 ("ko", "dc", "j"…).
- **Vì sao "không đủ chữ" tính là tiếng Việt:** dữ liệu lấy từ kênh tiếng Việt. Bình luận chỉ có emoji, chỉ có tên máy ("iPhone 17 Pro Max"), hay một chữ ("wow") không đủ để kết luận là tiếng nước ngoài. Các bình luận này cũng không tạo mention nào.

| Ví dụ | Kết quả |
|---|---|
| "Pin trâu quá" | true (`co_dau_tieng_viet`) |
| "pin trau qua", "ko dc j het", "iphone dep qua" | true (`khong_dau_hop_le`) |
| "nice phone bro", "the best phone ever" | false (`khong_dau_ngoai_ngu`) |
| "这个手机很好" | false (`chu_khac_latin`) |
| "😂😂", "iPhone 17 Pro Max", "wow" | true (`khong_du_chu`) |

## 4. Spam

Chỉ gắn khi có dấu hiệu quảng cáo, lừa đảo rõ ràng: **ưu tiên chính xác hơn bao phủ**, vì gắn nhầm là mất một lời chê thật.

| Lý do | Luật | Ví dụ |
|---|---|---|
| `lien_ket` | Link có `http(s)://` hoặc `www.`, hoặc link rút gọn (`bit.ly`, `t.me`, `zalo.me`, `shope.ee`…) | "xem tại https://…", "bit.ly/abc" |
| `so_dien_thoai` | Số di động Việt Nam, cùng mẫu với token `<phone>` của bước N1 | "0912 345 678" |
| `moi_lien_he` | Mời liên hệ ngoài: "add/qua/kb/ib zalo", "zalo: 09…", "telegram", "hotline", "ib cho mình/shop…" | "ib cho mình nhé" |
| `co_bac_lua_dao` | Cờ bạc, kiếm tiền, vay tiền: "tài xỉu", "nhà cái", "nổ hũ", "kiếm tiền online", "việc nhẹ lương cao", "app vay"… (có cả bản không dấu) | "chơi tài xỉu uy tín" |

**Cố ý không tính là spam:**

| Trường hợp | Vì sao |
|---|---|
| Tên miền trần ("tgdd.vn", "cellphones.com.vn") | Thường là nhắc cửa hàng khi bàn giá, bảo hành |
| "shopee", "lazada", "voucher", "sale" | Hay gặp trong bàn giá thật ("mua trên shopee rẻ hơn") |
| "zalo", "tele" đứng riêng | "zalo bị lag", "camera tele": không phải mời liên hệ |
| Chữ kéo dài, emoji lặp ("đẹp quáaaaa 😍😍😍") | Là cách nói, bước N4 đã rút gọn |
| Bình luận chỉ có emoji, không có chữ | Không phải spam, chỉ là không có nội dung |
| Tiếng nước ngoài | Đã có cờ `is_vietnamese` riêng |
| Câu trùng nhau từ nhiều tài khoản, đăng dồn | Là dấu hiệu phối hợp của Q6 (bài toán B8), xét theo nhiều bình luận cùng lúc, không phải luật trên từng bình luận |
| Bình luận xin quà dưới video tặng quà | Chờ quyết định 3 ở [đặc tả tầng 2 mục 7](dac-ta.md#7-quyết-định-đang-chờ-nhóm) |

Bộ luật cũ ở commit `59e2d16` (`cleaner/spam_detector.py`) không dùng lại nguyên vẹn. Nó có ba lỗi:
- tập chữ tiếng Việt chứa cả `a e i o u` không dấu, nên gần như mọi bình luận chữ Latin đều thành "tiếng Việt";
- gộp tiếng nước ngoài, bình luận chỉ có emoji và chữ kéo dài vào spam;
- coi "shopee", "voucher" là spam.

Bước này chỉ giữ lại hai danh sách mời liên hệ và cờ bạc của bộ luật cũ, có sửa.

## 5. Giới hạn đã biết

- Câu tiếng Anh ngắn toàn chữ ngắn có thể lọt thành tiếng Việt ("i love it": "i", "it" khớp mẫu âm tiết).
- Tiếng Pháp, Tây Ban Nha có chữ có dấu trùng tiếng Việt ("é", "à") bị tính là tiếng Việt. Gần như không gặp trong dữ liệu.
- Spam viết lách luật ("O9I2…", "za.lo") bị bỏ sót.

## 6. Tham số

| Tham số | Ở đâu | Mặc định |
|---|---|---|
| `NGUONG_AM_TIET` | `flags.py` | `0.5` |
| `TU_TRUNG_TINH` | `flags.py` | như mục 3 |
| Các regex `LIEN_KET_RE`, `MOI_LIEN_HE_RE`, `CO_BAC_LUA_DAO_RE` | `flags.py` | như mục 4 |

Đổi tham số là đổi kết quả: tăng `PIPELINE_VERSION`, sửa test, sửa đặc tả này.

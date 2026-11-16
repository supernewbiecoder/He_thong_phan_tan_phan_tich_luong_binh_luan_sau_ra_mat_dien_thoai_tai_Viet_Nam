# Hướng dẫn gán nhãn spam (Công việc 11)

> Mục đích: Định nghĩa nhãn spam / không spam và ngôn ngữ cho bình luận, để mọi người gán giống nhau; phiên bản `spam-guideline-v1.1`, cập nhật lần cuối: 2026-11-17.

## 1. Gán nhãn để làm gì

Bộ lọc spam chạy **trước** bước tách khía cạnh và cảm xúc. Bình luận bị coi là spam sẽ bị loại khỏi mọi thống kê Q1–Q5. Vì vậy:

- Loại nhầm một ý kiến thật (đặc biệt là lời chê) làm lệch kết quả phân tích.
- Giữ nhầm một bình luận vô thưởng vô phạt gần như không sao, vì nó không sinh ra mention nào.

**Nguyên tắc chung: khi phân vân, gán `ham`.**

## 2. Mỗi bình luận gán ba trường

| Trường | Giá trị | Ý nghĩa |
|---|---|---|
| `label` | `spam` / `ham` | Có phải spam không |
| `spam_type` | xem mục 3 | Chỉ điền khi `label = spam` |
| `lang` | `vi` / `other` / `none` | Ngôn ngữ của nội dung, **độc lập** với `label` |

"Không phải tiếng Việt" **không phải** là spam. Một bình luận tiếng Anh nghiêm túc là `ham` + `other`; một quảng cáo tiếng Việt là `spam` + `vi`.

## 3. Thế nào là spam

Bình luận là `spam` khi **mục đích chính không phải trao đổi về sản phẩm hay video**, mà thuộc một trong các loại:

| `spam_type` | Định nghĩa | Ví dụ |
|---|---|---|
| `ad` | Quảng cáo, bán hàng, dẫn link mua, mã giảm giá, affiliate; kể cả do chủ kênh hoặc cửa hàng tài trợ đăng | "Tham khảo iPhone 13 Pro Max chỉ từ 26,9 triệu: https://…", "Mua ở davis.vn nhập code TONYPHUNG giảm 10%" |
| `contact_sale` | Cá nhân rao bán, thu mua, mời liên hệ qua SĐT/Zalo/inbox | "S21 Ultra 22 triệu full box ai lấy ib mình 0362…" |
| `scam` | Cờ bạc, lừa đảo, kiếm tiền online, nội dung mồi nhử dán hàng loạt | "kiếm 500k mỗi ngày tại nhà, vào link…" |
| `channel_promo` | Kéo sub, kéo view cho kênh hoặc video khác; link trần không kèm nội dung | "ghé kênh mình ủng hộ nhé", "https://youtu.be/…" (chỉ có link) |
| `flood` | Chuỗi ký tự gõ bừa, lặp một từ/câu hàng loạt mà không có ý kiến nào | "gftrwtrrrrrttttttt…", "éc éc éc éc éc" |
| `other` | Spam không thuộc các loại trên; ghi chú lý do | |

## 4. Những trường hợp KHÔNG phải spam (`ham`)

| Trường hợp | Ví dụ | Vì sao |
|---|---|---|
| Kéo dài ký tự, nhiều dấu câu hoặc emoji để biểu cảm | "đẹp quáaaaaaa", "như con gà cạnh con công =]]]]]]]", "chết luôn rồi hay sao??????" | Vẫn là ý kiến thật |
| Nhắc tên sàn, cửa hàng, ứng dụng trong câu chuyện thật | "Lazada đang sale còn 26tr", "nhu cầu nghe gọi FB, Zalo, TikTok" | Không mời ai mua, không kèm liên hệ |
| Hỏi xin tư vấn, hỏi chỗ mua, xin link | "Xin link mua cái đồng hồ anh đeo", "tầm 7 triệu nên mua máy nào ạ" | Người xem hỏi thật |
| Tham gia minigame theo yêu cầu của kênh, dù có SĐT hay link Facebook | "SĐT: 09… Dự đoán: A là iPhone 6, B là Note 4. Nhận xét: …" | Kênh yêu cầu, thường kèm nhận xét thật |
| Dẫn link **kèm nội dung thảo luận liên quan** | "bên GSMArena đo pin được 110 giờ nè: https://…" | Link là dẫn chứng |
| Cùng một câu hỏi hay ý kiến thật được dán ở nhiều video | "Anh ơi tầm giá dưới 7 triệu nên mua Samsung nào…" (xuất hiện 3 lần) | Lặp nhưng vẫn là nhu cầu thật; ghi chú `dup` |
| Bình luận ngắn, ít thông tin | "Cmt đầu", "hay quá", "👍", "7:10 :))", "Lg v30" | Nhiễu, không phải spam |
| Lạc đề, đùa, chửi bới, công kích cá nhân | "nghe cái giọng muốn tắt video" | Độc hại là bài toán khác, không phải spam |
| Xin like, xin máy | "ai đồng ý cho 1 like", "anh có máy nào không dùng thì cho em" | Nhiễu, không quảng bá cho bên thứ ba |
| Bình luận bằng ngôn ngữ khác | "Great review, thanks!" | `ham` + `lang = other` |

## 5. Trường `lang`

| Giá trị | Khi nào |
|---|---|
| `vi` | Có nội dung tiếng Việt: có dấu, không dấu, teencode, hoặc tiếng Việt xen từ tiếng Anh ("pin trau vl", "camera ok nhưng giá chát") |
| `other` | Nội dung là một ngôn ngữ khác hẳn (câu tiếng Anh, tiếng Trung, tiếng Nga…), không có phần tiếng Việt |
| `none` | Không xác định được ngôn ngữ: chỉ emoji, dấu câu, số, mốc thời gian, tên máy hay tên riêng, hoặc từ dùng chung quốc tế ("ok", "wow", "haha", "tks", "first", "iPhone 12 Pro Max") |

Bình luận trộn nhiều ngôn ngữ: có một cụm tiếng Việt có nghĩa thì gán `vi`.

## 6. Ca khó

- **Chủ kênh ghim bình luận kèm link cửa hàng tài trợ:** `spam` / `ad`. Đây là nội dung quảng bá, không phải ý kiến người dùng.
- **Chủ kênh trả lời người xem bình thường:** `ham`. (Việc loại bình luận của chủ kênh khỏi `aggregates` do trường `author_is_creator` đảm nhiệm, không phải bộ lọc spam.)
- **Vừa có ý kiến thật vừa rao bán:** xét mục đích chính. "Máy dùng ngon, pin trâu. Ai cần mua lại ib 09…" → `spam` / `contact_sale` vì phần ý kiến chỉ để dẫn vào lời rao.
- **Nhắc tới kênh khác để so sánh hay chê:** `ham` ("kênh X review kỹ hơn nhiều").
- **Một đoạn văn lạ dán nguyên văn nhiều lần, không liên quan điện thoại, có vẻ để gây chú ý hay mồi nhử:** `spam` / `scam` hoặc `flood`.
- **Bình luận là phản hồi (reply):** đọc cả bình luận cha để hiểu ngữ cảnh. "0912… nhé" trả lời câu "cho mình xin số" là rao/liên hệ → `spam` / `contact_sale` nếu là người bán; nếu chỉ là hai người xem trao đổi riêng thì `ham`.
- **Chỉ có hashtag:** `ham` + `none` nếu là tên máy/kênh; `spam` / `ad` nếu là hashtag của cửa hàng kèm lời mời mua.

## 7. Quy tắc bổ sung sau vòng gán độc lập (v1.1)

Hai người gán độc lập lệch nhau ở 15/640 dòng. Các quy tắc dưới đây là kết quả phân giải, áp dụng cho mọi lần gán sau.

1. **Đoạn văn dán nguyên văn ở nhiều video để gây chú ý** (không liên quan điện thoại): `spam` / `flood`. Chỉ dùng `scam` khi có mồi nhử dẫn tới hành động: link, liên hệ, chuyển tiền.
2. **Link kèm vài chữ chú thích, không có ý kiến và không trả lời câu hỏi nào** ("Phần 2 đây nhé mọi người + link"): `spam` / `channel_promo`, kể cả khi do chủ kênh đăng. Link trả lời đúng điều bình luận cha hỏi, hoặc kèm nhận xét/câu đùa về video: `ham`.
3. **Ngưỡng `flood`:** cùng một âm hoặc từ vô nghĩa lặp từ 5 lần, hoặc chuỗi gõ bừa từ 8 ký tự. Ngắn hơn ("Ghj", "Xx") là `ham`.
4. **Chửi bới lặp nhiều lần:** `ham`. Nội dung độc hại vẫn là ý kiến của người viết; "độc hại" được ưu tiên hơn "lặp".
5. **`lang` cho nội dung ngắn:** viết tắt tiếng Việt ("vl", "cc", "dkm") và giá kèm đơn vị tiếng Việt ("38tr", "10 củ") là `vi`. "Cmt 1", link trần, tên máy kèm link là `none`.
6. **Số điện thoại không kèm lời rao hay lời mời liên hệ:** `ham`.
7. **Xin đăng ký kênh:** `spam` / `channel_promo`, khác với xin like (`ham`), vì mục đích là quảng bá một kênh.

## 8. Quy trình

1. Mẫu 640 bình luận được rút theo tầng bằng [`sampling.py`](../src/processing/spam/sampling.py). Người gán **không** được xem tầng hay kết quả của bộ luật.
2. Hai người gán độc lập toàn bộ mẫu. Tính Cohen's kappa cho `label`.
3. Các dòng hai người lệch nhau do người thứ ba quyết định.
4. Tập test chỉ được dùng để báo cáo chính thức khi nhãn đã có người duyệt (`label_source = human`), theo [ml-training.md](ml-training.md#4-gán-nhãn). Nhãn do AI gán ghi `label_source = llm`.

Cách chạy từng bước: [src/processing/spam/README.md](../src/processing/spam/README.md).

Đổi định nghĩa ở file này thì tăng số phiên bản guideline và gán lại các dòng bị ảnh hưởng.

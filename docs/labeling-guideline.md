# Quy tắc gán nhãn (Labeling Guideline)

> Mục đích: Quy định cách gán khía cạnh và cảm xúc cho từng mệnh đề bình luận về điện thoại, dùng cho dữ liệu huấn luyện mô hình cảm xúc (Công việc 9); cập nhật lần cuối: 2026-11-04 (v0.3).

**`guideline_version`: `v0.3`** (bản nháp, đã chỉnh sau hai lần thử 200 mệnh đề với Gemini; chưa qua bước hiệu chỉnh 50 mệnh đề của cả nhóm; xem mục 11 và lịch sử thay đổi).

Mã khía cạnh và mã cảm xúc lấy đúng từ [data-model.md](data-model.md#danh-mục-mã). Không tự đặt mã mới.

## 1. Phạm vi và nguyên tắc chung

1. **Đơn vị gán nhãn là một mệnh đề** (một phần tử trong `clauses` của `clean_data.jsonl`), không phải cả bình luận.
2. Mỗi mệnh đề có thể có **0, 1 hoặc nhiều khía cạnh**.
3. **Mỗi khía cạnh được gán có đúng một nhãn cảm xúc** (`pos`, `neg` hoặc `neu`). Không gán hai nhãn cho cùng một khía cạnh trong cùng một mệnh đề.
4. Cảm xúc là **thái độ của người viết đối với khía cạnh đó của chiếc điện thoại**, không phải thái độ chung của cả câu, không phải cảm xúc với người review, hãng hay người bán.
5. **Chỉ dựa vào những gì được viết.** Không suy diễn từ tên video, tên máy hay kiến thức riêng. Khi không chắc, giữ nhãn khả dĩ nhất và đặt `uncertain = true` (mục 8).
6. Mọi nhãn do LLM gán đều ghi `label_source = "llm"`. Đây **không phải gold label**, không dùng để chấm điểm mô hình.
7. **Ưu tiên chính xác hơn bao phủ (từ v0.2).** Khi do dự giữa "gán thêm" và "không gán", **không gán**. Dữ liệu huấn luyện nhiều nhãn thừa gây hại hơn thiếu một vài nhãn.

### Quy tắc "bằng chứng rõ ràng" (thêm ở v0.2)

Một cặp (khía cạnh, cảm xúc) chỉ được gán khi **chính mệnh đề** (`clause_text`) nêu khía cạnh đó. Lần thử 200 mệnh đề cho thấy lỗi phổ biến nhất là gán thừa, nên các quy tắc dưới đây có hiệu lực **trước** mọi quy tắc khác.

**(a) Trả `aspects = []` khi:**

| Trường hợp | Ví dụ | Kết quả |
|---|---|---|
| Chỉ nhắc tên người, hoặc câu cực ngắn/từ đệm không nêu khía cạnh | "@bạch-ngọc", "vậy", "ừ", "đúng rồi", "ok", "thật" | `[]` |
| Câu tường thuật/báo cáo, không đánh giá điện thoại | "admin chưa ghi nhận máy bị lỗi bạn nha" | `[]` |
| Không phải điện thoại: tai nghe, laptop, đồng hồ, máy tính bảng, ốp lưng, phụ kiện | "4tr 1 đôi tai nghe" | `[]` |
| Số tiền đứng một mình, không rõ là giá của điện thoại | "3 tr" | `[]` |
| Chỉ nêu thuật ngữ/tên tính năng, không đánh giá và không rõ ngữ cảnh | "ois this ois that" | `[]` |
| Chỉ nhắc tên một nhóm khía cạnh chung, không nói gì cụ thể | "phần cứng nhé bạn" | `[]` |
| Phụ kiện: kính cường lực, ốp lưng, dán màn hình (kể cả khi chê chúng khó mua/khó dùng) | "mua s22ultra về hỏi đâu cũng không có kính cường lực" | `[]` |

**(b) Không gán khía cạnh chỉ vì có từ khóa.** Phải đọc xem mệnh đề **đánh giá điều gì**:
- "và vào game vẫn bị 2 hóc đen 2 đầu" → `DISPLAY/neg` (từ "game" chỉ là bối cảnh, **không** thêm `PERFORMANCE`).
- "chắc phải lên dùng 14prm 138 sợ không đủ dùng" (nói về dung lượng lưu trữ) → `HARDWARE_OTHER/neu` + `uncertain`, **không** phải `BATTERY`.
- "vào game vẫn mượt" → `PERFORMANCE/pos` (đối chiếu: ở đây mệnh đề đánh giá hiệu năng).

**(c) Cảm xúc phải có bằng chứng.** Chỉ gán `pos`/`neg` khi mệnh đề có từ đánh giá hoặc hàm ý rõ ("dùng 2 ngày mới sạc", "sạc 3 tiếng mới đầy"). Chỉ nêu chất liệu, thông số, tên tính năng thì là `neu` nếu khía cạnh rõ ("mặt lưng kính", "nhôm", "30gr", "camera 200MP"), còn không rõ khía cạnh thì `[]`.

**(c2) Số tiền đi kèm tên phiên bản.** Dung lượng trong tên phiên bản không phải đánh giá bộ nhớ: "trc mua con n10+ bản 256gb 27 củ" → `PRICE/neu` (**không** thêm `HARDWARE_OTHER`, và không bỏ sót `PRICE`).

**(d) `uncertain` không thay cho việc để trống.** Nếu bạn định đặt `uncertain = true` vì mệnh đề gần như không có nội dung, hãy trả `[]`.

## 2. Chín khía cạnh

| Mã | Gán khi mệnh đề nói về | Ví dụ từ khóa/ý |
|---|---|---|
| `BATTERY` | dung lượng pin, thời lượng dùng, tốc độ sạc, sạc không dây, tụt pin | "pin trâu", "sạc nhanh", "tụt pin" |
| `DISPLAY` | độ sáng, màu sắc, tần số quét, kích thước, độ phân giải, chất lượng màn | "màn đẹp", "120Hz", "màn hơi tối" |
| `PERFORMANCE` | chip, độ mượt, chơi game, RAM, **nhiệt độ/nóng máy**, giật lag | "mượt", "lag", "nóng", "chiến game tốt" |
| `CAMERA` | chụp, quay, zoom, selfie, chụp đêm, chất lượng ảnh | "chụp đẹp", "quay rung", "zoom xa" |
| `DESIGN` | ngoại hình, chất liệu, trọng lượng, cầm nắm, **độ bền**, **chống nước** | "cầm nặng tay", "thiết kế đẹp", "dễ trầy" |
| `SOFTWARE` | hệ điều hành, giao diện, cập nhật, tính năng phần mềm, AI | "One UI mượt", "update lỗi", "AI dịch live" |
| `HARDWARE_OTHER` | loa, rung, vân tay, Face ID, sóng, wifi, bộ nhớ, bút | "loa to", "mất sóng", "Face ID nhạy" |
| `PRICE` | giá bán, đáng tiền, giữ giá, khuyến mãi | "giá cao", "đáng tiền", "xuống giá nhanh" |
| `WARRANTY` | bảo hành, sửa chữa, cửa hàng, chính hãng/xách tay, hậu mãi | "bảo hành tốt", "hàng xách tay", "trung tâm sửa lâu" |

### Ranh giới dễ nhầm (quyết định cố định)

| Trường hợp | Gán vào | Lý do |
|---|---|---|
| Nóng máy, hâm hấp, throttle | `PERFORMANCE` | theo data-model |
| Nóng khi **sạc** ("sạc nóng quá") | `PERFORMANCE` (nóng) và `BATTERY` nếu nói rõ về sạc chậm/nhanh | nêu hai khía cạnh chỉ khi mệnh đề thật sự nhắc cả hai |
| Chống nước, bụi, trầy xước, cong vênh, độ bền | `DESIGN` | theo data-model |
| Tần số quét, độ sáng, màu | `DISPLAY` | |
| Mượt khi cuộn/vuốt do tần số quét | `DISPLAY` nếu nhắc "Hz/tần số quét", ngược lại `PERFORMANCE` | |
| Giao diện, hệ điều hành, cập nhật, AI | `SOFTWARE` | |
| Bộ nhớ trong, khe thẻ nhớ | `HARDWARE_OTHER` | |
| Chip, RAM | `PERFORMANCE` | |
| "Hàng chính hãng / xách tay", cửa hàng bán | `WARRANTY` | |
| "Giá bảo hành/sửa đắt" | `WARRANTY` (không phải `PRICE`) | nói về hậu mãi |
| "Giá máy cao", "giảm giá", "đáng tiền" | `PRICE` | |
| Nhận xét chung "máy tốt/dở" không nêu mặt nào | **không có khía cạnh** | không gán tạm cho khía cạnh nào |

> Phần định nghĩa này chỉ gán khía cạnh khi mệnh đề **nhắc trực tiếp hoặc ngụ ý rõ ràng** (ví dụ "cầm đã tay" → `DESIGN`). Nếu phải đoán mới ra khía cạnh, không gán.

## 3. Ba nhãn cảm xúc

| Nhãn | Dùng khi | Ví dụ |
|---|---|---|
| `pos` | khen, đánh giá tích cực, hài lòng | "pin trâu thật sự" |
| `neg` | chê, đánh giá tiêu cực, phàn nàn, báo lỗi | "máy nóng kinh khủng" |
| `neu` | **câu hỏi**, mô tả trung tính, nêu thông số, không rõ thái độ | "pin 5000mAh", "màn có bị chớp không ae?" |

Quy tắc bổ sung:
- Chỉ nêu sự việc nhưng hàm ý rõ khen/chê thì gán theo hàm ý ("dùng 2 ngày mới sạc" → `BATTERY/pos`; "sạc 3 tiếng mới đầy" → `BATTERY/neg`).
- Chỉ nêu thông số không kèm đánh giá → `neu` ("camera 200MP").
- Mức độ mạnh/nhẹ không đổi nhãn: "hơi nóng" vẫn là `neg`, "tạm ổn" là `neu` hoặc `pos` tùy ngữ cảnh (xem "tạm được" ở mục 8).

## 4. Số lượng khía cạnh trong một mệnh đề

- **0 khía cạnh:** mệnh đề không nói về mặt nào của máy. Ghi `aspects = []`. Ví dụ: "cảm ơn anh review", "mình ở Hà Nội", "bao giờ ra mắt vậy?", "máy này tốt".
- **1 khía cạnh:** trường hợp phổ biến.
- **Nhiều khía cạnh:** mỗi khía cạnh một cặp, **mỗi cặp có cảm xúc riêng**.

| Mệnh đề | Kết quả |
|---|---|
| "máy nóng và pin tụt nhanh" | `PERFORMANCE/neg`, `BATTERY/neg` |
| "màn đẹp nhưng pin yếu" | `DISPLAY/pos`, `BATTERY/neg` |
| "camera đỉnh, giá hợp lý" | `CAMERA/pos`, `PRICE/pos` |

**Cùng một khía cạnh có cả khen lẫn chê trong một mệnh đề** (hiếm, thường đã bị tách): chọn nhãn của ý chính (ý sau "nhưng" thường là ý chính) và đặt `uncertain = true`; nếu không có ý nào nổi trội → `neu` + `uncertain = true`.

## 5. Phủ định

Đọc đúng nghĩa cuối cùng sau khi áp dụng phủ định. **Luôn xét phủ định trước khi gán nhãn.**

| Mệnh đề | Kết quả | Ghi chú |
|---|---|---|
| "không lag chút nào" | `PERFORMANCE/pos` | phủ định điều xấu = khen |
| "chẳng nóng gì cả" | `PERFORMANCE/pos` | |
| "pin không trâu" | `BATTERY/neg` | phủ định điều tốt = chê |
| "không đẹp lắm" | khía cạnh theo ngữ cảnh/`neg` | "không … lắm" giảm nhẹ mức khen → chê nhẹ |
| "không có gì để chê" | không có khía cạnh nếu không nêu mặt nào | |
| "camera không tệ" | `CAMERA/pos` (+ `uncertain = true` nếu có thể hiểu là "tạm được") | |

Lưu ý: văn bản đã bỏ dấu hoặc viết tắt (`ko`, `k` đã được chuẩn hóa thành "không" ở `text_norm`). Khi `clause_text` và `text_norm` khác nhau, **ưu tiên `text_norm`** để đọc nghĩa, nhưng chép lại nguyên `clause_text`.

## 6. Mỉa mai và nói giảm

- Chỉ coi là mỉa mai khi **có dấu hiệu rõ ràng** trong chính mệnh đề hoặc `parent_text`: khen cường điệu đối lập với sự thật hiển nhiên, "haha", "😂", "đỉnh thật đấy…" kèm lời chê trước đó.
- Gán theo **nghĩa thật**: "pin trâu ghê, 3 tiếng hết sạch" → `BATTERY/neg`.
- Không chắc có mỉa mai hay không → gán theo nghĩa đen và đặt `uncertain = true`.
- Emoji cười/khóc đơn lẻ không đủ để kết luận mỉa mai.

## 7. Câu hỏi, đồn đoán, mong muốn, so sánh

### Câu hỏi
- Câu hỏi thuần thông tin → `neu`: "pin trâu không ae?" → `BATTERY/neu`.
- Câu hỏi tu từ **nghiêng rõ về một phía** → gán theo phía đó + `uncertain = true`: "giá này ai mua nổi?" → `PRICE/neg`, `uncertain = true`.
- Câu hỏi nghi ngờ nêu lỗi ("máy mình bị nóng, có ai bị không?") → `PERFORMANCE/neg`: người viết **đã tự nêu** trải nghiệm xấu.

### Đồn đoán, nghe nói, giả định
- "Nghe nói pin yếu", "chắc là nóng" → `neu` (chưa phải trải nghiệm của người viết), trừ khi họ khẳng định đồng ý rõ ràng.
- "Ước gì pin trâu hơn", "giá mà rẻ hơn" → `neg` (bất mãn hiện tại).
- **Câu mong muốn hoặc điều kiện nêu điều máy hiện chưa đạt cũng là `neg` (kèm `uncertain` nếu mơ hồ), không phải `neu` hay `pos`** (từ v0.3):
  - "nếu rẻ như nước ngoài" → `PRICE/neg`
  - "giá như samsung cho độ sáng tầm 2k1 nits" → `DISPLAY/neg`
  - "hy vọng samsung ra con a54s chạy chip snapdragon 7 gen 1" → `PERFORMANCE/neg` + `uncertain`
  - "hoặc nếu 14 pro max mới rẻ thêm nữa là quất ổn áp" → `PRICE/neg` (giá hiện tại chưa đủ rẻ)

### Không phải khen/chê điện thoại
Không gán khía cạnh cho: khen/chê người review, video, hãng, quảng cáo, người bán; chuyện cá nhân; spam. Ví dụ: "anh review chi tiết quá" → `[]`.

### So sánh nhiều máy
Cảm xúc gán cho **máy là chủ ngữ của mệnh đề** (máy được nói đến chính).

| Mệnh đề | Kết quả | Ghi chú |
|---|---|---|
| "pin S23U trâu hơn ip14" | `BATTERY/pos` | chủ thể: S23U |
| "ip14 pin yếu hơn hẳn" | `BATTERY/neg` | chủ thể: iPhone 14 |
| "máy nào chụp đẹp hơn vậy?" | `CAMERA/neu` | câu hỏi |
| "S23U chụp đẹp nhưng ip14 quay mượt hơn" | `CAMERA/pos` + `uncertain = true` | hai máy, hai ý khác nhau; mệnh đề lẽ ra phải được tách ở bước segment |

Nếu không xác định được **một** máy chủ thể duy nhất, gán nhãn theo ý chính (thường là ý đầu hoặc ý sau "nhưng") và đặt `uncertain = true`.

Nếu một mệnh đề so sánh hai máy mà người viết **không** nêu máy nào là chủ thể (ví dụ "hai máy pin ngang nhau") → `neu`.

> Việc xác định `target_model`, `compare_with`, `compare_winner` thuộc Công việc 10, không thuộc bước này. Chỉ cần gán cảm xúc đúng với máy chủ thể của mệnh đề và đánh `uncertain` khi mơ hồ.

## 8. Thiếu ngữ cảnh và `uncertain = true`

**Khi nào dùng `parent_text`:** chỉ để hiểu đại từ/từ chỉ định ("nó", "cái đó") trong một mệnh đề **đã tự nêu** khía cạnh hoặc từ đánh giá cụ thể ("tụt nhanh", "khựng nhiều"). **Không** dùng `parent_text` để thêm khía cạnh mà mệnh đề không nhắc, và không gán nhãn cho câu đồng tình ngắn ("đúng rồi", "vậy", "chuẩn") chỉ vì bình luận cha nói về một khía cạnh (từ v0.2).

| Ví dụ | `parent_text` | Kết quả |
|---|---|---|
| "ừ nó tụt nhanh lắm" | "pin máy này sao ae?" | `BATTERY/neg` |
| "đúng rồi" | "camera chụp đẹp ghê" | `[]` (câu đồng tình ngắn; từ v0.2 không suy ra khía cạnh từ bình luận cha) |
| "vậy" | "máy này pin, camera, màn hình đều tốt" | `[]` (từ đệm, không dùng `parent_text` để thêm khía cạnh) |
| "có" | "máy nóng không?" | không thể xác định → `[]` |
| "nó tệ lắm" | (trống) | `[]` (không rõ khía cạnh) |

**Đặt `uncertain = true` khi:**
- không chắc khía cạnh hay cảm xúc, nhưng vẫn có một nhãn khả dĩ nhất;
- nghi mỉa mai nhưng chưa rõ;
- phải dựa vào `parent_text` mới hiểu được;
- hai khía cạnh gần nhau (ví dụ `DESIGN`/`HARDWARE_OTHER`) mà ranh giới ở mục 2 chưa quyết định được;
- từ nhẹ như "tạm được", "cũng được", "ổn" (có thể `neu` hoặc `pos`): gán `neu` hoặc `pos` theo giọng điệu + `uncertain = true`.

**Không được:**
- đoán khía cạnh từ tên máy, tên video, hay từ kiến thức bên ngoài;
- bịa nhãn để "lấp đầy" mệnh đề không có khía cạnh;
- dùng `uncertain = true` thay cho việc đọc kỹ; chỉ dùng khi thực sự mơ hồ.

Nếu quá mơ hồ để có nhãn khả dĩ nào (không biết khía cạnh) → `aspects = []`, **không** gán khía cạnh kèm `uncertain`.

## 9. Định dạng đầu ra

### Đầu ra gán nhãn theo mệnh đề (JSONL, mỗi dòng một mệnh đề)

```json
{
  "clause_id": "<comment_id>#<clause_idx>",
  "aspects": [
    {"aspect": "PERFORMANCE", "sentiment": "neg", "uncertain": false},
    {"aspect": "BATTERY",     "sentiment": "neg", "uncertain": false}
  ],
  "annotator": "<tên mô hình LLM>",
  "label_source": "llm",
  "guideline_version": "v0.3"
}
```

- `aspects = []` khi mệnh đề không có khía cạnh nào.
- `uncertain` thuộc từng cặp (aspect, sentiment).
- Không thêm trường ngoài danh sách trên. `uncertain` là trường mở rộng cho bước này; **chưa có trong schema `gold_labels` đã chốt** của [data-model.md](data-model.md#7-gold_labels). Nếu muốn đưa vào DB phải tăng `schema_version` và báo cả nhóm.

### Mẫu huấn luyện sau khi làm phẳng (mỗi dòng một cặp)

```json
{
  "clause_id": "abc123#0",
  "comment_id": "abc123",
  "video_id": "xyz789",
  "clause_text": "máy nóng và pin tụt nhanh",
  "aspect": "BATTERY",
  "sentiment": "neg",
  "uncertain": false,
  "label_source": "llm",
  "annotator": "<tên mô hình LLM>",
  "guideline_version": "v0.3"
}
```

Mệnh đề không có khía cạnh **không** tạo mẫu huấn luyện cảm xúc (nhưng nên giữ trong file nhãn gốc để dùng cho mô hình khía cạnh).

## 10. Bảng ví dụ tổng hợp

| # | Mệnh đề | `parent_text` | Kết quả | Lý do |
|---|---|---|---|---|
| 1 | "không lag chút nào" | | `PERFORMANCE/pos` | phủ định điều xấu |
| 2 | "máy nóng và pin tụt nhanh" | | `PERFORMANCE/neg`, `BATTERY/neg` | hai khía cạnh |
| 3 | "màn đẹp nhưng pin yếu" | | `DISPLAY/pos`, `BATTERY/neg` | hai cảm xúc khác nhau |
| 4 | "pin có trâu không mọi người?" | | `BATTERY/neu` | câu hỏi |
| 5 | "pin 5000mAh" | | `BATTERY/neu` | chỉ nêu thông số |
| 6 | "dùng cả ngày mới cần sạc" | | `BATTERY/pos` | hàm ý khen |
| 7 | "giá này ai mua nổi" | | `PRICE/neg` + `uncertain` | tu từ |
| 8 | "pin trâu ghê, 3 tiếng hết sạch" | | `BATTERY/neg` | mỉa mai rõ |
| 9 | "chống nước tốt, ngâm cả buổi vẫn ổn" | | `DESIGN/pos` | chống nước thuộc `DESIGN` |
| 10 | "Face ID nhạy, loa nghe hay" | | `HARDWARE_OTHER/pos` | gộp một khía cạnh, một nhãn |
| 11 | "update xong bị lỗi vặt hoài" | | `SOFTWARE/neg` | cập nhật |
| 12 | "bảo hành 1 đổi 1 nhanh gọn" | | `WARRANTY/pos` | |
| 13 | "hàng xách tay hơi rủi ro" | | `WARRANTY/neg` | |
| 14 | "anh review chi tiết quá" | | `[]` | không phải điện thoại |
| 15 | "ừ tụt nhanh lắm" | "pin máy sao ae?" | `BATTERY/neg` | dùng ngữ cảnh cha |
| 16 | "có" | "máy nóng không?" | `[]` | không đủ ngữ cảnh |
| 17 | "pin S23U trâu hơn ip14" | | `BATTERY/pos` | chủ thể S23U |
| 18 | "nghe nói máy nóng lắm" | | `PERFORMANCE/neu` | tin đồn |
| 19 | "giá mà rẻ hơn tí nữa" | | `PRICE/neg` | bất mãn |
| 20 | "camera tạm được" | | `CAMERA/neu` + `uncertain` | từ nhẹ, mơ hồ |
| 21 | "@bạch-ngọc" | | `[]` | chỉ nhắc tên |
| 22 | "vậy" | "máy này pin, camera, màn hình đều tốt" | `[]` | từ đệm; không dùng `parent_text` để thêm khía cạnh |
| 23 | "admin chưa ghi nhận máy bị lỗi bạn nha" | | `[]` | tường thuật, không đánh giá máy |
| 24 | "4tr 1 đôi tai nghe" | | `[]` | không phải điện thoại |
| 25 | "và vào game vẫn bị 2 hóc đen 2 đầu" | | `DISPLAY/neg` | "game" chỉ là bối cảnh |
| 26 | "chắc phải lên dùng 14prm 138 sợ không đủ dùng" | | `HARDWARE_OTHER/neu` + `uncertain` | dung lượng bộ nhớ, không phải pin |
| 27 | "ois this ois that" | "camera có OIS không?" | `[]` | chỉ nêu thuật ngữ |
| 28 | "mặt lưng kính" | | `DESIGN/neu` | chỉ mô tả chất liệu |
| 29 | "3 tr" | | `[]` | số tiền không rõ của máy nào |
| 30 | "vào game vẫn mượt" | | `PERFORMANCE/pos` | đối chiếu với ví dụ 25 |
| 31 | "nếu rẻ như nước ngoài" | | `PRICE/neg` | điều kiện = chưa đạt |
| 32 | "giá như samsung cho độ sáng tầm 2k1 nits" | | `DISPLAY/neg` | mong muốn = bất mãn |
| 33 | "mua s22ultra về hỏi đâu cũng không có kính cường lực" | | `[]` | phụ kiện |
| 34 | "phần cứng nhé bạn" | | `[]` | chỉ nhắc tên nhóm chung |
| 35 | "trc mua con n10+ bản 256gb 27 củ" | | `PRICE/neu` | số tiền; dung lượng chỉ là tên phiên bản |

## 11. Quy trình sử dụng

1. **Không gán hàng loạt trước khi hiệu chỉnh.** Cả nhóm gán thử cùng 50 mệnh đề, so kết quả, sửa guideline này, rồi nâng `guideline_version`.
2. Mẫu rải đều theo `video_id` và theo máy, không lấy dồn vào vài video lớn (theo [ml-training.md](ml-training.md#4-gán-nhãn)).
3. Chỉ lấy bình luận `is_spam = false` và `is_vietnamese = true`.
4. Ngẫu nhiên ~200 mệnh đề do LLM gán để người kiểm tra, báo cáo tỷ lệ đúng.
5. Nhãn LLM **chỉ dùng để huấn luyện**, không dùng làm test; tập test do người gán, hai người độc lập, tính Cohen's kappa.
6. Mọi thay đổi guideline → tăng `guideline_version`, ghi lại thay đổi bên dưới.

### Lịch sử thay đổi

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| `v0.1` | 2026-11-02 | Bản nháp đầu tiên, chưa hiệu chỉnh |
| `v0.3` | 2026-11-04 | Sau mẫu seed 7 (200 mệnh đề mới): câu mong muốn/điều kiện nêu điều chưa đạt luôn là `neg` (Gemini thường gán `neu`/`pos`); phụ kiện (kính cường lực, ốp) trả `[]`; "phần cứng nhé bạn" kiểu nhắc nhóm chung trả `[]`; số tiền đi kèm tên phiên bản → `PRICE/neu`, không thêm `HARDWARE_OTHER`; thêm ví dụ 31-35 |
| `v0.2` | 2026-11-04 | Sau lần thử 200 mệnh đề với Gemini: thêm nguyên tắc "ưu tiên chính xác hơn bao phủ" và quy tắc "bằng chứng rõ ràng" (không gán từ tên người/từ đệm, không gán sản phẩm không phải điện thoại, không gán chỉ vì từ khóa, cảm xúc phải có bằng chứng); không dùng `parent_text` để thêm khía cạnh; câu đồng tình ngắn trả `[]`; thêm ví dụ 21-30 |

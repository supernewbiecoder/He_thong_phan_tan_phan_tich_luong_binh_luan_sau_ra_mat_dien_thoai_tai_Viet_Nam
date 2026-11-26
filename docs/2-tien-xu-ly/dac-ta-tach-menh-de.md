# Đặc tả bước 2.3: tách mệnh đề

> Mục đích: Quy định cách tách một bình luận đã làm sạch thành các mệnh đề (vị trí bằng chứng và đơn vị chấm của luật mốc): cắt ở đâu, không cắt ở đâu, gộp mẩu ngắn ra sao, ghi ra trường gì; cập nhật lần cuối: 2026-11-20.

**Code:** `src/processing/clauses.py`, hàm `tach_menh_de`. **Test:** `tests/test_processing_clauses.py`. Đầu vào, đầu ra và phiên bản chung của tầng 2: [dac-ta.md](dac-ta.md).

## 1. Vì sao tách

**Từ 20/11 (phương án A), mệnh đề không còn là đơn vị đếm.** Đơn vị phân tích là cả bình luận, đếm theo (bình luận, máy, khía cạnh) ([muc-tieu.md](../0-chung/muc-tieu.md) mục 4). Lý do bỏ: tách mệnh đề làm mất ngữ cảnh trong cùng bình luận ("iPhone thì pin trâu, camera đẹp": mệnh đề sau mất tên máy), và đếm theo mệnh đề cho người viết nhiều dấu phẩy nhiều phiếu hơn.

Mệnh đề vẫn được tách cho hai việc:
- **Vị trí bằng chứng:** mỗi nhận xét trong `aspect_mentions` ghi `clause_idx`, `clause_text` là mệnh đề đầu tiên mang nhận xét đó, để người đọc thấy câu gốc ([dac-ta-suy-luan.md mục 2](../4-mo-hinh/dac-ta-suy-luan.md#2-đơn-vị-và-quy-tắc-gộp)).
- **Đơn vị chấm của luật mốc:** luật từ khóa không tách được "Cam đẹp nhưng pin yếu" nếu chấm cả câu, nên luật mốc chấm từng mệnh đề rồi gộp lên bình luận. Mô hình chính (PhoBERT, LLM) đọc cả bình luận.

## 2. Đầu vào, đầu ra

- **Đầu vào:** `text_clean` (kết quả bước 2.1). Không dùng `text_norm`, vì mệnh đề phải truy ngược được về chữ gốc.
- **Đầu ra:** cột `clauses`, danh sách theo thứ tự trong bình luận:

| Trường | Nội dung |
|---|---|
| `idx` | Thứ tự mệnh đề, đếm từ 0. Là `clause_idx` của contract `aspect-mention` |
| `start`, `end` | Vị trí ký tự trong `text_clean`: luôn có `text_clean[start:end] == text` |
| `text` | Chữ của mệnh đề, đã bỏ khoảng trắng hai đầu. Là `clause_text` của contract `aspect-mention` |
| `text_norm` | Bước 2.2 chạy trên `text` của mệnh đề; đầu vào của luật cảm xúc mốc |

- Bình luận rỗng → `clauses = []`. Bình luận không có ranh giới nào → 1 mệnh đề là cả bình luận.
- **Không mất chữ:** ghép các chữ (theo `tach_tu`) của mọi mệnh đề phải ra đúng các chữ của `text_clean`. Chỉ dấu phẩy và khoảng trắng ở chỗ cắt là nằm ngoài mệnh đề.

## 3. Cắt ở đâu

| Loại ranh giới (`ly_do`) | Luật | Ký tự ranh giới thuộc về | Ví dụ |
|---|---|---|---|
| `xuong_dong` | `\n` | không mệnh đề nào | "dòng một⏎dòng hai" → "dòng một" \| "dòng hai" |
| `het_cau` | Một hay nhiều dấu `. ! ? ; …` có khoảng trắng hoặc hết chuỗi theo sau | mệnh đề trước | "Máy đẹp. Pin tốt!" → "Máy đẹp." \| "Pin tốt!" |
| `dau_phay` | `,` có khoảng trắng, hết chuỗi hoặc chữ cái theo sau | không mệnh đề nào | "pin trâu, camera đẹp" → "pin trâu" \| "camera đẹp" |
| `tu_noi` | Từ nối tương phản đứng sau khoảng trắng: `nhưng mà`, `nhưng`, `tuy nhiên`, `tuy vậy`, `có điều`, `được cái`, `bù lại`, `ngược lại`, `nhma`, `nma` (không phân biệt hoa thường) | mệnh đề sau | "Cam đẹp nhưng pin yếu" → "Cam đẹp" \| "nhưng pin yếu" |

Mệnh đề đầu tiên có `ly_do = "dau"`. Từ nối đứng ngay sau một ranh giới khác (", nhưng", "⏎nhưng") không tạo ranh giới thứ hai; mệnh đề đó giữ loại ranh giới trước nó.

`ly_do` chỉ có khi gọi `tach_menh_de(..., kem_ly_do=True)` (notebook dùng để đếm). File đầu ra không ghi trường này; manifest đếm sẵn số mệnh đề theo từng loại.

## 4. Không cắt ở đâu

| Trường hợp | Vì sao | Ví dụ giữ nguyên |
|---|---|---|
| Dấu chấm không có khoảng trắng theo sau | Số thập phân, viết tắt, tên miền | "6.7 inch", "v.v", "tgdd.vn" |
| Dấu phẩy giữa hai chữ số | Số thập phân | "12,5 triệu" |
| Bên trong URL và email | Đường dẫn có `?`, `,`, `.` | "https://x.com/a?b=1,c". Dấu câu dính cuối URL vẫn là ranh giới: "…/a. Pin tốt" có cắt |
| Từ nối ở đầu bình luận | Không có gì phía trước để tách | "Nhưng mà pin yếu" |
| `mà`, `còn`, `song`, `trong khi` | Nhiều nghĩa: "máy còn mới", "song sim", "trong khi chơi game" | "máy còn mới mà giá rẻ" |
| Từ nối viết không dấu (`nhung`) | "nhung" cũng là danh từ | |

## 5. Gộp mẩu ngắn

Sau khi cắt, chạy theo thứ tự:

1. **Mẩu không có chữ nào** (chỉ emoji, emoticon, dấu câu) gộp vào mệnh đề **trước** nó; nếu đứng đầu bình luận thì gộp vào mệnh đề sau. Emoji thường nói cảm xúc của câu vừa viết.
   - "Đẹp quá!!! 😍😍" → 1 mệnh đề;
   - "pin tốt. :)))" → 1 mệnh đề;
   - "😍😍, pin tốt" → 1 mệnh đề.
2. **Mẩu có ít hơn `MIN_CHU` chữ** (mặc định 2, tức mẩu 1 chữ) nằm sát **dấu phẩy** thì gộp sang mệnh đề bên kia dấu phẩy (ưu tiên mệnh đề trước). Lặp tới khi không gộp được nữa.
   - "ok, pin trâu" → 1 mệnh đề;
   - "pin trâu, ok" → 1 mệnh đề;
   - "ok, ừ, pin trâu" → "ok, ừ" | "pin trâu".
3. **Mẩu 1 chữ ở ranh giới khác thì giữ:**
   - "Đẹp nhưng đắt" → "Đẹp" | "nhưng đắt": ý tương phản quan trọng;
   - "Pin⏎tốt" → "Pin" | "tốt": người viết tự xuống dòng.

Mẩu đúng 2 chữ không gộp: "theo mình, máy đẹp" → "theo mình" | "máy đẹp". Mệnh đề "theo mình" không có khía cạnh nên khi gán nhãn sẽ là `[]`, không gây sai.

Chữ đếm theo `tach_tu` (chữ cái và chữ số; không tính emoji, emoticon, dấu câu).

## 6. Giới hạn đã biết

- Câu dài không có dấu câu, không có từ nối ("pin trâu camera đẹp giá rẻ") vẫn là 1 mệnh đề nhắc nhiều khía cạnh. Mô hình khía cạnh phải xử lý được mệnh đề nhiều nhãn.
- "mà", "còn" dùng như từ nối tương phản bị bỏ sót. `notebooks/2_3_clauses.ipynb` mục 7 đếm mệnh đề dài có chứa hai chữ này để nhóm xem có cần thêm luật không.
- Không xét ngữ pháp, không dùng mô hình tách câu. Đổi sang mô hình là đổi phiên bản lớn (2.0).

## 7. Tham số

| Tham số | Ở đâu | Mặc định |
|---|---|---|
| `MIN_CHU` | `clauses.py` | `2` |
| `CAC_TU_NOI` (danh sách từ nối) | `clauses.py` | như mục 3 |

Đổi tham số là đổi kết quả: tăng `PIPELINE_VERSION`, sửa test, sửa đặc tả này.

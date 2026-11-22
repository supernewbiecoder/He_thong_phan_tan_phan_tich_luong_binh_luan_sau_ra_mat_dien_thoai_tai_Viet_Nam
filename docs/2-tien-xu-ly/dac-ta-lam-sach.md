# Đặc tả bước 2.1: làm sạch kỹ thuật (Level 1)

> Mục đích: Quy định bước làm sạch kỹ thuật biến `text` thành `text_clean`: sửa lỗi nào, giữ gì, theo thứ tự nào; cập nhật lần cuối: 2026-11-19.

**Code:** `src/processing/clean.py`. **Test:** `tests/test_processing.py`, lớp `Level1`. Đầu vào, đầu ra và phiên bản chung của tầng 2: [dac-ta.md](dac-ta.md).

## 1. Nguyên tắc

Chỉ sửa lỗi do cách máy lưu và truyền chữ. **Không:**
- đổi chữ hoa/thường;
- sửa teencode hay chính tả;
- bỏ emoji;
- lọc spam.

Những việc đó thuộc bước sau.

## 2. Các bước

| Bước | Lỗi | Luật | Hàm |
|---|---|---|---|
| B1 | Bình luận rỗng | `text` là null, không phải chuỗi, hoặc chỉ có khoảng trắng → `text_clean = ""` | `la_rong` |
| B2 | HTML entity | Đổi `&tên;`, `&#số;`, `&#xHEX;` (phải có `;`) về ký tự; lặp tối đa 3 lần cho chuỗi mã hóa chồng. "AT&T", "R&D" không đổi | `giai_ma_html` |
| B3 | Ký tự điều khiển, vô hình | Bỏ mọi ký tự nhóm Unicode `Cc`, `Cf`, `Cs`. **Giữ:** tab, xuống dòng (B5, B6 xử lý); ZWJ `U+200D` nằm giữa hai emoji; ký tự tag `U+E0020–E007F` (cờ) | `bo_ky_tu_dieu_khien` |
| B4 | Unicode không thống nhất | Chuẩn NFC. **Không** dùng NFKC (nó đổi cả nội dung, vd `①` → `1`) | `chuan_unicode` |
| B5 | Xuống dòng bất thường | `\r\n`, `\r`, `U+0085` → `\n`; nhiều dòng trống liền nhau → một `\n`. Xuống dòng **giữ lại** vì bước tách mệnh đề cần | `chuan_xuong_dong` |
| B6 | Khoảng trắng dư | Mọi khoảng trắng trừ `\n` (tab, NBSP, `U+3000`, `U+2028`, `U+2029`…) → một dấu cách; bỏ dấu cách quanh `\n` và ở hai đầu | `chuan_khoang_trang` |
| B7 | Rỗng sau làm sạch | Chuỗi chỉ có ký tự vô hình, sau B3–B6 thành `""` | `lam_sach` |

`lam_sach(text)` chạy cả B1–B7 và trả `text_clean`.

## 3. Thứ tự

B2 → B3 → B4 → B5 → B6:
- B2 trước, vì giải mã entity có thể sinh ra ký tự lạ (`&nbsp;`) để các bước sau dọn.
- B3 trước B4, vì ký tự vô hình chen giữa chữ và dấu làm NFC không gộp được.
- B5 trước B6, để dòng chỉ có dấu cách cũng được tính là dòng trống.

## 4. Không làm ở bước này

- **Thẻ HTML** (`<br>`, `<a>`): crawler gọi YouTube với `textFormat=plainText`, nên dữ liệu không có thẻ.
- **Thống nhất kiểu đặt dấu** (`hoà`/`hòa`): đó là chuẩn hóa ngôn ngữ, thuộc bước 2.2.

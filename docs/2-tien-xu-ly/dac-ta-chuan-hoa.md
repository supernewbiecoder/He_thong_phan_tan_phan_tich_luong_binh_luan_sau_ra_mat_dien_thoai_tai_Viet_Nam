# Đặc tả bước 2.2: chuẩn hóa ngôn ngữ (Level 2)

> Mục đích: Quy định bước chuẩn hóa biến `text_clean` thành `text_norm` và tách `emojis`: các bước N1–N7, luật từng bước, từ điển viết tắt; cập nhật lần cuối: 2026-11-19.

**Code:** `src/processing/normalize.py`, từ điển `src/processing/resources/abbreviations.tsv`. **Test:** `tests/test_processing.py`, các lớp `Level2TungBuoc`, `Level2CaChuoi`, `EmojiVaTachTu`. Đầu vào, đầu ra và phiên bản chung của tầng 2: [dac-ta.md](dac-ta.md).

## Nguyên tắc và thứ tự

- `text_norm` chỉ dùng cho máy, không đưa cho người đọc.
- **Chạy lại không đổi:** `chuan_hoa(chuan_hoa(x)) == chuan_hoa(x)`.
- **Không** thêm dấu cho chữ không dấu, không sửa chính tả, không bỏ emoji, không lọc spam, không đổi tên máy (thuộc Công việc 10).

| Bước | Làm gì | Hàm |
|---|---|---|
| N1 | URL, email, số điện thoại, @tên → token | `thay_token` |
| N2 | Chữ thường | `chu_thuong` |
| N3 | Dấu thanh về một kiểu | `chuan_dau_thanh` |
| N4 | Tiếng cười, emoticon, ký tự lặp | `rut_gon_lap` |
| N5 | Tách dấu câu dính chữ | `tach_dau_cau` |
| N6 | Viết tắt, teencode | `mo_viet_tat` |
| N7 | Dọn khoảng trắng (chạy lại B6 của bước 2.1) | `chuan_khoang_trang` |

`chuan_hoa(text_clean)` chạy N1–N7 và trả `text_norm`.

**Thứ tự có chủ đích; đổi thì phải sửa đặc tả và tăng phiên bản lớn:**
- N1 trước N2: thay URL, @tên khi còn nguyên dạng, để tên người dùng không lọt vào bước đếm từ.
- N4 gom tiếng cười trước khi rút ký tự lặp. Nếu không, "kkkkk" thành "k" rồi bị N6 đọc là "không".
- N6 sau N2–N5, vì từ điển viết thường và so khớp từng chữ đã tách khỏi dấu câu.

## 1. N1. Token

| Thay | Bằng | Luật |
|---|---|---|
| Email | `<email>` | `chữ@tên.miền`; chạy trước URL để email không bị cắt |
| URL | `<url>` | Bắt đầu bằng `http://`, `https://`, `www.`; hoặc tên miền trần có đuôi trong danh sách (`com`, `vn`, `net`, `org`, `io`, `me`, `ly`, `be`, `gl`, `ee`, `co`, `info`, `xyz`, `shop`, `store`, `app`, `link`, `top`, `vip`, `site`, `online`, `tv`, `cc`, `asia`, `biz`), có thể kèm `/đường-dẫn`. Dấu câu dính cuối URL (`.`, `,`, `)`…) được trả lại cho câu |
| Số điện thoại | `<phone>` | Số di động Việt Nam: `0` hoặc `+84`/`84`, rồi đầu số 3, 5, 7, 8, 9, rồi 8 chữ số; giữa các chữ số được có dấu cách, `.`, `-` |
| Tên người | `<user>` | `@` + chữ, số, `.`, `_`, `-` (dạng @handle của YouTube); bỏ `.` `-` dính cuối |

**Không đổi:** giá tiền (`3.990.000đ`), số thập phân (`6.7`, `1.5tr`), `v.v`.

**Giới hạn:** tên hiển thị có dấu cách (`@Nguyễn Văn A`) chỉ thay được chữ đầu.

## 2. N2. Chữ thường

`str.lower()` cho toàn chuỗi, kể cả `Đ` → `đ`. Sau bước này "AI" và "ai" không còn phân biệt được; việc nào cần phân biệt thì dùng `text_clean`.

## 3. N3. Dấu thanh

- Chỉ xét chữ kết thúc bằng **vần mở** `oa`, `oe`, `uy` và có đúng một dấu thanh: chỉ ở đó kiểu cũ và kiểu mới khác nhau.
- Đặt dấu theo `KIEU_DAU` trong `normalize.py`:
  - `"cu"` (mặc định): dấu ở nguyên âm đầu: `hòa`, `khỏe`, `thủy`;
  - `"moi"`: dấu ở nguyên âm sau: `hoà`, `khoẻ`, `thuỷ`.
- **Không đổi:**
  - `qu` + `y` (`quý`, `quỳ`): `u` là phụ âm, dấu luôn ở `y`;
  - có phụ âm cuối (`toàn`, `hoàng`, `thuyền`): hai kiểu như nhau.
- Kiểu mặc định chốt theo số đếm ở `notebooks/2_2_normalize.ipynb` mục 6.4 ([dac-ta.md](dac-ta.md) mục 7, quyết định 1).

## 4. N4. Tiếng cười, emoticon, ký tự lặp

Theo thứ tự:

1. **Tiếng cười** đứng thành chữ riêng → `haha`: `k` lặp từ 3 lần (`kkk`); `ha`/`he` lặp từ 2 lần, cho phép kéo dài (`hahaha`, `hahaaa`, `hehe`); `hi`/`hj` lặp từ 2 lần; `ka`/`ke` lặp từ 2 lần. **Không** gồm `huhu` (khóc).
2. **Emoticon** đứng riêng (có khoảng trắng hai bên): mọi ký tự lặp từ 3 lần rút còn 2: `:)))))` → `:))`, `=)))` → `=))`, `<333` → `<33`, `^^^` → `^^`. Emoticon dính chữ (`quá=)))`) không đổi.
3. **Ký tự lặp trong chữ:** đoạn từ 3 ký tự liền nhau có cùng chữ gốc (bỏ dấu thanh) → 1 ký tự, ưu tiên ký tự mang dấu thanh: `đẹppppp` → `đẹp`, `quáaaaa` → `quá`, `nhéeee` → `nhé`. **Không đổi:**
   - chữ chỉ gồm một ký tự lặp (`zzz`, `aaaa`): rút thành 1 chữ cái thì N6 sẽ đọc nhầm thành viết tắt;
   - lặp 2 lần (`xoong`, `đẹpp`);
   - chữ số.
4. **Dấu câu lặp:** `!`, `?`, `,`, `;`, `~`, `*` lặp → 1. Dấu chấm lửng (`..`, `....`, `…`) → `...`.

Mất mát: độ "kéo dài" (dấu hiệu nhấn mạnh) không còn trong `text_norm`; cần thì lấy từ `text_clean`.

## 5. N5. Dấu câu dính chữ

- Thêm dấu cách sau `,` `;` `!` `?` khi dấu câu dính liền chữ cái phía sau và phía trước nó không phải khoảng trắng: `đẹp,pin` → `đẹp, pin`.
- Thêm dấu cách sau `.` khi có ít nhất 2 chữ cái mỗi bên: `đẹp.pin` → `đẹp. pin`.
- Thêm dấu cách sau `...` khi dính chữ cái: `ổn...mà` → `ổn... mà`.
- **Không đổi:** số (`6.7`, `12,5tr`), `v.v`, emoticon đứng riêng (`;d`).

## 6. N6. Viết tắt, teencode

**Từ điển:** `src/processing/resources/abbreviations.tsv`, mỗi dòng `viết tắt <TAB> đầy đủ <TAB> ghi chú`. Dòng bắt đầu bằng `#` là chú thích.

**Luật của file:** viết tắt là một chữ, viết thường, không trùng nhau. Sai thì code dừng ngay khi đọc.

**Luật thay:**
- Tách chuỗi theo khoảng trắng. Mỗi mẩu bỏ ngoặc, nháy ở đầu và dấu câu ở cuối, phần lõi còn lại trùng đúng một mục từ điển thì thay. Ngoặc và dấu câu giữ nguyên: `(ko)` → `(không)`, `ko,` → `không,`.
- Không thay bên trong chữ khác (`kon` giữ nguyên) và không đụng emoticon (`:v`).
- `k`, `kg`, `v`, `ms` **không** thay khi đứng ngay sau một số (có hoặc không có dấu cách), vì đó là đơn vị: `500 k`, `1 kg`, `sạc 9 v`, `50 ms`.

**Nội dung bản đầu:** 64 mục do trưởng nhóm soạn, chỉ gồm mục ít nhập nhằng (phủ định `ko/k/hok…`, `dc`, `j`, `r`, `mn`, `cx`, `ntn`, `ok`…).

**Cố ý chưa đưa vào** (nhập nhằng trong bình luận điện thoại):

| Mục | Vì sao |
|---|---|
| `vs` | "với" hay "versus" ("s26u vs ip17prm") |
| `bh` | "bây giờ" hay "bảo hành" |
| `bn` | "bạn" hay "bao nhiêu" |
| `dk` | "điều kiện" hay "đăng ký" |
| `kb` | "không biết" hay "kết bạn" |
| `ty` | "thank you" hay "tỷ" (tiền) |
| `h` | "giờ" (bây h) hay giờ đồng hồ (2h) |
| `wa` | "qua" hay "quá" |
| `a`, `e`, `c`, `b`, `m`, `t` | đại từ hay tên dòng máy (Galaxy A…) |
| `vl`, `vcl`, `vkl` | từ cảm thán tăng mức độ: giữ nguyên vì mang cảm xúc |
| `ss`, `ip`, `táo`, `mh`, `cam` | tên máy, thuật ngữ: thuộc Công việc 10 |

**Thêm hay bỏ mục:**
1. Xem bảng ứng viên (`notebooks/2_2_normalize.ipynb` mục 6.3) và số lần gặp từng mục (mục 6.5).
2. Sửa file TSV.
3. Tăng `PIPELINE_VERSION`.
4. Chạy lại test rồi chạy lại lệnh ở [hướng dẫn](huong-dan.md).

## 7. N7. Dọn khoảng trắng

Chạy lại B6 của bước 2.1 để bỏ khoảng trắng thừa do các bước trên để lại.

## 8. Emoji (`emojis`)

- Lấy từ `text_clean`, theo thứ tự xuất hiện, trùng thì giữ cả (`😂😂` → 2 phần tử). Hàm `tach_emoji`.
- **Một emoji** là:
  - một ký tự gốc: nhóm Unicode `So` từ `U+2000` trở lên, hoặc thuộc `U+1F000–1FAFF`, `U+2600–27BF`, `U+2B00–2BFF`;
  - cộng các ký tự ghép theo sau: `U+FE0F`, `U+FE0E`, `U+20E3`, màu da `U+1F3FB–1F3FF`, ký tự tag; và các emoji nối bằng ZWJ.
- **Trường hợp riêng:** cờ quốc gia là cặp chữ cái cờ (`🇻🇳`); keycap là một ký tự `0–9 # *`, có hoặc không có `U+FE0F`, rồi `U+20E3` (`1️⃣`).
- **Không tính:** ký tự ASCII (`^`, `` ` ``) và ký hiệu dưới `U+2000` (`°`, `©`). Vì vậy con số này khác mục 2.5 của notebook, mục đó tính cả nhóm `Sk`.
- Emoji **vẫn nằm** trong `text_norm`.

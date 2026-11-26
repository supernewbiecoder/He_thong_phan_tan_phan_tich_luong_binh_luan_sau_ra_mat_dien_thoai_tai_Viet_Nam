# Đặc tả bước suy luận theo bình luận

> Mục đích: Quy định bước biến file tầng 2 thành `aspect_mentions` theo phương án A (đơn vị là cả bình luận): đầu vào, đầu ra, quy tắc gộp, luật mốc cho khía cạnh, thái độ, máy được nhắc, đã dùng máy, và cách thay luật bằng mô hình; cập nhật lần cuối: 2026-11-26.

**Code:** `src/models/run.py` (lệnh chạy, `suy_luan_binh_luan`), `src/models/aspect/keywords.py`, `src/models/sentiment/rules.py`, `src/models/target_model.py`, `src/models/owner_defect.py`. **Test:** `tests/test_models_run.py`.

**Trạng thái:** phiên bản `rule-v1.1` (26/11, theo [bộ nhãn chốt](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611) và contract `aspect-mention` v3), chỉ có **luật mốc**: chưa đo trên nhãn người, nên số liệu ra từ phiên bản này là **số liệu minh họa**, không dùng để kết luận. Có mô hình đã đánh giá thì thay từng phần theo mục 9.

## 1. Vị trí trong chuỗi, đầu vào, đầu ra

```text
data/processed/comments.jsonl   (tầng 2, processing-2.x: có clauses, is_spam, is_vietnamese)
   │  python -m src.models.run
   ▼
data/aspect_mentions.jsonl            mỗi dòng một mention, đúng contract aspect-mention v3
data/aspect_mentions.comments.jsonl   bình luận có ít nhất một mention, chỉ các trường Công việc 12 cần
data/aspect_mentions.manifest.json    phiên bản, SHA-256, số đếm
   ▼
Công việc 12: python -m src.analysis.build_aggregates   (lệnh src.run tự truyền hai file trên)
```

- **Đầu vào:** file tầng 2. Phải là `processing-2.x`, không thì lệnh dừng và báo chạy lại tầng 2. Danh mục máy: `config/pipeline.yaml`, cùng file Công việc 12 dùng để kiểm.
- **File bình luận cho Công việc 12** chỉ gồm bình luận có mention, với các trường: `comment_id, video_id, model, source, parent_id, author_hash, author_is_creator, published_at, fetched_at, is_spam, is_vietnamese, spam_reasons, text_clean, clauses`. Công việc 12 nạp cả file bình luận vào bộ nhớ, nên file đầy đủ ~470 nghìn dòng sẽ rất nặng.
- Ghi file tạm rồi đổi tên, nên lệnh lỗi giữa chừng không để lại file dở. Chạy lại thì ghi đè, không cộng dồn.

## 2. Đơn vị và quy tắc gộp

Đơn vị là **cả bình luận**. Đếm theo **(bình luận, máy, nhãn chiều 2)**: mỗi bộ này có tối đa **một lời khen và một lời chê**.

1. **Bỏ qua** bình luận rỗng, `is_spam = true`, hoặc `is_vietnamese = false`: không tạo mention ([thiết kế dữ liệu mục 4](../0-chung/thiet-ke-du-lieu.md#4-aspect_mentions)). Bình luận của chủ kênh vẫn tạo mention; Công việc 12 tự loại khỏi aggregates.
2. Với từng mệnh đề (bước 2.3) có từ khóa khía cạnh: xác định máy (mục 5) và thái độ (mục 4) của mệnh đề đó.
3. **Gộp lên bình luận** theo (máy, khía cạnh):
   - có khen → một dòng `tich_cuc`, bằng chứng là mệnh đề khen đầu tiên;
   - có chê → một dòng `tieu_cuc`, bằng chứng là mệnh đề chê đầu tiên;
   - không có khen, chê nào → một dòng `khong_danh_gia`, bằng chứng là mệnh đề đầu tiên.

| Bình luận (video S26 Ultra) | Mention |
|---|---|
| "pin tốt, pin trâu, pin ngon" | `s26u`, `pin_sac`, `tich_cuc` (1 dòng, không phải 3) |
| "camera ngày đẹp, đêm thì chụp kém" | `s26u`, `camera`, `tich_cuc` **và** `s26u`, `camera`, `tieu_cuc` |
| "camera 200mp, chụp đẹp" | `s26u`, `camera`, `tich_cuc` (bỏ dòng không đánh giá) |
| "iPhone 17 Pro Max thì pin trâu, camera đẹp" | `ip17prm`, `pin_sac`, `tich_cuc` và `ip17prm`, `camera`, `tich_cuc` |

**Quy ước với contract `aspect-mention`** (v2 giữ nguyên ở 20/11; v3 từ 26/11 chỉ đổi mã nhãn và thêm trường, không đổi khóa): khóa `mention_id = <comment_id>#<clause_idx>#<aspect>`. Theo phương án A thì:
- `clause_idx`, `clause_text` là **mệnh đề làm bằng chứng**, không phải đơn vị đếm. `clause_text` luôn bằng `clauses[clause_idx].text`, nên qua được bước kiểm của Công việc 12.
- `mention_id` **không bao giờ trùng** trong một bình luận. Mỗi mệnh đề chỉ có một máy và một thái độ, và mỗi (máy, khía cạnh, thái độ) chỉ ghi một lần ở mệnh đề đầu tiên.
- Muốn đếm "số người khen pin S26 Ultra" thì đếm số `comment_id` khác nhau, không cộng số dòng của nhiều bình luận cùng tác giả. Gộp theo `author_hash` là việc của Công việc 12.

## 3. Khía cạnh

- **Bộ từ khóa:** `TU_KHOA` trong `src/models/aspect/keywords.py`, theo 11 khía cạnh của bộ nhãn chốt (mã lấy từ `src/labeling/final_labels.py`). Bản `rule-v1` (9 khía cạnh cũ, chuyển từ notebook `3_aspect_keywords` bản 19/11) đổi sang `rule-v1.1` ngày 26/11:
  - nhóm "thiết kế & độ bền" tách thành `thiet_ke` (ngoại hình, chất liệu, trọng lượng, màu máy) và `do_ben` (độ bền, rơi vỡ, chống nước);
  - nhóm "bảo hành & hậu mãi" tách thành `bao_hanh_sua_chua` (bảo hành, sửa chữa, đổi trả, dịch vụ) và `mua_ban` (chính hãng, xách tay, cửa hàng);
  - "trả góp" chuyển từ `gia` sang `mua_ban`; thêm từ khóa `mua_ban`: lên đời, đổi máy, thu cũ, mua ở đâu, nên mua, định mua, đặt trước;
  - các nhóm còn lại giữ nguyên từ khóa, chỉ đổi mã (`pin_sac`, `man_hinh`, `hieu_nang` gồm nóng máy, `camera`, `phan_mem`, `phan_cung_khac` gồm loa, `gia`).
  Notebook `3_aspect_keywords` đọc lại từ module này, nên chỉ còn một bản.
- **Luật không đoán** `may_chung`, `hang_nguoi_dung`, `khac`: không có từ khóa đủ rõ.
- So khớp trên `clauses[i].text` (giữ chữ hoa: "AI" khác "ai"), không phân biệt hoa thường, có luật loại trừ: "màu cam", "cam on", "trẻ trâu", "chống rung", "lên sóng".
- Một mệnh đề có thể nhắc nhiều khía cạnh.
- **Giới hạn:** bỏ sót cách nói không có từ khóa ("máy đẹp" không tính vào `thiet_ke`, vì "đẹp" dùng cho mọi thứ). Bắt nhầm khi từ khóa dùng nghĩa khác.

## 4. Thái độ

`src/models/sentiment/rules.py`, hàm `cam_xuc`, chạy trên `clauses[i].text_norm` (chữ thường, viết tắt đã mở: "ko" → "không").

1. Câu hỏi là không đánh giá: có "?" hoặc kết thúc bằng "không", "chưa", "sao", "nhỉ" ("có lag không").
2. Đếm cụm khen (`KHEN`) và cụm chê (`CHE`). **Cụm dài khớp trước**: "tụt nhanh" là chê, dù "nhanh" là khen.
3. Cụm đứng sau từ phủ định (`PHU_DINH`: không, chẳng, chả, chưa, hết, đỡ, bớt…) trong vòng 2 chữ thì **đổi chiều**: "không lag" là khen, "không đẹp lắm" là chê, "hết lag" là khen.
4. Điểm = số khen − số chê. Dương là `tich_cuc`, âm là `tieu_cuc`, bằng 0 là `khong_danh_gia`. Luật **không** ra `so_sanh` (cần biết bên hơn).

**Cố ý không đưa vào:** "sáng" (buổi sáng), "chất" (chất liệu), "sang" (sang năm), "hơn" (so sánh).

**Giới hạn:**
- Mọi khía cạnh trong cùng một mệnh đề nhận chung một thái độ ("pin trâu cam xấu" không có dấu phẩy thì sai một trong hai).
- Không nhận mỉa mai.
- Không nhận câu mong muốn ("ước gì pin trâu hơn"), trong khi guideline tính là chê.

## 5. Máy được nhắc

`src/models/target_model.py`.

**Nhận tên máy:** lấy mã, `title`, `aliases` của mọi máy trong `config/pipeline.yaml` (gồm cả máy khai trong `rivals`).
- Chỉ dùng tên **có chữ số** và **chỉ thuộc đúng một máy**. Tên hãng trơn ("táo", "ss", "iphone") không đủ để biết máy nào.
- So khớp không dấu, không phân biệt hoa thường, cho phép có hoặc không có dấu cách: "ip17prm", "ip 17 prm", "iPhone17ProMax", "iphone 17 pro max" đều là `ip17prm`.
- Ở cùng một vị trí, tên dài thắng tên ngắn: "s26 ultra" thắng "s26u".

**Xác định máy cho mệnh đề thứ i** (hàm `xac_dinh_may`). Xét lần lượt, gặp trước thì dừng; nguồn được đếm trong manifest:

| # | Điều kiện | Nguồn |
|---|---|---|
| 1 | Mệnh đề i gọi tên máy (nhiều tên thì lấy tên đứng đầu) | `menh_de` |
| 2 | Mệnh đề đứng trước gần nhất có tên máy, cùng bình luận ("iPhone thì pin trâu, **camera đẹp**") | `menh_de_truoc` |
| 3 | Cả bình luận gọi tên đúng một máy | `binh_luan` |
| 4 | Bình luận cha gọi tên đúng một máy | `binh_luan_cha` |
| 5 | Video chỉ về một máy (trường `model` không có `\|`) | `video` |
| 6 | Không rõ: `target_model = null`, `days_since_launch = null` | `khong_ro` |

So với quy tắc cũ của Công việc 10 ("xét comment cha, rồi máy của video"), bước 2 và 3 mới có. Đây là lý do chính để chọn phương án A.

**`target_model_source`** (contract v3) ghi đúng cột "Nguồn" ở bảng trên, để phân tích tách riêng phần đoán theo máy của video.

**`model_mention`** (chiều 6, contract v3, hàm `may_duoc_nhac` trong `run.py`), xét cả bình luận: `goi_ten_may` khi có tên máy có số đời (trong danh mục, hay theo mẫu `MAY_CU_THE` của `src/labeling/label_set.py`); `chi_hang` khi chỉ có tên hãng hay dòng (mẫu `HANG`); còn lại `khong_nhac`.

**`days_since_launch`** = ngày đăng theo giờ Việt Nam (UTC+7, không đổi theo mùa) trừ `launch_date` của `target_model`. Cách tính giống `src/analysis/validation.py`.

**Chưa làm (cần nhãn để đo):**
- Câu so sánh: `compare_with` và `compare_winner` luôn `null`, nên Q3b chưa có dữ liệu.
- Câu nhắc hai máy trong cùng mệnh đề: hiện lấy máy đứng đầu.

## 6. Đã dùng máy (cho Q5)

`src/models/owner_defect.py`.

- **`is_owner`** (`da_dung_may`), xét trên `text_norm` của cả bình luận. Áp chung cho mọi mention của bình luận đó.
  - `true` khi có dấu hiệu đã dùng: "mình/tôi/em (đang/đã/mới) dùng/xài/mua", "đang dùng", "đã mua", "dùng được 2 tháng", "máy mình"…
  - **Không thấy thì `null`, không phải `false`**: không có từ khóa không chứng minh người viết chưa dùng.
  - Không tính "anh dùng…", vì thường là gọi người làm video.
- **`defect_type`** luôn `null`. Bộ 9 loại lỗi cũ và luật `loai_loi` đã bỏ ngày 26/11 cùng 9 khía cạnh cũ; bộ loại lỗi mới làm trên mẫu riêng các bình luận báo lỗi ([kế hoạch tổng thể](../0-chung/ke-hoach-tong-the.md) bước 2.6). Q5 tạm tính lời chê của người đã dùng máy theo khía cạnh.
- **`purposes`** (chiều 3) luôn `null`: luật chưa suy mục đích.

## 7. Các trường còn lại

| Trường | Giá trị |
|---|---|
| `confidence` | `null`: luật không có xác suất. Công việc 12 ghi cảnh báo `CONFIDENCE_UNKNOWN`, không loại |
| `label_source` | `rule` |
| `model_version` | `rule-v1.1` (hằng `MODEL_VERSION` trong `run.py`; `rule-v1` là bản 20/11 theo 9 khía cạnh cũ) |
| `schema_version` | `3` |
| `purposes`, `defect_type`, `compare_with`, `compare_winner` | `null` |
| `parent_id`, `source`, `video_id`, `video_model`, `author_hash`, `author_is_creator`, `published_at` | Chép từ bình luận (`video_model` = trường `model`) |

## 8. Manifest

`data/aspect_mentions.manifest.json` ghi:
- phiên bản, thời điểm chạy;
- SHA-256 file vào, danh mục máy, file ra; số bình luận đã xét;
- số bình luận bị bỏ qua theo lý do;
- số mention theo khía cạnh, theo thái độ, theo máy (20 máy nhiều nhất);
- số mention theo nguồn xác định máy (mục 5).

Tỷ lệ `video` và `khong_ro` cao nghĩa là phần lớn nhận xét không gọi tên máy. Đó là điều Công việc 10 cần đo.

## 9. Thay luật bằng mô hình

Mỗi phần thay riêng được, miễn là định dạng đầu ra giữ nguyên:

| Phần | Hàm đang dùng | Thay bằng | Ai |
|---|---|---|---|
| Khía cạnh | `keywords.khia_canh` trên từng mệnh đề | Mô hình đa nhãn đọc cả bình luận | Công việc 8 |
| Thái độ | `rules.cam_xuc` trên từng mệnh đề | Mô hình đọc "khía cạnh + cả bình luận" | Công việc 9 |
| Máy, so sánh | `target_model.xac_dinh_may` | Luật đã đo hoặc mô hình, thêm `compare_with` | Công việc 10 |
| Đã dùng; mục đích, loại lỗi (chưa có) | `owner_defect.da_dung_may` | Luật đã đo hoặc mô hình | Công việc 1 (nhãn), 9 |

Khi thay:
- đổi `MODEL_VERSION`, đổi `label_source` thành `model`, điền `confidence`;
- mô hình đọc cả bình luận thì vẫn phải chỉ ra mệnh đề bằng chứng: chọn mệnh đề có từ khóa của khía cạnh đó, không có thì mệnh đề 0;
- chạy lại cả bước suy luận và Công việc 12; sửa test và đặc tả này.

Muốn so luật với mô hình thì chấm cả hai trên cùng tập test người gán của Công việc 7.

## 10. Luật ↔ code ↔ test

| Mục | Code | Test (`tests/test_models_run.py`) |
|---|---|---|
| 1, 8 (lệnh, file, manifest) | `run.py`: `chay`, `file_binh_luan_cv12` | `QuaKiemTraCV12` |
| 2 (gộp) | `run.py`: `suy_luan_binh_luan` | `SuyLuanBinhLuan` |
| 3 | `aspect/keywords.py` | `LuatMoc.test_khia_canh` |
| 4 | `sentiment/rules.py` | `LuatMoc.test_cam_xuc` |
| 5 | `target_model.py`, `run.py`: `may_duoc_nhac` | `LuatMoc.test_nhan_may`, `test_xac_dinh_may`, `test_so_ngay`, `test_may_duoc_nhac` |
| 6 | `owner_defect.py` | `LuatMoc.test_da_dung` |
| Đúng contract, qua bước kiểm của Công việc 12 | toàn bộ | `SuyLuanBinhLuan.test_dung_contract`, `QuaKiemTraCV12` |

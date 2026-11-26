# Báo cáo quá trình: sổ ghi chép nhánh khám phá nhãn

> Mục đích: Ghi theo từng đợt, từ trước 22/11 tới 26/11/2026, nhánh `kham-pha-nhan` đã hỏi gì, làm gì, ra số liệu gì, suy ra gì, sai ở đâu và sửa ra sao, kèm công thức, lý do, tài liệu của từng đợt và kết quả cuối; cập nhật lần cuối: 2026-11-26.

**Nguồn.** Do Claude soạn từ tài liệu của nhánh và ghi chép gốc của trưởng nhóm (`Handwritting.md`, bản đầu sao ở `data/ban-sao/`). Đoạn đánh dấu **✍ Ghi chép gốc** là câu nguyên văn của trưởng nhóm. Số liệu chép từ các báo cáo do code sinh, ghi nguồn ở cuối mỗi đợt. File này kể lại theo thời gian. Luật nằm ở đặc tả; chỗ nào lệch thì theo đặc tả.

**Ai là ai.** A là Claude (AI), người mã hóa. B là trưởng nhóm, người kiểm và người quyết. Mọi nhãn do A gán là nhãn của AI cho tới khi B kiểm.

**Cách đọc một đợt:** **Hỏi** (câu hỏi hay giả thuyết) → **Làm** → **Kết quả** (có số) → **Suy ra** → **Sai, sửa** (nếu có) → **Tài liệu**. Dòng bắt đầu bằng → là điều suy ra.

---

## Đợt 0. Trước 22/11: câu hỏi và giả định ban đầu

**Hỏi.** Đề tài muốn dùng bình luận YouTube tiếng Việt sau khi một điện thoại ra mắt để trả lời 6 câu hỏi.

> ✍ **Ghi chép gốc:** "Chúng ta có hơn 400k dữ liệu từ youtube để phục vụ trả lời câu hỏi: 1. X được đón nhận tốt hay dở, thay đổi qua 4 tuần đầu như nào? 2. X có ưu, nhược điểm gì? 3. So với đối thủ, X mạnh, hay yếu ở đâu? 4. Đời trước bị chê gì, đời này đã sửa chưa? 5. Người đã dùng đã báo những lỗi gì, lỗi nào cần sửa trước. 6. Có tài khoản ảo seeding không, và nó làm lệch kết quả bao nhiêu? (đề xuất)"
>
> "Để trả lời được 5 câu hỏi từ 1-5, chúng ta cần phải có 1 mô hình để đánh giá cảm xúc bình luận của người cmt."

**Đã có trên `main`.** Code tiền xử lý, luật mốc `rule-v1`, guideline gán nhãn v1 nháp (20/11) với **bộ nhãn đặt sẵn**: 9 khía cạnh (Pin & sạc, Màn hình, Hiệu năng gồm nóng máy, Camera, Thiết kế & độ bền, Phần mềm, Phần cứng khác, Giá, Bảo hành & hậu mãi), cảm xúc khen / chê / trung tính, mức liên quan, spam, máy được nhắc, đã dùng máy và 9 loại lỗi. Ngày 20/11 nhóm chốt đơn vị phân tích là cả bình luận (phương án A).

**Bài báo tham khảo.** Wiegard và cộng sự (ECIS 2017) tìm khía cạnh trong 3.631 bình luận YouTube của 3 điện thoại tiếng Anh bằng thuật toán HAC. Precision trung bình 0,43 với YouTube, 0,45 với Amazon.

→ Bình luận YouTube dùng được để tìm khía cạnh. Nhưng bài này không đo cảm xúc, chỉ có 3 máy và là tiếng Anh, nên không mượn được con số.

→ Precision 0,43 nghĩa là hơn một nửa khía cạnh thuật toán xếp đầu là sai: kết quả tự động phải có người kiểm.

**Vấn đề.** Bộ nhãn trên `main` được đặt **trước khi đọc dữ liệu**. Chưa ai biết bình luận thật có những loại nội dung nào, mỗi loại chiếm bao nhiêu, và bộ nhãn đó thiếu hay thừa gì.

→ **Ý tưởng của nhánh:** bắt đầu lại từ dữ liệu. Đọc một mẫu ngẫu nhiên, rút bộ nhãn từ chính bình luận, đo tỷ lệ có khoảng tin cậy, rồi mới so với bộ đặt sẵn.

**Tài liệu:** `Handwritting.md`; trên `main`: `docs/0-chung/muc-tieu.md`, `docs/3-gan-nhan/huong-dan-gan-nhan-binh-luan.md`.

---

## Đợt 1. 22/11: tạo nhánh, kiểm tra cấu trúc dữ liệu (B1)

**Hỏi.** Trước khi đọc nội dung: dữ liệu hỏng hay lệch ở đâu? Có nhóm nào cần tách khi tính tỷ lệ?

**Làm.** Tạo nhánh mồ côi `kham-pha-nhan` (không chung lịch sử với `main`, nên không ai lỡ tay merge được). Chạy notebook `1_raw_audit` trên dữ liệu v4 (473.786 dòng, SHA-256 `722d0e1e…2b45`). Số Level 0 trùng từng con số với lần chạy 11/11 trên `main`.

**Kết quả** (tỷ lệ trên 473.786 bình luận, là số đếm toàn bộ nên không cần khoảng tin cậy):

| Thấy | Số | → Suy ra |
|---|---|---|
| Reply | 42,7% | Phiếu đọc phải hiện kèm bình luận cha |
| 5 trong 44 kênh | 62,7% (riêng một kênh 22,85%) | Tỷ lệ phải tách theo nhóm kênh |
| 4 trong 5 video đông nhất là video tặng quà | 15.998 bình luận (3,38%) | Nguồn nhiễu lớn nhất thấy được |
| Từ khóa `QUA_RE` nhận video tặng quà | 6.865 bình luận, sai cả hai chiều | Không dùng; đo bằng nhãn `minigame` |
| Bình luận của chủ kênh | 2,84% | Không phải ý kiến người xem; thêm cột `chu_kenh` |
| Trùng nội dung với bình luận khác | 4,12% | Chưa biết là spam hay câu ngắn tự nhiên |
| Bình luận ≤ 2 từ | 5,53% | Vẫn giữ trong mẫu, vì là dữ liệu thật |
| Tiếng Việt có dấu (đoán bằng luật) | 93,96% | Khoảng 6% còn lại để người đọc phân loại |
| Lượt bình luận tuần 1 / tuần 4 | 38,3% / 13,3% | Tách tuần 1–2 với 3–4 |

→ Dữ liệu sạch về kỹ thuật (không trùng `comment_id`), nên lấy mẫu thẳng từ file gốc.

→ EDA chỉ cho biết **hình dạng** dữ liệu, không cho biết người ta nói gì. Muốn biết thì phải đọc.

**Tài liệu:** [báo cáo kiểm tra dữ liệu](../1-thu-thap/bao-cao-kiem-tra-du-lieu.md), [đặc tả dữ liệu](../1-thu-thap/dac-ta.md), [kế hoạch](ke-hoach.md).

---

## Đợt 2. 22/11: lấy mẫu (B2), vì sao 500 và 600

**Hỏi.** Không ai đọc nổi 473.741 bình luận (giả sử 1 phút mỗi bình luận thì mất khoảng 7.900 giờ). Đọc bao nhiêu là đủ, và đủ cho việc gì?

> ✍ **Ghi chép gốc:** "Hiện tại chúng ta có 400k cmt, một số lượng rất lớn và khó để có thể gán bằng tay trong thời gian có hạn, nên mình đề xuất một phương pháp trong môn thống kê và xác suất."

**Ý tưởng.** Hai việc cần hai cỡ mẫu khác nhau: **thấy** được nhãn hiếm, và **đo** tỷ lệ đủ chính xác.

**Công thức 1, thấy nhãn hiếm.** Nhãn chiếm tỷ lệ `p` thì khả năng gặp nó ít nhất một lần trong `n` bình luận ngẫu nhiên là:

```text
P(gặp ≥ 1 lần) = 1 − (1 − p)^n
p = 0,5%:  n = 300 → 78%   n = 500 → 92%
p = 1%:    n = 300 → 95%   n = 500 → 99,3%
```

→ Đọc 500 bình luận thì nhãn từ 0,5% trở lên gần như chắc chắn hiện ra. Với 300 thì cứ khoảng 5 nhãn cỡ 0,5% sẽ sót 1.

**Công thức 2, đo đủ chính xác.** Nửa độ rộng khoảng tin cậy 95%, và cỡ mẫu cần cho sai số `E`:

```text
E ≈ z · √( p(1 − p) / n )         z = 1,96
n = z² · p(1 − p) / E²            p = 0,5 (xấu nhất), E = 4%  →  n = 600,25
n = 600:  p = 50% → ±4,0   p = 10% → ±2,4   p = 3% → ±1,4 (điểm %)
```

→ Đọc 500 bình luận để tìm nhãn, giữ kín thêm 100 (lô K) để kiểm. 500 + 100 = 600 là mẫu tính tỷ lệ.

**Làm.** Lấy ngẫu nhiên đơn 800 bình luận, không hoàn lại, seed `20261122` (ai chạy lại cũng ra đúng mẫu đó). Bỏ trước 45 bình luận rỗng sau làm sạch nhẹ.

| Lô | Số bình luận | Dùng cho |
|---|---|---|
| 1–5 | 500 | Mã hóa mở |
| K | 100 | Kiểm mù; **không ai đọc trước B6** |
| D1, D2 | 200 | Dự trữ |
| CD (có chủ đích) | 100 | Tìm theo 12 từ khóa ("lỗi", "bảo hành", "trả góp"…) để không sót loại hiếm. **Không tính vào tỷ lệ** |

**Kiểm mẫu 600 thật:** 351 bình luận gốc / 249 reply; 360 ở 5 kênh lớn / 237 kênh khác / 3 không rõ; 406 ở tuần 1–2 / 194 ở tuần 3–4; 18 của chủ kênh; 507 video, nhiều nhất 5 bình luận một video. Nhóm nhỏ nhất (194) vẫn cho sai số ±7,0% ở `p = 50%`. Hệ số hiệu chỉnh tổng thể hữu hạn `√(1 − 600/473.786) ≈ 0,9994`, bỏ qua được.

**Sai, sửa.** Chạy lại code lấy mẫu sẽ ghi đè phiếu đã có người điền. Đã thêm chốt chặn: phiếu đã có chữ thì giữ nguyên, muốn ghi đè phải thêm `--ghi-de`.

**Tài liệu:** [đặc tả khám phá nhãn mục 3](../3-gan-nhan/dac-ta-kham-pha-nhan.md#3-mẫu), `src/labeling/sample.py`, `data/kham-pha/mau.csv` (ngoài git).

---

## Đợt 3. 22/11: HAC trên cả bộ dữ liệu (B3)

**Hỏi.** Mẫu 600 không thấy được khía cạnh hiếm dưới khoảng 0,5%. Có cách nào quét cả 473 nghìn bình luận không?

**Ý tưởng.** Dùng lại thuật toán HAC của bài báo: khía cạnh thường là danh từ hay đi kèm từ đánh giá. Công cụ gán từ loại tiếng Việt yếu với teencode, nên viết bản **không cần tách từ**: tiếng Việt đặt danh từ trước từ đánh giá ("pin trâu"), và dùng một danh sách 61 từ đánh giá cố định thay cho từ loại "tính từ".

**Làm.** Với mỗi từ đánh giá, nhìn ngược tối đa 4 âm tiết trong câu, bỏ qua từ đệm ("quá", "rất", "không"…). Âm tiết nội dung gần nhất được 1 điểm.

```text
điểm HAC(w) = số lần w được gắn với một từ đánh giá
```

**Kết quả.** 473.741 bình luận, 45.256 ứng viên khác nhau, giữ 300 ứng viên điểm cao nhất. Đứng đầu: pin 4.759, giá 3.694, sạc 3.427, game 3.399, độ 3.338 (hay đi với "sáng", "bền"), hình 2.929.

→ Có ứng viên đúng (pin, giá, sạc), có mảnh từ ("độ" của "độ sáng", "hình" của "màn hình").

**Sai, sửa.** Câu ví dụ đổi mỗi lần chạy, vì code duyệt một tập hợp không có thứ tự. Sửa bằng cách sắp xếp trước (`sorted`), rồi kiểm: hai lần chạy với hai giá trị `PYTHONHASHSEED` khác nhau ra file giống hệt nhau.

**Tài liệu:** [đặc tả mục 4](../3-gan-nhan/dac-ta-kham-pha-nhan.md#4-hac-tìm-ứng-viên-khía-cạnh-trên-cả-bộ-dữ-liệu-b3), `src/labeling/hac.py`, `data/kham-pha/hac_ung_vien.csv`.

---

## Đợt 4. 22–23/11: mã hóa mở (B4)

**Hỏi.** Bình luận thật nói về cái gì, theo chữ của chính nó, khi chưa áp bộ nhãn nào?

**Ý tưởng.** Mã hóa mở: mỗi bình luận ghi một hay nhiều mã dạng `đối tượng: hành vi (ghi chú)`. Đối tượng ghi bằng từ của bình luận, không dùng tên 9 khía cạnh đặt sẵn, để không chỉ xác nhận lại giả định.

```text
"pin trâu, cam đêm hơi nhòe"            → pin: khen; cam đêm: chê
"cam ban ngày đẹp, nhưng ban đêm xấu"   → cam chụp sáng: khen; cam chụp tối: chê
```

**Làm.** A mã lô 1 trước (thí điểm), dừng cho B xem, rồi mã lô 2–5 và CD. Tên người dạng `@…` được che. Bảng hành vi (28 hành vi) rút từ lô 1.

**Kết quả.** 600 bình luận, 843 mã (lô 1–5: 680; CD: 163). Lô 1–5 có 412 đối tượng khác nhau, 346 đối tượng chỉ gặp một lần.

→ Để nguyên thì quá vụn: đúng cái lo "chia nhỏ quá" trong ghi chép gốc. Phải gom.

> ✍ **Ghi chép gốc:** "nếu như chúng ta chia khía cạnh nhỏ quá, thì sẽ thật khó để train mô hình vì quá ít dữ liệu để phân biệt các khía cạnh nhỏ ấy, quá ít ví dụ. Còn nếu khía cạnh lớn quá, thì lại khó để con người phân biệt được đâu mới là cái cần sửa"

**Sai, sửa.** Tên dạng `@a@b` viết liền chưa được che: sửa biểu thức chính quy. Lượt tự rà thứ hai sửa nhiều mã ở lô 1, ít ở các lô sau. Tự rà không thay được người kiểm.

**Tài liệu:** [guideline mã hóa mục 2](../3-gan-nhan/huong-dan-kham-pha-nhan.md#2-ghi-mã-tự-do), [báo cáo mã hóa mở](../3-gan-nhan/bao-cao-ma-hoa-mo.md), `data/kham-pha/phieu_ma_hoa_mo.csv`.

---

## Đợt 5. 23/11: B mã độc lập, đo đồng thuận; bỏ chấm HAC

**Hỏi.** Mã của A phản ánh dữ liệu, hay phản ánh cách đọc của A?

**Làm.** Code xuất phiếu trống. B tự mã tay cả 600 bình luận, không xem mã của A. Phiếu A được đóng băng trước (SHA-256 `f4a7922a…d170`). So được 599 bình luận (1 dòng bị Excel làm hỏng thành `#NAME?`). Mỗi hành vi là một câu có/không trên mỗi bình luận.

```text
p_o = tỷ lệ bình luận hai bên ghi giống nhau
p_e = p_A(có)·p_B(có) + p_A(không)·p_B(không)      (giống nhau do may rủi)
κ   = (p_o − p_e) / (1 − p_e)                       ngưỡng dùng được: κ ≥ 0,6
```

**Kết quả.** 21 trong 32 hành vi đạt κ ≥ 0,6. Cao: hỏi 0,88, yêu cầu 0,85, chửi 0,80, khen 0,77, chê 0,74. Thấp: nhắc 0,18, trêu 0,22, lo ngại 0,35, kể 0,37, nhận xét 0,38.

→ Vì sao phải dùng kappa: ở hành vi `nhắc`, hai bên giống nhau tới 97% số bình luận, chỉ vì cả hai gần như không dùng nó. Kappa trừ phần đó đi, còn 0,18.

→ Chỗ lệch chủ yếu do **luật mơ hồ**, không phải ai sai. B duyệt sửa bảng hành vi trong ngày: `kể` chỉ là kể, định mua là `mong muốn`, `báo lỗi` thành hành vi riêng.

→ Đây là đồng thuận **người với AI** trên mã tự do, chưa đo được bộ nhãn.

**Quyết định cùng ngày.** B không chấm danh sách HAC: nhiều mảnh từ và teencode, chấm 300 dòng tốn công mà ít thu được. HAC chỉ để A đối chiếu ở B8, ghi rõ "do AI làm".

**Tài liệu:** [đặc tả mục 7d](../3-gan-nhan/dac-ta-kham-pha-nhan.md#7-kiểm-b6), `data/kham-pha/dong_thuan_ma_hoa_mo.csv`, [guideline: bảng hành vi](../3-gan-nhan/huong-dan-kham-pha-nhan.md#bảng-hành-vi).

---

## Đợt 6. 23–24/11: gom mã thành bộ nhãn (B5)

**Hỏi.** Gom 843 mã thành những nhãn nào, xếp vào những câu hỏi nào? Khi nào thì đọc đủ?

**Làm.** Gom bằng code (luật từ khóa trên đối tượng, bảng hành vi → mục đích) để số đếm chạy lại được. Mỗi **chiều** là một câu hỏi về bình luận; mỗi **nhãn** là một câu trả lời.

**Kết quả.** Bộ nhãn nháp có 6 chiều, 43 nhãn:

| Chiều | Câu hỏi | Số nhãn |
|---|---|---|
| 1 | Nói về cái gì? | 6 |
| 2 | Nói về phần nào của điện thoại? | 15 (13 khía cạnh, 2 nhãn ngoài khía cạnh) |
| 3 | Viết để làm gì? | 13 |
| 4 | Thái độ với từng phần đó? | 4 |
| 5 | Người viết đã dùng máy chưa? | 2 |
| 6 | Có gọi tên máy không? | 3 |

**Bão hòa** (luật dừng: lô 5 không có nhãn nào xuất hiện lần đầu). Số nhãn xuất hiện lần đầu ở lô 1→5: 37, 0, 2, 0, 0 → đủ, không cần đọc lô dự trữ.

**Kiểm độc lập.** Áp cùng luật gom lên 797 mã của B: 36 mã chưa xếp được, phần lớn là từ đồng nghĩa ("tản nhiệt", "tần số quét").

→ Không thấy loại nội dung nào bộ nhãn thiếu.

→ So với giả định ban đầu: thêm hẳn một chiều "viết để làm gì", và một số nhãn không có trên `main` (`mua_ban`, `may_chung`, `hang_nguoi_dung`).

**Sai, sửa.** Hai từ *nhãn* và *khía cạnh* bị dùng lẫn trong tài liệu. Ngày 24/11 thống nhất lại: mọi khía cạnh là nhãn của chiều 2, nhưng không phải nhãn nào cũng là khía cạnh (`hoi`, `may_chung` là nhãn, không phải khía cạnh).

**Tài liệu:** [đặc tả bộ nhãn](../3-gan-nhan/dac-ta-bo-nhan.md), [báo cáo bộ nhãn](../3-gan-nhan/bao-cao-bo-nhan.md), [thuật ngữ](../3-gan-nhan/dac-ta-kham-pha-nhan.md#thuật-ngữ), `src/labeling/label_set.py`.

---

## Đợt 7. 25/11: duyệt bộ nhãn, làm rõ luật chốt, chuẩn bị gán

**Hỏi.** Bộ nhãn nháp có dùng được để gán không? Luật "từ 3% thì thêm" tính 3% của cái gì?

**B duyệt bộ nhãn (7 điểm).** Nhãn hiếm để riêng tới B8 (gộp sau dễ hơn tách sau). Không tách hãng với fan. Bài test trong video là `ngu_canh`. Tách `dua` với `cong_kich` để sau lọc bình luận độc hại. Cà khịa hãng, fan không tính là chê. Máy tính bảng là `khong_lien_quan`. Khen "đẹp" một máy mà không chỉ phần nào thì là `thiet_ke`.

**Làm rõ luật chốt (đặc tả mục 9).** Luật cũ chỉ ghi "3% số bình luận của phần áp dụng", không nói phần áp dụng là gì. B duyệt 4 điểm:

```text
tỷ lệ = số bình luận có nhãn (trong mẫu 600) / số bình luận thuộc phần áp dụng

chiều 1, 3, 5, 6 → mẫu số = cả 600 bình luận       (3% = 18 bình luận)
chiều 2          → mẫu số = bình luận dien_thoai
chiều 4          → mẫu số = số cặp (bình luận, nhãn chiều 2)
```

- Nhãn mới dưới 3% thì gộp vào nhãn gần nhất, trừ khi có câu hỏi cần riêng nó.
- Nhãn dưới 1% chỉ gộp khi không phục vụ câu hỏi nào **và** không giúp đánh giá chất lượng dữ liệu.
- Quyết theo tỷ lệ đo được; khoảng tin cậy trùm lên ngưỡng thì ghi "sát ngưỡng".

→ 3% và 1% là ngưỡng A đề xuất ngày 22/11, không có căn cứ thống kê nào được ghi lại. Ngay cả nhãn đo được đúng 3% (18/600) cũng có khoảng tin cậy Wilson 1,9%–4,7%.

**Làm.** A viết hướng dẫn gán lô K (phiếu mỗi chiều một cột, cách mở bằng Excel để khỏi hỏng ô). A gán lô K, rồi gán lại 500 bình luận lô 1–5 theo bộ nhãn, đọc từ chữ bình luận chứ không suy từ mã cũ (B7).

**Tài liệu:** [đặc tả bộ nhãn mục 7](../3-gan-nhan/dac-ta-bo-nhan.md#7-trưởng-nhóm-đã-quyết-khi-duyệt-2511), [đặc tả khám phá nhãn mục 9](../3-gan-nhan/dac-ta-kham-pha-nhan.md#9-so-ba-nguồn-và-chốt-bộ-nhãn-b8), [hướng dẫn gán lô K](../3-gan-nhan/huong-dan-gan-lo-k.md), [kế hoạch: quyết định 10, 11](ke-hoach.md#5-quyết-định).

---

## Đợt 8. 26/11 sáng: gán mù lô K (B6)

**Hỏi.** Hai bên gán theo bộ nhãn trên 100 bình luận chưa ai đọc có ra giống nhau không? Đây là phép đo duy nhất cho biết bộ nhãn có rõ, và nhãn của AI có tin được không.

**Làm.** A và B gán lô K, không xem của nhau. Chiều nhiều nhãn xét ngưỡng bằng **kappa gộp** (B quyết 26/11): mỗi cặp (bình luận, nhãn) là một câu có/không, tính chung cả chiều.

**Kết quả** (n = 100; chiều 2 chỉ tính 65 bình luận cả hai cùng gán `dien_thoai`):

| Chiều | Đồng ý thô | κ | Đạt 0,6 |
|---|---|---|---|
| 1. Nói về cái gì | 87,0% | 0,72 | đạt |
| 2. Nói về phần nào | 70,8% trùng cả tập | 0,81 (gộp) | đạt |
| 3. Viết để làm gì | 76,0% trùng cả tập | 0,83 (gộp) | đạt |
| 4. Thái độ (79 cặp) | 86,1% trùng cả tập | từng nhãn 0,77–0,86 | đạt |
| 5. Đã dùng máy | 97,0% | 0,83 | đạt |
| 6. Gọi tên máy | 95,0% | 0,92 | đạt |

**Nhãn yếu:** `khong_xac_dinh` (chiều 1) −0,03, `dua` 0,42, `mua_ban` 0,57, `thong_tin` 0,59. Có 52/100 bình luận lệch ít nhất một chiều; A đề xuất cách phân xử, B duyệt từng ca.

→ Bộ nhãn dùng được ở mọi chiều. Nhưng ba nhãn trên phải sửa định nghĩa trước khi gán chính thức.

→ Thêm luật 8: câu mẫu dự minigame là `ngu_canh`, kể cả khi khen máy. Luật 9: yêu cầu test kèm một thông tin về máy là `dien_thoai`.

**Giới hạn.** B gán theo hướng dẫn do A viết, nên kappa có thể cao hơn hai người độc lập thật. n = 100 nên kappa của nhãn dưới khoảng 10 bình luận dao động mạnh.

**Tài liệu:** [báo cáo lô K](../3-gan-nhan/bao-cao-lo-k.md), [đặc tả mục 7b](../3-gan-nhan/dac-ta-kham-pha-nhan.md#7-kiểm-b6), `src/labeling/lot_k.py`, `data/kham-pha/phan_xu_lo_K.md`.

---

## Đợt 9. 26/11: B kiểm nhãn của A, tính phân bố (B7)

**Hỏi.** Nhãn A gán cho 500 bình luận lô 1–5 sai bao nhiêu? Mỗi nhãn chiếm bao nhiêu phần trăm?

**Làm, đợt kiểm 1.** B kiểm 100 bình luận ngẫu nhiên và mọi bình luận A đánh dấu chưa chắc. Tỷ lệ phải sửa chỉ tính trên phần ngẫu nhiên:

```text
khoảng Wilson:  tâm = (x + z²/2)/(n + z²),   nửa độ rộng = z/(n + z²) · √( x(n − x)/n + z²/4 )
```

**Kết quả.** 17/100 bình luận phải sửa, 17,0% [10,9; 25,5]. Phần A đánh dấu chưa chắc: 80/200 phải sửa. Theo cột, số bình luận phải sửa nhiều nhất ở mục đích (43), chiều 1 (41), chiều 2 và thái độ (34).

→ 17% là cao, và lỗi có quy luật. B quyết **kiểm toàn bộ** lô 1–5 (đợt 2). Xong cả 500 bình luận.

**Phân bố.** Mẫu 600 = lô 1–5 đã kiểm + lô K đã phân xử. Khoảng tin cậy chính là **bootstrap theo video**: bốc lại có hoàn lại 507 video, 2.000 lần, lấy phân vị 2,5% và 97,5%. Lý do: bình luận cùng video giống nhau hơn bình luận ngẫu nhiên.

```text
deff ≈ (nửa độ rộng bootstrap / nửa độ rộng Wilson)²       cỡ mẫu hiệu dụng = n / deff
```

| Nhãn | Mẫu số | % | KTC 95% (bootstrap video) |
|---|---|---|---|
| `dien_thoai` | 600 | 65,8 | [61,5; 69,9] |
| `ngu_canh` | 600 | 18,5 | [14,9; 22,4] |
| `nguoi_binh_luan` | 600 | 8,0 | [5,9; 10,3] |
| `may_chung` | 395 `dien_thoai` | 20,8 | [16,9; 24,6] |
| `gia` | 395 | 14,4 | [10,8; 18,2] |
| `thiet_ke` | 395 | 13,7 | [10,4; 17,2] |
| `hieu_nang` | 395 | 13,4 | [10,0; 17,0] |
| `mua_ban` | 395 | 10,9 | [8,1; 14,1] |
| `danh_gia` | 600 | 40,0 | [35,9; 44,2] |
| `bao_loi` | 600 | 1,3 | [0,5; 2,3] |
| `co` (đã dùng máy) | 600 | 6,3 | [4,3; 8,5] |
| `khong_nhac` (không gọi tên máy) | 600 | 57,0 | [52,7; 61,4] |

→ Cứ 3 bình luận thì khoảng 1 không nói về điện thoại. Nhiễu chính là chuyện ngoài lề (video, người review, cãi nhau), không phải quảng cáo (2/600).

→ Trong 395 bình luận về điện thoại, chỉ 311 nêu được ít nhất một khía cạnh. Có khen: 19,5% [15,9; 23,7]; có chê: 25,3% [21,3; 29,8]; chỉ "không đánh giá": 46,8% [42,0; 51,8] (Wilson). → Chỉ tích cực / tiêu cực là không đủ, đúng như ghi chép gốc lo.

→ Câu 5 thiếu dữ liệu: chỉ 8 bình luận báo lỗi máy mình. Nhãn chiều 2 nào cũng có khen + chê dưới 30, nên chưa kết luận được khía cạnh nào bị khen hay chê nhiều hơn.

→ `minigame` có deff 3,67: dồn vào vài video, đúng lý do phải dùng bootstrap theo video.

**Tài liệu:** [báo cáo phân bố](../3-gan-nhan/bao-cao-phan-bo-nhan.md), [đặc tả mục 7c, 8](../3-gan-nhan/dac-ta-kham-pha-nhan.md#8-tính-phân-bố-b7), `src/labeling/distribution.py`, `notebooks/3_label_distribution.ipynb`.

---

## Đợt 10. 26/11: so ba nguồn, chốt bộ nhãn (B8)

**Hỏi.** Áp luật mục 9 lên từng nhãn: giữ, thêm, gộp hay bỏ? HAC có tìm ra khía cạnh nào mẫu bỏ sót không?

**Làm.** Code tính tỷ lệ, khoảng tin cậy, kappa lô K cho 44 nhãn, ghi "luật nói gì". A xét thêm nhãn phục vụ câu hỏi nào và đề xuất. B duyệt cả bảng.

**Kết quả.** 22 giữ, 19 thêm, 3 gộp:

| Gộp | Vào | Vì sao |
|---|---|---|
| `nhiet_do` (1,8%) | `hieu_nang` | Nhãn mới dưới 3%; về lại như bộ đặt sẵn "Hiệu năng (gồm nóng máy)" |
| `am_thanh` (2,8%) | `phan_cung_khac` | Nhãn mới dưới 3% |
| `khong_noi_dung` (0,8%) | `khong_xac_dinh` | Dưới 3%; emoji, dấu câu thì code nhận ra được |

- `bao_loi` 1,3% vẫn **thêm**, vì Q5 cần riêng nó (ngoại lệ có sẵn trong luật).
- `mua_ban` 10,9% được **thêm**, dù κ lô K 0,57; định nghĩa được sửa.
- Nhãn đặt sẵn không đưa vào: "spam khác", "chưa dùng" (gộp vào `khong_ro`), "chỉ suy được máy từ video" (trái quy tắc gán theo chữ viết). 9 loại lỗi để tầng sau.

**Đối chiếu HAC** (do AI làm, chưa có người kiểm). Rà 100 ứng viên đầu: không có khía cạnh nào bộ nhãn chưa có. Đếm từ khóa trên cả bộ dữ liệu: `mua_ban` được nhắc trong 61.122 bình luận (12,9%), `camera` 48.438. Đây là số bình luận **có nhắc từ khóa**, không phải tỷ lệ của nhãn.

→ Ba nguồn khớp nhau: bộ nhãn từ dữ liệu phủ hết bộ đặt sẵn và HAC, và có thêm những thứ bộ đặt sẵn không có (`mua_ban`, `may_chung`, `hang_nguoi_dung`, cả chiều mục đích).

**Tài liệu:** [báo cáo khám phá nhãn](../3-gan-nhan/bao-cao-kham-pha-nhan.md), [đặc tả bộ nhãn mục 8](../3-gan-nhan/dac-ta-bo-nhan.md#8-bộ-nhãn-chốt-b8-2611), `src/labeling/b8.py`.

---

## Đợt 11. 26/11 chiều: sửa nhãn yếu, kiểm lại trên lô D2, bàn giao

**Hỏi.** Sửa định nghĩa `dua`, `khong_xac_dinh` rồi thì hai bên có gán giống nhau hơn không? Thêm trường tên máy có làm được không?

**Làm.** Sửa định nghĩa theo các ca lệch ở lô K. Thêm trường `ten_may` (chiều 6 trước đó chỉ ghi có gọi tên hay không, chưa ghi máy nào; Q3, Q4 cần biết). Gán mù 50 bình luận đầu lô D2, chưa ai đọc.

**Kết quả** (n = 50): chiều 1 κ = 0,66; chiều 2 gộp 0,86; chiều 3 gộp 0,82; chiều 5 0,79; chiều 6 0,93. `khong_xac_dinh` chiều 1 lên 0,78 (lô K: gần 0). `dua` 0,66, nhưng chỉ có 1–2 ca. Tên máy khớp đúng ở 9/12 bình luận cả hai cùng gán `goi_ten_may`.

→ Mọi chiều vẫn đạt. Còn ba chỗ lệch, B quyết theo đề xuất: chỉ nêu tên máy khi yêu cầu test vẫn là `ngu_canh`; `tranh_luan` phải có chữ tỏ thái độ (κ 0,26 ở D2); ý định mua là `mua_ban` (κ 0,45 ở D2).

**Bàn giao.** Viết [hướng dẫn gán nhãn chính thức](../3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md), B duyệt 26/11. Cách ghi mới: nối nhận xét với máy bằng `@` (`camera:tich_cuc@s24u`), so sánh ghi bên hơn (`@s24u>ip15prm`), thêm cờ `tieng_viet`.

**Quyết định cùng ngày.** **Không chọn bộ 4 máy.** Dòng máy nào có trong dữ liệu thì phân tích hết; trước mắt lấy nhãn để làm mô hình phân loại cảm xúc. Đặc tả mục tiêu và đặc tả gán nhãn trên `main` phải sửa theo khi chép kết quả về.

**Tài liệu:** [báo cáo lô D2](../3-gan-nhan/bao-cao-lo-d2.md), [kế hoạch: quyết định 7, 12, 13](ke-hoach.md#5-quyết-định).

---

## Kết quả cuối cùng (26/11)

### Bộ nhãn chốt: 6 chiều, 41 nhãn

| Chiều | Nhãn |
|---|---|
| 1. Nói về cái gì (một nhãn) | `dien_thoai` · `ngu_canh` · `nguoi_binh_luan` · `khong_lien_quan` · `khong_xac_dinh` |
| 2. Nói về phần nào (nhiều nhãn): 11 khía cạnh | `pin_sac` · `man_hinh` · `hieu_nang` · `camera` · `thiet_ke` · `do_ben` · `phan_mem` · `phan_cung_khac` · `gia` · `mua_ban` · `bao_hanh_sua_chua` |
| 2. Ngoài khía cạnh, dự phòng | `may_chung` · `hang_nguoi_dung` · `khac` |
| 3. Viết để làm gì (nhiều nhãn) | `danh_gia` · `hoi` · `thong_tin` · `de_nghi` · `ban_than` · `bao_loi` · `tranh_luan` · `dua` · `cong_kich` · `minigame` · `quang_cao` · `xa_giao` · `khong_xac_dinh` |
| 4. Thái độ (theo cặp bình luận, nhãn chiều 2) | `tich_cuc` · `tieu_cuc` · `so_sanh` · `khong_danh_gia` |
| 5. Đã dùng máy (một nhãn) | `co` · `khong_ro` |
| 6. Máy được nhắc (một nhãn), kèm `ten_may` | `goi_ten_may` · `chi_hang` · `khong_nhac` |

Định nghĩa, ví dụ: [đặc tả bộ nhãn](../3-gan-nhan/dac-ta-bo-nhan.md). Cách gán: [hướng dẫn gán nhãn chính thức](../3-gan-nhan/huong-dan-gan-nhan-chinh-thuc.md).

### Độ tin cậy

| Phép đo | Kết quả |
|---|---|
| Lô K (n = 100, mù) | Mọi chiều κ ≥ 0,6 (0,72–0,92) |
| Lô D2 (n = 50, mù, sau khi sửa định nghĩa) | Mọi chiều κ ≥ 0,6 (0,66–0,93) |
| Nhãn A phải sửa (100 bình luận ngẫu nhiên) | 17,0% [10,9; 25,5] → B đã kiểm cả 500 |

### Điều trả lời được, điều chưa

- **Trả lời được:** bình luận v4 có những loại nội dung nào, và mỗi loại chiếm bao nhiêu trong cả bộ dữ liệu, kèm khoảng tin cậy ([báo cáo phân bố](../3-gan-nhan/bao-cao-phan-bo-nhan.md)).
- **Chưa trả lời:** Q1–Q6. Mẫu lấy trên cả v4 (139 máy, nhiều năm), nên không suy ra số cho riêng một máy. Câu 5 cần mẫu riêng các bình luận báo lỗi. Khen hay chê theo từng khía cạnh cần mẫu lớn hơn: nhãn nào cũng có dưới 30 lượt khen + chê.

### Giới hạn

- Người mã hóa A là AI và chính A đã soạn bộ nhãn đặt sẵn trên `main`, nên có thể bị nó dẫn dắt (hiệu ứng mỏ neo). Đo bằng lô K, lô D2 và tỷ lệ phải sửa, nhưng không loại hết được.
- B gán theo hướng dẫn do A viết, nên kappa có thể cao hơn hai người độc lập thật.
- Kappa trên 100 và 50 bình luận dao động mạnh với nhãn hiếm.
- Ngưỡng 3%, 1% và κ ≥ 0,6 là ngưỡng tự đặt, không phải kết quả thống kê.
- Đối chiếu HAC do AI làm, không ai chấm.

### Việc sau nhánh

Gán nhãn chính thức theo hướng dẫn mới (mẫu chất lượng dữ liệu và tập test hai người gán), làm mô hình, rồi chép kết quả về `main` bằng cách chép file. Thứ tự ở [kế hoạch mục 4](ke-hoach.md#4-sau-nhánh-này).

---

## Phụ lục: những chỗ đã sai và bài học

| Đợt | Sai | Vì sao | Sửa, bài học |
|---|---|---|---|
| 2 | Chạy lại lấy mẫu có thể xóa phiếu đã điền | Code ghi đè không hỏi | Giữ phiếu đã có chữ; ghi đè phải nói rõ `--ghi-de` |
| 3 | Câu ví dụ HAC đổi mỗi lần chạy | Duyệt tập hợp không có thứ tự | `sorted`, kiểm bằng hai `PYTHONHASHSEED` |
| 4 | Tên `@a@b` chưa được che | Biểu thức chính quy thiếu ca viết liền | Sửa biểu thức; sau thêm che `+Tên Họ` |
| 5 | Một ô phiếu B thành `#NAME?` | Excel hiểu ô bắt đầu bằng `+` là công thức | Mở CSV bằng Data → From Text/CSV; chữ bình luận lấy từ phiếu A |
| 5 | Kappa thấp ở `nhắc`, `kể`, `nhận xét` | Luật mơ hồ | Sửa bảng hành vi; nhãn đo bằng kappa, không bằng % giống nhau |
| 6 | Dùng lẫn *nhãn* và *khía cạnh* | Chưa có bảng thuật ngữ | Bảng thuật ngữ ở đặc tả là nguồn duy nhất |
| 7 | "3% của cái gì" không rõ | Đặc tả bỏ mất ví dụ về mẫu số | Ghi mẫu số từng chiều vào đặc tả mục 9 |
| 9 | 17% nhãn của A phải sửa | Lỗi có quy luật ở mục đích, chiều 1 | Kiểm toàn bộ, không chỉ 100 mẫu |
| 8, 11 | `khong_xac_dinh`, `dua`, `mua_ban` lệch ở lô K | Định nghĩa chưa rõ | Sửa định nghĩa, kiểm lại trên D2 |

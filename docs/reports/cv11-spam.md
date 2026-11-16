# Công việc 11: Phát hiện spam — so sánh bộ luật với mô hình ML

> Mục đích: Báo cáo kết quả so sánh bộ luật spam `rule-v0` với mô hình ML và phương án được chọn; file này do `python -m src.processing.spam.report` sinh ra từ [spam_eval_v1.json](../../src/processing/spam/results/spam_eval_v1.json), không sửa tay.

Người thực hiện: Nguyễn Lê Quân. Dữ liệu: `clean_data v1.0` (109.344 bình luận, SHA-256 `df4c72c25a15…`). Guideline: `spam-guideline-v1.1`.

**Kết quả TẠM THỜI.** Toàn bộ nhãn hiện do AI gán (`label_source = llm`). Theo quy định của nhóm, tập test phải có người duyệt trước khi số liệu được đưa vào báo cáo chính thức; cách duyệt ở mục 9.

## 1. Kết luận

**Chọn phương án kết hợp:** một bình luận là spam khi `rule-v0` gắn cờ vì nội dung hoặc hình thức **và** mô hình ML (`lr-char`) xác nhận. "Không phải tiếng Việt" và "không có chữ" được tách thành kết quả riêng, không còn tính là spam.

| | `rule-v0` nguyên trạng | Phương án kết hợp |
|---|---:|---:|
| Precision (quy về toàn bộ dữ liệu) | 0,14 | 0,87 |
| Recall | 0,78 | 0,65 |
| F1 | 0,24 | 0,74 |
| Số bình luận bị loại trên toàn bộ dữ liệu | 3.233 | 452 |

Lý do chọn:

- `rule-v0` loại 3.233 bình luận (3,0%), nhưng ước tính chỉ khoảng 0,60% dữ liệu là spam thật (khoảng 654 bình luận). Cứ 7 bình luận bị luật loại thì khoảng 6 bình luận không phải spam, trong đó có ý kiến thật về sản phẩm.
- Mô hình ML và phương án kết hợp cho cùng kết quả trên tập test. Trên toàn bộ dữ liệu hai phương án chỉ khác nhau 4 bình luận. Chọn phương án kết hợp vì nó không thể gắn cờ một bình luận mà luật không gắn cờ, nên rủi ro loại nhầm ở 106.111 bình luận mà luật không gắn cờ bằng 0 theo thiết kế, và mỗi quyết định vẫn kèm lý do đọc được (`spam_reasons`).
- Cái giá: recall thấp hơn luật (0,65 so với 0,78). Chấp nhận được vì spam bị sót gần như không sinh ra mention khía cạnh nào, còn ý kiến thật bị loại nhầm thì làm lệch Q1–Q5.

Khoảng tin cậy còn rộng vì tập test chỉ có 30 spam; xem mục 5 và mục 8.

## 2. Dữ liệu gán nhãn

Spam hiếm, nên rút ngẫu nhiên 500 bình luận sẽ chỉ có vài spam và gần như không thấy spam mà luật bỏ sót. Mẫu 640 bình luận được **rút theo tầng** dựa trên đầu ra của `rule-v0`, ngẫu nhiên đơn giản trong từng tầng (seed cố định). Mỗi dòng mang trọng số N/n của tầng để quy kết quả về toàn bộ dữ liệu.

| Tầng | Quần thể N | Mẫu n | train / test | Spam | Tỷ lệ spam |
|:---|---:|---:|---:|---:|---:|
| Luật gắn cờ: link, SĐT, mời liên hệ, thương mại | 1.191 | 150 | 76 / 74 | 62 | 41% |
| Luật gắn cờ: chỉ vì lặp ký tự / lặp từ | 678 | 70 | 39 / 31 | 2 | 3% |
| Luật gắn cờ: không có chữ cái / rỗng | 931 | 40 | 25 / 15 | 0 | 0% |
| Luật gắn cờ: chỉ vì "không phải tiếng Việt" | 433 | 60 | 40 / 20 | 0 | 0% |
| Luật không bắt: đoạn dài bị dán lặp ≥ 3 lần | 281 | 40 | 17 / 23 | 4 | 10% |
| Luật không bắt: có dấu hiệu quảng bá / dãy số | 3.035 | 80 | 48 / 32 | 3 | 4% |
| Luật không bắt: không có dấu hiệu nào | 102.795 | 200 | 123 / 77 | 0 | 0% |

- **Chia tập theo `video_id`** bằng mã băm cố định: 368 dòng train (199 video), 272 dòng test (139 video); không video nào nằm ở cả hai tập.
- **Quy trình gán:** hai lượt gán độc lập toàn bộ mẫu theo [guideline](../spam-labeling-guideline.md), không được xem tầng hay cờ của luật; một lượt thứ ba phân giải các dòng lệch.
- **Độ đồng thuận:** `label` khớp 98,4%, Cohen's kappa = 0,92; `lang` khớp 99,1%, kappa = 0,97. 15 dòng phải phân giải; các quy tắc rút ra đã bổ sung vào guideline v1.1.
- **Ai gán:** `A=llm:claude-fable-5-2;B=llm:claude-opus-5-5;adjudicator=llm:claude-fable-5-2`. Cả hai người gán và người phân giải đều là mô hình AI, nên kappa ở đây đo độ ổn định của guideline giữa hai mô hình, chưa phải đồng thuận giữa người với người.
- **Kết quả:** 71 spam / 569 không spam. Loại spam: `ad` 48, `channel_promo` 16, `flood` 5, `contact_sale` 2.

File nhãn [spam_labels_v1.tsv](../../src/processing/spam/labels/spam_labels_v1.tsv) chỉ chứa ID và nhãn. Nội dung bình luận được nối lại từ `clean_data.jsonl` và kiểm tra bằng mã băm từng dòng, nên không có nội dung hay số điện thoại của người dùng nằm trong git.

## 3. Tỷ lệ spam trong dữ liệu

Ước lượng từ mẫu phân tầng: **0,60%** bình luận là spam (khoảng tin cậy 95%: 0,46% – 0,75%), tức khoảng 654 bình luận. Trong 200 bình luận rút từ tầng "luật không bắt, không có dấu hiệu nào" không có spam nào; theo quy tắc số 3, tỷ lệ spam ở tầng này dưới 1,5% với độ tin cậy 95%.

Con số "khoảng 6%" trong mô tả công việc và 2,96% trong báo cáo tiền xử lý là tỷ lệ **bị luật gắn cờ**, không phải tỷ lệ spam.

## 4. Cách so sánh

- **Baseline:** `rule-v0` trong `src/processing/cleaner`, giữ nguyên. Vì luật gộp cả "không phải tiếng Việt" và "không có chữ" vào spam, báo cáo thêm ba cách đọc hẹp dần để so sánh công bằng.
- **Mô hình ML:** năm ứng viên TF-IDF (từ, ký tự, kèm đặc trưng hình thức) với Naive Bayes, Logistic Regression, Linear SVM. Link và số điện thoại được thay bằng token cố định trước khi vector hóa.
- **Chọn mô hình và ngưỡng chỉ trên train:** cross-validation 5 phần gom nhóm theo video. Chọn mô hình theo average precision có trọng số; chọn ngưỡng theo F0,5 có trọng số (coi precision quan trọng gấp đôi recall).
- **Tập test dùng đúng một lần** để ra bảng ở mục 5.
- **Chỉ số:** precision, recall, F1 của lớp spam, không dùng accuracy. Cột "quy về toàn bộ dữ liệu" dùng trọng số tầng; khoảng tin cậy 95% bằng bootstrap phân tầng 2.000 lần.

Kết quả cross-validation trên train (điểm out-of-fold):

| Mô hình | AP (quần thể) | AP (mẫu) | Precision | Recall | F0,5 |
|:---|---:|---:|---:|---:|---:|
| `nb-word` | 0,59 | 0,82 | 0,97 | 0,57 | 0,85 |
| `lr-word` | 0,61 | 0,83 | 0,94 | 0,64 | 0,86 |
| `lr-char` ✔ | 0,75 | 0,92 | 0,97 | 0,64 | 0,88 |
| `lr-word+char+meta` | 0,75 | 0,92 | 0,97 | 0,59 | 0,86 |
| `svm-word+char+meta` | 0,75 | 0,91 | 0,97 | 0,59 | 0,86 |

Precision, recall, F0,5 tính tại ngưỡng tốt nhất của từng mô hình. Mô hình được chọn: `lr-char`, ngưỡng 0,704. Cùng ngưỡng đó được chọn cho phương án kết hợp.

## 5. Kết quả trên tập test

| Phương pháp | TP / FP / FN (mẫu) | Precision (KTC 95%) | Recall (KTC 95%) | F1 (KTC 95%) |
|:---|---:|---:|---:|---:|
| rule-v0 (nguyên trạng) | 25 / 115 / 5 | 0,14 (0,09 – 0,19) | 0,78 (0,56 – 0,97) | 0,24 (0,17 – 0,30) |
| rule-v0 bỏ lý do ngôn ngữ | 25 / 95 / 5 | 0,16 (0,11 – 0,21) | 0,78 (0,56 – 0,97) | 0,26 (0,19 – 0,33) |
| rule-v0 chỉ nội dung + hình thức | 25 / 80 / 5 | 0,23 (0,16 – 0,30) | 0,78 (0,56 – 0,97) | 0,35 (0,26 – 0,45) |
| rule-v0 chỉ nội dung | 24 / 50 / 6 | 0,32 (0,22 – 0,43) | 0,74 (0,53 – 0,95) | 0,45 (0,33 – 0,57) |
| ML | 21 / 3 / 9 | 0,87 (0,72 – 1,00) | 0,65 (0,45 – 0,87) | 0,74 (0,58 – 0,90) |
| Kết hợp (luật nội dung + hình thức, ML xác nhận) | 21 / 3 / 9 | 0,87 (0,72 – 1,00) | 0,65 (0,45 – 0,87) | 0,74 (0,58 – 0,90) |

Precision, recall, F1 đã quy về toàn bộ dữ liệu. Cột TP / FP / FN là số dòng đếm trực tiếp trên 272 dòng test.

Kiểm định McNemar chính xác (trên mẫu, không trọng số), so số dòng mà chỉ một trong hai phương pháp phân loại đúng:

| So sánh (A so với B) | Chỉ A đúng | Chỉ B đúng | p |
|:---|---:|---:|---:|
| ML so với rule-v0 (nguyên trạng) | 112 | 4 | < 0,001 |
| Kết hợp (luật nội dung + hình thức, ML xác nhận) so với rule-v0 (nguyên trạng) | 112 | 4 | < 0,001 |
| rule-v0 chỉ nội dung + hình thức so với rule-v0 (nguyên trạng) | 35 | 0 | < 0,001 |
| Kết hợp (luật nội dung + hình thức, ML xác nhận) so với ML | 0 | 0 | 1,000 |

Phương án kết hợp và mô hình ML đều phân loại đúng nhiều hơn `rule-v0` có ý nghĩa thống kê. Giữa phương án kết hợp và mô hình ML không có dòng nào khác nhau trên tập test.

## 6. Áp dụng lên toàn bộ dữ liệu

Số bình luận từng phương án gắn cờ trên 109.344 bình luận. Bảng này không đo độ chính xác (không có nhãn cho toàn bộ dữ liệu); nó cho thấy mô hình ML không gắn cờ tràn lan ở vùng luật không bắt.

| Tầng | N | rule-v0 | ML | Kết hợp |
|:---|---:|---:|---:|---:|
| Luật gắn cờ: link, SĐT, mời liên hệ, thương mại | 1.191 | 1.191 | 451 | 451 |
| Luật gắn cờ: chỉ vì lặp ký tự / lặp từ | 678 | 678 | 1 | 1 |
| Luật gắn cờ: không có chữ cái / rỗng | 931 | 931 | 0 | 0 |
| Luật gắn cờ: chỉ vì "không phải tiếng Việt" | 433 | 433 | 0 | 0 |
| Luật không bắt: đoạn dài bị dán lặp ≥ 3 lần | 281 | 0 | 0 | 0 |
| Luật không bắt: có dấu hiệu quảng bá / dãy số | 3.035 | 0 | 3 | 0 |
| Luật không bắt: không có dấu hiệu nào | 102.795 | 0 | 1 | 0 |
| **Tổng** | **109.344** | **3.233** | **456** | **452** |

## 7. Tách "không phải tiếng Việt" khỏi spam

`rule-v0` coi mọi bình luận không phải tiếng Việt là spam. Hàm nhận diện trong cleaner còn có lỗi: tập ký tự tiếng Việt chứa cả nguyên âm không dấu, nên câu tiếng Anh có nguyên âm được coi là tiếng Việt, còn thứ bị gắn "không phải tiếng Việt" chủ yếu là emoji, ":)))", "vl", "tks". Trên toàn bộ dữ liệu luật gắn 1.372 bình luận là không phải tiếng Việt.

[language.py](../../src/processing/spam/language.py) trả về ba giá trị: `vi`, `other` (ngôn ngữ khác), `none` (không xác định được: emoji, số, tên máy). Trên toàn bộ dữ liệu: `vi` 105.953, `other` 495, `none` 2.896.

Đánh giá trên 233 dòng test có ngôn ngữ xác định:

|  | rule-v0 | language.py |
|:---|---:|---:|
| Bình luận tiếng Việt bị xếp nhầm | 3 / 229 | 1 / 229 |
| Bình luận ngôn ngữ khác phát hiện được | 1 / 4 | 2 / 4 |
| Báo nhầm là ngôn ngữ khác | 3 | 0 |

Tập test chỉ có 4 bình luận ngôn ngữ khác, nên **chưa đủ để kết luận về khả năng phát hiện**. Điều đo được chắc hơn là tỷ lệ loại nhầm tiếng Việt, vì có 229 dòng.

## 8. Phân tích lỗi trên tập test

**`rule-v0` báo nhầm 115 dòng.** Chia theo lý do mạnh nhất mà luật đưa ra (cột "Spam thật" là số dòng cùng lý do được gắn cờ đúng):

| Lý do của luật | Báo nhầm | Spam thật | Bình luận bị báo nhầm trông thế nào |
|:---|---:|---:|:---|
| Lặp ký tự / lặp từ | 30 | 1 | Kéo dài chữ hoặc dấu câu để biểu cảm: "rất ngầu :)))))))", "xễu cái đùn 😂😂😂😂😂😂" |
| Có link hoặc số điện thoại | 28 | 24 | Bài dự thi minigame; link dẫn chứng trong tranh luận |
| Chỉ vì "không phải tiếng Việt" | 20 | 0 | Bình luận ngắn không có nguyên âm: "Lg v30", "vl", ":v" |
| Không có chữ cái | 15 | 0 | Emoji, dấu câu, mốc thời gian: "😂😂😂", "2:30 5,4,2 😂" |
| Có từ Zalo, inbox, liên hệ… | 12 | 0 | Nhắc ứng dụng trong câu chuyện thật: "iPhone cũ không tải được Zalo" |
| Có từ Shopee, Lazada, link mua… | 10 | 0 | Hỏi chỗ mua, nói giá: "Cho tớ xin link mua áo với", "9 triệu sáu trên Lazada" |

Trong nhóm link hoặc số điện thoại, đọc tay từng dòng báo nhầm cho thấy: 17 dòng là bài dự thi minigame của một video (kênh yêu cầu ghi SĐT, link Facebook và dự đoán), 10 dòng là link dẫn chứng hoặc gợi ý trong lúc trao đổi, 1 dòng có SĐT nhưng không rao bán gì.

**Phương án kết hợp báo nhầm 3 dòng** (S0311, S0325, S0432): cả ba đều là người xem dán link để trả lời hoặc gợi ý cho người khác. Về hình thức chúng giống hệt spam kéo view; phân biệt được phải đọc bình luận cha, mà mô hình hiện chỉ đọc nội dung bình luận.

**Phương án kết hợp bỏ sót 9 dòng:**

| Nguyên nhân | Dòng | Ghi chú |
|---|---|---|
| Đoạn văn dán nguyên văn ở nhiều video, không có link | S0022, S0429, S0468 | Luật không có lý do nào bắt được; cần đặc trưng "nội dung trùng lặp giữa các video" |
| Xin đăng ký kênh, không có link hoặc link rút gọn | S0029, S0203 | Luật không bắt; mô hình ML đứng riêng cũng cho điểm thấp |
| Link kèm chú thích ngắn | S0332 | Điểm 0,60, dưới ngưỡng 0,70 |
| Quảng cáo ngoài lĩnh vực điện thoại | S0419 | Tập train gần như chỉ có quảng cáo điện thoại |
| Rao bán không dấu, rất ngắn | S0488 | "Co thi lien he zalo cho e …" |
| Chuỗi gõ bừa ngắn | S0105 | 9 ký tự |

## 9. Hạn chế và việc còn lại

1. **Nhãn chưa có người duyệt.** Đây là hạn chế lớn nhất. Để hoàn tất: chạy `python -m src.processing.spam.labels export-review`, mở `data/labels/spam/review_test.csv` bằng Excel, duyệt 272 dòng test (đúng thì gõ `x` vào cột `ok`, sai thì điền nhãn đúng), rồi `import-review`, `train`, `report`. Lệnh `import-review` cũng in tỷ lệ AI gán đúng so với người duyệt.
2. **Ít spam trong tập test** (30 dòng), nên khoảng tin cậy của recall rộng. Recall còn phụ thuộc nhiều vào vài dòng spam ở các tầng có trọng số lớn.
3. **Trần recall của phương án kết hợp là recall của luật.** Hai loại spam luật không bắt (đoạn văn dán lặp, xin đăng ký kênh) cần thêm luật hoặc đặc trưng mới; ước tính luật bỏ sót khoảng 22% số spam.
4. **Mô hình chỉ đọc nội dung bình luận**, không đọc bình luận cha, nên nhầm link trả lời câu hỏi với link kéo view.
5. **Chưa tích hợp vào `cleaner`.** `clean_data.jsonl` v1.0 vẫn mang cờ của `rule-v0`. Thay cờ spam sẽ đổi checksum của bản dữ liệu chung, nên cần cả nhóm đồng ý và phát hành phiên bản dữ liệu mới. Trong lúc chờ, `python -m src.processing.spam.predict` ghi kết quả ra file riêng theo `comment_id`.
6. **Khung đánh giá chung (Công việc 7) chưa có** tại thời điểm làm, nên cách chia tập theo video ở đây là của riêng công việc này. Khi có `split.json` chung thì cần đối chiếu.

## 10. Chạy lại

```powershell
python -m pip install -r src/processing/spam/requirements.txt
python src/processing/run_cleaning.py --verify      # dữ liệu phải đúng bản chuẩn v1.0
python -m src.processing.spam.train                 # huấn luyện + đánh giá, ghi spam_eval_v1.json
python -m src.processing.spam.report                # sinh lại file này
python -m pytest tests/test_spam_detection.py -q
```

Môi trường đã chạy: scikit-learn 1.7.2, numpy 2.5.5, seed 42. Mô hình lưu tại `data/models/spam-lr-v1.joblib` (không vào git), SHA-256 `7260b9fb7931e50c…`.

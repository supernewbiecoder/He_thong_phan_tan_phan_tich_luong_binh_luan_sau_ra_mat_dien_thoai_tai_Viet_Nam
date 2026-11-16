"""Sinh báo cáo Công việc 11 từ file kết quả, để số trong báo cáo luôn khớp với code.

Chạy:  python -m src.processing.spam.report
Đầu ra: docs/reports/cv11-spam.md (ghi đè). Không sửa tay file đó; sửa ở đây.
"""
import json
import sys
from typing import Dict, List, Optional

from . import config

REPORT_PATH = config.REPO_ROOT / "docs" / "reports" / "cv11-spam.md"
BASELINE = "rule-v0 (nguyên trạng)"
ML = "ML"
HYBRID = "Kết hợp (luật nội dung + hình thức, ML xác nhận)"

STRATUM_NAMES = {
    "rule_content": "Luật gắn cờ: link, SĐT, mời liên hệ, thương mại",
    "rule_form": "Luật gắn cờ: chỉ vì lặp ký tự / lặp từ",
    "rule_notext": "Luật gắn cờ: không có chữ cái / rỗng",
    "rule_nonvn_only": "Luật gắn cờ: chỉ vì \"không phải tiếng Việt\"",
    "unflagged_dup": "Luật không bắt: đoạn dài bị dán lặp ≥ 3 lần",
    "unflagged_suspect": "Luật không bắt: có dấu hiệu quảng bá / dãy số",
    "unflagged_rest": "Luật không bắt: không có dấu hiệu nào",
}


def num(value: Optional[float], digits: int = 2) -> str:
    """Số thập phân kiểu Việt (dấu phẩy); None thành gạch ngang."""
    return "–" if value is None else f"{value:.{digits}f}".replace(".", ",")


def pct(value: Optional[float], digits: int = 1) -> str:
    return "–" if value is None else f"{value * 100:.{digits}f}".replace(".", ",") + "%"


def count(value: float) -> str:
    return f"{round(value):,}".replace(",", ".")


def interval(bounds: Optional[List[float]]) -> str:
    return "–" if not bounds else f"{num(bounds[0])} – {num(bounds[1])}"


def table(header: List[str], rows: List[List[str]], align: str = "") -> str:
    align = align or "l" + "r" * (len(header) - 1)
    marks = {"l": ":---", "r": "---:", "c": ":---:"}
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(marks[a] for a in align) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def build(results: Dict[str, object]) -> str:
    meta, agreement = results["meta"], results["agreement"]
    cv, tests, full = results["cross_validation"], results["test"], results["full_dataset"]
    strata = json.loads((config.LABELS_DIR / "spam_strata_v1.json").read_text("utf-8"))["strata"]
    prevalence = results["prevalence"]["spam"]
    base, ml, hybrid = (tests[name]["population"] for name in (BASELINE, ML, HYBRID))
    verified = meta["test_human_verified"]

    status = ("Nhãn tập test đã có người duyệt." if verified else
              "**Kết quả TẠM THỜI.** Toàn bộ nhãn hiện do AI gán (`label_source = llm`). "
              "Theo quy định của nhóm, tập test phải có người duyệt trước khi số liệu được "
              "đưa vào báo cáo chính thức; cách duyệt ở mục 9.")

    sample_rows = []
    for name, info in strata.items():
        cells = [results["sample"].get(f"{name}/{split}", {"n": 0, "n_spam": 0}) for split in ("train", "test")]
        n_spam = sum(cell["n_spam"] for cell in cells)
        sample_rows.append([STRATUM_NAMES[name], count(info["N"]), str(info["n"]),
                            f"{cells[0]['n']} / {cells[1]['n']}", str(n_spam), pct(n_spam / info["n"], 0)])

    cv_rows = [[f"`{name}`" + (" ✔" if name == cv["selected"] else ""),
                num(item["average_precision_population"]), num(item["average_precision_sample"]),
                num(item["precision_population"]), num(item["recall_population"]), num(item["f05_population"])]
               for name, item in cv["candidates"].items()]

    test_rows = []
    for name, item in tests.items():
        sample, pop, ci = item["sample"], item["population"], item["population_ci95"]
        test_rows.append([
            name, f"{int(sample['tp'])} / {int(sample['fp'])} / {int(sample['fn'])}",
            f"{num(pop['precision'])} ({interval(ci['precision'])})",
            f"{num(pop['recall'])} ({interval(ci['recall'])})",
            f"{num(pop['f1'])} ({interval(ci['f1'])})",
        ])

    mcnemar_rows = [[name, str(item["only_a_correct"]), str(item["only_b_correct"]),
                     "< 0,001" if item["p_value"] < 0.001 else num(item["p_value"], 3)]
                    for name, item in results["mcnemar"].items()]

    full_rows = [[STRATUM_NAMES[name], count(cell["N"]), count(cell["rule_v0"]), count(cell["ml"]),
                  count(cell["hybrid"])] for name, cell in full["by_stratum"].items()]
    full_rows.append(["**Tổng**"] + [f"**{count(full['total'][key])}**" for key in ("N", "rule_v0", "ml", "hybrid")])

    language = results["language"]
    lang_rule, lang_new = language["rule-v0 (is_vietnamese = false)"], language["language.py (lang = other)"]
    vi_rule = language["rule-v0: tiếng Việt bị coi là không phải tiếng Việt"]
    vi_new = language["language.py: tiếng Việt bị xếp nhầm khác 'vi'"]
    spam_types = ", ".join(f"`{name}` {n}" for name, n in
                           sorted(results["spam_types"].items(), key=lambda kv: -kv[1]))
    n_spam = sum(results["spam_types"].values())
    flag_rate = results["prevalence"]["flag_rate"][BASELINE]
    false_positives = int(tests[BASELINE]["sample"]["fp"])
    hybrid_errors = results["errors"][HYBRID]

    groups = results["rule_v0_flags_by_reason_group"]
    reason_text = {
        "form": ("Lặp ký tự / lặp từ", "Kéo dài chữ hoặc dấu câu để biểu cảm: \"rất ngầu :)))))))\", \"xễu cái đùn 😂😂😂😂😂😂\""),
        "link_or_phone": ("Có link hoặc số điện thoại", "Bài dự thi minigame; link dẫn chứng trong tranh luận"),
        "language_only": ("Chỉ vì \"không phải tiếng Việt\"", "Bình luận ngắn không có nguyên âm: \"Lg v30\", \"vl\", \":v\""),
        "no_text": ("Không có chữ cái", "Emoji, dấu câu, mốc thời gian: \"😂😂😂\", \"2:30 5,4,2 😂\""),
        "contact_word": ("Có từ Zalo, inbox, liên hệ…", "Nhắc ứng dụng trong câu chuyện thật: \"iPhone cũ không tải được Zalo\""),
        "commerce_word": ("Có từ Shopee, Lazada, link mua…", "Hỏi chỗ mua, nói giá: \"Cho tớ xin link mua áo với\", \"9 triệu sáu trên Lazada\""),
    }
    reason_rows = [[reason_text[key][0], str(groups["false_positive"].get(key, 0)),
                    str(groups["true_positive"].get(key, 0)), reason_text[key][1]]
                   for key in sorted(reason_text, key=lambda k: -groups["false_positive"].get(k, 0))]
    analysed = {"fp": ["S0311", "S0325", "S0432"],
                "fn": ["S0022", "S0029", "S0105", "S0203", "S0332", "S0419", "S0429", "S0468", "S0488"]}
    stale = (hybrid_errors["false_positive"] != analysed["fp"]
             or hybrid_errors["false_negative"] != analysed["fn"])
    stale_note = ("> ⚠ Danh sách lỗi đã khác với lúc viết phần phân tích dưới đây (nhãn hoặc mô hình "
                  "đã đổi). Cần đọc lại các ca sai và cập nhật `report.py`." + "\n\n" if stale else "")
    one_in = max(round(1 / base["precision"]), 2) if base["precision"] else 0
    missed_share = pct(1 - base["recall"], 0) if base["recall"] is not None else "–"
    rest = [results["sample"].get(f"unflagged_rest/{split}", {"n": 0, "n_spam": 0}) for split in ("train", "test")]
    rest_n, rest_spam = sum(c["n"] for c in rest), sum(c["n_spam"] for c in rest)
    rest_note = (f"Trong {rest_n} bình luận rút từ tầng \"luật không bắt, không có dấu hiệu nào\" không có spam nào; "
                 f"theo quy tắc số 3, tỷ lệ spam ở tầng này dưới {pct(3 / rest_n)} với độ tin cậy 95%."
                 if rest_spam == 0 else
                 f"Trong {rest_n} bình luận rút từ tầng \"luật không bắt, không có dấu hiệu nào\" có {rest_spam} spam.")

    return f"""# Công việc 11: Phát hiện spam — so sánh bộ luật với mô hình ML

> Mục đích: Báo cáo kết quả so sánh bộ luật spam `rule-v0` với mô hình ML và phương án được chọn; file này do `python -m src.processing.spam.report` sinh ra từ [spam_eval_v1.json](../../src/processing/spam/results/spam_eval_v1.json), không sửa tay.

Người thực hiện: Nguyễn Lê Quân. Dữ liệu: `{meta['dataset']}` ({count(config.DATASET_LINES)} bình luận, SHA-256 `{meta['dataset_sha256'][:12]}…`). Guideline: `{meta['guideline_version']}`.

{status}

## 1. Kết luận

**Chọn phương án kết hợp:** một bình luận là spam khi `rule-v0` gắn cờ vì nội dung hoặc hình thức **và** mô hình ML (`{cv['selected']}`) xác nhận. "Không phải tiếng Việt" và "không có chữ" được tách thành kết quả riêng, không còn tính là spam.

| | `rule-v0` nguyên trạng | Phương án kết hợp |
|---|---:|---:|
| Precision (quy về toàn bộ dữ liệu) | {num(base['precision'])} | {num(hybrid['precision'])} |
| Recall | {num(base['recall'])} | {num(hybrid['recall'])} |
| F1 | {num(base['f1'])} | {num(hybrid['f1'])} |
| Số bình luận bị loại trên toàn bộ dữ liệu | {count(full['total']['rule_v0'])} | {count(full['total']['hybrid'])} |

Lý do chọn:

- `rule-v0` loại {count(full['total']['rule_v0'])} bình luận ({pct(flag_rate)}), nhưng ước tính chỉ khoảng {pct(prevalence['estimate'], 2)} dữ liệu là spam thật (khoảng {count(prevalence['estimated_count'])} bình luận). Cứ {one_in} bình luận bị luật loại thì khoảng {one_in - 1} bình luận không phải spam, trong đó có ý kiến thật về sản phẩm.
- Mô hình ML và phương án kết hợp cho cùng kết quả trên tập test. Trên toàn bộ dữ liệu hai phương án chỉ khác nhau {count(full['total']['ml'] - full['total']['hybrid'])} bình luận. Chọn phương án kết hợp vì nó không thể gắn cờ một bình luận mà luật không gắn cờ, nên rủi ro loại nhầm ở {count(full['total']['N'] - full['total']['rule_v0'])} bình luận mà luật không gắn cờ bằng 0 theo thiết kế, và mỗi quyết định vẫn kèm lý do đọc được (`spam_reasons`).
- Cái giá: recall thấp hơn luật ({num(hybrid['recall'])} so với {num(base['recall'])}). Chấp nhận được vì spam bị sót gần như không sinh ra mention khía cạnh nào, còn ý kiến thật bị loại nhầm thì làm lệch Q1–Q5.

Khoảng tin cậy còn rộng vì tập test chỉ có {int(tests[BASELINE]['sample']['tp'] + tests[BASELINE]['sample']['fn'])} spam; xem mục 5 và mục 8.

## 2. Dữ liệu gán nhãn

Spam hiếm, nên rút ngẫu nhiên 500 bình luận sẽ chỉ có vài spam và gần như không thấy spam mà luật bỏ sót. Mẫu {meta['n_labels']} bình luận được **rút theo tầng** dựa trên đầu ra của `rule-v0`, ngẫu nhiên đơn giản trong từng tầng (seed cố định). Mỗi dòng mang trọng số N/n của tầng để quy kết quả về toàn bộ dữ liệu.

{table(["Tầng", "Quần thể N", "Mẫu n", "train / test", "Spam", "Tỷ lệ spam"], sample_rows)}

- **Chia tập theo `video_id`** bằng mã băm cố định: {meta['n_train']} dòng train ({meta['n_videos_train']} video), {meta['n_test']} dòng test ({meta['n_videos_test']} video); không video nào nằm ở cả hai tập.
- **Quy trình gán:** hai lượt gán độc lập toàn bộ mẫu theo [guideline](../spam-labeling-guideline.md), không được xem tầng hay cờ của luật; một lượt thứ ba phân giải các dòng lệch.
- **Độ đồng thuận:** `label` khớp {pct(agreement['label_agreement'])}, Cohen's kappa = {num(agreement['label_kappa'])}; `lang` khớp {pct(agreement['lang_agreement'])}, kappa = {num(agreement['lang_kappa'])}. {agreement['resolution'].get('adjudicated', 0)} dòng phải phân giải; các quy tắc rút ra đã bổ sung vào guideline v1.1.
- **Ai gán:** `{agreement['annotators']}`. Cả hai người gán và người phân giải đều là mô hình AI, nên kappa ở đây đo độ ổn định của guideline giữa hai mô hình, chưa phải đồng thuận giữa người với người.
- **Kết quả:** {n_spam} spam / {meta['n_labels'] - n_spam} không spam. Loại spam: {spam_types}.

File nhãn [spam_labels_v1.tsv](../../src/processing/spam/labels/spam_labels_v1.tsv) chỉ chứa ID và nhãn. Nội dung bình luận được nối lại từ `clean_data.jsonl` và kiểm tra bằng mã băm từng dòng, nên không có nội dung hay số điện thoại của người dùng nằm trong git.

## 3. Tỷ lệ spam trong dữ liệu

Ước lượng từ mẫu phân tầng: **{pct(prevalence['estimate'], 2)}** bình luận là spam (khoảng tin cậy 95%: {pct(prevalence['ci95'][0], 2)} – {pct(prevalence['ci95'][1], 2)}), tức khoảng {count(prevalence['estimated_count'])} bình luận. {rest_note}

Con số "khoảng 6%" trong mô tả công việc và 2,96% trong báo cáo tiền xử lý là tỷ lệ **bị luật gắn cờ**, không phải tỷ lệ spam.

## 4. Cách so sánh

- **Baseline:** `rule-v0` trong `src/processing/cleaner`, giữ nguyên. Vì luật gộp cả "không phải tiếng Việt" và "không có chữ" vào spam, báo cáo thêm ba cách đọc hẹp dần để so sánh công bằng.
- **Mô hình ML:** năm ứng viên TF-IDF (từ, ký tự, kèm đặc trưng hình thức) với Naive Bayes, Logistic Regression, Linear SVM. Link và số điện thoại được thay bằng token cố định trước khi vector hóa.
- **Chọn mô hình và ngưỡng chỉ trên train:** cross-validation 5 phần gom nhóm theo video. Chọn mô hình theo average precision có trọng số; chọn ngưỡng theo F0,5 có trọng số (coi precision quan trọng gấp đôi recall).
- **Tập test dùng đúng một lần** để ra bảng ở mục 5.
- **Chỉ số:** precision, recall, F1 của lớp spam, không dùng accuracy. Cột "quy về toàn bộ dữ liệu" dùng trọng số tầng; khoảng tin cậy 95% bằng bootstrap phân tầng {count(meta['bootstrap_resamples'])} lần.

Kết quả cross-validation trên train (điểm out-of-fold):

{table(["Mô hình", "AP (quần thể)", "AP (mẫu)", "Precision", "Recall", "F0,5"], cv_rows)}

Precision, recall, F0,5 tính tại ngưỡng tốt nhất của từng mô hình. Mô hình được chọn: `{cv['selected']}`, ngưỡng {num(cv['threshold_ml'], 3)}. Cùng ngưỡng đó được chọn cho phương án kết hợp.

## 5. Kết quả trên tập test

{table(["Phương pháp", "TP / FP / FN (mẫu)", "Precision (KTC 95%)", "Recall (KTC 95%)", "F1 (KTC 95%)"], test_rows)}

Precision, recall, F1 đã quy về toàn bộ dữ liệu. Cột TP / FP / FN là số dòng đếm trực tiếp trên {meta['n_test']} dòng test.

Kiểm định McNemar chính xác (trên mẫu, không trọng số), so số dòng mà chỉ một trong hai phương pháp phân loại đúng:

{table(["So sánh (A so với B)", "Chỉ A đúng", "Chỉ B đúng", "p"], mcnemar_rows)}

Phương án kết hợp và mô hình ML đều phân loại đúng nhiều hơn `rule-v0` có ý nghĩa thống kê. Giữa phương án kết hợp và mô hình ML không có dòng nào khác nhau trên tập test.

## 6. Áp dụng lên toàn bộ dữ liệu

Số bình luận từng phương án gắn cờ trên {count(full['total']['N'])} bình luận. Bảng này không đo độ chính xác (không có nhãn cho toàn bộ dữ liệu); nó cho thấy mô hình ML không gắn cờ tràn lan ở vùng luật không bắt.

{table(["Tầng", "N", "rule-v0", "ML", "Kết hợp"], full_rows)}

## 7. Tách "không phải tiếng Việt" khỏi spam

`rule-v0` coi mọi bình luận không phải tiếng Việt là spam. Hàm nhận diện trong cleaner còn có lỗi: tập ký tự tiếng Việt chứa cả nguyên âm không dấu, nên câu tiếng Anh có nguyên âm được coi là tiếng Việt, còn thứ bị gắn "không phải tiếng Việt" chủ yếu là emoji, ":)))", "vl", "tks". Trên toàn bộ dữ liệu luật gắn {count(full['rule_v0_not_vietnamese'])} bình luận là không phải tiếng Việt.

[language.py](../../src/processing/spam/language.py) trả về ba giá trị: `vi`, `other` (ngôn ngữ khác), `none` (không xác định được: emoji, số, tên máy). Trên toàn bộ dữ liệu: `vi` {count(full['language_py'].get('vi', 0))}, `other` {count(full['language_py'].get('other', 0))}, `none` {count(full['language_py'].get('none', 0))}.

Đánh giá trên {language['n_rows']} dòng test có ngôn ngữ xác định:

{table(["", "rule-v0", "language.py"], [
    ["Bình luận tiếng Việt bị xếp nhầm", f"{vi_rule['n_missed']} / {vi_rule['n_vi']}", f"{vi_new['n_missed']} / {vi_new['n_vi']}"],
    ["Bình luận ngôn ngữ khác phát hiện được", f"{int(lang_rule['tp'])} / {language['n_other']}", f"{int(lang_new['tp'])} / {language['n_other']}"],
    ["Báo nhầm là ngôn ngữ khác", str(int(lang_rule['fp'])), str(int(lang_new['fp']))],
])}

Tập test chỉ có {language['n_other']} bình luận ngôn ngữ khác, nên **chưa đủ để kết luận về khả năng phát hiện**. Điều đo được chắc hơn là tỷ lệ loại nhầm tiếng Việt, vì có {vi_new['n_vi']} dòng.

## 8. Phân tích lỗi trên tập test

{stale_note}**`rule-v0` báo nhầm {false_positives} dòng.** Chia theo lý do mạnh nhất mà luật đưa ra (cột "Spam thật" là số dòng cùng lý do được gắn cờ đúng):

{table(["Lý do của luật", "Báo nhầm", "Spam thật", "Bình luận bị báo nhầm trông thế nào"], reason_rows, "lrrl")}

Trong nhóm link hoặc số điện thoại, đọc tay từng dòng báo nhầm cho thấy: 17 dòng là bài dự thi minigame của một video (kênh yêu cầu ghi SĐT, link Facebook và dự đoán), 10 dòng là link dẫn chứng hoặc gợi ý trong lúc trao đổi, 1 dòng có SĐT nhưng không rao bán gì.

**Phương án kết hợp báo nhầm {len(hybrid_errors['false_positive'])} dòng** ({', '.join(hybrid_errors['false_positive'])}): cả ba đều là người xem dán link để trả lời hoặc gợi ý cho người khác. Về hình thức chúng giống hệt spam kéo view; phân biệt được phải đọc bình luận cha, mà mô hình hiện chỉ đọc nội dung bình luận.

**Phương án kết hợp bỏ sót {len(hybrid_errors['false_negative'])} dòng:**

| Nguyên nhân | Dòng | Ghi chú |
|---|---|---|
| Đoạn văn dán nguyên văn ở nhiều video, không có link | S0022, S0429, S0468 | Luật không có lý do nào bắt được; cần đặc trưng "nội dung trùng lặp giữa các video" |
| Xin đăng ký kênh, không có link hoặc link rút gọn | S0029, S0203 | Luật không bắt; mô hình ML đứng riêng cũng cho điểm thấp |
| Link kèm chú thích ngắn | S0332 | Điểm 0,60, dưới ngưỡng 0,70 |
| Quảng cáo ngoài lĩnh vực điện thoại | S0419 | Tập train gần như chỉ có quảng cáo điện thoại |
| Rao bán không dấu, rất ngắn | S0488 | "Co thi lien he zalo cho e …" |
| Chuỗi gõ bừa ngắn | S0105 | 9 ký tự |

## 9. Hạn chế và việc còn lại

1. **Nhãn chưa có người duyệt.** Đây là hạn chế lớn nhất. Để hoàn tất: chạy `python -m src.processing.spam.labels export-review`, mở `data/labels/spam/review_test.csv` bằng Excel, duyệt {meta['n_test']} dòng test (đúng thì gõ `x` vào cột `ok`, sai thì điền nhãn đúng), rồi `import-review`, `train`, `report`. Lệnh `import-review` cũng in tỷ lệ AI gán đúng so với người duyệt.
2. **Ít spam trong tập test** ({int(tests[BASELINE]['sample']['tp'] + tests[BASELINE]['sample']['fn'])} dòng), nên khoảng tin cậy của recall rộng. Recall còn phụ thuộc nhiều vào vài dòng spam ở các tầng có trọng số lớn.
3. **Trần recall của phương án kết hợp là recall của luật.** Hai loại spam luật không bắt (đoạn văn dán lặp, xin đăng ký kênh) cần thêm luật hoặc đặc trưng mới; ước tính luật bỏ sót khoảng {missed_share} số spam.
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

Môi trường đã chạy: scikit-learn {meta['scikit_learn']}, numpy {meta['numpy']}, seed {meta['seed']}. Mô hình lưu tại `{results['model_file']['path']}` (không vào git), SHA-256 `{results['model_file']['sha256'][:16]}…`.
"""


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định không in được tiếng Việt
    results = json.loads(config.RESULTS_PATH.read_text("utf-8"))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build(results), encoding="utf-8")
    print(f"Đã ghi {REPORT_PATH}")


if __name__ == "__main__":
    main()

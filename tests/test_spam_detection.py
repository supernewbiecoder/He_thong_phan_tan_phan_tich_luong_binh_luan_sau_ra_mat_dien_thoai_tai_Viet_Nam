"""Kiểm thử Công việc 11 (phát hiện spam).

Chạy từ thư mục gốc repo:  python -m pytest tests/test_spam_detection.py -q
Các test không cần data/clean_data.jsonl, trừ nhóm đánh dấu `needs_data`
(tự bỏ qua khi máy chưa có dữ liệu).
"""
import collections
import json

import numpy as np
import pytest
from sklearn.metrics import average_precision_score, cohen_kappa_score

from src.processing.spam import config, data, labels
from src.processing.spam.baseline import (CONTENT_REASONS, FORM_REASONS, RULE_VARIANTS, flags,
                                          rule_reasons)
from src.processing.spam.evaluate import (average_precision, bootstrap_ci, cohen_kappa, f_beta,
                                          mcnemar_exact, prf, stratum_weights)
from src.processing.spam.language import detect_language
from src.processing.spam.model import build_candidates, normalize_for_model, scores
from src.processing.spam.predict import SpamDetector
from src.processing.spam.sampling import normalize_for_dup, stratum_of
from src.processing.spam.train import best_threshold

needs_data = pytest.mark.skipif(not config.CLEAN_DATA_PATH.exists(),
                                reason="cần data/clean_data.jsonl (xem src/processing/README.md)")


# ---------------------------------------------------------------- chỉ số

def test_prf_counts_and_ratios():
    result = prf([1, 1, 1, 0, 0, 0], [1, 1, 0, 1, 0, 0])
    assert (result["tp"], result["fp"], result["fn"], result["tn"]) == (2, 1, 1, 2)
    assert result["precision"] == pytest.approx(2 / 3)
    assert result["recall"] == pytest.approx(2 / 3)
    assert result["f1"] == pytest.approx(2 / 3)


def test_prf_returns_none_instead_of_zero_when_undefined():
    nothing_flagged = prf([1, 0], [0, 0])
    assert nothing_flagged["precision"] is None and nothing_flagged["recall"] == 0
    no_spam = prf([0, 0], [1, 0])
    assert no_spam["recall"] is None and no_spam["precision"] == 0


def test_weights_change_precision_the_way_the_population_would():
    # 1 spam đúng trong tầng nhỏ, 1 báo nhầm trong tầng lớn gấp 100 lần.
    y_true, y_pred = [1, 0], [1, 1]
    weights = stratum_weights(["small", "big"], {"small": 10, "big": 1000})
    assert list(weights) == [10, 1000]
    assert prf(y_true, y_pred)["precision"] == pytest.approx(0.5)
    assert prf(y_true, y_pred, weights)["precision"] == pytest.approx(10 / 1010)


def test_stratum_weights_divide_population_by_sample_count():
    weights = stratum_weights(["a", "a", "b"], {"a": 100, "b": 7})
    assert list(weights) == [50, 50, 7]


def test_f_beta_prefers_precision_when_beta_below_one():
    assert f_beta(0.9, 0.5, beta=0.5) > f_beta(0.5, 0.9, beta=0.5)
    assert f_beta(None, 0.5, beta=0.5) == 0.0


def test_cohen_kappa_matches_sklearn_and_handles_degenerate_case():
    a = ["spam", "ham", "ham", "spam", "ham", "ham", "ham", "spam"]
    b = ["spam", "ham", "spam", "spam", "ham", "ham", "ham", "ham"]
    assert cohen_kappa(a, b) == pytest.approx(cohen_kappa_score(a, b))
    assert cohen_kappa(["ham"] * 4, ["ham"] * 4) is None


def test_average_precision_matches_sklearn_including_ties_and_weights():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 200)
    score = np.round(rng.random(200) + 0.3 * y, 1)  # làm tròn để tạo nhiều điểm trùng
    weights = rng.integers(1, 50, 200).astype(float)
    assert average_precision(y, score) == pytest.approx(average_precision_score(y, score))
    assert average_precision(y, score, weights) == pytest.approx(
        average_precision_score(y, score, sample_weight=weights))
    assert average_precision([0, 0], [0.1, 0.2]) is None


def test_mcnemar_counts_only_discordant_rows():
    y_true = [1, 1, 0, 0, 1]
    result = mcnemar_exact(y_true, [1, 1, 0, 0, 1], [0, 1, 1, 0, 1])
    assert (result["only_a_correct"], result["only_b_correct"]) == (2, 0)
    assert result["p_value"] == pytest.approx(0.5)
    assert mcnemar_exact(y_true, y_true, y_true)["p_value"] == 1.0


def test_bootstrap_ci_brackets_the_point_estimate_and_is_reproducible():
    rng = np.random.default_rng(1)
    strata = ["flagged"] * 60 + ["rest"] * 60
    y_true = np.r_[rng.integers(0, 2, 60), np.zeros(60, int)]
    y_pred = np.r_[np.ones(60, int), np.zeros(60, int)]
    population = {"flagged": 600, "rest": 60000}
    point = prf(y_true, y_pred, stratum_weights(strata, population))["precision"]
    first = bootstrap_ci(y_true, y_pred, strata, population, n_boot=300, seed=7)
    second = bootstrap_ci(y_true, y_pred, strata, population, n_boot=300, seed=7)
    assert first == second
    assert first["precision"][0] <= point <= first["precision"][1]


def test_bootstrap_ci_is_none_when_metric_is_usually_undefined():
    # Không có dòng nào bị gắn cờ nên precision không xác định ở mọi lần rút.
    interval = bootstrap_ci([1, 0, 0, 0], [0, 0, 0, 0], ["a"] * 4, {"a": 40}, n_boot=50)
    assert interval["precision"] is None


def test_best_threshold_with_gate_can_keep_rule_decision():
    y = np.array([1, 1, 0, 0])
    score = np.array([0.1, 0.2, 0.9, 0.8])  # mô hình xếp hạng ngược hoàn toàn
    gate = np.array([True, True, False, False])
    threshold, value = best_threshold(y, score, np.ones(4), gate)
    assert threshold <= 0.1 and value == pytest.approx(1.0)


# ---------------------------------------------------------------- dữ liệu, chia tập

def test_split_is_deterministic_per_video_and_close_to_target_fraction():
    videos = [f"video_{i}" for i in range(4000)]
    assert [data.split_of(v) for v in videos] == [data.split_of(v) for v in videos]
    share = sum(data.split_of(v) == "test" for v in videos) / len(videos)
    assert abs(share - config.TEST_FRACTION) < 0.03


def test_attach_text_rejects_rows_from_a_different_dataset_version():
    comments = {"c1": {"comment_id": "c1", "text": "pin trâu", "model": "s23u"}}
    good = [{"comment_id": "c1", "text_sha1": data.text_hash("pin trâu")}]
    assert data.attach_text(good, comments)[0]["text"] == "pin trâu"
    with pytest.raises(ValueError, match="sai phiên bản"):
        data.attach_text([{"comment_id": "c1", "text_sha1": "000000000000"}], comments)
    with pytest.raises(KeyError):
        data.attach_text([{"comment_id": "missing", "text_sha1": "x"}], comments)


# ---------------------------------------------------------------- baseline và tầng mẫu

@pytest.mark.parametrize("text, expected", [
    ("Mua tại https://shop.example.com/iphone giá tốt", "contains_url"),
    ("ai lấy ib mình 0362834577", "contains_phone_number"),
    ("đẹp quáaaaaaaaa", "excessive_character_repetition"),
    ("😂😂😂", "no_alphabetical_content"),
])
def test_rule_v0_reasons(text, expected):
    assert expected in rule_reasons(text)


def test_rule_v0_keeps_ordinary_opinion():
    assert rule_reasons("Camera đẹp nhưng pin hơi yếu") == []


def test_rule_variants_are_nested_from_wide_to_narrow():
    names = list(RULE_VARIANTS)
    for wider, narrower in zip(names, names[1:]):
        assert RULE_VARIANTS[narrower] < RULE_VARIANTS[wider]
    assert flags(["non_vietnamese_language"], RULE_VARIANTS[names[0]])
    assert not flags(["non_vietnamese_language"], RULE_VARIANTS[names[1]])


def test_stratum_of_follows_documented_priority():
    dup = collections.Counter()
    comment = lambda text, reasons: {"text": text, "spam_reasons": reasons}
    assert stratum_of(comment("x", ["contains_url", "no_alphabetical_content"]), dup) == "rule_content"
    assert stratum_of(comment("x", ["no_alphabetical_content", "non_vietnamese_language"]), dup) == "rule_notext"
    assert stratum_of(comment("x", ["repetitive_words", "non_vietnamese_language"]), dup) == "rule_form"
    assert stratum_of(comment("x", ["non_vietnamese_language"]), dup) == "rule_nonvn_only"
    assert stratum_of(comment("ghé kênh mình ủng hộ nhé", []), dup) == "unflagged_suspect"
    assert stratum_of(comment("camera chụp đêm đẹp thật", []), dup) == "unflagged_rest"
    pasted = "Anh ơi tầm giá dưới 7 triệu nên mua máy nào"
    dup[normalize_for_dup(pasted)] = 3
    assert stratum_of(comment(pasted, []), dup) == "unflagged_dup"


# ---------------------------------------------------------------- ngôn ngữ

@pytest.mark.parametrize("text, expected", [
    ("Máy đẹp, pin trâu, đáng tiền", "vi"),
    ("may nay pin trau khong anh em", "vi"),
    ("camera ok nhưng giá chát", "vi"),
    ("This phone is really good and the camera is great", "other"),
    ("越南人可笑至极！苹果在中国销量不行", "other"),
    ("Очень хороший телефон", "other"),
    ("😂😂😂", "none"),
    ("7:10 :))", "none"),
    ("iPhone 12 Pro Max", "none"),
    ("ok", "none"),
    ("", "none"),
])
def test_detect_language(text, expected):
    assert detect_language(text) == expected


def test_english_sentence_is_not_vietnamese_unlike_rule_v0():
    # Lỗi của rule-v0: câu tiếng Anh có nguyên âm được coi là tiếng Việt.
    from src.processing.cleaner.spam_detector import is_vietnamese_text
    text = "This phone is really good and the camera is great"
    assert is_vietnamese_text(text) is True
    assert detect_language(text) == "other"


# ---------------------------------------------------------------- mô hình

def test_normalize_for_model_masks_links_and_phones_and_squeezes_repeats():
    text = normalize_for_model("ĐẸP quáaaaaaa https://shop.example.com/x gọi 0362834577")
    assert "xxurl" in text and "xxphone" in text
    assert "example" not in text and "0362834577" not in text
    # "á" khác "a": sáu chữ "a" lặp được rút về ba.
    assert "quáaaa " in text and "quáaaaa" not in text


TINY_SPAM = ["Mua ngay tại https://shop.example.com/a giảm giá sốc", "Tham khảo giá https://store.example.vn/b",
             "Đặt hàng tại https://shop.example.com/c nhận quà", "Xem giá tốt https://store.example.vn/d hôm nay"]
TINY_HAM = ["Camera đẹp nhưng pin yếu", "Máy này chơi game có nóng không anh", "Màn hình sáng quá đẹp",
            "Giá hơi cao so với cấu hình", "Pin dùng được cả ngày", "Thiết kế đẹp cầm chắc tay"]


def test_every_candidate_trains_and_returns_one_score_per_text():
    texts, y = TINY_SPAM + TINY_HAM, [1] * len(TINY_SPAM) + [0] * len(TINY_HAM)
    for name, pipeline in build_candidates().items():
        pipeline.fit(texts, y)
        result = scores(pipeline, texts)
        assert result.shape == (len(texts),), name
        assert result[:len(TINY_SPAM)].mean() > result[len(TINY_SPAM):].mean(), name


@pytest.fixture()
def tiny_bundle():
    pipeline = build_candidates()["lr-char"]
    pipeline.fit(TINY_SPAM + TINY_HAM, [1] * len(TINY_SPAM) + [0] * len(TINY_HAM))
    return {"pipeline": pipeline, "model_version": "spam-test", "selected": "lr-char",
            "threshold_ml": 0.5, "threshold_hybrid": 0.5}


def test_hybrid_never_flags_a_comment_the_rules_did_not_flag(tiny_bundle):
    tiny_bundle["threshold_hybrid"] = tiny_bundle["threshold_ml"] = -1.0  # ML đồng ý với mọi thứ
    texts = ["Camera đẹp nhưng pin yếu", "Mua tại https://shop.example.com/a giảm giá", ""]
    hybrid = SpamDetector(tiny_bundle, "hybrid").predict(texts)
    assert [r["is_spam"] for r in hybrid] == [False, True, False]
    assert hybrid[1]["spam_reasons"] == ["contains_url"] and hybrid[0]["spam_reasons"] == []
    assert all(r["is_spam"] for r in SpamDetector(tiny_bundle, "ml").predict(texts))


def test_language_is_reported_separately_from_spam(tiny_bundle):
    english, emoji = SpamDetector(tiny_bundle).predict(
        ["This phone is really good and the camera is great", "😂😂😂"])
    assert english["is_spam"] is False and english["is_vietnamese"] is False and english["lang"] == "other"
    assert emoji["is_spam"] is False and emoji["lang"] == "none"
    # rule-v0 nguyên trạng coi bình luận chỉ có emoji là spam.
    assert SpamDetector(tiny_bundle, "rule").predict(["😂😂😂"])[0]["is_spam"] is True


def test_detector_rejects_unknown_mode_and_handles_empty_input(tiny_bundle):
    with pytest.raises(ValueError):
        SpamDetector(tiny_bundle, "auto")
    assert SpamDetector(tiny_bundle).predict([]) == []


# ---------------------------------------------------------------- file nhãn

def _write_annotator(directory, name, rows):
    data.write_tsv(directory / f"annotator_{name}.tsv", rows,
                   ["item_id", "label", "spam_type", "lang", "note"])


@pytest.fixture()
def label_workspace(tmp_path, monkeypatch):
    work, repo = tmp_path / "work", tmp_path / "repo"
    work.mkdir()
    monkeypatch.setattr(config, "WORK_DIR", work)
    monkeypatch.setattr(config, "SAMPLE_PATH", repo / "sample.tsv")
    monkeypatch.setattr(config, "LABELS_PATH", repo / "labels.tsv")
    texts = {"S0001": "pin trâu", "S0002": "mua tại https://shop.example.com", "S0003": "ok"}
    comments = {f"c{i}": {"comment_id": f"c{i}", "text": text, "model": "s23u"}
                for i, text in enumerate(texts.values())}
    sample = [{"item_id": item, "comment_id": f"c{i}", "video_id": f"v{i}",
               "text_sha1": data.text_hash(text), "stratum": "unflagged_rest", "split": "test"}
              for i, (item, text) in enumerate(texts.items())]
    data.write_tsv(config.SAMPLE_PATH, sample,
                   ["item_id", "comment_id", "video_id", "text_sha1", "stratum", "split"])
    monkeypatch.setattr(data, "attach_text",
                        lambda rows, *_a, **_k: [{**r, "text": comments[r["comment_id"]]["text"],
                                                  "parent_text": None} for r in rows])
    return work


def test_merge_stops_until_disagreements_are_adjudicated(label_workspace, capsys):
    agree = [{"item_id": "S0001", "label": "ham", "spam_type": "", "lang": "vi"},
             {"item_id": "S0003", "label": "ham", "spam_type": "", "lang": "none"}]
    _write_annotator(label_workspace, "A", agree + [
        {"item_id": "S0002", "label": "spam", "spam_type": "ad", "lang": "vi"}])
    _write_annotator(label_workspace, "B", agree + [
        {"item_id": "S0002", "label": "ham", "spam_type": "", "lang": "vi"}])

    assert labels.merge("A,B", "A=x;B=y") == 1
    assert not config.LABELS_PATH.exists()
    assert "S0002" in (label_workspace / "disagreements.txt").read_text("utf-8")

    data.write_tsv(label_workspace / "adjudication.tsv",
                   [{"item_id": "S0002", "label": "spam", "spam_type": "ad", "lang": "vi", "note": "adj"}],
                   ["item_id", "label", "spam_type", "lang", "note"])
    assert labels.merge("A,B", "A=x;B=y") == 0
    merged = {row["item_id"]: row for row in data.read_tsv(config.LABELS_PATH)}
    assert merged["S0002"]["label"] == "spam" and merged["S0002"]["resolution"] == "adjudicated"
    assert merged["S0002"]["label_a"] == "spam" and merged["S0002"]["label_b"] == "ham"
    assert merged["S0001"]["resolution"] == "agree"
    assert {row["label_source"] for row in merged.values()} == {"llm"}


@pytest.mark.parametrize("bad_row, message", [
    ({"label": "junk", "spam_type": "", "lang": "vi"}, "label"),
    ({"label": "spam", "spam_type": "", "lang": "vi"}, "spam_type"),
    ({"label": "ham", "spam_type": "ad", "lang": "vi"}, "ham không được"),
    ({"label": "ham", "spam_type": "", "lang": "en"}, "lang"),
])
def test_invalid_annotation_is_rejected(label_workspace, bad_row, message):
    good = [{"item_id": item, "label": "ham", "spam_type": "", "lang": "vi"} for item in ("S0002", "S0003")]
    _write_annotator(label_workspace, "A", good + [{"item_id": "S0001", **bad_row}])
    _write_annotator(label_workspace, "B", good + [{"item_id": "S0001", "label": "ham", "spam_type": "", "lang": "vi"}])
    with pytest.raises(ValueError, match=message):
        labels.merge("A,B", "A=x;B=y")


def test_missing_item_in_annotation_is_rejected(label_workspace):
    rows = [{"item_id": "S0001", "label": "ham", "spam_type": "", "lang": "vi"}]
    _write_annotator(label_workspace, "A", rows)
    _write_annotator(label_workspace, "B", rows)
    with pytest.raises(ValueError, match="thiếu"):
        labels.merge("A,B", "A=x;B=y")


def test_human_review_roundtrip_marks_rows_human_and_applies_corrections(label_workspace, capsys):
    same = [{"item_id": "S0001", "label": "ham", "spam_type": "", "lang": "vi"},
            {"item_id": "S0002", "label": "spam", "spam_type": "ad", "lang": "vi"},
            {"item_id": "S0003", "label": "ham", "spam_type": "", "lang": "none"}]
    _write_annotator(label_workspace, "A", same)
    _write_annotator(label_workspace, "B", same)
    assert labels.merge("A,B", "A=x;B=y") == 0
    assert labels.export_review("test") == 0

    import csv
    review_path = label_workspace / "review_test.csv"
    with open(review_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["text"] for row in rows][0] == "pin trâu"
    rows[0]["ok"] = "x"                                    # đồng ý
    rows[1]["human_label"] = "ham"                         # sửa spam -> ham
    # rows[2] để trống: chưa duyệt
    with open(review_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=labels.REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    assert labels.import_review(str(review_path), "nlquan") == 0
    result = {row["item_id"]: row for row in data.read_tsv(config.LABELS_PATH)}
    assert result["S0001"]["label_source"] == "human" and result["S0001"]["reviewed_by"] == "nlquan"
    assert result["S0002"]["label"] == "ham" and result["S0002"]["spam_type"] == ""
    assert result["S0002"]["resolution"] == "human_corrected"
    assert result["S0003"]["label_source"] == "llm"
    assert "0.5000" in capsys.readouterr().out             # AI đúng 1/2 dòng đã duyệt


# ---------------------------------------------------------------- file đã commit

def test_committed_sample_labels_and_strata_are_consistent():
    sample = {row["item_id"]: row for row in data.read_tsv(config.SAMPLE_PATH)}
    label_rows = data.read_tsv(config.LABELS_PATH)
    strata = json.loads((config.LABELS_DIR / "spam_strata_v1.json").read_text("utf-8"))

    assert len(sample) == sum(config.STRATA_SIZES.values()) == len(label_rows)
    assert collections.Counter(r["stratum"] for r in sample.values()) == config.STRATA_SIZES
    assert sum(info["N"] for info in strata["strata"].values()) == config.DATASET_LINES
    assert strata["dataset_sha256"] == config.DATASET_SHA256
    for info in strata["strata"].values():
        assert info["N_train"] + info["N_test"] == info["N"]

    for row in label_rows:
        source = sample[row["item_id"]]
        assert all(row[key] == source[key] for key in ("comment_id", "video_id", "text_sha1", "stratum", "split"))
        assert row["split"] == data.split_of(row["video_id"])
        labels._validate(row, "labels")
        assert row["label_source"] in ("llm", "human")
        assert row["resolution"] in ("agree", "adjudicated", "human_corrected")
        if row["resolution"] == "agree":
            assert (row["label"], row["lang"]) == (row["label_a"], row["lang_a"]) == (row["label_b"], row["lang_b"])
    by_split = collections.defaultdict(set)
    for row in label_rows:
        by_split[row["split"]].add(row["video_id"])
    assert not by_split["train"] & by_split["test"], "một video nằm ở cả train và test"


def test_committed_results_match_committed_labels():
    """Sửa nhãn mà quên chạy lại train thì test này báo."""
    results = json.loads(config.RESULTS_PATH.read_text("utf-8"))
    label_rows = data.read_tsv(config.LABELS_PATH)
    test_rows = [row for row in label_rows if row["split"] == "test"]
    meta = results["meta"]
    assert meta["n_labels"] == len(label_rows) and meta["n_test"] == len(test_rows)
    assert meta["label_sources"] == dict(collections.Counter(r["label_source"] for r in label_rows))
    assert meta["test_human_verified"] == all(r["label_source"] == "human" for r in test_rows)
    assert meta["dataset_sha256"] == config.DATASET_SHA256
    baseline = results["test"]["rule-v0 (nguyên trạng)"]["sample"]
    assert baseline["tp"] + baseline["fn"] == sum(r["label"] == "spam" for r in test_rows)
    assert baseline["tp"] + baseline["fp"] + baseline["fn"] + baseline["tn"] == len(test_rows)


@needs_data
def test_rule_v0_recomputed_on_text_matches_stored_dataset_output():
    rows = data.attach_text(data.read_tsv(config.LABELS_PATH)[:150])
    for row in rows:
        assert sorted(rule_reasons(row["text"])) == sorted(row["rule_reasons"])

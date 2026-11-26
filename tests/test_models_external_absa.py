"""Mục đích: Kiểm chuẩn hóa UIT-ViSD4SA về bộ nhãn chốt (src/models/external_absa.py); cập nhật lần cuối: 2026-11-26."""

import unittest

from src.models.external_absa import (
    _review_html,
    normalize_visd4sa_row,
)


class NormalizeExternalAbsaTests(unittest.TestCase):
    def test_output_contains_only_text_and_normalized_span_sentiment_labels(self):
        text = "Máy đẹp, pin trâu, phụ kiện đủ."
        row, review = normalize_visd4sa_row(
            {
                "text": text,
                "labels": [
                    [0, 7, "DESIGN#POSITIVE"],
                    [9, 17, "BATTERY#POSITIVE"],
                    [19, 27, "SER&ACC#POSITIVE"],
                    [28, 31, "STORAGE#NEGATIVE"],
                    [0, 7, "FEATURES#POSITIVE"],
                ],
            }
        )

        self.assertEqual(set(row), {"text", "labels"})
        self.assertEqual(
            row["labels"],
            [
                [0, 7, "thiet_ke#tich_cuc"],
                [9, 17, "pin_sac#tich_cuc"],
                [19, 27, "bao_hanh_sua_chua#tich_cuc"],
                [28, 31, "phan_cung_khac#tieu_cuc"],
            ],
        )
        self.assertEqual(review[0]["span_text"], "Máy đẹp")

    def test_invalid_span_is_omitted_from_training_labels(self):
        row, review = normalize_visd4sa_row(
            {"text": "pin tốt", "labels": [[0, 99, "BATTERY#POSITIVE"]]}
        )

        self.assertEqual(row, {"text": "pin tốt", "labels": []})
        self.assertEqual(review[0]["_invalid_offset"]["end"], 99)

    def test_general_maps_to_whole_phone_label(self):
        row, _ = normalize_visd4sa_row({"text": "máy ngon", "labels": [[0, 8, "GENERAL#POSITIVE"]]})
        self.assertEqual(row["labels"], [[0, 8, "may_chung#tich_cuc"]])

    def test_features_are_reviewable_but_not_silently_mapped(self):
        row, review = normalize_visd4sa_row(
            {"text": "tính năng tốt", "labels": [[0, 13, "FEATURES#POSITIVE"]]}
        )

        self.assertEqual(row["labels"], [])
        self.assertEqual(review[0]["span_text"], "tính năng tốt")

    def test_review_html_escapes_text(self):
        page = _review_html(
            [
                {
                    "source_dataset": "UIT-ViSD4SA",
                    "source_sentiment": "tich_cuc",
                    "span_text": "</script>",
                    "text": "<script>alert(1)</script>",
                }
            ]
        )

        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("\\u003cscript\\u003e", page)
        self.assertIn('id="export-output"', page)


if __name__ == "__main__":
    unittest.main()

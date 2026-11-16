import unittest

from src.processing.normalize_external_absa import (
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
                [0, 7, "DESIGN#pos"],
                [9, 17, "BATTERY#pos"],
                [19, 27, "WARRANTY#pos"],
                [28, 31, "HARDWARE_OTHER#neg"],
            ],
        )
        self.assertEqual(review[0]["span_text"], "Máy đẹp")

    def test_invalid_span_is_omitted_from_training_labels(self):
        row, review = normalize_visd4sa_row(
            {"text": "pin tốt", "labels": [[0, 99, "BATTERY#POSITIVE"]]}
        )

        self.assertEqual(row, {"text": "pin tốt", "labels": []})
        self.assertEqual(review[0]["_invalid_offset"]["end"], 99)

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
                    "source_sentiment": "pos",
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

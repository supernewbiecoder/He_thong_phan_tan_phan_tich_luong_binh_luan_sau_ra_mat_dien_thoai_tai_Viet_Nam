# -*- coding: utf-8 -*-
"""
Unit tests for Spam Detection Module (CV 11 - Nguyễn Lê Quân).
Tests Precision-First filtering, language separation, rating expressions,
Unicode normalization, Model Card governance, and model loading.
"""
import os
import sys
import json
import pytest
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "processing"))
from cleaner.spam_detector import detect_spam, is_vietnamese_text, normalize_unicode


def test_legitimate_tech_comments():
    """Valid positive, negative and neutral comments must NOT be flagged as spam."""
    legitimate_samples = [
        "Máy mượt pin trâu, chơi genshin không bị drop fps",
        "Camera chụp đêm bị nhiễu hạt quá thất vọng",
        "Giá 30 củ cho con này thì hơi chát",
        "Có nên lên đời từ ip14prm lên ip15prm không các bác?",
        "Màn hình đẹp, độ sáng cao ngoài trời nhìn rõ",
        "Pin tụt nhanh vãi chưởng sau khi update ios",
        "Loa to, âm bass ấm nghe nhạc phê",
        "Thiết kế viền titan cầm nhẹ tay hơn hẳn"
    ]
    for text in legitimate_samples:
        res = detect_spam(text)
        actual_spam = [r for r in res["spam_reasons"] if r not in ("non_vietnamese_language", "pure_emoji_no_text")]
        assert len(actual_spam) == 0, f"False positive on legitimate comment: '{text}', reasons: {res['spam_reasons']}"
        assert res["is_spam"] is False


def test_rating_and_enthusiastic_expressions():
    """Numerical ratings like '10/10', '+1', '100%' should NOT be flagged as spam."""
    ratings = ["10/10", "9.5/10", "+1", "100%", "10 điểm", "5 sao"]
    for text in ratings:
        res = detect_spam(text)
        assert res["is_spam"] is False, f"Rating '{text}' was incorrectly flagged as spam!"


def test_unicode_normalization_nfd_to_nfc():
    """Decomposed Unicode (NFD) text should behave identically to precomposed (NFC)."""
    nfc_text = "Máy dùng rất tốt, pin trâu và màn hình mượt mà"
    nfd_text = unicodedata.normalize("NFD", nfc_text)
    
    assert nfc_text != nfd_text  # Verify NFD has different byte representation
    res_nfc = detect_spam(nfc_text)
    res_nfd = detect_spam(nfd_text)
    
    assert res_nfc["is_vietnamese"] is True
    assert res_nfd["is_vietnamese"] is True
    assert res_nfd["is_spam"] is False


def test_obvious_spam_patterns():
    """Commercial, gambling, and contact scam comments must be caught."""
    spam_samples = [
        "Kiếm tiền online ngày 500k ib zalo 0987654321",
        "Nhận kéo tài xỉu kubet thabet uy tín liên hệ telegram @kèo_chuẩn",
        "Mọi người mua hàng bấm vào link http://bit.ly/sale_re_nhat_shopee",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "Voucher giảm 50% chiết khấu hoa hồng cao xem tại www.deal-hot.xyz"
    ]
    for text in spam_samples:
        res = detect_spam(text)
        assert res["is_spam"] is True, f"Failed to catch obvious spam: '{text}'"


def test_foreign_language_detection():
    """Non-Vietnamese text must be recognized as is_vietnamese=False without false spam tagging."""
    foreign_samples = [
        "This phone has great camera quality and battery life.",
        "Этот телефон очень хороший, но дорогой.",
        "このスマートフォンはとても使いやすいです。"
    ]
    for text in foreign_samples:
        is_vn = is_vietnamese_text(text)
        assert is_vn is False, f"Foreign text incorrectly identified as Vietnamese: '{text}'"


def test_ml_model_and_model_card_artifacts():
    """Verifies that the serialized ML model and Model Card exist and are valid."""
    model_path = os.path.join(BASE_DIR, "src", "processing", "models", "spam_model.pkl")
    card_path = os.path.join(BASE_DIR, "src", "processing", "models", "model_card.json")
    
    assert os.path.exists(model_path), f"Spam model artifact not found at {model_path}"
    assert os.path.getsize(model_path) > 1000, "Spam model artifact is unexpectedly empty"
    
    assert os.path.exists(card_path), f"Model Card not found at {card_path}"
    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)
    assert card["task"] == "Binary Spam Classification (CV 11)"
    assert card["author"] == "Nguyễn Lê Quân"
    assert "metrics_summary" in card

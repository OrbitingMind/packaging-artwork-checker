"""
tests/test_ocr.py
Pytest suite verifying OCR text extraction:
1. Output format matches specification: list of {"text": str, "bbox": [x1, y1, x2, y2], "confidence": float}.
2. OCR text extracted from biscuit_clean1.png contains "Crunchy".
"""

import os
import sys
import pytest

# Ensure project root is available in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extract_ocr import extract_text

SAMPLE_IMAGE = os.path.join("dataset", "images", "biscuit_clean1.png")


def test_extract_text_output_format():
    """Verify that extract_text returns a list of dicts with text, bbox, and confidence."""
    assert os.path.isfile(SAMPLE_IMAGE), f"Sample image missing at {SAMPLE_IMAGE}"

    results = extract_text(SAMPLE_IMAGE)

    # Must return a non-empty list of detected text boxes
    assert isinstance(results, list), "extract_text must return a list"
    assert len(results) > 0, "extract_text returned an empty list"

    for idx, item in enumerate(results):
        assert isinstance(item, dict), f"Item {idx} is not a dictionary"
        assert "text" in item, f"Item {idx} missing 'text' key"
        assert "bbox" in item, f"Item {idx} missing 'bbox' key"
        assert "confidence" in item, f"Item {idx} missing 'confidence' key"

        # Check types
        assert isinstance(item["text"], str), f"Item {idx} 'text' is not a str"
        assert isinstance(item["bbox"], list), f"Item {idx} 'bbox' is not a list"
        assert len(item["bbox"]) == 4, f"Item {idx} 'bbox' must contain exactly 4 elements [x1, y1, x2, y2]"

        x1, y1, x2, y2 = item["bbox"]
        assert all(isinstance(coord, int) for coord in (x1, y1, x2, y2)), (
            f"Item {idx} bbox coordinates must be integers: {item['bbox']}"
        )
        assert x1 <= x2 and y1 <= y2, f"Item {idx} invalid bounding box geometry: {item['bbox']}"

        assert isinstance(item["confidence"], float), f"Item {idx} 'confidence' must be float"
        assert 0.0 <= item["confidence"] <= 1.0, f"Item {idx} confidence out of [0, 1] range: {item['confidence']}"


def test_biscuit_clean1_contains_crunchy():
    """Verify that OCR on biscuit_clean1.png detects 'Crunchy'."""
    assert os.path.isfile(SAMPLE_IMAGE), f"Sample image missing at {SAMPLE_IMAGE}"

    results = extract_text(SAMPLE_IMAGE)
    matched_items = [item["text"] for item in results if "Crunchy" in item["text"]]

    assert len(matched_items) > 0, (
        f"Expected 'Crunchy' in detected text for biscuit_clean1.png, but found none. "
        f"Detected texts: {[item['text'] for item in results]}"
    )

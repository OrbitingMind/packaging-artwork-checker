"""
test_locate.py - Tests for evidence localization using hand-made OCR lines.
Ensures zero API calls and deterministic execution.
"""

import os
import sys
from typing import Any, Dict, List
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from locate import get_info_panel_bbox, locate_evidence, merge_bboxes


@pytest.fixture
def sample_ocr_lines() -> List[Dict[str, Any]]:
    """Hand-crafted OCR lines simulating a packaged biscuit label."""
    return [
        {"bbox": [100, 50, 400, 90], "text": "Super Crunchy Cookies", "confidence": 0.99},
        {"bbox": [100, 120, 160, 150], "text": "Net", "confidence": 0.98},
        {"bbox": [170, 120, 220, 150], "text": "Qty:", "confidence": 0.98},
        {"bbox": [230, 120, 290, 150], "text": "200 g", "confidence": 0.99},
        {
            "bbox": [100, 180, 700, 210],
            "text": "Ingredients: Wheat flour, sugar, palm oil, invert syrup, salt,",
            "confidence": 0.97,
        },
        {"bbox": [100, 215, 250, 245], "text": "raising agents", "confidence": 0.96},
        {
            "bbox": [100, 270, 600, 300],
            "text": "Allergen Information: Contains wheat. May contain nuts",
            "confidence": 0.98,
        },
        {
            "bbox": [100, 330, 650, 360],
            "text": "Manufactured by: Bakers Treat Foods Ltd, Industrial Area,",
            "confidence": 0.97,
        },
        {"bbox": [100, 365, 260, 395], "text": "Mumbai 400001", "confidence": 0.98},
        {"bbox": [100, 420, 250, 450], "text": "FSSAI Lic. No.-", "confidence": 0.99},
        {"bbox": [260, 420, 420, 450], "text": "10020042001234", "confidence": 0.99},
        {"bbox": [100, 480, 180, 510], "text": "MRP: Rs.", "confidence": 0.98},
        {"bbox": [190, 480, 250, 510], "text": "50.00", "confidence": 0.99},
        {
            "bbox": [100, 530, 500, 560],
            "text": "Best before 6 months from date of packing",
            "confidence": 0.98,
        },
    ]


def test_get_info_panel_bbox(sample_ocr_lines):
    img_size = (800, 800)
    bbox = get_info_panel_bbox(sample_ocr_lines, img_size, pad=15)
    # min_x is 100 - 15 = 85, max_x is 700 + 15 = 715
    # min_y is 50 - 15 = 35, max_y is 560 + 15 = 575
    assert bbox == [85, 35, 715, 575]


def test_get_info_panel_bbox_empty():
    bbox = get_info_panel_bbox([], (800, 600), pad=15)
    assert bbox == [0, 0, 800, 600]


def test_merge_bboxes():
    boxes = [
        [100, 100, 200, 150],
        [80, 160, 220, 200],
    ]
    merged = merge_bboxes(boxes)
    assert merged == [80, 100, 220, 200]


def test_locate_r01_net_quantity_found(sample_ocr_lines):
    finding = {
        "rule_id": "R01",
        "verdict": "PASS",
        "found": "200 g",
        "expected": "200 g",
        "reason": "Net quantity '200 g' is present",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "found"
    assert box["bbox"] == [230, 120, 290, 150]
    assert "200 g" in box["label"]
    assert box["rule_id"] == "R01"


def test_locate_r02_wrong_net_quantity_found():
    """Simulates biscuit_errR02 where net quantity is 20 g instead of 200 g."""
    ocr_lines = [
        {"bbox": [100, 120, 160, 150], "text": "Net", "confidence": 0.98},
        {"bbox": [230, 120, 280, 150], "text": "20 g", "confidence": 0.99},
    ]
    finding = {
        "rule_id": "R02",
        "verdict": "FAIL",
        "found": "20 g",
        "expected": "200 g",
        "reason": "Net quantity '20 g' does not match spec '200 g'",
    }
    results = locate_evidence(ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "found"
    assert box["bbox"] == [230, 120, 280, 150]
    assert "20 g" in box["label"]
    assert box["verdict"] == "FAIL"


def test_locate_r05_missing_allergen_section(sample_ocr_lines):
    """Simulates biscuit_errR05 where allergen section is absent (FAIL)."""
    finding = {
        "rule_id": "R05",
        "verdict": "FAIL",
        "found": "None",
        "expected": "Contains wheat, oats. May contain milk.",
        "reason": "Allergen statement is missing when specification requires disclosure",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "missing"
    assert box["bbox"] == [85, 35, 715, 575]  # Padded info panel box
    assert "Allergen" in box["label"]
    assert "not found" in box["label"]


def test_locate_r04_veg_mark_missing(sample_ocr_lines):
    """Simulates juice_errR04 where vegetarian logo is absent."""
    finding = {
        "rule_id": "R04",
        "verdict": "FAIL",
        "found": "Absent",
        "expected": "Vegetarian logo present",
        "reason": "Vegetarian logo is missing",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "missing"
    assert box["bbox"] == [85, 35, 715, 575]
    assert "Vegetarian" in box["label"]


def test_locate_r04_veg_mark_passing_has_no_ocr_box(sample_ocr_lines):
    finding = {
        "rule_id": "R04",
        "verdict": "PASS",
        "found": "Present",
        "expected": "Vegetarian logo present",
        "reason": "Vegetarian logo is present",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    # Veg mark has no OCR text, so it does not produce a text box
    assert results == []


def test_locate_r07_multiline_ingredients_merged(sample_ocr_lines):
    finding = {
        "rule_id": "R07",
        "verdict": "PASS",
        "found": "Wheat flour, sugar, palm oil, invert syrup, salt, raising agents",
        "expected": "Wheat flour, sugar, palm oil, invert syrup, salt, raising agents",
        "reason": "Ingredients match specification in declared order",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "found"
    # Merges line 4 [100, 180, 700, 210] and line 5 [100, 215, 250, 245]
    assert box["bbox"] == [100, 180, 700, 245]
    assert "Ingredients" in box["label"]


def test_locate_r08_multiline_manufacturer_merged(sample_ocr_lines):
    finding = {
        "rule_id": "R08",
        "verdict": "PASS",
        "found": "Bakers Treat Foods Ltd, Industrial Area, Mumbai 400001",
        "expected": "Bakers Treat Foods Ltd, Industrial Area, Mumbai 400001",
        "reason": "Manufacturer name and address present",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "found"
    # Merges line 7 [100, 330, 650, 360] and line 8 [100, 365, 260, 395]
    assert box["bbox"] == [100, 330, 650, 395]
    assert "Manufacturer" in box["label"]


def test_locate_r09_fssai_license(sample_ocr_lines):
    finding = {
        "rule_id": "R09",
        "verdict": "PASS",
        "found": "10020042001234",
        "expected": "10020042001234",
        "reason": "FSSAI license number contains exactly 14 digits: '10020042001234'",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    box = results[0]
    assert box["kind"] == "found"
    assert box["bbox"] == [260, 420, 420, 450]


def test_locate_r10_mrp_and_best_before(sample_ocr_lines):
    finding = {
        "rule_id": "R10",
        "verdict": "PASS",
        "found": "MRP: 'Rs. 50.00', Best Before: '6 months from date of packing'",
        "expected": "MRP: Rs. 50.00, Best Before: 6 months from date of packing",
        "reason": "Both MRP and Best Before declarations are present",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 2
    mrp_box = next((b for b in results if "MRP" in b["label"]), None)
    bb_box = next((b for b in results if "Best before" in b["label"] or "Best Before" in b["label"]), None)
    assert mrp_box is not None
    assert bb_box is not None
    assert mrp_box["kind"] == "found"
    assert bb_box["kind"] == "found"
    # MRP merges adjacent 'MRP: Rs.' [100, 480, 180, 510] and '50.00' [190, 480, 250, 510]
    assert mrp_box["bbox"] == [100, 480, 250, 510]
    assert bb_box["bbox"] == [100, 530, 500, 560]


def test_locate_na_finding(sample_ocr_lines):
    finding = {
        "rule_id": "R05",
        "verdict": "N/A",
        "found": "None",
        "expected": "N/A",
        "reason": "Product specification specifies no allergens",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert results == []


def test_locate_r01_missing_net_quantity(sample_ocr_lines):
    finding = {
        "rule_id": "R01",
        "verdict": "FAIL",
        "found": "",
        "expected": "200 g",
        "reason": "Net quantity is missing",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    assert results[0]["kind"] == "missing"
    assert "Net quantity" in results[0]["label"]


def test_locate_r03_illegal_unit(sample_ocr_lines):
    ocr = [
        {"bbox": [100, 100, 200, 130], "text": "Net Qty: 100 gm", "confidence": 0.99}
    ]
    finding = {
        "rule_id": "R03",
        "verdict": "FAIL",
        "found": "100 gm",
        "expected": "Approved unit (g, kg, mg, ml, l)",
        "reason": "Net quantity unit in '100 gm' is not an approved symbol (g, kg, mg, ml, l)",
    }
    results = locate_evidence(ocr, finding, (800, 800))
    assert len(results) == 1
    assert results[0]["kind"] == "found"
    assert results[0]["bbox"] == [100, 100, 200, 130]


def test_ingredients_does_not_merge_allergen_barrier(sample_ocr_lines):
    finding = {
        "rule_id": "R07",
        "verdict": "PASS",
        "found": "Wheat flour, sugar, palm oil, invert syrup, salt, raising agents",
        "expected": "Wheat flour, sugar, palm oil, invert syrup, salt, raising agents",
        "reason": "Ingredients match",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    # Y2 must not reach the allergen line (which starts at Y=270)
    assert results[0]["bbox"][3] <= 250


def test_locate_missing_manufacturer(sample_ocr_lines):
    finding = {
        "rule_id": "R08",
        "verdict": "FAIL",
        "found": "None",
        "expected": "Manufacturer details",
        "reason": "Manufacturer name and address missing",
    }
    results = locate_evidence(sample_ocr_lines, finding, (800, 800))
    assert len(results) == 1
    assert results[0]["kind"] == "missing"
    assert "Manufacturer" in results[0]["label"]


"""
Unit tests for checks.py using hand-made extracted data dictionaries without API calls.
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from checks import check_rules

BISCUIT_SPEC = {
    "product": "biscuit",
    "product_name": "Crunchy Oat Biscuits",
    "net_quantity": "200 g",
    "veg_mark": "veg",
    "ingredients": "Wheat flour, oats, sugar, palm oil, invert syrup, salt, raising agents",
    "has_allergens": True,
    "allergens": "Contains wheat, oats. May contain milk.",
    "manufacturer": "Golden Crust Foods Pvt Ltd, 12 MG Road, Bengaluru 560001",
    "fssai_license": "10020042001234",
    "mrp": "Rs. 40.00",
    "best_before": "Best before 6 months from date of packing",
}

SALT_SPEC = {
    "product": "salt",
    "product_name": "Iodized Salt",
    "net_quantity": "1 kg",
    "veg_mark": "veg",
    "ingredients": "Edible common salt, potassium iodate (iodine 15 ppm)",
    "has_allergens": False,
    "allergens": "",
    "manufacturer": "Seashore Salts Pvt Ltd, 21 Harbour Road, Udupi 576101",
    "fssai_license": "10019043000654",
    "mrp": "Rs. 28.00",
    "best_before": "Best before 24 months from date of packing",
}


def _make_sample_extracted(overrides=None):
    """Generates a complete, valid extracted dict with optional field overrides."""
    base = {
        "product_name": {"value": "Crunchy Oat Biscuits", "confidence": 0.99},
        "net_quantity": {"value": "200 g", "confidence": 0.99},
        "veg_mark_present": True,
        "ingredients": {
            "value": "Wheat flour, oats, sugar, palm oil, invert syrup, salt, raising agents",
            "confidence": 0.98,
        },
        "allergen_statement": {
            "value": "Contains wheat, oats. May contain milk.",
            "confidence": 0.99,
        },
        "manufacturer": {
            "value": "Golden Crust Foods Pvt Ltd, 12 MG Road, Bengaluru 560001",
            "confidence": 0.98,
        },
        "fssai_license": {"value": "10020042001234", "confidence": 0.98},
        "mrp": {"value": "Rs. 40.00", "confidence": 0.99},
        "best_before": {
            "value": "Best before 6 months from date of packing",
            "confidence": 0.98,
        },
    }
    if overrides:
        base.update(overrides)
    return base


def _find_rule(findings, rule_id):
    """Helper to retrieve a finding dictionary by rule_id."""
    for item in findings:
        if item["rule_id"] == rule_id:
            return item
    return None


def test_r01_pass_case():
    """R01 PASS: Declared net quantity is present on the packaging."""
    extracted = _make_sample_extracted({"net_quantity": {"value": "200 g", "confidence": 0.99}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r01 = _find_rule(findings, "R01")
    assert r01 is not None
    assert r01["verdict"] == "PASS"
    assert r01["found"] == "200 g"


def test_r01_fail_case():
    """R01 FAIL: Net quantity is missing from the packaging."""
    extracted = _make_sample_extracted({"net_quantity": {"value": "", "confidence": 0.95}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r01 = _find_rule(findings, "R01")
    assert r01 is not None
    assert r01["verdict"] == "FAIL"


def test_r02_pass_case():
    """R02 PASS: Declared net quantity matches approved specification value."""
    extracted = _make_sample_extracted({"net_quantity": {"value": "200 g", "confidence": 0.99}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r02 = _find_rule(findings, "R02")
    assert r02 is not None
    assert r02["verdict"] == "PASS"


def test_r02_fail_case():
    """R02 FAIL: Declared net quantity differs from approved specification value."""
    extracted = _make_sample_extracted({"net_quantity": {"value": "20 g", "confidence": 0.95}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r02 = _find_rule(findings, "R02")
    assert r02 is not None
    assert r02["verdict"] == "FAIL"


def test_r09_pass_case():
    """R09 PASS: FSSAI license number consists of exactly 14 numeric digits."""
    extracted = _make_sample_extracted({"fssai_license": {"value": "10020042001234", "confidence": 0.99}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r09 = _find_rule(findings, "R09")
    assert r09 is not None
    assert r09["verdict"] == "PASS"


def test_r09_fail_case():
    """R09 FAIL: FSSAI license number does not have 14 digits (e.g. 13 digits)."""
    extracted = _make_sample_extracted({"fssai_license": {"value": "1002004200123", "confidence": 0.95}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r09 = _find_rule(findings, "R09")
    assert r09 is not None
    assert r09["verdict"] == "FAIL"


def test_salt_allergens_na_case():
    """R05 & R06 N/A: Salt product specification has has_allergens=False."""
    extracted = {
        "product_name": {"value": "Iodized Salt", "confidence": 0.99},
        "net_quantity": {"value": "1 kg", "confidence": 0.99},
        "veg_mark_present": True,
        "ingredients": {
            "value": "Edible common salt, potassium iodate (iodine 15 ppm)",
            "confidence": 0.98,
        },
        "allergen_statement": {"value": "", "confidence": 0.99},
        "manufacturer": {
            "value": "Seashore Salts Pvt Ltd, 21 Harbour Road, Udupi 576101",
            "confidence": 0.98,
        },
        "fssai_license": {"value": "10019043000654", "confidence": 0.98},
        "mrp": {"value": "Rs. 28.00", "confidence": 0.99},
        "best_before": {
            "value": "Best before 24 months from date of packing",
            "confidence": 0.98,
        },
    }
    findings = check_rules(extracted, SALT_SPEC)
    r05 = _find_rule(findings, "R05")
    r06 = _find_rule(findings, "R06")
    assert r05 is not None
    assert r05["verdict"] == "N/A"
    assert r06 is not None
    assert r06["verdict"] == "N/A"


def test_low_confidence_triggers_needs_review():
    """Low confidence (< 0.6) on a failing field converts FAIL to NEEDS_REVIEW."""
    extracted = _make_sample_extracted({"fssai_license": {"value": "123", "confidence": 0.45}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r09 = _find_rule(findings, "R09")
    assert r09 is not None
    assert r09["verdict"] == "NEEDS_REVIEW"


def test_r02_r03_na_when_net_quantity_empty():
    """R02 and R03 return N/A with reason 'net quantity missing, see R01' when net_quantity is empty."""
    extracted = _make_sample_extracted({"net_quantity": {"value": "", "confidence": 0.95}})
    findings = check_rules(extracted, BISCUIT_SPEC)
    r01 = _find_rule(findings, "R01")
    r02 = _find_rule(findings, "R02")
    r03 = _find_rule(findings, "R03")
    assert r01["verdict"] == "FAIL"
    assert r02["verdict"] == "N/A"
    assert r02["reason"] == "net quantity missing, see R01"
    assert r03["verdict"] == "N/A"
    assert r03["reason"] == "net quantity missing, see R01"


def test_r07_pass_case():
    """R07 PASS: Same items in same order."""
    extracted = _make_sample_extracted({
        "ingredients": {
            "value": "Wheat flour, oats, sugar, palm oil, invert syrup, salt, raising agents",
            "confidence": 0.98,
        }
    })
    findings = check_rules(extracted, BISCUIT_SPEC)
    r07 = _find_rule(findings, "R07")
    assert r07 is not None
    assert r07["verdict"] == "PASS"
    assert "declared order" in r07["reason"]


def test_r07_fail_one_item_removed():
    """R07 FAIL: One item removed from spec (e.g. oats removed)."""
    extracted = _make_sample_extracted({
        "ingredients": {
            "value": "Wheat flour, sugar, palm oil, invert syrup, salt, raising agents",
            "confidence": 0.98,
        }
    })
    findings = check_rules(extracted, BISCUIT_SPEC)
    r07 = _find_rule(findings, "R07")
    assert r07 is not None
    assert r07["verdict"] == "FAIL"
    assert "Missing ingredient(s): oats" in r07["reason"]


def test_r07_needs_review_reordered():
    """R07 NEEDS_REVIEW: Same items present, but in a different order."""
    extracted = _make_sample_extracted({
        "ingredients": {
            "value": "oats, Wheat flour, sugar, palm oil, invert syrup, salt, raising agents",
            "confidence": 0.98,
        }
    })
    findings = check_rules(extracted, BISCUIT_SPEC)
    r07 = _find_rule(findings, "R07")
    assert r07 is not None
    assert r07["verdict"] == "NEEDS_REVIEW"
    assert "different order" in r07["reason"]


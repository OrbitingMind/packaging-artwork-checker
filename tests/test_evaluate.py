"""
tests/test_evaluate.py
Unit tests for the packaging compliance evaluation module (evaluate.py).
"""

import os
import pytest
from evaluate import (
    safe_div,
    init_metrics_counter,
    compute_rates,
    format_pct,
    build_markdown_table,
    evaluate_split,
    save_evaluation_results,
)


def test_safe_div():
    assert safe_div(10, 2) == 5.0
    assert safe_div(10, 0) == 0.0
    assert safe_div(10, 0, default=-1.0) == -1.0


def test_init_metrics_counter():
    counts = init_metrics_counter()
    assert set(counts.keys()) == {"tp", "fn", "caught", "fp", "review_burden", "tn"}
    assert all(v == 0 for v in counts.values())


def test_compute_rates():
    counts = {
        "tp": 10,
        "fn": 1,
        "caught": 1,
        "fp": 2,
        "review_burden": 1,
        "tn": 20,
    }
    rates = compute_rates(counts)

    assert rates["tp"] == 10
    assert rates["total"] == 35  # 10 + 1 + 1 + 2 + 1 + 20
    assert pytest.approx(rates["precision"], 0.0001) == 10 / 12
    assert pytest.approx(rates["recall"], 0.0001) == 10 / 12
    assert pytest.approx(rates["recall_with_review"], 0.0001) == 11 / 12
    assert pytest.approx(rates["false_alarm_rate"], 0.0001) == 2 / 23
    assert pytest.approx(rates["review_rate"], 0.0001) == 2 / 35


def test_compute_rates_zero_division():
    counts = init_metrics_counter()
    rates = compute_rates(counts)
    assert rates["total"] == 0
    assert rates["precision"] == 0.0
    assert rates["recall"] == 0.0
    assert rates["recall_with_review"] == 0.0
    assert rates["false_alarm_rate"] == 0.0
    assert rates["review_rate"] == 0.0


def test_format_pct():
    assert format_pct(0.875) == "87.5%"
    assert format_pct(1.0) == "100.0%"
    assert format_pct(0.0) == "0.0%"
    assert format_pct(0.0288) == "2.9%"


def test_build_markdown_table():
    headers = ["Col1", "Col2"]
    rows = [["A", "1"], ["B", "2"]]
    table = build_markdown_table(headers, rows, ["left", "right"])
    lines = table.splitlines()
    assert len(lines) == 4
    assert lines[0] == "| Col1 | Col2 |"
    assert lines[1] == "| :--- | ---: |"
    assert lines[2] == "| A | 1 |"
    assert lines[3] == "| B | 2 |"


def test_evaluate_invalid_split():
    with pytest.raises(ValueError):
        evaluate_split("invalid_split")


def test_evaluate_dev_split_runs():
    result = evaluate_split("dev")
    assert result["split"] == "dev"
    assert result["images_total"] == 24
    assert result["images_evaluated"] == 24
    assert result["images_failed"] == 0

    overall = result["overall"]
    assert "precision" in overall
    assert "recall" in overall
    assert "recall_with_review" in overall
    assert "false_alarm_rate" in overall
    assert "review_rate" in overall
    assert result["rules_excluded_na"] == 6
    assert overall["total"] == 226

    # Check per-rule covers R01-R10
    per_rule = result["per_rule"]
    for i in range(1, 11):
        rule_id = f"R{i:02d}"
        assert rule_id in per_rule

    # Check per-product covers the 5 products
    per_product = result["per_product"]
    for prod in ["biscuit", "chips", "juice", "masala", "salt"]:
        assert prod in per_product

    # Check saving results
    json_path, md_path = save_evaluation_results(result)
    assert os.path.exists(json_path)
    assert os.path.exists(md_path)

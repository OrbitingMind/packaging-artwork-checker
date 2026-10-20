import os
import sys
import pytest

# Ensure project root is in sys.path for direct pytest invocation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rules_loader import REQUIRED_FIELDS, load_rules


def test_load_ten_rules():
    """Verify that exactly 10 rules load successfully from rules.yaml."""
    rules = load_rules()
    assert isinstance(rules, list), "Rules should be returned as a list"
    assert len(rules) == 10, f"Expected exactly 10 rules, found {len(rules)}"


def test_rule_ids_unique_and_match_expected():
    """Verify that all rule IDs are unique and match R01-R10."""
    rules = load_rules()
    rule_ids = [rule["id"] for rule in rules]

    # Check uniqueness (in Python, set() deduplicates items like std::set in C++)
    assert len(rule_ids) == len(set(rule_ids)), f"Duplicate rule IDs detected: {rule_ids}"

    expected_ids = [f"R{i:02d}" for i in range(1, 11)]
    assert rule_ids == expected_ids, f"Expected {expected_ids}, got {rule_ids}"


def test_all_required_fields_present():
    """Verify that every rule contains all mandatory fields with non-empty values."""
    rules = load_rules()
    for rule in rules:
        rule_id = rule.get("id", "UNKNOWN")
        for field in REQUIRED_FIELDS:
            assert field in rule, f"Rule {rule_id} is missing required field '{field}'"
            assert rule[field] is not None, f"Rule {rule_id} field '{field}' cannot be None"
            assert str(rule[field]).strip() != "", f"Rule {rule_id} field '{field}' cannot be empty"


def test_r05_r06_applies_when_condition():
    """Verify that R05 and R06 specify an allergen applies_when condition."""
    rules = load_rules()
    rules_by_id = {r["id"]: r for r in rules}

    # R05 and R06 must specify condition based on has_allergens
    for rid in ["R05", "R06"]:
        rule = rules_by_id[rid]
        applies_when = rule["applies_when"].strip()
        assert applies_when != "always", f"Rule {rid} applies_when must be conditional, got '{applies_when}'"
        assert "has_allergens" in applies_when, f"Rule {rid} applies_when should reference has_allergens"

    # Other rules apply always
    for rid, rule in rules_by_id.items():
        if rid not in ["R05", "R06"]:
            assert rule["applies_when"] == "always", f"Rule {rid} expected applies_when 'always', got '{rule['applies_when']}'"


def test_check_types():
    """Verify check_type is 'llm' for R04 and R07, and 'deterministic' for all others."""
    rules = load_rules()
    for rule in rules:
        rid = rule["id"]
        if rid in ["R04", "R07"]:
            assert rule["check_type"] == "llm", f"Rule {rid} check_type should be 'llm', got '{rule['check_type']}'"
        else:
            assert rule["check_type"] == "deterministic", (
                f"Rule {rid} check_type should be 'deterministic', got '{rule['check_type']}'"
            )


def test_fssai_clause_is_verify():
    """Verify that fssai_clause is 'VERIFY' for every rule as instructed."""
    rules = load_rules()
    for rule in rules:
        assert rule["fssai_clause"] == "VERIFY", f"Rule {rule['id']} fssai_clause should be 'VERIFY'"


def test_loader_raises_on_missing_field(tmp_path):
    """Verify that load_rules raises ValueError if a required field is missing."""
    invalid_yaml = tmp_path / "invalid_rules.yaml"
    # Missing 'review_condition'
    content = """
- id: "R01"
  name: "Net quantity present"
  fssai_clause: "VERIFY"
  check_type: "deterministic"
  applies_when: "always"
  spec_field: "net_quantity"
  what_to_extract: "Net quantity"
  pass_condition: "Pass"
  fail_condition: "Fail"
"""
    invalid_yaml.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="missing required field"):
        load_rules(str(invalid_yaml))


def test_loader_raises_on_file_not_found():
    """Verify that load_rules raises FileNotFoundError when given a non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_rules("non_existent_rules_file.yaml")

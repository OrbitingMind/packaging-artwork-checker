"""
Rules Loader module for FSSAI packaging compliance checker.
Loads and validates rules defined in rules.yaml using PyYAML.
"""

import os
from typing import Any, Dict, List
import yaml

# List of all mandatory fields required in each rule definition
REQUIRED_FIELDS: List[str] = [
    "id",
    "name",
    "fssai_clause",
    "check_type",
    "applies_when",
    "spec_field",
    "what_to_extract",
    "pass_condition",
    "fail_condition",
    "review_condition",
]


def load_rules(path: str = "rules.yaml") -> List[Dict[str, Any]]:
    """
    Loads packaging compliance rules from a YAML file and validates that
    every rule has all required fields.

    Parameters:
        path (str): File path to rules.yaml. Defaults to 'rules.yaml'.

    Returns:
        List[Dict[str, Any]]: List of rule dictionaries.

    Raises:
        FileNotFoundError: If the rules file does not exist.
        ValueError: If YAML syntax is invalid, structure is not a list,
                    or any rule is missing a required field.
    """
    # Resolve path relative to this script directory if not found in current working directory
    resolved_path = path
    if not os.path.isabs(path) and not os.path.exists(path):
        fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        if os.path.exists(fallback_path):
            resolved_path = fallback_path

    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Rules file not found at '{path}' (resolved: '{resolved_path}')")

    with open(resolved_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse YAML from '{resolved_path}': {exc}") from exc

    # In YAML, a top-level sequence parses as a Python list (like std::vector<std::map<...>> in C++)
    if not isinstance(data, list):
        raise ValueError(
            f"Expected a top-level list of rules in '{resolved_path}', but got {type(data).__name__}"
        )

    # Validate each rule against REQUIRED_FIELDS
    for index, rule in enumerate(data):
        if not isinstance(rule, dict):
            raise ValueError(
                f"Rule at index {index} must be a dictionary/mapping, got {type(rule).__name__}"
            )

        rule_id = rule.get("id", f"index_{index}")
        for field in REQUIRED_FIELDS:
            # Check if field is present and not None
            if field not in rule or rule[field] is None:
                raise ValueError(
                    f"Rule '{rule_id}' at index {index} is missing required field: '{field}'"
                )

    return data


if __name__ == "__main__":
    # Self-test when executed directly
    rules = load_rules()
    print(f"Successfully loaded {len(rules)} rules from rules.yaml:")
    for r in rules:
        print(f"  [{r['id']}] {r['name']} ({r['check_type']}, applies: {r['applies_when']})")

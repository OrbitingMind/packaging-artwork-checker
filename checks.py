"""
Rule checker module for FSSAI packaging compliance (R01 - R10).
"""

from difflib import SequenceMatcher
import re
from typing import Any, Dict, List, Optional, Tuple
from rules_loader import load_rules

ALLERGEN_FILLER = {"contains", "may", "contain", "and", "or", "traces", "of", "in"}


def _get_val_conf(extracted: Dict[str, Any], field: str) -> Tuple[str, float]:
    """Helper to extract string value and confidence float from extracted dict."""
    entry = extracted.get(field, {})
    if isinstance(entry, dict):
        val = str(entry.get("value", "") or "").strip()
        conf = float(entry.get("confidence", 1.0) if entry.get("confidence") is not None else 1.0)
        return val, conf
    if isinstance(entry, str):
        return entry.strip(), 1.0
    return str(entry or "").strip(), 1.0


def _apply_confidence_threshold(verdict: str, conf: float, reason: str) -> Tuple[str, str]:
    """If field confidence is below 0.6, return NEEDS_REVIEW instead of FAIL."""
    if verdict == "FAIL" and conf < 0.6:
        return "NEEDS_REVIEW", f"{reason} (low confidence: {conf:.2f})"
    return verdict, reason


def _split_and_normalize_ingredients(text: str) -> List[str]:
    """
    Splits ingredients string on commas and normalizes each item:
    lowercase, trimmed, with trailing punctuation removed.
    """
    if not text:
        return []
    items: List[str] = []
    for part in text.split(","):
        cleaned = part.strip().lower().rstrip(".;:!?,-").strip()
        if cleaned:
            items.append(cleaned)
    return items


def check_rules(
    extracted: Dict[str, Any],
    spec: Dict[str, Any],
    rules: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates rules R01-R10 against extracted packaging data and approved specification.
    Returns list of findings: {rule_id, verdict, found, expected, reason}.
    """
    if rules is None:
        rules = load_rules()

    findings: List[Dict[str, Any]] = []

    # R01: Net quantity present
    net_val, net_conf = _get_val_conf(extracted, "net_quantity")
    spec_net = spec.get("net_quantity", "")
    if net_val:
        r01_v = "PASS"
        r01_r = f"Net quantity '{net_val}' is present"
    else:
        r01_v = "FAIL"
        r01_r = "Net quantity is missing"
    r01_v, r01_r = _apply_confidence_threshold(r01_v, net_conf, r01_r)
    findings.append({
        "rule_id": "R01",
        "verdict": r01_v,
        "found": net_val,
        "expected": spec_net or "Declared net quantity",
        "reason": r01_r,
    })

    # R02: Normalized equality with spec (numerical quantity matches spec)
    if not net_val:
        r02_v = "N/A"
        r02_r = "net quantity missing, see R01"
    else:
        net_nums = re.findall(r"\d+(?:\.\d+)?", net_val)
        spec_nums = re.findall(r"\d+(?:\.\d+)?", str(spec_net))
        if net_nums and spec_nums and float(net_nums[0]) == float(spec_nums[0]):
            r02_v = "PASS"
            r02_r = f"Net quantity numerical value '{net_nums[0]}' matches spec '{spec_nums[0]}'"
        else:
            r02_v = "FAIL"
            r02_r = f"Net quantity '{net_val}' does not match spec '{spec_net}'"
    r02_v, r02_r = _apply_confidence_threshold(r02_v, net_conf, r02_r)
    findings.append({
        "rule_id": "R02",
        "verdict": r02_v,
        "found": net_val,
        "expected": spec_net,
        "reason": r02_r,
    })

    # R03: Unit regex (g, kg, mg, ml, l)
    unit_match = re.search(r"(?<=[0-9\s])(g|kg|mg|ml|[lL])\s*$", net_val) if net_val else None
    if not net_val:
        r03_v = "N/A"
        r03_r = "net quantity missing, see R01"
    elif unit_match:
        r03_v = "PASS"
        r03_r = f"Net quantity unit '{unit_match.group(1)}' conforms to legal metrology standards"
    else:
        r03_v = "FAIL"
        r03_r = f"Net quantity unit in '{net_val}' is not an approved symbol (g, kg, mg, ml, l)"
    r03_v, r03_r = _apply_confidence_threshold(r03_v, net_conf, r03_r)
    findings.append({
        "rule_id": "R03",
        "verdict": r03_v,
        "found": net_val,
        "expected": "Approved unit (g, kg, mg, ml, l)",
        "reason": r03_r,
    })

    # R04: veg_mark_present
    veg_present = extracted.get("veg_mark_present", False)
    if isinstance(veg_present, dict):
        veg_present = bool(veg_present.get("value", False))
    if veg_present:
        r04_v = "PASS"
        r04_r = "Vegetarian logo (green square and circle) is present"
    else:
        r04_v = "FAIL"
        r04_r = "Vegetarian logo is missing"
    findings.append({
        "rule_id": "R04",
        "verdict": r04_v,
        "found": "Present" if veg_present else "Absent",
        "expected": "Vegetarian logo present",
        "reason": r04_r,
    })

    # R05: Allergen statement present (N/A if spec has_allergens is false)
    has_allergens = bool(spec.get("has_allergens", False))
    allergen_val, allergen_conf = _get_val_conf(extracted, "allergen_statement")
    spec_allergens_raw = spec.get("allergens", "")
    if not has_allergens:
        r05_v = "N/A"
        r05_r = "Product specification specifies no allergens"
    elif allergen_val:
        r05_v = "PASS"
        r05_r = f"Allergen statement is present: '{allergen_val}'"
    else:
        r05_v = "FAIL"
        r05_r = "Allergen statement is missing when specification requires disclosure"
    r05_v, r05_r = _apply_confidence_threshold(r05_v, allergen_conf, r05_r)
    findings.append({
        "rule_id": "R05",
        "verdict": r05_v,
        "found": allergen_val or "None",
        "expected": spec_allergens_raw if has_allergens else "N/A",
        "reason": r05_r,
    })

    # R06: Every spec allergen appears in statement (N/A if no allergens)
    if not has_allergens:
        r06_v = "N/A"
        r06_r = "Product specification specifies no allergens"
        r06_exp = "N/A"
    else:
        spec_words = [
            w for w in re.findall(r"[a-zA-Z]+", spec_allergens_raw.lower()) if w not in ALLERGEN_FILLER
        ]
        r06_exp = ", ".join(spec_words)
        if not allergen_val:
            # Allergen section absence is flagged by R05
            r06_v = "PASS"
            r06_r = "Allergen statement absent (handled by R05)"
        else:
            missing = [a for a in spec_words if a not in allergen_val.lower()]
            if not missing:
                r06_v = "PASS"
                r06_r = f"All spec allergens ({r06_exp}) declared on packaging"
            else:
                r06_v = "FAIL"
                r06_r = f"Missing allergen declaration for: {', '.join(missing)}"
    r06_v, r06_r = _apply_confidence_threshold(r06_v, allergen_conf, r06_r)
    findings.append({
        "rule_id": "R06",
        "verdict": r06_v,
        "found": allergen_val or "None",
        "expected": r06_exp,
        "reason": r06_r,
    })

    # R07: Split ingredients on commas, normalize, match one-to-one using ratio >= 0.9
    ing_val, ing_conf = _get_val_conf(extracted, "ingredients")
    spec_ing = spec.get("ingredients", "")

    spec_items = _split_and_normalize_ingredients(spec_ing)
    found_items = _split_and_normalize_ingredients(ing_val)

    if not found_items:
        r07_v = "FAIL"
        r07_r = f"Missing ingredient(s): {', '.join(spec_items)}" if spec_items else "Ingredients list is missing"
    else:
        # Check if same items in same order
        same_order = False
        if len(spec_items) == len(found_items):
            same_order = all(
                SequenceMatcher(None, s, f).ratio() >= 0.9
                for s, f in zip(spec_items, found_items)
            )

        if same_order:
            r07_v = "PASS"
            r07_r = "Ingredients match specification in declared order"
        else:
            # One-to-one bipartite matching using SequenceMatcher ratio >= 0.9
            candidates = []
            for i, s in enumerate(spec_items):
                for j, f in enumerate(found_items):
                    ratio = SequenceMatcher(None, s, f).ratio()
                    if ratio >= 0.9:
                        candidates.append((ratio, i, j))

            # Greedily match pairs with highest similarity ratio first
            candidates.sort(key=lambda x: x[0], reverse=True)

            matched_spec = set()
            matched_found = set()
            for _, i, j in candidates:
                if i not in matched_spec and j not in matched_found:
                    matched_spec.add(i)
                    matched_found.add(j)

            missing = [spec_items[i] for i in range(len(spec_items)) if i not in matched_spec]
            extra = [found_items[j] for j in range(len(found_items)) if j not in matched_found]

            if not missing and not extra:
                # All items matched one-to-one, but not in same order
                r07_v = "NEEDS_REVIEW"
                r07_r = "Ingredients match specification but in a different order"
            else:
                r07_v = "FAIL"
                parts = []
                if missing:
                    parts.append(f"Missing ingredient(s): {', '.join(missing)}")
                if extra:
                    parts.append(f"Extra ingredient(s): {', '.join(extra)}")
                r07_r = "; ".join(parts)

    r07_v, r07_r = _apply_confidence_threshold(r07_v, ing_conf, r07_r)
    findings.append({
        "rule_id": "R07",
        "verdict": r07_v,
        "found": ing_val or "None",
        "expected": spec_ing,
        "reason": r07_r,
    })

    # R08: Manufacturer present and similar to spec
    mfg_val, mfg_conf = _get_val_conf(extracted, "manufacturer")
    spec_mfg = spec.get("manufacturer", "")
    if not mfg_val:
        r08_v = "FAIL"
        r08_r = "Manufacturer name and address missing"
    else:
        mfg_ratio = SequenceMatcher(
            None, " ".join(mfg_val.lower().split()), " ".join(spec_mfg.lower().split())
        ).ratio()
        if mfg_ratio >= 0.70:
            r08_v = "PASS"
            r08_r = f"Manufacturer name and address present (similarity: {mfg_ratio:.2f})"
        else:
            r08_v = "FAIL"
            r08_r = f"Manufacturer details differ from specification (similarity: {mfg_ratio:.2f})"
    r08_v, r08_r = _apply_confidence_threshold(r08_v, mfg_conf, r08_r)
    findings.append({
        "rule_id": "R08",
        "verdict": r08_v,
        "found": mfg_val or "None",
        "expected": spec_mfg,
        "reason": r08_r,
    })

    # R09: FSSAI is exactly 14 digits
    fssai_val, fssai_conf = _get_val_conf(extracted, "fssai_license")
    spec_fssai = spec.get("fssai_license", "")
    digits = re.sub(r"\D", "", fssai_val)
    if len(digits) == 14:
        spec_digits = re.sub(r"\D", "", str(spec_fssai))
        if spec_digits and digits != spec_digits:
            r09_v = "FAIL"
            r09_r = f"FSSAI license '{digits}' does not match spec '{spec_digits}'"
        else:
            r09_v = "PASS"
            r09_r = f"FSSAI license number contains exactly 14 digits: '{digits}'"
    else:
        r09_v = "FAIL"
        r09_r = f"FSSAI license number has {len(digits)} digits (expected 14 digits)"
    r09_v, r09_r = _apply_confidence_threshold(r09_v, fssai_conf, r09_r)
    findings.append({
        "rule_id": "R09",
        "verdict": r09_v,
        "found": fssai_val or "None",
        "expected": spec_fssai or "14-digit license number",
        "reason": r09_r,
    })

    # R10: MRP and best_before both present
    mrp_val, mrp_conf = _get_val_conf(extracted, "mrp")
    bb_val, bb_conf = _get_val_conf(extracted, "best_before")
    spec_mrp = spec.get("mrp", "")
    spec_bb = spec.get("best_before", "")
    min_r10_conf = min(mrp_conf, bb_conf)
    if mrp_val and bb_val:
        r10_v = "PASS"
        r10_r = "Both MRP and Best Before declarations are present"
    else:
        missing_parts = []
        if not mrp_val:
            missing_parts.append("MRP")
        if not bb_val:
            missing_parts.append("Best Before")
        r10_v = "FAIL"
        r10_r = f"Missing mandatory field(s): {', '.join(missing_parts)}"
    r10_v, r10_r = _apply_confidence_threshold(r10_v, min_r10_conf, r10_r)
    findings.append({
        "rule_id": "R10",
        "verdict": r10_v,
        "found": f"MRP: '{mrp_val}', Best Before: '{bb_val}'",
        "expected": f"MRP: {spec_mrp}, Best Before: {spec_bb}",
        "reason": r10_r,
    })

    return findings

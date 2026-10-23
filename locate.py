"""
locate.py - Evidence localization for packaging artwork compliance findings.

Locates evidence regions for FSSAI compliance findings on packaging images:
- Fuzzy matches text values against OCR detected lines using difflib.
- Merges adjacent matching lines for multi-line fields (ingredients, allergens, manufacturer).
- Outlines missing sections using the padded info panel bounding box.
"""

from difflib import SequenceMatcher
import re
from typing import Any, Dict, List, Optional, Set, Tuple


# Common rule names and clauses for quick lookup if not supplied in findings
RULE_INFO = {
    "R01": {"name": "Net quantity present", "clause": "VERIFY", "section": "net_quantity"},
    "R02": {"name": "Net quantity matches spec", "clause": "VERIFY", "section": "net_quantity"},
    "R03": {"name": "Correct unit", "clause": "VERIFY", "section": "net_quantity"},
    "R04": {"name": "Veg mark present", "clause": "VERIFY", "section": "veg_mark"},
    "R05": {"name": "Allergen section present", "clause": "VERIFY", "section": "allergens"},
    "R06": {"name": "Allergens match spec", "clause": "VERIFY", "section": "allergens"},
    "R07": {"name": "Ingredients match spec", "clause": "VERIFY", "section": "ingredients"},
    "R08": {"name": "Manufacturer name and address present", "clause": "VERIFY", "section": "manufacturer"},
    "R09": {"name": "FSSAI number is 14 digits", "clause": "VERIFY", "section": "fssai_license"},
    "R10": {"name": "MRP and best-before present", "clause": "VERIFY", "section": "mrp_best_before"},
}

SECTION_BARRIERS = {
    "ingredients": ["allergen", "manufactured", "mfg", "mkt", "fssai", "mrp", "net", "best before"],
    "allergens": ["ingredients", "manufactured", "mfg", "mkt", "fssai", "mrp", "net", "best before"],
    "manufacturer": ["ingredients", "allergen", "fssai", "mrp", "net", "best before"],
}

MULTILINE_RULES = {"R05", "R06", "R07", "R08"}


def normalize_text(text: Any) -> str:
    """Normalizes string for comparison: lowercase, replaces punctuation with single spaces."""
    if text is None:
        return ""
    return re.sub(r"[^a-zA-Z0-9]+", " ", str(text).lower()).strip()


def is_absent_value(val: Any) -> bool:
    """Checks if a finding found value indicates absence or missing text."""
    if val is None:
        return True
    s = str(val).strip().lower()
    return s in ["", "none", "absent", "(none)", "false", "missing"]


def get_info_panel_bbox(
    ocr_lines: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    pad: int = 15,
) -> List[int]:
    """
    Computes bounding box encompassing all OCR detected boxes, padded by `pad` pixels.
    Falls back to full image bounds if no OCR boxes are available.
    """
    width, height = image_size
    if not ocr_lines:
        return [0, 0, int(width), int(height)]

    min_x = min(line["bbox"][0] for line in ocr_lines)
    min_y = min(line["bbox"][1] for line in ocr_lines)
    max_x = max(line["bbox"][2] for line in ocr_lines)
    max_y = max(line["bbox"][3] for line in ocr_lines)

    pad_min_x = max(0, int(min_x) - pad)
    pad_min_y = max(0, int(min_y) - pad)
    pad_max_x = min(int(width), int(max_x) + pad)
    pad_max_y = min(int(height), int(max_y) + pad)

    return [pad_min_x, pad_min_y, pad_max_x, pad_max_y]


def merge_bboxes(bboxes: List[List[int]]) -> List[int]:
    """Merges a collection of [x1, y1, x2, y2] bounding boxes into a single enclosing box."""
    if not bboxes:
        return [0, 0, 0, 0]
    return [
        int(min(b[0] for b in bboxes)),
        int(min(b[1] for b in bboxes)),
        int(max(b[2] for b in bboxes)),
        int(max(b[3] for b in bboxes)),
    ]


def _match_single_line(ocr_lines: List[Dict[str, Any]], target: str) -> Optional[int]:
    """
    Finds the index of the single OCR line that best fuzzy-matches `target`.
    Uses difflib SequenceMatcher and substring containment.
    """
    target_norm = normalize_text(target)
    if not target_norm or not ocr_lines:
        return None

    best_idx = None
    best_score = -1.0

    target_digits = re.sub(r"\D", "", target_norm)

    for idx, line in enumerate(ocr_lines):
        line_norm = normalize_text(line.get("text", ""))
        if not line_norm:
            continue

        # Exact match
        if target_norm == line_norm:
            return idx

        # Exact digits match for numeric fields (e.g. FSSAI or net quantity)
        if len(target_digits) >= 6:
            line_digits = re.sub(r"\D", "", line_norm)
            if target_digits in line_digits or line_digits == target_digits:
                return idx

        score = 0.0

        # Substring checks
        if target_norm in line_norm:
            score = 0.90 + 0.10 * (len(target_norm) / len(line_norm))
        elif line_norm in target_norm:
            score = 0.80 + 0.10 * (len(line_norm) / len(target_norm))
        else:
            # SequenceMatcher ratio
            ratio = SequenceMatcher(None, target_norm, line_norm).ratio()
            # Longest matching block
            sm = SequenceMatcher(None, target_norm, line_norm)
            match = sm.find_longest_match(0, len(target_norm), 0, len(line_norm))
            longest_ratio = match.size / max(len(target_norm), len(line_norm))
            score = max(ratio, longest_ratio)

        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx if best_score >= 0.25 else None


def _match_multiline_section(
    ocr_lines: List[Dict[str, Any]],
    target: str,
    section_name: str,
) -> List[List[int]]:
    """
    Matches a multi-line target string against OCR lines and merges adjacent matching lines.
    Returns merged bounding box [x1, y1, x2, y2].
    """
    target_norm = normalize_text(target)
    if not target_norm or not ocr_lines:
        return []

    target_words = set(target_norm.split())
    barriers = SECTION_BARRIERS.get(section_name, [])

    candidates: List[Tuple[int, float]] = []

    for i, line in enumerate(ocr_lines):
        line_raw = str(line.get("text", "")).strip()
        line_norm = normalize_text(line_raw)
        if not line_norm:
            continue

        # Check section barriers
        line_lower = line_raw.lower()
        if any(line_lower.startswith(b) for b in barriers):
            continue

        line_words = set(line_norm.split())
        overlap = line_words & target_words

        sm = SequenceMatcher(None, line_norm, target_norm)
        longest = sm.find_longest_match(0, len(line_norm), 0, len(target_norm))
        overlap_ratio = len(overlap) / max(len(line_words), 1)

        # Candidate if good match block, majority words overlap, or line is contained in target
        if longest.size >= 8 or overlap_ratio >= 0.40 or (len(overlap) >= 1 and line_norm in target_norm):
            score = float(longest.size + len(overlap) * 5)
            candidates.append((i, score))

    if not candidates:
        # Fallback to single best line
        single_idx = _match_single_line(ocr_lines, target)
        if single_idx is not None:
            return ocr_lines[single_idx]["bbox"]
        return []

    # Sort candidates by score descending to find primary anchor line
    candidates.sort(key=lambda x: x[1], reverse=True)
    seed_idx = candidates[0][0]
    cand_indices = set(x[0] for x in candidates)

    # Merge contiguous/adjacent candidate lines around seed
    matched_indices: Set[int] = {seed_idx}

    # Expand backwards
    cur = seed_idx - 1
    while cur >= 0 and cur in cand_indices:
        matched_indices.add(cur)
        cur -= 1

    # Expand forwards
    cur = seed_idx + 1
    while cur < len(ocr_lines) and cur in cand_indices:
        matched_indices.add(cur)
        cur += 1

    boxes_to_merge = [ocr_lines[idx]["bbox"] for idx in sorted(matched_indices)]
    return merge_bboxes(boxes_to_merge)


def locate_evidence(
    ocr_lines: List[Dict[str, Any]],
    finding: Dict[str, Any],
    image_size: Tuple[int, int],
) -> List[Dict[str, Any]]:
    """
    Locates evidence annotations for a given rule finding on a packaging image.

    Args:
        ocr_lines: List of OCR line dictionaries:
                   [{"text": str, "bbox": [x1, y1, x2, y2], "confidence": float}, ...]
        finding: Compliance finding dictionary:
                 {"rule_id": str, "verdict": str, "found": Any, "expected": Any, "reason": str}
        image_size: Tuple of (width, height) in pixels.

    Returns:
        List of evidence dictionaries:
        [{"bbox": [x1, y1, x2, y2], "kind": "found" | "missing", "label": str}, ...]
    """
    rule_id = finding.get("rule_id", "")
    verdict = finding.get("verdict", "")
    found = finding.get("found", "")
    reason = finding.get("reason", "")
    expected = finding.get("expected", "")

    # Rule metadata
    meta = RULE_INFO.get(rule_id, {"name": rule_id, "clause": "VERIFY", "section": ""})
    rule_name = meta["name"]
    clause = meta["clause"]

    # Base metadata attached to each returned evidence box
    def make_box_item(
        bbox: List[int],
        kind: str,
        label: str,
        f_val: Any = found,
        e_val: Any = expected,
    ) -> Dict[str, Any]:
        return {
            "bbox": [int(x) for x in bbox],
            "kind": kind,
            "label": label,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "verdict": verdict,
            "found": str(f_val if f_val is not None else "(None)"),
            "expected": str(e_val if e_val is not None else "(None)"),
            "reason": reason,
            "fssai_clause": clause,
        }

    # 1. Not applicable rules generate no image annotations
    if verdict == "N/A":
        return []

    # 2. Rule R04 (Vegetarian mark) - visual logo without OCR text
    if rule_id == "R04":
        if verdict == "FAIL" or is_absent_value(found):
            return [make_box_item(
                bbox=get_info_panel_bbox(ocr_lines, image_size),
                kind="missing",
                label="Vegetarian mark not found",
            )]
        # Passing R04 has no OCR text line
        return []

    # 3. Rule R10 (MRP and Best-Before) - two separate mandatory statements
    if rule_id == "R10":
        results: List[Dict[str, Any]] = []
        found_str = str(found or "")

        # Extract MRP and Best-Before values from found string
        mrp_m = re.search(r"MRP:\s*'([^']*)'", found_str)
        bb_m = re.search(r"Best Before:\s*'([^']*)'", found_str)
        mrp_val = mrp_m.group(1).strip() if mrp_m else ""
        bb_val = bb_m.group(1).strip() if bb_m else ""

        # If both are absent or failure indicates both missing
        if not mrp_val and not bb_val:
            return [make_box_item(
                bbox=get_info_panel_bbox(ocr_lines, image_size),
                kind="missing",
                label="MRP and best-before not found",
            )]

        # Locate MRP
        if mrp_val:
            # Fuzzy match to MRP line or price digits
            mrp_idx = _match_single_line(ocr_lines, mrp_val)
            if mrp_idx is not None:
                # If there is a horizontally adjacent line with 'MRP' or 'Rs', merge it
                mrp_bbox = ocr_lines[mrp_idx]["bbox"]
                adjacent_mrp_boxes = [mrp_bbox]
                m_y1, m_y2 = mrp_bbox[1], mrp_bbox[3]
                for j, line in enumerate(ocr_lines):
                    if j != mrp_idx:
                        ly1, ly2 = line["bbox"][1], line["bbox"][3]
                        # Same vertical line level
                        if abs(ly1 - m_y1) < 15 and abs(ly2 - m_y2) < 15:
                            if any(k in line.get("text", "").lower() for k in ["mrp", "rs", "₹"]):
                                adjacent_mrp_boxes.append(line["bbox"])
                results.append(make_box_item(
                    bbox=merge_bboxes(adjacent_mrp_boxes),
                    kind="found",
                    label=f"MRP: {mrp_val}",
                    f_val=mrp_val,
                ))
        elif verdict == "FAIL":
            results.append(make_box_item(
                bbox=get_info_panel_bbox(ocr_lines, image_size),
                kind="missing",
                label="MRP declaration not found",
            ))

        # Locate Best Before
        if bb_val:
            bb_idx = _match_single_line(ocr_lines, bb_val)
            if bb_idx is not None:
                results.append(make_box_item(
                    bbox=ocr_lines[bb_idx]["bbox"],
                    kind="found",
                    label=f"Best before: {bb_val}",
                    f_val=bb_val,
                ))
        elif verdict == "FAIL":
            results.append(make_box_item(
                bbox=get_info_panel_bbox(ocr_lines, image_size),
                kind="missing",
                label="Best before declaration not found",
            ))

        if results:
            return results

    # 4. Absent field check (FAIL because missing value)
    if verdict == "FAIL" and is_absent_value(found):
        missing_labels = {
            "R01": "Net quantity statement not found",
            "R05": "Allergen section not found",
            "R07": "Ingredients section not found",
            "R08": "Manufacturer details not found",
            "R09": "FSSAI number not found",
        }
        label = missing_labels.get(rule_id, f"{rule_name} not found")
        return [make_box_item(
            bbox=get_info_panel_bbox(ocr_lines, image_size),
            kind="missing",
            label=label,
        )]

    # 5. Field has a found value: Locate via fuzzy match
    target_str = str(found or "").strip()
    if not target_str or target_str.lower() in ["none", "absent", "(none)"]:
        if verdict == "FAIL":
            return [make_box_item(
                bbox=get_info_panel_bbox(ocr_lines, image_size),
                kind="missing",
                label=f"{rule_name} not found",
            )]
        return []

    # Multi-line fields: ingredients, allergens, manufacturer
    if rule_id in MULTILINE_RULES:
        sec = meta.get("section", "ingredients")
        merged_box = _match_multiline_section(ocr_lines, target_str, sec)
        if merged_box and any(merged_box):
            multiline_labels = {
                "R05": "Allergen statement",
                "R06": "Allergen declaration",
                "R07": "Ingredients list",
                "R08": "Manufacturer details",
            }
            label = multiline_labels.get(rule_id, rule_name)
            return [make_box_item(
                bbox=merged_box,
                kind="found",
                label=label,
            )]

    # Single-line fields: R01, R02, R03, R09, etc.
    line_idx = _match_single_line(ocr_lines, target_str)
    if line_idx is not None:
        single_labels = {
            "R01": f"Net quantity: {target_str}",
            "R02": f"Net quantity: {target_str}",
            "R03": f"Net quantity unit: {target_str}",
            "R09": f"FSSAI license: {target_str}",
        }
        label = single_labels.get(rule_id, f"{rule_name}: {target_str}")
        return [make_box_item(
            bbox=ocr_lines[line_idx]["bbox"],
            kind="found",
            label=label,
        )]

    # Fallback if no matching OCR line found
    if verdict == "FAIL":
        return [make_box_item(
            bbox=get_info_panel_bbox(ocr_lines, image_size),
            kind="missing",
            label=f"{rule_name} (evidence region)",
        )]

    return []

"""
ocr_diagnose.py
Diagnoses OCR misses on dev-set packaging images for net_quantity and mrp.

Identifies every dev-set image where ocr_check.py misses net_quantity or mrp
(ignoring fields deliberately removed):
- Finds the 3 OCR lines most similar to the expected string using difflib.SequenceMatcher.
- Outputs the image name, field, expected string, and top 3 candidate OCR lines with confidence.
- Saves the full diagnosis output to outputs/ocr_misses.txt.
- Prints a summary count of misses per product.

Constraints: standard library + existing modules only.
"""

import difflib
import json
import os
from typing import Any, Dict, List, Tuple

from extract_ocr import extract_text
from ocr_check import normalize_text

SPLIT_PATH = os.path.join("dataset", "split.json")
ANSWER_KEY_PATH = os.path.join("dataset", "answer_key.json")
IMAGES_DIR = os.path.join("dataset", "images")
OUTPUT_PATH = os.path.join("outputs", "ocr_misses.txt")

# Target fields to diagnose as specified in requirements
TARGET_FIELDS = ["net_quantity", "mrp"]


def get_top_similar_lines(
    expected_str: str,
    ocr_items: List[Dict[str, Any]],
    top_k: int = 3,
) -> List[Tuple[str, float, float]]:
    """
    Finds the top_k OCR lines most similar to expected_str using difflib.SequenceMatcher.

    In Python, difflib.SequenceMatcher uses Ratcliff-Obershelp (longest common contiguity),
    yielding a similarity ratio in [0.0, 1.0]. This is analogous to edit-distance / LCS
    algorithms in DSA / C++.

    Args:
        expected_str: Ground-truth target string (e.g. "Rs. 40.00" or "200 g").
        ocr_items: List of detected OCR dicts, each containing 'text' and 'confidence'.
        top_k: Number of highest-similarity lines to return (default 3).

    Returns:
        List of tuples: (ocr_line_text, confidence, similarity_ratio) sorted descending.
    """
    scored_lines: List[Tuple[str, float, float]] = []

    for item in ocr_items:
        text = str(item.get("text", ""))
        confidence = float(item.get("confidence", 0.0))
        # SequenceMatcher compares the two strings; None specifies no junk-filter function
        similarity = difflib.SequenceMatcher(None, expected_str, text).ratio()
        scored_lines.append((text, confidence, similarity))

    # In Python, sorted() with key=lambda x: ... works like std::sort in C++ with a custom comparator.
    # We sort primarily by similarity descending, breaking ties by confidence descending.
    scored_lines.sort(key=lambda x: (x[2], x[1]), reverse=True)

    # Slice the top k items (in Python, [:k] safely takes up to k elements without index errors)
    return scored_lines[:top_k]


def run_ocr_diagnosis() -> Dict[str, Any]:
    """
    Evaluates all dev set images, diagnoses misses for net_quantity and mrp,
    writes the report to outputs/ocr_misses.txt, and prints results to console.
    """
    # Ensure dataset files exist
    if not os.path.exists(SPLIT_PATH):
        raise FileNotFoundError(f"Split file missing at: {SPLIT_PATH}")
    if not os.path.exists(ANSWER_KEY_PATH):
        raise FileNotFoundError(f"Answer key missing at: {ANSWER_KEY_PATH}")

    with open(SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    with open(ANSWER_KEY_PATH, "r", encoding="utf-8") as f:
        answer_key = json.load(f)

    dev_images = split_data.get("dev", [])

    # Ensure output directory exists (like std::filesystem::create_directories in C++)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Track miss counts per product for all products present in dev set
    misses_per_product: Dict[str, int] = {}
    for img_name in dev_images:
        entry = answer_key.get(img_name, {})
        prod = entry.get("product", "unknown")
        if prod not in misses_per_product:
            misses_per_product[prod] = 0

    miss_reports: List[str] = []
    total_misses = 0

    header = "OCR MISS DIAGNOSIS REPORT (Dev Set: net_quantity & mrp)"
    separator = "=" * 70
    miss_reports.append(separator)
    miss_reports.append(header)
    miss_reports.append(separator)

    print(f"\nRunning OCR diagnosis on {len(dev_images)} dev-set images...")

    for img_name in dev_images:
        img_path = os.path.join(IMAGES_DIR, img_name)
        if not os.path.exists(img_path):
            print(f"[WARNING] Image missing: {img_path}")
            continue

        entry = answer_key.get(img_name, {})
        product = entry.get("product", "unknown")
        fields = entry.get("fields", {})

        # Run OCR extraction on the packaging image
        ocr_items = extract_text(img_path)
        # Replicate ocr_check.py joining & normalization logic
        joined_ocr = " ".join(item["text"] for item in ocr_items)
        norm_ocr = normalize_text(joined_ocr)

        for field in TARGET_FIELDS:
            expected_val = fields.get(field, "")

            # Skip images where this field was deliberately removed (empty or whitespace-only)
            if not expected_val or not str(expected_val).strip():
                continue

            expected_str = str(expected_val)
            norm_expected = normalize_text(expected_str)

            # Check if ocr_check missed this field
            if norm_expected not in norm_ocr:
                # Miss detected!
                total_misses += 1
                misses_per_product[product] = misses_per_product.get(product, 0) + 1

                # Find top 3 OCR lines most similar to expected string
                top_3 = get_top_similar_lines(expected_str, ocr_items, top_k=3)

                # Format diagnosis block
                lines_block = [
                    f"\nImage: {img_name}",
                    f"Product: {product}",
                    f"Field: {field}",
                    f"Expected: {expected_str}",
                    "Top 3 Similar OCR Lines (difflib.SequenceMatcher):",
                ]

                if not top_3:
                    lines_block.append("  (No OCR text detected on image)")
                else:
                    for rank, (line_text, conf, sim) in enumerate(top_3, 1):
                        lines_block.append(
                            f'  {rank}. "{line_text}" '
                            f"(similarity: {sim:.3f}, confidence: {conf:.3f})"
                        )

                block_str = "\n".join(lines_block)
                miss_reports.append(block_str)
                # Print each miss diagnosis to console
                print(block_str)

    # Format summary table
    summary_lines = [
        "\n" + separator,
        "SUMMARY: Misses Per Product",
        separator,
        f"{'Product':<20} {'Misses':<10}",
        "-" * 70,
    ]
    for prod in sorted(misses_per_product.keys()):
        summary_lines.append(f"{prod:<20} {misses_per_product[prod]:<10}")
    summary_lines.append("-" * 70)
    summary_lines.append(f"{'Total Misses':<20} {total_misses:<10}")
    summary_lines.append(separator + "\n")

    summary_str = "\n".join(summary_lines)
    miss_reports.append(summary_str)

    # Save complete report to outputs/ocr_misses.txt
    full_output = "\n".join(miss_reports)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_output)

    # Print summary to console
    print(summary_str)
    print(f"Report saved to: {OUTPUT_PATH}\n")

    return {
        "total_misses": total_misses,
        "misses_per_product": misses_per_product,
        "output_path": OUTPUT_PATH,
    }


if __name__ == "__main__":
    run_ocr_diagnosis()

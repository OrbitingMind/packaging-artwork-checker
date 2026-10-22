"""
ocr_check.py
Evaluates EasyOCR performance across the dev split dataset against ground-truth values.

For every image in the dev set (from dataset/split.json):
- Extracts text via extract_ocr.extract_text()
- Joins all detected text fragments
- Checks whether net_quantity, fssai_license, and mrp from answer_key.json appear
  in joined text (ignoring case and whitespace)
- Skips images where a field was deliberately removed (empty string in answer_key.json)
- Computes and prints hit rates per field and per product
"""

import json
import os
from typing import Dict
from extract_ocr import extract_text

SPLIT_PATH = os.path.join("dataset", "split.json")
ANSWER_KEY_PATH = os.path.join("dataset", "answer_key.json")
IMAGES_DIR = os.path.join("dataset", "images")
TARGET_FIELDS = ["net_quantity", "fssai_license", "mrp"]


def normalize_text(text: str) -> str:
    """
    Normalizes text by removing all whitespace and converting to lowercase.
    Allows exact substring search that ignores spacing and case differences.
    """
    return "".join(text.split()).lower()


def run_ocr_check() -> Dict[str, Dict[str, int]]:
    # Load dataset split and ground-truth answer key
    with open(SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    with open(ANSWER_KEY_PATH, "r", encoding="utf-8") as f:
        answer_key = json.load(f)

    dev_images = split_data.get("dev", [])
    print(f"Evaluating OCR on {len(dev_images)} dev set images...")

    field_stats = {f: {"hits": 0, "total": 0} for f in TARGET_FIELDS}
    product_stats = {}

    for idx, img_name in enumerate(dev_images, 1):
        img_path = os.path.join(IMAGES_DIR, img_name)
        if not os.path.exists(img_path):
            print(f"[WARNING] Image missing: {img_path}")
            continue

        entry = answer_key.get(img_name, {})
        product = entry.get("product", "unknown")
        fields = entry.get("fields", {})

        if product not in product_stats:
            product_stats[product] = {"hits": 0, "total": 0}

        # Run OCR extraction and join all detected text segments
        ocr_items = extract_text(img_path)
        joined_ocr = " ".join(item["text"] for item in ocr_items)
        norm_ocr = normalize_text(joined_ocr)

        # Evaluate each targeted field
        for field in TARGET_FIELDS:
            expected_val = fields.get(field, "")

            # Skip images where this field was deliberately removed (empty or missing)
            if not expected_val or not str(expected_val).strip():
                continue

            field_stats[field]["total"] += 1
            product_stats[product]["total"] += 1

            norm_expected = normalize_text(str(expected_val))
            if norm_expected in norm_ocr:
                field_stats[field]["hits"] += 1
                product_stats[product]["hits"] += 1

    # Print summary reports
    print("\n" + "=" * 50)
    print("OCR Hit Rate Per Field (Dev Set)")
    print("=" * 50)
    print(f"{'Field':<20} {'Hits / Total':<15} {'Hit Rate':<10}")
    print("-" * 50)
    total_hits = 0
    total_evals = 0
    for field in TARGET_FIELDS:
        hits = field_stats[field]["hits"]
        tot = field_stats[field]["total"]
        rate = (hits / tot * 100) if tot > 0 else 0.0
        total_hits += hits
        total_evals += tot
        print(f"{field:<20} {f'{hits} / {tot}':<15} {rate:>5.1f}%")
    print("-" * 50)
    overall_rate = (total_hits / total_evals * 100) if total_evals > 0 else 0.0
    print(f"{'Overall':<20} {f'{total_hits} / {total_evals}':<15} {overall_rate:>5.1f}%\n")

    print("=" * 50)
    print("OCR Hit Rate Per Product (Dev Set)")
    print("=" * 50)
    print(f"{'Product':<20} {'Hits / Total':<15} {'Hit Rate':<10}")
    print("-" * 50)
    for prod in sorted(product_stats.keys()):
        hits = product_stats[prod]["hits"]
        tot = product_stats[prod]["total"]
        rate = (hits / tot * 100) if tot > 0 else 0.0
        print(f"{prod:<20} {f'{hits} / {tot}':<15} {rate:>5.1f}%")
    print("=" * 50 + "\n")

    return {"fields": field_stats, "products": product_stats}


if __name__ == "__main__":
    run_ocr_check()

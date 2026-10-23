"""
precompute_cache.py
Precomputes and caches OCR lines and evidence boxes in outputs/cache/
for curated sample images so the Streamlit demo remains instant without API calls.
"""

import json
import os
from typing import Dict, Tuple
from PIL import Image

from checks import check_rules
from extract_ocr import extract_text
from locate import locate_evidence

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "outputs", "cache")
IMAGES_DIR = os.path.join(BASE_DIR, "dataset", "images")
SPECS_DIR = os.path.join(BASE_DIR, "dataset", "specs")

# Curated sample artworks mapped to their specifications
CURATED_SAMPLES = [
    ("biscuit_clean1.png", "biscuit.json"),
    ("biscuit_clean2.png", "biscuit.json"),
    ("biscuit_errR02.png", "biscuit.json"),
    ("biscuit_errR05.png", "biscuit.json"),
    ("biscuit_errR07.png", "biscuit.json"),
    ("chips_clean1.png", "chips.json"),
    ("chips_clean2.png", "chips.json"),
    ("chips_errR01.png", "chips.json"),
    ("juice_clean1.png", "juice.json"),
    ("juice_clean2.png", "juice.json"),
    ("juice_errR04.png", "juice.json"),
    ("masala_clean1.png", "masala.json"),
    ("masala_clean2.png", "masala.json"),
    ("masala_errR03.png", "masala.json"),
    ("salt_clean1.png", "salt.json"),
    ("salt_clean2.png", "salt.json"),
]


def precompute():
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Precomputing OCR and evidence caches for {len(CURATED_SAMPLES)} sample artworks...")

    for img_file, spec_file in CURATED_SAMPLES:
        img_path = os.path.join(IMAGES_DIR, img_file)
        spec_path = os.path.join(SPECS_DIR, spec_file)
        base_name = os.path.splitext(img_file)[0]

        if not os.path.exists(img_path):
            print(f"  [SKIP] Image not found: {img_path}")
            continue

        print(f"  Processing {img_file} ...")
        # 1. OCR Lines
        ocr_cache_path = os.path.join(CACHE_DIR, f"{base_name}_ocr.json")
        if os.path.exists(ocr_cache_path):
            with open(ocr_cache_path, "r", encoding="utf-8") as f:
                ocr_lines = json.load(f)
        else:
            ocr_lines = extract_text(img_path)
            with open(ocr_cache_path, "w", encoding="utf-8") as f:
                json.dump(ocr_lines, f, indent=2)

        # 2. Get extracted fields from cache or run checks
        field_cache_path = os.path.join(CACHE_DIR, f"{base_name}.json")
        if not os.path.exists(field_cache_path):
            print(f"  [WARN] Field extraction cache missing for {base_name}.json")
            continue

        with open(field_cache_path, "r", encoding="utf-8") as f:
            extracted = json.load(f)
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        findings = check_rules(extracted, spec)

        # 3. Evidence Boxes
        with Image.open(img_path) as img:
            image_size = img.size

        all_boxes = []
        for finding in findings:
            boxes = locate_evidence(ocr_lines, finding, image_size)
            all_boxes.extend(boxes)

        evidence_cache_path = os.path.join(CACHE_DIR, f"{base_name}_evidence.json")
        with open(evidence_cache_path, "w", encoding="utf-8") as f:
            json.dump(all_boxes, f, indent=2)

        print(f"    Saved: {len(ocr_lines)} OCR lines, {len(all_boxes)} evidence boxes.")

    print("Precomputation complete!")


if __name__ == "__main__":
    precompute()

"""
ocr_demo.py
Demonstrates OCR extraction and bounding box visualization on sample packaging images.

Runs on:
- dataset/images/biscuit_clean1.png
- dataset/images/masala_clean1.png
- dataset/images/chips_clean1.png

Draws bounding boxes around detected text and saves outputs to outputs/ocr_demo/.
"""

import os
from PIL import Image, ImageDraw
from extract_ocr import extract_text

# Target demo images specified in task
DEMO_IMAGES = [
    os.path.join("dataset", "images", "biscuit_clean1.png"),
    os.path.join("dataset", "images", "masala_clean1.png"),
    os.path.join("dataset", "images", "chips_clean1.png"),
]

OUTPUT_DIR = os.path.join("outputs", "ocr_demo")


def run_demo():
    # Ensure destination directory exists (similar to std::filesystem::create_directories)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== Running OCR Demo ===")
    for img_path in DEMO_IMAGES:
        if not os.path.exists(img_path):
            print(f"[WARNING] Image file not found: {img_path}")
            continue

        filename = os.path.basename(img_path)
        print(f"Processing: {filename} ...")

        # 1. Run OCR extraction
        ocr_results = extract_text(img_path)
        print(f"  Detected {len(ocr_results)} text regions.")

        # 2. Open image and draw bounding boxes using Pillow
        with Image.open(img_path) as img:
            annotated = img.copy()
            draw = ImageDraw.Draw(annotated)

            for item in ocr_results:
                bbox = item["bbox"]  # [x1, y1, x2, y2]
                # Draw red bounding rectangle around detected text
                draw.rectangle(bbox, outline="red", width=3)

            # 3. Save annotated image to outputs/ocr_demo/
            out_path = os.path.join(OUTPUT_DIR, filename)
            annotated.save(out_path)
            print(f"  Saved visual demo to: {out_path}")

    print("\nOCR demo finished successfully.")


if __name__ == "__main__":
    run_demo()

"""
extract_ocr.py
Extracts text and bounding boxes from packaging images using EasyOCR.

Constraints: EasyOCR, Pillow and the standard library only.
"""

import os
from typing import Any, Dict, List
import easyocr

# Create the EasyOCR reader once at module load (reused across calls).
# English language, CPU-only execution as required.
# verbose=False suppresses download progress bars that can fail on Windows consoles.
READER = easyocr.Reader(["en"], gpu=False, verbose=False)


def extract_text(image_path: str) -> List[Dict[str, Any]]:
    """
    Extract text elements and their bounding boxes from an image file.

    Args:
        image_path: Filesystem path to the packaging image.

    Returns:
        List of dictionaries with format:
        {
            "text": str,
            "bbox": [x1, y1, x2, y2],
            "confidence": float (0.0 to 1.0)
        }
    """
    # os.fspath converts str or PathLike to a standard string/bytes path
    path_str = os.fspath(image_path)
    if not os.path.isfile(path_str):
        raise FileNotFoundError(f"Image not found at: {path_str}")

    # reader.readtext returns a list of tuples: (polygon_pts, text, confidence)
    # where polygon_pts is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    raw_results = READER.readtext(path_str)

    extracted = []
    for polygon, text, confidence in raw_results:
        # Convert polygon points to axis-aligned bounding box [x1, y1, x2, y2]
        # In Python, list comprehensions provide concise mapping similar to std::transform in C++
        xs = [int(round(pt[0])) for pt in polygon]
        ys = [int(round(pt[1])) for pt in polygon]

        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)

        extracted.append({
            "text": str(text),
            "bbox": [x1, y1, x2, y2],
            "confidence": float(confidence),
        })

    return extracted

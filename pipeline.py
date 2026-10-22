"""
Pipeline module combining vision extraction and packaging compliance checks with local disk caching.
"""

import json
import os
from typing import Any, Dict, List, Union
from checks import check_rules
from extract_vision import extract_fields

CACHE_DIR = os.path.join("outputs", "cache")


def check_image(image_path: str, spec_path: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs vision extraction and compliance checks on packaging image against approved spec.
    Caches extraction results per image in outputs/cache/ so reruns cost nothing.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    # Ensure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    cache_path = os.path.join(CACHE_DIR, f"{base_name}.json")

    # Load from cache if available, otherwise extract and cache
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            extracted = json.load(f)
    else:
        extracted = extract_fields(image_path)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2)

    # Load specification
    if isinstance(spec_path, dict):
        spec = spec_path
    else:
        resolved_spec_path = spec_path
        if not os.path.isabs(spec_path) and not os.path.exists(spec_path):
            fallback_spec = os.path.join(os.path.dirname(os.path.abspath(__file__)), spec_path)
            if os.path.exists(fallback_spec):
                resolved_spec_path = fallback_spec

        if not os.path.exists(resolved_spec_path):
            raise FileNotFoundError(f"Spec file not found at: {spec_path}")

        with open(resolved_spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

    # Evaluate compliance rules
    return check_rules(extracted, spec)

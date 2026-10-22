"""
Vision extraction module using Anthropic Claude to extract label fields from packaging artwork.
"""

import base64
import json
import os
import anthropic
from dotenv import load_dotenv

MODEL = "claude-sonnet-5-5"

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Fallback to Streamlit secrets if running in Streamlit Cloud
if not api_key:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

TEXT_FIELDS = [
    "product_name",
    "net_quantity",
    "ingredients",
    "allergen_statement",
    "manufacturer",
    "fssai_license",
    "mrp",
    "best_before",
]

PROMPT = """You are an automated packaging artwork inspection assistant.
transcribe EXACTLY what is printed, do not correct or guess, return "" if absent.

Extract the following packaging fields from the label image:
- product_name: The declared product title/name
- net_quantity: The declared net quantity with unit (e.g. "200 g")
- veg_mark_present: Boolean true if green square border with green filled circle is present, false otherwise
- ingredients: The full ingredients list text
- allergen_statement: The allergen declaration text (e.g. "Contains wheat...")
- manufacturer: The manufacturer name and postal address
- fssai_license: The 14-digit FSSAI license number
- mrp: Maximum retail price text (e.g. "Rs. 40.00")
- best_before: Best before or expiry statement text

Return ONLY valid JSON matching this schema:
{
  "product_name": {"value": str, "confidence": float 0-1},
  "net_quantity": {"value": str, "confidence": float 0-1},
  "veg_mark_present": bool,
  "ingredients": {"value": str, "confidence": float 0-1},
  "allergen_statement": {"value": str, "confidence": float 0-1},
  "manufacturer": {"value": str, "confidence": float 0-1},
  "fssai_license": {"value": str, "confidence": float 0-1},
  "mrp": {"value": str, "confidence": float 0-1},
  "best_before": {"value": str, "confidence": float 0-1}
}
Do not include section headings in value (e.g. omit 'Net Qty:', 'FSSAI Lic. No.:', 'MRP:').
"""


def _clean_json_str(text: str) -> str:
    """Removes markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _normalize_extracted(data: dict) -> dict:
    """Ensures expected types and keys for all fields."""
    normalized = {}

    # Normalize veg_mark_present to bool
    raw_veg = data.get("veg_mark_present", False)
    if isinstance(raw_veg, dict):
        normalized["veg_mark_present"] = bool(raw_veg.get("value", False))
    elif isinstance(raw_veg, str):
        normalized["veg_mark_present"] = raw_veg.strip().lower() in ("true", "1", "yes")
    else:
        normalized["veg_mark_present"] = bool(raw_veg)

    # Normalize text fields to {"value": str, "confidence": float}
    for field in TEXT_FIELDS:
        val_entry = data.get(field, {"value": "", "confidence": 0.0})
        if isinstance(val_entry, dict):
            val = str(val_entry.get("value", "") or "").strip()
            conf = float(val_entry.get("confidence", 1.0) if val_entry.get("confidence") is not None else 1.0)
        else:
            val = str(val_entry or "").strip()
            conf = 1.0 if val else 0.0
        normalized[field] = {"value": val, "confidence": conf}

    return normalized


def extract_fields(image_path: str) -> dict:
    """
    Sends the image to Anthropic API (MODEL = claude-sonnet-5-5) and extracts packaging fields.
    Retries once on bad JSON. Does not send the spec to the model.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Determine media type from extension
    ext = os.path.splitext(image_path)[1].lower()
    media_type = "image/png"
    if ext in (".jpg", ".jpeg"):
        media_type = "image/jpeg"
    elif ext == ".webp":
        media_type = "image/webp"

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    active_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not active_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
                active_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass

    client = anthropic.Anthropic(api_key=active_key)

    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_b64,
                },
            },
            {"type": "text", "text": PROMPT},
        ],
    }]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages,
    )

    raw_text = next((b.text for b in response.content if hasattr(b, "text")), "")
    try:
        data = json.loads(_clean_json_str(raw_text))
    except (json.JSONDecodeError, ValueError):
        # Retry once on bad JSON
        retry_messages = list(messages)
        retry_messages.append({"role": "assistant", "content": raw_text})
        retry_messages.append({
            "role": "user",
            "content": "Your response was not valid JSON. Return ONLY the raw valid JSON matching the schema.",
        })
        retry_response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=retry_messages,
        )
        retry_text = next((b.text for b in retry_response.content if hasattr(b, "text")), "")
        data = json.loads(_clean_json_str(retry_text))

    return _normalize_extracted(data)

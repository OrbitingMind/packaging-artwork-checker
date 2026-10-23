"""
app.py - ArtGuard Streamlit Web Application
Esko Hackathon (Track 2) - Team: PixelProof
AI-Powered Packaging Artwork Compliance Checker for FSSAI Regulations
"""

import json
import os
import tempfile
from typing import Any, Dict, List, Tuple
from PIL import Image
import streamlit as st

from annotated_view import render_annotated_image
from locate import locate_evidence
from pipeline import check_image
from rules_loader import load_rules

# Page Configuration
st.set_page_config(
    page_title="ArtGuard | Packaging Artwork Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished enterprise presentation
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-pixelproof {
        background-color: #EEF2FF;
        color: #4F46E5;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
    }
    .pass-badge {
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .fail-badge {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .review-badge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .na-badge {
        background-color: #F1F5F9;
        color: #475569;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "dataset", "images")
SPECS_DIR = os.path.join(BASE_DIR, "dataset", "specs")
CACHE_DIR = os.path.join(BASE_DIR, "outputs", "cache")


def get_cached_ocr_lines(img_path: str) -> List[Dict[str, Any]]:
    """Loads OCR lines from cache or extracts via EasyOCR once."""
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    cache_path = os.path.join(CACHE_DIR, f"{base_name}_ocr.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    from extract_ocr import extract_text
    lines = extract_text(img_path)
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(lines, f, indent=2)
    except Exception:
        pass
    return lines


def get_cached_evidence_boxes(
    img_path: str,
    findings: List[Dict[str, Any]],
    img_size: Tuple[int, int],
) -> List[Dict[str, Any]]:
    """Loads evidence boxes from cache or computes via locate_evidence."""
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    cache_path = os.path.join(CACHE_DIR, f"{base_name}_evidence.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    ocr_lines = get_cached_ocr_lines(img_path)
    boxes = []
    for f in findings:
        boxes.extend(locate_evidence(ocr_lines, f, img_size))
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(boxes, f, indent=2)
    except Exception:
        pass
    return boxes


@st.cache_data
def get_rules_map() -> Dict[str, str]:
    """Loads rules and returns map of rule_id -> rule_name."""
    try:
        rules = load_rules()
        return {r["id"]: r["name"] for r in rules}
    except Exception:
        return {}


rules_map = get_rules_map()

# Curated sample artworks demonstrating compliance and key defect categories
SAMPLE_OPTIONS = {
    "Biscuit Clean 1 (Fully Compliant)": {
        "file": "biscuit_clean1.png",
        "spec": "biscuit.json",
        "desc": "Compliant packaging meeting all FSSAI labelling standards.",
    },
    "Biscuit Error R02 (Wrong Net Quantity)": {
        "file": "biscuit_errR02.png",
        "spec": "biscuit.json",
        "desc": "Violates R02: Declared net quantity (20 g) does not match specification (200 g).",
    },
    "Biscuit Error R05 (Missing Allergen Box)": {
        "file": "biscuit_errR05.png",
        "spec": "biscuit.json",
        "desc": "Violates R05: Contains wheat/oats but allergen disclosure is absent.",
    },
    "Biscuit Error R07 (Missing Oats in Ingredients)": {
        "file": "biscuit_errR07.png",
        "spec": "biscuit.json",
        "desc": "Violates R07: 'oats' omitted from declared ingredients.",
    },
    "Chips Error R01 (Missing Net Quantity)": {
        "file": "chips_errR01.png",
        "spec": "chips.json",
        "desc": "Violates R01: Net quantity missing; R02 and R03 gracefully return N/A.",
    },
    "Juice Error R04 (Missing Veg Logo)": {
        "file": "juice_errR04.png",
        "spec": "juice.json",
        "desc": "Violates R04: Green vegetarian square/circle symbol is absent.",
    },
    "Masala Error R03 (Illegal Metrology Unit)": {
        "file": "masala_errR03.png",
        "spec": "masala.json",
        "desc": "Violates R03: Unapproved net quantity symbol used.",
    },
    "Salt Clean 1 (Clean Salt - Allergens N/A)": {
        "file": "salt_clean1.png",
        "spec": "salt.json",
        "desc": "Compliant salt: R05 and R06 correctly evaluate to N/A.",
    },
}

# Sidebar - Configuration & Inputs
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg",
        width=40,
    )
    st.markdown("### **ArtGuard Configuration**")
    st.markdown("Team **PixelProof** | Track 2: Packaging Artwork Verification")
    st.divider()

    input_mode = st.radio(
        "Choose Artwork Source:",
        ["Curated Sample Artwork", "Upload Artwork Image"],
    )

    image_path = None
    spec_path = None
    selected_spec_file = "biscuit.json"

    if input_mode == "Curated Sample Artwork":
        chosen_sample_label = st.selectbox(
            "Select Sample Artwork:",
            list(SAMPLE_OPTIONS.keys()),
        )
        sample_meta = SAMPLE_OPTIONS[chosen_sample_label]
        image_path = os.path.join(IMAGES_DIR, sample_meta["file"])
        selected_spec_file = sample_meta["spec"]
        spec_path = os.path.join(SPECS_DIR, selected_spec_file)
        st.info(f"**Scenario:** {sample_meta['desc']}")

    else:
        uploaded_file = st.file_uploader(
            "Upload Packaging Artwork (PNG, JPG, WEBP):",
            type=["png", "jpg", "jpeg", "webp"],
        )
        if uploaded_file is not None:
            # Cache uploaded image in session state to avoid re-writing temp file on every interaction
            file_key = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
            if file_key not in st.session_state or not os.path.exists(st.session_state[file_key]):
                suffix = os.path.splitext(uploaded_file.name)[1]
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tfile.write(uploaded_file.getvalue())
                tfile.close()
                st.session_state[file_key] = tfile.name
            image_path = st.session_state[file_key]

        # Spec selector for uploaded images
        available_specs = [f for f in os.listdir(SPECS_DIR) if f.endswith(".json")] if os.path.exists(SPECS_DIR) else []
        selected_spec_file = st.selectbox(
            "Select Approved Product Specification:",
            available_specs,
            index=0 if available_specs else 0,
        )
        if selected_spec_file:
            spec_path = os.path.join(SPECS_DIR, selected_spec_file)

    st.divider()
    run_btn = st.button("🚀 Run Compliance Audit", type="primary", use_container_width=True)

# Main Application Area
st.markdown('<div class="badge-pixelproof">Esko Hackathon Track 2 &bull; Team PixelProof</div>', unsafe_allow_html=True)
st.markdown('<div class="main-header">ArtGuard: AI Packaging Compliance Checker</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated regulatory verification against 10 FSSAI labelling rules with deterministic evidence.</div>',
    unsafe_allow_html=True,
)

# Run audit or retrieve cached results
should_audit = bool(run_btn or ("last_run" in st.session_state and st.session_state["last_run"] == image_path))
findings: List[Dict[str, Any]] = []
evidence_boxes: List[Dict[str, Any]] = []

if should_audit and image_path and os.path.exists(image_path) and spec_path and os.path.exists(spec_path):
    st.session_state["last_run"] = image_path
    try:
        findings = check_image(image_path, spec_path)
        with Image.open(image_path) as img_obj:
            evidence_boxes = get_cached_evidence_boxes(image_path, findings, img_obj.size)
    except Exception as e:
        st.error(f"Error executing compliance audit: {e}")
        findings = []

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("🖼️ Packaging Artwork")
    if image_path and os.path.exists(image_path):
        if should_audit and findings:
            show_passing = st.toggle("Show passing rules on image", value=False)
            render_annotated_image(image_path, evidence_boxes, show_passing=show_passing)
        else:
            img = Image.open(image_path)
            st.image(img, use_container_width=True, caption=os.path.basename(image_path))
    else:
        st.warning("Please select or upload a packaging artwork image.")

with col_right:
    st.subheader("📋 Approved Specification")
    if spec_path and os.path.exists(spec_path):
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_data = json.load(f)

        st.markdown(f"**Product Name:** `{spec_data.get('product_name', 'N/A')}`")
        st.markdown(f"**Declared Net Qty:** `{spec_data.get('net_quantity', 'N/A')}`")
        st.markdown(f"**Vegetarian Mark:** `{spec_data.get('veg_mark', 'N/A')}`")
        st.markdown(f"**Mandatory Allergens:** `{spec_data.get('allergens', 'None')}`")

        with st.expander("🔍 View Complete Approved Specification (JSON)"):
            st.json(spec_data)
    else:
        st.warning("Specification not found.")

st.divider()

# Audit Results Section
if should_audit:
    if findings:
        # Calculate summary stats
        pass_count = sum(1 for f in findings if f.get("verdict") == "PASS")
        fail_count = sum(1 for f in findings if f.get("verdict") == "FAIL")
        review_count = sum(1 for f in findings if f.get("verdict") == "NEEDS_REVIEW")
        na_count = sum(1 for f in findings if f.get("verdict") == "N/A")

        # High-level Banner
        if fail_count > 0:
            st.error(f"❌ **NON-COMPLIANT ARTWORK**: {fail_count} regulatory violation(s) detected. Artwork cannot be approved for printing.")
        elif review_count > 0:
            st.warning(f"⚠️ **HUMAN REVIEW REQUIRED**: {review_count} rule(s) require manual inspection due to low confidence or order ambiguity.")
        else:
            st.success("✅ **PACKAGING APPROVED**: All applicable FSSAI regulatory requirements are satisfied with 100% compliance!")

        # Metric Scorecards
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(findings)}</div><div class="kpi-label">Rules Checked</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#16a34a;">{pass_count}</div><div class="kpi-label">Passed</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#dc2626;">{fail_count}</div><div class="kpi-label">Violations (FAIL)</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#d97706;">{review_count}</div><div class="kpi-label">Needs Review</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#64748b;">{na_count}</div><div class="kpi-label">Not Applicable</div></div>', unsafe_allow_html=True)

        st.markdown("### 📑 Detailed Rule-by-Rule Findings")

        filter_mode = st.radio(
            "Filter findings by:",
            ["All Rules", "Violations Only (FAIL)", "Review Needed (NEEDS_REVIEW)"],
            horizontal=True,
        )

        for item in findings:
            r_id = item["rule_id"]
            r_name = rules_map.get(r_id, r_id)
            verdict = item["verdict"]

            if filter_mode == "Violations Only (FAIL)" and verdict != "FAIL":
                continue
            if filter_mode == "Review Needed (NEEDS_REVIEW)" and verdict != "NEEDS_REVIEW":
                continue

            if verdict == "PASS":
                badge_html = '<span class="pass-badge">PASS</span>'
                icon = "✅"
            elif verdict == "FAIL":
                badge_html = '<span class="fail-badge">FAIL</span>'
                icon = "❌"
            elif verdict == "NEEDS_REVIEW":
                badge_html = '<span class="review-badge">NEEDS REVIEW</span>'
                icon = "⚠️"
            else:
                badge_html = '<span class="na-badge">N/A</span>'
                icon = "⚪"

            with st.expander(f"{icon} **[{r_id}] {r_name}** — {verdict}", expanded=(verdict == "FAIL")):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"**Found Text / Value:**")
                    st.code(str(item.get("found", "(None)")), language="text")
                with c2:
                    st.markdown(f"**Expected (Spec / Regulation):**")
                    st.code(str(item.get("expected", "(None)")), language="text")

                st.markdown(f"**Finding Reason:** {item.get('reason', 'N/A')}")
else:
    st.info("Select an artwork on the left and click 'Run Compliance Audit' to start.")

# Footer with quick reference
with st.expander("📚 Reference: The 10 FSSAI Labelling Rules Evaluated"):
    st.markdown(
        """
        | Rule | Title | Scope & Requirement |
        |:---|:---|:---|
        | **R01** | Net Quantity Present | Net quantity statement exists on packaging |
        | **R02** | Net Quantity Matches Spec | Numerical quantity matches approved spec (`N/A` if missing) |
        | **R03** | Correct Unit | Conformance to Legal Metrology symbols (`g`, `kg`, `mg`, `ml`, `l`) |
        | **R04** | Vegetarian Mark | Green square border with filled green circle symbol present |
        | **R05** | Allergen Section Present | Allergen declaration present if product spec contains allergens |
        | **R06** | Allergens Match Spec | All specified allergen ingredients declared on label |
        | **R07** | Ingredients Match Spec | 1-to-1 itemized ingredient matching & declaration order check |
        | **R08** | Manufacturer Address | Manufacturer name and physical postal address verified |
        | **R09** | FSSAI License Number | Exactly 14 numeric digits matching registration |
        | **R10** | MRP & Best-Before | Presence of both Maximum Retail Price and Expiry/Best-Before |
        """
    )

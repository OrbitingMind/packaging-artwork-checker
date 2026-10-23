"""
annotated_view.py
Renders interactive packaging artwork image with clickable evidence annotations
using Streamlit HTML components (st.components.v1.html).
"""

import base64
import html
import json
import os
from typing import Any, Dict, List
from PIL import Image
import streamlit.components.v1 as components


def render_annotated_image(
    image_path: str,
    evidence_boxes: List[Dict[str, Any]],
    show_passing: bool = False,
) -> None:
    """
    Renders base64 image with absolutely positioned percentage-based evidence boxes.
    Clicking a box displays rule details; clicking empty areas closes the panel.
    """
    if not os.path.exists(image_path):
        return

    with Image.open(image_path) as img:
        img_w, img_h = img.size

    # Filter boxes based on toggle
    if not show_passing:
        boxes_to_render = [b for b in evidence_boxes if b.get("verdict") != "PASS"]
    else:
        boxes_to_render = [b for b in evidence_boxes if b.get("verdict") != "N/A"]

    # Base64 encode image
    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png"
    if ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    img_data_uri = f"data:{mime};base64,{img_b64}"

    # Generate HTML boxes
    boxes_html_list = []
    box_data_payload = []

    for idx, box in enumerate(boxes_to_render):
        bbox = box.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox
        verdict = box.get("verdict", "PASS")
        kind = box.get("kind", "found")
        rule_id = box.get("rule_id", "")

        # Compute percentage coordinates relative to full image
        left_pct = max(0.0, min(100.0, (x1 / img_w) * 100.0))
        top_pct = max(0.0, min(100.0, (y1 / img_h) * 100.0))
        width_pct = max(1.5, min(100.0 - left_pct, ((x2 - x1) / img_w) * 100.0))
        height_pct = max(1.5, min(100.0 - top_pct, ((y2 - y1) / img_h) * 100.0))

        # Color schemes: Red for FAIL, Amber for NEEDS_REVIEW, Green for PASS
        if verdict == "FAIL":
            color = "#EF4444"
            bg = "rgba(239, 68, 68, 0.18)"
        elif verdict == "NEEDS_REVIEW":
            color = "#F59E0B"
            bg = "rgba(245, 158, 11, 0.22)"
        else:
            color = "#10B981"
            bg = "rgba(16, 185, 129, 0.18)"

        # Missing sections use dashed outline
        if kind == "missing":
            border_style = f"2.5px dashed {color}"
            bg = "rgba(239, 68, 68, 0.08)"
        else:
            border_style = f"2px solid {color}"

        tag_text = html.escape(rule_id)
        if kind == "missing":
            tag_text += " • MISSING"

        box_html = (
            f'<div class="evidence-box" data-idx="{idx}" '
            f'style="left: {left_pct:.3f}%; top: {top_pct:.3f}%; width: {width_pct:.3f}%; height: {height_pct:.3f}%; '
            f'border: {border_style}; background-color: {bg};">'
            f'<div class="box-tag" style="background-color: {color};">{tag_text}</div>'
            f'</div>'
        )
        boxes_html_list.append(box_html)

        # Store payload for JavaScript interactivity
        box_data_payload.append({
            "rule_id": box.get("rule_id", ""),
            "rule_name": box.get("rule_name", ""),
            "verdict": box.get("verdict", ""),
            "found": box.get("found", "(None)"),
            "expected": box.get("expected", "(None)"),
            "reason": box.get("reason", "N/A"),
            "fssai_clause": box.get("fssai_clause", "VERIFY"),
            "kind": kind,
            "label": box.get("label", ""),
        })

    boxes_html = "\n".join(boxes_html_list)
    boxes_json = json.dumps(box_data_payload)

    # Dynamic height calculation
    aspect_ratio = img_h / max(img_w, 1)
    container_height = int(max(480, min(850, 560 * aspect_ratio + 45)))

    html_code = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: transparent;
    overflow: hidden;
  }}
  .viewer-container {{
    position: relative;
    width: 100%;
    max-width: 100%;
    display: inline-block;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    background: #0F172A;
    user-select: none;
    -webkit-user-select: none;
  }}
  .artwork-img {{
    display: block;
    width: 100%;
    height: auto;
    pointer-events: auto;
  }}
  .evidence-box {{
    position: absolute;
    cursor: pointer;
    border-radius: 4px;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    z-index: 10;
  }}
  .evidence-box:hover {{
    transform: scale(1.02);
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.4);
    z-index: 20;
  }}
  .evidence-box.active {{
    box-shadow: 0 0 0 3px #FFFFFF, 0 0 16px rgba(0, 0, 0, 0.6);
    z-index: 30;
  }}
  .box-tag {{
    position: absolute;
    top: -12px;
    left: 4px;
    color: #FFFFFF;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    white-space: nowrap;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    pointer-events: none;
  }}
  .detail-panel {{
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.35), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
    z-index: 100;
    font-size: 13px;
    color: #1E293B;
    animation: slideUp 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  }}
  @keyframes slideUp {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  .panel-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    border-bottom: 1px solid #F1F5F9;
    padding-bottom: 8px;
  }}
  .panel-title {{
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .panel-close-btn {{
    background: #F1F5F9;
    border: none;
    border-radius: 6px;
    width: 26px;
    height: 26px;
    font-size: 16px;
    line-height: 26px;
    text-align: center;
    cursor: pointer;
    color: #64748B;
    font-weight: 700;
  }}
  .panel-close-btn:hover {{
    background: #E2E8F0;
    color: #0F172A;
  }}
  .badge-fail {{
    background: #FEE2E2;
    color: #991B1B;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
  }}
  .badge-review {{
    background: #FEF3C7;
    color: #92400E;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
  }}
  .badge-pass {{
    background: #DCFCE7;
    color: #166534;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 8px;
  }}
  .field-label {{
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 3px;
  }}
  .field-val-code {{
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    color: #0F172A;
    word-break: break-word;
    max-height: 58px;
    overflow-y: auto;
  }}
  .reason-row {{
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid #F1F5F9;
    font-size: 12px;
    color: #334155;
    line-height: 1.4;
  }}
  .clause-tag {{
    display: inline-block;
    background: #EEF2FF;
    color: #4F46E5;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
  }}
  .missing-tag {{
    display: inline-block;
    background: #FFF1F2;
    color: #BE123C;
    border: 1px dashed #FDA4AF;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
    margin-left: 6px;
  }}
</style>
</head>
<body>
<div class="viewer-container" id="viewer">
  <img class="artwork-img" id="artwork-img" src="{img_data_uri}" alt="Packaging Artwork" />
  {boxes_html}
  <div id="detail-panel" class="detail-panel" style="display: none;">
    <div class="panel-header">
      <div class="panel-title">
        <span id="panel-rule-id"></span>
        <span id="panel-rule-name"></span>
        <span id="panel-badge"></span>
      </div>
      <button class="panel-close-btn" id="close-btn" title="Close details">&times;</button>
    </div>
    <div class="grid-2">
      <div>
        <div class="field-label">Found on Artwork</div>
        <div class="field-val-code" id="panel-found"></div>
      </div>
      <div>
        <div class="field-label">Expected (Spec / Regulation)</div>
        <div class="field-val-code" id="panel-expected"></div>
      </div>
    </div>
    <div class="reason-row">
      <strong>Reason:</strong> <span id="panel-reason"></span>
    </div>
    <div>
      <span class="clause-tag">FSSAI Clause: <span id="panel-clause"></span></span>
      <span class="missing-tag" id="panel-missing" style="display: none;">Dashed Region: Missing Mandatory Section</span>
    </div>
  </div>
</div>

<script>
  const boxData = {boxes_json};
  const panel = document.getElementById('detail-panel');
  const viewer = document.getElementById('viewer');
  const closeBtn = document.getElementById('close-btn');

  function showDetails(idx) {{
    const d = boxData[idx];
    if (!d) return;

    document.getElementById('panel-rule-id').textContent = '[' + (d.rule_id || '') + ']';
    document.getElementById('panel-rule-name').textContent = d.rule_name || '';

    const badge = document.getElementById('panel-badge');
    badge.textContent = d.verdict || '';
    if (d.verdict === 'FAIL') {{
      badge.className = 'badge-fail';
    }} else if (d.verdict === 'NEEDS_REVIEW') {{
      badge.className = 'badge-review';
    }} else {{
      badge.className = 'badge-pass';
    }}

    document.getElementById('panel-found').textContent = d.found || '(None)';
    document.getElementById('panel-expected').textContent = d.expected || '(None)';
    document.getElementById('panel-reason').textContent = d.reason || 'N/A';
    document.getElementById('panel-clause').textContent = d.fssai_clause || 'VERIFY';

    const missingTag = document.getElementById('panel-missing');
    if (d.kind === 'missing') {{
      missingTag.style.display = 'inline-block';
    }} else {{
      missingTag.style.display = 'none';
    }}

    // Highlight active box
    document.querySelectorAll('.evidence-box').forEach(b => b.classList.remove('active'));
    const activeBox = document.querySelector(`.evidence-box[data-idx="${{idx}}"]`);
    if (activeBox) activeBox.classList.add('active');

    panel.style.display = 'block';
  }}

  function hideDetails() {{
    panel.style.display = 'none';
    document.querySelectorAll('.evidence-box').forEach(b => b.classList.remove('active'));
  }}

  // Click on box
  document.querySelectorAll('.evidence-box').forEach(b => {{
    b.addEventListener('click', function(e) {{
      e.stopPropagation();
      const idx = parseInt(this.getAttribute('data-idx'));
      showDetails(idx);
    }});
  }});

  // Close button inside detail panel
  if (closeBtn) {{
    closeBtn.addEventListener('click', function(e) {{
      e.stopPropagation();
      hideDetails();
    }});
  }}

  // Click on empty area closes it
  document.addEventListener('click', function(e) {{
    if (panel.style.display === 'block') {{
      if (!panel.contains(e.target) && !e.target.closest('.evidence-box')) {{
        hideDetails();
      }}
    }}
  }});
</script>
</body>
</html>
"""

    components.html(html_code, height=container_height, scrolling=False)

"""
Packaging artwork test dataset generator for artwork compliance checker evaluation.
Generates synthetic label images with known injected errors, answer_key.json, and split.json.
"""

import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

# Set fixed random seed for reproducible dataset generation
SEED = 42
random.seed(SEED)

# Directory configurations
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
SPECS_DIR = os.path.join(SCRIPT_DIR, "specs")
OUTPUT_IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
ANSWER_KEY_PATH = os.path.join(SCRIPT_DIR, "answer_key.json")
SPLIT_PATH = os.path.join(SCRIPT_DIR, "split.json")

# Rule definitions R01 - R10
ALL_RULES = ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10"]

# Product panel and text color specifications
# biscuit & salt: light panel with dark text
# masala & chips: dark panel with light text
# juice: orange-tinted panel with dark text
PRODUCT_THEMES = {
    "biscuit": {
        "panel_rgb": (252, 250, 244),
        "text_rgb": (25, 25, 25),
    },
    "salt": {
        "panel_rgb": (246, 248, 252),
        "text_rgb": (25, 25, 25),
    },
    "masala": {
        "panel_rgb": (34, 24, 20),
        "text_rgb": (245, 244, 238),
    },
    "chips": {
        "panel_rgb": (28, 28, 34),
        "text_rgb": (245, 245, 245),
    },
    "juice": {
        "panel_rgb": (255, 226, 186),
        "text_rgb": (45, 25, 15),
    },
}

# Clean render configurations differing in font family, font size, and panel opacity
STYLE_CLEAN1 = {
    "font_family": "arial",
    "title_size": 36,
    "body_size": 24,
    "panel_opacity": 0.88,
}

STYLE_CLEAN2 = {
    "font_family": "calibri",
    "title_size": 32,
    "body_size": 22,
    "panel_opacity": 0.72,
}


def load_font(family="arial", size=24, bold=False):
    """Loads a system or DejaVu font without downloading external files."""
    candidates = []
    if family == "calibri":
        candidates = [
            "calibrib.ttf" if bold else "calibri.ttf",
            "tahomabd.ttf" if bold else "tahoma.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
        ]
    else:
        candidates = [
            "arialbd.ttf" if bold else "arial.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "calibrib.ttf" if bold else "calibri.ttf",
            "DejaVuSans.ttf",
        ]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
        # Search Windows Fonts directory
        win_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        candidate_path = os.path.join(win_fonts, name)
        if os.path.exists(candidate_path):
            try:
                return ImageFont.truetype(candidate_path, size)
            except OSError:
                pass
        # Search Linux standard font directories
        for linux_dir in ["/usr/share/fonts", "/usr/share/fonts/truetype", "/usr/share/fonts/truetype/dejavu"]:
            candidate_path = os.path.join(linux_dir, name)
            if os.path.exists(candidate_path):
                try:
                    return ImageFont.truetype(candidate_path, size)
                except OSError:
                    pass

    return ImageFont.load_default()


def wrap_section_text(heading, text, max_width, font_bold, font_norm):
    """Auto-wraps section text within available panel width with bold heading."""
    words = text.split()
    lines = []
    h_str = (heading + " ") if heading else ""
    h_w = font_bold.getlength(h_str) if h_str else 0.0

    # Line 1 includes the heading
    cur_words = []
    idx = 0
    while idx < len(words):
        test_words = cur_words + [words[idx]]
        test_w = h_w + font_norm.getlength(" ".join(test_words))
        if test_w <= max_width:
            cur_words.append(words[idx])
            idx += 1
        else:
            if not cur_words:
                cur_words.append(words[idx])
                idx += 1
            break
    lines.append((True, h_str, " ".join(cur_words)))

    # Subsequent lines span full width
    while idx < len(words):
        cur_words = []
        while idx < len(words):
            test_words = cur_words + [words[idx]]
            test_w = font_norm.getlength(" ".join(test_words))
            if test_w <= max_width:
                cur_words.append(words[idx])
                idx += 1
            else:
                if not cur_words:
                    cur_words.append(words[idx])
                    idx += 1
                break
        lines.append((False, "", " ".join(cur_words)))

    return lines


def render_label_image(template_path, product, fields, config):
    """Renders a 1080x1440 label with semi-opaque panel, veg mark, and back-of-pack sections."""
    # Resize template to 1080x1440
    base_img = Image.open(template_path).convert("RGBA")
    base_img = base_img.resize((1080, 1440), Image.Resampling.LANCZOS)

    # Semi-opaque rounded panel covering roughly x 8-92%, y 18-82%
    p_x1 = int(1080 * 0.08)  # 86
    p_y1 = int(1440 * 0.18)  # 259
    p_x2 = int(1080 * 0.92)  # 993
    p_y2 = int(1440 * 0.82)  # 1180

    theme = PRODUCT_THEMES[product]
    alpha = int(255 * config["panel_opacity"])
    panel_rgba = theme["panel_rgb"] + (alpha,)
    text_color = theme["text_rgb"] + (255,)

    overlay = Image.new("RGBA", (1080, 1440), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle([p_x1, p_y1, p_x2, p_y2], radius=24, fill=panel_rgba)
    img = Image.alpha_composite(base_img, overlay)

    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = load_font(config["font_family"], config["title_size"], bold=True)
    font_bold = load_font(config["font_family"], config["body_size"], bold=True)
    font_norm = load_font(config["font_family"], config["body_size"], bold=False)

    pad_x = 45
    pad_y = 45
    content_x = p_x1 + pad_x
    content_max_w = (p_x2 - pad_x) - content_x
    cur_y = p_y1 + pad_y
    line_h = int(config["body_size"] * 1.45)
    section_gap = 18

    # Veg mark: green square outline with green filled circle inside (no text)
    if fields.get("veg_mark") == "veg":
        veg_size = 36
        vx = p_x2 - pad_x - veg_size
        vy = cur_y + 4
        green = (0, 138, 0, 255)
        draw.rectangle([vx, vy, vx + veg_size, vy + veg_size], outline=green, width=3)
        draw.ellipse([vx + 9, vy + 9, vx + veg_size - 9, vy + veg_size - 9], fill=green)

    # Product Name
    title_text = fields.get("product_name", "")
    if title_text:
        title_max_w = content_max_w - 50  # leave room on right for veg mark
        words = title_text.split()
        t_lines = []
        cur_w = []
        for w in words:
            test_line = " ".join(cur_w + [w])
            if font_title.getlength(test_line) <= title_max_w:
                cur_w.append(w)
            else:
                if cur_w:
                    t_lines.append(" ".join(cur_w))
                    cur_w = [w]
                else:
                    t_lines.append(w)
        if cur_w:
            t_lines.append(" ".join(cur_w))

        for tl in t_lines:
            draw.text((content_x, cur_y), tl, font=font_title, fill=text_color)
            cur_y += int(config["title_size"] * 1.3)

        cur_y += 12
        draw.line([content_x, cur_y, p_x2 - pad_x, cur_y], fill=text_color[:3] + (80,), width=1)
        cur_y += 22

    # Back-of-pack sections with specified headings
    sections = [
        ("Net Qty:", fields.get("net_quantity", "")),
        ("Ingredients:", fields.get("ingredients", "")),
        ("Allergen Information:", fields.get("allergens", "")),
        ("Manufactured by:", fields.get("manufacturer", "")),
        ("FSSAI Lic. No.:", fields.get("fssai_license", "")),
        ("MRP:", fields.get("mrp", "")),
        ("Best before", fields.get("best_before", "")),
    ]

    for heading, val in sections:
        if not val:
            continue

        text_to_wrap = val
        h_to_use = heading
        # For "Best before", heading is "Best before", followed by remainder of string
        if heading == "Best before":
            if val.lower().startswith("best before"):
                text_to_wrap = val[len("best before"):].strip()
            h_to_use = "Best before"

        lines = wrap_section_text(h_to_use, text_to_wrap, content_max_w, font_bold, font_norm)
        for is_first, h_str, line_text in lines:
            if is_first and h_str:
                draw.text((content_x, cur_y), h_str, font=font_bold, fill=text_color)
                hw = font_bold.getlength(h_str)
                if line_text:
                    draw.text((content_x + hw, cur_y), line_text, font=font_norm, fill=text_color)
            else:
                if line_text:
                    draw.text((content_x, cur_y), line_text, font=font_norm, fill=text_color)
            cur_y += line_h
        cur_y += section_gap

    return img


def create_error_fields(spec, rule_id, rng):
    """
    Creates a copy of spec fields with exactly one injected error.
    Returns (modified_fields, r10_target).
    """
    fields = dict(spec)
    r10_target = None

    if rule_id == "R01":
        # R01: net quantity removed
        fields["net_quantity"] = ""
    elif rule_id == "R02":
        # R02: net quantity value changed
        qty_changes = {
            "biscuit": "20 g",
            "masala": "10 g",
            "juice": "2 L",
            "chips": "25 g",
            "salt": "2 kg",
        }
        fields["net_quantity"] = qty_changes[spec["product"]]
    elif rule_id == "R03":
        # R03: wrong unit (e.g. gm, ltr, KG)
        unit_changes = {
            "biscuit": "200 gm",
            "masala": "100 gm",
            "juice": "1 ltr",
            "chips": "52 gm",
            "salt": "1 KG",
        }
        fields["net_quantity"] = unit_changes[spec["product"]]
    elif rule_id == "R04":
        # R04: veg mark removed
        fields["veg_mark"] = ""
    elif rule_id == "R05":
        # R05: allergen section removed
        fields["allergens"] = ""
    elif rule_id == "R06":
        # R06: one allergen deleted from allergen text
        prod = spec["product"]
        if prod == "biscuit":
            fields["allergens"] = "Contains wheat. May contain milk."
        elif prod == "masala":
            fields["allergens"] = "Contains mustard."
        elif prod == "chips":
            fields["allergens"] = "Contains milk. May contain wheat."
        elif prod == "juice":
            fields["allergens"] = "Contains."
    elif rule_id == "R07":
        # R07: ingredient list altered (one ingredient removed or changed)
        prod = spec["product"]
        if prod == "biscuit":
            fields["ingredients"] = "Wheat flour, sugar, palm oil, invert syrup, salt, raising agents"
        elif prod == "masala":
            fields["ingredients"] = "Coriander, cumin, black pepper, cinnamon, cloves, bay leaf, salt"
        elif prod == "juice":
            fields["ingredients"] = "Water, orange juice concentrate (10%), acidity regulator (330), preservative (223)"
        elif prod == "chips":
            fields["ingredients"] = "Potato, edible vegetable oil (palm), spices and condiments, salt"
        elif prod == "salt":
            fields["ingredients"] = "Edible common salt"
    elif rule_id == "R08":
        # R08: manufacturer address removed
        fields["manufacturer"] = ""
    elif rule_id == "R09":
        # R09: FSSAI number wrong length (13 digits)
        fields["fssai_license"] = spec["fssai_license"][:13]
    elif rule_id == "R10":
        # R10: MRP removed or best-before removed (randomly picked and recorded)
        r10_target = rng.choice(["mrp", "best_before"])
        if r10_target == "mrp":
            fields["mrp"] = ""
        else:
            fields["best_before"] = ""

    return fields, r10_target


def compute_verdicts(has_allergens, injected_errors):
    """
    Computes verdicts for R01-R10 as pass, fail, or n/a.
    R05 and R06 are n/a when has_allergens is false.
    """
    verdicts = {}
    for rule in ALL_RULES:
        if not has_allergens and rule in ("R05", "R06"):
            verdicts[rule] = "n/a"
        elif rule in injected_errors:
            verdicts[rule] = "fail"
        else:
            verdicts[rule] = "pass"
    return verdicts


def main():
    os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
    rng = random.Random(SEED)

    # Load all specs
    products = sorted([f.split(".")[0] for f in os.listdir(SPECS_DIR) if f.endswith(".json")])
    specs = {}
    for prod in products:
        with open(os.path.join(SPECS_DIR, f"{prod}.json"), "r", encoding="utf-8") as f:
            specs[prod] = json.load(f)

    answer_key = {}
    generated_images = []

    # Generate variants per product
    for prod in products:
        spec = specs[prod]
        tpl_path = os.path.join(TEMPLATES_DIR, f"{prod}.png")

        # 1. Clean 1 variant
        c1_name = f"{prod}_clean1.png"
        c1_fields = dict(spec)
        if not spec.get("has_allergens", False):
            c1_fields["allergens"] = ""
        c1_img = render_label_image(tpl_path, prod, c1_fields, STYLE_CLEAN1)
        c1_img.save(os.path.join(OUTPUT_IMAGES_DIR, c1_name))
        generated_images.append(c1_name)
        answer_key[c1_name] = {
            "product": prod,
            "injected_errors": [],
            "fields": c1_fields,
            "verdicts": compute_verdicts(spec["has_allergens"], []),
            "expected_verdicts": compute_verdicts(spec["has_allergens"], []),
        }

        # 2. Clean 2 variant (differing in font family, size, opacity)
        c2_name = f"{prod}_clean2.png"
        c2_fields = dict(spec)
        if not spec.get("has_allergens", False):
            c2_fields["allergens"] = ""
        c2_img = render_label_image(tpl_path, prod, c2_fields, STYLE_CLEAN2)
        c2_img.save(os.path.join(OUTPUT_IMAGES_DIR, c2_name))
        generated_images.append(c2_name)
        answer_key[c2_name] = {
            "product": prod,
            "injected_errors": [],
            "fields": c2_fields,
            "verdicts": compute_verdicts(spec["has_allergens"], []),
            "expected_verdicts": compute_verdicts(spec["has_allergens"], []),
        }

        # 3. Injected error variants
        for rule_id in ALL_RULES:
            # Skip R05 and R06 when has_allergens is false
            if not spec["has_allergens"] and rule_id in ("R05", "R06"):
                continue

            err_name = f"{prod}_err{rule_id}.png"
            err_fields, r10_target = create_error_fields(spec, rule_id, rng)
            err_img = render_label_image(tpl_path, prod, err_fields, STYLE_CLEAN1)
            err_img.save(os.path.join(OUTPUT_IMAGES_DIR, err_name))
            generated_images.append(err_name)

            entry = {
                "product": prod,
                "injected_errors": [rule_id],
                "fields": err_fields,
                "verdicts": compute_verdicts(spec["has_allergens"], [rule_id]),
                "expected_verdicts": compute_verdicts(spec["has_allergens"], [rule_id]),
            }
            if r10_target:
                entry["r10_removed"] = r10_target
            answer_key[err_name] = entry

    # Save answer_key.json
    with open(ANSWER_KEY_PATH, "w", encoding="utf-8") as f:
        json.dump(answer_key, f, indent=2)

    # Create stratified dev/test split (~40% dev, ~60% test)
    split_rng = random.Random(SEED)
    dev_images = []
    test_images = []

    for prod in products:
        prod_imgs = [img for img in sorted(generated_images) if img.startswith(prod + "_")]
        split_rng.shuffle(prod_imgs)
        n_dev = round(len(prod_imgs) * 0.40)
        dev_images.extend(prod_imgs[:n_dev])
        test_images.extend(prod_imgs[n_dev:])

    dev_images.sort()
    test_images.sort()

    split_data = {
        "dev": dev_images,
        "test": test_images,
    }

    with open(SPLIT_PATH, "w", encoding="utf-8") as f:
        json.dump(split_data, f, indent=2)

    # Print count summary
    print(f"Generated {len(generated_images)} images across {len(products)} products:")
    for prod in products:
        prod_count = sum(1 for img in generated_images if img.startswith(prod + "_"))
        print(f"  - {prod}: {prod_count} images")

    print(f"\nStratified Split (seed={SEED}):")
    print(f"  - dev:  {len(dev_images)} images ({len(dev_images)/len(generated_images):.1%})")
    print(f"  - test: {len(test_images)} images ({len(test_images)/len(generated_images):.1%})")
    print(f"\nOutputs written successfully:")
    print(f"  - Images: {OUTPUT_IMAGES_DIR} ({len(generated_images)} files)")
    print(f"  - Answer key: {ANSWER_KEY_PATH}")
    print(f"  - Split: {SPLIT_PATH}")


if __name__ == "__main__":
    main()

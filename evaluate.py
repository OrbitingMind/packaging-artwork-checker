"""
evaluate.py
Evaluates the packaging compliance pipeline against the dataset.

Usage:
    python evaluate.py --split dev|test|all   (default: dev)

Measures precision, recall, recall-with-review, false-alarm rate, and review rate
against the ground truth in dataset/answer_key.json.
Outputs results to console and saves:
    - outputs/eval_<split>.json
    - outputs/eval_<split>.md
"""

import argparse
from collections import defaultdict
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from pipeline import check_image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPLIT_PATH = os.path.join(BASE_DIR, "dataset", "split.json")
ANSWER_KEY_PATH = os.path.join(BASE_DIR, "dataset", "answer_key.json")
SPECS_DIR = os.path.join(BASE_DIR, "dataset", "specs")
IMAGES_DIR = os.path.join(BASE_DIR, "dataset", "images")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely computes division avoiding ZeroDivisionError.
    Equivalent to returning default if denominator is 0.
    """
    return (numerator / denominator) if denominator > 0 else default


def init_metrics_counter() -> Dict[str, int]:
    """
    Initializes confusion matrix counts for packaging compliance:
    - TP: expected fail, predicted FAIL
    - FN: expected fail, predicted PASS
    - caught: expected fail, predicted NEEDS_REVIEW
    - fp: expected pass, predicted FAIL
    - review_burden: expected pass, predicted NEEDS_REVIEW
    - tn: expected pass, predicted PASS
    """
    return {
        "tp": 0,
        "fn": 0,
        "caught": 0,
        "fp": 0,
        "review_burden": 0,
        "tn": 0,
    }


def compute_rates(counts: Dict[str, int]) -> Dict[str, Any]:
    """
    Computes precision, recall, recall-with-review, false-alarm rate, and review rate.

    Definitions (positive = rule is truly violated):
    - precision = TP / (TP + FP)
    - recall = TP / (TP + FN + Caught)
    - recall_with_review = (TP + Caught) / (TP + FN + Caught)
    - false_alarm_rate = FP / (FP + TN + Review-burden)
    - review_rate = (Caught + Review-burden) / Total
    """
    tp = counts["tp"]
    fn = counts["fn"]
    caught = counts["caught"]
    fp = counts["fp"]
    review_burden = counts["review_burden"]
    tn = counts["tn"]

    total = tp + fn + caught + fp + review_burden + tn
    total_positives = tp + fn + caught  # Truly violated
    total_negatives = fp + tn + review_burden  # Truly compliant

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, total_positives)
    recall_with_review = safe_div(tp + caught, total_positives)
    false_alarm_rate = safe_div(fp, total_negatives)
    review_rate = safe_div(caught + review_burden, total)

    return {
        "tp": tp,
        "fn": fn,
        "caught": caught,
        "fp": fp,
        "review_burden": review_burden,
        "tn": tn,
        "total": total,
        "precision": precision,
        "recall": recall,
        "recall_with_review": recall_with_review,
        "false_alarm_rate": false_alarm_rate,
        "review_rate": review_rate,
    }


def format_pct(val: float) -> str:
    """Formats float (0.0 to 1.0) as percentage string, e.g. 87.5%."""
    return f"{val * 100:.1f}%"


def build_markdown_table(headers: List[str], rows: List[List[str]], alignments: Optional[List[str]] = None) -> str:
    """
    Helper to construct standard GitHub-flavored Markdown tables.
    alignments can be 'left' (:---) or 'right' (---:).
    """
    if alignments is None:
        alignments = ["left"] * len(headers)

    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join([":---" if a == "left" else "---:" for a in alignments]) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, sep_line] + row_lines)


def evaluate_split(split_name: str = "dev") -> Dict[str, Any]:
    """
    Runs evaluation on the selected split ('dev', 'test', or 'all').
    Returns evaluation dictionary containing overall, per_rule, per_product metrics,
    and wrong predictions.
    """
    split_name = split_name.lower().strip()
    if split_name not in ("dev", "test", "all"):
        raise ValueError(f"Invalid split '{split_name}'. Must be 'dev', 'test', or 'all'.")

    # Load split definitions and ground truth answer key
    with open(SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    with open(ANSWER_KEY_PATH, "r", encoding="utf-8") as f:
        answer_key = json.load(f)

    # Determine image list
    if split_name == "dev":
        target_images = split_data.get("dev", [])
    elif split_name == "test":
        target_images = split_data.get("test", [])
    else:  # all
        # Combine dev and test while preserving order
        dev_list = split_data.get("dev", [])
        test_list = split_data.get("test", [])
        target_images = dev_list + [img for img in test_list if img not in dev_list]

    overall_counts = init_metrics_counter()
    rule_counts: Dict[str, Dict[str, int]] = defaultdict(init_metrics_counter)
    product_counts: Dict[str, Dict[str, int]] = defaultdict(init_metrics_counter)

    wrong_predictions: List[Dict[str, Any]] = []
    failed_images: List[Dict[str, str]] = []
    rules_excluded_na = 0

    print(f"\nRunning evaluation on split '{split_name}' ({len(target_images)} images)...")

    for idx, img_name in enumerate(target_images, 1):
        img_path = os.path.join(IMAGES_DIR, img_name)
        entry = answer_key.get(img_name, {})
        product = entry.get("product") or img_name.split("_")[0]
        spec_path = os.path.join(SPECS_DIR, f"{product}.json")

        if not os.path.exists(img_path):
            err_msg = f"Image file not found: {img_path}"
            print(f"[ERROR] {err_msg}", file=sys.stderr)
            failed_images.append({"image": img_name, "error": err_msg})
            continue

        try:
            # check_image handles vision extraction with local disk caching
            findings = check_image(img_path, spec_path)
        except Exception as exc:
            err_msg = str(exc)
            print(f"[ERROR] Pipeline execution failed on '{img_name}': {err_msg}", file=sys.stderr)
            failed_images.append({"image": img_name, "error": err_msg})
            continue

        # Expected verdicts per rule from answer key
        expected_verdicts = entry.get("expected_verdicts", entry.get("verdicts", {}))

        for finding in findings:
            rule_id = finding.get("rule_id", "")
            raw_expected = str(expected_verdicts.get(rule_id, "")).strip().lower()

            # Skip rules whose expected verdict is "n/a"
            if raw_expected == "n/a" or not raw_expected:
                continue

            pred_verdict = str(finding.get("verdict", "")).strip().upper()
            found_val = finding.get("found", "")

            # Exclude rules predicted N/A from metrics (e.g. R02/R03 when net quantity missing)
            if pred_verdict == "N/A":
                rules_excluded_na += 1
                continue

            # Classify prediction into confusion matrix category
            cls = ""
            if raw_expected == "fail":
                if pred_verdict == "FAIL":
                    cls = "TP"
                    overall_counts["tp"] += 1
                    rule_counts[rule_id]["tp"] += 1
                    product_counts[product]["tp"] += 1
                elif pred_verdict == "PASS":
                    cls = "FN"
                    overall_counts["fn"] += 1
                    rule_counts[rule_id]["fn"] += 1
                    product_counts[product]["fn"] += 1
                elif pred_verdict == "NEEDS_REVIEW":
                    cls = "Caught-for-review"
                    overall_counts["caught"] += 1
                    rule_counts[rule_id]["caught"] += 1
                    product_counts[product]["caught"] += 1
                else:
                    cls = "FN"
                    overall_counts["fn"] += 1
                    rule_counts[rule_id]["fn"] += 1
                    product_counts[product]["fn"] += 1

            elif raw_expected == "pass":
                if pred_verdict == "PASS":
                    cls = "TN"
                    overall_counts["tn"] += 1
                    rule_counts[rule_id]["tn"] += 1
                    product_counts[product]["tn"] += 1
                elif pred_verdict == "FAIL":
                    cls = "FP"
                    overall_counts["fp"] += 1
                    rule_counts[rule_id]["fp"] += 1
                    product_counts[product]["fp"] += 1
                elif pred_verdict == "NEEDS_REVIEW":
                    cls = "Review-burden"
                    overall_counts["review_burden"] += 1
                    rule_counts[rule_id]["review_burden"] += 1
                    product_counts[product]["review_burden"] += 1
                else:
                    cls = "FP"
                    overall_counts["fp"] += 1
                    rule_counts[rule_id]["fp"] += 1
                    product_counts[product]["fp"] += 1

            # Discrepancy / wrong prediction recording
            if pred_verdict != raw_expected.upper():
                wrong_predictions.append({
                    "image": img_name,
                    "product": product,
                    "rule": rule_id,
                    "expected": raw_expected,
                    "predicted": pred_verdict,
                    "found": found_val,
                    "found_value": found_val,
                    "classification": cls,
                    "reason": finding.get("reason", ""),
                })

    # Compute rate metrics for overall, per-rule, and per-product
    overall_metrics = compute_rates(overall_counts)

    per_rule_metrics: Dict[str, Dict[str, Any]] = {}
    for r_id in sorted(rule_counts.keys()):
        per_rule_metrics[r_id] = compute_rates(rule_counts[r_id])

    per_product_metrics: Dict[str, Dict[str, Any]] = {}
    for prod in sorted(product_counts.keys()):
        per_product_metrics[prod] = compute_rates(product_counts[prod])

    eval_result = {
        "split": split_name,
        "images_total": len(target_images),
        "images_evaluated": len(target_images) - len(failed_images),
        "images_failed": len(failed_images),
        "rules_excluded_na": rules_excluded_na,
        "failed_images": failed_images,
        "overall": overall_metrics,
        "per_rule": per_rule_metrics,
        "per_product": per_product_metrics,
        "wrong_predictions": wrong_predictions,
    }

    return eval_result


def print_evaluation_report(result: Dict[str, Any]) -> None:
    """
    Prints human-readable evaluation tables to the console:
    - Overall summary
    - Per-rule table
    - Per-product table
    - List of wrong predictions
    - Images failed report
    """
    split = result["split"]
    overall = result["overall"]
    per_rule = result["per_rule"]
    per_product = result["per_product"]
    wrong_preds = result["wrong_predictions"]

    print("\n" + "=" * 90)
    print(f"PACKAGING COMPLIANCE EVALUATION REPORT (Split: {split})")
    print("=" * 90)
    print(f"Images Total     : {result['images_total']}")
    print(f"Images Evaluated : {result['images_evaluated']}")
    print(f"Images Failed    : {result['images_failed']}")
    print(f"Rules Excluded NA: {result.get('rules_excluded_na', 0)} (predicted N/A, e.g. R02/R03 when net quantity missing)")

    # Overall Summary
    print("\n" + "-" * 90)
    print("OVERALL PERFORMANCE SUMMARY")
    print("-" * 90)
    print(f"Total Rule Checks   : {overall['total']}")
    print(f"True Positives (TP) : {overall['tp']:<5} (expected fail, predicted FAIL)")
    print(f"False Negatives (FN): {overall['fn']:<5} (expected fail, predicted PASS)")
    print(f"Caught for Review   : {overall['caught']:<5} (expected fail, predicted NEEDS_REVIEW)")
    print(f"False Positives (FP): {overall['fp']:<5} (expected pass, predicted FAIL - false alarm)")
    print(f"Review Burden       : {overall['review_burden']:<5} (expected pass, predicted NEEDS_REVIEW)")
    print(f"True Negatives (TN) : {overall['tn']:<5} (expected pass, predicted PASS)")
    print("-" * 90)
    print(f"Precision           : {format_pct(overall['precision']):>6}   [TP / (TP + FP)]")
    print(f"Recall              : {format_pct(overall['recall']):>6}   [TP / (TP + FN + Caught)]")
    print(f"Recall (w/ review)  : {format_pct(overall['recall_with_review']):>6}   [(TP + Caught) / (TP + FN + Caught)]")
    print(f"False Alarm Rate    : {format_pct(overall['false_alarm_rate']):>6}   [FP / (FP + TN + Review-burden)]")
    print(f"Review Rate         : {format_pct(overall['review_rate']):>6}   [(Caught + Review-burden) / Total]")
    print("-" * 90)

    # Per-Rule Table
    print("\n" + "=" * 128)
    print("PER-RULE PERFORMANCE TABLE")
    print("=" * 128)
    header = (
        f"{'Rule':<6} | {'Total':<5} | {'TP':<3} | {'FN':<3} | {'Cgt':<3} | {'FP':<3} | "
        f"{'Brdn':<4} | {'TN':<4} | {'Precision':<9} | {'Recall':<7} | {'Rec(w/Rev)':<10} | {'False Alarm':<11} | {'Review Rate':<11}"
    )
    print(header)
    print("-" * 128)
    for r_id in sorted(per_rule.keys()):
        m = per_rule[r_id]
        print(
            f"{r_id:<6} | {m['total']:<5} | {m['tp']:<3} | {m['fn']:<3} | {m['caught']:<3} | {m['fp']:<3} | "
            f"{m['review_burden']:<4} | {m['tn']:<4} | {format_pct(m['precision']):>9} | {format_pct(m['recall']):>7} | "
            f"{format_pct(m['recall_with_review']):>10} | {format_pct(m['false_alarm_rate']):>11} | {format_pct(m['review_rate']):>11}"
        )
    print("=" * 128)

    # Per-Product Table
    print("\n" + "=" * 128)
    print("PER-PRODUCT PERFORMANCE TABLE")
    print("=" * 128)
    p_header = (
        f"{'Product':<10} | {'Total':<5} | {'TP':<3} | {'FN':<3} | {'Cgt':<3} | {'FP':<3} | "
        f"{'Brdn':<4} | {'TN':<4} | {'Precision':<9} | {'Recall':<7} | {'Rec(w/Rev)':<10} | {'False Alarm':<11} | {'Review Rate':<11}"
    )
    print(p_header)
    print("-" * 128)
    for prod in sorted(per_product.keys()):
        m = per_product[prod]
        print(
            f"{prod:<10} | {m['total']:<5} | {m['tp']:<3} | {m['fn']:<3} | {m['caught']:<3} | {m['fp']:<3} | "
            f"{m['review_burden']:<4} | {m['tn']:<4} | {format_pct(m['precision']):>9} | {format_pct(m['recall']):>7} | "
            f"{format_pct(m['recall_with_review']):>10} | {format_pct(m['false_alarm_rate']):>11} | {format_pct(m['review_rate']):>11}"
        )
    print("=" * 128)

    # Wrong Predictions Table
    print(f"\nWRONG PREDICTIONS ({len(wrong_preds)}):")
    print("-" * 120)
    w_header = f"{'Image':<22} | {'Rule':<5} | {'Expected':<8} | {'Predicted':<12} | {'Found Value'}"
    print(w_header)
    print("-" * 120)
    if not wrong_preds:
        print("  (None! All predictions matched expected ground truth)")
    else:
        for wp in wrong_preds:
            img = wp["image"]
            rule = wp["rule"]
            exp = wp["expected"]
            pred = wp["predicted"]
            found = str(wp["found"]).replace("\n", " ").strip()
            if len(found) > 60:
                found = found[:57] + "..."
            if not found:
                found = "(empty)"
            print(f"{img:<22} | {rule:<5} | {exp:<8} | {pred:<12} | {found}")
    print("=" * 120 + "\n")


def generate_markdown_report(result: Dict[str, Any]) -> str:
    """
    Generates GitHub-flavored Markdown text suitable for pasting directly into README.
    """
    split = result["split"]
    overall = result["overall"]
    per_rule = result["per_rule"]
    per_product = result["per_product"]
    wrong_preds = result["wrong_predictions"]

    md_lines: List[str] = [
        f"# Evaluation Report ({split} split)",
        "",
        f"- **Images Evaluated**: {result['images_evaluated']} / {result['images_total']}",
        f"- **Images Failed**: {result['images_failed']}",
        f"- **Rules Excluded (Predicted N/A)**: {result.get('rules_excluded_na', 0)}",
        "",
        "## Overall Summary",
        "",
    ]

    # Overall Summary Table
    overall_headers = ["Metric", "Value", "Definition"]
    overall_alignments = ["left", "right", "left"]
    overall_rows = [
        ["Total Rule Evaluations", str(overall["total"]), "Excludes skipped 'n/a' rules"],
        ["Rules Excluded (Predicted N/A)", str(result.get("rules_excluded_na", 0)), "Excluded from metrics (e.g. R02/R03 when net quantity missing)"],
        ["True Positives (TP)", str(overall["tp"]), "Expected fail, predicted FAIL"],
        ["False Negatives (FN)", str(overall["fn"]), "Expected fail, predicted PASS (missed defect)"],
        ["Caught for Review", str(overall["caught"]), "Expected fail, predicted NEEDS_REVIEW"],
        ["False Positives (FP)", str(overall["fp"]), "Expected pass, predicted FAIL (false alarm)"],
        ["Review Burden", str(overall["review_burden"]), "Expected pass, predicted NEEDS_REVIEW"],
        ["True Negatives (TN)", str(overall["tn"]), "Expected pass, predicted PASS"],
        ["**Precision**", f"**{format_pct(overall['precision'])}**", "`TP / (TP + FP)`"],
        ["**Recall**", f"**{format_pct(overall['recall'])}**", "`TP / (TP + FN + Caught)`"],
        ["**Recall (with review)**", f"**{format_pct(overall['recall_with_review'])}**", "`(TP + Caught) / (TP + FN + Caught)`"],
        ["**False Alarm Rate**", f"**{format_pct(overall['false_alarm_rate'])}**", "`FP / (FP + TN + Review-burden)`"],
        ["**Review Rate**", f"**{format_pct(overall['review_rate'])}**", "`(Caught + Review-burden) / Total`"],
    ]
    md_lines.append(build_markdown_table(overall_headers, overall_rows, overall_alignments))
    md_lines.append("")

    # Per-Rule Table
    md_lines.extend([
        "## Per-Rule Breakdown",
        "",
    ])
    rule_headers = [
        "Rule", "Total", "TP", "FN", "Caught", "FP", "Burden", "TN",
        "Precision", "Recall", "Recall (w/ Rev)", "False Alarm Rate", "Review Rate",
    ]
    rule_alignments = ["left"] + ["right"] * 12
    rule_rows = []
    for r_id in sorted(per_rule.keys()):
        m = per_rule[r_id]
        rule_rows.append([
            r_id,
            str(m["total"]),
            str(m["tp"]),
            str(m["fn"]),
            str(m["caught"]),
            str(m["fp"]),
            str(m["review_burden"]),
            str(m["tn"]),
            format_pct(m["precision"]),
            format_pct(m["recall"]),
            format_pct(m["recall_with_review"]),
            format_pct(m["false_alarm_rate"]),
            format_pct(m["review_rate"]),
        ])
    md_lines.append(build_markdown_table(rule_headers, rule_rows, rule_alignments))
    md_lines.append("")

    # Per-Product Table
    md_lines.extend([
        "## Per-Product Breakdown",
        "",
    ])
    prod_headers = [
        "Product", "Total", "TP", "FN", "Caught", "FP", "Burden", "TN",
        "Precision", "Recall", "Recall (w/ Rev)", "False Alarm Rate", "Review Rate",
    ]
    prod_alignments = ["left"] + ["right"] * 12
    prod_rows = []
    for prod in sorted(per_product.keys()):
        m = per_product[prod]
        prod_rows.append([
            prod,
            str(m["total"]),
            str(m["tp"]),
            str(m["fn"]),
            str(m["caught"]),
            str(m["fp"]),
            str(m["review_burden"]),
            str(m["tn"]),
            format_pct(m["precision"]),
            format_pct(m["recall"]),
            format_pct(m["recall_with_review"]),
            format_pct(m["false_alarm_rate"]),
            format_pct(m["review_rate"]),
        ])
    md_lines.append(build_markdown_table(prod_headers, prod_rows, prod_alignments))
    md_lines.append("")

    # Wrong Predictions Table
    md_lines.extend([
        f"## Wrong Predictions ({len(wrong_preds)})",
        "",
    ])
    if not wrong_preds:
        md_lines.append("*(None! All predictions matched expected ground truth)*\n")
    else:
        wp_headers = ["Image", "Rule", "Expected", "Predicted", "Found Value"]
        wp_alignments = ["left", "left", "left", "left", "left"]
        wp_rows = []
        for wp in wrong_preds:
            found_str = str(wp["found"]).replace("\n", " ").replace("|", "\\|").strip()
            if not found_str:
                found_str = "*(empty)*"
            wp_rows.append([
                wp["image"],
                wp["rule"],
                wp["expected"],
                wp["predicted"],
                found_str,
            ])
        md_lines.append(build_markdown_table(wp_headers, wp_rows, wp_alignments))
        md_lines.append("")

    return "\n".join(md_lines)


def save_evaluation_results(result: Dict[str, Any]) -> Tuple[str, str]:
    """
    Saves outputs to:
    - outputs/eval_<split>.json
    - outputs/eval_<split>.md
    Returns tuple of file paths.
    """
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    split = result["split"]

    json_path = os.path.join(OUTPUTS_DIR, f"eval_{split}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    md_content = generate_markdown_report(result)
    md_path = os.path.join(OUTPUTS_DIR, f"eval_{split}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate packaging compliance pipeline against ground-truth dataset."
    )
    parser.add_argument(
        "--split",
        choices=["dev", "test", "all"],
        default="dev",
        help="Dataset split to evaluate (dev, test, or all; default: dev)",
    )
    args = parser.parse_args()

    result = evaluate_split(args.split)
    print_evaluation_report(result)
    json_path, md_path = save_evaluation_results(result)
    print(f"Evaluation results successfully saved to:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")


if __name__ == "__main__":
    main()

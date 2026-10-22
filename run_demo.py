"""
Demo script running the compliance pipeline on clean and error biscuit packaging images.
"""

import os
from pipeline import check_image


def print_findings_table(image_name: str, findings: list) -> None:
    """Prints findings list as a readable, formatted text table."""
    print("\n" + "=" * 90)
    print(f"Artwork Compliance Findings: {image_name}")
    print("=" * 90)
    header = f"{'Rule':<6} | {'Verdict':<12} | {'Found':<24} | {'Expected':<22} | {'Reason'}"
    print(header)
    print("-" * 90)

    for item in findings:
        rule_id = item["rule_id"]
        verdict = item["verdict"]
        found = str(item["found"]).replace("\n", " ")
        if len(found) > 22:
            found = found[:19] + "..."
        expected = str(item["expected"]).replace("\n", " ")
        if len(expected) > 20:
            expected = expected[:17] + "..."
        reason = item["reason"]
        print(f"{rule_id:<6} | {verdict:<12} | {found:<24} | {expected:<22} | {reason}")

    print("=" * 90)


def main():
    images_dir = os.path.join("dataset", "images")
    spec_path = os.path.join("dataset", "specs", "biscuit.json")

    demo_images = [
        "biscuit_clean1.png",
        "biscuit_errR05.png",
    ]

    for img_name in demo_images:
        img_path = os.path.join(images_dir, img_name)
        print(f"\nProcessing {img_name}...")
        findings = check_image(img_path, spec_path)
        print_findings_table(img_name, findings)


if __name__ == "__main__":
    main()

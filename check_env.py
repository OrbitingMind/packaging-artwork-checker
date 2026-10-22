"""
check_env.py
Verifies the Python environment setup for the packaging artwork checker:
1. Imports all required third-party packages.
2. Loads environment variables from .env and checks ANTHROPIC_API_KEY.
3. Runs the test suite via pytest.

Security rule: ANTHROPIC_API_KEY is never printed or logged, only its presence is reported.
"""

import importlib
import os
import sys

# Mapping of (importable_module_name, package_display_name)
REQUIRED_PACKAGES = [
    ("yaml", "pyyaml"),
    ("pytest", "pytest"),
    ("PIL", "pillow"),
    ("dotenv", "python-dotenv"),
    ("anthropic", "anthropic"),
    ("easyocr", "easyocr"),
    ("streamlit", "streamlit"),
    ("cv2", "opencv-python-headless"),
]


def check_packages() -> bool:
    """Attempt to import each required module and print OK / FAILED."""
    print("=== Checking Required Packages ===")
    all_ok = True

    for module_name, package_name in REQUIRED_PACKAGES:
        try:
            # In Python, importlib.import_module() allows dynamic importing
            # similar to dlopen / runtime symbol resolution.
            importlib.import_module(module_name)
            print(f"{package_name}: OK")
        except Exception as exc:
            print(f"{package_name}: FAILED ({exc})")
            all_ok = False

    return all_ok


def check_env_key() -> bool:
    """Load .env file and check if ANTHROPIC_API_KEY is present and non-empty."""
    print("\n=== Checking Environment Variables ===")

    # python-dotenv parses .env file and injects key-value pairs into os.environ
    from dotenv import load_dotenv

    load_dotenv()

    # SECURITY CONSTRAINT:
    # We only check for presence and non-emptiness.
    # Never print, log, or expose the key value.
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key and key.strip():
        print("ANTHROPIC_API_KEY: found")
        return True
    else:
        print("ANTHROPIC_API_KEY: missing")
        return False


def run_tests() -> int:
    """Run pytest suite programmatically and return the exit code."""
    print("\n=== Running pytest Suite ===")
    import pytest

    # pytest.main accepts command-line arguments as a list of strings.
    # Returns 0 on success (all tests pass), non-zero on failure.
    return pytest.main(["-v"])


def main():
    packages_ok = check_packages()
    key_found = check_env_key()

    if not packages_ok:
        print("\n[ERROR] One or more packages failed to import. Fix dependencies before running tests.")
        sys.exit(1)

    if not key_found:
        print("\n[WARNING] ANTHROPIC_API_KEY is missing or empty in .env.")

    # Run the test suite
    test_exit_code = run_tests()
    if test_exit_code != 0:
        print(f"\n[ERROR] pytest exited with status code {test_exit_code}")
        sys.exit(int(test_exit_code))

    print("\n[SUCCESS] Environment check passed successfully!")


if __name__ == "__main__":
    main()

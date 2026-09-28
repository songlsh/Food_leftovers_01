import os
import sys
import subprocess
from test_suite_config import TEST_CASES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    passed = 0
    failed = 0

    print("=" * 60)
    print("SLS Unified Test Runner")
    print("Version: V31_3_12")
    print("=" * 60)

    for item in TEST_CASES:
        print("\n>>>", item["name"])
        result = subprocess.run(
            [sys.executable, item["file"]],
            cwd=ROOT
        )

        if result.returncode == 0:
            passed += 1
            print(item["name"], "PASS")
        else:
            failed += 1
            print(item["name"], "FAIL")

    print("=" * 60)
    print("PASS:", passed)
    print("FAIL:", failed)
    print("RESULT:", "SUCCESS" if failed == 0 else "FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()

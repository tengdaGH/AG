# ============================================================
# Purpose:       CLI wrapper for prompt_schema.enforce_all().
#                Scans every test_items row and normalises field names.
# Usage:         python -m app.scripts.enforce_schema          # dry-run
#                python -m app.scripts.enforce_schema --apply  # write fixes
# Created:       2026-02-27
# Self-Destruct: No
# ============================================================
"""
Enforce canonical prompt_content schema across the entire item bank.

Run without args for a dry-run report; pass --apply to write the fixes.
"""
import argparse
import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.prompt_schema import enforce_all

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../item_bank.db"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Enforce prompt_content schema normalisation.")
    parser.add_argument("--apply", action="store_true", help="Write fixes to the database (default: dry-run).")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[enforce_schema] mode={mode}  db={DB_PATH}")

    result = enforce_all(DB_PATH, dry_run=not args.apply)

    print(f"\nScanned:  {result['scanned']} items")
    print(f"Modified: {result['modified']} items")

    if result["details"]:
        print("\nDetails:")
        for d in result["details"]:
            fixes_str = ", ".join(d["fixes"])
            print(f"  [{d['id'][:8]}] {fixes_str}")
    else:
        print("\n✅ All items already conform to canonical schema.")


if __name__ == "__main__":
    main()

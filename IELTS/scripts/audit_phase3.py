#!/usr/bin/env python3
"""
audit_phase3.py
================
Phase 3 of the IELTS Item Bank Audit.

Controlled Integration: deduplication + staging upload.

Checks:
  1. Title-based deduplication (case-insensitive exact match + slug match)
  2. Slug deduplication (any slug used more than once)
  3. DB collision check — queries ielts_passages table for existing source_ids
  4. Copies all clean items (from parsed_v2/) into a staging/ directory

Reads from:
  - IELTS/parsed_v2/*.json
  - IELTS/audit_phase1_report.json (to exclude critical failures)

Location : /Users/tengda/Antigravity/IELTS/scripts/
Run      : python /Users/tengda/Antigravity/IELTS/scripts/audit_phase3.py
"""

import os
import json
import shutil
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PARSED_V2_DIR     = "/Users/tengda/Antigravity/IELTS/parsed_v2"
STAGING_DIR       = "/Users/tengda/Antigravity/IELTS/staging"
REPORT_PATH       = "/Users/tengda/Antigravity/IELTS/audit_phase3_report.json"
PHASE1_REPORT     = "/Users/tengda/Antigravity/IELTS/audit_phase1_report.json"

# DB config for collision check (optional — graceful degradation if unavailable)
DB_MODULE_PATH    = "/Users/tengda/Antigravity/toefl-2026/backend"


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def normalize_title(title):
    """Normalize for comparison: lowercase, strip whitespace."""
    if not title:
        return ""
    return " ".join(title.lower().split())


def check_db_collisions(parsed_ids):
    """
    Check if any source_id already exists in the ielts_passages DB table.
    Returns (list of collisions, error_message_or_None)
    """
    try:
        sys.path.insert(0, DB_MODULE_PATH)
        from app.database.connection import SessionLocal
        from app.models.models import IeltsPassage

        db = SessionLocal()
        existing = db.query(IeltsPassage.source_id).all()
        db.close()

        existing_ids = {row[0] for row in existing}
        collisions = [pid for pid in parsed_ids if pid in existing_ids]
        return collisions, None

    except ImportError as e:
        return [], f"DB module not available (skipping): {e}"
    except Exception as e:
        return [], f"DB query failed (skipping): {e}"


def main():
    print("=" * 70)
    print("Phase 3 Audit: Deduplication & Controlled Staging")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # ---------------------------------------------------------------------------
    # Load Phase 1 report to know which files have critical failures
    # ---------------------------------------------------------------------------
    critical_files = set()
    p1_data, p1_err = load_json(PHASE1_REPORT)
    if p1_err:
        print(f"⚠️  Could not load Phase 1 report: {p1_err}")
        print("   Will stage all parsed_v2 files without Phase 1 filtering.")
    else:
        p1_issues = p1_data.get("parsed_files_with_issues", {})
        for fname, result in p1_issues.items():
            for issue in result.get("issues", []):
                issue_lower = issue.lower()
                if any(kw in issue_lower for kw in ["empty", "missing key", "load error", "not a dict"]):
                    critical_files.add(fname)
                    break
        print(f"\nPhase 1 critical failures (will be excluded from staging): {len(critical_files)}")

    # ---------------------------------------------------------------------------
    # Load all parsed_v2 files
    # ---------------------------------------------------------------------------
    parsed_files = sorted(f for f in os.listdir(PARSED_V2_DIR) if f.endswith(".json"))
    print(f"Total parsed_v2 files: {len(parsed_files)}")

    all_items = []
    load_errors = []

    for filename in parsed_files:
        fpath = os.path.join(PARSED_V2_DIR, filename)
        data, err = load_json(fpath)
        if err:
            load_errors.append({"filename": filename, "error": err})
            continue
        all_items.append({
            "filename": filename,
            "id": data.get("id", ""),
            "slug": data.get("slug", ""),
            "title": data.get("title", ""),
            "title_normalized": normalize_title(data.get("title", "")),
            "is_critical": filename in critical_files,
        })

    print(f"Successfully loaded: {len(all_items)} files")
    print(f"Load errors        : {len(load_errors)}")

    # ---------------------------------------------------------------------------
    # Check 1: Slug deduplication
    # ---------------------------------------------------------------------------
    slug_map = {}
    for item in all_items:
        slug = item["slug"]
        if slug:
            if slug not in slug_map:
                slug_map[slug] = []
            slug_map[slug].append(item["filename"])

    duplicate_slugs = {slug: files for slug, files in slug_map.items() if len(files) > 1}
    print(f"\n[1/3] Duplicate slugs : {len(duplicate_slugs)}")
    for slug, files in list(duplicate_slugs.items())[:10]:
        print(f"  slug='{slug}': {files}")

    # ---------------------------------------------------------------------------
    # Check 2: Title deduplication
    # ---------------------------------------------------------------------------
    title_map = {}
    for item in all_items:
        t = item["title_normalized"]
        if t:
            if t not in title_map:
                title_map[t] = []
            title_map[t].append(item["filename"])

    duplicate_titles = {t: files for t, files in title_map.items() if len(files) > 1}
    print(f"\n[2/3] Duplicate titles: {len(duplicate_titles)}")
    for title, files in list(duplicate_titles.items())[:10]:
        print(f"  title='{title[:60]}': {files}")

    # ---------------------------------------------------------------------------
    # Check 3: DB collision check
    # ---------------------------------------------------------------------------
    all_source_ids = [item["id"] for item in all_items if item["id"]]
    print(f"\n[3/3] Checking DB for existing source_ids...")
    db_collisions, db_err = check_db_collisions(all_source_ids)
    if db_err:
        print(f"  ℹ️  {db_err}")
    else:
        print(f"  DB collisions found: {len(db_collisions)}")
        for c in db_collisions[:10]:
            print(f"    - {c}")

    # ---------------------------------------------------------------------------
    # Build the set of files to exclude from staging
    # ---------------------------------------------------------------------------
    # Exclude: critical failures, load errors, and KEEP only the first of any duplicates
    excluded_from_staging = set(critical_files)
    excluded_from_staging.update(item["filename"] for item in load_errors
                                  if isinstance(item, dict))

    # For duplicate slugs: keep first alphabetically, exclude rest
    slug_excluded = set()
    for slug, files in duplicate_slugs.items():
        # Keep first, skip rest
        for f in sorted(files)[1:]:
            slug_excluded.add(f)

    print(f"\nSlugs excluded (duplicates, keeping first): {len(slug_excluded)}")
    excluded_from_staging.update(slug_excluded)

    # For duplicate titles: same logic
    title_excluded = set()
    for title, files in duplicate_titles.items():
        for f in sorted(files)[1:]:
            title_excluded.add(f)

    print(f"Titles excluded (duplicates, keeping first): {len(title_excluded)}")
    excluded_from_staging.update(title_excluded)

    # DB collisions: exclude all
    db_collision_files = set()
    for source_id in db_collisions:
        for item in all_items:
            if item["id"] == source_id:
                db_collision_files.add(item["filename"])

    excluded_from_staging.update(db_collision_files)

    # ---------------------------------------------------------------------------
    # Stage valid items
    # ---------------------------------------------------------------------------
    os.makedirs(STAGING_DIR, exist_ok=True)

    # Clear staging dir first
    for f in os.listdir(STAGING_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(STAGING_DIR, f))

    staged = []
    skipped = []

    for filename in parsed_files:
        src = os.path.join(PARSED_V2_DIR, filename)
        dst = os.path.join(STAGING_DIR, filename)

        if filename in excluded_from_staging:
            reason = []
            if filename in critical_files:
                reason.append("schema_critical_failure")
            if filename in slug_excluded:
                reason.append("duplicate_slug")
            if filename in title_excluded:
                reason.append("duplicate_title")
            if filename in db_collision_files:
                reason.append("db_collision")
            skipped.append({"filename": filename, "reasons": reason})
        else:
            shutil.copy2(src, dst)
            staged.append(filename)

    print(f"\nStaged to {STAGING_DIR}: {len(staged)} files")
    print(f"Skipped               : {len(skipped)} files")

    # ---------------------------------------------------------------------------
    # Write report
    # ---------------------------------------------------------------------------
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_parsed_v2_files": len(parsed_files),
            "successfully_staged": len(staged),
            "excluded_total": len(skipped),
            "excluded_reasons": {
                "schema_critical_failures": len(critical_files),
                "duplicate_slugs": len(slug_excluded),
                "duplicate_titles": len(title_excluded),
                "db_collisions": len(db_collisions),
                "load_errors": len(load_errors),
            },
        },
        "duplicate_slugs": {slug: files for slug, files in duplicate_slugs.items()},
        "duplicate_titles": {t: files for t, files in duplicate_titles.items()},
        "db_collisions": db_collisions if not db_err else [],
        "db_check_error": db_err,
        "staged_files": staged,
        "skipped_files": skipped,
        "load_errors": load_errors,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport written to: {REPORT_PATH}")
    print("\n" + "=" * 70)
    print("PHASE 3 SUMMARY")
    print("=" * 70)
    print(f"  ✅ Staged (ready for DB)  : {len(staged)}")
    print(f"  🔁 Duplicate slugs        : {len(duplicate_slugs)}")
    print(f"  🔁 Duplicate titles       : {len(duplicate_titles)}")
    print(f"  🗄️  DB collisions          : {len(db_collisions)}")
    print(f"  ❌ Excluded total         : {len(skipped)}")
    print(f"  📁 Staging dir            : {STAGING_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    main()

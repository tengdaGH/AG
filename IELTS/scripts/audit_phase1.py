#!/usr/bin/env python3
"""
audit_phase1.py
================
Phase 1 of the IELTS Item Bank Audit.

Schema Consistency & Data Integrity checks across all 651 items.

Checks:
  1. Missing processed files (in extracted/ but not in parsed_v2/)
  2. Required key presence in parsed_v2 files
  3. Empty / truncated fields
  4. Answer key integrity (raw_answer_key count == parsed_total_questions)
  5. ID uniqueness across all parsed_v2 files

Location : /Users/tengda/Antigravity/IELTS/scripts/
Run      : python /Users/tengda/Antigravity/IELTS/scripts/audit_phase1.py
"""

import os
import json
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EXTRACTED_DIR  = "/Users/tengda/Antigravity/IELTS/extracted"
PARSED_V2_DIR  = "/Users/tengda/Antigravity/IELTS/parsed_v2"
REPORT_PATH    = "/Users/tengda/Antigravity/IELTS/audit_phase1_report.json"

REQUIRED_KEYS_EXTRACTED = [
    "id", "slug", "title", "page_range",
    "passage_text", "answer_key", "extracted_at"
]

REQUIRED_KEYS_PARSED = [
    "id", "slug", "title", "page_range",
    "raw_answer_key", "content", "questions", "processed_at"
]

MIN_PASSAGE_WORDS = 30   # absolute minimum — anything below this is suspect


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"
    except Exception as e:
        return None, f"Read error: {e}"


def audit_extracted(filename, data):
    """Audit a single extracted/*.json file for basic sanity."""
    issues = []
    for key in REQUIRED_KEYS_EXTRACTED:
        if key not in data:
            issues.append(f"Missing key: {key}")

    passage_text = data.get("passage_text", "")
    word_count = len(passage_text.split()) if passage_text else 0
    if word_count < MIN_PASSAGE_WORDS:
        issues.append(f"passage_text too short: {word_count} words")

    if not data.get("answer_key"):
        issues.append("answer_key is empty or missing")

    if not data.get("question_sections"):
        # Not fatal — question_sections is optional metadata
        pass

    return {"word_count": word_count, "issues": issues}


def audit_parsed(filename, data):
    """Audit a single parsed_v2/*.json file for schema compliance."""
    issues = []

    # Check required top-level keys
    for key in REQUIRED_KEYS_PARSED:
        if key not in data:
            issues.append(f"Missing key: {key}")

    # Check content structure
    content = data.get("content", {})
    if not isinstance(content, dict):
        issues.append("content is not a dict")
    else:
        paragraphs = content.get("paragraphs", [])
        if not isinstance(paragraphs, list) or len(paragraphs) == 0:
            issues.append("content.paragraphs is empty or missing")
        else:
            # Check each paragraph has at least a 'content' field
            for i, p in enumerate(paragraphs):
                if not isinstance(p, dict) or not p.get("content"):
                    issues.append(f"paragraph[{i}] missing 'content' field")

    # Check questions structure
    questions = data.get("questions", {})
    if not isinstance(questions, dict):
        issues.append("questions is not a dict")
    else:
        groups = questions.get("question_groups", [])
        if not isinstance(groups, list) or len(groups) == 0:
            issues.append("questions.question_groups is empty or missing")
        else:
            total_parsed = 0
            for gi, group in enumerate(groups):
                qs = group.get("questions", [])
                if not isinstance(qs, list) or len(qs) == 0:
                    issues.append(f"question_group[{gi}] ({group.get('type', '?')}) has no questions")
                total_parsed += len(qs)

            # Check parsed_total_questions consistency
            declared_total = questions.get("parsed_total_questions", -1)
            if declared_total != total_parsed:
                issues.append(
                    f"parsed_total_questions mismatch: declared={declared_total}, actual={total_parsed}"
                )

        # Answer key integrity
        raw_key = data.get("raw_answer_key", {})
        declared_total = questions.get("parsed_total_questions", -1)
        raw_key_count = len(raw_key) if isinstance(raw_key, dict) else 0
        if raw_key_count != declared_total and raw_key_count > 0:
            issues.append(
                f"raw_answer_key count ({raw_key_count}) != parsed_total_questions ({declared_total})"
            )

    return {"issues": issues}


def main():
    print("=" * 70)
    print("Phase 1 Audit: Schema Consistency & Data Integrity")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # Gather all file lists
    extracted_files = {f for f in os.listdir(EXTRACTED_DIR) if f.endswith(".json")}
    parsed_files    = {f for f in os.listdir(PARSED_V2_DIR)  if f.endswith(".json")}

    missing_from_parsed = sorted(extracted_files - parsed_files)
    extra_in_parsed     = sorted(parsed_files - extracted_files)

    print(f"\nExtracted files   : {len(extracted_files)}")
    print(f"Parsed v2 files   : {len(parsed_files)}")
    print(f"Missing from parsed_v2: {len(missing_from_parsed)}")
    print(f"Extra in parsed_v2   : {len(extra_in_parsed)}")

    # ---------------------------------------------------------------------------
    # Audit extracted files
    # ---------------------------------------------------------------------------
    print("\n[1/4] Auditing extracted/*.json files...")
    extracted_results = {}
    extracted_issues_count = 0
    for filename in sorted(extracted_files):
        fpath = os.path.join(EXTRACTED_DIR, filename)
        data, err = load_json(fpath)
        if err:
            extracted_results[filename] = {"error": err, "word_count": 0, "issues": [f"Load error: {err}"]}
            extracted_issues_count += 1
            continue
        result = audit_extracted(filename, data)
        extracted_results[filename] = result
        if result["issues"]:
            extracted_issues_count += 1

    print(f"   Extracted files with issues: {extracted_issues_count}/{len(extracted_files)}")

    # ---------------------------------------------------------------------------
    # Audit parsed_v2 files
    # ---------------------------------------------------------------------------
    print("\n[2/4] Auditing parsed_v2/*.json files...")
    parsed_results = {}
    parsed_issues_count = 0
    seen_ids = {}
    duplicate_ids = []

    for filename in sorted(parsed_files):
        fpath = os.path.join(PARSED_V2_DIR, filename)
        data, err = load_json(fpath)
        if err:
            parsed_results[filename] = {"error": err, "issues": [f"Load error: {err}"]}
            parsed_issues_count += 1
            continue
        result = audit_parsed(filename, data)
        parsed_results[filename] = result
        if result["issues"]:
            parsed_issues_count += 1

        # Check ID uniqueness
        file_id = data.get("id", "")
        if file_id in seen_ids:
            duplicate_ids.append({"id": file_id, "files": [seen_ids[file_id], filename]})
        else:
            seen_ids[file_id] = filename

    print(f"   Parsed files with issues : {parsed_issues_count}/{len(parsed_files)}")
    print(f"   Duplicate IDs found      : {len(duplicate_ids)}")

    # ---------------------------------------------------------------------------
    # Detailed issue summary
    # ---------------------------------------------------------------------------
    print("\n[3/4] Categorizing issues...")

    # Files with critical failures in parsed_v2
    critical_failures = {
        f: r for f, r in parsed_results.items()
        if any(
            kw in issue for issue in r.get("issues", [])
            for kw in ["empty", "missing", "Load error", "not a dict"]
        )
    }

    # Files missing from parsed_v2 (LLM never processed them)
    print(f"\n   Files missing from parsed_v2 ({len(missing_from_parsed)}):")
    for f in missing_from_parsed[:20]:
        print(f"     - {f}")
    if len(missing_from_parsed) > 20:
        print(f"     ... and {len(missing_from_parsed) - 20} more")

    # Build issue-type counts
    issue_type_counts = {}
    for r in parsed_results.values():
        for issue in r.get("issues", []):
            # Bucket by prefix
            if "Missing key" in issue:
                key = "missing_key"
            elif "parsed_total_questions mismatch" in issue:
                key = "answer_count_mismatch"
            elif "empty or missing" in issue:
                key = "empty_field"
            elif "raw_answer_key count" in issue:
                key = "raw_answer_key_mismatch"
            elif "paragraph" in issue:
                key = "bad_paragraph"
            elif "question_group" in issue:
                key = "empty_question_group"
            elif "Load error" in issue:
                key = "load_error"
            else:
                key = "other"
            issue_type_counts[key] = issue_type_counts.get(key, 0) + 1

    print(f"\n   Issue type breakdown (parsed_v2):")
    for issue_type, count in sorted(issue_type_counts.items(), key=lambda x: -x[1]):
        print(f"     {issue_type:40s}: {count}")

    # ---------------------------------------------------------------------------
    # Build full report
    # ---------------------------------------------------------------------------
    print("\n[4/4] Writing report...")

    # Classify parsed files into clean/warn/critical
    clean_files = []
    warn_files  = []
    crit_files  = []

    for f, r in parsed_results.items():
        issues = r.get("issues", [])
        if not issues:
            clean_files.append(f)
        elif any("empty" in i.lower() or "missing key" in i.lower() or "load error" in i.lower() or "not a dict" in i.lower() for i in issues):
            crit_files.append(f)
        else:
            warn_files.append(f)

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_extracted_files": len(extracted_files),
            "total_parsed_v2_files": len(parsed_files),
            "missing_from_parsed_v2": len(missing_from_parsed),
            "extra_in_parsed_v2": len(extra_in_parsed),
            "extracted_files_with_issues": extracted_issues_count,
            "parsed_files_clean": len(clean_files),
            "parsed_files_warn": len(warn_files),
            "parsed_files_critical": len(crit_files),
            "duplicate_ids": len(duplicate_ids),
            "issue_type_counts": issue_type_counts,
        },
        "missing_from_parsed_v2": missing_from_parsed,
        "extra_in_parsed_v2": extra_in_parsed,
        "duplicate_ids": duplicate_ids,
        "parsed_files_with_issues": {
            f: r for f, r in parsed_results.items() if r.get("issues")
        },
        "extracted_files_with_issues": {
            f: r for f, r in extracted_results.items() if r.get("issues")
        },
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport written to: {REPORT_PATH}")
    print("\n" + "=" * 70)
    print("PHASE 1 SUMMARY")
    print("=" * 70)
    print(f"  Total extracted    : {len(extracted_files)}")
    print(f"  Total parsed_v2   : {len(parsed_files)}")
    print(f"  Missing (not proc) : {len(missing_from_parsed)}")
    print(f"  ✅ Clean           : {len(clean_files)}")
    print(f"  ⚠️  Warn (minor)    : {len(warn_files)}")
    print(f"  ❌ Critical        : {len(crit_files)}")
    print(f"  🔁 Duplicate IDs   : {len(duplicate_ids)}")
    print("=" * 70)


if __name__ == "__main__":
    main()

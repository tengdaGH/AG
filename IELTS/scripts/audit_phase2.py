#!/usr/bin/env python3
"""
audit_phase2.py
================
Phase 2 of the IELTS Item Bank Audit.

Pedagogical Spec Audit: checks whether passages and question sets conform
to IELTS Academic Reading standards.

Checks:
  1. Passage word count (target: 700–900 words for full passages)
  2. Question count per passage (target: 13–14)
  3. Question type coverage (must have ≥ 1 structured question group)
  4. Mini-passage classification (50–350 words, single MCQ — valid but flagged)

Reads from:
  - IELTS/extracted/*.json  (for passage_text word counts)
  - IELTS/parsed_v2/*.json  (for structured question group analysis)

Location : /Users/tengda/Antigravity/IELTS/scripts/
Run      : python /Users/tengda/Antigravity/IELTS/scripts/audit_phase2.py
"""

import os
import json
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EXTRACTED_DIR = "/Users/tengda/Antigravity/IELTS/extracted"
PARSED_V2_DIR = "/Users/tengda/Antigravity/IELTS/parsed_v2"
REPORT_PATH   = "/Users/tengda/Antigravity/IELTS/audit_phase2_report.json"

# IELTS Academic Full Passage spec
WORD_COUNT_MIN_IDEAL    = 700
WORD_COUNT_MAX_IDEAL    = 900
WORD_COUNT_MIN_CRITICAL = 50    # anything below this is definitely wrong
WORD_COUNT_MAX_CRITICAL = 1400  # anything above suggests merged/double passage
MINI_PASSAGE_MAX        = 350   # short paragraph-style items
QUESTION_COUNT_MIN      = 10    # minimum acceptable (excluding mini-passages)
QUESTION_COUNT_MAX      = 20    # maximum acceptable
QUESTION_COUNT_IDEAL_LO = 13
QUESTION_COUNT_IDEAL_HI = 14


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def word_count(text):
    """Count words in a string, stripping whitespace tokens."""
    if not text:
        return 0
    return len([w for w in text.split() if w.strip()])


def passage_word_count_from_extracted(data):
    """Use passage_text (not full_text) to avoid contaminating with question text."""
    passage_text = data.get("passage_text", "")
    return word_count(passage_text)


def analyze_questions(parsed_data):
    """Return question count and list of unique question types from parsed_v2."""
    qs = parsed_data.get("questions", {})
    groups = qs.get("question_groups", [])
    total = qs.get("parsed_total_questions", 0)
    types = list({g.get("type", "UNKNOWN") for g in groups})
    return total, types


def classify_passage(wc, q_count):
    """Return a classification string based on passage characteristics."""
    if wc < WORD_COUNT_MIN_CRITICAL:
        return "EMPTY_OR_STUB"
    elif wc <= MINI_PASSAGE_MAX:
        return "MINI_PASSAGE"
    elif WORD_COUNT_MIN_IDEAL <= wc <= WORD_COUNT_MAX_IDEAL:
        if QUESTION_COUNT_IDEAL_LO <= q_count <= QUESTION_COUNT_IDEAL_HI:
            return "IDEAL"
        else:
            return "WARN_QUESTION_COUNT"
    elif wc > WORD_COUNT_MAX_CRITICAL:
        return "WARN_OVERSIZED"
    else:
        return "WARN_WORD_COUNT"


def main():
    print("=" * 70)
    print("Phase 2 Audit: Pedagogical Spec Compliance")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    extracted_files = sorted(f for f in os.listdir(EXTRACTED_DIR) if f.endswith(".json"))
    parsed_files_set = set(f for f in os.listdir(PARSED_V2_DIR) if f.endswith(".json"))

    results = []
    classification_counts = {}
    type_distribution = {}

    print(f"\nAnalyzing {len(extracted_files)} extracted items...")

    for filename in extracted_files:
        item_id = filename.replace(".json", "")

        # Load extracted for word count
        ext_path = os.path.join(EXTRACTED_DIR, filename)
        ext_data, ext_err = load_json(ext_path)

        wc = 0
        if ext_data and not ext_err:
            wc = passage_word_count_from_extracted(ext_data)

        # Load parsed_v2 for question analysis
        q_count = 0
        q_types = []
        has_parsed = filename in parsed_files_set
        if has_parsed:
            prs_path = os.path.join(PARSED_V2_DIR, filename)
            prs_data, prs_err = load_json(prs_path)
            if prs_data and not prs_err:
                q_count, q_types = analyze_questions(prs_data)

        # Classify
        classification = classify_passage(wc, q_count) if has_parsed else "NOT_PROCESSED"
        classification_counts[classification] = classification_counts.get(classification, 0) + 1

        # Track question type distribution
        for qt in q_types:
            type_distribution[qt] = type_distribution.get(qt, 0) + 1

        # Determine pedagogical issues
        issues = []
        if wc < WORD_COUNT_MIN_CRITICAL:
            issues.append(f"CRITICAL: passage_text too short ({wc} words)")
        elif wc <= MINI_PASSAGE_MAX:
            issues.append(f"MINI_PASSAGE: {wc} words — likely single-MCQ item")
        elif wc < WORD_COUNT_MIN_IDEAL:
            issues.append(f"WARN: passage below ideal length ({wc} words, target 700+)")
        elif wc > WORD_COUNT_MAX_CRITICAL:
            issues.append(f"WARN: passage may be merged/oversized ({wc} words)")

        if has_parsed:
            if q_count < QUESTION_COUNT_MIN and classification != "MINI_PASSAGE":
                issues.append(f"CRITICAL: too few questions ({q_count}, min {QUESTION_COUNT_MIN})")
            elif q_count > QUESTION_COUNT_MAX:
                issues.append(f"WARN: too many questions ({q_count}, max {QUESTION_COUNT_MAX})")
            if not q_types:
                issues.append("CRITICAL: no question types parsed")

        results.append({
            "id": item_id,
            "filename": filename,
            "word_count": wc,
            "question_count": q_count,
            "question_types": q_types,
            "classification": classification,
            "has_parsed_v2": has_parsed,
            "issues": issues,
        })

    # ---------------------------------------------------------------------------
    # Summary statistics
    # ---------------------------------------------------------------------------
    word_counts_all = [r["word_count"] for r in results if r["word_count"] > 0]
    q_counts_full   = [r["question_count"] for r in results if r["classification"] not in ("MINI_PASSAGE", "NOT_PROCESSED", "EMPTY_OR_STUB")]
    q_counts_mini   = [r["question_count"] for r in results if r["classification"] == "MINI_PASSAGE"]

    def safe_avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0

    print(f"\nPassage word count statistics (all {len(word_counts_all)} items with text):")
    if word_counts_all:
        print(f"  Min   : {min(word_counts_all)}")
        print(f"  Max   : {max(word_counts_all)}")
        print(f"  Avg   : {safe_avg(word_counts_all)}")

    print(f"\nClassification breakdown:")
    for cls, cnt in sorted(classification_counts.items(), key=lambda x: -x[1]):
        print(f"  {cls:30s}: {cnt}")

    print(f"\nQuestion type distribution across all parsed items:")
    for qt, cnt in sorted(type_distribution.items(), key=lambda x: -x[1]):
        print(f"  {qt:45s}: {cnt}")

    print(f"\nQuestion count — full passages (avg): {safe_avg(q_counts_full)}")
    print(f"Question count — mini passages (avg) : {safe_avg(q_counts_mini)}")

    # Items with issues
    items_with_issues = [r for r in results if r["issues"]]
    print(f"\nItems with pedagogical issues: {len(items_with_issues)}")

    # ---------------------------------------------------------------------------
    # Write report
    # ---------------------------------------------------------------------------
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_analyzed": len(results),
            "total_with_parsed_v2": sum(1 for r in results if r["has_parsed_v2"]),
            "classification_counts": classification_counts,
            "question_type_distribution": type_distribution,
            "word_count_stats": {
                "min": min(word_counts_all) if word_counts_all else 0,
                "max": max(word_counts_all) if word_counts_all else 0,
                "avg": safe_avg(word_counts_all),
            },
            "question_count_stats_full_passages": {
                "min": min(q_counts_full) if q_counts_full else 0,
                "max": max(q_counts_full) if q_counts_full else 0,
                "avg": safe_avg(q_counts_full),
            },
            "items_with_issues": len(items_with_issues),
        },
        "items_with_issues": [
            {
                "id": r["id"],
                "word_count": r["word_count"],
                "question_count": r["question_count"],
                "classification": r["classification"],
                "issues": r["issues"],
            }
            for r in items_with_issues
        ],
        "all_items": results,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport written to: {REPORT_PATH}")
    print("\n" + "=" * 70)
    print("PHASE 2 SUMMARY")
    print("=" * 70)
    ideal = classification_counts.get("IDEAL", 0)
    mini  = classification_counts.get("MINI_PASSAGE", 0)
    warn  = sum(v for k, v in classification_counts.items() if k.startswith("WARN"))
    crit  = sum(v for k, v in classification_counts.items() if "STUB" in k or "NOT_PROCESSED" in k)
    print(f"  ✅ Ideal (700-900w, 13-14q) : {ideal}")
    print(f"  📎 Mini passages (≤350w)    : {mini}")
    print(f"  ⚠️  Warn                     : {warn}")
    print(f"  ❌ Critical / Not Processed  : {crit}")
    print("=" * 70)


if __name__ == "__main__":
    main()

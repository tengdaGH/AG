#!/usr/bin/env python3
"""
generate_audit_report.py
=========================
Reads the three phase audit JSON reports and generates a comprehensive
human-readable Markdown summary report.

Location : /Users/tengda/Antigravity/IELTS/scripts/
Run      : python /Users/tengda/Antigravity/IELTS/scripts/generate_audit_report.py
"""

import os
import json
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PHASE1_REPORT = "/Users/tengda/Antigravity/IELTS/audit_phase1_report.json"
PHASE2_REPORT = "/Users/tengda/Antigravity/IELTS/audit_phase2_report.json"
PHASE3_REPORT = "/Users/tengda/Antigravity/IELTS/audit_phase3_report.json"
OUTPUT_REPORT = "/Users/tengda/Antigravity/IELTS/full_audit_report.md"


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def fmt_pct(n, total):
    if total == 0:
        return "0%"
    return f"{n/total*100:.1f}%"


def main():
    print("Generating full audit report...")

    p1, p1_err = load_json(PHASE1_REPORT)
    p2, p2_err = load_json(PHASE2_REPORT)
    p3, p3_err = load_json(PHASE3_REPORT)

    lines = []

    # Header
    lines += [
        "# IELTS Item Bank — Full Audit Report",
        f"",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST  ",
        f"**Source**: 651 newly processed IELTS Reading JSON objects  ",
        f"**Pipeline**: `extracted/ → (LLM via Minimax) → parsed_v2/ → staging/`",
        f"",
        "---",
        "",
    ]

    # -------------------------------------------------------------------------
    # PHASE 1
    # -------------------------------------------------------------------------
    lines += [
        "## Phase 1: Structural & Schema Validation",
        "",
    ]

    if p1_err:
        lines.append(f"> ❌ Could not load Phase 1 report: {p1_err}")
    else:
        s1 = p1.get("summary", {})
        total_ext  = s1.get("total_extracted_files", 0)
        total_prs  = s1.get("total_parsed_v2_files", 0)
        missing    = s1.get("missing_from_parsed_v2", 0)
        extra      = s1.get("extra_in_parsed_v2", 0)
        clean      = s1.get("parsed_files_clean", 0)
        warn       = s1.get("parsed_files_warn", 0)
        crit       = s1.get("parsed_files_critical", 0)
        dups       = s1.get("duplicate_ids", 0)

        lines += [
            "### Summary",
            "",
            "| Metric | Count | % |",
            "|---|---|---|",
            f"| Total extracted (raw) | {total_ext} | — |",
            f"| Successfully parsed by LLM | {total_prs} | {fmt_pct(total_prs, total_ext)} |",
            f"| **Missing from parsed_v2** (LLM failures) | {missing} | {fmt_pct(missing, total_ext)} |",
            f"| Extra in parsed_v2 (unexpected) | {extra} | — |",
            f"| ✅ Clean schema | {clean} | {fmt_pct(clean, total_prs)} |",
            f"| ⚠️ Minor warnings | {warn} | {fmt_pct(warn, total_prs)} |",
            f"| ❌ Critical schema failures | {crit} | {fmt_pct(crit, total_prs)} |",
            f"| 🔁 Duplicate IDs | {dups} | — |",
            "",
        ]

        # Missing files list
        missing_list = p1.get("missing_from_parsed_v2", [])
        if missing_list:
            lines += [
                "### Files Missing from parsed_v2 (LLM never processed these)",
                "",
                "These items require re-processing via `structure_v2.py`.",
                "",
            ]
            for f in missing_list:
                lines.append(f"- `{f}`")
            lines.append("")

        # Issue type breakdown
        issue_types = s1.get("issue_type_counts", {})
        if issue_types:
            lines += [
                "### Issue Type Breakdown (parsed_v2 files)",
                "",
                "| Issue Type | Count |",
                "|---|---|",
            ]
            for k, v in sorted(issue_types.items(), key=lambda x: -x[1]):
                lines.append(f"| `{k}` | {v} |")
            lines.append("")

        # Duplicate IDs
        dup_ids = p1.get("duplicate_ids", [])
        if dup_ids:
            lines += [
                "### Duplicate IDs Found",
                "",
            ]
            for d in dup_ids:
                lines.append(f"- ID `{d['id']}` appears in: {d['files']}")
            lines.append("")

    lines += ["---", ""]

    # -------------------------------------------------------------------------
    # PHASE 2
    # -------------------------------------------------------------------------
    lines += [
        "## Phase 2: Pedagogical Spec Audit",
        "",
    ]

    if p2_err:
        lines.append(f"> ❌ Could not load Phase 2 report: {p2_err}")
    else:
        s2 = p2.get("summary", {})
        total_analyzed = s2.get("total_analyzed", 0)
        has_parsed     = s2.get("total_with_parsed_v2", 0)
        cls_counts     = s2.get("classification_counts", {})
        issue_count    = s2.get("items_with_issues", 0)
        wc_stats       = s2.get("word_count_stats", {})
        q_stats        = s2.get("question_count_stats_full_passages", {})
        type_dist      = s2.get("question_type_distribution", {})

        ideal   = cls_counts.get("IDEAL", 0)
        mini    = cls_counts.get("MINI_PASSAGE", 0)
        warn_wc = cls_counts.get("WARN_WORD_COUNT", 0)
        warn_qc = cls_counts.get("WARN_QUESTION_COUNT", 0)
        warn_os = cls_counts.get("WARN_OVERSIZED", 0)
        stub    = cls_counts.get("EMPTY_OR_STUB", 0)
        notp    = cls_counts.get("NOT_PROCESSED", 0)

        lines += [
            "### Passage Classification",
            "",
            "| Classification | Count | % |",
            "|---|---|---|",
            f"| ✅ IDEAL (700–900w, 13–14q) | {ideal} | {fmt_pct(ideal, total_analyzed)} |",
            f"| 📎 MINI_PASSAGE (≤350 words, 1 MCQ) | {mini} | {fmt_pct(mini, total_analyzed)} |",
            f"| ⚠️ WARN_WORD_COUNT | {warn_wc} | {fmt_pct(warn_wc, total_analyzed)} |",
            f"| ⚠️ WARN_QUESTION_COUNT | {warn_qc} | {fmt_pct(warn_qc, total_analyzed)} |",
            f"| ⚠️ WARN_OVERSIZED | {warn_os} | {fmt_pct(warn_os, total_analyzed)} |",
            f"| ❌ EMPTY_OR_STUB | {stub} | {fmt_pct(stub, total_analyzed)} |",
            f"| ❌ NOT_PROCESSED (missing parsed_v2) | {notp} | {fmt_pct(notp, total_analyzed)} |",
            "",
            "### Word Count Statistics (passage_text only)",
            "",
            f"| Stat | Value |",
            "|---|---|",
            f"| Min | {wc_stats.get('min', '—')} words |",
            f"| Max | {wc_stats.get('max', '—')} words |",
            f"| Avg | {wc_stats.get('avg', '—')} words |",
            "",
            "### Question Count Statistics (full passages only)",
            "",
            f"| Stat | Value |",
            "|---|---|",
            f"| Min | {q_stats.get('min', '—')} |",
            f"| Max | {q_stats.get('max', '—')} |",
            f"| Avg | {q_stats.get('avg', '—')} |",
            "",
            "### Question Type Distribution",
            "",
            "> This shows how many question groups of each type exist across all 651 items.",
            "",
            "| Question Type | Groups |",
            "|---|---|",
        ]
        for qt, cnt in sorted(type_dist.items(), key=lambda x: -x[1]):
            lines.append(f"| `{qt}` | {cnt} |")
        lines.append("")

        # Notable issues
        pbm_items = p2.get("items_with_issues", [])
        pbm_critical = [i for i in pbm_items if any("CRITICAL" in issue for issue in i.get("issues", []))]
        pbm_warn     = [i for i in pbm_items if all("CRITICAL" not in issue for issue in i.get("issues", []))]

        if pbm_critical:
            lines += [
                f"### Critical Pedagogical Issues ({len(pbm_critical)})",
                "",
                "| ID | Words | Questions | Issue |",
                "|---|---|---|---|",
            ]
            for item in pbm_critical[:40]:
                issues_str = "; ".join(item.get("issues", []))[:80]
                lines.append(f"| `{item['id']}` | {item['word_count']} | {item['question_count']} | {issues_str} |")
            if len(pbm_critical) > 40:
                lines.append(f"| *...and {len(pbm_critical) - 40} more* | | | |")
            lines.append("")

    lines += ["---", ""]

    # -------------------------------------------------------------------------
    # PHASE 3
    # -------------------------------------------------------------------------
    lines += [
        "## Phase 3: Controlled Integration",
        "",
    ]

    if p3_err:
        lines.append(f"> ❌ Could not load Phase 3 report: {p3_err}")
    else:
        s3 = p3.get("summary", {})
        total_prs  = s3.get("total_parsed_v2_files", 0)
        staged     = s3.get("successfully_staged", 0)
        excluded   = s3.get("excluded_total", 0)
        ex_reasons = s3.get("excluded_reasons", {})
        dup_slugs  = p3.get("duplicate_slugs", {})
        dup_titles = p3.get("duplicate_titles", {})
        db_coll    = p3.get("db_collisions", [])
        db_err_msg = p3.get("db_check_error")

        lines += [
            "### Staging Summary",
            "",
            "| Metric | Count | % |",
            "|---|---|---|",
            f"| Total parsed_v2 files | {total_prs} | — |",
            f"| ✅ Successfully staged | {staged} | {fmt_pct(staged, total_prs)} |",
            f"| ❌ Excluded from staging | {excluded} | {fmt_pct(excluded, total_prs)} |",
            "",
            "### Exclusion Reasons",
            "",
            "| Reason | Count |",
            "|---|---|",
        ]
        for reason, cnt in ex_reasons.items():
            lines.append(f"| `{reason}` | {cnt} |")
        lines.append("")

        if db_err_msg:
            lines += [
                f"> ℹ️ **DB collision check**: {db_err_msg}",
                "",
            ]
        else:
            lines += [
                f"> ✅ **DB collision check**: {len(db_coll)} existing source_ids found in `ielts_passages`",
                "",
            ]

        if dup_slugs:
            lines += [
                "### Duplicate Slugs",
                "",
                "| Slug | Files |",
                "|---|---|",
            ]
            for slug, files in list(dup_slugs.items())[:20]:
                lines.append(f"| `{slug}` | {', '.join(files)} |")
            lines.append("")

        if dup_titles:
            lines += [
                "### Duplicate Titles",
                "",
                "| Title | Files |",
                "|---|---|",
            ]
            for title, files in list(dup_titles.items())[:20]:
                lines.append(f"| {title[:60]} | {', '.join(files)} |")
            lines.append("")

    lines += ["---", ""]

    # -------------------------------------------------------------------------
    # Action Summary
    # -------------------------------------------------------------------------
    lines += [
        "## Recommended Action Items",
        "",
    ]

    action_items = []

    if p1 and not p1_err:
        missing_count = p1["summary"].get("missing_from_parsed_v2", 0)
        crit_count    = p1["summary"].get("parsed_files_critical", 0)
        if missing_count > 0:
            action_items.append(
                f"**Re-run `structure_v2.py`** for {missing_count} files missing from `parsed_v2/` "
                f"(LLM timeouts during batch processing)."
            )
        if crit_count > 0:
            action_items.append(
                f"**Investigate {crit_count} critical schema failures** in `parsed_v2/` — "
                f"these have empty `content.paragraphs` or `questions.question_groups`."
            )
        if p1["summary"].get("duplicate_ids", 0) > 0:
            action_items.append(
                "**Resolve duplicate IDs** — files with the same `id` field must be deduplicated."
            )

    if p3 and not p3_err:
        staged_count  = p3["summary"].get("successfully_staged", 0)
        action_items.append(
            f"**Import {staged_count} staged files** from `IELTS/staging/` into the database "
            f"using `scripts/migrate_reading_to_db.py` (update it to read from `staging/`)."
        )

    for i, action in enumerate(action_items, 1):
        lines.append(f"{i}. {action}")
    lines.append("")

    # -------------------------------------------------------------------------
    # Write file
    # -------------------------------------------------------------------------
    content = "\n".join(lines)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Report written to: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()

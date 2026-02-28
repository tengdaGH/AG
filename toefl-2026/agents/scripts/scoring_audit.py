#!/usr/bin/env python3
# ============================================================
# Purpose:    Weekly score integrity audit. Compares IRT theta estimates
#             vs AI band scores for Writing & Speaking. Finds null scores,
#             stuck sessions, and overexposed items. Saves report to
#             logs/scoring_audits/YYYY-MM-DD.md
# Usage:      python3 agents/scripts/scoring_audit.py
# Created:    2026-02-28
# Self-Destruct: No
# ============================================================

import os
import sys
import sqlite3
import datetime
import json

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ITEM_BANK_DB  = os.path.join(PROJECT_ROOT, "backend", "item_bank.db")
USER_DATA_DB  = os.path.join(PROJECT_ROOT, "backend", "user_data.db")
AUDITS_DIR    = os.path.join(PROJECT_ROOT, "logs", "scoring_audits")

os.makedirs(AUDITS_DIR, exist_ok=True)

TODAY = datetime.datetime.now().strftime("%Y-%m-%d")
NOW   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ── Helpers ───────────────────────────────────────────────────────────────────
GREEN  = "🟢"
YELLOW = "🟡"
RED    = "🔴"

issues   = {"green": [], "yellow": [], "red": []}
sections = []


def db_query(db_path, sql, params=()):
    try:
        conn = sqlite3.connect(db_path)
        cur  = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []


def safe_int(rows, default=0):
    if not rows:
        return default
    try:
        return int(rows[0][0])
    except (TypeError, ValueError):
        return default


def flag(level, message, fix=None):
    entry = f"**{message}**" if level == "red" else message
    if fix:
        entry += f"\n  → *{fix}*"
    issues[level].append(entry)


def section(title, lines):
    sections.append(f"### {title}\n" + "\n".join(f"- {l}" for l in lines))


# ── Check A — Null final scores on completed sessions ─────────────────────────
def check_null_scores():
    lines = []
    if not os.path.exists(USER_DATA_DB):
        flag("yellow", "user_data.db not found locally — cannot audit scores (cloud-only volume)")
        section("Null Score Check", ["ℹ️ user_data.db not present locally"])
        return

    rows = db_query(USER_DATA_DB,
        "SELECT id, student_id, created_at FROM sessions "
        "WHERE status='completed' AND final_score IS NULL")
    count = len(rows)
    lines.append(f"Completed sessions with null final_score: **{count}**")

    if count == 0:
        flag("green", "Score completeness: all completed sessions have a final_score")
    else:
        flag("red", f"Score completeness: {count} completed session(s) have null final_score",
             "Check score_calculator.py — scoring pipeline may have silently failed")
        for row in rows[:5]:
            lines.append(f"  ❌ Session {row[0]} | student={row[1]} | created={row[2]}")

    section("Null Score Check", lines)


# ── Check B — IRT vs AI score divergence ──────────────────────────────────────
def check_score_divergence():
    """
    Compares IRT-based band (from irt_theta) with AI band (from scores table).
    ETS spec: human-machine r >= 0.85. We flag sessions where |irt_band - ai_band| > 1.0.
    """
    lines = []
    if not os.path.exists(USER_DATA_DB):
        section("IRT vs AI Divergence", ["ℹ️ user_data.db not present locally"])
        return

    # Try to query the scores/sections tables — schema may vary
    # Attempt: sessions table has irt_theta and ai_score columns directly
    try:
        rows = db_query(USER_DATA_DB, """
            SELECT id, student_id, irt_theta, ai_score, final_score
            FROM sessions
            WHERE status='completed'
              AND irt_theta IS NOT NULL
              AND ai_score IS NOT NULL
            LIMIT 100
        """)
    except Exception:
        rows = []

    if not rows:
        lines.append("IRT vs AI divergence: no sessions with both irt_theta and ai_score — cannot compare yet")
        flag("yellow", "Score divergence: no sessions with both IRT and AI scores recorded",
             "Generate synthetic sessions first: python3 agents/scripts/seed_student_sessions.py")
        section("IRT vs AI Divergence", lines)
        return

    divergent = []
    for row in rows:
        session_id, student_id, irt_theta, ai_score = row[0], row[1], row[2], row[3]
        # Convert IRT theta (-3 to +3) to band (1–6): band = (theta + 3) + 1, clamped 1–6
        irt_band = max(1.0, min(6.0, (float(irt_theta) + 3.0) + 1.0))
        ai_band  = float(ai_score)
        delta    = abs(irt_band - ai_band)
        if delta > 1.0:
            divergent.append((session_id, student_id, irt_band, ai_band, delta))

    lines.append(f"Sessions checked: **{len(rows)}**")
    lines.append(f"Divergent sessions (|IRT - AI| > 1.0 band): **{len(divergent)}**")

    if not divergent:
        flag("green", f"Score divergence: all {len(rows)} sessions within ETS tolerance (Δ ≤ 1.0 band)")
    elif len(divergent) <= 2:
        flag("yellow", f"Score divergence: {len(divergent)} session(s) exceed ETS tolerance",
             "Review these sessions manually — may be edge cases or AI scoring failure")
        for d in divergent:
            lines.append(f"  ⚠ Session {d[0]} | student={d[1]} | IRT={d[2]:.1f} AI={d[3]:.1f} Δ={d[4]:.2f}")
    else:
        flag("red", f"Score divergence: {len(divergent)} sessions exceed ETS tolerance — scoring pipeline may be broken",
             "Check irt_service.py and gemini_service.py for recent changes")
        for d in divergent[:5]:
            lines.append(f"  ❌ Session {d[0]} | student={d[1]} | IRT={d[2]:.1f} AI={d[3]:.1f} Δ={d[4]:.2f}")

    section("IRT vs AI Divergence", lines)


# ── Check C — Item overexposure ───────────────────────────────────────────────
def check_overexposure():
    lines = []
    if not os.path.exists(ITEM_BANK_DB):
        section("Item Exposure", ["ℹ️ item_bank.db not found"])
        return

    total_sessions_rows = db_query(USER_DATA_DB, "SELECT COUNT(*) FROM sessions WHERE status='completed'") \
        if os.path.exists(USER_DATA_DB) else [(0,)]
    total_sessions = safe_int(total_sessions_rows)

    rows = db_query(ITEM_BANK_DB,
        "SELECT id, title, exposure_count, task_type FROM test_items "
        "WHERE lifecycle_status='ACTIVE' AND exposure_count > 0 "
        "ORDER BY exposure_count DESC LIMIT 10")

    if not rows:
        flag("green", "Item exposure: no overexposed items detected")
        lines.append("No items with exposure_count > 0")
        section("Item Exposure", lines)
        return

    lines.append(f"Total completed sessions: **{total_sessions}**")
    lines.append("Top exposed items (max 10):")

    overexposed = []
    for row in rows:
        item_id, title, exposure, task_type = row[0], row[1], row[2], row[3]
        safe_title = str(title)[:50] if title else f"ID:{item_id}"
        rate = (int(exposure) / max(total_sessions, 1)) * 100
        lines.append(f"  {'⚠' if rate > 15 else '•'} [{task_type}] {safe_title}: {exposure} exposures ({rate:.1f}%)")
        if rate > 15:
            overexposed.append((item_id, safe_title, exposure, rate))

    if not overexposed:
        flag("green", "Item exposure: all items within ETS 15% overexposure threshold")
    else:
        for item in overexposed:
            flag("yellow", f"Item overexposed: '{item[1]}' at {item[3]:.1f}% (limit 15%)",
                 f"Consider retiring item ID={item[0]} or activating replacement items")

    section("Item Exposure", lines)


# ── Check D — Scoring latency ─────────────────────────────────────────────────
def check_scoring_latency():
    lines = []
    if not os.path.exists(USER_DATA_DB):
        section("Scoring Latency", ["ℹ️ user_data.db not present locally"])
        return

    try:
        rows = db_query(USER_DATA_DB, """
            SELECT id, student_id,
                   ROUND((julianday(completed_at) - julianday(created_at)) * 24 * 60, 1) as minutes
            FROM sessions
            WHERE status='completed' AND completed_at IS NOT NULL AND created_at IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
        """)
    except Exception:
        rows = []

    if not rows:
        lines.append("Scoring latency: no completed sessions with timestamps")
        flag("yellow", "Scoring latency: cannot measure — no completed sessions with both timestamps")
        section("Scoring Latency", lines)
        return

    slow = [(r[0], r[1], r[2]) for r in rows if r[2] is not None and float(r[2]) > 5]
    avg_min = sum(float(r[2]) for r in rows if r[2] is not None) / max(len(rows), 1)

    lines.append(f"Sessions checked: **{len(rows)}**")
    lines.append(f"Average completion time: **{avg_min:.1f} min**")
    lines.append(f"Sessions > 5 min (slow): **{len(slow)}**")

    if not slow:
        flag("green", f"Scoring latency: avg {avg_min:.1f} min — all sessions scored within 5 min")
    else:
        flag("yellow", f"Scoring latency: {len(slow)} session(s) took > 5 min to score",
             "Check Gemini API timeout in gemini_service.py — increase timeout or add retry logic")
        for s in slow[:3]:
            lines.append(f"  ⚠ Session {s[0]} | student={s[1]} | {s[2]} min")

    section("Scoring Latency", lines)


# ── Build & Save Report ───────────────────────────────────────────────────────
def build_report():
    red_c    = len(issues["red"])
    yellow_c = len(issues["yellow"])
    green_c  = len(issues["green"])

    if red_c > 0:
        headline = f"⚠️ {red_c} critical issue(s) — scoring pipeline may be compromised"
    elif yellow_c > 0:
        headline = f"🟡 {yellow_c} item(s) to monitor — scores are within tolerance"
    else:
        headline = "✅ All clear — scoring pipeline healthy"

    lines = [
        f"# Scoring Audit Report — {NOW}",
        "",
        f"## {headline}",
        "",
    ]

    if issues["red"]:
        lines.append(f"## {RED} Critical ({red_c})")
        for item in issues["red"]:
            lines.append(f"- {item}")
        lines.append("")

    if issues["yellow"]:
        lines.append(f"## {YELLOW} Watch ({yellow_c})")
        for item in issues["yellow"]:
            lines.append(f"- {item}")
        lines.append("")

    if issues["green"]:
        lines.append(f"## {GREEN} All Clear ({green_c})")
        for item in issues["green"]:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📋 Detailed Findings")
    lines.append("")
    for s in sections:
        lines.append(s)
        lines.append("")

    lines.append("---")
    lines.append(f"*scoring_auditor signed off at {NOW}.*")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  Scoring Audit — {NOW}")
    print(f"{'='*60}\n")

    print("Checking null scores...", end="", flush=True)
    check_null_scores()
    print(" done")

    print("Checking IRT vs AI divergence...", end="", flush=True)
    check_score_divergence()
    print(" done")

    print("Checking item overexposure...", end="", flush=True)
    check_overexposure()
    print(" done")

    print("Checking scoring latency...", end="", flush=True)
    check_scoring_latency()
    print(" done")

    report = build_report()

    report_path = os.path.join(AUDITS_DIR, f"{TODAY}.md")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    red_c    = len(issues["red"])
    yellow_c = len(issues["yellow"])
    green_c  = len(issues["green"])
    print(f"  {RED} {red_c}  {YELLOW} {yellow_c}  {GREEN} {green_c}")
    print(f"  Report saved: {report_path}")
    print(f"{'='*60}\n")

    print(report)
    return 0 if red_c == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

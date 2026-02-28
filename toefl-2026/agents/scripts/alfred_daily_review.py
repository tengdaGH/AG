#!/usr/bin/env python3
# ============================================================
# Purpose:    Alfred's daily review engine. Checks item bank health,
#             student data integrity, deployment status, and codebase
#             hygiene. Outputs a Markdown brief to logs/alfred_briefs/.
# Usage:      python3 agents/scripts/alfred_daily_review.py
# Created:    2026-02-28
# Self-Destruct: No
# ============================================================

import os
import sys
import sqlite3
import subprocess
import datetime
import json
import urllib.request
import urllib.error

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ITEM_BANK_DB = os.path.join(PROJECT_ROOT, "backend", "item_bank.db")
USER_DATA_DB = os.path.join(PROJECT_ROOT, "backend", "user_data.db")
BRIEFS_DIR   = os.path.join(PROJECT_ROOT, "logs", "alfred_briefs")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
CLOUD_API    = "http://101.32.187.39:8000"

os.makedirs(BRIEFS_DIR, exist_ok=True)

TODAY = datetime.datetime.now().strftime("%Y-%m-%d")
NOW   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Helpers ──────────────────────────────────────────────────────────────────
GREEN  = "🟢"
YELLOW = "🟡"
RED    = "🔴"

issues   = {"green": [], "yellow": [], "red": []}
sections = []

def run(cmd):
    """Run a shell command, return stdout string or '' on error."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception:
        return ""

def db_query(db_path, sql, params=()):
    """Run a SQL query, return rows list or [] on error."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []  # Return empty list on any error; callers handle missing data gracefully

def safe_int(rows, default=0):
    """Safely extract an integer count from a COUNT(*) query result."""
    if not rows:
        return default
    val = rows[0][0]
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def flag(level, message, fix=None):
    entry = f"**{message}**" if level == "red" else message
    if fix:
        entry += f"\n  → *{fix}*"
    issues[level].append(entry)

def section(title, lines):
    sections.append(f"### {title}\n" + "\n".join(f"- {l}" for l in lines))


# ── PILLAR 1: Item Bank Health ────────────────────────────────────────────────
def check_item_bank():
    lines = []

    if not os.path.exists(ITEM_BANK_DB):
        flag("red", "item_bank.db NOT FOUND at expected path",
             f"Expected: {ITEM_BANK_DB}")
        section("Item Bank (item_bank.db)", ["❌ Database file missing"])
        return

    # Total active
    rows = db_query(ITEM_BANK_DB, "SELECT COUNT(*) FROM test_items WHERE lifecycle_status='ACTIVE'")
    active_count = safe_int(rows)
    lines.append(f"ACTIVE items: **{active_count}**")
    if active_count >= 1000:
        flag("green", f"Item bank: {active_count} ACTIVE items")
    elif active_count >= 900:
        flag("yellow", f"Item bank dropping: only {active_count} ACTIVE items (target ≥ 1,000)")
    else:
        flag("red", f"Item bank critically low: {active_count} ACTIVE items",
             "Check for accidental bulk deactivation in recent git commits")

    # Status distribution
    rows = db_query(ITEM_BANK_DB,
        "SELECT lifecycle_status, COUNT(*) FROM test_items GROUP BY lifecycle_status")
    for row in rows:
        status, count = row[0], int(row[1]) if len(row) > 1 else 0
        if status:
            lines.append(f"{status}: {count}")
            if status == "SUSPENDED" and count > 30:
                flag("red", f"{count} SUSPENDED items — too many languishing",
                     "Run IRT re-calibration or remediate suspended items")
            elif status == "SUSPENDED" and count > 10:
                flag("yellow", f"{count} SUSPENDED items — schedule remediation")

    # IRT null checks
    rows = db_query(ITEM_BANK_DB,
        "SELECT COUNT(*) FROM test_items WHERE lifecycle_status='ACTIVE' AND irt_difficulty IS NULL")
    null_irt = safe_int(rows)
    lines.append(f"ACTIVE items with null IRT b: **{null_irt}**")
    if null_irt == 0:
        flag("green", "IRT: all ACTIVE items have calibrated difficulty (b) values")
    elif null_irt <= 5:
        flag("yellow", f"IRT: {null_irt} ACTIVE items missing irt_difficulty",
             "Run: python3 backend/scripts/calibrate_full_itembank.py --apply")
    else:
        flag("red", f"IRT: {null_irt} ACTIVE items served without calibrated b values",
             "Run calibration immediately — these items give unreliable scores")

    # C-Test corruption check
    rows = db_query(ITEM_BANK_DB,
        "SELECT COUNT(*) FROM test_items WHERE task_type='C_TEST' "
        "AND (prompt_content LIKE '%blank lin%' OR prompt_content LIKE '%(% blank%')")
    corrupt_ctest = safe_int(rows)
    lines.append(f"Corrupted C-Test items: **{corrupt_ctest}**")
    if corrupt_ctest == 0:
        flag("green", "C-Test: no corruption detected (no 'blank lines' annotations)")
    else:
        flag("red", f"C-Test corruption: {corrupt_ctest} items have '(blank lines)' text in them",
             "Re-run: python3 backend/scripts/fix_ctest_items.py")

    # C-Test gap count — use subquery to avoid HAVING alias issue in SQLite
    rows = db_query(ITEM_BANK_DB, """
        SELECT id, title, gap_count FROM (
            SELECT id, title,
                   (LENGTH(prompt_content) - LENGTH(REPLACE(prompt_content, '_', ''))) AS gap_count
            FROM test_items
            WHERE task_type='C_TEST' AND lifecycle_status='ACTIVE'
        ) sub WHERE gap_count < 8
    """)
    low_gap = len(rows)
    if low_gap == 0:
        flag("green", "C-Test: all active items have ≥ 8 gap markers")
    else:
        flag("yellow", f"C-Test: {low_gap} items have fewer than 8 gaps",
             "Review and regen these items with fix_ctest_items.py")
        for row in rows[:3]:
            title = row[1] if len(row) > 1 else "unknown"
            gaps  = row[2] if len(row) > 2 else "?"
            lines.append(f"  ⚠ Low-gap C-Test: {title} ({gaps} underscores)")

    # Missing audio on listening items
    rows = db_query(ITEM_BANK_DB,
        "SELECT COUNT(*) FROM test_items "
        "WHERE section='LISTENING' AND lifecycle_status='ACTIVE' "
        "AND (audio_url IS NULL OR audio_url = '')")
    missing_audio = safe_int(rows)
    lines.append(f"Listening items missing audio_url: **{missing_audio}**")
    if missing_audio == 0:
        flag("green", "Audio: all ACTIVE Listening items have audio URLs")
    elif missing_audio <= 3:
        flag("yellow", f"Audio: {missing_audio} Listening items missing audio_url",
             "Run audio generation for these items")
    else:
        flag("red", f"Audio: {missing_audio} Listening items have no audio — students cannot take the test",
             "Priority: generate audio for missing listening items")

    # Exposure rate warning
    rows = db_query(ITEM_BANK_DB,
        "SELECT id, title, exposure_count FROM test_items "
        "WHERE lifecycle_status='ACTIVE' AND exposure_count > 50 "
        "ORDER BY exposure_count DESC LIMIT 5")
    if rows:
        lines.append(f"High-exposure items (top 5):")
        for row in rows:
            lines.append(f"  📊 {str(row[1])[:40]}: exposure={row[2]}")
        top_exp = int(rows[0][2]) if rows[0][2] else 0
        if top_exp > 200:
            flag("yellow", f"Exposure: '{str(rows[0][1])[:40]}' served {top_exp} times — monitor against 15% ETS limit",
                 "Consider retiring this item if sessions > 1,000 total")

    section("Item Bank (item_bank.db)", lines)


# ── PILLAR 2: Student Data Health ─────────────────────────────────────────────
def check_user_data():
    lines = []

    if not os.path.exists(USER_DATA_DB):
        flag("yellow", "user_data.db not found locally — expected on cloud server only")
        section("Student Data (user_data.db)", ["ℹ️ Not present locally (cloud-only volume — OK)"])
        return

    # Session count
    rows = db_query(USER_DATA_DB, "SELECT COUNT(*) FROM sessions")
    total_sessions = safe_int(rows)
    lines.append(f"Total sessions: **{total_sessions}**")

    # In-progress sessions stuck for > 7 days
    rows = db_query(USER_DATA_DB,
        "SELECT COUNT(*) FROM sessions WHERE status='in_progress' "
        "AND created_at < datetime('now', '-7 days')")
    stuck = safe_int(rows)
    lines.append(f"Stuck sessions (in_progress > 7 days): **{stuck}**")
    if stuck == 0:
        flag("green", "Student sessions: no stuck in-progress sessions")
    elif stuck <= 3:
        flag("yellow", f"Student data: {stuck} sessions stuck in 'in_progress' > 7 days",
             "Check if these are test accounts or real students who abandoned")
    else:
        flag("red", f"Student data: {stuck} sessions stuck — possible scoring pipeline failure",
             "Check /api/sessions endpoint and score_calculator.py")

    # Recent 24h activity
    rows = db_query(USER_DATA_DB,
        "SELECT COUNT(*) FROM sessions WHERE created_at > datetime('now', '-1 day')")
    recent = safe_int(rows)
    lines.append(f"Sessions in last 24h: **{recent}**")
    flag("green", f"Student data: {recent} sessions in the last 24 hours")

    # Sessions with no responses (abandoned immediately)
    rows = db_query(USER_DATA_DB,
        "SELECT COUNT(*) FROM sessions s WHERE NOT EXISTS "
        "(SELECT 1 FROM responses r WHERE r.session_id = s.id)")
    empty = safe_int(rows)
    if empty > 1:
        flag("yellow", f"Student data: {empty} sessions with zero responses (abandoned on start)",
             "May indicate login/loading issues — check with recent user reports")

    section("Student Data (user_data.db)", lines)


# ── PILLAR 3: Deployment & Server ─────────────────────────────────────────────
def check_deployment():
    lines = []

    # Cloud API health
    try:
        req = urllib.request.Request(f"{CLOUD_API}/docs", headers={"User-Agent": "Alfred/1.0"})
        resp = urllib.request.urlopen(req, timeout=8)
        status = resp.getcode()
        if status == 200:
            flag("green", f"Cloud API: responding at {CLOUD_API} (HTTP {status})")
            lines.append(f"Cloud API: ✅ HTTP {status}")
        else:
            flag("yellow", f"Cloud API: unexpected status {status}", "Check Tencent Cloud server logs")
            lines.append(f"Cloud API: ⚠ HTTP {status}")
    except Exception as e:
        flag("red", f"Cloud API: NOT responding — {CLOUD_API} unreachable",
             "SSH to Tencent Cloud and check: docker ps && docker logs toefl_backend")
        lines.append(f"Cloud API: ❌ unreachable ({e})")

    # Git sync
    local_head  = run("git -C " + PROJECT_ROOT + " rev-parse HEAD")
    remote_head = run("git -C " + PROJECT_ROOT + " ls-remote origin HEAD | awk '{print $1}'")
    if local_head and remote_head and local_head == remote_head:
        flag("green", "Git: local HEAD matches remote origin/main — fully synced")
        lines.append(f"Git: ✅ synced ({local_head[:8]})")
    elif local_head and remote_head:
        flag("yellow", "Git: local is ahead or behind remote — changes may not be deployed",
             "Run: git pull origin main && git push origin main")
        lines.append(f"Git: ⚠ local={local_head[:8]} remote={remote_head[:8]}")
    else:
        lines.append("Git: ⚠ could not compare heads")

    # Port 8000 process check
    # NOTE: uvicorn --reload spawns 2 PIDs (parent + reload worker). This is normal.
    # Ghost process = 3+ PIDs, meaning an orphaned previous uvicorn is still holding the port.
    procs = run("lsof -ti :8000 | wc -l").strip()
    proc_count = int(procs) if procs.isdigit() else 0
    lines.append(f"Processes on port 8000: **{proc_count}**")
    if proc_count == 0:
        flag("yellow", "Port 8000: no process running locally — backend is down",
             "Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
    elif proc_count <= 2:
        # 1 = production mode (uvicorn without --reload)
        # 2 = --reload mode (parent supervisor + 1 worker) — both are healthy
        label = "production mode" if proc_count == 1 else "--reload mode (parent + worker)"
        flag("green", f"Port 8000: {proc_count} process(es) — backend healthy ({label})")
    else:
        # 3+ PIDs = a previous uvicorn was not killed cleanly before a new one started
        flag("red", f"Port 8000: {proc_count} PIDs detected — probable ghost process from unclean restart!",
             "Run: kill $(lsof -ti :8000) && cd backend && source venv/bin/activate && uvicorn app.main:app --reload")

    # .env.local check (should NOT exist — it breaks cloud connectivity)
    env_local = os.path.join(FRONTEND_DIR, ".env.local")
    if os.path.exists(env_local):
        with open(env_local) as f:
            content = f.read()
        flag("red", "frontend/.env.local EXISTS — this breaks cloud API connectivity!",
             f"Delete it: rm {env_local}  (content: {content.strip()[:60]})")
        lines.append(f"frontend/.env.local: ❌ EXISTS (breaks cloud connectivity)")
    else:
        flag("green", "frontend/.env.local: absent — frontend correctly hits cloud API")
        lines.append("frontend/.env.local: ✅ absent")

    # Old DB name check
    old_names = run(f"find {PROJECT_ROOT}/backend -name 'toefl_2026.db' -o -name 'toefl_user_data.db' -o -name 'toefl_item_bank.db' 2>/dev/null")
    if old_names:
        flag("yellow", f"Old DB filenames found: {old_names}",
             "Delete these — they are confusing artifacts from before the Feb 28 rename")
        lines.append(f"Old DB files: ⚠ {old_names}")
    else:
        flag("green", "DB filenames: no old 'toefl_2026.db' names found — naming is clean")
        lines.append("DB filenames: ✅ clean")

    # Zero-byte stub DBs
    stub_dbs = run(f"find {PROJECT_ROOT}/backend -name '*.db' -size 0 2>/dev/null")
    if stub_dbs:
        flag("yellow", f"Zero-byte stub databases found: {stub_dbs}",
             "Delete these: rm <filename>")
    else:
        flag("green", "Stub databases: none found")

    section("Deployment & Server", lines)


# ── PILLAR 4: Codebase Hygiene ────────────────────────────────────────────────
def check_codebase():
    lines = []

    # Recent git commits (last 7 days)
    log = run(f"git -C {PROJECT_ROOT} log --oneline --since='7 days ago' --no-merges")
    if log:
        commit_lines = log.strip().split("\n")
        lines.append(f"Commits in last 7 days: **{len(commit_lines)}**")
        for c in commit_lines[:5]:
            lines.append(f"  • {c}")
    else:
        lines.append("Commits in last 7 days: **0**")
        flag("yellow", "Codebase: no commits in 7 days — is development paused?")

    # Orphaned /tmp scripts
    tmp_scripts = run("find /tmp -name '*.py' -newer /tmp 2>/dev/null | head -5")
    if tmp_scripts:
        flag("yellow", f"Temp scripts in /tmp: {tmp_scripts.replace(chr(10), ', ')}",
             "Delete if no longer needed (python_housekeeping Rule 3)")
        lines.append(f"Temp /tmp scripts: ⚠ {len(tmp_scripts.split(chr(10)))} found")
    else:
        flag("green", "Temp scripts: /tmp is clean — no leftover Python scripts")
        lines.append("Temp scripts: ✅ /tmp clean")

    # connection.py DB path sanity
    conn_py = os.path.join(PROJECT_ROOT, "backend/app/database/connection.py")
    if os.path.exists(conn_py):
        with open(conn_py) as f:
            content = f.read()
        if "item_bank.db" in content and "user_data.db" in content:
            flag("green", "connection.py: uses correct DB filenames (item_bank.db + user_data.db)")
            lines.append("connection.py: ✅ correct DB names")
        elif "toefl_2026.db" in content:
            flag("red", "connection.py still references 'toefl_2026.db' — DB rename not applied!",
                 "Run the DB rename refactor immediately")
            lines.append("connection.py: ❌ old DB name found")

    section("Codebase Hygiene", lines)


# ── PILLAR 5: Agent Cadence Checks ────────────────────────────────────────────
def check_agent_cadence():
    """Verify that scheduled sub-agents have run within their required windows."""
    lines = []

    # scoring_auditor — must run weekly
    audits_dir = os.path.join(PROJECT_ROOT, "logs", "scoring_audits")
    os.makedirs(audits_dir, exist_ok=True)
    audit_files = sorted([
        f for f in os.listdir(audits_dir) if f.endswith(".md")
    ]) if os.path.isdir(audits_dir) else []

    if not audit_files:
        flag("yellow", "scoring_auditor: never run — no audit log found in logs/scoring_audits/",
             "Run: python3 agents/scripts/scoring_audit.py")
        lines.append("scoring_auditor: ⚠ never run")
    else:
        latest_audit = audit_files[-1]  # e.g. "2026-02-28.md"
        try:
            audit_date_str = latest_audit.replace(".md", "")
            audit_date = datetime.datetime.strptime(audit_date_str, "%Y-%m-%d")
            days_ago = (datetime.datetime.now() - audit_date).days
            if days_ago <= 7:
                flag("green", f"scoring_auditor: last run {days_ago}d ago ({audit_date_str}) — on schedule")
                lines.append(f"scoring_auditor: ✅ last run {days_ago}d ago")
            else:
                flag("yellow", f"scoring_auditor: last run {days_ago} days ago — overdue (run weekly)",
                     "Run: python3 agents/scripts/scoring_audit.py")
                lines.append(f"scoring_auditor: ⚠ {days_ago}d ago — overdue")
        except ValueError:
            lines.append(f"scoring_auditor: ⚠ could not parse date from {latest_audit}")

    # Synthetic data check — SYN_ users must not be in production user_data.db
    if os.path.exists(USER_DATA_DB):
        rows = db_query(USER_DATA_DB,
            "SELECT COUNT(*) FROM students WHERE username LIKE 'SYN_%'")
        syn_count = safe_int(rows)
        if syn_count > 0:
            flag("yellow", f"Synthetic data: {syn_count} SYN_ test users found in user_data.db — clean before production",
                 "Run: python3 agents/scripts/seed_student_sessions.py --purge-synthetic")
            lines.append(f"Synthetic data: ⚠ {syn_count} SYN_ users present")
        else:
            flag("green", "Synthetic data: no SYN_ test users in production DB")
            lines.append("Synthetic data: ✅ clean")

    section("Agent Cadence", lines)


# ── PILLAR 6: Priorities ───────────────────────────────────────────────────────
def compute_priorities():
    """Derive top priorities from red+yellow flags."""
    priorities = []
    for msg in issues["red"]:
        clean = msg.replace("**", "").split("\n")[0]
        priorities.append(f"🔴 {clean}")
    for msg in issues["yellow"]:
        clean = msg.replace("**", "").split("\n")[0]
        priorities.append(f"🟡 {clean}")
    return priorities[:5]  # Cap at 5


# ── Build & Save the Brief ─────────────────────────────────────────────────────
def build_brief():
    priorities = compute_priorities()
    red_count    = len(issues["red"])
    yellow_count = len(issues["yellow"])
    green_count  = len(issues["green"])

    if red_count > 0:
        headline = f"⚠️ {red_count} issue(s) require immediate action"
    elif yellow_count > 0:
        headline = f"🟡 {yellow_count} item(s) to monitor — no fires today"
    else:
        headline = "✅ All clear — platform healthy"

    lines = [
        f"# Alfred Daily Brief — {NOW}",
        "",
        f"## {headline}",
        "",
    ]

    if issues["red"]:
        lines.append(f"## {RED} Action Required ({red_count})")
        for item in issues["red"]:
            lines.append(f"- {item}")
        lines.append("")

    if issues["yellow"]:
        lines.append(f"## {YELLOW} Watch ({yellow_count})")
        for item in issues["yellow"]:
            lines.append(f"- {item}")
        lines.append("")

    if issues["green"]:
        lines.append(f"## {GREEN} All Clear ({green_count})")
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

    if priorities:
        lines.append("---")
        lines.append("")
        lines.append(f"## 🎯 Your Top {min(len(priorities), 5)} Priorities")
        lines.append("")
        for i, p in enumerate(priorities[:5], 1):
            lines.append(f"{i}. {p}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Alfred signed off at {NOW}.*")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  Alfred Daily Review — {NOW}")
    print(f"{'='*60}\n")

    print("Checking item bank...", end="", flush=True)
    check_item_bank()
    print(" done")

    print("Checking student data...", end="", flush=True)
    check_user_data()
    print(" done")

    print("Checking deployment...", end="", flush=True)
    check_deployment()
    print(" done")

    print("Checking codebase...", end="", flush=True)
    check_codebase()
    print(" done")

    print("Checking agent cadence...", end="", flush=True)
    check_agent_cadence()
    print(" done")

    brief = build_brief()

    # Save brief
    brief_path = os.path.join(BRIEFS_DIR, f"{TODAY}.md")
    with open(brief_path, "w") as f:
        f.write(brief)

    # Terminal summary
    print(f"\n{'='*60}")
    red_c    = len(issues["red"])
    yellow_c = len(issues["yellow"])
    green_c  = len(issues["green"])
    print(f"  {RED} {red_c}  {YELLOW} {yellow_c}  {GREEN} {green_c}")
    print(f"  Brief saved: {brief_path}")
    print(f"{'='*60}\n")

    # Print the brief to stdout for agent consumption
    print(brief)

    return 0 if red_c == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

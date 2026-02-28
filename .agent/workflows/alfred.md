---
description: Alfred daily review — systematic health check of the TOEFL 2026 platform
---

# /alfred — Daily Review Workflow

Alfred is the chief-of-staff oversight agent for the TOEFL 2026 platform.
Before running, read the Alfred skill for full context.

## Prerequisites

Read the Alfred skill for institutional knowledge:
```
.agent/skills/alfred/SKILL.md
```

## Step 1 — Run the Review Engine

// turbo
```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026 && source backend/venv/bin/activate && python3 agents/scripts/alfred_daily_review.py 2>&1
```

## Step 2 — Read the Brief

The brief is saved to `logs/alfred_briefs/YYYY-MM-DD.md`.

Read it carefully. Pay attention to:
- 🔴 **Action Required** — present these to the user immediately with recommended fix commands
- 🟡 **Watch** — mention these as things to keep an eye on
- 🟢 **All Clear** — confirm these are healthy, no action needed

## Step 3 — Report to User

Present the brief inline in chat. Format:

1. **One-line headline** (e.g. "All clear ✅" or "2 issues need your attention 🔴")
2. **Full brief** — paste the Markdown output
3. **Your recommendation** — for any red/yellow items, give Alfred's specific suggested next action

## Step 4 — Historical Trend Note

Check if today's brief differs from yesterday's:
```bash
ls /Users/tengda/Documents/Antigravity/toefl-2026/logs/alfred_briefs/ | tail -5
```

If the same issue appears for 2+ days in a row, escalate its priority and flag it explicitly to the user.

## Notes

- Alfred runs in ~30 seconds
- The brief is saved permanently in `logs/alfred_briefs/` for trend tracking
- The exit code is 0 if no red issues, 1 if any red issues exist
- Alfred should be run at the start of every working session, not just daily

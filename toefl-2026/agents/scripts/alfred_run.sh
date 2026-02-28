#!/bin/bash
# ============================================================
# Purpose:    Shell wrapper for Alfred's daily review.
#             Activates the venv, runs the review engine, and
#             sends a native macOS notification with the summary.
# Usage:      bash agents/scripts/alfred_run.sh
#             (Also called automatically by LaunchAgent at 9 AM)
# Created:    2026-02-28
# Self-Destruct: No
# ============================================================

PROJECT="/Users/tengda/Documents/Antigravity/toefl-2026"
PYTHON="$PROJECT/backend/venv/bin/python3"
SCRIPT="$PROJECT/agents/scripts/alfred_daily_review.py"

cd "$PROJECT" || exit 1

# Run Alfred and capture output
OUTPUT=$("$PYTHON" "$SCRIPT" 2>&1)
EXIT_CODE=$?

# Extract counts from the terminal summary line: "🔴 N  🟡 N  🟢 N"
RED=$(echo "$OUTPUT" | grep -oE "🔴 [0-9]+" | grep -oE "[0-9]+" | head -1)
YELLOW=$(echo "$OUTPUT" | grep -oE "🟡 [0-9]+" | grep -oE "[0-9]+" | head -1)
GREEN=$(echo "$OUTPUT" | grep -oE "🟢 [0-9]+" | grep -oE "[0-9]+" | head -1)

RED=${RED:-0}
YELLOW=${YELLOW:-0}
GREEN=${GREEN:-0}

# Build notification message
if [ "$RED" -gt 0 ]; then
    TITLE="Alfred ⚠️ — $RED issue(s) need attention"
    BODY="$YELLOW watching · $GREEN all clear · Open brief in logs/alfred_briefs/"
elif [ "$YELLOW" -gt 0 ]; then
    TITLE="Alfred 🟡 — All good, $YELLOW item(s) to monitor"
    BODY="$GREEN checks passed · Open brief in logs/alfred_briefs/"
else
    TITLE="Alfred ✅ — Platform healthy"
    BODY="All $GREEN checks passed · Nothing to do today"
fi

# Send macOS native notification
osascript -e "display notification \"$BODY\" with title \"$TITLE\" sound name \"Glass\""

exit $EXIT_CODE

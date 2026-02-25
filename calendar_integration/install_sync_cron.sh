#!/bin/bash
# Script to install the Notion Sync cron job
# Runs every 15 minutes

CRON_CMD="*/15 * * * * cd /Users/tengda/Antigravity/calendar_integration && /usr/bin/python3 sync_to_notion.py >> sync.log 2>&1"

# Check if job already exists
(crontab -l 2>/dev/null | grep -v -F "sync_to_notion.py"; echo "$CRON_CMD") | crontab -
echo "✅ Notion Sync Cron Job installed! It will now automatically sync from Google Calendar to Notion every 15 minutes."

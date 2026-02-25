# ============================================================
# Purpose:       Quick utility to list all items currently in REVIEW lifecycle status.
# Usage:         python backend/scripts/check_review_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.connection import SessionLocal
from app.models.models import TestItem, ItemStatus

db = SessionLocal()
items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.REVIEW).all()
for i in items:
    print(f"{i.id[:8]} | {i.task_type.name} | {i.generation_notes}")
db.close()

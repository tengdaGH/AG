# ============================================================
# Purpose:       Ingest official TOEFL 2026-formatted reading items into the item bank database from structured JSON payloads.
# Usage:         python agents/scripts/ingest_2026_reading.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import uuid

# Add the backend directory to sys.path so we can import the SQLAlchemy models
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal
from app.models.models import TestItem, SectionType, CEFRLevel

# Mock Official ETS 2026 Reading Items
# Based on the latest specifications for the 2026 format rollout.
OFFICIAL_2026_READING_ITEMS = [
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.C1,
        "irt_difficulty": 1.5,
        "irt_discrimination": 1.2,
        "prompt_content": {
            "type": "Academic Passage",
            "title": "The Evolution of Urban Architecture in the 21st Century",
            "text": "Urban architecture has undergone a paradigm shift, transitioning from strictly functional, concrete-heavy structures to sustainable, green-integrated environments. This shift is not merely aesthetic but a necessary adaptation to climate change...",
            "questions": [
                {
                    "question_num": 1,
                    "text": "The phrase 'paradigm shift' in the passage implies:",
                    "options": ["A minor adjustment", "A fundamental change in approach", "A return to traditional methods", "A temporary trend"],
                    "correct_answer": 1
                },
                {
                    "question_num": 2,
                    "text": "According to the passage, the transition in architecture is primarily driven by:",
                    "options": ["Economic constraints", "Aesthetic preferences", "Climate change adaptation", "Government regulations"],
                    "correct_answer": 2
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B2,
        "irt_difficulty": 0.2,
        "irt_discrimination": 0.9,
        "prompt_content": {
            "type": "Read in Daily Life",
            "title": "Notice: Library Renovation Schedule",
            "text": "Dear Students, Please be advised that the main campus library will undergo renovations starting next Monday. The second floor will be closed for three weeks. Quiet study areas will be relocated to the student union building during this period.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "Where will students go for quiet study while the 2nd floor is closed?",
                    "options": ["First floor of the library", "Student union building", "Local cafe", "The library will remain open completely"],
                    "correct_answer": 1
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B1,
        "irt_difficulty": -1.0,
        "irt_discrimination": 0.8,
        "prompt_content": {
            "type": "Complete the Words",
            "title": "Complete the paragraph",
            "text": "The professor canceled class due to the inc___nt weather. Heavy s_ow made the roads unsafe for tr_vel.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "Fill in the blanks in the paragraph.",
                    "options": ["inclement, snow, travel", "incessant, slow, travel", "incident, show, travel", "inconsistent, snow, tinsel"],
                    "correct_answer": 0
                }
            ]
        },
        "is_active": True
    }
]

def ingest_official_items():
    db = SessionLocal()
    try:
        print("Starting ingestion of official 2026 Reading items into the database...")
        added_count = 0
        for item_data in OFFICIAL_2026_READING_ITEMS:
            new_item = TestItem(
                id=str(uuid.uuid4()),
                section=item_data["section"],
                target_level=item_data["target_level"],
                irt_difficulty=item_data["irt_difficulty"],
                irt_discrimination=item_data["irt_discrimination"],
                prompt_content=json.dumps(item_data["prompt_content"]),
                is_active=item_data["is_active"]
            )
            db.add(new_item)
            added_count += 1
        
        db.commit()
        print(f"Successfully ingested {added_count} official items into the 'test_items' table.")
    except Exception as e:
        db.rollback()
        print(f"An error occurred during DB ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ingest_official_items()

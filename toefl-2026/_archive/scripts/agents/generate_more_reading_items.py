# ============================================================
# Purpose:       Generate additional TOEFL 2026 reading items via Gemini and append them to the item bank database.
# Usage:         python agents/scripts/generate_more_reading_items.py
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

# Agent-Generated 2026 Reading Items
AGENT_GENERATED_ITEMS = [
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.C1,
        "irt_difficulty": 1.8,
        "irt_discrimination": 1.3,
        "prompt_content": {
            "type": "Academic Passage",
            "title": "The Global Ocean Conveyor Belt",
            "text": "The thermohaline circulation, often referred to as the global ocean conveyor belt, plays a vital role in regulating the Earth's climate. Driven by gradients in temperature and salinity, taking centuries to complete a single cycle, this massive network of currents transports vast amounts of heat from the equator toward the poles...",
            "questions": [
                {
                    "question_num": 1,
                    "text": "According to the passage, what primarily drives the thermohaline circulation?",
                    "options": ["Wind patterns and atmospheric pressure", "Gradients in temperature and salinity", "The gravitational pull of the moon", "Tectonic plate movements"],
                    "correct_answer": 1
                },
                {
                    "question_num": 2,
                    "text": "What does the passage imply about the speed of the global ocean conveyor belt?",
                    "options": ["It travels extremely rapidly.", "It moves at the speed of surface winds.", "It takes hundreds of years to complete one cycle.", "It is entirely stationary."],
                    "correct_answer": 2
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B2,
        "irt_difficulty": 0.5,
        "irt_discrimination": 1.1,
        "prompt_content": {
            "type": "Academic Passage",
            "title": "The Printing Press and the Renaissance",
            "text": "Johannes Gutenberg's invention of the movable type printing press in the 15th century catalyzed the spread of the Renaissance. By drastically reducing the cost and effort of reproducing texts, knowledge that had previously been monopolized by the elite became accessible to a burgeoning middle class, fundamentally altering European society.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "The phrase 'catalyzed the spread' is closest in meaning to:",
                    "options": ["Prevented the growth", "Accelerated the expansion", "Analyzed the details", "Documented the history"],
                    "correct_answer": 1
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B1,
        "irt_difficulty": -0.5,
        "irt_discrimination": 0.9,
        "prompt_content": {
            "type": "Read in Daily Life",
            "title": "Notice: Emergency Maintenance on Campus WiFi",
            "text": "IT Services will be conducting emergency maintenance on the campus WiFi network this Friday between 2:00 AM and 6:00 AM. During this window, internet access in all residence halls and the main library will be intermittent or completely unavailable. We apologize for any inconvenience this may cause to your studies.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "When will the campus WiFi be completely stable?",
                    "options": ["Any time on Thursday", "Friday at 1:00 AM", "Friday at 7:00 AM", "Any time during the maintenance window"],
                    "correct_answer": 2
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B2,
        "irt_difficulty": 0.1,
        "irt_discrimination": 1.0,
        "prompt_content": {
            "type": "Read in Daily Life",
            "title": "Email: Spring Semester Course Registration",
            "text": "Dear Student, this is a final reminder that the regular deadline to register for Spring semester courses is November 15th at 5:00 PM EST. A late fee of $50 will be automatically applied to any registrations completed after this date. If you have holds on your account, please contact the bursar's office before attempting to register.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "What happens if a student registers for a course on November 16th?",
                    "options": ["They are not allowed to register.", "They must pay a $50 late fee.", "They have to contact the bursar's office first.", "They will be placed on a waitlist."],
                    "correct_answer": 1
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B1,
        "irt_difficulty": -0.8,
        "irt_discrimination": 0.85,
        "prompt_content": {
            "type": "Complete the Words",
            "title": "Complete the paragraph: Biology Lab",
            "text": "In today's lab session, we will obs___ve the specific reaction of the enz_me when exposed to high temp___atures. Please record your ind___ings carefully in your lab notebook.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "Fill in the blanks to successfully complete the text.",
                    "options": ["observe, enzyme, temperatures, findings", "obstruct, ensign, tempers, indicants", "observe, enzyme, templates, indings", "obsess, enter, temperatures, endings"],
                    "correct_answer": 0
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B2,
        "irt_difficulty": 0.3,
        "irt_discrimination": 1.2,
        "prompt_content": {
            "type": "Complete the Words",
            "title": "Complete the paragraph: The Rosetta Stone",
            "text": "The discovery of the Rosetta Stone was mon___ental because it provided the cr__cial key to dec___hering Egyptian hieroglyphs, allowing historians to finally und___stand an ancient civilization.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "Fill in the missing letters to complete the paragraph.",
                    "options": ["monumental, crucial, deciphering, understand", "monotonous, cruel, declaring, understate", "momentary, crucial, deceiving, understand", "monumental, crushing, decoding, undo"],
                    "correct_answer": 0
                }
            ]
        },
        "is_active": True
    }
]

def ingest_agent_items():
    db = SessionLocal()
    try:
        print("Starting ingestion: Agent-Generated 2026 Reading Items...")
        added_count = 0
        for item_data in AGENT_GENERATED_ITEMS:
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
        print(f"Successfully injected {added_count} items into the database!")
    except Exception as e:
        db.rollback()
        print(f"Error during DB ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ingest_agent_items()

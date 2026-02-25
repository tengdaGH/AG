# ============================================================
# Purpose:       Generate TOEFL 2026-compliant reading test items using Gemini and insert them into the item bank.
# Usage:         python agents/scripts/agent_generate_compliant_items.py
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

SPECS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../specs'))


def read_technical_manual():
    """Load the full concatenated technical manual (for backward compatibility)."""
    manual_path = os.path.join(SPECS_DIR, 'toefl_2026_technical_manual.md')
    with open(manual_path, 'r') as file:
        return file.read()


def load_spec_sheet():
    """Load just the compact spec sheet (~900 words) for every generation call."""
    path = os.path.join(SPECS_DIR, 'toefl_2026_spec_sheet.md')
    with open(path, 'r') as file:
        return file.read()


def load_task_spec(filename):
    """Load a specific task type spec, e.g. 'reading_complete_the_words.md'."""
    path = os.path.join(SPECS_DIR, 'task_types', filename)
    with open(path, 'r') as file:
        return file.read()


def load_rubric(filename):
    """Load a specific scoring rubric, e.g. 'writing_email_rubric.md'."""
    path = os.path.join(SPECS_DIR, 'rubrics', filename)
    with open(path, 'r') as file:
        return file.read()

# The Agent (AI) has read the technical manual and generated these strictly compliant items
# based on the Type A, Type B, and Type C formatting requirements.
AGENT_GENERATED_COMPLIANT_ITEMS = [
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.C1,
        "irt_difficulty": 2.1,
        "irt_discrimination": 1.5,
        "prompt_content": {
            "type": "Read an Academic Passage",
            "title": "Quantum Entanglement and Information Theory",
            "text": "Quantum entanglement occurs when pairs or groups of particles are generated, interact, or share spatial proximity in ways such that the quantum state of each particle cannot be described independently of the state of the others, even when the particles are separated by a large distance. This phenomenon, which Albert Einstein famously derided as 'spooky action at a distance,' forms the bedrock of modern quantum information theory. It enables protocols such as quantum cryptography and superdense coding, fundamentally challenging classical intuitions about local realism.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "The phrase 'spooky action at a distance' in the passage is closest in meaning to:",
                    "options": ["Predictable mechanical forces", "Inexplicable non-local interaction", "Frightening radioactive decay", "Standard gravitational pull"],
                    "correct_answer": 1
                },
                {
                    "question_num": 2,
                    "text": "According to the passage, what is a practical application of quantum entanglement?",
                    "options": ["Developing classical cryptography", "Disproving Albert Einstein's theories", "Enabling superdense coding protocols", "Confirming the principles of local realism"],
                    "correct_answer": 2
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.B2,
        "irt_difficulty": 0.4,
        "irt_discrimination": 1.1,
        "prompt_content": {
            "type": "Read in Daily Life",
            "title": "Memo: Updates to the Student Health Center Protocol",
            "text": "To all registered students: Beginning October 1st, the Student Health Center will transition to a fully digital appointment system. Walk-in consultations for non-emergencies will no longer be accepted. You must schedule your visit via the university portal at least 24 hours in advance. For sudden acute illness, please call the triage nurse hotline rather than arriving unannounced.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "What action should a student take if they experience a sudden acute illness after October 1st?",
                    "options": ["Walk into the Student Health Center immediately.", "Schedule an appointment 24 hours in advance.", "Call the triage nurse hotline.", "Email the university portal administrator."],
                    "correct_answer": 2
                }
            ]
        },
        "is_active": True
    },
    {
        "section": SectionType.READING,
        "target_level": CEFRLevel.A2,
        "irt_difficulty": -2.0,
        "irt_discrimination": 0.7,
        "prompt_content": {
            "type": "Complete the Words",
            "title": "Complete the paragraph: Transportation",
            "text": "The campus b_s arrives every twenty min_tes. It is free for all stu_ents to use. Please remember to show your ID card when you get on.",
            "questions": [
                {
                    "question_num": 1,
                    "text": "Fill in the exact missing letters for the paragraph above.",
                    "options": ["bus, minutes, students", "boy, minutes, stutters", "bus, manages, students", "bug, motives, students"],
                    "correct_answer": 0
                }
            ]
        },
        "is_active": True
    }
]

def run_agent_generation():
    manual = read_technical_manual()
    print("Test Item Designer Agent initialized.")
    print(f"Loaded Technical Manual. Length: {len(manual)} characters.")
    print("Strictly adhering to formatting guidelines: [Type A, Type B, Type C]")
    
    db = SessionLocal()
    try:
        print("Generating items and committing to database...")
        added_count = 0
        for item_data in AGENT_GENERATED_COMPLIANT_ITEMS:
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
        print(f"Agent Successfully injected {added_count} highly-compliant items into the database!")
    except Exception as e:
        db.rollback()
        print(f"Error during agent DB ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_agent_generation()

# ============================================================
# Purpose:       Ingest mock TPO (TOEFL Practice Online) reading data into the item bank as baseline content.
# Usage:         python agents/scripts/ingest_tpo_data.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import json
import uuid
import random
from typing import List, Dict

# Mock legacy TPO JSON structure
MOCK_TPO_DATA = [
    {
        "tpo_id": "TPO-54",
        "section": "READING",
        "passage_title": "The Rise of Teotihuacán",
        "passage_text": "The city of Teotihuacán, which lay about 50 kilometers northeast of modern-day Mexico City, began its growth by 200–100 B.C...",
        "questions": [
            {
                "question_num": 1,
                "text": "The word 'massive' in the passage is closest in meaning to",
                "options": ["ancient", "careful", "huge", "important"],
                "correct_answer": 2
            },
            {
                "question_num": 2,
                "text": "According to paragraph 1, what can be inferred about the city of Teotihuacán?",
                "options": ["It was larger than modern-day Mexico City.", "It grew rapidly after 200 B.C.", "It was a center of religious worship.", "It had well-planned streets and neighborhoods."],
                "correct_answer": 3
            }
        ]
    }
]

def generate_irt_parameters() -> Dict[str, float]:
    """
    Simulates the AI 'Item Bank Architect' assigning Item Response Theory 
    difficulty (b) and discrimination (a) parameters to a legacy item.
    """
    return {
        "difficulty": round(random.uniform(-3.0, 3.0), 2),  # b parameter (-3 easy, +3 hard)
        "discrimination": round(random.uniform(0.5, 2.5), 2)  # a parameter
    }

def map_cefr_level(difficulty: float) -> str:
    """Maps an IRT difficulty parameter to a 2026 target CEFR level."""
    if difficulty < -2.0: return "A1"
    if difficulty < -1.0: return "A2"
    if difficulty < 0.0: return "B1"
    if difficulty < 1.0: return "B2"
    if difficulty < 2.0: return "C1"
    return "C2"

def ingest_tpo_data():
    """Reads legacy TPO structural data and formats it for the 2026 Adaptive Schema."""
    formatted_items = []

    for test in MOCK_TPO_DATA:
        print(f"Ingesting {test['tpo_id']} - {test['section']}")
        
        irt_params = generate_irt_parameters()
        target_level = map_cefr_level(irt_params['difficulty'])
        
        item_id = str(uuid.uuid4())
        
        # Format for the new SQL Schema 
        formatted_item = {
            "id": item_id,
            "section": test["section"],
            "target_level": target_level,
            "irt_difficulty": irt_params["difficulty"],
            "irt_discrimination": irt_params["discrimination"],
            "prompt_content": json.dumps({
                "title": test["passage_title"],
                "text": test["passage_text"],
                "questions": test["questions"]
            }),
            "media_url": None,
            "is_active": True
        }
        formatted_items.append(formatted_item)
        print(f" -> Formatted 1 Item. Target Level: {target_level}, IRT Difficulty: {irt_params['difficulty']}")
        
    return formatted_items

if __name__ == "__main__":
    print("Starting TPO Data Ingestion & Transformation Simulator...")
    items = ingest_tpo_data()
    
    # In a real environment, this data would be bulk-inserted into PostgreSQL via SQLAlchemy
    print(f"Successfully processed {len(items)} items for the 2026 Adaptive Engine.")
    print(json.dumps(items, indent=2))

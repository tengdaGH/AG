# ============================================================
# Purpose:       Migrate C-Test items from legacy 'gaps' format to standard 'questions' format.
# Usage:         python backend/scripts/migrate_format.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import json
import re
import os
import sys

# Set up paths to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus, TaskType
from app.database.connection import SessionLocal

def migrate_cw_items():
    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.DRAFT).all()
    # Also check REVIEW items
    review_items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.REVIEW).all()
    all_items = items + review_items
    
    count = 0
    for item in all_items:
        try:
            data = json.loads(item.prompt_content)
            # Check if it's the 'gaps' format
            if 'gaps' in data and 'questions' not in data:
                new_questions = []
                new_text = data['text']
                
                # Sort gaps by position in text if possible, or just use as is
                for i, gap in enumerate(data['gaps']):
                    ans = gap['answer']
                    trunc_word = gap['position']
                    # Convert 'deter_ _ _ _ _' to 'deter_____'
                    clean_trunc = re.sub(r' +', '', trunc_word)
                    
                    # Ensure the text has the clean_trunc or replace it
                    if trunc_word in new_text:
                        new_text = new_text.replace(trunc_word, "____")
                    
                    new_questions.append({
                        "question_num": i + 1,
                        "text": clean_trunc,
                        "options": [ans], # In C-test format, we often just have the correct answer or a few choices
                        "correct_answer": 0
                    })
                
                data['questions'] = new_questions
                data['text'] = new_text
                # Cleanup old fields
                if 'gaps' in data: del data['gaps']
                
                item.prompt_content = json.dumps(data)
                item.lifecycle_status = ItemStatus.DRAFT
                item.generation_notes = "Migrated from gaps format to standard questions format."
                count += 1
        except Exception as e:
            print(f"Error migrating {item.id}: {e}")
            
    db.commit()
    print(f"Successfully migrated {count} items.")
    db.close()

if __name__ == "__main__":
    migrate_cw_items()

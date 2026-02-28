import sys
import json
from pathlib import Path
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.database.connection import engine, Base
from app.models.models import TestItem, IeltsPassage

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def unify_keys():
    print("UNIFYING JSON QUESTION KEYS TO 'question_text' IN ALL ITEMS...")
    db = SessionLocal()
    try:
        # 1. Update TOEFL test items
        toefl_items = db.query(TestItem).all()
        toefl_count = 0
        for item in toefl_items:
            try:
                pc = json.loads(item.prompt_content)
                changed = False
                
                # Check for questions inside the prompt_content
                if "questions" in pc and isinstance(pc["questions"], list):
                    for q in pc["questions"]:
                        # Extract the actual text value from multiple possible keys
                        q_text = q.pop("question", None)
                        if q_text is None:
                            q_text = q.pop("text", None)
                        
                        # Only set question_text if there was some text to move
                        # or if it already exists we just ensure others are deleted
                        if q_text is not None and "question_text" not in q:
                            q["question_text"] = q_text
                            changed = True
                        elif "question_text" in q and q_text is not None:
                            # It has question_text but also had question or text, which we popped
                            changed = True
                
                if changed:
                    item.prompt_content = json.dumps(pc)
                    toefl_count += 1
            except Exception as e:
                print(f"Error processing TOEFL item {item.id}: {e}")
                
        # 2. Update IELTS paragraphs (they might have inline questions, though usually separate models)
        ielts_passages = db.query(IeltsPassage).all()
        ielts_count = 0
        for p in ielts_passages:
            try:
                changed = False
                paragraphs = p.paragraphs
                # Unlikely to have questions inside paragraphs here, but let's check
                if isinstance(paragraphs, list):
                    for idx, para in enumerate(paragraphs):
                        if isinstance(para, dict):
                            pass
                            # Usually IELTS paragraphs are just text / labels
                
                if changed:
                    p.paragraphs = paragraphs # Wait, if we mutated it
                    ielts_count += 1
            except Exception as e:
                pass

        db.commit()
        print(f"DONE! Unified JSON in {toefl_count} TOEFL items.")
        
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    unify_keys()

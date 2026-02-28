#!/usr/bin/env python3
import sys
import uuid
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.database.connection import engine, Base
from app.models.models import TestItem, TestItemQuestion, TaskType

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate():
    print("Creating TestItemQuestion table if it doesn't exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we already migrated
    existing_q_count = db.query(TestItemQuestion).count()
    if existing_q_count > 0:
        print(f"TestItemQuestion table already contains {existing_q_count} records. Clearing for a fresh migration...")
        db.query(TestItemQuestion).delete()
        db.commit()

    # Get all COMPLETE_THE_WORDS items
    c_test_items = db.query(TestItem).filter(TestItem.task_type == TaskType.COMPLETE_THE_WORDS).all()
    print(f"Found {len(c_test_items)} C-Test items to migrate.")

    total_questions_migrated = 0

    for item in c_test_items:
        try:
            content = json.loads(item.prompt_content)
            questions = content.get("questions", [])
            
            for q in questions:
                # Ensure we have the necessary data
                question_num = q.get("question_num")
                correct_answer = q.get("correct_answer")
                
                if question_num is None or correct_answer is None:
                    print(f"WARNING: Item {item.id} has malformed question: {q}")
                    continue

                new_q = TestItemQuestion(
                    id=str(uuid.uuid4()),
                    test_item_id=item.id,
                    question_number=question_num,
                    correct_answer=str(correct_answer).strip(),
                    options=q.get("options"), # Some older items had options array
                    irt_difficulty=0.0,
                    irt_discrimination=1.0,
                    exposure_count=0,
                    is_active=True
                )
                db.add(new_q)
                total_questions_migrated += 1
                
        except json.JSONDecodeError:
            print(f"WARNING: Item {item.id} has invalid JSON prompt_content.")
        except Exception as e:
            print(f"ERROR: Failed to migrate item {item.id}: {e}")

    try:
        db.commit()
        print(f"Migration successful! Inserted {total_questions_migrated} TestItemQuestion records.")
    except Exception as e:
        db.rollback()
        print(f"Database commit failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

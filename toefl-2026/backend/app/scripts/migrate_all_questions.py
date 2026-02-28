import sys
import uuid
import json
from pathlib import Path
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path("/Users/tengda/Documents/Antigravity/toefl-2026/backend").resolve()))
from app.database.connection import engine, Base
from app.models.models import TestItem, TestItemQuestion, TaskType

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate():
    print("MIGRATING ALL NESTED QUESTIONS TO test_item_questions...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clear existing
    existing = db.query(TestItemQuestion).count()
    if existing > 0:
        print(f"Clearing {existing} old question records...")
        db.query(TestItemQuestion).delete()
        db.commit()

    migrated_count = 0
    # Items to process
    target_tasks = [
        TaskType.COMPLETE_THE_WORDS,
        TaskType.READ_ACADEMIC_PASSAGE,
        TaskType.READ_IN_DAILY_LIFE,
        TaskType.LISTEN_CHOOSE_RESPONSE,
        TaskType.LISTEN_ACADEMIC_TALK,
        TaskType.LISTEN_ANNOUNCEMENT,
        TaskType.LISTEN_CONVERSATION
    ]

    items = db.query(TestItem).filter(TestItem.task_type.in_(target_tasks)).all()
    print(f"Scanning {len(items)} items for nested questions...")

    for item in items:
        try:
            pc = json.loads(item.prompt_content)
            questions = pc.get("questions")
            if not questions or not isinstance(questions, list):
                continue
            
            for idx, q in enumerate(questions):
                # Try to extract the number
                q_num = q.get("question_num") or q.get("number") or (idx + 1)
                
                ans = q.get("correct_answer")
                if ans is None:
                    # Some don't have correct_answer?
                    continue

                new_q = TestItemQuestion(
                    id=str(uuid.uuid4()),
                    test_item_id=item.id,
                    question_number=q_num,
                    question_text=q.get("question") or q.get("text"),
                    question_audio_url=q.get("audio_path") or q.get("audio_url"),
                    replay_audio_url=q.get("replay_audio_path") or q.get("replay_audio_url"),
                    correct_answer=str(ans).strip(),
                    options=q.get("options", []),
                    irt_difficulty=0.0,
                    irt_discrimination=1.0,
                    exposure_count=0,
                    is_active=True
                )
                db.add(new_q)
                migrated_count += 1
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"ERROR: {item.id} -> {e}")

    try:
        db.commit()
        print(f"DONE! Successfully inserted {migrated_count} question records.")
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

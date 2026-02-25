# ============================================================
# Purpose:       Verify and fix incorrect answer keys in JSON-Import academic passage items using Gemini.
# Usage:         python backend/scripts/fix_answer_keys.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""Fix incorrect answer keys in JSON-Import academic passage items."""
import os, sys, json, re, logging
import google.generativeai as genai
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.connection import SessionLocal
from app.models.models import TestItem, TaskType, ItemVersionHistory

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def verify_and_fix_keys(passage_text: str, questions: list) -> list[int]:
    """Use Gemini to verify and return correct answer indices for each question."""
    q_block = ""
    for qi, q in enumerate(questions):
        stem = q.get("text", "")
        options = q.get("options", [])
        q_block += f"\nQ{qi+1}: {stem}\n"
        for oi, o in enumerate(options):
            q_block += f"  {chr(65+oi)}) {o}\n"

    prompt = f"""You are a TOEFL reading comprehension expert. Given this passage and questions, determine the CORRECT answer for each question.

PASSAGE:
{passage_text}

QUESTIONS:
{q_block}

For each question, output ONLY the question number and the correct letter (A, B, C, or D), one per line, like:
Q1: D
Q2: A
Q3: C
Q4: B

Be very precise. The correct answer must be directly supported by the passage text."""

    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Parse results into ordered list
    results = [None] * len(questions)
    for line in text.split('\n'):
        m = re.match(r'Q(\d+):\s*([A-D])', line.strip())
        if m:
            qidx = int(m.group(1)) - 1  # zero-based
            letter = m.group(2)
            idx = ord(letter) - ord('A')
            if 0 <= qidx < len(questions):
                results[qidx] = idx
    
    return results


def main():
    db = SessionLocal()
    items = db.query(TestItem).filter(
        TestItem.task_type == TaskType.READ_ACADEMIC_PASSAGE,
        TestItem.generated_by_model == "JSON-Import"
    ).all()

    logging.info(f"Found {len(items)} JSON-Import academic passage items.")
    total_fixed = 0

    for item in items:
        data = json.loads(item.prompt_content)
        title = data.get("title", "?")
        text = data.get("text", "")
        questions = data.get("questions", [])

        logging.info(f"\nVerifying: {title}")

        try:
            corrections = verify_and_fix_keys(text, questions)
        except Exception as e:
            logging.error(f"  Gemini call failed: {e}")
            continue

        changed = False
        for qi, q in enumerate(questions):
            new_idx = corrections[qi]
            if new_idx is None:
                logging.warning(f"  Q{qi+1}: No answer from Gemini")
                continue
                
            old_idx = q.get("correct_answer")
            opts = q.get("options", [])
            stem = q.get("text", "")[:60]
            
            if old_idx != new_idx:
                old_label = f"{chr(65+old_idx)}) {opts[old_idx][:40]}" if isinstance(old_idx, int) and 0 <= old_idx < len(opts) else str(old_idx)
                new_label = f"{chr(65+new_idx)}) {opts[new_idx][:40]}" if 0 <= new_idx < len(opts) else str(new_idx)
                logging.info(f"  Q{qi+1}: {old_label}  →  {new_label}")
                q["correct_answer"] = new_idx
                changed = True
            else:
                logging.info(f"  Q{qi+1}: Already correct ({chr(65+old_idx)})")
        
        # Also fix missing question_num
        for qi, q in enumerate(questions):
            if q.get("question_num") is None:
                q["question_num"] = qi + 1
                changed = True

        if changed:
            db.add(ItemVersionHistory(
                item_id=item.id,
                version_number=item.version,
                prompt_content=item.prompt_content,
                changed_by="Answer-Key-Fixer"
            ))
            item.prompt_content = json.dumps(data)
            item.version += 1
            item.generation_notes = "Answer keys verified and corrected by Gemini."
            db.commit()
            total_fixed += 1
            logging.info(f"  ✅ Updated {title}")
        else:
            logging.info(f"  ✅ No changes needed for {title}")

    logging.info(f"\nDone. Fixed {total_fixed}/{len(items)} items.")
    db.close()

if __name__ == "__main__":
    main()

# ============================================================
# Purpose:       Remediate all REVIEW-status items: LLM rewrites + key distribution balancing + QA re-run.
# Usage:         python backend/scripts/remediate_all.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import sys
import os
import json
import random
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.connection import SessionLocal
from app.models.models import TestItem, ItemStatus, ItemVersionHistory
from scripts.gauntlet_qa import qa_single_item, run_llm_remediation

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def balance_keys(data):
    """Programmatically balance key distribution."""
    if "questions" not in data:
        return data
        
    questions = data["questions"]
    n = len(questions)
    
    # Create target key distribution
    # e.g., for 3 qs: [0, 1, 2], for 4 qs: [0, 1, 2, 3], for 5: [0, 1, 2, 3, 0]
    targets = []
    for i in range(n):
        targets.append(i % 4)
    random.shuffle(targets)
    
    for i, q in enumerate(questions):
        options = q.get("options", [])
        if not options or len(options) != 4:
            continue
            
        correct_idx = q.get("correct_answer", 0)
        correct_text = options[correct_idx]
        
        target_idx = targets[i]
        
        # We want correct_text to be at target_idx
        new_options = list(options)
        new_options.remove(correct_text)
        new_options.insert(target_idx, correct_text)
        
        q["options"] = new_options
        q["correct_answer"] = target_idx
        
    return data

def main():
    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.lifecycle_status == ItemStatus.REVIEW).all()
    
    for item in items:
        logging.info(f"Processing item {item.id[:8]} - {item.generation_notes}")
        try:
            data = json.loads(item.prompt_content)
        except Exception as e:
            logging.error(f"Failed to load json for {item.id}, {e}")
            continue

        needs_llm = False
        notes = item.generation_notes
        if "text length error" in notes or "distressing topic" in notes or "too short" in notes:
            needs_llm = True
            
        if needs_llm:
            logging.info(f"Using LLM for {item.id}")
            # Ensure proper prompt to handle short options
            llm_prompt = notes
            if "too short" in notes:
                llm_prompt += " Ensure ALL options are at least 5 characters long by adding descriptive words."
            if "text length" in notes:
                llm_prompt += " Add a few more sentences to expand the passage slightly to be within 15-150 words."
            if "distressing topic" in notes:
                llm_prompt += " Remove any mention of the distressed topic. Choose a neutral alternative."
                
            new_json_str = run_llm_remediation(item.prompt_content, item.task_type.value, llm_prompt)
            if new_json_str:
                data = json.loads(new_json_str)
            else:
                logging.error(f"LLM remediation failed for {item.id}")
                continue
                
        # Always run balance_keys just in case (e.g. LLM didn't distribute them, or pure imbalance)
        data = balance_keys(data)
        
        # Save to DB
        item.prompt_content = json.dumps(data)
        item.lifecycle_status = ItemStatus.DRAFT # Reset to DRAFT so qa_single_item picks it
        db.add(ItemVersionHistory(item_id=item.id, version_number=item.version, prompt_content=item.prompt_content, changed_by="Auto-Remediator"))
        item.version += 1
        db.commit()
        
        logging.info(f"Running QA on {item.id}")
        qa_res = qa_single_item(item.id)
        logging.info(f"QA result for {item.id}: {qa_res}")
        
    db.close()

if __name__ == "__main__":
    main()

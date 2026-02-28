# ============================================================
# Purpose:       Automatically remediate MCQ option length bias in the database using Gemini.
# Usage:         python agents/scripts/remediate_option_bias.py [--apply]
# Created:       2026-02-26
# ============================================================
import os, sys, json, re
from dotenv import load_dotenv
from google import genai
from google.genai import types

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal
from app.models.models import TestItem, SectionType, TaskType

load_dotenv(os.path.join(backend_dir, '.env'))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY in backend/.env.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def word_count(text):
    return len(text.split()) if text else 0

def check_bias(options, correct_index):
    if not options or correct_index is None or correct_index >= len(options):
        return False, 0, 0
    
    wcs = [word_count(o) for o in options]
    key_wc = wcs[correct_index]
    dist_wcs = [w for i, w in enumerate(wcs) if i != correct_index]
    mean_dist = sum(dist_wcs) / max(len(dist_wcs), 1)
    
    # Bias if key is >30% longer than mean distractor OR parity ratio > 2.0
    is_biased = (key_wc > mean_dist * 1.3) or (max(wcs) > min(wcs) * 2.0)
    return is_biased, key_wc, mean_dist

REMEDIATION_PROMPT = """You are an ETS-certified Language Assessment Designer.
Your task is to rebalance the length of multiple-choice options for a TOEFL 2026 item to eliminate "longest answer" bias.

PASSAGE:
{passage}

ORIGINAL QUESTION:
Stem: {stem}
Options:
{options_formatted}
Correct Answer Index: {correct_index}

REQUIREMENTS:
1. Rewrite the 4 options so they are of approximately EQUAL LENGTH and COMPLEXITY.
2. The correct answer MUST NOT be notably longer or shorter than the distractors.
3. Preserve the exact meaning and correctness of the correct answer.
4. Distractors must remain plausible but clearly incorrect based on the passage.
5. Do NOT change the correct answer index.
6. The longest option word count should be within 1.5x of the shortest.

OUTPUT FORMAT:
Return ONLY a JSON list of 4 strings (the new options).
Example: ["Option A", "Option B", "Option C", "Option D"]
"""

def remediate_question(passage, stem, options, correct_index):
    opts_fmt = "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
    prompt = REMEDIATION_PROMPT.format(
        passage=passage,
        stem=stem,
        options_formatted=opts_fmt,
        correct_index=correct_index
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(temperature=0.3)
    )
    
    text = response.text
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return None

def run():
    apply_changes = "--apply" in sys.argv
    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.task_type == TaskType.READ_ACADEMIC_PASSAGE).all()
    
    remediated_count = 0
    total_checked = 0
    
    print(f"Scanning {len(items)} items for option bias...")
    
    for item in items:
        try:
            pc = json.loads(item.prompt_content)
            passage = pc.get("text") or pc.get("content") or pc.get("passage") or ""
            questions = pc.get("questions", [])
            
            item_changed = False
            for q in questions:
                stem = q.get("text") or q.get("question") or q.get("stem") or ""
                options = q.get("options", [])
                correct = q.get("correct_answer")
                if correct is None: correct = q.get("correct")
                if correct is None: correct = q.get("answer")
                
                total_checked += 1
                is_biased, k_wc, m_wc = check_bias(options, correct)
                
                if is_biased:
                    print(f"  [BIASED] Item {item.id[:8]} Q: {stem[:40]}... (Key {k_wc}w vs Dist {m_wc:.1f}w)")
                    new_options = remediate_question(passage, stem, options, correct)
                    if new_options and len(new_options) == 4:
                        q["options"] = new_options
                        # Standardize keys while we are at it
                        q["correct_answer"] = correct
                        item_changed = True
                        print(f"    ✓ Options balanced: {[word_count(o) for o in new_options]}")
                    else:
                        print(f"    × Failed to remediate.")

            if item_changed:
                item.prompt_content = json.dumps(pc)
                remediated_count += 1
                if apply_changes:
                    db.commit()
                    print(f"  ✓ Saved changes to DB.")
                else:
                    print(f"  [DRY RUN] No changes saved.")
                    
        except Exception as e:
            print(f"  Error processing item {item.id}: {e}")
            continue

    db.close()
    print(f"\nDone. Checked {total_checked} questions. Remediated {remediated_count} items.")
    if not apply_changes:
        print("NOTE: Run with --apply to actually update the database.")

if __name__ == "__main__":
    run()

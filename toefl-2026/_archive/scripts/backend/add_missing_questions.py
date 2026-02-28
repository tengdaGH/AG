# ============================================================
# Purpose:       Add missing MCQ questions to academic passages to reach the ETS-mandated 5 per item via Gemini.
# Usage:         python backend/scripts/add_missing_questions.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Add missing questions to academic passage items to reach the ETS-mandated 5.

Uses Gemini 2.5 Flash to generate questions of the missing types:
  - Main Idea, Factual Detail, Inference, Vocabulary, Rhetorical Purpose
"""
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

QUESTION_TYPES = {
    "main_idea": "Main Idea / Purpose (e.g., 'What is the passage mainly about?')",
    "factual": "Factual Detail (e.g., 'According to the passage, ...')",
    "inference": "Inference (e.g., 'What can be inferred from the passage?')",
    "vocabulary": "Vocabulary in Context (e.g., 'The word X in the passage is closest in meaning to...')",
    "rhetorical": "Rhetorical Purpose (e.g., 'The author mentions X in order to...')",
}


def classify_question(stem: str) -> str:
    s = stem.lower()
    if "mainly about" in s or "main purpose" in s or "main idea" in s:
        return "main_idea"
    if "according to the passage" in s:
        return "factual"
    if "infer" in s or "suggest" in s or "imply" in s:
        return "inference"
    if ("word" in s or "phrase" in s) and ("meaning" in s or "closest" in s):
        return "vocabulary"
    if "in order to" in s or "author mentions" in s or "author uses" in s or "author describes" in s:
        return "rhetorical"
    return "factual"  # default


def generate_missing_questions(passage_text: str, existing_questions: list, missing_types: list, level: str) -> list:
    """Use Gemini to generate questions of the specified types."""
    existing_block = ""
    for qi, q in enumerate(existing_questions):
        existing_block += f"\nQ{qi+1}: {q.get('text', '')}\n"

    type_descriptions = "\n".join(f"- {QUESTION_TYPES[t]}" for t in missing_types)
    num_needed = 5 - len(existing_questions)

    prompt = f"""You are an ETS-certified TOEFL item writer. Generate exactly {num_needed} new multiple-choice question(s) for this academic reading passage at CEFR level {level}.

PASSAGE:
{passage_text}

EXISTING QUESTIONS (do NOT duplicate these):
{existing_block}

Generate questions of these missing types:
{type_descriptions}

STRICT RULES:
1. Each question must have exactly 4 options (A, B, C, D)
2. The correct answer (key) must be unambiguously supported by the passage
3. Distractors must be plausible but clearly wrong when checked against the passage
4. Do NOT use "all of the above" or "none of the above"
5. Do NOT use absolute words like "always", "never" in the key
6. All options must be parallel in grammar and similar in length
7. For vocabulary questions, pick a word actually used in the passage

Output as JSON array:
[
  {{
    "text": "question stem",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": 0
  }}
]

correct_answer is the 0-based index (0=A, 1=B, 2=C, 3=D).
Return ONLY the JSON array, no markdown fences."""

    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Strip markdown fences if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    return json.loads(text)


def main():
    db = SessionLocal()
    items = db.query(TestItem).filter(
        TestItem.task_type == TaskType.READ_ACADEMIC_PASSAGE
    ).all()

    logging.info(f"Reviewing {len(items)} academic passage items.")
    updated = 0

    for item in items:
        data = json.loads(item.prompt_content)
        title = data.get("title", "?")
        text = data.get("text", "")
        questions = data.get("questions", [])

        if len(questions) >= 5:
            logging.info(f"✅ {title}: Already has {len(questions)} questions")
            continue

        # Find existing types
        existing_types = set()
        for q in questions:
            existing_types.add(classify_question(q.get("text", "")))

        # Determine missing types
        all_types = {"main_idea", "factual", "inference", "vocabulary", "rhetorical"}
        missing_types = list(all_types - existing_types)

        # If we need more questions than missing types, add more factual
        num_needed = 5 - len(questions)
        while len(missing_types) < num_needed:
            missing_types.append("factual")
        missing_types = missing_types[:num_needed]

        logging.info(f"🔧 {title}: Has {len(questions)} questions, need {num_needed} more ({', '.join(missing_types)})")

        try:
            new_questions = generate_missing_questions(text, questions, missing_types, item.target_level.value)
        except Exception as e:
            logging.error(f"  Gemini failed: {e}")
            continue

        if not new_questions or len(new_questions) < num_needed:
            logging.warning(f"  Got only {len(new_questions) if new_questions else 0} questions, needed {num_needed}")
            if not new_questions:
                continue

        # Save version history
        db.add(ItemVersionHistory(
            item_id=item.id,
            version_number=item.version,
            prompt_content=item.prompt_content,
            changed_by="Question-Generator"
        ))

        # Append new questions
        start_num = len(questions) + 1
        for qi, nq in enumerate(new_questions[:num_needed]):
            nq["question_num"] = start_num + qi
            # Clean option prefixes if present
            cleaned_opts = []
            for opt in nq.get("options", []):
                opt = re.sub(r'^[A-D]\)\s*', '', opt)
                cleaned_opts.append(opt)
            nq["options"] = cleaned_opts
            questions.append(nq)

        data["questions"] = questions
        item.prompt_content = json.dumps(data)
        item.version += 1
        item.generation_notes = f"Questions expanded to {len(questions)} for ETS compliance."
        db.commit()
        updated += 1
        logging.info(f"  ✅ Now has {len(questions)} questions")

    logging.info(f"\nDone. Updated {updated} items.")
    db.close()

if __name__ == "__main__":
    main()

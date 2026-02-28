# ============================================================
# Purpose:       Omni-Agent QA pipeline: content, fairness, MCQ quality, editorial checks with auto-remediation.
# Usage:         python backend/scripts/gauntlet_qa.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import logging
import re
from scripts.c_test_generator import generate_c_test
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up paths to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.models import TestItem, ItemStatus, ItemReviewLog, ItemVersionHistory, TaskType
from app.database.connection import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def log_to_file(item_id: str, agent_name: str, status: str, reason: str):
    import datetime
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'qa_reviews.jsonl')
    with open(log_file, 'a', encoding='utf-8') as f:
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "item_id": item_id,
            "agent_name": agent_name,
            "status": status,
            "reason": reason,
            "reviewer": "Antigravity-Expert-v3"
        }
        f.write(json.dumps(log_data) + '\n')

def run_content_agent(item_id: str, prompt_content_json: str, task_type: TaskType) -> tuple[bool, str]:
    try:
        data = json.loads(prompt_content_json)
    except Exception as e:
        return False, f"JSON Parse Error: {str(e)}"

    if task_type == TaskType.COMPLETE_THE_WORDS:
        questions = data.get("questions", [])
        text = data.get("text", "") or data.get("content", "")
        if len(questions) != 10:
            return False, f"CRITICAL: C-test must have exactly 10 questions. Found {len(questions)}."
        blanks_in_text = len(re.findall(r'_+', text))
        if blanks_in_text != 10:
            return False, f"CRITICAL: C-test must have exactly 10 truncated words in the passage. Found {blanks_in_text}."
        for q in questions:
            if "_" not in q.get("text", ""):
                 return False, f"Question {q.get('question_num')} is missing underscores."
            if not isinstance(q.get("correct_answer"), str):
                return False, f"Question {q.get('question_num')} must have a 'correct_answer' string (the full word), not MCQ options."
            if q.get("options"):
                return False, f"Question {q.get('question_num')} has MCQ 'options' — C-test is fill-in-the-blank, not MCQ."

    elif task_type == TaskType.BUILD_A_SENTENCE:
        fragments = data.get("fragments", [])
        if not fragments:
            return False, "Sentence Builder item must have a list of fragments."
        if not data.get("endPunctuation"):
            return False, "Sentence Builder item must have an endPunctuation field."

    elif task_type in [TaskType.READ_IN_DAILY_LIFE, TaskType.READ_ACADEMIC_PASSAGE]:
        questions = data.get("questions", [])
        if not questions:
            return False, "Reading passage must have comprehension questions."
        for q in questions:
            if len(q.get("options", [])) < 3:
                return False, f"Question {q.get('question_num')} must have at least 3 options."

    elif task_type in [TaskType.LISTEN_CONVERSATION, TaskType.LISTEN_ACADEMIC_TALK]:
        if not data.get("audioUrl"):
            # Warn but don't hard-fail — legacy items may not have audio yet
            logging.info(f"  [warn] Listening item {item_id[:8]} has no audioUrl — needs TTS generation.")

    return True, f"Content matches {task_type} technical specs."

def run_fairness_agent(item_id: str, prompt_content_json: str, task_type: TaskType) -> tuple[bool, str]:
    forbidden_topics = ["death", "cancer", "murder", "religion", "racism", "terrorism"]
    try:
        data = json.loads(prompt_content_json)
        full_text = f"{data.get('title', '')} {data.get('text', '')} {data.get('transcript', '')}".lower()
        for topic in forbidden_topics:
            if topic in full_text:
                return False, f"Fairness violation: Item mentions potentially distressing topic '{topic}'."
    except:
        pass
    return True, "Passed fairness heuristics check."

def run_editorial_agent(item_id: str, prompt_content_json: str, task_type: TaskType) -> tuple[bool, str]:
    try:
        data = json.loads(prompt_content_json)
        text = data.get("text", "") or data.get("content", "") or data.get("transcript", "")
    except:
        return False, "JSON Parse Error."

    if task_type == TaskType.COMPLETE_THE_WORDS:
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if sentences and "_" in sentences[0]:
            return False, "CRITICAL: C-test first sentence must be completely intact."

    if task_type == TaskType.READ_IN_DAILY_LIFE:
        word_count = len(text.split())
        if word_count < 15 or word_count > 155:
            return False, f"Daily Life text length error: {word_count} words (Limit 15-150)."

    if task_type == TaskType.READ_ACADEMIC_PASSAGE:
        word_count = len(text.split())
        if word_count < 100:
            return False, f"Academic passage too short: {word_count} words (Expected ~200)."
        
        # New check: Detect mid-sentence line breaks (single \n)
        if re.search(r'(?<!\n)\n(?!\n)', text):
            return False, "Formatting error: Mid-sentence line breaks (single \\n) detected. Ensure text is continuous."

    return True, "Structural and mechanics formatting adheres to specs."

# ─── MCQ Quality Agent ───────────────────────────────────────────────────
MCQ_TASK_TYPES = {
    TaskType.READ_IN_DAILY_LIFE,
    TaskType.READ_ACADEMIC_PASSAGE,
    TaskType.LISTEN_CONVERSATION,
    TaskType.LISTEN_ACADEMIC_TALK,
    TaskType.LISTEN_ANNOUNCEMENT,
    TaskType.LISTEN_CHOOSE_RESPONSE,
}

def run_mcq_agent(item_id: str, prompt_content_json: str, task_type: TaskType) -> tuple[bool, str]:
    """Validate MCQ quality: stems, keys, distractors, and key distribution."""
    if task_type not in MCQ_TASK_TYPES:
        return True, "Not an MCQ task type — skipped."

    try:
        data = json.loads(prompt_content_json)
    except Exception as e:
        return False, f"JSON Parse Error: {e}"

    questions = data.get("questions", [])
    if not questions:
        return True, "No questions to check."

    errors = []   # hard fails
    warnings = [] # soft warnings (logged but pass)
    key_positions = []

    for qi, q in enumerate(questions):
        qnum = qi + 1
        stem = q.get("text", "")
        raw_options = q.get("options", [])
        correct = q.get("correct_answer")

        # ── Normalize options: support both plain strings and {"text": ...} or {"id": ..., "text": ...} dicts ──
        options = []
        for opt in raw_options:
            if isinstance(opt, dict):
                options.append(opt.get("text", ""))
            else:
                options.append(str(opt) if opt is not None else "")

        # ── Normalize correct_answer: support integer index or letter string ('a'/'b'/'c'/'d') ──
        if isinstance(correct, str) and len(correct) == 1 and correct.lower() in 'abcd':
            correct = ord(correct.lower()) - ord('a')
        elif isinstance(correct, str):
            # Try parsing as integer string
            try:
                correct = int(correct)
            except ValueError:
                errors.append(f"Q{qnum}: Invalid correct_answer string: '{correct}'.")
                correct = None

        # ── Stem checks (skip for listening types — audio-only stimulus) ──
        AUDIO_STEM_TYPES = {TaskType.LISTEN_CHOOSE_RESPONSE, TaskType.LISTEN_ANNOUNCEMENT,
                           TaskType.LISTEN_CONVERSATION, TaskType.LISTEN_ACADEMIC_TALK}
        if task_type not in AUDIO_STEM_TYPES and len(stem.strip()) < 10:
            errors.append(f"Q{qnum}: Stem too short ({len(stem.strip())} chars, need ≥10).")

        stem_upper = stem.strip().upper()
        if " NOT " in f" {stem_upper} " or " EXCEPT " in f" {stem_upper} ":
            warnings.append(f"Q{qnum}: Stem uses negative phrasing (NOT/EXCEPT) — ETS discourages this.")

        # ── Option checks ──
        if len(options) != 4:
            errors.append(f"Q{qnum}: Must have exactly 4 options, found {len(options)}.")

        # Empty options
        for oi, opt in enumerate(options):
            if len(opt.strip()) < 5:
                errors.append(f"Q{qnum}: Option {chr(65+oi)} too short ('{opt.strip()}').")

        # Duplicate options
        lowered = [o.strip().lower() for o in options]
        if len(lowered) != len(set(lowered)):
            errors.append(f"Q{qnum}: Duplicate options detected.")

        # Forbidden patterns
        for oi, opt in enumerate(options):
            opt_low = opt.strip().lower()
            if "none of the above" in opt_low or "all of the above" in opt_low:
                errors.append(f"Q{qnum}: Option {chr(65+oi)} uses 'none/all of the above' (ETS violation).")

        # Parallel length — longest ≤ 3× shortest
        if len(options) >= 2:
            lengths = [len(o.strip()) for o in options if o.strip()]
            if lengths:
                shortest, longest = min(lengths), max(lengths)
                if shortest > 0 and longest > 3 * shortest:
                    warnings.append(f"Q{qnum}: Option lengths unbalanced ({shortest}–{longest} chars) — may cue the key.")

        # ── Key checks ──
        if correct is None:
            pass  # already recorded error above
        elif not isinstance(correct, int) or correct < 0 or (options and correct >= len(options)):
            errors.append(f"Q{qnum}: Invalid correct_answer: {correct}.")
        elif options:
            key_text = options[correct].strip()
            key_positions.append(correct)

            # Key not shortest
            opt_lengths = [len(o.strip()) for o in options]
            if all(len(key_text) < len(o.strip()) for oi, o in enumerate(options) if oi != correct and o.strip()):
                warnings.append(f"Q{qnum}: Key is the shortest option — may cue test-takers.")

            # Absolutes in key
            absolute_words = ["always", "never", "only", "none", "every", "no one"]
            for aw in absolute_words:
                if f" {aw} " in f" {key_text.lower()} " or key_text.lower().startswith(f"{aw} "):
                    warnings.append(f"Q{qnum}: Key contains absolute word '{aw}'.")

    # ── Key distribution check ──
    if len(key_positions) >= 3:
        from collections import Counter
        pos_counts = Counter(key_positions)
        total = len(key_positions)
        for pos, count in pos_counts.items():
            if count / total > 0.5:
                errors.append(f"Key distribution imbalance: {chr(65+pos)} used for {count}/{total} keys ({count/total:.0%}).")
        if len(pos_counts) == 1:
            errors.append(f"All {total} keys are in position {chr(65+key_positions[0])} — not acceptable.")

    # ── Return result ──
    if errors:
        return False, "; ".join(errors)

    if warnings:
        logging.info(f"  MCQ warnings for {item_id[:8]}: {'; '.join(warnings)}")

    return True, "MCQ quality checks passed."

def run_remediation_agent(item_id: str, prompt_content_json: str, task_type: TaskType, failure_stage: str, failure_reason: str) -> tuple[str, str]:
    if "First sentence" in failure_reason:
        return "FIX", "Formatting fix: Restore primary context sentence."
    if "exactly 10" in failure_reason or "length error" in failure_reason:
        return "REWRITE", "Structural rewrite required via LLM fallback."
    return "FIX", "Applying standard programmatic remediation."

def run_llm_remediation(original_content: str, task_type: str, fail_reason: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logging.error("google-genai not installed, skipping LLM remediation.")
        return None
    client = genai.Client(api_key=api_key)
    prompt = f"""
The following TOEFL test item of type '{task_type}' failed quality assurance.
Failure Reason: {fail_reason}

Original Content JSON:
{original_content}

Please provide a rewritten JSON object for "prompt_content" that fully fixes the failure reason while maintaining the original meaning as much as possible.
Ensure EXACT compliance with all TOEFL 2026 specs.
For C-Test (Complete the Words), there MUST be EXACTLY 10 blanks (words with underscores like 'b_s'), and the first sentence MUST be completely intact with no blanks.
For Reading, passages must be the correct length.

Return ONLY a valid JSON object. Do not wrap it in markdown.
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )
        content_text = response.text
        match = re.search(r'\{.*\}', content_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            json.loads(json_str)
            return json_str
    except Exception as e:
        logging.error(f"LLM Remediation failed: {e}")
    return None

def execute_remediation(item_id: str, original_content: str, task_type: TaskType, decision: str, rem_reason: str, fail_stage: str, fail_reason: str) -> str | None:
    if decision == "REWRITE":
        return run_llm_remediation(original_content, task_type.value, fail_reason)
    if decision != "FIX":
        return None
    try:
        data = json.loads(original_content)
        if "First sentence" in fail_reason:
             text = data.get("text", "")
             parts = text.split(".", 1)
             if len(parts) > 1:
                 data["text"] = parts[0].replace("_", "") + "." + parts[1]
                 return json.dumps(data)
    except:
        pass
    return None


def auto_remediate_c_test(item, db) -> dict:
    """Deterministically regenerate a C-test item. Returns a result dict."""
    topic_hint = "General topic"
    try:
        data = json.loads(item.prompt_content)
        topic_hint = data.get("text", "")[:100]
    except:
        pass

    for attempt in range(2):
        new_data = generate_c_test(item.target_level.value, topic_hint)
        if not new_data:
            continue
        new_data["id"] = item.id
        new_content = json.dumps(new_data)
        c_pass, c_reason = run_content_agent(item.id, new_content, item.task_type)
        e_pass, e_reason = run_editorial_agent(item.id, new_content, item.task_type)
        if c_pass and e_pass:
            db.add(ItemVersionHistory(item_id=item.id, version_number=item.version, prompt_content=item.prompt_content, changed_by="Auto-Remediator"))
            item.prompt_content = new_content
            item.version += 1
            item.lifecycle_status = ItemStatus.FIELD_TEST
            item.is_active = True
            item.generation_notes = f"Auto-remediated (deterministic). Passed all QA."
            db.commit()
            return {"id": item.id, "status": "Remediated", "reason": "Deterministic rewrite passed QA."}
    return None  # caller falls through to REVIEW

def _run_single(item, db) -> dict:
    """Run QA checks on a single item and auto-remediate if possible."""
    logging.info(f"--- Reviewing Item [{item.task_type}] ID: {item.id} ---")

    def record_review(stage, is_pass, reason):
        action = "PASS" if is_pass else "FAIL"
        log = ItemReviewLog(
            item_id=item.id,
            stage_name=stage,
            reviewer="Antigravity-Expert-v3",
            action=action,
            notes=reason
        )
        db.add(log)
        log_to_file(item.id, stage, action, reason)

    # 1. Content
    c_pass, c_reason = run_content_agent(item.id, item.prompt_content, item.task_type)
    record_review("Content Agent", c_pass, c_reason)

    if not c_pass:
        # Try deterministic auto-remediation for C-tests
        if item.task_type == TaskType.COMPLETE_THE_WORDS:
            result = auto_remediate_c_test(item, db)
            if result:
                record_review("Auto-Remediation", True, "Deterministic rewrite passed QA.")
                return result

        # Fallback: legacy remediation
        decision, rem_note = run_remediation_agent(item.id, item.prompt_content, item.task_type, "Content", c_reason)
        new_content = execute_remediation(item.id, item.prompt_content, item.task_type, decision, rem_note, "Content", c_reason)
        if new_content:
            db.add(ItemVersionHistory(item_id=item.id, version_number=item.version, prompt_content=item.prompt_content, changed_by="Auto-Remediator"))
            item.version += 1
            item.prompt_content = new_content
            item.lifecycle_status = ItemStatus.DRAFT
            item.generation_notes = f"[Remediated] {rem_note}"
            db.commit()
            return {"id": item.id, "status": "Remediated", "reason": c_reason}

        item.lifecycle_status = ItemStatus.REVIEW
        item.generation_notes = f"[ACTION REQUIRED: {decision}] Failed Content: {c_reason}"
        db.commit()
        return {"id": item.id, "status": "Failed", "reason": c_reason}

    # 2. Fairness
    f_pass, f_reason = run_fairness_agent(item.id, item.prompt_content, item.task_type)
    record_review("Fairness Agent", f_pass, f_reason)
    if not f_pass:
        item.lifecycle_status = ItemStatus.REVIEW
        item.generation_notes = f"[Fairness Violation] {f_reason}"
        db.commit()
        return {"id": item.id, "status": "Failed", "reason": f_reason}

    # 3. MCQ Quality
    m_pass, m_reason = run_mcq_agent(item.id, item.prompt_content, item.task_type)
    record_review("MCQ Agent", m_pass, m_reason)
    if not m_pass:
        item.lifecycle_status = ItemStatus.REVIEW
        item.generation_notes = f"[MCQ Quality Error] {m_reason}"
        db.commit()
        return {"id": item.id, "status": "Failed", "reason": m_reason}

    # 4. Editorial
    e_pass, e_reason = run_editorial_agent(item.id, item.prompt_content, item.task_type)
    record_review("Editorial Agent", e_pass, e_reason)
    if not e_pass:
        # Try deterministic auto-remediation for C-tests failing editorial
        if item.task_type == TaskType.COMPLETE_THE_WORDS:
            result = auto_remediate_c_test(item, db)
            if result:
                record_review("Auto-Remediation", True, "Deterministic rewrite passed QA.")
                return result

        item.lifecycle_status = ItemStatus.REVIEW
        item.generation_notes = f"[Editorial Error] {e_reason}"
        db.commit()
        return {"id": item.id, "status": "Failed", "reason": e_reason}

    # Passed
    item.lifecycle_status = ItemStatus.FIELD_TEST
    item.is_active = True
    item.generation_notes = f"Verified by Omni-Agent - {item.task_type} compliant."
    db.commit()
    return {"id": item.id, "status": "Passed", "reason": "All checks passed."}


def qa_pipeline(limit=50):
    db = SessionLocal()
    items = db.query(TestItem).filter(
        TestItem.lifecycle_status.in_([ItemStatus.DRAFT, ItemStatus.REVIEW])
    ).limit(limit).all()

    if not items:
        logging.info("No DRAFT/REVIEW items found in queue.")
        db.close()
        return []

    logging.info(f"Picked up {len(items)} items for Omni-Agent Review.")
    results = []
    for item in items:
        results.append(_run_single(item, db))
    db.close()
    return results


def qa_single_item(item_id: str):
    """Run QA + auto-remediation on a single item by ID."""
    db = SessionLocal()
    item = db.query(TestItem).filter(TestItem.id == item_id).first()
    if not item:
        db.close()
        return {"id": item_id, "status": "Error", "reason": "Item not found."}
    result = _run_single(item, db)
    db.close()
    return result


if __name__ == "__main__":
    qa_pipeline()

# ============================================================
# Purpose:       Reclassify listening items to ensure task_type matches spec criteria (LCR/CONV/ANN/TALK) based on content analysis.
# Usage:         python agents/scripts/reclassify_listening_items.py [--apply]
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Reclassify Listening Items — deterministic spec-compliance checker.

For each of the 204 listening items, validates that the assigned task_type
matches the official TOEFL 2026 spec criteria (RR-25-12):

  LCR  : ≤2 dialogue lines, exactly 1 question, "response" question type
  CONV : multi-turn text with speaker labels, ≥3 questions, everyday topics
  ANN  : monologic text 60–160 words OR audio-only with campus context, 2–3 questions
  TALK : monologic text ≥150 words OR audio-only with academic subject context, ≥2 questions

Items that don't match their label are reclassified.
Items that can't be classified (audio-only, no transcript) are left as-is
if their title/context already fits.

Usage:
    cd toefl-2026
    source backend/venv/bin/activate
    python agents/scripts/reclassify_listening_items.py          # dry-run
    python agents/scripts/reclassify_listening_items.py --apply  # commit changes
"""
import os, sys, json, re, argparse

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal, engine, Base
from app.models.models import TestItem, SectionType, TaskType

Base.metadata.create_all(bind=engine)

# ─── Spec-based classification rules ────────────────────────────────────────

# Keywords that signal academic talk context (for audio-only items)
ACADEMIC_CONTEXTS = {
    'science', 'biology', 'history', 'physics', 'chemistry', 'economics',
    'psychology', 'sociology', 'art', 'music', 'literature', 'philosophy',
    'environmental', 'seminar', 'lecture', 'class', 'orientation',
}

# Keywords that signal announcement context (for audio-only items)
ANNOUNCEMENT_CONTEXTS = {
    'campus', 'office', 'library', 'security', 'administration', 'dining',
    'parking', 'registration', 'shuttle', 'health', 'department', 'services',
    'government', 'activities', 'affairs', 'center', 'event',
}


def has_speaker_labels(text: str) -> bool:
    """Detect dialogue turn markers in text."""
    if not text:
        return False
    patterns = [
        r'^\s*\(?[FM]\)?[:\s]',       # (F): or M: or F 
        r'^\s*\*\*\w+.*?\*\*:?\s',     # **Student**: or **Admin**:
        r'^\s*Speaker\s*\d',            # Speaker 1
    ]
    for p in patterns:
        if re.search(p, text, re.MULTILINE):
            return True
    return False


def classify_item(content: dict, current_type: str, title: str) -> str:
    """
    Classify a listening item based on its content structure.
    Returns the TaskType enum value string.
    """
    text = content.get('text', '')
    dialogue = content.get('dialogue', [])
    questions = content.get('questions', [])
    context = content.get('context', '')
    wc = len(text.split()) if text else 0
    q_count = len(questions)

    is_response_q = any(
        'appropriate response' in q.get('question', '').lower()
        or 'best response' in q.get('question', '').lower()
        for q in questions
    )

    # ─── Rule 1: LCR — short dialogue + 1 response-selection question ───
    if len(dialogue) <= 2 and q_count == 1 and is_response_q:
        return TaskType.LISTEN_CHOOSE_RESPONSE.value

    # ─── Rule 2: Conversation — multi-turn text with speaker labels ───
    if wc > 50 and has_speaker_labels(text) and q_count >= 3:
        return TaskType.LISTEN_CONVERSATION.value

    # ─── Rule 3: Items with meaningful monologic text ───
    if wc > 50 and not has_speaker_labels(text):
        # Academic Talk: ≥150 words, academic subject context
        ctx_lower = (context + ' ' + title).lower()
        is_academic = any(kw in ctx_lower for kw in ACADEMIC_CONTEXTS)
        is_campus = any(kw in ctx_lower for kw in ANNOUNCEMENT_CONTEXTS)

        if wc >= 150 and is_academic and not is_campus:
            return TaskType.LISTEN_ACADEMIC_TALK.value
        elif wc >= 150 and is_campus:
            # Long campus announcement — stays as announcement
            return TaskType.LISTEN_ANNOUNCEMENT.value
        elif is_campus:
            return TaskType.LISTEN_ANNOUNCEMENT.value
        elif is_academic:
            return TaskType.LISTEN_ACADEMIC_TALK.value
        else:
            # Default: shorter monologic = announcement, longer = talk
            return TaskType.LISTEN_ANNOUNCEMENT.value if wc < 150 else TaskType.LISTEN_ACADEMIC_TALK.value

    # ─── Rule 4: Audio-only items (no transcript, wc ≤ 10) ───
    if wc <= 10:
        ctx_lower = (context + ' ' + title).lower()
        is_academic = any(kw in ctx_lower for kw in ACADEMIC_CONTEXTS)
        is_campus = any(kw in ctx_lower for kw in ANNOUNCEMENT_CONTEXTS)

        if is_academic and not is_campus:
            return TaskType.LISTEN_ACADEMIC_TALK.value
        elif is_campus:
            return TaskType.LISTEN_ANNOUNCEMENT.value
        else:
            # Can't determine — keep current
            return current_type

    # ─── Rule 5: PENDING_TTS items with no text yet ───
    if wc == 0 and q_count >= 3:
        ctx_lower = (context + ' ' + title).lower()
        is_academic = any(kw in ctx_lower for kw in ACADEMIC_CONTEXTS)
        if is_academic:
            return TaskType.LISTEN_ACADEMIC_TALK.value
        return TaskType.LISTEN_ANNOUNCEMENT.value

    # Fallback: keep current type
    return current_type


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Commit reclassifications to DB')
    args = parser.parse_args()

    db = SessionLocal()
    items = db.query(TestItem).filter(TestItem.section == SectionType.LISTENING).all()
    print(f"Auditing {len(items)} listening items...\n")

    changes = []
    confirmed = 0
    skipped = 0

    for item in items:
        content = json.loads(item.prompt_content)
        title = content.get('title', '')
        current = item.task_type.value
        inferred = classify_item(content, current, title)

        if inferred != current:
            changes.append({
                'id': item.id,
                'title': title[:50],
                'level': item.target_level.name,
                'from': current,
                'to': inferred,
            })
        else:
            confirmed += 1

    # Report
    print(f"  ✓ Confirmed correct: {confirmed}")
    print(f"  ⚡ Needs reclassification: {len(changes)}")
    print()

    if changes:
        # Group by transition
        from collections import Counter
        transitions = Counter((c['from'], c['to']) for c in changes)
        for (fr, to), count in transitions.most_common():
            label_from = fr.replace('_', ' ').title()
            label_to = to.replace('_', ' ').title()
            print(f"  {label_from}  →  {label_to}:  {count} items")

        print()
        for c in changes:
            print(f"  {c['id'][:8]}  [{c['level']}]  {c['from']} → {c['to']}  \"{c['title']}\"")

        if args.apply:
            print(f"\n  Applying {len(changes)} reclassifications...")
            for c in changes:
                item = db.query(TestItem).filter(TestItem.id == c['id']).first()
                if item:
                    old_notes = item.generation_notes or ''
                    item.task_type = TaskType(c['to'])
                    item.generation_notes = f"Reclassified {c['from']}→{c['to']}. {old_notes}"
            db.commit()
            print("  ✓ Done!")
        else:
            print(f"\n  [DRY RUN] Pass --apply to commit changes.")
    else:
        print("  All items are correctly classified. No changes needed.")

    db.close()


if __name__ == '__main__':
    run()

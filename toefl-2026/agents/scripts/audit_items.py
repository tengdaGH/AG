# ============================================================
# Purpose:       Quick structural and quality audit of all reading + listening MCQ items. Checks data structure, audio availability, and option quality.
# Usage:         python agents/scripts/audit_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import sys, os, json, re
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))
from app.database.connection import SessionLocal
from app.models.models import TestItem, SectionType, TaskType

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

ABSOLUTE_WORDS = {"always", "never", "only", "none", "all", "every", "no one", "must"}


def check_audio(url):
    if not url or url == 'PENDING_TTS':
        return False
    return (os.path.exists(os.path.join(PROJECT, 'frontend/public', url)) or
            os.path.exists(os.path.join(PROJECT, url)))


def wc(text):
    return len(text.split()) if text else 0


def check_option_quality(questions, task_type_val):
    """
    Run option-length-parity and key-dominance checks across all questions.
    Returns list of problem strings.
    """
    probs = []
    for qi, q in enumerate(questions):
        options  = q.get('options', [])
        correct  = q.get('correct_answer', q.get('answer'))
        qnum     = qi + 1

        if not options or not isinstance(correct, int) or correct >= len(options):
            continue  # Structural issues caught elsewhere

        wcs = [wc(o) for o in options]
        max_wc = max(wcs) if wcs else 0
        min_wc = min(wcs) if wcs else 0

        # 1. Option length parity
        if min_wc > 0 and max_wc > min_wc * 2.5:
            probs.append(f"Q{qnum}_PARITY({min_wc}–{max_wc}w)")

        # 2. Key length dominance
        key_wc = wcs[correct]
        dist_wcs = [w for i, w in enumerate(wcs) if i != correct]
        mean_dist = sum(dist_wcs) / max(len(dist_wcs), 1)
        if mean_dist > 0 and key_wc > mean_dist * 1.5:
            probs.append(f"Q{qnum}_KEY_LONG({key_wc}w vs {mean_dist:.0f}w mean)")

        # 3. All/None of the above
        for oi, opt in enumerate(options):
            if re.search(r'\b(all|none)\s+of\s+the\s+above\b', opt.lower()):
                probs.append(f"Q{qnum}_OPT{chr(65+oi)}_ALL_NONE_ABOVE")

        # 4. Absolute words in key
        key_text = options[correct]
        for aw in ABSOLUTE_WORDS:
            if re.search(rf'\b{aw}\b', key_text.lower()):
                probs.append(f"Q{qnum}_KEY_ABSOLUTE({aw})")
                break

        # 5. Duplicate options
        cleaned = [o.lower().strip() for o in options]
        if len(cleaned) != len(set(cleaned)):
            probs.append(f"Q{qnum}_DUP_OPTS")

        # 6. Option count (LISTEN_CHOOSE_RESPONSE may have different norms)
        expected_count = 4
        if len(options) != expected_count:
            probs.append(f"Q{qnum}_OPT_COUNT({len(options)}≠4)")

    return probs


db = SessionLocal()

# ─── LISTENING ───────────────────────────────────────────────────────────────
listening = db.query(TestItem).filter(TestItem.section == SectionType.LISTENING).all()
l_issues = []

for item in listening:
    c  = json.loads(item.prompt_content)
    tt = item.task_type
    probs = []

    text     = c.get('text', '')
    dialogue = c.get('dialogue', [])
    twc      = wc(text)

    # Structural checks
    if tt == TaskType.LISTEN_CHOOSE_RESPONSE:
        if not dialogue:
            probs.append("NO_DIALOGUE")
    elif twc < 20:
        probs.append(f"TEXT_SHORT({twc}w)")

    qs = c.get('questions', [])
    if not qs:
        probs.append("NO_QUESTIONS")
    else:
        for qi, q in enumerate(qs):
            if not q.get('text', q.get('question', '')):
                probs.append(f"Q{qi+1}_NO_TEXT")
            if len(q.get('options', [])) < 2:
                probs.append(f"Q{qi+1}_FEW_OPTS")
            if q.get('correct_answer', q.get('answer')) is None:
                probs.append(f"Q{qi+1}_NO_ANS")

        # Option quality checks (apply to MCQ types with ≥2 options)
        if tt in (TaskType.LISTEN_CONVERSATION, TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_ACADEMIC_TALK):
            quality_probs = check_option_quality(qs, tt.value if tt else '')
            probs.extend(quality_probs)
        elif tt == TaskType.LISTEN_CHOOSE_RESPONSE:
            # Lighter parity check for single-sentence response options
            for qi, q in enumerate(qs):
                opts = q.get('options', [])
                if len(opts) >= 2:
                    wcs = [wc(o) for o in opts]
                    max_wc_v, min_wc_v = max(wcs), min(wcs)
                    if min_wc_v > 0 and max_wc_v > min_wc_v * 2.0:
                        probs.append(f"Q{qi+1}_PARITY({min_wc_v}–{max_wc_v}w)")

    if not check_audio(c.get('audio_url', '')):
        probs.append("NO_AUDIO")
    if not c.get('title'):
        probs.append("NO_TITLE")

    if probs:
        l_issues.append((item.id[:8], item.target_level.name if item.target_level else '?',
                         tt.value[:22] if tt else 'None', c.get('title', '?')[:35], probs))

print("=" * 80)
print("  LISTENING AUDIT")
print("=" * 80)
print(f"  Total: {len(listening)} | Clean: {len(listening)-len(l_issues)} | Issues: {len(l_issues)}")
tc = Counter(i.task_type.value for i in listening)
for t, cnt in tc.most_common():
    print(f"    {t}: {cnt}")
if l_issues:
    print()
    for uid, lvl, tt, title, probs in l_issues:
        print(f"  {uid} [{lvl}] {tt:25s} | {', '.join(probs)} | \"{title}\"")
else:
    print("\n  ✅ ALL LISTENING ITEMS CLEAN!")

# ─── READING ──────────────────────────────────────────────────────────────────
reading = db.query(TestItem).filter(TestItem.section == SectionType.READING).all()
r_issues = []

for item in reading:
    c  = json.loads(item.prompt_content)
    tt = item.task_type
    probs = []

    text    = c.get('text', '') or c.get('passage', '') or c.get('content', '')
    is_disc = bool(c.get('professor_prompt') or c.get('professorQuestion'))
    is_daily = (tt == TaskType.READ_IN_DAILY_LIFE) if tt else False
    twc = wc(text)

    # Passage length checks
    if is_disc:
        prof = c.get('professor_prompt', c.get('professorQuestion', ''))
        if not prof or len(prof.split()) < 5:
            probs.append("NO_PROF_PROMPT")
    elif is_daily:
        if twc < 3 and not c.get('situation'):
            probs.append(f"TEXT_SHORT({twc}w)")
    else:
        if twc < 50:
            probs.append(f"PASSAGE_SHORT({twc}w)")

    qs = c.get('questions', [])
    if not qs and not is_disc and not c.get('task') and not c.get('prompt'):
        probs.append("NO_QUESTIONS")
    if not c.get('title'):
        probs.append("NO_TITLE")

    # Option quality checks for MCQ reading types
    if qs and tt in (TaskType.READ_IN_DAILY_LIFE, TaskType.READ_ACADEMIC_PASSAGE):
        quality_probs = check_option_quality(qs, tt.value if tt else '')
        probs.extend(quality_probs)

    if probs:
        tname = tt.value[:25] if tt else c.get('type', 'None')[:25]
        r_issues.append((item.id[:8], item.target_level.name if item.target_level else '?',
                         tname, c.get('title', '?')[:35], probs))

print()
print("=" * 80)
print("  READING AUDIT")
print("=" * 80)
print(f"  Total: {len(reading)} | Clean: {len(reading)-len(r_issues)} | Issues: {len(r_issues)}")
tc = Counter((i.task_type.value if i.task_type else json.loads(i.prompt_content).get('type', 'None')) for i in reading)
for t, cnt in tc.most_common():
    print(f"    {t}: {cnt}")
if r_issues:
    print()
    for uid, lvl, tt, title, probs in r_issues:
        print(f"  {uid} [{lvl}] {tt:25s} | {', '.join(probs)} | \"{title}\"")
else:
    print("\n  ✅ ALL READING ITEMS CLEAN!")

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
total  = len(listening) + len(reading)
issues = len(l_issues) + len(r_issues)
print()
print("=" * 80)
print(f"  GRAND TOTAL: {total} items | Clean: {total-issues} | Issues: {issues}")
if issues:
    quality_flags = sum(
        sum(1 for p in probs if any(flag in p for flag in ('PARITY', 'KEY_LONG', 'KEY_ABSOLUTE', 'ALL_NONE')))
        for *_, probs in l_issues + r_issues
    )
    print(f"  MCQ QUALITY FLAGS: {quality_flags} (PARITY, KEY_LONG, KEY_ABSOLUTE, ALL_NONE)")
print("=" * 80)
db.close()

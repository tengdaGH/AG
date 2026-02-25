# ============================================================
# Purpose:       Full ETS-standards review of academic passage items: stem, key, distractor, passage, type coverage checks.
# Usage:         python backend/scripts/review_academic_items.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Full ETS-Standards Review of Academic Passage Items.

Standards source: TOEFL iBT Technical Manual RR-25-12 + .agent/knowledge/item-quality/mcq_item_quality.md

Checks each item against TOEFL 2026 ETS guidelines:
  STEM:
    1. Stem completeness (non-empty, meaningful question)
    2. Negative phrasing (NOT/EXCEPT must be ALL CAPS)
    3. Vague opener detection ("which of the following is true/false")

  KEY (correct answer):
    4. Uniqueness / valid correct_answer index
    5. KEY LENGTH DOMINANCE — key must not be >50% longer (in words) than mean distractor
    6. Verbatim lift from passage — key must not copy ≥6 consecutive passage words verbatim

  DISTRACTORS:
    7. No "all of the above" / "none of the above"
    8. No duplicate options (identical text)
    9. No option-leading-phrase overlap (first 5 words identical)
    10. Absolute words in distractors (always/never → easy elimination)

  OPTION SET:
    11. Exactly 4 options (A–D) per question
    12. OPTION LENGTH PARITY — longest option ≤ 2.5× the shortest option word count

  PASSAGE:
    13. ~200 words (150–250 range; warn at 180–150 and 200–250)

  QUESTION COUNT & TYPE COVERAGE:
    14. Exactly 5 questions per passage (ETS spec)
    15. All 5 required question types present (main_idea, factual, inference, vocabulary, rhetorical)

Quality Score: 0–100, used to prioritize remediation.
"""
import os, sys, json, sqlite3, re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

ETS_RULES_HEADER = """
ETS TOEFL 2026 Item Quality Standards for "Read an Academic Passage"
Source: RR-25-12 Technical Manual + .agent/knowledge/item-quality/mcq_item_quality.md
"""

ABSOLUTE_WORDS = {"always", "never", "only", "none", "all", "every", "no one", "must", "impossible"}
VAGUE_OPENERS  = ["which of the following is true", "which of the following is false",
                   "which of the following is correct", "which of the following is not correct"]

# Quality score penalties
PENALTY = {
    "key_dominance":        25,   # Key >50% longer in words than mean distractor
    "option_parity":        20,   # Longest option > 2.5× shortest
    "fail_per_violation":   20,   # Structural FAIL (no answer, dupe, <4 options, all/none-above)
    "verbatim_lift":        10,   # Key copies ≥6 consecutive passage words
    "absolute_in_key":       5,   # Absolute word in key
    "absolute_per_distractor": 3, # Per distractor with absolute word
    "missing_q_type":        5,   # Per missing required question type
    "negative_no_caps":      5,   # NOT/EXCEPT not in ALL CAPS in stem
    "vague_opener":          5,   # Stem is a vague "which is true/false" opener
}


# ──────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def detect_verbatim_lift(key_text: str, passage: str, min_words: int = 6) -> str | None:
    """Return the first verbatim phrase found in both key and passage (>= min_words consecutive)."""
    key_words = key_text.lower().split()
    passage_lower = passage.lower()
    for start in range(len(key_words) - min_words + 1):
        phrase = " ".join(key_words[start:start + min_words])
        if phrase in passage_lower:
            return phrase
    return None


def classify_question_type(stem: str) -> str:
    s = stem.lower()
    if any(p in s for p in ["mainly about", "main purpose", "main idea", "primarily about"]):
        return "main_idea"
    if "according to" in s or "states that" in s or "mentions that" in s:
        return "factual"
    if any(p in s for p in ["infer", "suggest", "imply", "conclude", "can be understood"]):
        return "inference"
    if ("word" in s or "phrase" in s) and any(p in s for p in ["meaning", "closest", "refers to"]):
        return "vocabulary"
    if any(p in s for p in ["in order to", "author mentions", "author uses", "author discusses",
                              "why does the author", "purpose of"]):
        return "rhetorical"
    return "other"


def check_stem(stem: str) -> tuple[list, list]:
    """Returns (issues, notes) for a single stem."""
    issues, notes = [], []
    s_lower = stem.lower()

    # Vague opener
    if any(s_lower.startswith(op) for op in VAGUE_OPENERS):
        notes.append(f"VAGUE_OPENER: Rewrite as specific question")

    # Negative phrasing check
    for neg in ["not", "except"]:
        if re.search(rf'\b{neg}\b', s_lower):
            if not re.search(rf'\b{neg.upper()}\b', stem):
                notes.append(f"NEG_NO_CAPS: '{neg}' in stem should be ALL CAPS (ETS standard)")
            break

    return issues, notes


def check_option_set(options: list, correct: int, passage: str) -> tuple[list, list, float]:
    """
    Check a single question's option set.
    Returns (issues, notes, quality_penalty).
    """
    issues, notes = [], []
    penalty = 0.0

    # 1. Option count
    if len(options) != 4:
        issues.append(f"OPTION_COUNT: Has {len(options)} options (need exactly 4)")
        penalty += PENALTY["fail_per_violation"]

    if not options or not isinstance(correct, int) or correct < 0 or correct >= len(options):
        issues.append(f"INVALID_KEY: correct_answer={correct} is not a valid index")
        penalty += PENALTY["fail_per_violation"]
        return issues, notes, penalty

    key_text = options[correct]
    distractors = [opt for i, opt in enumerate(options) if i != correct]

    # 2. All/None of the above
    for oi, opt in enumerate(options):
        if re.search(r'\b(all|none)\s+of\s+the\s+above\b', opt.lower()):
            issues.append(f"OPT_{chr(65+oi)}: Contains 'all/none of the above' (ETS violation)")
            penalty += PENALTY["fail_per_violation"]

    # 3. Duplicate options
    clean_opts = [o.lower().strip() for o in options]
    if len(clean_opts) != len(set(clean_opts)):
        issues.append("DUPLICATE_OPTS: Two or more identical options detected")
        penalty += PENALTY["fail_per_violation"]

    # 4. Leading-phrase overlap (first 5 words)
    leading = [" ".join(o.lower().split()[:5]) for o in options]
    seen_leading = set()
    for oi, lead in enumerate(leading):
        if lead in seen_leading and len(lead.split()) >= 4:
            issues.append(f"OPT_{chr(65+oi)}: First 5 words overlap with another option (ambiguous distractors)")
            penalty += PENALTY["fail_per_violation"]
        seen_leading.add(lead)

    # 5. Option length parity
    wcs = [word_count(o) for o in options]
    max_wc, min_wc = max(wcs), min(wcs)
    if min_wc > 0 and max_wc > min_wc * 2.5:
        issues.append(
            f"PARITY_FAIL: Longest option ({max_wc}w) > 2.5× shortest ({min_wc}w). "
            f"Outlier: \"{options[wcs.index(max_wc)][:50]}...\""
        )
        penalty += PENALTY["option_parity"]
    elif min_wc > 0 and max_wc > min_wc * 1.8:
        notes.append(
            f"PARITY_WARN: Longest option ({max_wc}w) is {max_wc/min_wc:.1f}× shortest ({min_wc}w) — verify balance"
        )

    # 6. Key length dominance
    key_wc = word_count(key_text)
    mean_dist_wc = sum(word_count(d) for d in distractors) / max(len(distractors), 1)
    if mean_dist_wc > 0 and key_wc > mean_dist_wc * 1.5:
        issues.append(
            f"KEY_DOMINANCE: Key ({key_wc}w) is {key_wc/mean_dist_wc:.1f}× mean distractor ({mean_dist_wc:.1f}w). "
            f"Key: \"{key_text[:60]}...\""
        )
        penalty += PENALTY["key_dominance"]
    elif mean_dist_wc > 0 and key_wc > mean_dist_wc * 1.25:
        notes.append(
            f"KEY_LONG: Key ({key_wc}w) is notably longer than mean distractor ({mean_dist_wc:.1f}w) — consider trimming"
        )

    # 7. Verbatim lift in key
    if passage:
        lift = detect_verbatim_lift(key_text, passage)
        if lift:
            notes.append(f"VERBATIM_LIFT: Key copies passage verbatim: \"...{lift}...\" — paraphrase required")
            penalty += PENALTY["verbatim_lift"]

    # 8. Absolute words in key
    for aw in ABSOLUTE_WORDS:
        if re.search(rf'\b{aw}\b', key_text.lower()):
            notes.append(f"ABSOLUTE_IN_KEY: Key contains absolute word '{aw}' — replace with hedged form")
            penalty += PENALTY["absolute_in_key"]
            break

    # 9. Absolute words in distractors
    for di, dist in enumerate(distractors):
        for aw in ABSOLUTE_WORDS:
            if re.search(rf'\b{aw}\b', dist.lower()):
                notes.append(f"ABSOLUTE_IN_D{di+1}: Distractor contains '{aw}' — easy elimination cue")
                penalty += PENALTY["absolute_per_distractor"]
                break

    return issues, notes, penalty


# ──────────────────────────────────────────────────────────────────────────────
# MAIN REVIEW
# ──────────────────────────────────────────────────────────────────────────────

def run_review():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'toefl_2026.db'))
    cur = conn.cursor()
    cur.execute("""
        SELECT id, target_level, generated_by_model, prompt_content
        FROM test_items WHERE task_type='READ_ACADEMIC_PASSAGE'
        ORDER BY target_level
    """)
    rows = cur.fetchall()

    report = []
    report.append("# ETS Standards Review — Read an Academic Passage\n")
    report.append(f"**Total items:** {len(rows)}\n")
    report.append("> Checks: ETS Technical Manual RR-25-12 + mcq_item_quality.md standards\n")

    summary_issues = []
    grand_pass = grand_notes = grand_fail = 0

    for item_id, level, model, pc in rows:
        data = json.loads(pc)
        title = data.get("title", "Untitled")
        passage = data.get("text", "")
        questions = data.get("questions", [])
        wc = word_count(passage)

        item_issues: list[str] = []
        item_notes: list[str] = []
        total_penalty = 0.0

        # ── Passage checks ──────────────────────────────────────────────────
        if wc < 150:
            item_issues.append(f"PASSAGE_SHORT: {wc}w — minimum 150 (target ~200)")
            total_penalty += PENALTY["fail_per_violation"]
        elif wc < 180:
            item_notes.append(f"PASSAGE_SLIGHTLY_SHORT: {wc}w — target ~200")
        elif wc > 250:
            item_issues.append(f"PASSAGE_LONG: {wc}w — maximum 250 (target ~200)")
            total_penalty += PENALTY["fail_per_violation"]

        # ── Question count ───────────────────────────────────────────────────
        if len(questions) < 5:
            item_issues.append(f"Q_COUNT_LOW: Only {len(questions)} questions (ETS spec: 5)")
            total_penalty += PENALTY["fail_per_violation"]
        elif len(questions) > 5:
            item_notes.append(f"Q_COUNT_HIGH: {len(questions)} questions (spec says exactly 5)")

        # ── Per-question checks ──────────────────────────────────────────────
        q_types_found: set[str] = set()

        for qi, q in enumerate(questions):
            stem    = q.get("text", q.get("question", ""))
            options = q.get("options", [])
            correct = q.get("correct_answer", q.get("answer"))
            qnum    = qi + 1

            # Stem checks
            s_issues, s_notes = check_stem(stem)
            for s in s_issues:
                item_issues.append(f"Q{qnum} {s}")
                total_penalty += PENALTY["fail_per_violation"]
            for n in s_notes:
                item_notes.append(f"Q{qnum} {n}")
                key_note = next((k for k in PENALTY if k in n.split(":")[0].lower()), None)
                if key_note:
                    total_penalty += PENALTY[key_note]
                else:
                    # Notes from stem check use fixed small penalties
                    if "NEG_NO_CAPS" in n:
                        total_penalty += PENALTY["negative_no_caps"]
                    elif "VAGUE_OPENER" in n:
                        total_penalty += PENALTY["vague_opener"]

            # Classify question type
            q_types_found.add(classify_question_type(stem))

            # Option set checks
            if not isinstance(correct, int):
                try:
                    correct = int(correct)
                except (TypeError, ValueError):
                    item_issues.append(f"Q{qnum} INVALID_KEY: correct_answer is not an integer: {correct!r}")
                    total_penalty += PENALTY["fail_per_violation"]
                    continue

            o_issues, o_notes, o_penalty = check_option_set(options, correct, passage)
            for s in o_issues:
                item_issues.append(f"Q{qnum} {s}")
            for n in o_notes:
                item_notes.append(f"Q{qnum} {n}")
            total_penalty += o_penalty

        # ── Question type coverage ───────────────────────────────────────────
        required_types = {"main_idea", "factual", "rhetorical", "inference", "vocabulary"}
        missing_types  = required_types - q_types_found
        type_names     = {
            "main_idea":  "Main Idea/Purpose",
            "factual":    "Factual Detail",
            "inference":  "Inference",
            "vocabulary": "Vocabulary in Context",
            "rhetorical": "Rhetorical Purpose",
        }
        for t in missing_types:
            item_notes.append(f"MISSING_Q_TYPE: No '{type_names[t]}' question — add one (ETS spec: all 5 types)")
            total_penalty += PENALTY["missing_q_type"]

        # ── Quality score ────────────────────────────────────────────────────
        quality_score = max(0, round(100 - total_penalty))
        if quality_score >= 85:
            score_label = "✅ PASS"
            grand_pass += 1
        elif quality_score >= 70:
            score_label = "⚠️ NOTES"
            grand_notes += 1
        else:
            score_label = "❌ FAIL"
            grand_fail += 1

        # ── Build report entry ───────────────────────────────────────────────
        report.append(f"\n---\n### {score_label} | {title}")
        report.append(
            f"**Level:** {level} | **Words:** {wc} | **Questions:** {len(questions)} "
            f"| **Quality Score:** {quality_score}/100 | **Model:** {model}\n"
        )

        if item_issues:
            report.append("**❌ Issues (must fix):**")
            for iss in item_issues:
                report.append(f"- {iss}")
            summary_issues.append((title, item_issues))
            report.append("")

        if item_notes:
            report.append("**⚠️ Notes (recommended):**")
            for note in item_notes:
                report.append(f"- {note}")
            report.append("")

        # Questions summary
        report.append("**Question Breakdown:**")
        for qi, q in enumerate(questions):
            stem    = q.get("text", q.get("question", ""))[:90]
            opts    = q.get("options", [])
            correct = q.get("correct_answer", q.get("answer", -1))
            qtype   = classify_question_type(stem)
            report.append(f"- Q{qi+1} [{qtype}]: {stem}")
            for oi, o in enumerate(opts):
                wc_o   = word_count(o)
                marker = " ✓" if oi == correct else ""
                report.append(f"  - {chr(65+oi)}) [{wc_o}w] {o[:75]}{marker}")

    # ── Final summary ────────────────────────────────────────────────────────
    total = len(rows)
    report.append(f"\n---\n## Summary")
    report.append(f"| Status | Count | % |")
    report.append(f"|--------|-------|---|")
    report.append(f"| ✅ PASS (≥85) | {grand_pass} | {grand_pass/max(total,1)*100:.0f}% |")
    report.append(f"| ⚠️ NOTES (70–84) | {grand_notes} | {grand_notes/max(total,1)*100:.0f}% |")
    report.append(f"| ❌ FAIL (<70) | {grand_fail} | {grand_fail/max(total,1)*100:.0f}% |")
    report.append(f"| **Total** | **{total}** | |")

    if summary_issues:
        report.append("\n### Items Needing Immediate Attention:")
        for title, issues in summary_issues:
            report.append(f"\n**{title}:**")
            for iss in issues:
                report.append(f"- {iss}")

    conn.close()
    return "\n".join(report)


if __name__ == "__main__":
    result = run_review()

    # Save to brain artifacts dir so it's accessible in the UI
    output_path = os.path.join(
        os.path.dirname(__file__), '..', '..', '.gemini', 'antigravity', 'brain',
        '3b3fa660-2a0a-426c-9b9c-c4bc3e4b3241', 'ets_review_report.md'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(result)

    print(result)
    print(f"\nReport saved to: {output_path}")

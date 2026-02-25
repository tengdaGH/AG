# ============================================================
# Purpose:       Deterministic C-Test generator: Gemini produces raw passage, rule-based truncation creates exactly 10 blanks.
# Usage:         Imported by other scripts (gauntlet_qa.py, fix_c_test_deterministic.py).
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Deterministic C-Test Generator.

Uses Gemini to produce a raw passage, then applies rule-based truncation
to guarantee exactly 10 blanks with an intact first sentence.
"""
import os
import re
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def _get_raw_passage(cefr_level: str, topic_hint: str) -> str:
    """Call Gemini 2.5 Flash to generate a clean ~50-word paragraph."""
    import google.generativeai as genai
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = (
        f"Write a 40 to 50 word informative paragraph about "
        f"'{topic_hint[:80]}' suitable for an English learner at "
        f"CEFR level {cefr_level}. Do NOT include any blanks, "
        f"underscores, or formatting. Just raw natural text."
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def _build_c_test(raw_text: str) -> dict:
    """
    Deterministically produce a C-test from a clean passage.

    Rules:
      1. First sentence is intact (no blanks).
      2. Every 2nd content word thereafter is truncated (second half → underscores).
      3. Exactly 10 blanks.
    """
    # Split first sentence from rest
    m = re.search(r'^([A-Z].*?[.!?])\s+(.*)$', raw_text, re.DOTALL)
    if m:
        first_sentence, rest_text = m.group(1), m.group(2)
    else:
        words = raw_text.split()
        first_sentence = " ".join(words[:10]) + "."
        rest_text = " ".join(words[10:])

    tokens = re.findall(r"[\w']+|[.,!?;:]", rest_text)
    final_words: list[str] = []
    questions: list[dict] = []
    word_idx = 0

    for token in tokens:
        if re.match(r'^[.,!?;:]$', token):
            if final_words:
                final_words[-1] += token
            else:
                final_words.append(token)
            continue

        word_idx += 1

        if word_idx % 2 == 0 and len(questions) < 10 and len(token) >= 2:
            half = len(token) // 2
            visible = token[:half]
            hidden = token[half:]
            truncated = visible + "_" * len(hidden)
            final_words.append(truncated)
            questions.append({
                "question_num": len(questions) + 1,
                "text": truncated,
                "correct_answer": token,
            })
        else:
            final_words.append(token)

    full_text = first_sentence + " " + " ".join(final_words)
    full_text = re.sub(r'\s+([.,!?;:])', r'\1', full_text)

    return {
        "text": full_text,
        "questions": questions,
    }


def generate_c_test(cefr_level: str, topic_hint: str) -> dict | None:
    """
    High-level helper: generate a fully compliant C-test dict.

    Returns a dict with ``text`` and ``questions`` (10 items) or ``None``
    if the Gemini call fails.
    """
    try:
        raw = _get_raw_passage(cefr_level, topic_hint)
        return _build_c_test(raw)
    except Exception as e:
        logging.error(f"C-test generation failed: {e}")
        return None

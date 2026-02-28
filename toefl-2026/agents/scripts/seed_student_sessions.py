#!/usr/bin/env python3
# ============================================================
# Purpose:    Generates realistic synthetic student sessions for testing
#             the scoring pipeline, Teacher Dashboard, and Alfred's student
#             data checks. All synthetic accounts are prefixed with SYN_.
#             Inserts into user_data.db only — never touches item_bank.db.
# Usage:      python3 agents/scripts/seed_student_sessions.py [--count N]
#             [--profile {weak|average|good|strong|mixed}] [--purge-synthetic]
# Created:    2026-02-28
# Self-Destruct: No
# ============================================================

import os
import sys
import sqlite3
import datetime
import random
import json
import argparse
import hashlib

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ITEM_BANK_DB = os.path.join(PROJECT_ROOT, "backend", "item_bank.db")
USER_DATA_DB = os.path.join(PROJECT_ROOT, "backend", "user_data.db")

# ── Student Profiles ─────────────────────────────────────────────────────────
# Each profile defines accuracy rates (0.0–1.0) per section and expected band scores.
# Gaussian noise (σ=0.08) is added per item to simulate natural variation.
PROFILES = {
    "weak":     {"cefr": "A2", "reading": 0.38, "listening": 0.33, "writing_band": 1.5, "speaking_band": 1.5},
    "average":  {"cefr": "B1", "reading": 0.58, "listening": 0.54, "writing_band": 3.0, "speaking_band": 3.0},
    "good":     {"cefr": "B2", "reading": 0.74, "listening": 0.70, "writing_band": 4.0, "speaking_band": 4.0},
    "strong":   {"cefr": "C1", "reading": 0.87, "listening": 0.84, "writing_band": 5.0, "speaking_band": 5.0},
    "native":   {"cefr": "C2", "reading": 0.95, "listening": 0.93, "writing_band": 5.5, "speaking_band": 5.5},
}


def make_password_hash(password="synthetic_test"):
    """Create a simple SHA256 hash for synthetic accounts."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_db(path):
    if not os.path.exists(path):
        print(f"❌ Database not found: {path}")
        sys.exit(1)
    return sqlite3.connect(path)


def get_items_by_type(item_conn, task_type, limit=20):
    """Fetch ACTIVE items of a specific task_type from item_bank.db."""
    rows = item_conn.execute("""
        SELECT id, task_type, correct_answer, irt_difficulty
        FROM test_items
        WHERE lifecycle_status='ACTIVE' AND task_type=?
        ORDER BY RANDOM()
        LIMIT ?
    """, (task_type, limit)).fetchall()
    return rows


def simulate_response(correct_answer, accuracy_rate):
    """
    Simulate a student response. Returns the student's answer and whether it was correct.
    For MCQ (A/B/C/D), picks the correct answer with p=accuracy_rate, else a random wrong one.
    For non-MCQ (Build-a-Sentence etc.), returns '1'/'0' for correct/incorrect.
    """
    choices = ["A", "B", "C", "D"]
    noisy_accuracy = max(0.05, min(0.98, accuracy_rate + random.gauss(0, 0.08)))
    is_correct = random.random() < noisy_accuracy

    if correct_answer in choices:
        if is_correct:
            return correct_answer, True
        else:
            wrong = [c for c in choices if c != correct_answer]
            return random.choice(wrong), False
    else:
        # Non-MCQ: return correct_answer (correct) or empty string (wrong)
        return (correct_answer or "correct", True) if is_correct else ("", False)


def create_synthetic_student(user_conn, username, cefr):
    """Insert a synthetic student. Idempotent — skips if already exists."""
    existing = user_conn.execute(
        "SELECT id FROM students WHERE username=?", (username,)
    ).fetchone()
    if existing:
        return existing[0]

    user_conn.execute("""
        INSERT INTO students (username, password_hash, cefr_level, created_at, notes)
        VALUES (?, ?, ?, ?, 'SYNTHETIC')
    """, (username, make_password_hash(), cefr, datetime.datetime.utcnow().isoformat()))
    user_conn.commit()

    student_id = user_conn.execute(
        "SELECT id FROM students WHERE username=?", (username,)
    ).fetchone()[0]
    return student_id


def seed_session(user_conn, item_conn, student_id, profile_name, session_num):
    """Create one complete synthetic session with responses."""
    profile = PROFILES[profile_name]
    now     = datetime.datetime.utcnow()
    # Simulate session that happened between 1 and 30 days ago
    start_time = now - datetime.timedelta(days=random.randint(1, 30),
                                          hours=random.randint(0, 23))
    # Sessions take 90–120 minutes
    end_time = start_time + datetime.timedelta(minutes=random.randint(90, 120))

    # Insert session
    user_conn.execute("""
        INSERT INTO sessions (student_id, status, created_at, completed_at, notes)
        VALUES (?, 'completed', ?, ?, 'SYNTHETIC')
    """, (student_id, start_time.isoformat(), end_time.isoformat()))
    user_conn.commit()

    session_id = user_conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    responses_inserted = 0
    score_total = 0.0

    # ── Reading items (35 scored Qs across C_TEST + DAILY_LIFE + ACADEMIC_PASSAGE)
    reading_types = [("C_TEST", 10), ("DAILY_LIFE", 5), ("ACADEMIC_PASSAGE", 5)]
    for task_type, count in reading_types:
        items = get_items_by_type(item_conn, task_type, limit=count * 2)
        used  = random.sample(items, min(count, len(items)))
        for item in used:
            item_id, _, correct, _ = item
            student_ans, is_correct = simulate_response(correct, profile["reading"])
            score = 1 if is_correct else 0
            score_total += score
            user_conn.execute("""
                INSERT INTO responses
                    (session_id, item_id, student_answer, is_correct, score, responded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, item_id, student_ans, int(is_correct), score,
                  start_time.isoformat()))
            responses_inserted += 1

    # ── Listening items (35 scored Qs)
    listening_types = [
        ("LISTEN_CHOOSE_RESPONSE", 8),
        ("LISTEN_CONVERSATION", 4),
        ("LISTEN_ANNOUNCEMENT", 4),
        ("LISTEN_ACADEMIC_TALK", 4),
    ]
    for task_type, count in listening_types:
        items = get_items_by_type(item_conn, task_type, limit=count * 2)
        used  = random.sample(items, min(count, len(items)))
        for item in used:
            item_id, _, correct, _ = item
            student_ans, is_correct = simulate_response(correct, profile["listening"])
            score = 1 if is_correct else 0
            score_total += score
            user_conn.execute("""
                INSERT INTO responses
                    (session_id, item_id, student_answer, is_correct, score, responded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, item_id, student_ans, int(is_correct), score,
                  start_time.isoformat()))
            responses_inserted += 1

    # ── Writing (Build-a-Sentence x10, Email x1, Academic Discussion x1)
    writing_types = [("BUILD_SENTENCE", 10), ("WRITE_EMAIL", 1), ("WRITE_ACADEMIC_DISCUSSION", 1)]
    writing_score = 0.0
    for task_type, count in writing_types:
        items = get_items_by_type(item_conn, task_type, limit=count * 2)
        used  = random.sample(items, min(count, len(items)))
        for item in used:
            item_id, _, correct, _ = item
            if task_type == "BUILD_SENTENCE":
                student_ans, is_correct = simulate_response(correct, profile["reading"])
                score = 1.0 if is_correct else 0.0
            else:
                # AI-scored: simulate band score around profile expectation
                score = max(0, min(5, round(profile["writing_band"] + random.gauss(0, 0.5))))
                student_ans = f"[Synthetic essay — band {score}]"
                is_correct = score >= 3
            writing_score += score
            user_conn.execute("""
                INSERT INTO responses
                    (session_id, item_id, student_answer, is_correct, score, responded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, item_id, student_ans, int(is_correct), score,
                  start_time.isoformat()))
            responses_inserted += 1

    # ── Speaking (Listen and Repeat x7, Interview x4)
    speaking_types = [("LISTEN_REPEAT", 7), ("SPEAKING_INTERVIEW", 4)]
    speaking_score = 0.0
    for task_type, count in speaking_types:
        items = get_items_by_type(item_conn, task_type, limit=count * 2)
        used  = random.sample(items, min(count, len(items)))
        for item in used:
            item_id, _, correct, _ = item
            score = max(0, min(5, round(profile["speaking_band"] + random.gauss(0, 0.5))))
            student_ans = f"[Synthetic transcript — band {score}]"
            user_conn.execute("""
                INSERT INTO responses
                    (session_id, item_id, student_answer, is_correct, score, responded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, item_id, student_ans, 1 if score >= 3 else 0, score,
                  start_time.isoformat()))
            responses_inserted += 1
            speaking_score += score

    # ── Compute synthetic final_score (band 1–6, average of sections)
    # Reading + Listening: raw 0–35 each → band 1–6 via linear scaling
    reading_raw   = score_total  # approximate — actual items may vary
    reading_band  = max(1.0, min(6.0, 1.0 + (reading_raw / 35.0) * 5.0))
    listening_raw = score_total * 0.5  # rough estimate
    listening_band = max(1.0, min(6.0, 1.0 + (listening_raw / 35.0) * 5.0))
    writing_band_final  = max(1.0, min(6.0, writing_score / 4.0))   # rough band
    speaking_band_final = max(1.0, min(6.0, speaking_score / 5.5))  # rough band

    final_score = round(
        (reading_band + listening_band + writing_band_final + speaking_band_final) / 4.0
    , 1)

    user_conn.execute("""
        UPDATE sessions SET final_score=? WHERE id=?
    """, (final_score, session_id))
    user_conn.commit()

    return session_id, responses_inserted, final_score


def purge_synthetic(user_conn):
    """Remove all SYN_ synthetic users and their sessions/responses."""
    print("🗑  Purging all synthetic (SYN_) data from user_data.db...")
    syn_students = user_conn.execute(
        "SELECT id FROM students WHERE username LIKE 'SYN_%'"
    ).fetchall()
    student_ids  = [r[0] for r in syn_students]

    if not student_ids:
        print("✅ Nothing to purge — no SYN_ users found.")
        return

    placeholders = ",".join("?" * len(student_ids))
    # Delete responses for sessions of syn students
    session_ids = user_conn.execute(
        f"SELECT id FROM sessions WHERE student_id IN ({placeholders})", student_ids
    ).fetchall()
    session_id_list = [r[0] for r in session_ids]
    if session_id_list:
        sp = ",".join("?" * len(session_id_list))
        user_conn.execute(f"DELETE FROM responses WHERE session_id IN ({sp})", session_id_list)
    user_conn.execute(f"DELETE FROM sessions WHERE student_id IN ({placeholders})", student_ids)
    user_conn.execute(f"DELETE FROM students WHERE id IN ({placeholders})", student_ids)
    user_conn.commit()
    print(f"✅ Purged {len(student_ids)} synthetic students and their data.")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Seed synthetic TOEFL student sessions")
    parser.add_argument("--count",   type=int, default=10,
                        help="Number of sessions to generate (default: 10)")
    parser.add_argument("--profile", choices=list(PROFILES.keys()) + ["mixed"],
                        default="mixed", help="Student ability profile (default: mixed)")
    parser.add_argument("--purge-synthetic", action="store_true",
                        help="Delete all SYN_ synthetic data and exit")
    args = parser.parse_args()

    user_conn = get_db(USER_DATA_DB)
    item_conn = get_db(ITEM_BANK_DB)

    if args.purge_synthetic:
        purge_synthetic(user_conn)
        user_conn.close()
        item_conn.close()
        return 0

    print(f"\n{'='*60}")
    print(f"  Student Session Seeder")
    print(f"  Generating {args.count} session(s) — profile: {args.profile}")
    print(f"{'='*60}\n")

    # Determine profile sequence
    if args.profile == "mixed":
        profile_pool = list(PROFILES.keys())
    else:
        profile_pool = [args.profile]

    created = []
    for i in range(args.count):
        profile_name = profile_pool[i % len(profile_pool)]
        profile      = PROFILES[profile_name]
        username     = f"SYN_{profile_name.upper()}_{i+1:03d}"

        print(f"  [{i+1}/{args.count}] Creating session for {username} ({profile['cefr']})...",
              end="", flush=True)

        try:
            student_id = create_synthetic_student(user_conn, username, profile["cefr"])
            session_id, n_responses, final_score = seed_session(
                user_conn, item_conn, student_id, profile_name, i
            )
            print(f" done — session {session_id}, {n_responses} responses, band {final_score}")
            created.append((username, session_id, final_score))
        except Exception as e:
            print(f" ❌ FAILED: {e}")

    user_conn.close()
    item_conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Created {len(created)}/{args.count} synthetic sessions")
    print(f"  Run Alfred to verify: python3 agents/scripts/alfred_daily_review.py")
    print(f"  Purge before production: python3 {__file__} --purge-synthetic")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

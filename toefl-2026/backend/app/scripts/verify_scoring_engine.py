import sys
import os
import requests
import time
import subprocess

# Ensure the root 'backend' is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.database.connection import SessionLocal
from app.models.models import TestResponse, TestItemQuestion, TestItem

def get_items():
    db = SessionLocal()
    # Let's get a standard sr and cr
    # SR: MCQ
    sr_q = db.query(TestItemQuestion).filter_by(is_constructed_response=False).first()
    
    # CR: Written
    cr_q = db.query(TestItemQuestion).filter_by(is_constructed_response=True).first()
    
    return db, sr_q, cr_q

def main():
    print("Starting FastAPI server in background on port 8011...")
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8011"])
    time.sleep(4) # Wait for server to start
    
    try:
        base_url = "http://localhost:8011"
        
        # 1. Fetch valid questions from DB
        db, sr_q, cr_q = get_items()
        
        if not sr_q or not cr_q:
            print("Database has no items to test.")
            return

        print(f"Testing with SR Question: {sr_q.id} (Expected answer: {sr_q.correct_answer})")
        print(f"Testing with CR Question: {cr_q.id}")

        # 2. Create Session
        print("Creating TestSession...")
        sess_resp = requests.post(f"{base_url}/api/sessions", json={"student_id": "test_user_123"})
        sess_resp.raise_for_status()
        session_id = sess_resp.json()["id"]
        print(f"Created Session ID: {session_id}")

        # 3. Submit Answers
        sr_answer = str(sr_q.correct_answer or "test")
        # Try avoid parsing JSON lists if exist for BUILD_A_SENTENCE
        if sr_answer.startswith("["):
            import json
            parts = json.loads(sr_answer)
            if isinstance(parts, list):
                sr_answer = " ".join([str(v) for v in parts])
        
        submission = {
            "answers": {
                sr_q.id: sr_answer,
                cr_q.id: "To solve the problem, the university should allocate more funds to library services over the next few years. This would ensure students have access to all the textbooks they need."
            }
        }
        
        print("Submitting student answers and triggering ScoringEngine...")
        sub_resp = requests.post(f"{base_url}/api/sessions/{session_id}/submit", json=submission)
        
        try:
            sub_resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response Body: {sub_resp.text}")
            return
            
        print("Submission Result:", sub_resp.json())
        
        # 4. Verify Database Logging
        print("\nVerifying Data Persistence in SQLite...")
        
        # Need to refresh from db
        db.commit() # ensure latest from other connection
        responses = db.query(TestResponse).filter_by(session_id=session_id).all()
        
        print(f"Found {len(responses)} TestResponse records in the ledger.")
        assert len(responses) == 2, f"Expected 2 responses, got {len(responses)}"
        
        for r in responses:
            if r.question_id == sr_q.id:
                print(f"[SR Verification] Student Raw: {r.student_raw_response}, is_correct: {r.is_correct}")
                assert r.is_correct is not None, "SR should have is_correct set"
            elif r.question_id == cr_q.id:
                print(f"[CR Verification] Student Raw: {r.student_raw_response[:50]}..., rubric_score: {r.rubric_score}, ai_feedback: {bool(r.ai_feedback)}")
                assert r.rubric_score is not None, "CR should have a rubric_score"
                assert r.ai_feedback is not None, "CR should have ai_feedback"
                if r.ai_feedback:
                    print(f"    Feedback contents: {list(r.ai_feedback.keys())}")
                
        print("\n✅ End-to-end Data Persistence verified successfully!")
        
    finally:
        print("Shutting down server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    main()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database.connection import get_db, get_user_db
from app.models.models import TestSession, SessionStatus, TestResponse, TestItem, TestItemQuestion, User, TestEventLog

router = APIRouter()

@router.get("/admin/sessions", tags=["admin"])
def get_all_sessions(db: Session = Depends(get_db), user_db: Session = Depends(get_user_db)):
    """Fetch all test sessions with basic student info attached."""
    sessions = user_db.query(TestSession).order_by(TestSession.start_time.desc()).all()
    
    result = []
    for s in sessions:
        user = db.query(User).filter(User.id == s.student_id).first()
        student_name = f"{user.first_name} {user.last_name}" if user else "Unknown Student"
        result.append({
            "id": s.id,
            "student_id": s.student_id,
            "student_name": student_name,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "status": s.status,
            "total_score": s.total_score,
            "browser_fingerprint": s.browser_fingerprint
        })
    return result

@router.get("/admin/sessions/{session_id}", tags=["admin"])
def get_session_details(session_id: str, db: Session = Depends(get_db), user_db: Session = Depends(get_user_db)):
    """Fetch detailed response data for a specific session."""
    session = user_db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    user = db.query(User).filter(User.id == session.student_id).first()
    student_name = f"{user.first_name} {user.last_name}" if user else "Unknown Student"
    
    responses = user_db.query(TestResponse).filter(TestResponse.session_id == session_id).all()
    
    formatted_responses = []
    for r in responses:
        q = db.query(TestItemQuestion).filter(TestItemQuestion.id == r.question_id).first()
        item_type = "Unknown"
        section = "Unknown"
        question_text = ""
        correct_answer = None
        max_score = None
        
        if q:
            question_text = q.question_text
            correct_answer = q.correct_answer
            max_score = q.max_score
            item = db.query(TestItem).filter(TestItem.id == q.test_item_id).first()
            if item:
                item_type = item.task_type
                section = item.section

        formatted_responses.append({
            "id": r.id,
            "question_id": r.question_id,
            "section": section,
            "task_type": item_type,
            "question_text": question_text,
            "correct_answer": correct_answer,
            "max_score": max_score,
            "student_raw_response": r.student_raw_response,
            "is_correct": r.is_correct,
            "rubric_score": r.rubric_score,
            "ai_feedback": r.ai_feedback,
            "created_at": r.created_at
        })
        
    return {
        "session": {
            "id": session.id,
            "student_id": session.student_id,
            "student_name": student_name,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "status": session.status,
            "total_score": session.total_score,
            "browser_fingerprint": session.browser_fingerprint
        },
        "responses": formatted_responses
    }

@router.get("/admin/sessions/{session_id}/logs", tags=["admin"])
def get_session_logs(session_id: str, user_db: Session = Depends(get_user_db)):
    """Fetch behavioral event log timeline for a specific session."""
    session = user_db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    logs = user_db.query(TestEventLog).filter(TestEventLog.session_id == session_id).order_by(TestEventLog.event_timestamp.asc()).all()
    return logs

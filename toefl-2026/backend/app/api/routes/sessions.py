from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.models import TestSession, SessionStatus
from pydantic import BaseModel

router = APIRouter()

class SessionCreate(BaseModel):
    student_id: str

@router.post("/sessions", tags=["sessions"])
def create_test_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    new_session = TestSession(
        student_id=session_data.student_id,
        status=SessionStatus.ACTIVE
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions/{session_id}", tags=["sessions"])
def get_test_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

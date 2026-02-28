from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.database.connection import get_db
from app.models.models import TestEventLog, TestSession

router = APIRouter()

class EventLogEntry(BaseModel):
    event_type: str
    question_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    event_timestamp: str

class BatchLogSubmission(BaseModel):
    session_id: str
    student_id: str
    browser_fingerprint: Optional[str] = None
    logs: List[EventLogEntry]

@router.post("/logs/batch", tags=["logs"])
async def receive_batch_logs(submission: BatchLogSubmission, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None
    
    # 1. Optionally verify session exists
    session = db.query(TestSession).filter(TestSession.id == submission.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="TestSession not found for logging")

    # 2. Bulk insert logs
    new_logs = []
    for log in submission.logs:
        try:
            timestamp = datetime.fromisoformat(log.event_timestamp.replace('Z', '+00:00'))
        except ValueError:
            timestamp = datetime.utcnow()
            
        event_log = TestEventLog(
            session_id=submission.session_id,
            student_id=submission.student_id,
            question_id=log.question_id,
            event_type=log.event_type,
            event_data=log.event_data,
            client_ip=client_ip,
            browser_fingerprint=submission.browser_fingerprint,
            event_timestamp=timestamp
        )
        new_logs.append(event_log)
        
    if new_logs:
        db.bulk_save_objects(new_logs)
        db.commit()

    return {"status": "success", "inserted": len(new_logs)}

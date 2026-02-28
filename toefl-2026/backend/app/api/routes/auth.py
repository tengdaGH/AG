from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User, UserRole

router = APIRouter()

class StudentLoginRequest(BaseModel):
    student_id: str
    password: str

@router.post("/auth/student-login")
async def student_login(credentials: StudentLoginRequest, db: Session = Depends(get_db)):
    # Since the user stated "student id and password I can generate manually",
    # we use the 'email' field to store the student ID.
    user = db.query(User).filter(
        User.email == credentials.student_id, 
        User.role == UserRole.STUDENT
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not found",
        )
    
    # Check password. Since we generate manually, we will just compare as plaintext/direct hash comparison.
    if user.password_hash != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
        
    return {
        "status": "success",
        "student_id": user.email,
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

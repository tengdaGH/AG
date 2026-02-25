from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any, Union
import enum

from app.database.connection import get_db
from app.models.models import IeltsPassage, IeltsQuestionGroup, IeltsQuestion

router = APIRouter(prefix="/ielts", tags=["ielts"])

# --- Response Models ---
class IeltsQuestionResponse(BaseModel):
    id: str
    question_number: int
    question_text: Optional[str]
    options: Optional[Any]
    answer: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class IeltsQuestionGroupResponse(BaseModel):
    id: str
    group_type: str
    instructions: Optional[str]
    range_start: Optional[int]
    range_end: Optional[int]
    sort_order: int
    questions: List[IeltsQuestionResponse]

    model_config = ConfigDict(from_attributes=True)

class IeltsPassageDetailResponse(BaseModel):
    id: str
    source_id: str
    position: str
    difficulty: Optional[str]
    title: str
    has_paragraph_labels: bool
    paragraphs: List[Dict[str, str]]
    question_groups: List[IeltsQuestionGroupResponse]

    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---
@router.get("/readings/{source_id}", response_model=IeltsPassageDetailResponse)
def get_ielts_reading(source_id: str, db: Session = Depends(get_db)):
    """Fetch a complete IELTS reading passage and all its questions."""
    
    passage = db.query(IeltsPassage).options(
        joinedload(IeltsPassage.question_groups).joinedload(IeltsQuestionGroup.questions)
    ).filter(IeltsPassage.source_id == source_id).first()
    
    if not passage:
        raise HTTPException(status_code=404, detail="IELTS passage not found")
        
    # Enum conversion for Pydantic
    passage_dict = {
        "id": passage.id,
        "source_id": passage.source_id,
        "position": passage.position.value if passage.position else "UNKNOWN",
        "difficulty": passage.difficulty.value if passage.difficulty else None,
        "title": passage.title,
        "has_paragraph_labels": passage.has_paragraph_labels,
        "paragraphs": passage.paragraphs,
        "question_groups": []
    }
    
    # Sort groups by sort order
    sorted_groups = sorted(passage.question_groups, key=lambda g: g.sort_order)
    
    for group in sorted_groups:
        q_group = {
            "id": group.id,
            "group_type": group.group_type,
            "instructions": group.instructions,
            "range_start": group.range_start,
            "range_end": group.range_end,
            "sort_order": group.sort_order,
            "questions": []
        }
        
        # Sort questions by number
        sorted_qs = sorted(group.questions, key=lambda q: q.question_number)
        
        for q in sorted_qs:
            q_group["questions"].append({
                "id": q.id,
                "question_number": q.question_number,
                "question_text": q.question_text,
                "options": q.options,
                "answer": q.answer
            })
            
        passage_dict["question_groups"].append(q_group)
    
    return passage_dict

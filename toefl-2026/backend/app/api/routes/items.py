from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import func as sa_func
from typing import List, Optional, Dict, Any
from datetime import datetime

# Local imports
from app.database.connection import get_db
from app.models.models import TestItem, ItemVersionHistory, ItemReviewLog
try:
    from scripts.gauntlet_qa import qa_pipeline
except ImportError:
    pass # handle properly in the endpoint
import pydantic

router = APIRouter(prefix="/items", tags=["items"])

class TestItemQuestionResponse(pydantic.BaseModel):
    id: str
    question_number: int
    question_text: Optional[str] = None
    question_audio_url: Optional[str] = None
    replay_audio_url: Optional[str] = None
    options: Optional[List[Any]] = None
    is_constructed_response: bool
    max_score: Optional[int] = None

    class Config:
        from_attributes = True

class TestItemResponse(pydantic.BaseModel):
    id: str
    section: str
    task_type: Optional[str] = None
    target_level: str
    irt_difficulty: float
    irt_discrimination: float
    prompt_content: str
    lifecycle_status: str
    is_active: bool
    version: int = 1
    generated_by_model: Optional[str] = None
    generation_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    exposure_count: int = 0
    last_exposed_at: Optional[datetime] = None
    source_file: Optional[str] = None
    source_id: Optional[str] = None
    questions: List[TestItemQuestionResponse] = []

    class Config:
        from_attributes = True

class TestItemUpdate(pydantic.BaseModel):
    section: Optional[str] = None
    task_type: Optional[str] = None
    target_level: Optional[str] = None
    irt_difficulty: Optional[float] = None
    irt_discrimination: Optional[float] = None
    prompt_content: Optional[str] = None
    lifecycle_status: Optional[str] = None
    is_active: Optional[bool] = None
    generation_notes: Optional[str] = None

@router.get("/audit")
def get_audit(db: Session = Depends(get_db)):
    """Return item counts grouped by section and task_type for merge diagnostics."""
    rows = (
        db.query(
            TestItem.section,
            TestItem.task_type,
            sa_func.count(TestItem.id).label("count"),
        )
        .group_by(TestItem.section, TestItem.task_type)
        .all()
    )
    result = {}
    total = 0
    for section, task_type, count in rows:
        sec = section.value if section else "UNKNOWN"
        tt = task_type.value if task_type else "UNTYPED"
        result.setdefault(sec, {})[tt] = count
        total += count
    return {"total": total, "by_section": result}

@router.get("", response_model=List[TestItemResponse])
def get_items(db: Session = Depends(get_db)):
    """Retrieve all test items from the database."""
    items = db.query(TestItem).all()
    # Pydantic will serialize the ORM objects
    return items

@router.post("/qa-pipeline")
def run_qa_pipeline(db: Session = Depends(get_db)):
    """Run the LLM QA Pipeline on a batch of DRAFT and REVIEW items, with auto-remediation."""
    try:
        from scripts.gauntlet_qa import qa_pipeline
        results = qa_pipeline(limit=50)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{item_id}/qa")
def run_qa_single(item_id: str, db: Session = Depends(get_db)):
    """Run QA + auto-remediation on a single item."""
    try:
        from scripts.gauntlet_qa import qa_single_item
        result = qa_single_item(item_id)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-field-test")
def simulate_field_test(db: Session = Depends(get_db)):
    """Simulate pilot testing for items in FIELD_TEST status."""
    try:
        from scripts.simulate_field_test import run_simulation
        results = run_simulation(limit=5)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/random", response_model=List[TestItemResponse])
def get_random_items(
    section: Optional[str] = None,
    task_type: Optional[str] = None,
    count: int = 5,
    db: Session = Depends(get_db)
):
    """Return random items for test assembly, filtered by section and task_type."""
    query = db.query(TestItem)
    if section:
        query = query.filter(TestItem.section == section)
    if task_type:
        query = query.filter(TestItem.task_type == task_type)
    items = query.order_by(sa_func.random()).limit(min(count, 50)).all()
    return items

@router.get("/filter", response_model=List[TestItemResponse])
def filter_items(
    source_id_prefix: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Filter items by source_id prefix and optional section."""
    query = db.query(TestItem).filter(TestItem.is_active == True)
    if source_id_prefix:
        query = query.filter(TestItem.source_id.like(f"{source_id_prefix}%"))
    if section:
        query = query.filter(TestItem.section == section)
    return query.all()

@router.get("/by-source/{source_id}", response_model=TestItemResponse)
def get_item_by_source(source_id: str, db: Session = Depends(get_db)):
    """Retrieve a single test item by source_id."""
    item = db.query(TestItem).filter(TestItem.source_id == source_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with source_id {source_id} not found")
    return item

@router.get("/{item_id}", response_model=TestItemResponse)
def get_item(item_id: str, db: Session = Depends(get_db)):
    """Retrieve a single test item by ID."""
    item = db.query(TestItem).filter(TestItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.patch("/{item_id}", response_model=TestItemResponse)
def update_item(item_id: str, update_data: TestItemUpdate, db: Session = Depends(get_db)):
    """Update an existing test item."""
    item = db.query(TestItem).filter(TestItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update fields that are provided
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # If core prompt gets updated, we bump the version and log history to DB
    if "prompt_content" in update_dict and update_dict["prompt_content"] != item.prompt_content:
        # Save snapshot of the OLD state before we overwrite it
        old_version_snapshot = ItemVersionHistory(
            item_id=item.id,
            version_number=item.version,
            prompt_content=item.prompt_content,
            changed_by="Human Editor"
        )
        db.add(old_version_snapshot)
        item.version += 1 # bump integer
        
    for key, value in update_dict.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_item(item_id: str, db: Session = Depends(get_db)):
    """Delete a test item."""
    item = db.query(TestItem).filter(TestItem.id == item_id).first()
    if not item:
         raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted", "id": item_id}


@router.get("/{item_id}/history")
def get_item_history(item_id: str, db: Session = Depends(get_db)):
    """Retrieve review logs and version history for a specific item."""
    
    # Get review logs
    reviews = db.query(ItemReviewLog).filter(ItemReviewLog.item_id == item_id).order_by(ItemReviewLog.timestamp.desc()).all()
    
    # Get version history
    versions = db.query(ItemVersionHistory).filter(ItemVersionHistory.item_id == item_id).order_by(ItemVersionHistory.version_number.desc()).all()
    
    return {
        "reviews": [
            {
                "id": r.id,
                "stage_name": r.stage_name,
                "reviewer": r.reviewer,
                "action": r.action,
                "notes": r.notes,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            } for r in reviews
        ],
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "prompt_content": v.prompt_content,
                "changed_by": v.changed_by,
                "timestamp": v.timestamp.isoformat() if v.timestamp else None
            } for v in versions
        ]
    }

# ============================================================
# Purpose:       Phase 4: Ingest validated WAD items into the SQLite item bank database.
# Usage:         python backend/scripts/wad_ingestion/phase4_ingest.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import uuid

# Add backend dir to path for imports
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal
from app.models.models import TestItem, SectionType, TaskType, CEFRLevel

def run_phase_4():
    print("Phase 4: Database Ingestion...")
    valid_path = os.path.join(os.path.dirname(__file__), "validated_items.json")
    
    if not os.path.exists(valid_path):
        print("validated_items.json not found.")
        sys.exit(1)
        
    with open(valid_path, "r", encoding="utf-8") as f:
        validated_items = json.load(f)
        
    db = SessionLocal()
    
    count = 0
    for folder_name, data in validated_items.items():
        # Avoid duplicates based on source_id or content
        # Check if we already imported this one
        existing = db.query(TestItem).filter(TestItem.source_id == folder_name).first()
        if existing:
            print(f"  [Skip] Already imported: {folder_name[:30]}")
            continue
            
        pc = {
            "type": "Write for an Academic Discussion",
            "title": data.get("topic", "Academic Discussion"),
            "professor_prompt": data.get("professor_prompt"),
            "student_1_name": data.get("student_1_name"),
            "student_1_response": data.get("student_1_response"),
            "student_2_name": data.get("student_2_name"),
            "student_2_response": data.get("student_2_response")
        }
        
        new_item = TestItem(
            id=str(uuid.uuid4()),
            section=SectionType.WRITING,
            task_type=TaskType.WRITE_ACADEMIC_DISCUSSION,
            target_level=CEFRLevel.B2,  # Defaulting to B2 for WAD standard items
            irt_difficulty=0.5,
            irt_discrimination=1.0,
            prompt_content=json.dumps(pc),
            is_active=True,
            version=1,
            generated_by_model="Gemini-1.5-Pro-Extraction",
            generation_notes=f"Auto-extracted via Optical Character Recognition from image: {data.get('original_image_file')}.",
            source_file="validated_items.json",
            source_id=folder_name
        )
        
        db.add(new_item)
        count += 1
        print(f"  ✓ Inserted: {pc['title'][:40]}")
        
    db.commit()
    db.close()
    
    print(f"\nPhase 4 Complete! Successfully inserted {count} valid WAD items into the Item Bank.")

if __name__ == "__main__":
    run_phase_4()

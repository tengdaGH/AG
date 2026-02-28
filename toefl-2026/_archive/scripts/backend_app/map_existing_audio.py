"""
Script to map existing synthesized audio files to database records for TOEFL 2026.
Focuses on resolving ID mismatches between filesystem assets and database entries.
"""
import os
import sys
import json
from pathlib import Path
from sqlalchemy.orm.attributes import flag_modified

# Add project root to path
sys.path.append("/Users/tengda/Antigravity/toefl-2026/backend")
from app.database.connection import SessionLocal
from app.models.models import TestItem

AUDIO_DIR = Path("/Users/tengda/Antigravity/toefl-2026/audio")

def main():
    db = SessionLocal()
    
    # 1. Gather all existing audio files
    audio_files = []
    for root, _, files in os.walk(AUDIO_DIR):
        for f in files:
            if f.endswith(".mp3") or f.endswith(".wav"):
                rel_path = Path(root).relative_to(AUDIO_DIR.parent) / f
                audio_files.append({
                    "name": f,
                    "stem": Path(f).stem,
                    "path": f"/{rel_path}"
                })
                
    print(f"Found {len(audio_files)} audio files in {AUDIO_DIR}")

    # 2. Get ALL listening/speaking items that lack audio path
    items = db.query(TestItem).filter(
        TestItem.section.in_(["LISTENING", "SPEAKING"])
    ).all()
    
    mapping_count = 0
    
    for item in items:
        pc = json.loads(item.prompt_content)
        if pc.get("audio_path"):
            continue
            
        source_id = item.source_id
        if not source_id:
            continue
        matched_path = None
        
        # Strategy A: Direct Match
        for af in audio_files:
            if af["stem"] == source_id:
                matched_path = af["path"]
                break
                
        # Strategy B: Suffix Match (e.g., ETS-T1-L-M1-CR-1 -> ETS-T1-L-M1-CR)
        if not matched_path:
            for af in audio_files:
                if source_id.startswith(af["stem"] + "-"):
                    matched_path = af["path"]
                    break
                    
        if matched_path:
            print(f"Mapping {source_id} -> {matched_path}")
            pc["audio_path"] = matched_path
            item.prompt_content = json.dumps(pc, ensure_ascii=False)
            flag_modified(item, "prompt_content")
            mapping_count += 1
            
    if mapping_count > 0:
        db.commit()
        print(f"Successfully mapped {mapping_count} items.")
    else:
        print("No new mappings found.")

if __name__ == "__main__":
    main()

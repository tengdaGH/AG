import os
import json
import shutil
import subprocess
from pathlib import Path
from app.database.connection import SessionLocal
from app.models.models import TestItem
from sqlalchemy.orm.attributes import flag_modified

# Paths
DOWNLOADS_DIR = Path("/Users/tengda/Downloads")
S1_OGG_DIR = DOWNLOADS_DIR / "Student Practice Test 1 - Audio Files" / "Listening" / "Question Response"
S1_MP3_DIR = DOWNLOADS_DIR / "2026托福改革新题型官方15套样题合集（截止至2025.12.25）" / "【2套】2026新版托福官方样题-学生用" / "样题1 音频"
S2_MP3_DIR = DOWNLOADS_DIR / "2026托福改革新题型官方15套样题合集（截止至2025.12.25）" / "【2套】2026新版托福官方样题-学生用" / "样题2 音频"
AUDIO_OUTPUT_BASE = Path("/Users/tengda/Antigravity/toefl-2026/audio")

# Ensure output dirs exist
(AUDIO_OUTPUT_BASE / "listening").mkdir(parents=True, exist_ok=True)
(AUDIO_OUTPUT_BASE / "speaking").mkdir(parents=True, exist_ok=True)

db = SessionLocal()

# Mapping Dictionaries: item_id -> source_audio_path
MAPPING = {}

# --- S1 Choose Response (Segmented OGGs) ---
# Module 1 (1-8)
for i in range(1, 9):
    item_id = f"ETS-S1-L-M1-CR-{i}"
    source_path = S1_OGG_DIR / f"Listening1_Question Response_Question{i}.ogg"
    MAPPING[item_id] = source_path

# Module 2 (1-8)
for i in range(1, 9):
    item_id = f"ETS-S1-L-M2-CR-{i}"
    source_path = S1_OGG_DIR / f"Listening2_Question Response_Question{i}.ogg"
    MAPPING[item_id] = source_path

# --- S1 Passages (Combined MP3s) ---
MAPPING["ETS-S1-L-M1-PA-1"] = S1_MP3_DIR / "托福样题01-听力-Module 01-02-Conversation 01.mp3"
MAPPING["ETS-S1-L-M1-PA-2"] = S1_MP3_DIR / "托福样题01-听力-Module 01-02-Conversation 02.mp3"
MAPPING["ETS-S1-L-M1-PA-3"] = S1_MP3_DIR / "托福样题01-听力-Module 01-03-Announcement.mp3"
MAPPING["ETS-S1-L-M1-PA-4"] = S1_MP3_DIR / "托福样题01-听力-Module 01-04-Academic Talk.mp3"

MAPPING["ETS-S1-L-M2-PA-1"] = S1_MP3_DIR / "托福样题01-听力-Module 02-02-Conversation 01.mp3"
MAPPING["ETS-S1-L-M2-PA-2"] = S1_MP3_DIR / "托福样题01-听力-Module 02-03-Announcement.mp3"
MAPPING["ETS-S1-L-M2-PA-3"] = S1_MP3_DIR / "托福样题01-听力-Module 02-04-Academic Talk.mp3"

# --- S2 Passages (Combined MP3s) ---
MAPPING["ETS-S2-L-M1-PA-1"] = S2_MP3_DIR / "托福样题02-听力-Module 01-02-Conversation 01.mp3"
MAPPING["ETS-S2-L-M1-PA-2"] = S2_MP3_DIR / "托福样题02-听力-Module 01-02-Conversation 02.mp3"
MAPPING["ETS-S2-L-M1-PA-3"] = S2_MP3_DIR / "托福样题02-听力-Module 01-03-Announcement.mp3"
MAPPING["ETS-S2-L-M1-PA-4"] = S2_MP3_DIR / "托福样题02-听力-Module 01-04-Academic Talk.mp3"

MAPPING["ETS-S2-L-M2-PA-1"] = S2_MP3_DIR / "托福样题02-听力-Module 02-02-Conversation 01.mp3"
MAPPING["ETS-S2-L-M2-PA-2"] = S2_MP3_DIR / "托福样题02-听力-Module 02-03-Announcement.mp3"
MAPPING["ETS-S2-L-M2-PA-3"] = S2_MP3_DIR / "托福样题02-听力-Module 02-04-Academic Talk.mp3"

# --- Speaking Tasks (S1 & S2) ---
MAPPING["ETS-S1-S-LAR"] = S1_MP3_DIR / "托福样题01-口语-01-Listen and Repeat.mp3"
MAPPING["ETS-S1-S-INT"] = S1_MP3_DIR / "托福样题01-口语-02-Interview.mp3"
MAPPING["ETS-S2-S-LAR"] = S2_MP3_DIR / "托福样题02-口语-01-Listen and Repeat.mp3"
MAPPING["ETS-S2-S-INT"] = S2_MP3_DIR / "托福样题02-口语-02-Interview.mp3"

mapped_count = 0
not_found_in_db = 0
file_missing = 0

for item_id, source_path in MAPPING.items():
    if not source_path.exists():
        print(f"Warning: Source file missing: {source_path}")
        file_missing += 1
        continue
    
    item = db.query(TestItem).filter(TestItem.source_id == item_id).first()
    if not item:
        print(f"Warning: Item {item_id} not found in database.")
        not_found_in_db += 1
        continue
    
    # Determine section folder
    section_dir = "speaking" if "-S-" in item_id else "listening"
    out_filename = f"{item_id}.mp3"
    out_path = AUDIO_OUTPUT_BASE / section_dir / out_filename
    
    # Copy or Convert
    if out_path.exists():
        pass # Already exists
    elif source_path.suffix.lower() == ".ogg":
        print(f"Converting {source_path.name} -> {out_filename}")
        # Transcode OGG to MP3
        subprocess.run([
            "ffmpeg", "-y", "-i", str(source_path), 
            "-codec:a", "libmp3lame", "-qscale:a", "2", 
            str(out_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"Copying {source_path.name} -> {out_filename}")
        shutil.copy2(source_path, out_path)
    
    # Assign relative path to databank prompt_content
    rel_path = f"/audio/{section_dir}/{out_filename}"
    prompt_content = json.loads(item.prompt_content)
    if prompt_content.get("audio_path") != rel_path:
        prompt_content["audio_path"] = rel_path
        item.prompt_content = json.dumps(prompt_content, ensure_ascii=False)
        flag_modified(item, "prompt_content")
        mapped_count += 1

db.commit()
print("========================================")
print(f"✅ Successfully mapped & updated {mapped_count} audio tracks in DB.")
if not_found_in_db > 0:
    print(f"❌ Items not found in DB: {not_found_in_db}")
if file_missing > 0:
    print(f"❌ Source files missing on disk: {file_missing}")
print("========================================")

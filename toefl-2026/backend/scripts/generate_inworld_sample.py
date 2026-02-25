# ============================================================
# Purpose:       Sample run: generate Inworld TTS audio for the first 3 listening/speaking items (proof of concept).
# Usage:         python backend/scripts/generate_inworld_sample.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import time
import json
import sqlite3
import asyncio
import tempfile
import subprocess

from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.inworld_service import generate_audio_with_inworld

async def generate_line_audio(text, voice, out_path):
    result = await generate_audio_with_inworld(text, voice_id=voice, output_path=out_path)
    return result.get('status') == 'success'

async def process_items():
    db_path = "/Users/tengda/Antigravity/toefl-2026/backend/toefl_2026.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, task_type, prompt_content 
        FROM test_items 
        WHERE section IN ('LISTENING', 'SPEAKING') 
        AND (media_url IS NULL OR media_url = '' OR prompt_content LIKE '%PENDING_TTS%')
        LIMIT 3
    """)
    rows = cur.fetchall()

    frontend_audio_dir = "/Users/tengda/Antigravity/toefl-2026/frontend/public/audio"
    
    for row in rows:
        item_id = row[0]
        task_type = row[1]
        content = json.loads(row[2])
        
        lines = [] # list of (speaker, text)
        
        # Voice mapping options for Inworld
        speaker_mapping = {
            "Narrator": "Blake",
            "Interviewer": "Olivia",
            "Professor": "Edward",
            "Speaker": "Ashley",
            "Speaker A": "Ashley",
            "Speaker B": "Diego",
        }
        
        if task_type == "LISTEN_CONVERSATION":
            if "transcript" in content:
                for idx, turn in enumerate(content["transcript"]):
                    speaker = turn.get("speaker", f"Speaker_{idx}")
                    text = turn.get("text", "")
                    if speaker not in speaker_mapping:
                        speaker_mapping[speaker] = "Ashley" if len(speaker_mapping) % 2 == 0 else "Diego"
                    lines.append((speaker_mapping[speaker], text))
                    
        elif task_type in ["LISTEN_ACADEMIC_TALK", "LISTEN_ANNOUNCEMENT"]:
            speaker = "Professor" if task_type == "LISTEN_ACADEMIC_TALK" else "Narrator"
            text = content.get("text", "")
            lines.append((speaker_mapping[speaker], text))

        elif task_type == "LISTEN_CHOOSE_RESPONSE":
            if "dialogue" in content:
                for idx, turn in enumerate(content["dialogue"]):
                    speaker = "Speaker A" if idx % 2 == 0 else "Speaker B"
                    lines.append((speaker_mapping[speaker], turn))

        elif task_type == "TAKE_AN_INTERVIEW":
            scenario = content.get("scenario", "")
            if scenario:
                lines.append(("Blake", scenario))
            if "questions" in content:
                for idx, q in enumerate(content["questions"]):
                    q_text = q.get("text", "")
                    lines.append(("Olivia", q_text))
            
        elif task_type == "LISTEN_AND_REPEAT":
            text = ""
            if "sentences" in content and len(content["sentences"]) > 0:
                text = content["sentences"][0].get("text", "")
            lines.append(("Ashley", text))
            
        else:
            print(f"Unsupported task_type {task_type}")
            continue

        if not lines:
            continue

        filename = f"{item_id}.mp3"
        filepath = os.path.join(frontend_audio_dir, filename)
        print(f"Generating Inworld audio for item {item_id} ({task_type}) - {len(lines)} lines")
        
        final_audio_path = filepath
        silence_path = os.path.join(tempfile.gettempdir(), f"silence_500ms.mp3")
        if not os.path.exists(silence_path):
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", silence_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
        success_all = True
        tmp_paths = []
        for idx, (voice, text) in enumerate(lines):
            tmp_path = os.path.join(tempfile.gettempdir(), f"tmp_{item_id}_{idx}.mp3")
            print(f"  Line {idx+1}/{len(lines)} -> Voice {voice}")
            ok = await generate_line_audio(text, voice, tmp_path)
            if not ok:
                success_all = False
                break
            tmp_paths.append(tmp_path)
            
        if success_all:
            concat_list_path = os.path.join(tempfile.gettempdir(), f"concat_list_{item_id}.txt")
            with open(concat_list_path, 'w') as f:
                for i, tp in enumerate(tmp_paths):
                    f.write(f"file '{tp}'\n")
                    if i < len(tmp_paths) - 1:
                        f.write(f"file '{silence_path}'\n")
                        
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", final_audio_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            # Clean up
            os.remove(concat_list_path)
            for tp in tmp_paths:
                if os.path.exists(tp):
                    os.remove(tp)
            
            db_media_param = f"audio/{filename}"
            if content.get("audio_url") == "PENDING_TTS":
                content["audio_url"] = db_media_param
                
            cur.execute("""
                UPDATE test_items 
                SET media_url = ?, prompt_content = ?, generated_by_model = ?
                WHERE id = ?
            """, (db_media_param, json.dumps(content), "Inworld", item_id))
            conn.commit()
            print(f"Saved DB for item {item_id}")
            
    conn.close()
    print("Completed Inworld sample generation.")

if __name__ == "__main__":
    asyncio.run(process_items())

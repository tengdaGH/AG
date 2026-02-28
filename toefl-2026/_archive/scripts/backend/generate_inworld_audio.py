# ============================================================
# Purpose:       Generate TTS audio for listening/speaking items via Inworld voices with per-line slicing and concatenation.
# Usage:         python backend/scripts/generate_inworld_audio.py
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
    clean_text = text
    result = await generate_audio_with_inworld(clean_text, voice_id=voice, output_path=out_path)
    return result.get('status') == 'success'

async def process_items():
    db_path = "/Users/tengda/Antigravity/toefl-2026/backend/item_bank.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, task_type, prompt_content 
        FROM test_items 
        WHERE section IN ('LISTENING', 'SPEAKING') 
        AND (media_url IS NULL OR media_url = '' OR prompt_content LIKE '%PENDING_TTS%')
        AND generated_by_model IS NOT 'Inworld' AND generated_by_model IS NOT 'Inworld_Sliced'
    """)
    rows = cur.fetchall()

    frontend_audio_dir = "/Users/tengda/Antigravity/toefl-2026/frontend/public/audio"
    print(f"Found {len(rows)} remaining items to generate natively via Inworld.")
    
    speaker_mapping = {
        "Narrator": "Edward",
        "Interviewer": "Ashley",
        "Professor": "Edward",
        "Speaker": "Diego",
        "Speaker A": "Diego",
        "Speaker B": "Olivia",
    }
    
    for idx_item, row in enumerate(rows):
        item_id = row[0]
        task_type = row[1]
        try:
            content = json.loads(row[2])
        except Exception:
            continue
            
        success_all = True
        
        # Interactive Sliced Items
        if task_type in ["TAKE_AN_INTERVIEW", "LISTEN_AND_REPEAT"]:
            print(f"[{idx_item+1}/{len(rows)}] Generating Sliced Inworld audio for {item_id} ({task_type})")
            
            if task_type == "TAKE_AN_INTERVIEW":
                scenario = content.get("scenario", "")
                if scenario:
                    scen_file = f"{item_id}_scenario.mp3"
                    scen_path = os.path.join(frontend_audio_dir, scen_file)
                    if await generate_line_audio(scenario, speaker_mapping["Narrator"], scen_path):
                        content["scenario_audio"] = f"/audio/{scen_file}"
                    else:
                        success_all = False
                
                if "questions" in content:
                    for q_idx, q in enumerate(content["questions"]):
                        q_text = q.get("text", "")
                        q_file = f"{item_id}_q{q_idx}.mp3"
                        q_path = os.path.join(frontend_audio_dir, q_file)
                        if await generate_line_audio(q_text, speaker_mapping["Interviewer"], q_path):
                            q["audio_url"] = f"/audio/{q_file}"
                        else:
                            success_all = False
                            
            elif task_type == "LISTEN_AND_REPEAT":
                if "sentences" in content:
                    for s_idx, s in enumerate(content["sentences"]):
                        s_text = s.get("text", "")
                        s_file = f"{item_id}_s{s_idx}.mp3"
                        s_path = os.path.join(frontend_audio_dir, s_file)
                        if await generate_line_audio(s_text, speaker_mapping["Interviewer"], s_path):
                            s["audio_url"] = f"/audio/{s_file}"
                        else:
                            success_all = False
                            
            if success_all:
                if content.get("audio_url") == "PENDING_TTS":
                    del content["audio_url"]
                cur.execute("""
                    UPDATE test_items 
                    SET prompt_content = ?, generated_by_model = ?
                    WHERE id = ?
                """, (json.dumps(content), "Inworld_Sliced", item_id))
                conn.commit()
                print(f"  -> Saved sliced {item_id}")

        else:
            # Traditional Concatenated Items
            lines = []
            if task_type == "LISTEN_CONVERSATION":
                if "transcript" in content:
                    for idx, turn in enumerate(content["transcript"]):
                        speaker = turn.get("speaker", f"Speaker_{idx}")
                        text = turn.get("text", "")
                        if speaker not in speaker_mapping:
                            speaker_mapping[speaker] = "Diego" if len(speaker_mapping) % 2 == 0 else "Olivia"
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

            if not lines:
                continue

            filename = f"{item_id}.mp3"
            filepath = os.path.join(frontend_audio_dir, filename)
            print(f"[{idx_item+1}/{len(rows)}] Generating Inworld concated audio for {item_id} ({task_type}) - {len(lines)} lines")
            
            silence_path = os.path.join(tempfile.gettempdir(), f"silence_500ms.mp3")
            if not os.path.exists(silence_path):
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", silence_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
            tmp_paths = []
            for idx, (voice, text) in enumerate(lines):
                tmp_path = os.path.join(tempfile.gettempdir(), f"tmp_{item_id}_{idx}.mp3")
                if await generate_line_audio(text, voice, tmp_path):
                    tmp_paths.append(tmp_path)
                else:
                    success_all = False
                    break
                
            if success_all:
                concat_list_path = os.path.join(tempfile.gettempdir(), f"concat_list_{item_id}.txt")
                with open(concat_list_path, 'w') as f:
                    for i, tp in enumerate(tmp_paths):
                        f.write(f"file '{tp}'\n")
                        if i < len(tmp_paths) - 1:
                            f.write(f"file '{silence_path}'\n")
                            
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
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
                print(f"  -> Saved {item_id}")

    conn.close()
    print("Completed full Inworld generation run.")

if __name__ == "__main__":
    asyncio.run(process_items())

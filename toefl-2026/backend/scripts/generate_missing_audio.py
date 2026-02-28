# ============================================================
# Purpose:       Generate missing TTS audio for listening/speaking items using Gemini multi-speaker TTS.
# Usage:         python backend/scripts/generate_missing_audio.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import time
import json
import sqlite3
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def save_wav_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """Saves raw PCM audio data as a proper .wav file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

def generate_conversation_audio(dialogue_script, speaker_mapping, filename, max_retries=5):
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"Skipping {filename}, already exists.")
        return True

    prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n\n{dialogue_script}"
    
    speaker_configs = []
    for speaker_name, voice_name in speaker_mapping.items():
        speaker_configs.append(
            types.SpeakerVoiceConfig(
                speaker=speaker_name, 
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            )
        )
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-preview-tts',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['AUDIO'],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_configs
                        )
                    )
                )
            )
            data = response.candidates[0].content.parts[0].inline_data.data
            save_wav_file(filename, data)
            
            time.sleep(6.1) 
            return True
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (2 ** attempt)
                print(f"Rate limited. Sleeping for {wait}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"Error generating audio: {e}")
                return False

    return False

def process_items():
    db_path = "/Users/tengda/Antigravity/toefl-2026/backend/item_bank.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, task_type, prompt_content FROM test_items WHERE section IN ('LISTENING', 'SPEAKING') AND (media_url IS NULL OR media_url = '' OR prompt_content LIKE '%PENDING_TTS%')")
    rows = cur.fetchall()

    frontend_audio_dir = "/Users/tengda/Antigravity/toefl-2026/frontend/public/audio"
    
    processed_count = 0
    
    for row in rows:
        item_id = row[0]
        task_type = row[1]
        try:
            content = json.loads(row[2])
        except Exception:
            print(f"Error parsing JSON for item {item_id}")
            continue
            
        dialogue_script = ""
        speaker_mapping = {}
        
        if task_type == "LISTEN_CONVERSATION":
            speaker_mapping = {}
            lines = []
            if "transcript" in content:
                for idx, turn in enumerate(content["transcript"]):
                    speaker = turn.get("speaker", f"Speaker_{idx}")
                    text = turn.get("text", "")
                    lines.append(f"{speaker}: {text}")
                    if speaker not in speaker_mapping:
                        if len(speaker_mapping) == 0:
                            speaker_mapping[speaker] = "Puck"
                        elif len(speaker_mapping) == 1:
                            speaker_mapping[speaker] = "Kore"
                        else:
                            speaker_mapping[speaker] = "Aoede"
            dialogue_script = "\n".join(lines)
            
        elif task_type in ["LISTEN_ACADEMIC_TALK", "LISTEN_ANNOUNCEMENT"]:
            speaker = "Professor" if task_type == "LISTEN_ACADEMIC_TALK" else "Narrator"
            voice = "Charon" if task_type == "LISTEN_ACADEMIC_TALK" else "Fenrir"
            text = content.get("text", "")
            dialogue_script = f"{speaker}: {text}"
            speaker_mapping = {speaker: voice}

        elif task_type == "LISTEN_CHOOSE_RESPONSE":
            lines = []
            speaker_mapping = {"Speaker A": "Puck", "Speaker B": "Kore"}
            if "dialogue" in content:
                for idx, turn in enumerate(content["dialogue"]):
                    speaker = "Speaker A" if idx % 2 == 0 else "Speaker B"
                    lines.append(f"{speaker}: {turn}")
            dialogue_script = "\n".join(lines)

        elif task_type == "TAKE_AN_INTERVIEW":
            lines = []
            speaker_mapping = {"Narrator": "Fenrir", "Interviewer": "Aoede"}
            scenario = content.get("scenario", "")
            if scenario:
                lines.append(f"Narrator: {scenario}")
            
            if "questions" in content:
                for idx, q in enumerate(content["questions"]):
                    q_text = q.get("text", "")
                    lines.append(f"Interviewer: {q_text}")
            dialogue_script = "\n".join(lines)
            
        elif task_type == "LISTEN_AND_REPEAT":
            speaker_mapping = {"Speaker": "Aoede"}
            text = ""
            if "sentences" in content and len(content["sentences"]) > 0:
                text = content["sentences"][0].get("text", "")
            dialogue_script = f"Speaker: {text}"
            
        else:
            print(f"Unsupported task_type {task_type} for item {item_id}")
            continue

        if not dialogue_script.strip():
            print(f"Empty dialogue script for item {item_id}, skipping")
            continue

        filename = f"{item_id}.wav"
        filepath = os.path.join(frontend_audio_dir, filename)
        
        print(f"[{processed_count+1}/{len(rows)}] Generating audio for item {item_id} ({task_type})...")
        success = generate_conversation_audio(dialogue_script, speaker_mapping, filepath)
        
        if success:
            db_media_param = f"audio/{filename}"
            if content.get("audio_url") == "PENDING_TTS":
                content["audio_url"] = db_media_param
            
            cur.execute("""
                UPDATE test_items 
                SET media_url = ?, prompt_content = ? 
                WHERE id = ?
            """, (db_media_param, json.dumps(content), item_id))
            conn.commit()
            print(f"Saved DB for item {item_id}")
            
        processed_count += 1

    conn.close()
    print("Completed processing.")

if __name__ == "__main__":
    process_items()

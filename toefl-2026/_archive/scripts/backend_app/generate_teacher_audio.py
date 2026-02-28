import os
import sys
import json
import wave
import uuid
import re
import random
import subprocess
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv

# Add skills dir for log_audio
sys.path.append("/Users/tengda/Antigravity/.agent/skills/toefl_voice_direction")
from log_audio import append_voice_log, set_log_path

from app.database.connection import SessionLocal
from app.models.models import TestItem, TaskType
from sqlalchemy.orm.attributes import flag_modified

from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

AUDIO_OUTPUT_BASE = Path("/Users/tengda/Antigravity/toefl-2026/audio")
set_log_path("/Users/tengda/Antigravity/toefl-2026/audio/audio_voice_log.jsonl")

def generate_multi_speaker(script_lines, speaker_voice_map, tone_instruction, out_path_wav):
    formatted = "\n".join(f"{spk}: {txt}" for spk, txt in script_lines)
    prompt = f"{tone_instruction}\n\nGenerate audio from this precise transcript without adding or modifying anything:\n\n{formatted}"
    
    speaker_configs = [
        types.SpeakerVoiceConfig(
            speaker=name,
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))
        )
        for name, voice in speaker_voice_map.items()
    ]
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_configs[:2] # Max 2
                )
            )
        )
    )
    
    pcm = response.candidates[0].content.parts[0].inline_data.data
    with wave.open(str(out_path_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)

def generate_single_speaker(text, voice, tone_instruction, out_path_wav):
    prompt = f"{tone_instruction}\n\nGenerate audio from this precise transcript without adding or modifying anything:\n{text}"
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))
            )
        )
    )
    pcm = response.candidates[0].content.parts[0].inline_data.data
    with wave.open(str(out_path_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)

def transcode_to_mp3(wav_path, mp3_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path), 
        "-codec:a", "libmp3lame", "-qscale:a", "2", 
        str(mp3_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def determine_assignment(text, task_type):
    """
    Parses the text and returns processing variables.
    """
    if task_type == TaskType.LISTEN_CONVERSATION:
        lines = []
        for line in text.splitlines():
            if ":" in line:
                spk, dialog = line.split(":", 1)
                lines.append((spk.strip(), dialog.strip()))
        
        # Determine speakers
        speaker_voice_map = {}
        for spk, _ in lines:
            if spk not in speaker_voice_map:
                if "woman" in spk.lower() or "female" in spk.lower():
                    speaker_voice_map[spk] = random.choice(["Kore", "Leda", "Despina"])
                elif "man" in spk.lower() or "male" in spk.lower():
                    speaker_voice_map[spk] = random.choice(["Puck", "Achird", "Zephyr"])
                else:
                    speaker_voice_map[spk] = random.choice(["Puck", "Kore"])
                    
        if len(speaker_voice_map) >= 2:
            # Multi-speaker requires exactly 2 voices for now in Gemini TTS
            # Use the first two detected roles
            top_two = {}
            roles = list(speaker_voice_map.keys())[:2]
            for r in roles:
                top_two[r] = speaker_voice_map[r]
            
            return {
                "mode": "multi",
                "script_lines": lines,
                "speaker_voice_map": top_two,
                "tone": "Natural, conversational tone. Each speaker should sound like a real person talking, not reading. Match the emotion implied by the dialogue."
            }
        elif len(speaker_voice_map) == 1:
            spk = list(speaker_voice_map.keys())[0]
            voice = speaker_voice_map[spk]
            return {
                "mode": "single",
                "voice": voice,
                "speaker_data": {"role": spk, "gender": "F" if voice in ["Kore", "Leda", "Despina"] else "M", "age_range": "young-adult", "accent": "american", "voice": voice},
                "tone": "Natural, conversational tone. Match the emotion implied by the dialogue."
            }
        else:
            return {
                "mode": "single",
                "voice": "Kore",
                "speaker_data": {"role": "Speaker", "gender": "F", "age_range": "young-adult", "accent": "american", "voice": "Kore"},
                "tone": "Natural, conversational tone."
            }
        
    elif task_type == TaskType.LISTEN_ACADEMIC_TALK:
        is_female = random.choice([True, False])
        voice = "Callirrhoe" if is_female else "Charon"
        return {
            "mode": "single",
            "voice": voice,
            "speaker_data": {"role": "Professor", "gender": "F" if is_female else "M", "age_range": "mid-career/senior", "accent": "american", "voice": voice},
            "tone": "Deliver in a measured, authoritative academic lecture tone. Speak clearly with natural academic pacing — not rushed. Slight gravitas; this is an educator addressing students."
        }
        
    elif task_type == TaskType.LISTEN_ANNOUNCEMENT:
        is_female = random.choice([True, False])
        voice = "Autonoe" if is_female else "Fenrir"
        return {
            "mode": "single",
            "voice": voice,
            "speaker_data": {"role": "Announcer", "gender": "F" if is_female else "M", "age_range": "mid-career", "accent": "american", "voice": voice},
            "tone": "Friendly, clear campus broadcast voice. Upbeat but professional, like a university radio announcer. Moderate pace, warm energy."
        }
        
    elif task_type == TaskType.LISTEN_CHOOSE_RESPONSE:
        # e.g. "1. Woman: Need anything... \n(A) ..."
        # We only want the first line for the stimulus
        stimulus = text.split("\n")[0]
        # Remove "1. "
        stimulus = re.sub(r'^\d+\.\s*', '', stimulus)
        is_female = "woman" in stimulus.lower() or "female" in stimulus.lower()
        if not is_female and "man" not in stimulus.lower():
            is_female = random.choice([True, False])
        voice = "Kore" if is_female else "Puck"
        return {
            "mode": "single",
            "voice": voice,
            "speaker_data": {"role": "Student", "gender": "F" if voice == "Kore" else "M", "age_range": "young-adult", "accent": "american", "voice": voice},
            "tone": "Neutral, natural conversational stimulus. Short, clear, single utterance. Sound like an ordinary person in a casual exchange.",
            "clean_text": stimulus
        }
        
    elif task_type == TaskType.LISTEN_AND_REPEAT:
        return {
            "mode": "single",
            "voice": "Fenrir",
            "speaker_data": {"role": "Instructor", "gender": "M", "age_range": "mid-career", "accent": "american", "voice": "Fenrir"},
            "tone": "Clear, pedagogical delivery. Speak each word cleanly and at a slightly measured pace — this audio is used for language learning repetition practice."
        }
        
    elif task_type == TaskType.TAKE_AN_INTERVIEW:
        return {
            "mode": "single",
            "voice": "Laomedeia",
            "speaker_data": {"role": "Interviewer", "gender": "F", "age_range": "mid-career", "accent": "british", "voice": "Laomedeia"},
            "tone": "Professional, warm, and genuinely curious. Conversational but polished, like a TV journalist."
        }
    
    return None

def main():
    db = SessionLocal()
    # Get all ETS items (Teacher + Student) without audio
    items = db.query(TestItem).filter(
        TestItem.source_id.like("ETS-%"),
        TestItem.section.in_(["LISTENING", "SPEAKING"])
    ).all()
    
    items_to_process = []
    for it in items:
        try:
            pc = json.loads(it.prompt_content)
            if not pc.get("audio_path"):
                items_to_process.append(it)
        except:
            pass
            
    if not items_to_process:
        print("No items need audio generation!")
        return
        
    print(f"[{len(items_to_process)}] items need TTS Audio generated.")
    
    for idx, item in enumerate(items_to_process, 1):
        print(f"Processing {idx}/{len(items_to_process)}: {item.source_id}...")
        
        pc = json.loads(item.prompt_content)
        raw_text = pc.get("transcript", pc.get("text", ""))
        if isinstance(raw_text, dict):
            text = raw_text.get("text", "")
        else:
            text = raw_text
            
        if not text:
            print(f"  Skipping {item.source_id} - no text/transcript found.")
            continue
            
        plan = determine_assignment(text, item.task_type)
        if not plan:
            print(f"  Unknown task type {item.task_type}, skipping.")
            continue
            
        section_dir = "speaking" if item.section == "SPEAKING" else "listening"
        out_filename = f"{item.source_id}.mp3"
        out_path_mp3 = AUDIO_OUTPUT_BASE / section_dir / out_filename
        
        os.makedirs(out_path_mp3.parent, exist_ok=True)
        
        # Generate Audio
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_wav:
            try:
                if plan["mode"] == "multi":
                    generate_multi_speaker(plan["script_lines"], plan["speaker_voice_map"], plan["tone"], tmp_wav.name)
                else:
                    generate_single_speaker(plan.get("clean_text", text), plan["voice"], plan["tone"], tmp_wav.name)
            except Exception as e:
                print(f"  TTS Error for {item.source_id}: {e}")
                time.sleep(30) # Backoff
                continue
                
            # Convert
            transcode_to_mp3(tmp_wav.name, out_path_mp3)
        
        # Log to JSONL
        log_speakers = []
        if plan["mode"] == "multi":
            for n, v in plan["speaker_voice_map"].items():
                log_speakers.append({
                    "role": "Speaker",
                    "name": n,
                    "gender": "F" if v in ["Kore", "Leda", "Despina", "Callirrhoe", "Aoede", "Autonoe", "Laomedeia"] else "M",
                    "age_range": "mixed",
                    "accent": "american",
                    "voice": v,
                    "tone_instruction": plan["tone"]
                })
        else:
            log_speakers.append(plan["speaker_data"])
            
        append_voice_log(
            item_id=item.source_id,
            task_type=item.task_type.name,
            audio_file=f"audio/{section_dir}/{out_filename}",
            engine="gemini-2.5-flash-preview-tts",
            mode=plan["mode"],
            speakers=log_speakers,
            tts_prompt_preview=(plan["tone"] + "\n\n" + plan.get("clean_text", text))[:200],
            notes="Auto-generated ETS Teacher Practice Test missing audio"
        )
        
        # Update DB
        pc["audio_path"] = f"/audio/{section_dir}/{out_filename}"
        item.prompt_content = json.dumps(pc, ensure_ascii=False)
        flag_modified(item, "prompt_content")
        db.commit()
        time.sleep(10) # Follow the API rate limit rules
        
if __name__ == "__main__":
    main()

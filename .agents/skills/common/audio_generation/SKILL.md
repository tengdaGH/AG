---
name: common_audio_generation
description: Generating high-fidelity listening and speaking item audio using Gemini 2.5 Flash Preview TTS. Highly reusable across TOEFL and IELTS modules.
---

# Global Audio Generation Skill

> [!WARNING]
> **COST CONSTRAINT**: The Gemini API should be STRICTLY used for voice generation only. All other tasks (e.g., text/item generation, QA, or formatting) must utilize Antigravity built-in models to avoid cost incurrence.

This skill provides mandatory instructions for generating high-fidelity conversational audio for TOEFL listening and speaking test items using the experimental Gemini TTS models' native multi-speaker capabilities.

## 🛠 Prerequisites
- `GEMINI_API_KEY` set in the environment or `.env` file.
- The `google-genai` and `python-dotenv` packages installed in the backend virtual environment.

## 🎭 Voice Selection & Direction
When interpreting a conversational transcript, you must act as the **Voice Director**. Select voices based on the speaker's persona. Map each speaker name used in the text to one of the 30 prebuilt voices. Here are some recommended ones:

- **Puck**: Bright, youthful, inquisitive (Best for students, young adults asking questions).
- **Aoede**: Warm, professional, articulate (Best for professors, librarians, campus staff).
- **Charon**: Deep, authoritative, measured (Best for university administrators, older professors).
- **Kore**: Clear, friendly, analytical (Best for teaching assistants, conversational peers).
- **Fenrir**: Energetic, distinct, robust (Best for narrators or dynamic guest speakers).

## 🚀 Native Multi-Speaker Implementation

You *must* use the `gemini-2.5-flash-preview-tts` model via the `google-genai` SDK. Do not generate audio for each line individually or batch them into one block for manual slicing. Instead, use the native multi-speaker capability.

### 1. Format the Prompt
Provide the full dialogue script in a single prompt using the exact format: `SpeakerName: [Dialogue]`.
Use the wrapper: `"Generate audio from this precise transcript without adding or modifying anything:\n\n{text}"`

### 2. Configure Speakers
In the `speech_config`, define a `multi_speaker_voice_config`. Map each speaker name used in the text to one of the prebuilt voices.

### 3. Manage Rate Limits
Ensure the script is restricted to **max 10 RPM** to protect the API key from temporary lockouts, even though this reduces total requests. Include a delay of at least 6 seconds between requests, and implement exponential backoff on 429s.

### 4. Post-Processing
Save the single returned audio stream directly as a `.wav` file. No slicing or concatenation is required, which will fix the clipping issues.

### Python Code Pattern
```python
import os
import time
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def save_wav_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """Saves raw PCM audio data as a proper .wav file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

def generate_conversation_audio(dialogue_script, speaker_mapping, filename, max_retries=5):
    """
    Generates a full multi-speaker conversation in a single API call, 
    saving directly to a .wav file to avoid clipping issues.
    """
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"Skipping {filename}, already exists.")
        return

    # Ensure dialogue_script uses "SpeakerName: [Dialogue]" format
    prompt = f"Generate audio from this precise transcript without adding or modifying anything:\n\n{dialogue_script}"
    
    # Map speaker names in the transcript to prebuilt voice names
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
            # Extract out the audio bytes
            data = response.candidates[0].content.parts[0].inline_data.data
            
            # Save the single returned audio stream directly as a .wav file
            save_wav_file(filename, data)
            
            # Enforce max 10 RPM (6 seconds per request)
            time.sleep(6.1) 
            return # Success
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (2 ** attempt)  # 60s, 120s, 240s, 480s, 960s
                print(f"Rate limited. Sleeping for {wait}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise e

    # Fallback delay just in case
    time.sleep(6.1)
```

## 💾 Saving to Item Bank
Once the native multi-speaker `.wav` file is verified, move the file into the `public/audio` directory of the frontend and update the corresponding `TestItem` in the SQLite database to point its `audioUrl` field to the new file path. Ensure the file has a `.wav` extension.

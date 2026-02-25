---
name: toefl_voice_direction
description: |
  Voice acting direction skill for TOEFL iBT 2026 and IELTS listening audio generation.
  Provides complete guidance on voice selection (gender, age, accent), tone/emotion direction
  by task type, Gemini 2.5 Flash TTS prompt engineering, and post-generation audio logging.
  Use this skill every time you generate audio for a TOEFL or IELTS listening item.
---

# TOEFL / IELTS Voice Acting Direction Skill

This skill tells you **exactly** how to select voices, direct tone and emotion, write TTS prompts,
and log audio decisions for every listening item. Follow it precisely every time you generate audio.

---

## 1. When To Use This Skill

Activate this skill whenever you are about to:
- Generate audio for any TOEFL 2026 or IELTS listening item.
- Regenerate or replace existing audio for a listening item.
- Review or audit audio quality and need a reference for expected voice choices.

---

## 2. Gemini 2.5 Flash TTS — API Reference

The project canonical TTS engine is **`gemini-2.5-flash-preview-tts`** via the `google-genai` SDK.

### 2a. Single-Speaker (Announcements, Academic Talks, LCR stimulus)

```python
from google import genai
from google.genai import types
import os, wave

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_single_speaker(text: str, voice: str, tone_instruction: str, out_path: str):
    """
    text             — the raw transcript text (do NOT include speaker labels)
    voice            — one of the Gemini prebuilt voice names (see Section 4)
    tone_instruction — a short direction sentence (see Section 6)
    out_path         — absolute path to output .mp3 or .wav file
    """
    prompt = (
        f"{tone_instruction}\n\n"
        f"Generate audio from this precise transcript without adding or modifying anything:\n{text}"
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            )
        )
    )
    # Response is raw 16-bit PCM at 24000 Hz, 1 channel. Convert to .wav:
    pcm = response.candidates[0].content.parts[0].inline_data.data
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    # Or use ffmpeg to convert to MP3:
    # os.system(f"ffmpeg -y -f s16le -ar 24000 -ac 1 -i '{pcm_path}' '{mp3_path}' > /dev/null 2>&1")
```

### 2b. Multi-Speaker (Conversations)

```python
def generate_multi_speaker(script_lines: list[tuple[str, str]], speaker_voice_map: dict[str, str],
                           tone_instruction: str, out_path: str):
    """
    script_lines      — list of (speaker_name, dialogue_text) tuples in order
    speaker_voice_map — {"SpeakerName": "VoiceName", ...}  (max 2 voices per API call)
    tone_instruction  — overall direction sentence
    out_path          — absolute path to output .wav

    Format: each line as "SpeakerName: dialogue" — the API reads speaker labels.
    """
    formatted = "\n".join(f"{spk}: {txt}" for spk, txt in script_lines)
    prompt = (
        f"{tone_instruction}\n\n"
        f"Generate audio from this precise transcript without adding or modifying anything:\n\n{formatted}"
    )
    speaker_configs = [
        types.SpeakerVoiceConfig(
            speaker=name,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
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
                    speaker_voice_configs=speaker_configs
                )
            )
        )
    )
    pcm = response.candidates[0].content.parts[0].inline_data.data
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000)
        wf.writeframes(pcm)
```

> [!IMPORTANT]
> The multi-speaker API accepts a **maximum of 2 explicit `SpeakerVoiceConfig` entries** per request.
> For conversations with 3+ speakers, generate each speaker's lines separately, then concatenate with ffmpeg.

### 2c. Rate Limits & Retry Policy

| Situation | Action |
|---|---|
| `429 / RESOURCE_EXHAUSTED` | Exponential backoff: 60s → 120s → 240s → 480s (max 4 attempts) |
| `quota exceeded` (daily) | `sys.exit(1)` immediately — do not retry |
| `500 Internal` | Retry once after 30s |
| Between successful calls | Sleep **10 seconds** minimum (safe = ~6 RPM) |

---

## 3. Gender Detection from Script Names

Before selecting a voice, **always determine the character's gender**. Use this cascade:

### Step 1 — Explicit Speaker Labels
If the script uses gender labels like `(F)`, `(M)`, `F:`, or `M:` — use them directly.

### Step 2 — Name-Based Detection
Parse the first name from the speaker label or surrounding text (e.g., _"Professor Sarah Chen"_, _"Dr. James Okafor"_).

**Female first names (common in academic contexts):**
Sarah, Emily, Emma, Olivia, Sophia, Ava, Isabella, Mia, Abigail, Charlotte, Amanda, Jennifer, Jessica,
Laura, Rachel, Karen, Michelle, Lisa, Anna, Maria, Claire, Grace, Linda, Mei, Yuki, Priya, Aisha, Fatima,
Amara, Nguyen (F), Kim (F in Korean context), Chen (F if given name), Liu (F if given name)

**Male first names (common in academic contexts):**
James, John, David, Michael, Robert, William, Thomas, Daniel, Matthew, Andrew, Christopher, Joseph,
Kevin, Brian, Mark, Steven, Paul, Charles, George, Edward, Richard, Scott, Jason, Ryan, Tyler, Ethan,
Carlos, Ahmed, Mohammed, Wei, Zhang (M if given name), Park (M in Korean context), Patel (M if given name)

**Ambiguous / Neutral names:** Alex, Jordan, Taylor, Morgan, Casey, Sam, Robin, Riley, Charlie, Jamie
→ If ambiguous, check surrounding pronouns in the script text ("his", "her", "they").
→ If still ambiguous, default to **Female** for narrators/interviewers, **Male** for professors.

### Step 3 — Role-Based Default (no name available)
| Role | Default Gender |
|---|---|
| Professor | Male (TOEFL statistical default) |
| Campus Announcer | Female |
| ETS Test Instructions | Neutral → Male (Fenrir) |
| Interviewer | Female |
| Student (unnamed) | Alternate M/F per conversation turn |

---

## 4. Voice Catalog — Full Reference

Read `voice_profiles.json` in this skill directory for the machine-readable version.
Below is the human-readable quick reference:

### 4a. Male Voices

| Voice | Age | Accent | Tone | Primary Use |
|---|---|---|---|---|
| **Charon** | Senior (50+) | American | Deep, scholarly | Professor M (first choice) |
| **Orus** | Senior (50+) | American | Resonant, authoritative | Professor M (second choice) |
| **Rasalgethi** | Senior (50+) | American | Deep, clear | Elder professor, senior narrator |
| **Iapetus** | Mid-career (35–45) | American | Measured, academic | Associate professor, formal interviewer |
| **Algieba** | Mid-career (35–45) | American | Warm, measured | Secondary professor, narrator |
| **Fenrir** | Mid-career (30–40) | American | Clear, neutral | Narrator M, announcer, ETS instructions |
| **Enceladus** | Mid-career (30–40) | American | Solid, neutral | Secondary narrator, instruction voice |
| **Achernar** | Young-adult (22–30) | American | Confident, clear | Narrator M, energetic student |
| **Algenib** | Mid-career (30–40) | American | Smooth, professional | Campus announcer |
| **Puck** | Young-adult (20–27) | American | Bright, energetic | Student M (first choice) |
| **Achird** | Young-adult (20–27) | American | Casual, natural | Student M (second choice) |
| **Sadachbia** | Young-adult (20–27) | American | Bright, casual | Student M (third choice) |
| **Zephyr** | Young-adult (20–27) | American | Breezy, confident | Student M (fourth choice) |
| **Sadaltager** | Young-adult (20–27) | Neutral-Intl | Neutral, energetic | International student M, IELTS candidate |
| **Schedar** | Mid-career (30–40) | Neutral-Intl | Measured, neutral | Secondary narrator |
| **Alnilam** | Mid-career (35–45) | British | Crisp, authoritative | IELTS examiner M, British professor |
| **Umbriel** | Mid-career (35–45) | British | Measured, serious | IELTS examiner M, formal academic |

### 4b. Female Voices

| Voice | Age | Accent | Tone | Primary Use |
|---|---|---|---|---|
| **Callirrhoe** | Mid-career (38–48) | American | Warm, authoritative | Professor F (first choice) |
| **Aoede** | Mid-career (32–42) | American | Warm, professional | Professor F (second choice), narrator F |
| **Autonoe** | Mid-career (30–40) | American | Neutral, warm | Narrator F, campus announcer |
| **Sulafat** | Young-adult (22–30) | American | Warm, casual | Campus announcer F, student F |
| **Kore** | Young-adult (20–27) | American | Clear, friendly | Student F (first choice) |
| **Leda** | Young-adult (22–28) | American | Bright, clear | Student F (second choice), graduate student |
| **Despina** | Young-adult (20–27) | American | Casual, friendly | Student F (third choice) |
| **Erinome** | Young-adult (20–27) | Neutral-Intl | Soft, clear | International student F, IELTS candidate |
| **Pulcherrima** | Mid-career (35–45) | Neutral-Intl | Elegant, clear | IELTS examiner F, international narrator |
| **Laomedeia** | Mid-career (38–48) | British | Crisp, professional | IELTS examiner F (first choice), British professor |

---

## 5. Role → Voice Decision Tree

Follow this decision tree for every new character you encounter in a script.

```
1. What is the character's ROLE?
   │
   ├─ PROFESSOR / ACADEMIC LECTURER
   │    ├─ Gender = Male  → Age = Senior → Charon (first), Orus (second), Rasalgethi (third)
   │    ├─ Gender = Female → Age = Mid-career → Callirrhoe (first), Aoede (second)
   │    └─ Accent override for IELTS: M → Alnilam | F → Laomedeia
   │
   ├─ UNIVERSITY STUDENT / GRAD STUDENT
   │    ├─ Gender = Male, undergrad → Puck (first), Achird, Sadachbia, Zephyr
   │    ├─ Gender = Female, undergrad → Kore (first), Leda, Despina, Sulafat
   │    └─ International / IELTS → Sadaltager (M), Erinome (F)
   │
   ├─ CAMPUS ANNOUNCER / NARRATOR
   │    ├─ Gender = Male → Fenrir (first), Achernar, Algenib, Enceladus
   │    └─ Gender = Female → Aoede (first), Autonoe, Sulafat
   │
   ├─ ETS TEST INSTRUCTION VOICE (no gender specified)
   │    └─ Use Fenrir (M) for primary; Aoede (F) as alternate
   │
   ├─ INTERVIEWER (formal, e.g., TAKE_AN_INTERVIEW)
   │    ├─ Gender = Male → Iapetus (first), Charon
   │    └─ Gender = Female → Laomedeia (first), Callirrhoe
   │
   └─ LISTEN_AND_REPEAT (pedagogical, single speaker)
        └─ Use Fenrir (M) or Aoede (F) — their clear articulation aids comprehension
```

### Accent Override Rules
| Test | Target Accent | Preferred Voices |
|---|---|---|
| TOEFL iBT | American English | Any voice without "British" tag |
| IELTS | British English | Laomedeia (F), Alnilam (M), Umbriel (M) |
| Neutral / International | Neutral | Erinome (F), Sadaltager (M), Schedar (M), Pulcherrima (F) |

---

## 6. Tone & Emotion Direction by Task Type

Prepend the following direction string to ***every*** TTS prompt you write (before the transcript text).

| Task Type | Tone Direction String |
|---|---|
| `LISTEN_ACADEMIC_TALK` | `Deliver in a measured, authoritative academic lecture tone. Speak clearly with natural academic pacing — not rushed. Slight gravitas; this is an educator addressing students.` |
| `LISTEN_ANNOUNCEMENT` | `Friendly, clear campus broadcast voice. Upbeat but professional, like a university radio announcer. Moderate pace, warm energy.` |
| `LISTEN_CONVERSATION` | `Natural, conversational tone. Each speaker should sound like a real person talking, not reading. Match the emotion implied by the dialogue.` |
| `LISTEN_CHOOSE_RESPONSE` | `Neutral, natural conversational stimulus. Short, clear, single utterance. Sound like an ordinary person in a casual exchange.` |
| `LISTEN_AND_REPEAT` | `Clear, pedagogical delivery. Speak each word cleanly and at a slightly measured pace — this audio is used for language learning repetition practice.` |
| `TAKE_AN_INTERVIEW` — Narrator | `Neutral, clear narration. This is a scene-setting voice. Professional, unhurried.` |
| `TAKE_AN_INTERVIEW` — Interviewer | `Professional, warm, and genuinely curious. Conversational but polished, like a TV journalist.` |

---

## 7. TTS Prompt Engineering

### 7a. Full Prompt Structure

```
{TONE_DIRECTION_STRING}

Generate audio from this precise transcript without adding or modifying anything:

{RAW_TRANSCRIPT_TEXT}
```

- **Never** title the transcript, add speaker names to single-speaker prompts, or modify the text.
- For multi-speaker, format each line as `SpeakerLabel: dialogue` (e.g., `Professor: Good morning everyone.`).

### 7b. Inline Delivery Cues (use sparingly)

You can embed natural-language cues directly in the transcript text to guide delivery:
- Emphasis: Use **standard punctuation** — exclamation marks, ellipsis, em-dashes are respected.
- Pause: Insert a literal pause cue in parentheses: `(pause)` — e.g., `"The answer is... (pause) fascinating."`
- Slower: Prefix a sentence: `[speak slowly] Repeat after me: the library is open until midnight.`
- Emphasis on word: `The *key* finding was the temperature increase.` (italics signal stress)

> [!TIP]
> The best results come from **well-punctuated, naturally written text**. Gemini respects commas, periods,
> and ellipsis for pacing. Add cues only when the default delivery is clearly wrong.

### 7c. Common Pitfalls to Avoid

| Mistake | Fix |
|---|---|
| Prompt says "Generate audio for this text:" | Use exact phrasing: "…without adding or modifying anything:" |
| Using Professor voice (Charon) for a student | Always check the decision tree — age mismatch sounds wrong |
| Sending multi-speaker script to single-speaker endpoint | Check: does the transcript have 2+ named speakers? → Use multi-speaker config |
| Not converting PCM → MP3 | Gemini returns raw PCM; always convert with ffmpeg or the `wave` module |

---

## 8. Post-Generation: Audio Voice Log Protocol

After **every** successful audio generation, you **MUST** write one entry to the project's voice log.

The log utility is at `.agent/skills/toefl_voice_direction/log_audio.py` (this skill directory).
The log file is written to `{project_root}/audio/audio_voice_log.jsonl` by default.

> [!NOTE]
> Set the `VOICE_LOG_DIR` environment variable to override where the log is written,
> or call `set_log_path()` before appending entries.

### 8a. Log Entry Schema

```jsonc
{
  "timestamp": "2026-02-25T16:00:00+08:00",   // ISO-8601, local time
  "item_id": "abc123",                          // DB item ID or descriptive slug
  "task_type": "LISTEN_ACADEMIC_TALK",           // TOEFL task type enum value
  "audio_file": "audio/listening/LT-abc1234.wav", // relative path from project root
  "engine": "gemini-2.5-flash-preview-tts",
  "mode": "single",                              // "single" or "multi"
  "speakers": [                                  // one entry per voice used
    {
      "role": "Professor",
      "name": "Dr. Ellen Park",                  // actual character name, if any
      "gender": "F",
      "age_range": "mid-career",
      "accent": "american",
      "voice": "Callirrhoe",
      "tone_instruction": "Measured, authoritative academic lecture tone."
    }
  ],
  "tts_prompt_preview": "Deliver in a measured...\n[first 200 chars of transcript]",
  "duration_seconds": null,                      // fill in if you can measure it
  "verified": false,                             // set to true after human review
  "notes": ""                                    // any anomalies or special handling
}
```

### 8b. How to Write the Log Entry

Use the utility in this skill directory:

```bash
cd /path/to/your-project
python /Users/tengda/Antigravity/.agent/skills/toefl_voice_direction/log_audio.py \
  --item_id "abc123" \
  --task_type "LISTEN_ACADEMIC_TALK" \
  --audio_file "audio/listening/LT-abc1234.wav" \
  --voice "Callirrhoe" \
  --gender "F" \
  --age_range "mid-career" \
  --accent "american" \
  --role "Professor" \
  --character_name "Dr. Ellen Park" \
  --tone "Measured, authoritative academic lecture tone." \
  --prompt_preview "Deliver in a measured...\nGood morning, everyone..."
```

Or import it in your script:

```python
import sys
sys.path.append("/Users/tengda/Antigravity/.agent/skills/toefl_voice_direction")
from log_audio import append_voice_log, set_log_path

# Point to the project's audio log
set_log_path("/path/to/project/audio/audio_voice_log.jsonl")

append_voice_log(
    item_id="abc123",
    task_type="LISTEN_ACADEMIC_TALK",
    audio_file="audio/listening/LT-abc1234.wav",
    engine="gemini-2.5-flash-preview-tts",
    mode="single",
    speakers=[{
        "role": "Professor",
        "name": "Dr. Ellen Park",
        "gender": "F",
        "age_range": "mid-career",
        "accent": "american",
        "voice": "Callirrhoe",
        "tone_instruction": "Measured, authoritative academic lecture tone."
    }],
    tts_prompt_preview="Deliver in a measured...\nGood morning, everyone...",
    notes=""
)
```

### 8c. Reviewing the Log

To review past generations or debug a problematic audio file:

```bash
# Show all entries for a particular item_id
grep '"item_id": "abc123"' audio/audio_voice_log.jsonl | python -m json.tool

# Show all unverified entries
grep '"verified": false' audio/audio_voice_log.jsonl

# Show all voices used per task type
grep '"task_type"' audio/audio_voice_log.jsonl | sort | uniq -c | sort -rn
```

---

## 9. Quick-Start Checklist

When starting a new audio generation run, go through this checklist:

- [ ] **Identify task type** → determines single vs multi-speaker mode and tone direction.
- [ ] **Read the script** → identify all speaker roles and character names.
- [ ] **Detect gender** for each character (Step 3 cascade above).
- [ ] **Pick voices** using the Role → Voice Decision Tree (Section 5).
- [ ] **Apply accent override** if the project is IELTS (British) or international.
- [ ] **Write TTS prompt** with the correct tone direction prefix (Section 6).
- [ ] **Generate audio** using the correct API config (single or multi-speaker, Section 2).
- [ ] **Convert PCM → WAV/MP3** and save to the project's audio directory.
- [ ] **Update the database** with the new `audio_url`.
- [ ] **Append a log entry** to `audio/audio_voice_log.jsonl` using `log_audio.py`.

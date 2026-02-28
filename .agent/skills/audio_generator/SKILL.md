---
name: audio_generator
description: >
  Batch-generates TTS audio for new Listening and Speaking items using the toefl_voice_direction
  skill. Uploads audio to cloud storage (or serves from backend/static/audio/), then logs
  the audio_url back to item_bank.db. Use whenever new Listening items are added and
  audio_url is null. Supervised by Alfred.
---

# audio_generator — TTS Audio Pipeline Agent

The audio_generator removes the last major manual bottleneck in item creation:
generating and linking audio files for Listening and Speaking items.

---

## audio_generator's Mandate

> "No Listening item goes ACTIVE without an audio file. No exceptions."

Alfred enforces this: `ACTIVE Listening items with null audio_url = RED flag`.
audio_generator is the automated fix for that red flag.

---

## When to Run

- After any batch of new Listening items is inserted by `item_writer`
- After Alfred reports: "X Listening items missing audio_url"
- After any `toefl_voice_direction` voice spec change (to regenerate mismatched audio)

---

## Prerequisite: Read toefl_voice_direction

**MANDATORY**: Before generating any audio, read the full voice direction skill:
```
.agent/skills/toefl_voice_direction/SKILL.md
```

This skill contains:
- Voice selection rules by task type (gender, accent, age)
- Tone/emotion direction per item type
- Gemini 2.5 Flash TTS prompt engineering
- Post-generation audio logging requirements

---

## Generation Protocol

### Step 1 — Find items needing audio

```bash
cd /Users/tengda/Documents/Antigravity/toefl-2026
source backend/venv/bin/activate
python3 - <<'EOF'
import sqlite3
conn = sqlite3.connect("backend/item_bank.db")
rows = conn.execute("""
    SELECT id, task_type, title, prompt_content
    FROM test_items
    WHERE section='LISTENING'
      AND lifecycle_status IN ('ACTIVE', 'DRAFT')
      AND (audio_url IS NULL OR audio_url = '')
    ORDER BY lifecycle_status DESC, id ASC
    LIMIT 20
""").fetchall()
for r in rows:
    print(f"  ID={r[0]} | {r[1]} | {r[2][:60]}")
conn.close()
print(f"\nTotal: {len(rows)} items need audio")
EOF
```

---

### Step 2 — Generate audio with Gemini TTS

Per the `toefl_voice_direction` skill, construct the TTS prompt:

```python
# Example prompt structure (customize per task type):
tts_prompt = f"""
[VOICE: {voice_spec}]
[TONE: {tone_spec}]
[SPEED: natural academic pace, ~130 WPM]

{item_text}
"""
```

Voice selection by `task_type`:
| task_type | Voice | Accent | Age |
|-----------|-------|--------|-----|
| `LISTEN_CHOOSE_RESPONSE` | Male or Female (alternate) | North American | 25–40 |
| `LISTEN_CONVERSATION` | 2 voices: M + F | Mix accents | 20–35 |
| `LISTEN_ANNOUNCEMENT` | Female | UK or Australian | 30–45 |
| `LISTEN_ACADEMIC_TALK` | Male | North American | 35–55 |
| `LISTEN_REPEAT` (Speaking) | Male or Female | North American | 25–40 |

---

### Step 3 — Save audio file

Save generated audio to:
```
backend/static/audio/<task_type>/<item_id>_v1.mp3
```

Create the directory if it does not exist:
```bash
mkdir -p /Users/tengda/Documents/Antigravity/toefl-2026/backend/static/audio/<task_type>/
```

---

### Step 4 — Update audio_url in item_bank.db

The audio URL served to the frontend follows this pattern:
```
http://101.32.187.39:8000/static/audio/<task_type>/<item_id>_v1.mp3
```

Update the database:
```python
import sqlite3
conn = sqlite3.connect("backend/item_bank.db")
conn.execute("""
    UPDATE test_items
    SET audio_url = ?
    WHERE id = ?
""", (audio_url, item_id))
conn.commit()
conn.close()
print(f"✅ Updated audio_url for item {item_id}")
```

---

### Step 5 — Log the generation

Per the `toefl_voice_direction` skill, log every generated file to:
```
logs/audio_generation_log.csv
```

Format: `timestamp, item_id, task_type, title, voice_spec, audio_url, duration_seconds`

---

### Step 6 — Verify

After batch generation, run Alfred's item bank check:
```bash
python3 agents/scripts/alfred_daily_review.py 2>&1 | grep -A3 "Audio"
```

Alfred should report: `✅ all ACTIVE Listening items have audio URLs`

---

## Minimax VPN Note

If using Minimax API for TTS (alternative to Gemini):
**MANDATORY**: Read `.agent/skills/minimax_vpn_workaround/SKILL.md` first.
The TUN-mode proxy causes silent hangs. The skill has the fix.

---

## Files audio_generator Reads

1. `.agent/skills/toefl_voice_direction/SKILL.md` — voice specs (MANDATORY)
2. `.agent/skills/minimax_vpn_workaround/SKILL.md` — if using Minimax TTS
3. `backend/static/audio/` — existing audio files (avoid duplicates)
4. `logs/audio_generation_log.csv` — audit trail

---

## Relationship to Other Agents

- **Alfred** supervises audio_generator — he flags null audio_urls as red
- **item_writer** creates items that audio_generator then voices
- **toefl_voice_direction** provides all voice direction rules

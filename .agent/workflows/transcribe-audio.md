---
description: Transcribe audio files locally using the Whisper CLI (no API needed)
---

# Local Audio Transcription with Whisper CLI

The system has OpenAI's `whisper` CLI installed at `/opt/homebrew/bin/whisper` via the `openai-whisper` Python package. All transcription runs **locally on the Mac** — no network calls, no API keys needed.

> [!IMPORTANT]
> **MacWhisper (GUI app) and the `whisper` CLI use separate model stores.** MacWhisper uses CoreML/WhisperKit models; the CLI uses PyTorch `.pt` models stored in `~/.cache/whisper/`. They cannot share models. Do NOT assume MacWhisper's downloaded models are available to the CLI.

## Currently Cached CLI Models

Only use models that are already cached to avoid long downloads. Check with:
```bash
ls -lh ~/.cache/whisper/
```

**As of Feb 2026:** `small.pt` (147 MB) is cached. Use `--model small` by default.

## Basic Usage

```bash
whisper /path/to/audio.mp3 --model small --language en --output_format txt
```

// turbo-all

## Available Options

| Option             | Values                                          | Default  | Notes                                        |
|--------------------|------------------------------------------------|----------|----------------------------------------------|
| `--model`          | `tiny`, `base`, `small`, `medium`, `large`     | `small`  | **Use `small` unless user requests otherwise** |
| `--language`       | `en`, `zh`, `ja`, etc.                         | auto     | Specify to skip language detection           |
| `--output_format`  | `txt`, `srt`, `vtt`, `json`, `tsv`, `all`      | `all`    | Use `txt` for plain text, `srt` for subtitles |
| `--output_dir`     | any directory path                              | `.`      | Where to write output files                  |
| `--task`           | `transcribe`, `translate`                       | `transcribe` | `translate` converts non-English to English |
| `--word_timestamps`| flag                                            | off      | Adds per-word timing (use with `json` output)|

## Examples

### 1. Simple transcription to text file
```bash
whisper /path/to/audio.mp3 --model small --language en --output_format txt --output_dir /tmp
```

### 2. Generate subtitles (SRT)
```bash
whisper /path/to/lecture.mp3 --model small --language en --output_format srt --output_dir /tmp
```

### 3. Batch transcribe multiple files
```bash
whisper /path/to/dir/*.mp3 --model small --language en --output_format txt --output_dir /tmp/transcripts
```

### 4. Translate non-English audio to English
```bash
whisper /path/to/chinese_audio.mp3 --model small --task translate --output_format txt
```

### 5. Get word-level timestamps (JSON output)
```bash
whisper /path/to/audio.mp3 --model small --language en --output_format json --word_timestamps True
```

## Model Size Guide

| Model    | Parameters | Download Size | Cached? | Best For                        |
|----------|-----------|---------------|---------|----------------------------------|
| `tiny`   | 39M       | ~75 MB        | ❌      | Quick drafts, short clips       |
| `base`   | 74M       | ~142 MB       | ❌      | Fast with decent accuracy       |
| `small`  | 244M      | ~461 MB       | ✅      | Good balance **(use this)**     |
| `medium` | 769M      | ~1.5 GB       | ❌      | High accuracy, slow download    |
| `large`  | 1550M     | ~2.9 GB       | ❌      | Best accuracy, very slow        |

## Reading the Output

- Output files are named after the input file (e.g., `audio.txt`, `audio.srt`)
- Use `cat /tmp/audio.txt` to read the plain text transcript
- The `json` format includes timestamps per segment and optionally per word

## ⚠️ VPN Download Speed Issue

The system has a TUN-mode VPN proxy active. Python's `urllib` (used by whisper internally) gets routed through it and throttled to ~20 KiB/s, even though the actual internet connection is much faster. **This makes downloading new models via `whisper` itself painfully slow (~3+ hours for 461 MB).**

### Workaround: Pre-download with curl

`curl` bypasses the VPN more efficiently (~1.5 MB/s). If you need a model that isn't cached, download it directly:

```bash
# Model URLs (openaipublic.azureedge.net/main/whisper/models/<hash>/<size>.pt)
# tiny:   https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt
# base:   https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt
# small:  https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt
# medium: https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt
# large:  https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt

# Example: download medium model with curl
curl -L -o ~/.cache/whisper/medium.pt "https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt"
```

After downloading, verify with `ls -lh ~/.cache/whisper/` — whisper CLI will find and use the cached file automatically.

## Tips

- **Always check `~/.cache/whisper/`** before choosing a model. Only use cached models unless the user explicitly asks for a larger one.
- If a model is not cached, **warn the user** and use the `curl` workaround above instead of letting whisper download it (due to VPN throttling).
- For **long audio files** (>30 min), `small` model works well on Apple Silicon.
- If transcription quality is poor, try explicitly setting `--language` before upgrading model size.
- Output goes to the **current working directory** by default — use `--output_dir` to control this.

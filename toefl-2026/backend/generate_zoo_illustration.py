# ============================================================
# Purpose:       Generate a cartoon zoo illustration for TOEFL Figure 11 using Gemini Imagen API.
# Usage:         python backend/generate_zoo_illustration.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
#!/usr/bin/env python3
"""Generate a cartoon-style zoo illustration matching TOEFL Figure 11 using Gemini Imagen."""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

prompt = (
    "A simple cartoon illustration of a zoo scene from a slightly elevated angle. "
    "The scene shows: a giraffe and people behind a curved fence on the left, "
    "elephants with a keeper in a lower-left enclosure, "
    "a lion highlighted with a teal/turquoise circle on the right side with excited visitors nearby, "
    "a teal arrow pointing from the elephants toward the lion, "
    "a small gift shop building at the bottom center, "
    "a 'no food or drinks' prohibition sign, "
    "and a decorative stone bridge/archway at the very bottom. "
    "Muted grey and green color palette with teal/turquoise accents. "
    "Soft cloudy sky background. "
    "Clean, flat, educational textbook illustration style. No text or labels."
)

url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-ultra-generate-001:predict?key={API_KEY}"

payload = {
    "instances": [{"prompt": prompt}],
    "parameters": {
        "sampleCount": 1,
        "aspectRatio": "1:1",
        "outputOptions": {"mimeType": "image/jpeg"}
    }
}

print("Generating cartoon zoo illustration...")
response = requests.post(url, json=payload, timeout=120)

if response.status_code == 200:
    data = response.json()
    predictions = data.get("predictions", [])
    if predictions:
        img_data = base64.b64decode(predictions[0]["bytesBase64Encoded"])
        out_path = os.path.join(OUTPUT_DIR, "listen_repeat_zoo_sample.jpg")
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"✅ Saved: {out_path} ({len(img_data)} bytes)")
    else:
        print("❌ No predictions returned")
        print(data)
else:
    print(f"❌ Error {response.status_code}: {response.text}")

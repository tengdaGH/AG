# ============================================================
# Purpose:       Smoke test for Gemini Vision API: extract text from a sample WAD image to compare with OCR.
# Usage:         python backend/scripts/wad_ingestion/test_vision.py
# Created:       2026-02-25
# Self-Destruct: Yes — one-time verification script.
# ============================================================
import os
import sys
import json
from PIL import Image
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

img_path = "../Writing for academic discussions/Automation/Automation.png"
if not os.path.exists(img_path):
    print("Image not found:", img_path)
    sys.exit(1)

try:
    img = Image.open(img_path)
except Exception as e:
    print(f"Error opening image: {e}")
    sys.exit(1)

print("Calling Gemini 1.5 Pro with vision...")

try:
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[
            "Extract all the text you can see in this image verbatim. Do not summarize.",
            img
        ],
        config=types.GenerateContentConfig(
            temperature=0.0
        )
    )
    print("Response Text:")
    print(response.text)
except Exception as e:
    print("Error:", e)

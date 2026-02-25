# ============================================================
# Purpose:       Smoke test for Tesseract OCR: verify installation and extract text from a sample WAD image.
# Usage:         python backend/scripts/wad_ingestion/test_tesseract.py
# Created:       2026-02-25
# Self-Destruct: Yes — one-time verification script.
# ============================================================
import os
import sys
import pytesseract
from PIL import Image

# Use the explicitly found tesseract path just in case
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

img_path = "../Writing for academic discussions/Automation/Automation.png"
if not os.path.exists(img_path):
    print("Image not found at:", img_path)
    sys.exit(1)

print("Running Tesseract OCR on:", img_path)
try:
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img)
    print("--- Extracted Text ---")
    print(text)
    print("----------------------")
except Exception as e:
    print("Error during OCR:", e)

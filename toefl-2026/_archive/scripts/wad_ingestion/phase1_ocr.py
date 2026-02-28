# ============================================================
# Purpose:       Phase 1: Local OCR extraction from WAD screenshot images using Tesseract with incremental caching.
# Usage:         python backend/scripts/wad_ingestion/phase1_ocr.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

def run_ocr_phase1():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Writing for academic discussions"))
    
    if not os.path.isdir(base_dir):
        print(f"Directory not found: {base_dir}")
        sys.exit(1)

    print("Phase 1: Starting Local OCR Extraction (Incremental)...")

    cache_path = os.path.join(os.path.dirname(__file__), "raw_extraction_cache.json")
    
    # Load existing cache
    extracted_data = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            try:
                extracted_data = json.load(f)
                print(f"Resuming from {len(extracted_data)} existing items.")
            except:
                print("Cache file is corrupted, starting fresh.")

    count = 0
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f)) and f != "新建文件夹"]
    
    for item_folder in folders:
        if item_folder in extracted_data:
            continue
            
        folder_path = os.path.join(base_dir, item_folder)
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            continue
            
        # Priority on .png, else largest file
        image_path = os.path.join(folder_path, image_files[0])
        
        try:
            img = Image.open(image_path)
            # Add a timeout so it doesn't hang forever on weird images
            text = pytesseract.image_to_string(img, timeout=20)
            extracted_data[item_folder] = {
                "folder_name": item_folder,
                "image_file": image_files[0],
                "raw_ocr_text": text
            }
            count += 1
            print(f"  ✓ Processed: {item_folder[:30]}...")
        except RuntimeError as e:
            # specifically for timeout
            print(f"  ✗ Timeout on {item_folder}")
            extracted_data[item_folder] = {
                "folder_name": item_folder,
                "image_file": image_files[0],
                "raw_ocr_text": "[ERROR: OCR TIMEOUT]"
            }
        except Exception as e:
            print(f"  ✗ Failed on {item_folder}: {e}")
            extracted_data[item_folder] = {
                "folder_name": item_folder,
                "image_file": image_files[0],
                "raw_ocr_text": f"[ERROR: {e}]"
            }
            
        # Incremental save
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
    print(f"\nDone! Total items in cache: {len(extracted_data)}")

if __name__ == "__main__":
    run_ocr_phase1()

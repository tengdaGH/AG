# ============================================================
# Purpose:       Phase 2: Parse raw OCR text into structured JSON using Gemini LLM (multi-threaded).
# Usage:         python backend/scripts/wad_ingestion/phase2_parse.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# LLM prompt schema
SYSTEM_PROMPT = """You are an expert data extraction assistant. I will provide raw OCR text extracted from a TOEFL 'Writing for Academic Discussion' task image.
Your job is to parse this noisy text into a strict JSON object with the following schema:
{
  "topic": "The general topic or subject being discussed (e.g. Environmental Tax, Automation, etc.)",
  "professor_prompt": "The FULL text of the professor's prompt and question, without any of the UI elements like 'Hide Time'.",
  "student_1_name": "Name of the first student (e.g. Paul)",
  "student_1_response": "The full text of the first student's response.",
  "student_2_name": "Name of the second student (e.g. Kelly)",
  "student_2_response": "The full text of the second student's response."
}

Rules:
1. Fix any obvious OCR typos (e.g. 'I' instead of '|').
2. Remove any UI artifacts like 'Hide Time', 'Wordcount', button texts, timestamp '00:09:51', or symbols like '@'.
3. Output ONLY the raw JSON object. Do not include markdown formatting like ```json ... ```. No commentary.
"""

def parse_item(raw_text):
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[f"RAW OCR TEXT:\n{raw_text}"],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )
        content = response.text
                
        # Clean potential markdown if model disobeyed
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"  [LLM Error]: {e}")
        return None

def process_worker(folder_name, data):
    raw_text = data.get("raw_ocr_text", "")
    if "ERROR" in raw_text or len(raw_text) < 50:
        return folder_name, {
            "folder_name": folder_name,
            "error": "OCR failed or empty content"
        }, False
    
    print(f"Parsing [Thread]: {folder_name[:30]}...")
    structured_data = parse_item(raw_text)
    
    if structured_data:
        structured_data["folder_name"] = folder_name
        structured_data["original_image_file"] = data.get("image_file")
        return folder_name, structured_data, True
    else:
        return folder_name, {
            "folder_name": folder_name,
            "error": "LLM Parsing Failed"
        }, False

def run_phase_2():
    print("Phase 2: Starting LLM Data Parsing & Structuring (Multi-threaded)...")
    base_dir = os.path.dirname(__file__)
    cache_path = os.path.join(base_dir, "raw_extraction_cache.json")
    out_path = os.path.join(base_dir, "parsed_items.json")
    
    if not os.path.exists(cache_path):
        print("raw_extraction_cache.json not found. Run Phase 1 first.")
        sys.exit(1)
        
    with open(cache_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)
        
    parsed_items = {}
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            try:
                parsed_items = json.load(f)
                print(f"Resuming from {len(parsed_items)} already parsed items.")
            except:
                print("parsed_items.json is corrupted, starting fresh.")
                
    tasks_to_run = []
    for folder_name, data in raw_items.items():
        if folder_name not in parsed_items:
            tasks_to_run.append((folder_name, data))
            
    print(f"Items remaining: {len(tasks_to_run)}")
    count = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_worker, f_name, dat): f_name for f_name, dat in tasks_to_run}
        
        for future in as_completed(futures):
            folder_name = futures[future]
            try:
                name, result_data, success = future.result()
                parsed_items[name] = result_data
                if success:
                    count += 1
                    print(f"  ✓ Success: {result_data.get('topic', 'Unknown Topic')} ({name[:20]}...)")
                else:
                    print(f"  ✗ Failed: {name[:20]}...")
            except Exception as e:
                print(f"  ✗ Exception on {folder_name}: {e}")
                parsed_items[folder_name] = {"folder_name": folder_name, "error": str(e)}
                
            # Incremental save
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(parsed_items, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 2 Complete! Total newly parsed successfully: {count}, overall: {len(parsed_items)}")

if __name__ == "__main__":
    run_phase_2()

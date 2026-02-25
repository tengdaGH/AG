# ============================================================
# Purpose:       Phase 5: Remediate flagged items by re-OCR'ing all images + LLM-assisted reconstruction (multi-threaded).
# Usage:         python backend/scripts/wad_ingestion/phase5_remediate.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
import pytesseract
from PIL import Image
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor, as_completed

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

SYSTEM_PROMPT = """You are an expert data extraction assistant. I will provide raw OCR text extracted from MULTIPLE overlapping screenshots of a TOEFL 'Writing for Academic Discussion' task.
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
1. The OCR text comes from multiple images that might overlap. Merge the content intelligently to get the full professor prompt and BOTH student responses.
2. If the text genuinely does not contain a professor's prompt or one of the students' responses, you MUST infer and generate a highly realistic, TOEFL-compliant replacement for the missing piece based on the context of the other pieces.
   - Example 1: If Student 2's response is missing, generate a ~50-word response from Student 2 that takes a DISTINCT/OPPOSING position to Student 1.
   - Example 2: If the professor's prompt is missing, generate a ~100-word professor introduction that clearly frames the topic and ends with a question.
3. Output ONLY the raw JSON object. Do not include markdown formatting like ```json ... ```. No commentary.
"""

def process_flagged_item(folder_name, base_dir):
    folder_path = os.path.join(base_dir, folder_name)
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files.sort()
    
    combined_raw_text = ""
    for img_file in image_files:
        try:
            img_path = os.path.join(folder_path, img_file)
            img = Image.open(img_path)
            text = pytesseract.image_to_string(img, timeout=20)
            combined_raw_text += f"\n--- IMAGE: {img_file} ---\n{text}\n"
        except Exception as e:
            pass # ignore timeouts for partial images
            
    if not combined_raw_text.strip() or len(combined_raw_text) < 50:
        return folder_name, None, False
        
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[f"RAW OVERLAPPING OCR TEXT:\n{combined_raw_text}"],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )
        content = response.text
                
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return folder_name, json.loads(content.strip()), True
    except Exception as e:
        return folder_name, {"error": str(e)}, False

def run_phase_5_threaded():
    print("Phase 5: Remediating Flagged Items (Multi-threaded)...")
    base_dir = os.path.dirname(__file__)
    flagged_path = os.path.join(base_dir, "flagged_for_review.json")
    remediated_path = os.path.join(base_dir, "remediated_items.json")
    images_dir = os.path.abspath(os.path.join(base_dir, "../../../Writing for academic discussions"))
    
    if not os.path.exists(flagged_path):
        print("flagged_for_review.json not found.")
        sys.exit(1)
        
    with open(flagged_path, "r", encoding="utf-8") as f:
        flagged_items = json.load(f)
        
    remediated_items = {}
    if os.path.exists(remediated_path):
        with open(remediated_path, "r", encoding="utf-8") as f:
            try:
                remediated_items = json.load(f)
            except:
                pass
                
    tasks_to_run = []
    for folder_name in flagged_items.keys():
        if folder_name not in remediated_items:
            tasks_to_run.append(folder_name)
            
    print(f"Items to remediate: {len(tasks_to_run)}")
    count = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_flagged_item, f_name, images_dir): f_name for f_name in tasks_to_run}
        
        for future in as_completed(futures):
            folder_name = futures[future]
            try:
                name, data, success = future.result()
                if success:
                    data["folder_name"] = name
                    data["original_image_file"] = "MULTIPLE_IMAGES"
                    data["remediation_logs"] = "Aggregated across multiple images. LLM filled in missing components."
                    remediated_items[name] = data
                    count += 1
                    print(f"  ✓ Reconstructed: {data.get('topic', 'Unknown Topic')} ({name[:20]}...)")
                else:
                    remediated_items[name] = {"error": "Failed in Phase 5 threading", "details": data}
                    print(f"  ✗ Failed: {name[:20]}...")
            except Exception as e:
                print(f"  ✗ Exception on {folder_name}: {e}")
                
            with open(remediated_path, "w", encoding="utf-8") as f:
                json.dump(remediated_items, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 5 Complete! Remediated {count} items.")

if __name__ == "__main__":
    run_phase_5_threaded()

# ============================================================
# Purpose:       Phase 3: LLM-based compliance and QA validation of parsed WAD items against RR-25-12 spec.
# Usage:         python backend/scripts/wad_ingestion/phase3_validate.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# Load RR-25-12 spec snippet
spec_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../rr_25_12_extracted.txt"))
with open(spec_path, "r", encoding="utf-8", errors="ignore") as f:
    manual_text = f.read()[:15000]

SYSTEM_PROMPT = f"""You are an ETS TOEFL Assessment Quality Assurance Evaluator. I will provide a parsed 'Writing for Academic Discussion' task.
Evaluate if this task strictly meets the requirements outlined in the TOEFL 2026 RR-25-12 specs.

CRITERIA:
1. Does the professor briefly frame the topic and pose a clear opinion question for discussion?
2. Do the two students provide different/distinct positions or perspectives on the issue?
3. Are there any severe OCR hallucinations or garbled text that makes the prompt unusable?

Output your evaluation as a strict JSON object:
{{
  "is_valid": true or false,
  "reason": "If false, briefly explain why. If true, write 'Pass'."
}}

Output ONLY the raw JSON object. Do not include markdown formatting like ```json ... ```.
"""

def evaluate_item(parsed_data):
    try:
        # Construct the item string to evaluate
        item_text = f"Topic: {parsed_data.get('topic')}\n"
        item_text += f"Professor: {parsed_data.get('professor_prompt')}\n"
        item_text += f"Student 1 ({parsed_data.get('student_1_name')}): {parsed_data.get('student_1_response')}\n"
        item_text += f"Student 2 ({parsed_data.get('student_2_name')}): {parsed_data.get('student_2_response')}\n"

        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[f"EVALUATE THIS ITEM:\n\n{item_text}"],
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
            
        res = json.loads(content.strip())
        return res.get("is_valid", False), res.get("reason", "Unknown reason")
    except Exception as e:
        return False, f"LLM QA Error: {e}"

def process_worker(folder_name, data):
    if "error" in data:
        return folder_name, data, False, "Previously failed parsing"
        
    is_valid, reason = evaluate_item(data)
    data["qa_reason"] = reason
    return folder_name, data, is_valid, reason

def run_phase_3():
    print("Phase 3: LLM Compliance & Quality Assurance...")
    base_dir = os.path.dirname(__file__)
    in_path = os.path.join(base_dir, "parsed_items.json")
    valid_path = os.path.join(base_dir, "validated_items.json")
    flagged_path = os.path.join(base_dir, "flagged_for_review.json")
    
    if not os.path.exists(in_path):
        print("parsed_items.json not found. Run Phase 2 first.")
        sys.exit(1)
        
    with open(in_path, "r", encoding="utf-8") as f:
        parsed_items = json.load(f)
        
    remed_path = os.path.join(base_dir, "remediated_items.json")
    if os.path.exists(remed_path):
        print("Loading remediated items for validation...")
        with open(remed_path, "r", encoding="utf-8") as f:
            remediated = json.load(f)
            # Overlay remediated items on top of parsed items
            for k, v in remediated.items():
                if "error" not in v:
                    parsed_items[k] = v
        
    # Load previously evaluated to support incremental runs
    validated = {}
    flagged = {}
    if os.path.exists(valid_path):
        with open(valid_path, "r", encoding="utf-8") as f:
            validated = json.load(f)
    if os.path.exists(flagged_path):
        with open(flagged_path, "r", encoding="utf-8") as f:
            flagged = json.load(f)
            
    # Force re-evaluation: if it's remediated, we want to evaluate it even if it was flagged before.
    tasks_to_run = []
    for folder_name, data in parsed_items.items():
        if folder_name not in validated:
            tasks_to_run.append((folder_name, data))
            
    print(f"Items to evaluate: {len(tasks_to_run)}")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_worker, f_name, dat): f_name for f_name, dat in tasks_to_run}
        
        for future in as_completed(futures):
            folder_name = futures[future]
            try:
                name, data, is_valid, reason = future.result()
                if is_valid:
                    validated[name] = data
                    print(f"  ✓ Validated: {name[:25]}...")
                else:
                    flagged[name] = data
                    print(f"  ✗ Flagged: {name[:25]}... Reason: {reason}")
            except Exception as e:
                print(f"  ✗ Exception on {folder_name}: {e}")
                data = parsed_items.get(folder_name, {})
                data["qa_reason"] = f"Exception: {e}"
                flagged[folder_name] = data
                
            # Incremental saves
            with open(valid_path, "w", encoding="utf-8") as f:
                json.dump(validated, f, indent=2, ensure_ascii=False)
            with open(flagged_path, "w", encoding="utf-8") as f:
                json.dump(flagged, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 3 Complete!")
    print(f"Total Validated: {len(validated)}")
    print(f"Total Flagged: {len(flagged)}")

if __name__ == "__main__":
    run_phase_3()

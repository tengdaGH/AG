# ============================================================
# Purpose:       Phase 6: Force compliance on flagged items by rewriting Student 2 to oppose Student 1 via Gemini.
# Usage:         python backend/scripts/wad_ingestion/phase6_fix_compliance.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import sys
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are an expert ETS TOEFL test developer. I will provide a 'Writing for Academic Discussion' task that was REJECTED by QA.
The reason it was rejected is usually because Student 1 and Student 2 agreed with each other or failed to take distinct positions.
Your job is to REWRITE Student 2's response so that they take a clear, distinct, and OPPOSING position to Student 1, while still directly answering the Professor's prompt. 
Ensure Student 2 still speaks in a natural B2-level student voice (about 40-60 words).

Input Schema:
{
  "topic": "...",
  "professor_prompt": "...",
  "student_1_name": "...",
  "student_1_response": "...",
  "student_2_name": "...",
  "student_2_response": "..."
}

Output ONLY the raw updated JSON object with Student 2's response rewritten. Do not include markdown formatting like ```json ... ```. No commentary.
"""

def force_compliance():
    base_dir = os.path.dirname(__file__)
    flagged_path = os.path.join(base_dir, "flagged_for_review.json")
    valid_path = os.path.join(base_dir, "validated_items.json")
    
    with open(flagged_path, "r", encoding="utf-8") as f:
        flagged_items = json.load(f)
        
    with open(valid_path, "r", encoding="utf-8") as f:
        validated_items = json.load(f)
        
    count = 0
    for folder_name, data in flagged_items.items():
        print(f"Fixing compliance for: {folder_name[:40]}...")
        reason = data.get("qa_reason", "Unknown")
        print(f"  Reason: {reason}")
        
        try:
            response = client.models.generate_content(
                model="gemini-1.5-pro",
                contents=[f"QA REASON: {reason}\n\nITEM TO FIX:\n{json.dumps(data, indent=2, ensure_ascii=False)}"],
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
                
            fixed_data = json.loads(content.strip())
            fixed_data["remediation_logs"] = f"Forced Student 2 to take opposing position because: {reason}"
            validated_items[folder_name] = fixed_data
            count += 1
            print(f"  ✓ Fixed: {fixed_data.get('student_2_response')[:50]}...")
            
        except Exception as e:
            print(f"  ✗ Failed to fix {folder_name}: {e}")
            
    # Save the finalized validated items
    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump(validated_items, f, indent=2, ensure_ascii=False)
        
    print(f"\nPhase 6 Complete! Fixed {count} items. Total Validated: {len(validated_items)}")

if __name__ == "__main__":
    force_compliance()

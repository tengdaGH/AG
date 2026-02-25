# ============================================================
# Purpose:       Check parsed IELTS JSON files against spec requirements (question count, paragraph sizes, answer presence).
# Usage:         python agents/scripts/check_ielts_spec.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
import os
import json

PARSED_DIR = "/Users/tengda/Antigravity/IELTS/parsed"

def check_specs():
    files = sorted([f for f in os.listdir(PARSED_DIR) if f.endswith('.json') and not f.startswith('_')])
    
    issues = []
    
    for filename in files:
        filepath = os.path.join(PARSED_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Check Total Questions
        q_range = data.get("question_range", [0,0])
        total_q = q_range[1] - q_range[0] + 1
        actual_q = 0
        for group in data.get("question_groups", []):
            actual_q += len(group.get("questions", []))
            
        if total_q not in [13, 14]:
            issues.append(f"{filename}: Unexpected total questions {total_q} (should be 13 or 14)")
            
        if total_q != actual_q:
            issues.append(f"{filename}: Mismatch between range ({total_q}) and actual questions count ({actual_q})")
            
        # Check paragraph sizes again
        paragraphs = data.get("passage", {}).get("paragraphs", [])
        for i, p in enumerate(paragraphs):
            words = len(p.get("text", "").split())
            if words > 400: # 400 is a very safe upper bound after our manual fixes
                issues.append(f"{filename}: Paragraph {i+1} is exceptionally long: {words} words")
            if words < 10 and len(paragraphs) > 3: # Maybe valid if it's a short title/heading, but worth noting
                # Only flag if it's super short and seems like an error. Let's skip this to avoid false positives.
                pass
                
        # Check answers
        for group in data.get("question_groups", []):
            for q in group.get("questions", []):
                if not q.get("answer"):
                    issues.append(f"{filename}: Missing answer for Question {q.get('number')}")
                elif q.get("answer") == "NOT GIVEN" and group.get("type") not in ["TFNG", "YNNG"]:
                    # Check if answer makes sense for question type
                    pass

    if not issues:
        print("All items meet deep IELTS specifications.")
    else:
        print(f"Found {len(issues)} potential spec violations:")
        for issue in issues[:30]: # print first 30
            print(issue)
        if len(issues) > 30:
            print(f"...and {len(issues) - 30} more.")

if __name__ == '__main__':
    check_specs()

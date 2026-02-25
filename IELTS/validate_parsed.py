import os
import json

VALID_TYPES = {
    "TFNG", "YNNG", "MCQ", "MCQ_MULTI", "PARAGRAPH_MATCHING", 
    "HEADING_MATCHING", "SUMMARY_COMPLETION", "SUMMARY_WORDBANK", 
    "SENTENCE_COMPLETION", "SENTENCE_ENDING", "PERSON_MATCHING", 
    "SHORT_ANSWER", "DIAGRAM_LABEL", "TABLE_COMPLETION",
    "MATCHING", "NOTES_COMPLETION", "FLOWCHART_COMPLETION",
    "CLASSIFICATION", "OTHER_MATCHING", "PLACE_MATCHING", "UNKNOWN"
}

def validate_item(item):
    errors = []
    
    # Check question range and counts
    q_range = item.get("question_range", [0, 0])
    expected_count = q_range[1] - q_range[0] + 1
    
    if expected_count == 0 or q_range == [0, 0]:
        return []
    
    # Some older tests might have fewer questions or up to 17
    if not (9 <= expected_count <= 17):
        errors.append(f"Unexpected question range {q_range} (expected 9-17 questions, found {expected_count})")
        
    actual_count = 0
    groups = item.get("question_groups", [])
    
    if len(groups) < 2:
        errors.append(f"Only {len(groups)} question groups found. Expected at least 2.")
        
    for g_idx, group in enumerate(groups):
        q_type = group.get("type")
        if q_type not in VALID_TYPES:
            errors.append(f"Group {g_idx} has invalid/unknown type: {q_type}")
            
        qs = group.get("questions", [])
        actual_count += len(qs)
        
        for q in qs:
            if not q.get("text"):
                errors.append(f"Question {q.get('number')} has empty text")
            if not q.get("answer"):
                errors.append(f"Question {q.get('number')} has empty answer")
                
            if q_type in ["MCQ", "MCQ_MULTI"]:
                if not q.get("options") or len(q.get("options")) < 3:
                     errors.append(f"MCQ Question {q.get('number')} missing or too few options")
                     
    if actual_count != expected_count:
        errors.append(f"Found {actual_count} discrete questions, but range implies {expected_count}")
        
    passage = item.get("passage", {})
    if len(passage.get("paragraphs", [])) < 1:
         errors.append(f"Passage has no paragraphs. Expected >= 1.")
         
    return errors

def main():
    input_dir = "/Users/tengda/Antigravity/IELTS/parsed"
    if not os.path.exists(input_dir):
        print(f"Directory not found: {input_dir}")
        return
        
    files = sorted([f for f in os.listdir(input_dir) if f.endswith('.json')])
    
    total = 0
    failed = 0
    
    for filename in files:
        if filename.startswith('_'):
            continue
            
        total += 1
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        errors = validate_item(data)
        
        if errors:
            failed += 1
            print(f"❌ {filename}")
            for err in errors:
                print(f"   - {err}")
        else:
            print(f"✅ {filename}")
            
    print(f"\nValidation Complete: {total - failed}/{total} passed.")

if __name__ == "__main__":
    main()

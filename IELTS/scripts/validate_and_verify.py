import os
import json
import argparse
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

INPUT_DIR = "/Users/tengda/Antigravity/IELTS/parsed_v2"
REPORT_FILE = "/Users/tengda/Antigravity/IELTS/qa_report.json"

VALID_TYPES = {
    "MULTIPLE_CHOICE",
    "MULTIPLE_CHOICE_MULTIPLE_ANSWER",
    "TRUE_FALSE_NOT_GIVEN",
    "YES_NO_NOT_GIVEN",
    "MATCHING_HEADINGS",
    "MATCHING_FEATURES",
    "MATCHING_SENTENCE_ENDINGS",
    "MATCHING_PARAGRAPH_INFORMATION",
    "SENTENCE_COMPLETION",
    "SUMMARY_COMPLETION",
    "NOTE_COMPLETION",
    "TABLE_COMPLETION",
    "FLOWCHART_COMPLETION",
    "FLOW_CHART_COMPLETION",
    "DIAGRAM_LABEL_COMPLETION",
    "CLASSIFICATION",
    "SHORT_ANSWER"
}

def validate_structure(item: Dict[str, Any]) -> List[str]:
    """Run strict structural and quality heuristics checks on a single parsed item."""
    errors = []
    
    passage_id = item.get("id", "Unknown ID")
    
    # 1. Parsing Errors
    if "error" in item:
        errors.append(f"LLM Parsing failed: {item['error']}")
        return errors
        
    # 2. Passage Structure Completeness & Strict Paragraph Checks
    content = item.get("content", {})
    if "paragraphs" not in content:
        errors.append("Missing paragraphs in content")
        return errors # Can't check further
        
    paragraphs = content["paragraphs"]
    if not isinstance(paragraphs, list) or len(paragraphs) < 2:
        errors.append("Too few paragraphs detected (merged passages or poor OCR)")
        
    for idx, p in enumerate(paragraphs):
        p_text = p.get("text", "")
        if len(p_text) > 2500:
            errors.append(f"Unparsed long paragraph detected (Para {idx} length: {len(p_text)} chars)")
            
    # 3. Question Structure & Counts
    if "questions" not in item or "question_groups" not in item["questions"]:
        errors.append("Missing question_groups")
        return errors
        
    groups = item["questions"]["question_groups"]
    parsed_total = item["questions"].get("parsed_total_questions", 0)
    
    actual_question_count = sum(len(g.get("questions", [])) for g in groups)
    if actual_question_count != parsed_total:
        errors.append(f"Question count mismatch: {actual_question_count} actual vs {parsed_total} declared")
        
    if actual_question_count == 0:
        errors.append("ZERO questions found in groups")
        
    # Strictly enforce 12-14 questions for standard IELTS passages
    if actual_question_count not in [12, 13, 14]:
        errors.append(f"Non-standard or missing questions: Total {actual_question_count} (Expected 12-14)")
        
    # 4. Question Details, Completeness, and Options Length
    seen_numbers = set()
    for g in groups:
        gtype = g.get("type", "")
        if gtype not in VALID_TYPES:
            errors.append(f"Invalid question group type: '{gtype}'")
            
        if not g.get("instruction"):
            errors.append(f"Missing instruction for group type '{gtype}'")
            
        for q in g.get("questions", []):
            try:
                # Force numbers to be integers for exact sequence matching
                num = int(q.get("number"))
            except (ValueError, TypeError):
                errors.append(f"Invalid or missing question number: '{q.get('number')}'")
                continue
                
            ans = q.get("answer")
            text = q.get("text", "")
            
            if num in seen_numbers:
                errors.append(f"Duplicate question number: {num}")
            seen_numbers.add(num)
                
            if not ans:
                errors.append(f"Empty answer for Q{num}")
            
            if len(text.strip()) < 3 and gtype not in ["MATCHING_HEADINGS", "MATCHING_PARAGRAPH_INFORMATION"]:
                # Some matchings don't have text, just "Paragraph A". Otherwise text is required.
                errors.append(f"Empty or malformed question text for Q{num}: '{text}'")
                
            # Type-specific quality constraints
            if gtype in ["TRUE_FALSE_NOT_GIVEN", "YES_NO_NOT_GIVEN"]:
                valid_tfng = ["TRUE", "FALSE", "NOT GIVEN", "YES", "NO"]
                if ans.upper() not in valid_tfng:
                    errors.append(f"Invalid Boolean format for Q{num}: '{ans}'")
                    
            if gtype in ["MULTIPLE_CHOICE", "MATCHING_FEATURES", "MATCHING_SENTENCE_ENDINGS", "CLASSIFICATION"]:
                opts = q.get("options", [])
                if not isinstance(opts, list) or len(opts) < 2:
                    errors.append(f"Missing or insufficient options array for {gtype} Q{num}")
                    
    # 5. Strict Sequence Verification (Contiguity without gaps)
    if seen_numbers:
        sorted_nums = sorted(list(seen_numbers))
        expected_seq = list(range(sorted_nums[0], sorted_nums[-1] + 1))
        if sorted_nums != expected_seq:
            missing = set(expected_seq) - set(sorted_nums)
            errors.append(f"Question sequence gap detected. Missing numbers: {missing}")

    return errors

def process_file(filename: str) -> Dict[str, Any]:
    filepath = os.path.join(INPUT_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    errors = validate_structure(data)
    
    return {
        "filename": filename,
        "id": data.get("id"),
        "error_count": len(errors),
        "errors": errors,
        "valid": len(errors) == 0
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--structural-only", action="store_true", help="Only run structural checks, no LLM verification")
    parser.add_argument("--workers", type=int, default=10, help="Workers for processing")
    args = parser.parse_args()
    
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Output directory {INPUT_DIR} does not exist.")
        return
        
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    print(f"Starting structural validation of {len(files)} files...")
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for res in executor.map(process_file, files):
            results.append(res)
            
    # Calculate stats
    total = len(results)
    valid = sum(1 for r in results if r["valid"])
    invalid = total - valid
    
    print("\n" + "="*40)
    print("STRUCTURAL VALIDATION RESULTS")
    print("="*40)
    print(f"Total files: {total}")
    print(f"Passed:      {valid} ({(valid/total)*100:.1f}%)" if total > 0 else "Passed: 0")
    print(f"Failed:      {invalid} ({(invalid/total)*100:.1f}%)" if total > 0 else "Failed: 0")
    print("="*40)
    
    if invalid > 0:
        print("\nErrors by file:")
        for r in results:
            if not r["valid"]:
                print(f"  ❌ {r['filename']}:")
                for err in r["errors"]:
                    print(f"      - {err}")
                    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed report written to {REPORT_FILE}")

if __name__ == "__main__":
    main()

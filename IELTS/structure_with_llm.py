import os
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Load API Key from TOEFL Backend .env
with open('/Users/tengda/Antigravity/toefl-2026/backend/.env', 'r') as f:
    for line in f:
        if line.startswith('GEMINI_API_KEY='):
            os.environ['GEMINI_API_KEY'] = line.strip().split('=', 1)[1].strip('"\'')
            break

client = genai.Client()

# --- Pydantic Schema for Gemini Structured Output ---

class Option(BaseModel):
    letter: str = Field(description="The option letter (A, B, C, etc.)")
    text: str = Field(description="The text of the option")

class StructuredQuestion(BaseModel):
    number: int = Field(description="The question number (e.g., 1, 14, 27)")
    text: str = Field(description="The text of the question. For summary/sentence completion, use '___' for blanks.")
    options: Optional[List[Option]] = Field(default=None, description="For Choice types, list of options. Null otherwise.")
    answer: str = Field(description="The correct answer you generate. Always provide an answer even if unsure. Example: 'TRUE', 'A', '3', 'word'")
    answer_source: str = Field(default="llm_generated", description="Always set to 'llm_generated'")

class StructuredQuestionGroup(BaseModel):
    type: str = Field(description="One of: TFNG, YNNG, MCQ, MCQ_MULTI, PARAGRAPH_MATCHING, HEADING_MATCHING, SUMMARY_COMPLETION, SUMMARY_WORDBANK, SENTENCE_COMPLETION, SENTENCE_ENDING, PERSON_MATCHING, SHORT_ANSWER, DIAGRAM_LABEL, TABLE_COMPLETION")
    range: List[int] = Field(description="[start_q_num, end_q_num]")
    instructions: str = Field(description="The instruction text for this group.")
    questions: List[StructuredQuestion] = Field(description="The extracted questions for this group")

class StructuredParagraph(BaseModel):
    label: str = Field(description="Paragraph label 'A', 'B', etc. if it exists, otherwise empty string ''")
    text: str = Field(description="The cleaned paragraph text.")

class StructuredPassage(BaseModel):
    has_paragraph_labels: bool
    paragraphs: List[StructuredParagraph]
    
class CleanedItem(BaseModel):
    title: str = Field(description="The English title of the passage. Cleaned of OCR artifacts.")
    passage: StructuredPassage
    question_groups: List[StructuredQuestionGroup]

# --- Main Logic ---

def process_item_with_llm(raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """Pass the raw extracted text + JSON to Gemini for structuring and answer generation."""
    
    # We construct a prompt passing the messy passage text and questions raw text
    prompt = f"""
You are an expert IELTS parser. I am providing you with roughly extracted text from an IELTS Reading PDF.
Your job is to structure it perfectly into the requested JSON schema, clean up any OCR artifacts, and GENERATE the correct answers for every question.

# DOCUMENT METADATA
ID: {raw_json.get('id')}
Title: {raw_json.get('title')}
Question Range: {raw_json.get('question_range')}

# EXTRACTED PASSAGE
```text
{json.dumps(raw_json.get('passage', {}), indent=2, ensure_ascii=False)}
```

# EXTRACTED QUESTION GROUPS (RAW TEXT)
```json
{json.dumps(raw_json.get('question_groups', []), indent=2, ensure_ascii=False)}
```

# INSTRUCTIONS
1. Clean the passage: remove hyphenated splits across lines and fix OCR errors. 
   - Preserve the exact wording and paragraph labels (A-H) if they exist.
   - You MUST split the passage into logical paragraphs based on the text flow and natural breaks. DO NOT return a single giant paragraph. Even if there are no A-H labels, break the text into multiple distinct paragraphs.
2. Structure the questions: read the `raw_text` for each question group, determine the boundaries of each question, and create a `StructuredQuestion` object for each.
   - DEDUPLICATION: If the `raw_text` contains the exact same question group twice (e.g., due to OCR repeating a page), DO NOT duplicate the questions. Only create the questions once.
   - MULTI-BOX QUESTIONS (e.g. MCQ_MULTI): If a question instruction says to "Choose THREE letters... in boxes 35-37", you MUST create EXACTLY THREE separate `StructuredQuestion` objects (one for 35, one for 36, and one for 37), even if they share the same question text. The number of question objects MUST match the number of boxes.
3. Generate answers: You MUST generate the correct answer for every question based on the passage. Set `answer_source` to "llm_generated".
- For TFNG/YNNG: Answer is "TRUE", "FALSE", "NOT GIVEN" etc.
- For MCQ: Answer is "A", "B", "C", or "D"
- For Matching: Answer is the correct letter or Roman numeral.
- For Short Answer / Completion: Answer is the word(s) from the text.
4. Verify numbers: Ensure every question number in the `Question Range` is represented exactly once.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CleanedItem,
            temperature=0.1,
        ),
    )
    
    cleaned_data = response.parsed
    
    # Merge back into the final IELTS schema
    final_output = raw_json.copy()
    final_output['title'] = cleaned_data.title
    
    # Convert Pydantic to dict
    final_output['passage'] = cleaned_data.passage.model_dump()
    final_output['question_groups'] = [g.model_dump() for g in cleaned_data.question_groups]
    
    # Update metadata
    types_found = [g['type'] for g in final_output['question_groups']]
    total_q = sum([(g['range'][1] - g['range'][0] + 1) for g in final_output['question_groups']])
    
    final_output['metadata'] = {
        "parsed_total_questions": total_q,
        "question_types": types_found,
        "parsed_at": raw_json['metadata']['parsed_at'],
        "llm_structured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "parser_version": "1.0",
        "needs_review": True
    }
    
    return final_output


def process_file(f, input_dir, output_dir):
    out_name = f.replace('_raw.json', '.json')
    out_path = os.path.join(output_dir, out_name)
    if os.path.exists(out_path):
        print(f"  -> Skipping, already exists: {out_name}")
        return

    print(f"Structuring {f} with LLM...")
    try:
        with open(os.path.join(input_dir, f), 'r', encoding='utf-8') as in_f:
            raw_json = json.load(in_f)
            
        cleaned_data = process_item_with_llm(raw_json)
        
        with open(out_path, 'w', encoding='utf-8') as out_f:
            json.dump(cleaned_data, out_f, indent=2, ensure_ascii=False)
            
        print(f"  -> Saved {out_name}")
    except Exception as e:
        print(f"  -> Error structuring {f}: {e}")

def main():
    input_dir = "/Users/tengda/Antigravity/IELTS/parsed_raw"
    output_dir = "/Users/tengda/Antigravity/IELTS/parsed"
    os.makedirs(output_dir, exist_ok=True)
    
    files = sorted(os.listdir(input_dir))
    files_to_process = [f for f in files if f.endswith("_raw.json")]
    
    print(f"Total raw files: {len(files_to_process)}")
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        for f in files_to_process:
            # Check if it exists before sleeping
            out_name = f.replace('_raw.json', '.json')
            if os.path.exists(os.path.join(output_dir, out_name)):
                continue
                
            print(f"DEBUG: Submitting {f}...")
            executor.submit(process_file, f, input_dir, output_dir)
            import sys
            sys.stdout.flush()
            import time
            time.sleep(4)

if __name__ == "__main__":
    main()

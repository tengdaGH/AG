#!/usr/bin/env python3
"""
structure_v2.py
===============
Phase 2 of the IELTS Reading reprocessing pipeline.

Takes the raw extracted text from `IELTS/extracted/` and structures it into
clean JSON representations of the passage and questions.
Uses the Minimax API (via OpenAI client) to perform structuring.

This is a two-call process per item:
  1. Clean & structure the passage text (identify paragraphs A, B, etc.)
  2. Parse the questions & answers based on the clean passage + raw question text

Location : /Users/tengda/Antigravity/IELTS/scripts/
Venv     : source /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/activate
Run      : python /Users/tengda/Antigravity/IELTS/scripts/structure_v2.py
"""

import os  
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = "/Users/tengda/Antigravity/IELTS/extracted"
OUTPUT_DIR = "/Users/tengda/Antigravity/IELTS/parsed_v2"
ERROR_DIR = "/Users/tengda/Antigravity/IELTS/broken"
ENV_PATH = "/Users/tengda/Antigravity/IELTS/.env"

# Load local .env manually to avoid python-dotenv dependency
def load_env():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        k, v = line.split('=', 1)
                        os.environ[k.strip()] = v.strip()

load_env()
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
if not MINIMAX_API_KEY:
    print("❌ MINIMAX_API_KEY not found in environment or .env file.")
    sys.exit(1)

# Initialize OpenAI client with Minimax base URL
client = OpenAI(
    api_key=MINIMAX_API_KEY,
    base_url="https://api.minimaxi.chat/v1"
)

# Best current Minimax general model for complex tasks
MODEL_NAME = "MiniMax-Text-01"


# ---------------------------------------------------------------------------
# Schema Definitions
# ---------------------------------------------------------------------------
class Paragraph(BaseModel):
    label: Optional[str] = Field(None, description="The paragraph label, e.g., 'A', 'B'. Null if no label.")
    content: str = Field(description="The cleaned text of the paragraph.")

class CleanedPassage(BaseModel):
    title: str = Field(description="The title of the reading passage.")
    has_paragraph_labels: bool = Field(description="True if the passage has labeled paragraphs (e.g., A, B, C).")
    paragraphs: List[Paragraph] = Field(description="List of structured paragraphs.")

class QuestionOption(BaseModel):
    label: str = Field(description="The option label: 'A', 'B', etc. Or 'TRUE', 'FALSE', 'NOT GIVEN'.")
    text: str = Field(description="The text content of the option.")

class Question(BaseModel):
    number: int = Field(description="The question number (1-40).")
    text: str = Field(description="The text of the question. Empty for simple gap fills where the instruction provides context.")
    answer: str = Field(description="The correct answer key. MUST EXACTLY MATCH THE PROVIDED ANSWER KEY.")
    options: Optional[List[QuestionOption]] = Field(None, description="Options for Multiple Choice or True/False/Not Given tasks.")

class QuestionGroup(BaseModel):
    type: str = Field(
        description="Must be one of: MULTIPLE_CHOICE, TRUE_FALSE_NOT_GIVEN, YES_NO_NOT_GIVEN, MATCHING_FEATURES, MATCHING_HEADINGS, MATCHING_SENTENCE_ENDINGS, MATCHING_PARAGRAPH_INFORMATION, SUMMARY_COMPLETION, SENTENCE_COMPLETION, TABLE_COMPLETION, DIAGRAM_LABEL_COMPLETION, FLOW_CHART_COMPLETION, SHORT_ANSWER_QUESTIONS"
    )
    instruction: str = Field(description="The instruction text indicating how to answer the questions in this group.")
    questions: List[Question] = Field(description="List of questions in this group.")

class StructuredQuestions(BaseModel):
    question_groups: List[QuestionGroup] = Field(description="List of question groups.")
    parsed_total_questions: int = Field(description="Total number of questions parsed. Should equal the number of answers in the answer key.")


# ---------------------------------------------------------------------------
# LLM Processing Logic
# ---------------------------------------------------------------------------
def call_minimax_structured(prompt: str, response_schema: type, system_prompt: str = "") -> dict:
    """Helper to make a structured call to Minimax."""
    schema = response_schema.model_json_schema()
    
    # Inject schema into the system prompt
    full_sys = system_prompt + f'''\n\nYou MUST respond with ONLY valid JSON that conforms exactly to this schema:\n{json.dumps(schema, indent=2)}\n\nIMPORTANT: DO NOT output the JSON schema definitions themselves. You must output the ACTUAL EXTRACTED DATA populated into this schema structure. Do not include any other conversational text. Wrap your JSON in a ```json code block.'''
    
    messages = [
        {"role": "system", "content": full_sys},
        {"role": "user", "content": prompt}
    ]

    import time
    import subprocess
    
    max_retries = 8
    base_delay = 15
    content = None
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.01,
        "max_tokens": 8192
    }
    
    for attempt in range(max_retries):
        try:
            print(f"      [API] Looping curl subprocess to Minimax (Attempt {attempt+1}/{max_retries})...")
            t0 = time.time()
            
            # Use raw unbuffered OS-level curl to bypass Python socket death traps
            curl_cmd = [
                "curl", "-s", "-S", "-m", "60", # 60 second hard timeout to allow for slow responses over VPN
                "-X", "POST", "https://api.minimaxi.chat/v1/chat/completions",
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {MINIMAX_API_KEY}",
                "-d", json.dumps(payload)
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True)
            t1 = time.time()
            
            if result.returncode != 0:
                print(f"      [!] Curl returned code {result.returncode} in {t1-t0:.2f}s: {result.stderr}")
                if result.returncode == 28: # curl timeout code
                    if attempt < max_retries - 1:
                        print(f"      [!] Connection timeout/drop. Retrying (attempt {attempt+1}/{max_retries}) in 5s...")
                        time.sleep(5)
                        continue
                raise Exception(f"Curl failed: {result.stderr}")
            
            print(f"      [API] Minimax responded via curl in {t1-t0:.2f}s.")
            resp_json = json.loads(result.stdout)
            
            if "error" in resp_json:
                err_msg = json.dumps(resp_json["error"])
                if "429" in err_msg or "rate limit" in err_msg.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay + (10 * attempt)
                        print(f"      [!] Rate limit hit (429). Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                raise Exception(f"Minimax API Error: {err_msg}")
                
            content = resp_json['choices'][0]['message']['content']
            break
            
        except Exception as e:
            print(f"  [!] Minimax subprocess Error: {str(e)}")
            raise
            
    if not isinstance(content, str):
        raise ValueError("LLM returned empty or invalid content.")
        
    # Extract JSON from markdown blocks if present
    if '```' in content:
        import re
        # Find the content between the first ```json and the next ```
        # or just take whatever is between the first and last backticks
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            content = match.group(1)
        else:
            # Fallback: just strip leading/trailing backticks
            content = re.sub(r'^```(?:json)?\s*', '', content.strip())
            content = re.sub(r'\s*```$', '', content)
            
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  [!] JSON Decode Error. Raw string length: {len(content)}")
        raise ValueError(f"Invalid JSON: {str(e)}. Raw: {content[:500]}...{content[-500:]}")


def clean_passage(raw_text: str) -> dict:
    """Stage 1: Clean the passage text into coherent paragraphs."""
    system_prompt = """You are an expert IELTS parser.
Your only job is to take raw OCR text of an IELTS reading passage and output it cleanly as structured paragraphs.
Fix line breaks within sentences. Identify if paragraphs are labeled (A, B, C...).
Do NOT attempt to parse any questions here."""

    prompt = f"Raw Passage Text:\n{raw_text}\n\nPlease parse this into the requested structured paragraph format."
    
    return call_minimax_structured(prompt, CleanedPassage, system_prompt)


def structure_questions(passage: dict, raw_q_text: str, answer_key: dict) -> dict:
    """Stage 2: Parse questions and pair them with exact answers from the key."""
    system_prompt = """You are an expert IELTS parser.
I will give you a clean reading passage, raw OCR text of the test questions, and the EXACT Answer Key.
Your job is to structure the questions into groups (e.g., MULTIPLE_CHOICE, TRUE_FALSE_NOT_GIVEN) and pair each individual question with its EXACT answer from the provided key.

RULES:
1. Every question number in the raw text MUST exist in your output.
2. The `answer` field for a question MUST be exactly the value provided in the Answer Key. Do not generate or modify answers.
3. If the Answer Key has 'B OR D IN EITHER ORDER', keep it exactly as is.
4. Extract options for multiple choice and TFNG (e.g., A, B, C, D).
"""

    prompt = f"""
Cleaned Passage (for context only):
{json.dumps(passage, ensure_ascii=False)}

Raw Question Text:
{raw_q_text}

EXACT Answer Key (use these EXACT string values for the `answer` fields):
{json.dumps(answer_key, indent=2)}

Please extract all questions into structured groups and apply the answer key.
"""
    
    return call_minimax_structured(prompt, StructuredQuestions, system_prompt)


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
def process_single_item(item: dict) -> dict:
    """Complete 2-stage pipeline for a single item."""
    passage_text = item.get('passage_text', '')
    questions_text = item.get('questions_text', '')
    answer_key = item.get('answer_key', {})
    
    if not passage_text:
        raise ValueError("Missing passage_text")
    if not questions_text:
        # Some passages might have everything in passage_text if formatting is weird
        questions_text = "No separate questions text found. Look for questions at the end of the passage text."
        
    print(f"  [{item['id']}] Extracted {len(item.get('page_range', []))} pages.")
    
    print("    [Stage 1] Cleaning passage text...")
    cleaned_passage = clean_passage(passage_text)
    if "paragraphs" not in cleaned_passage or not isinstance(cleaned_passage["paragraphs"], list):
        raise ValueError("Stage 1 failed: LLM likely returned schema instead of actual paragraph data.")
    if not cleaned_passage:
        raise RuntimeError("Stage 1 failed to return structured passage.")
        
    print("    [Stage 2] Structuring questions and pairing answers...")
    structured_qs = structure_questions(cleaned_passage, questions_text, answer_key)
    if not structured_qs:
        raise RuntimeError("Stage 2 failed to return structured questions.")
        
    cleaned_passage.pop("$defs", None)
    structured_qs.pop("$defs", None)
        
    # Combine outputs
    result = {
        "id": item["id"],
        "slug": item["slug"],
        "title": item["title"],
        "page_range": item["page_range"],
        "raw_answer_key": answer_key,
        "content": cleaned_passage,
        "questions": structured_qs,
        "processed_at": datetime.now().isoformat()
    }
    
    return result


def process_file(filename, args):
    print(f"  [>] Started {filename}")
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)
    error_path = os.path.join(ERROR_DIR, filename)
    
    if os.path.exists(output_path) and not getattr(args, 'test_id', None):
        print(f"  [-] Skipping {filename}, already processed.")
        return True
        
    with open(input_path, 'r', encoding='utf-8') as f:
        item = json.load(f)
        
    try:
        structured_data = process_single_item(item)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print(f"  [+] Success {filename}")
        return True
        
    except Exception as e:
        print(f"  [!] Error processing {filename}: {e}")
        # Move or save a stub in error dir so we know it failed
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump({"error": str(e), "original": item}, f, indent=2)
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ERROR_DIR, exist_ok=True)
    
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    parser = argparse.ArgumentParser("Phase 2 - LLM Structuring with Minimax")
    parser.add_argument("--test-id", type=str, help="Run only on a specific item ID (e.g. ielts-r-0001)")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers")
    args = parser.parse_args()
    
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    files.sort()
    
    if args.test_id:
        files = [f"{args.test_id}.json"]
        args.workers = 1
        
    total = len(files)
    print(f"Found {total} files to process with {args.workers} workers.")
    
    success = 0
    failed = 0
    skipped = 0
    t_start = time.time()
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_file, f, args): f for f in files}
        for future in as_completed(futures):
            f = futures[future]
            try:
                res = future.result()
                if res:
                    success += 1
                else:
                    failed += 1
            except Exception as exc:
                print(f"  [!] Unhandled exception processing {f}: {exc}")
                failed += 1

    t_end = time.time()
    print(f"\nExecution finished in {t_end - t_start:.2f}s")
    print(f"Total: {total}, Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()

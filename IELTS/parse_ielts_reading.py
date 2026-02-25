import os
import json
import re
import PyPDF2
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

class QuestionType:
    TFNG = "TFNG"
    YNNG = "YNNG"
    MCQ = "MCQ"
    MCQ_MULTI = "MCQ_MULTI"
    PARAGRAPH_MATCHING = "PARAGRAPH_MATCHING"
    HEADING_MATCHING = "HEADING_MATCHING"
    SUMMARY_COMPLETION = "SUMMARY_COMPLETION"
    SUMMARY_WORDBANK = "SUMMARY_WORDBANK"
    SENTENCE_COMPLETION = "SENTENCE_COMPLETION"
    SENTENCE_ENDING = "SENTENCE_ENDING"
    PERSON_MATCHING = "PERSON_MATCHING"
    SHORT_ANSWER = "SHORT_ANSWER"
    DIAGRAM_LABEL = "DIAGRAM_LABEL"
    TABLE_COMPLETION = "TABLE_COMPLETION"


def extract_pdf_text(path: str) -> str:
    """Extract raw text from PDF using PyPDF2."""
    reader = PyPDF2.PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def parse_filename(filename: str) -> Tuple[str, str, str, str, str]:
    """Parse filename to extract P level, title, etc."""
    # e.g. "9. P1 - Listening to the Ocean 海洋探测【次】.pdf"
    # e.g. "38. P2 - Egypt's ancient boat-builders 古埃及造船.pdf"
    
    # Strip extension
    base = filename.rsplit('.', 1)[0]
    
    parts = base.split(' - ', 1)
    prefix = parts[0] # "9. P1"
    rest = parts[1] if len(parts) > 1 else ""
    
    prefix_parts = prefix.split('. ')
    num = prefix_parts[0]
    position = prefix_parts[1] if len(prefix_parts) > 1 else "Unknown"
    
    # Try to extract difficulty
    difficulty = "unmarked"
    if '【高】' in rest:
        difficulty = "high"
        rest = rest.replace('【高】', '')
    elif '【次】' in rest:
        difficulty = "medium"
        rest = rest.replace('【次】', '')
    
    # Try to extract Chinese title if any
    title = rest.strip()
    title_cn = ""
    
    # Simple heuristic: last space separates English and Chinese, but sometimes there's no space.
    # Let's just use regex for Chinese characters
    cn_match = re.search(r'([\u4e00-\u9fa5]+.*)$', title)
    if cn_match:
        title_cn = cn_match.group(1).strip()
        title = title[:cn_match.start()].strip()
        
    return position, title, title_cn, difficulty, num


def identify_question_type(instructions: str) -> str:
    """Identify the IELTS question type from the instructions."""
    instructions = instructions.lower()
    
    if "true" in instructions and "false" in instructions and "not given" in instructions:
        return QuestionType.TFNG
    elif "yes" in instructions and "no" in instructions and "not given" in instructions:
        return QuestionType.YNNG
    elif "choose the correct letter" in instructions and "a, b, c or d" in instructions:
        return QuestionType.MCQ
    elif "choose two letters" in instructions or "choose three letters" in instructions:
        return QuestionType.MCQ_MULTI
    elif "which paragraph contains the following information" in instructions:
        return QuestionType.PARAGRAPH_MATCHING
    elif "choose the correct heading" in instructions:
        return QuestionType.HEADING_MATCHING
    elif "complete the summary" in instructions:
        if "list of words" in instructions or "choose the correct letter" in instructions or "choose no more than" not in instructions:
            if re.search(r'choose the correct letter,?\s*[a-z]', instructions) or "list of words" in instructions:
                return QuestionType.SUMMARY_WORDBANK
        return QuestionType.SUMMARY_COMPLETION
    elif "complete the sentences below" in instructions:
        return QuestionType.SENTENCE_COMPLETION
    elif "complete each sentence with the correct ending" in instructions:
        return QuestionType.SENTENCE_ENDING
    elif "match each" in instructions and ("person" in instructions or "researcher" in instructions or "statement" in instructions or "feature" in instructions):
        return QuestionType.PERSON_MATCHING
    elif "no more than" in instructions and "words" in instructions and "complete the" not in instructions:
        return QuestionType.SHORT_ANSWER
    elif "label the diagram" in instructions or "label the map" in instructions or "label the plan" in instructions:
        return QuestionType.DIAGRAM_LABEL
    elif "complete the table" in instructions or "complete the notes" in instructions or "complete the flow-chart" in instructions:
        return QuestionType.TABLE_COMPLETION
    
    if "match the" in instructions:
        return QuestionType.PERSON_MATCHING
    if "choose no more than" in instructions:
        return QuestionType.SHORT_ANSWER
        
    return "UNKNOWN"


def split_into_blocks_and_passage(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Splits the raw text into the main passage and a list of question group blocks.
    Handles cases where questions appear BEFORE or AFTER the passage.
    """
    # Find all Question headers, ignoring the "spend about 20 minutes" ones
    all_headers = list(re.finditer(r'(Questions?\s+(\d+)(?:\s*[-–—]\s*(\d+))?)', text, re.IGNORECASE))
    
    valid_headers = []
    for match in all_headers:
        context_before = text[max(0, match.start() - 30):match.start()].lower()
        if "minutes on" in context_before:
            continue
        valid_headers.append(match)
        
    if not valid_headers:
        return text, []
        
    # Split text into chunks based on valid_headers
    chunks = []
    
    # Text before the first valid header (might be passage if no questions before it)
    first_chunk = text[:valid_headers[0].start()].strip()
    if first_chunk:
        chunks.append({"header": None, "text": first_chunk, "start_idx": 0})
        
    for i, match in enumerate(valid_headers):
        start_idx = match.start()
        end_idx = valid_headers[i+1].start() if i + 1 < len(valid_headers) else len(text)
        
        chunk_text = text[start_idx:end_idx].strip()
        chunks.append({
            "header": match,
            "text": chunk_text,
            "start_idx": start_idx
        })
        
    # The passage is the longest contiguous block of text that does not look like a list of questions.
    # We will identify the chunk containing the longest text (or longest sub-chunk if a chunk contains both questions and passage).
    # Actually, a chunk starting with "Questions X-Y" might contain the questions AND the passage!
    # Let's separate passage from questions within each chunk by finding the longest paragraph block.
    
    passage_text = ""
    question_groups = []
    
    passage_chunk_idx = -1
    max_len = 0
    
    # First, find which chunk has the most characters. The passage is almost certainly in the longest chunk.
    for i, c in enumerate(chunks):
        if len(c["text"]) > max_len:
            max_len = len(c["text"])
            passage_chunk_idx = i
            
    for i, c in enumerate(chunks):
        header_match = c["header"]
        
        if header_match:
            q_start = int(header_match.group(2))
            q_end = int(header_match.group(3)) if header_match.group(3) else q_start
            
            # If this is the chunk containing the passage, we need to split it
            if i == passage_chunk_idx:
                # The passage usually has paragraph labels (A, B, C) or is a huge block of text.
                # The questions are usually short lines.
                # Let's just find the first double newline after the questions, or look for paragraph A.
                # If it's HEADING_MATCHING (List of Headings), the questions are before the passage.
                
                chunk_text = c["text"]
                # A heuristic: look for a title or Paragraph A
                # Often passage starts after the headings list
                passage_start_match = re.search(r'\n([A-Z][^\n]{5,100})\n+A\s+[A-Z]', chunk_text)
                if passage_start_match:
                    q_text = chunk_text[:passage_start_match.start()].strip()
                    p_text = chunk_text[passage_start_match.start():].strip()
                    passage_text = p_text
                    
                    instructions = q_text[header_match.end() - header_match.start():].strip()
                    question_groups.append({
                        "type": identify_question_type(instructions),
                        "range": [q_start, q_end],
                        "instructions": instructions.replace('\n', ' '),
                        "raw_text": q_text,
                        "questions": []
                    })
                else:
                    # Fallback: if we can't cleanly split, assume the whole chunk is the passage 
                    # except the first 500 chars which might be the questions.
                    # This implies questions might be lost or mangled here, but Gemini will fix it.
                    p_text = chunk_text
                    instructions = chunk_text[header_match.end() - header_match.start():][:300]
                    passage_text = p_text
                    question_groups.append({
                         "type": identify_question_type(instructions),
                         "range": [q_start, q_end],
                         "instructions": instructions.replace('\n', ' '),
                         "raw_text": chunk_text[:500],
                         "questions": []
                    })
            else:
                instructions = c["text"][header_match.end() - header_match.start():].strip()
                question_groups.append({
                    "type": identify_question_type(instructions),
                    "range": [q_start, q_end],
                    "instructions": instructions.replace('\n', ' '),
                    "raw_text": c["text"],
                    "questions": []
                })
        else:
            if i == passage_chunk_idx:
                passage_text = c["text"]
                
    # If passage text is still empty, fallback to the text from the first chunk
    if not passage_text and chunks:
        passage_text = chunks[0]["text"]
        
    return passage_text, question_groups


def parse_passage(text: str) -> Dict[str, Any]:
    """Parse passage into paragraphs."""
    paragraphs = []
    blocks = re.split(r'\n\s*\n', text)
    
    has_labels = False
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if re.search(r'^READING PASSAGE', block, re.IGNORECASE):
            continue
        if re.search(r'You should spend about \d+ minutes', block, re.IGNORECASE):
            continue
            
        label = ""
        label_match = re.match(r'^([A-H])[\s\n]', block)
        if label_match:
            has_labels = True
            label = label_match.group(1)
            block = block[label_match.end():].strip()
            
        paragraphs.append({
            "label": label,
            "text": block.replace('\n', ' ')
        })
        
    return {
        "has_paragraph_labels": has_labels,
        "paragraphs": [p for p in paragraphs if p["text"]],
        "raw_text": text
    }


def process_file(filepath: str, filename: str) -> Dict[str, Any]:
    text = extract_pdf_text(filepath)
    
    position, title, title_cn, difficulty, num = parse_filename(filename)
    
    passage_text, question_groups = split_into_blocks_and_passage(text)
    
    passage_data = parse_passage(passage_text)
    
    q_range_start = min([g["range"][0] for g in question_groups]) if question_groups else (1 if position == "P1" else (14 if position == "P2" else 27))
    q_range_end = max([g["range"][1] for g in question_groups]) if question_groups else (13 if position == "P1" else (26 if position == "P2" else 40))
    
    # Collect derived stats
    types_found = [g["type"] for g in question_groups]
    total_q = sum([(g["range"][1] - g["range"][0] + 1) for g in question_groups])
    
    return {
        "id": f"ielts-r-{num.zfill(3)}",
        "source_file": filename,
        "position": position,
        "question_range": [q_range_start, q_range_end],
        "difficulty": difficulty,
        "title": title,
        "title_cn": title_cn,
        "time_allocation": "20 minutes",
        "passage": passage_data,
        "question_groups": question_groups,
        "metadata": {
            "parsed_total_questions": total_q,
            "question_types": types_found,
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "1.0",
            "needs_review": True
        }
    }

def main():
    input_dir = "/Users/tengda/Antigravity/IELTS/IELTS Reading 130"
    output_dir = "/Users/tengda/Antigravity/IELTS/parsed_raw"
    os.makedirs(output_dir, exist_ok=True)
    
    files = sorted(os.listdir(input_dir))
    
    # Just run on a few to test
    for filename in files:
        if not filename.endswith(".pdf"):
            continue
        print(f"Parsing {filename}...")
        try:
            filepath = os.path.join(input_dir, filename)
            parsed_data = process_file(filepath, filename)
            
            out_name = f"{parsed_data['id']}_raw.json"
            with open(os.path.join(output_dir, out_name), 'w', encoding='utf-8') as out_f:
                json.dump(parsed_data, out_f, ensure_ascii=False, indent=2)
                
            print(f"  -> Saved to {out_name}")
        except Exception as e:
            print(f"  -> Error parsing {filename}: {e}")

if __name__ == "__main__":
    main()

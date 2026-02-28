#!/usr/bin/env python3
"""
extract_og_pdf.py – Extract text from the TOEFL Official Guide PDF to identify
the 6 sample test sets and their structure.

Usage:
    cd /Users/tengda/Antigravity/toefl-2026/backend
    python app/scripts/extract_og_pdf.py
"""
import pymupdf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
PDF_PATH = BASE_DIR / "2026新托福Pack-6.pdf"

doc = pymupdf.open(str(PDF_PATH))
print(f"Total pages: {doc.page_count}")
print("=" * 80)

# Extract text for each page — dump first 300 pages to find structure
for i in range(min(doc.page_count, 400)):
    text = doc[i].get_text()
    # Only print pages that have interesting content markers
    text_lower = text.lower()
    if any(kw in text_lower for kw in [
        "reading section", "practice set", "sample test",
        "reading practice", "test 1", "test 2", "test 3",
        "test 4", "test 5", "test 6", "practice test",
        "reading passage", "reading comprehension",
        "table of contents", "contents"
    ]):
        print(f"\n{'='*80}")
        print(f"PAGE {i+1}")
        print(f"{'='*80}")
        print(text[:2000])
        print("...")

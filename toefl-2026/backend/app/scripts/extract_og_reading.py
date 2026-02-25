#!/usr/bin/env python3
"""
extract_og_reading.py – Extract all 6 Reading Practice Sets + Chapter 6 Reading
from the TOEFL Official Guide PDF and write them as structured JSON files.

Usage:
    cd /Users/tengda/Antigravity/toefl-2026/backend
    /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/python app/scripts/extract_og_reading.py
"""
import pymupdf
import json
from pathlib import Path

PDF_PATH = Path(__file__).resolve().parents[3] / "The Official Guide to the TOEFL iBT Test_ Pocket Edition (Limited Digital Release).pdf"
OUT_DIR = Path(__file__).resolve().parents[3] / "data"

doc = pymupdf.open(str(PDF_PATH))

# Based on TOC:
# Reading Practice Sets: pages 86-127 (6 sets, ~7 pages each)
# Practice Set 1: 86-92, Set 2: 93-99, Set 3: 100-106, Set 4: 107-113, Set 5: 114-120, Set 6: 121-127
# Chapter 6 Practice Test Reading: pages 250-259
# Answers/Explanations: pages 291-337

# Let's dump the reading practice set pages to see the actual structure
print("=" * 80)
print("READING PRACTICE SETS (pages 86-127)")
print("=" * 80)

for page_num in range(85, 127):  # 0-indexed → pages 86-127
    text = doc[page_num].get_text()
    print(f"\n{'─'*80}")
    print(f"PAGE {page_num + 1}")
    print(f"{'─'*80}")
    print(text)

print("\n" + "=" * 80)
print("CHAPTER 6 PRACTICE TEST - READING (pages 250-259)")
print("=" * 80)

for page_num in range(249, 259):  # 0-indexed → pages 250-259
    text = doc[page_num].get_text()
    print(f"\n{'─'*80}")
    print(f"PAGE {page_num + 1}")
    print(f"{'─'*80}")
    print(text)

print("\n" + "=" * 80)
print("ANSWERS & EXPLANATIONS (pages 291-310)")
print("=" * 80)

for page_num in range(290, 310):  # 0-indexed → pages 291-310  
    text = doc[page_num].get_text()
    print(f"\n{'─'*80}")
    print(f"PAGE {page_num + 1}")
    print(f"{'─'*80}")
    print(text)

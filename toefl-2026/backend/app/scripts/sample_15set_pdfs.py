#!/usr/bin/env python3
"""
sample_15set_pdfs.py – Extract first 10 pages of text from representative PDFs
across the 15-set collection to understand their structure.

Usage:
    /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/python app/scripts/sample_15set_pdfs.py
"""
import pymupdf
from pathlib import Path

BASE = Path("/Users/tengda/Antigravity/toefl-2026/2026托福改革新题型官方15套样题合集（截止至2025.12.25）")
OUT = Path("/Users/tengda/Antigravity/toefl-2026/15set_sample_dump.txt")

PDFS = [
    ("TPO Pack-1", BASE / "【6套】2026新托福 TPO 1-6/2026新托福Pack-1/2026新托福Pack-1.pdf"),
    ("Dec Test1 lower", BASE / "【2套】12月增加的2套新题/Test 1/Test 1 - lower level.pdf"),
    ("Dec Test1 upper", BASE / "【2套】12月增加的2套新题/Test 1/Test 1 - upper level M2.pdf"),
    ("Student Sample 1", BASE / "【2套】2026新版托福官方样题-学生用/toefl-ibt-full-length-practice-test-1.pdf"),
    ("Teacher Sample 1", BASE / "【2套】2026新版托福官方样题-教师用（未提供音频）/toefl-ibt-teachers-resources-practice-test-1.pdf"),
    ("Experience Day 1", BASE / "【3套】托福体验日 Test 1-3/TOEFL iBT Experience Day Exclusive Pracitce Test 1.pdf"),
]

with open(OUT, "w", encoding="utf-8") as f:
    for label, pdf_path in PDFS:
        f.write(f"\n{'#'*80}\n")
        f.write(f"# {label}\n")
        f.write(f"# Path: {pdf_path.name}\n")
        if not pdf_path.exists():
            f.write("# FILE NOT FOUND\n")
            continue
        doc = pymupdf.open(str(pdf_path))
        f.write(f"# Total pages: {doc.page_count}\n")
        f.write(f"{'#'*80}\n")
        
        # Show first 15 pages and TOC-like pages
        for i in range(min(doc.page_count, 15)):
            text = doc[i].get_text()
            # Strip DRM watermarks
            clean = "\n".join(
                line for line in text.split("\n")
                if "ebook was issued" not in line
                and "SdkBytes" not in line
                and "Brandy Brandy" not in line
            )
            f.write(f"\n{'='*60}\nPAGE {i+1}\n{'='*60}\n")
            f.write(clean)
        doc.close()

print(f"Dumped to {OUT}")
print(f"Size: {OUT.stat().st_size:,} bytes")

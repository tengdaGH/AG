#!/usr/bin/env python3
"""
extract_og_pdf_v2.py – Dump all pages to a text file for analysis.
"""
import pymupdf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
PDF_PATH = BASE_DIR / "2026新托福Pack-6.pdf"
OUT_PATH = BASE_DIR / "og_pdf_dump.txt"

doc = pymupdf.open(str(PDF_PATH))
print(f"Total pages: {doc.page_count}")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for i in range(doc.page_count):
        text = doc[i].get_text()
        f.write(f"\n{'='*80}\n")
        f.write(f"PAGE {i+1}\n")
        f.write(f"{'='*80}\n")
        f.write(text)

print(f"Dumped to {OUT_PATH}")
print(f"File size: {OUT_PATH.stat().st_size:,} bytes")

#!/usr/bin/env python3
"""
dump_og_pages.py – Dump specific pages from the OG PDF to a text file for analysis.

Usage:
    /Users/tengda/Antigravity/toefl-2026/backend/venv/bin/python app/scripts/dump_og_pages.py
"""
import pymupdf
from pathlib import Path

PDF_PATH = Path(__file__).resolve().parents[3] / "The Official Guide to the TOEFL iBT Test_ Pocket Edition (Limited Digital Release).pdf"
OUT_PATH = Path(__file__).resolve().parents[3] / "og_reading_dump.txt"

doc = pymupdf.open(str(PDF_PATH))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    # Reading Practice Sets: pages 86-127
    for page_num in range(85, 127):
        text = doc[page_num].get_text()
        # Strip the DRM watermark lines
        clean_lines = []
        for line in text.split("\n"):
            if "ebook was issued to" in line or "SdkBytes" in line or "Brandy Brandy 141558475" in line:
                continue
            clean_lines.append(line)
        f.write(f"\n{'='*80}\n")
        f.write(f"PAGE {page_num + 1}\n")
        f.write(f"{'='*80}\n")
        f.write("\n".join(clean_lines))

    # Chapter 6 Practice Test Reading: pages 250-259
    f.write(f"\n\n{'#'*80}\n")
    f.write("CHAPTER 6 PRACTICE TEST - READING\n")
    f.write(f"{'#'*80}\n")
    for page_num in range(249, 259):
        text = doc[page_num].get_text()
        clean_lines = []
        for line in text.split("\n"):
            if "ebook was issued to" in line or "SdkBytes" in line or "Brandy Brandy 141558475" in line:
                continue
            clean_lines.append(line)
        f.write(f"\n{'='*80}\n")
        f.write(f"PAGE {page_num + 1}\n")
        f.write(f"{'='*80}\n")
        f.write("\n".join(clean_lines))

    # Answers/Explanations: pages 291-337
    f.write(f"\n\n{'#'*80}\n")
    f.write("ANSWERS AND EXPLANATIONS\n")
    f.write(f"{'#'*80}\n")
    for page_num in range(290, 337):
        text = doc[page_num].get_text()
        clean_lines = []
        for line in text.split("\n"):
            if "ebook was issued to" in line or "SdkBytes" in line or "Brandy Brandy 141558475" in line:
                continue
            clean_lines.append(line)
        f.write(f"\n{'='*80}\n")
        f.write(f"PAGE {page_num + 1}\n")
        f.write(f"{'='*80}\n")
        f.write("\n".join(clean_lines))

print(f"Dumped to {OUT_PATH}")
print(f"File size: {OUT_PATH.stat().st_size:,} bytes")

#!/usr/bin/env python3
"""
check_pdf_libs.py – Quick check which PDF libraries are available.
Self-destruct after successful execution.
"""
libs = {}
try:
    import pymupdf
    libs["pymupdf"] = True
except ImportError:
    libs["pymupdf"] = False

try:
    import fitz
    libs["fitz"] = True
except ImportError:
    libs["fitz"] = False

try:
    from pdfminer.high_level import extract_text
    libs["pdfminer"] = True
except ImportError:
    libs["pdfminer"] = False

try:
    import PyPDF2
    libs["PyPDF2"] = True
except ImportError:
    libs["PyPDF2"] = False

for k, v in libs.items():
    print(f"  {'✓' if v else '✗'} {k}")

if not any(libs.values()):
    print("\nNo PDF library found. Install one: pip install pymupdf")

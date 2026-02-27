# ============================================================
# Purpose:       Shared utility for identifying ETS-sourced items in the item bank.
# Usage:         from scripts.ets_utils import is_ets_source
# Created:       2026-02-26
# Self-Destruct: No
# ============================================================
"""
ETS Source Detection Utility

ETS-produced materials are the gold standard — they are exempt from content
quality audits. The only check required is parsing integrity (correct
transcription of text, answer keys, distractors, and audio links from the
original PDF).
"""

# Source files that originated from official ETS PDFs
ETS_SOURCE_PREFIXES = ("ets_official_",)

# Legacy HTML files that were parsed from ETS practice materials
LEGACY_ETS_FILES = {
    "toefl-listen-repeat-practice.html",
    "toefl-listening-choose-response-practice.html",
    "toefl-listening-academic-talk-practice.html",
    "toefl-listening-announcement-practice.html",
    "toefl-listening-conversation-practice.html",
}


def is_ets_source(item) -> bool:
    """Check whether an item was parsed from an official ETS source.

    Works with both SQLAlchemy ORM objects (TestItem) and plain dicts.
    Returns True if the item's source_file matches known ETS origins.
    """
    if isinstance(item, dict):
        sf = item.get("source_file", "") or ""
    else:
        sf = getattr(item, "source_file", None) or ""
    return any(sf.startswith(p) for p in ETS_SOURCE_PREFIXES) or sf in LEGACY_ETS_FILES

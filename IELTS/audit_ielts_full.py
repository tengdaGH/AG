#!/usr/bin/env python3
"""
IELTS Reading Item Bank — Full Autonomous Semantic Audit
=========================================================
Scans all 651 items, auto-fixes known patterns, flags items
needing manual review, and produces a markdown audit report.

Usage:
    python3 audit_ielts_full.py              # Apply fixes + generate report
    python3 audit_ielts_full.py --dry-run    # Preview only, no writes

Output:
    IELTS/audit_report.md — Full audit report
"""

import json
import os
import sys
import re
from collections import Counter, defaultdict
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────
BASE_DIR = '/Users/tengda/Antigravity/IELTS/parsed_v2'
REPORT_PATH = '/Users/tengda/Antigravity/IELTS/audit_report.md'
WORKFLOW_PATH = '/Users/tengda/Antigravity/.agent/workflows/audit_ielts_semantic.md'
DRY_RUN = '--dry-run' in sys.argv

KNOWN_Q_TYPES = {
    'MULTIPLE_CHOICE', 'TRUE_FALSE_NOT_GIVEN', 'YES_NO_NOT_GIVEN',
    'SUMMARY_COMPLETION', 'SENTENCE_COMPLETION', 'SHORT_ANSWER_QUESTIONS',
    'MATCHING_HEADINGS', 'MATCHING_FEATURES', 'MATCHING_PARAGRAPH_INFORMATION',
    'MATCHING_SENTENCE_ENDINGS', 'TABLE_COMPLETION', 'FLOW_CHART_COMPLETION',
    'DIAGRAM_LABEL_COMPLETION', 'CLASSIFICATION', 'LABEL_DIAGRAM',
    'MATCHING_INFORMATION',
}

COMPLETION_TYPES = {
    'SUMMARY_COMPLETION', 'SENTENCE_COMPLETION', 'SHORT_ANSWER_QUESTIONS',
    'TABLE_COMPLETION', 'FLOW_CHART_COMPLETION', 'DIAGRAM_LABEL_COMPLETION',
}

TFNG_VALID = {'TRUE', 'FALSE', 'NOT GIVEN'}
YNNG_VALID = {'YES', 'NO', 'NOT GIVEN'}

# Fuzzy corrections for common raw-key typos
TFNG_FUZZY = {
    'TRE': 'TRUE', 'TURE': 'TRUE', 'TREU': 'TRUE', 'TRUR': 'TRUE',
    'FLSE': 'FALSE', 'FASLE': 'FALSE', 'FALES': 'FALSE', 'FLASE': 'FALSE',
    'NOT': 'NOT GIVEN', 'NOTGIVEN': 'NOT GIVEN', 'NOT  GIVEN': 'NOT GIVEN',
}
YNNG_FUZZY = {
    'YSE': 'YES', 'YSE': 'YES', 'YE': 'YES',
    'NQ': 'NO',
    'NOT': 'NOT GIVEN', 'NOTGIVEN': 'NOT GIVEN', 'NOT  GIVEN': 'NOT GIVEN',
}


# ── Helpers ────────────────────────────────────────────────────
def get_questions(group):
    """Get question items from a group (handles both 'items' and 'questions' keys)."""
    return group.get('items', group.get('questions', []))


def get_answer(item):
    """Get answer from a question item (handles both 'answer' and 'correct_answer')."""
    return item.get('answer', item.get('correct_answer', ''))


def set_answer(item, value):
    """Set answer on a question item."""
    if 'answer' in item:
        item['answer'] = value
    elif 'correct_answer' in item:
        item['correct_answer'] = value
    else:
        item['answer'] = value


def get_passage_text(data):
    """Extract full passage text from item."""
    paras = data.get('content', {}).get('paragraphs', [])
    parts = []
    for p in paras:
        if isinstance(p, dict):
            parts.append(p.get('content', ''))
        else:
            parts.append(str(p))
    return ' '.join(parts).lower()


def clean_completion_answer(answer):
    """Clean a completion answer for passage-text matching.
    Handles alternatives like 'word1// word2' and parenthetical like '(the) answer'.
    """
    # Split on // and take alternatives
    alternatives = [a.strip() for a in answer.split('//')]
    cleaned = []
    for alt in alternatives:
        # Remove parenthetical optional words: "(the) answer" → "answer" and "the answer"
        if '(' in alt and ')' in alt:
            without = re.sub(r'\([^)]*\)\s*', '', alt).strip()
            with_parens = re.sub(r'[()]', '', alt).strip()
            cleaned.extend([without.lower(), with_parens.lower()])
        else:
            cleaned.append(alt.lower())
    return cleaned


# ── Fix Rules ──────────────────────────────────────────────────

class AuditEngine:
    def __init__(self):
        self.fixes = defaultdict(list)       # fid → [(rule, detail)]
        self.flags = defaultdict(list)       # fid → [(category, detail)]
        self.modified_files = set()
        self.titles = Counter()
        self.slugs = Counter()
        self.title_to_ids = defaultdict(list)
        self.stats = Counter()

    def audit_item(self, fid, data, fsize):
        """Run all checks on a single item. Returns True if data was modified."""
        modified = False
        title = data.get('title', '')
        self.titles[title] += 1
        self.title_to_ids[title].append(fid)
        self.slugs[data.get('slug', '')] += 1

        content = data.get('content', {})
        paras = content.get('paragraphs', [])
        has_labels = content.get('has_paragraph_labels', False)
        passage_text = get_passage_text(data)

        qs = data.get('questions', {})
        groups = qs.get('question_groups', []) if isinstance(qs, dict) else []
        total_parsed = qs.get('parsed_total_questions', 0) if isinstance(qs, dict) else 0
        raw_key = data.get('raw_answer_key', {})

        # Count actual questions
        actual_q_count = 0
        all_numbers = []
        for g in groups:
            q_items = get_questions(g)
            actual_q_count += len(q_items)
            for item in q_items:
                n = item.get('number')
                if n is not None:
                    all_numbers.append(int(n))

        # ── Flag: Tiny file ──
        if fsize < 3500:
            self.flags[fid].append(('TINY_FILE', f'{fsize} bytes — likely incomplete extraction'))
            self.stats['flag_tiny'] += 1

        # ── Flag: Missing title ──
        if not title:
            self.flags[fid].append(('NO_TITLE', 'Missing title field'))
            self.stats['flag_no_title'] += 1

        # ── Flag: Short passage ──
        total_chars = sum(len(p.get('content', '') if isinstance(p, dict) else str(p)) for p in paras)
        if total_chars < 200:
            self.flags[fid].append(('SHORT_PASSAGE', f'{total_chars} chars'))
            self.stats['flag_short_passage'] += 1

        # ── Flag: No question groups ──
        if not groups:
            self.flags[fid].append(('NO_QUESTIONS', 'No question_groups found'))
            self.stats['flag_no_questions'] += 1

        # ── Flag: Unknown question types ──
        for g in groups:
            qtype = g.get('type', '')
            if qtype not in KNOWN_Q_TYPES:
                self.flags[fid].append(('UNKNOWN_Q_TYPE', qtype))
                self.stats['flag_unknown_type'] += 1

        # ── Flag: Q count mismatch ──
        if total_parsed and actual_q_count != total_parsed:
            self.flags[fid].append(('Q_COUNT_MISMATCH', f'parsed={total_parsed} actual={actual_q_count}'))
            self.stats['flag_q_count'] += 1

        # ── Flag: Question numbering gaps ──
        if all_numbers:
            expected = list(range(min(all_numbers), max(all_numbers) + 1))
            if sorted(all_numbers) != expected:
                missing = sorted(set(expected) - set(all_numbers))
                self.flags[fid].append(('Q_NUMBER_GAP', f'Missing: {missing[:10]}'))
                self.stats['flag_q_gap'] += 1

        # ── Rule 1: Raw answer key alignment ──
        if raw_key:
            for g in groups:
                q_items = get_questions(g)
                for item in q_items:
                    qnum = str(item.get('number', ''))
                    q_ans = get_answer(item)
                    raw_ans = raw_key.get(qnum, '')
                    if q_ans and raw_ans and str(q_ans) != str(raw_ans):
                        # Check if raw key contains the answer as prefix (trailing text)
                        if str(raw_ans).startswith(str(q_ans)):
                            old = raw_key[qnum]
                            raw_key[qnum] = str(q_ans)
                            self.fixes[fid].append(('RAW_KEY_TRIM', f'Q{qnum}: "{old}" → "{q_ans}"'))
                            self.stats['fix_raw_key_trim'] += 1
                            modified = True
                        # Check if answer contains raw key (raw key is truncated)
                        elif str(q_ans).startswith(str(raw_ans)) and len(raw_ans) < len(q_ans):
                            old = raw_key[qnum]
                            raw_key[qnum] = str(q_ans)
                            self.fixes[fid].append(('RAW_KEY_EXTEND', f'Q{qnum}: "{old}" → "{q_ans}"'))
                            self.stats['fix_raw_key_extend'] += 1
                            modified = True

        # ── Rule 2: T/F/NG ↔ Y/N/NG type correction ──
        for g in groups:
            qtype = g.get('type', '')
            q_items = get_questions(g)
            answers = [get_answer(item) for item in q_items]
            answers_set = set(a for a in answers if a)

            if qtype == 'TRUE_FALSE_NOT_GIVEN':
                if answers_set & {'YES', 'NO'} and not answers_set & {'TRUE', 'FALSE'}:
                    g['type'] = 'YES_NO_NOT_GIVEN'
                    self.fixes[fid].append(('TYPE_TFNG_TO_YNNG', f'Answers use YES/NO'))
                    self.stats['fix_type_correction'] += 1
                    modified = True
            elif qtype == 'YES_NO_NOT_GIVEN':
                if answers_set & {'TRUE', 'FALSE'} and not answers_set & {'YES', 'NO'}:
                    g['type'] = 'TRUE_FALSE_NOT_GIVEN'
                    self.fixes[fid].append(('TYPE_YNNG_TO_TFNG', f'Answers use TRUE/FALSE'))
                    self.stats['fix_type_correction'] += 1
                    modified = True

        # ── Rule 3: Raw key typo correction ──
        for g in groups:
            qtype = g.get('type', '')
            q_items = get_questions(g)

            if qtype in ('TRUE_FALSE_NOT_GIVEN', 'YES_NO_NOT_GIVEN'):
                valid = TFNG_VALID if qtype == 'TRUE_FALSE_NOT_GIVEN' else YNNG_VALID
                fuzzy = TFNG_FUZZY if qtype == 'TRUE_FALSE_NOT_GIVEN' else YNNG_FUZZY

                for item in q_items:
                    qnum = str(item.get('number', ''))
                    ans = get_answer(item)

                    # Check raw key
                    if qnum in raw_key:
                        rk = raw_key[qnum].strip()
                        if rk not in valid:
                            upper_rk = rk.upper().strip()
                            if upper_rk in fuzzy:
                                corrected = fuzzy[upper_rk]
                                self.fixes[fid].append(('RAW_KEY_TYPO', f'Q{qnum}: "{rk}" → "{corrected}"'))
                                raw_key[qnum] = corrected
                                self.stats['fix_raw_key_typo'] += 1
                                modified = True

                    # Check question answer
                    if ans and ans not in valid:
                        upper_ans = ans.upper().strip()
                        # Try fuzzy
                        if upper_ans in fuzzy:
                            corrected = fuzzy[upper_ans]
                            self.fixes[fid].append(('ANS_TYPO', f'Q{qnum}: "{ans}" → "{corrected}"'))
                            set_answer(item, corrected)
                            self.stats['fix_ans_typo'] += 1
                            modified = True

        # ── Rule 4: Paragraph label deduplication ──
        if has_labels and paras:
            labels = [p.get('label', '') for p in paras if isinstance(p, dict)]
            label_counts = Counter(labels)
            num_unique = len(set(l for l in labels if l))
            dups = [l for l, c in label_counts.items() if c > 1 and l]

            if dups:
                # Case 1: Multi-paragraph sections (e.g., 14 paras with 5 sections)
                # If unique labels < total paras by a lot, it's intentional sub-sections
                if num_unique < len(paras) * 0.7:
                    self.flags[fid].append(('LABEL_MULTI_PARA_SECTIONS',
                        f'{len(paras)} paras with {num_unique} unique labels ({dups}) — intentional sub-sections'))
                    self.stats['flag_label_sections'] += 1
                else:
                    # Case 2: Simple label errors (e.g., A,B,B,E → A,B,C,D)
                    # Only fix if total paragraph count <= 26 (max labels A-Z)
                    if len(paras) <= 26:
                        new_labels = [chr(ord('A') + i) for i in range(len(paras))]
                        old_labels = labels[:]
                        for i, p in enumerate(paras):
                            if isinstance(p, dict):
                                p['label'] = new_labels[i]
                        self.fixes[fid].append(('LABEL_RESEQUENCE',
                            f'{old_labels} → {new_labels}'))
                        self.stats['fix_label_resequence'] += 1
                        modified = True
            else:
                # Check for non-sequential labels even without duplicates
                non_empty = [l for l in labels if l]
                for i, l in enumerate(non_empty):
                    expected = chr(ord('A') + i)
                    if l != expected:
                        # Check if labels are numeric (1, 2, 3...) instead of letters
                        if all(x.isdigit() for x in non_empty if x):
                            self.flags[fid].append(('LABEL_NUMERIC',
                                f'Uses numeric labels: {non_empty[:5]}'))
                            self.stats['flag_label_numeric'] += 1
                        else:
                            self.flags[fid].append(('LABEL_NON_SEQUENTIAL',
                                f'Labels: {non_empty[:8]}'))
                            self.stats['flag_label_nonseq'] += 1
                        break

        # ── Rule 5: Completion answer verification ──
        if passage_text:
            for g in groups:
                qtype = g.get('type', '')
                if qtype in COMPLETION_TYPES:
                    q_items = get_questions(g)
                    for item in q_items:
                        ans = get_answer(item)
                        if not ans:
                            continue
                        alternatives = clean_completion_answer(ans)
                        found = any(alt in passage_text for alt in alternatives if len(alt) > 2)
                        if not found and len(ans) > 2:
                            # Don't flag very short answers (single letters, numbers)
                            self.flags[fid].append(('COMPLETION_NOT_IN_PASSAGE',
                                f'Q{item.get("number","")}: "{ans}" not found in passage'))
                            self.stats['flag_completion_missing'] += 1

        # ── Rule 6: MCQ answer validity ──
        for g in groups:
            qtype = g.get('type', '')
            if qtype == 'MULTIPLE_CHOICE':
                q_items = get_questions(g)
                for item in q_items:
                    ans = get_answer(item)
                    opts = item.get('options', [])
                    if opts and ans:
                        opt_labels = {o.get('label', '') for o in opts}
                        # Skip multi-select answers like "B OR E IN EITHER ORDER"
                        if ' OR ' in str(ans) or 'EITHER ORDER' in str(ans) or 'ANY ORDER' in str(ans):
                            continue
                        elif ans not in opt_labels:
                            self.flags[fid].append(('MCQ_INVALID_ANS',
                                f'Q{item.get("number","")}: "{ans}" not in {opt_labels}'))
                            self.stats['flag_mcq_invalid'] += 1

        # ── Remaining raw key ↔ answer alignment (post other fixes) ──
        if raw_key:
            for g in groups:
                q_items = get_questions(g)
                for item in q_items:
                    qnum = str(item.get('number', ''))
                    q_ans = get_answer(item)
                    raw_ans = raw_key.get(qnum, '')
                    if q_ans and raw_ans and str(q_ans) != str(raw_ans):
                        self.flags[fid].append(('ANS_MISMATCH',
                            f'Q{qnum}: item="{q_ans}" raw="{raw_ans}"'))
                        self.stats['flag_ans_mismatch'] += 1

        return modified

    def check_duplicates(self):
        """Check for duplicate titles and passages after scanning all items."""
        for title, count in self.titles.items():
            if count > 1 and title:
                ids = self.title_to_ids[title]
                self.flags['GLOBAL'].append(('DUPLICATE_TITLE',
                    f'"{title}" appears {count} times: {ids}'))
                self.stats['flag_duplicate_title'] += 1

    def generate_report(self):
        """Generate the markdown audit report."""
        total_items = sum(self.titles.values())
        items_fixed = len(self.modified_files)
        items_flagged = len([fid for fid in self.flags if fid != 'GLOBAL' and self.flags[fid]])
        items_clean = total_items - len(set(list(self.modified_files) +
                      [fid for fid in self.flags if fid != 'GLOBAL' and self.flags[fid]]))

        lines = [
            f'# IELTS Reading Item Bank — Audit Report',
            f'',
            f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            f'**Mode:** {"DRY RUN (no files modified)" if DRY_RUN else "LIVE (fixes applied)"}',
            f'',
            f'## Summary',
            f'',
            f'| Metric | Count |',
            f'|---|---|',
            f'| Total items scanned | {total_items} |',
            f'| Items auto-fixed | {items_fixed} |',
            f'| Items flagged for review | {items_flagged} |',
            f'| Items clean | {items_clean} |',
            f'',
        ]

        # Fix stats
        lines.append('## Fix Statistics')
        lines.append('')
        lines.append('| Rule | Count |')
        lines.append('|---|---|')
        fix_keys = sorted([k for k in self.stats if k.startswith('fix_')])
        for k in fix_keys:
            lines.append(f'| {k.replace("fix_", "").replace("_", " ").title()} | {self.stats[k]} |')
        lines.append('')

        # Flag stats
        lines.append('## Flag Statistics')
        lines.append('')
        lines.append('| Category | Count |')
        lines.append('|---|---|')
        flag_keys = sorted([k for k in self.stats if k.startswith('flag_')])
        for k in flag_keys:
            lines.append(f'| {k.replace("flag_", "").replace("_", " ").title()} | {self.stats[k]} |')
        lines.append('')

        # Detailed fixes
        if self.fixes:
            lines.append('---')
            lines.append('')
            lines.append('## Auto-Fixes Applied')
            lines.append('')
            for fid in sorted(self.fixes.keys()):
                fx = self.fixes[fid]
                lines.append(f'### {fid}')
                for rule, detail in fx:
                    lines.append(f'- **{rule}**: {detail}')
                lines.append('')

        # Detailed flags
        flagged_items = {fid: fl for fid, fl in self.flags.items()
                        if fl and fid != 'GLOBAL'}
        if flagged_items:
            lines.append('---')
            lines.append('')
            lines.append('## Flagged Items (Manual Review Recommended)')
            lines.append('')

            # Group by category
            by_cat = defaultdict(list)
            for fid, fl_list in flagged_items.items():
                for cat, detail in fl_list:
                    by_cat[cat].append((fid, detail))

            for cat in sorted(by_cat.keys()):
                entries = by_cat[cat]
                lines.append(f'### {cat} ({len(entries)})')
                lines.append('')
                for fid, detail in entries[:50]:
                    lines.append(f'- **{fid}**: {detail}')
                if len(entries) > 50:
                    lines.append(f'- *… and {len(entries) - 50} more*')
                lines.append('')

        # Global flags
        if self.flags.get('GLOBAL'):
            lines.append('### Global Issues')
            lines.append('')
            for cat, detail in self.flags['GLOBAL']:
                lines.append(f'- **{cat}**: {detail}')
            lines.append('')

        return '\n'.join(lines)


# ── Main ───────────────────────────────────────────────────────
def main():
    engine = AuditEngine()
    files = sorted(f for f in os.listdir(BASE_DIR) if f.endswith('.json'))

    print(f'IELTS Semantic Audit — {"DRY RUN" if DRY_RUN else "LIVE"} mode')
    print(f'Scanning {len(files)} items in {BASE_DIR}')
    print()

    for fname in files:
        path = os.path.join(BASE_DIR, fname)
        fsize = os.path.getsize(path)

        with open(path) as f:
            data = json.load(f)

        fid = data.get('id', fname.replace('.json', ''))
        modified = engine.audit_item(fid, data, fsize)

        if modified:
            engine.modified_files.add(fid)
            if not DRY_RUN:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

    # Check for duplicates across all items
    engine.check_duplicates()

    # Generate report
    report = engine.generate_report()
    with open(REPORT_PATH, 'w') as f:
        f.write(report)

    # Print summary
    print(f'✅ Scan complete')
    print(f'   Items scanned:  {len(files)}')
    print(f'   Items fixed:    {len(engine.modified_files)}')
    print(f'   Items flagged:  {len([f for f in engine.flags if f != "GLOBAL" and engine.flags[f]])}')
    print(f'   Report:         {REPORT_PATH}')
    print()

    if DRY_RUN:
        print('ℹ️  DRY RUN — no files were modified. Run without --dry-run to apply fixes.')
    else:
        print(f'📝 {len(engine.modified_files)} files modified.')

    # Print fix/flag breakdown
    for k in sorted(engine.stats):
        print(f'   {k}: {engine.stats[k]}')


if __name__ == '__main__':
    main()

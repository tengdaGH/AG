"""
Transcript Processor — 5-phase pipeline for processing teaching transcripts.

Architecture: This module handles Notion CRUD operations for each phase.
The AI analysis (transcript → structured notes) is performed by Antigravity
directly (internal compute), not by an external API.

Phases:
  0: Date validation — find target Session page in 课表
  1: Structured notes — write 10-module content to Session page
  2: Transcript backup — save raw transcript to Session page field
  3: Teaching quality — create entry in 教学质量跟踪
  4: Student tracking — create entries in 学情记录
"""

import json
import traceback
from datetime import datetime

import notion_api as notion
from config import (
    TRIGGER_DB, SCHEDULE_DB, QUALITY_DB, TRACKING_DB,
    STATUS_PENDING, STATUS_PROCESSING, STATUS_DONE,
)


# ═══════════════════════════════════════════════════════════════════════
# Phase 0: Date Validation
# ═══════════════════════════════════════════════════════════════════════

def phase0_find_session(date_str: str) -> dict | None:
    """
    Query 小楷课表 for a Session page matching the given date.
    Uses query-data-source (database query), never search.
    Returns the first matching Session page, or None.
    """
    print(f"  [Phase 0] Looking for session on date: {date_str}")

    results = notion.query_database(
        SCHEDULE_DB,
        filter={
            "property": "Date/Period",
            "date": {"equals": date_str}
        }
    )

    if results:
        session = results[0]
        title_parts = session["properties"].get("Session", {}).get("title", [])
        title = "".join(t.get("plain_text", "") for t in title_parts)
        print(f"  [Phase 0] ✅ Found session: {title} (ID: {session['id']})")
        return session
    else:
        print(f"  [Phase 0] ⚠️  No session found for {date_str}")
        return None


# ═══════════════════════════════════════════════════════════════════════
# Phase 1: Structured Notes → Session Page
# ═══════════════════════════════════════════════════════════════════════

def phase1_write_notes(session_page_id: str, structured_data: dict):
    """
    Write the structured notes (10 modules) to the target Session page.
    structured_data is a dict matching the output schema from the AI analysis.
    Content is written as Notion blocks.
    """
    print(f"  [Phase 1] Writing structured notes to session page: {session_page_id}")

    blocks = _build_note_blocks(structured_data)

    # Write in batches of 5 blocks to prevent JSON overflow
    for i in range(0, len(blocks), 5):
        batch = blocks[i:i + 5]
        notion.append_blocks(session_page_id, batch)
        print(f"  [Phase 1] Wrote blocks {i+1}-{i+len(batch)} of {len(blocks)}")

    # Update Session page properties
    updates = {}
    if structured_data.get("class_content_summary"):
        updates["Class content"] = {
            "rich_text": [{"text": {"content": structured_data["class_content_summary"][:2000]}}]
        }
    if structured_data.get("performance"):
        updates["Performance(教师填)"] = {
            "select": {"name": structured_data["performance"]}
        }
    if updates:
        notion.update_page(session_page_id, updates)

    print(f"  [Phase 1] ✅ Structured notes written ({len(blocks)} blocks)")


def _build_note_blocks(data: dict) -> list:
    """Convert structured data dict into Notion block objects."""
    blocks = []

    # ── Header ──
    blocks.append(_heading2("📘 课堂笔记"))

    # Student + highlights
    if data.get("student_name"):
        blocks.append(_callout(f"学员：{data['student_name']}", "📘", "blue_background"))
    if data.get("highlights"):
        blocks.append(_callout(f"本次课亮点表现\n{data['highlights']}", "✅", "green_background"))

    # ── Module 1: Materials ──
    if data.get("materials"):
        blocks.append(_heading3("一、本节课用了哪些材料"))
        for m in data["materials"]:
            blocks.append(_bullet(f"**{m['name']}**：{m.get('description', '')}"))

    # ── Module 2: Student Output ──
    if data.get("student_output"):
        blocks.append(_heading3("二、学生课堂输出"))
        for i, ex in enumerate(data["student_output"], 1):
            blocks.append(_callout(
                f"练习{i}｜{ex.get('exercise_name', '未命名')}\n{ex.get('student_answer', '')}",
                "🧲", "gray_background"
            ))

    # ── Module 3: Teacher Demo + Vocabulary ──
    if data.get("teacher_demo"):
        blocks.append(_heading3("三、老师示范 + 重点词汇"))
        for demo in data["teacher_demo"]:
            blocks.append(_callout(
                f"{demo.get('template_name', '示范')}\n{demo.get('full_text', '')}",
                "🧠", "blue_background"
            ))
            if demo.get("vocabulary_upgrades"):
                blocks.append(_quote("💡 **高级替换技巧**（词汇升级）："))
                for v in demo["vocabulary_upgrades"]:
                    blocks.append(_quote(
                        f"- **{v['basic']}** → **{v['advanced']}**（{v.get('level', '')}）"
                    ))

    # ── Module 4: Error Corrections ──
    if data.get("error_corrections"):
        blocks.append(_heading3("四、本节课纠错"))
        # Build table
        header = ["原句", "错误类型", "修正", "规则", "同类易错", "记忆技巧"]
        rows = []
        for ec in data["error_corrections"]:
            rows.append([
                ec.get("original", ""),
                ec.get("error_type", ""),
                ec.get("correction", ""),
                ec.get("rule", ""),
                ec.get("similar_examples", ""),
                ec.get("memory_tip", ""),
            ])
        blocks.extend(_table(header, rows))

    # ── Module 4.5: Final Essay (writing only) ──
    if data.get("final_essay"):
        blocks.append(_heading3("四½、定稿作文（仅写作课）"))
        blocks.append(_callout(
            f"⚠️ 仅在写作课逐字稿中输出本模块\n\n{data['final_essay']}",
            "✍️", "green_background"
        ))

    # ── Module 5: Homework ──
    if data.get("homework"):
        blocks.append(_heading3("五、课后任务"))
        blocks.append(_callout(
            "\n".join(f"• {h}" for h in data["homework"]),
            "📝", "orange_background"
        ))

    # ── Module 6: Teacher Quotes ──
    if data.get("teacher_quotes"):
        blocks.append(_heading3("六、老师金句"))
        for q in data["teacher_quotes"]:
            blocks.append(_quote(f"💡 \"{q}\""))

    # ── Module 7: Mindset Analysis ──
    if data.get("mindset_analysis"):
        blocks.append(_heading3("七、学习心态分析"))
        ma = data["mindset_analysis"]
        parts = []
        if ma.get("engagement"): parts.append(f"• **课堂参与度**：{ma['engagement']}")
        if ma.get("confidence"): parts.append(f"• **自信心**：{ma['confidence']}")
        if ma.get("patterns"): parts.append(f"• **行为模式**：{ma['patterns']}")
        if ma.get("emotional_state"): parts.append(f"• **情绪状态**：{ma['emotional_state']}")
        blocks.append(_callout("\n".join(parts), "🧠", "pink_background"))

    # ── Module 8: Supplementary Vocab ──
    if data.get("supplementary_vocab"):
        blocks.append(_heading3("八、补充词汇"))
        header = ["生词/短语", "释义", "例句"]
        rows = [[v["word"], v["meaning"], v.get("example", "")] for v in data["supplementary_vocab"]]
        blocks.extend(_table(header, rows))

    # ── Module 9: Additional Content ──
    if data.get("additional_content"):
        blocks.append(_heading3("九、其他补充内容"))
        for item in data["additional_content"]:
            blocks.append(_bullet(item))

    # ── Module 10: Method Summary ──
    if data.get("method_summary"):
        blocks.append(_heading3("十、方法总结"))
        for m in data["method_summary"]:
            blocks.append(_paragraph(f"**方法｜{m['name']}**"))
            if m.get("when_to_use"): blocks.append(_bullet(f"**什么时候用**：{m['when_to_use']}"))
            if m.get("how_to"): blocks.append(_bullet(f"**怎么操作**：{m['how_to']}"))
            if m.get("example"): blocks.append(_bullet(f"**举例**：{m['example']}"))
            if m.get("caution"): blocks.append(_bullet(f"**注意**：{m['caution']}"))

    return blocks


# ═══════════════════════════════════════════════════════════════════════
# Phase 2: Transcript Backup
# ═══════════════════════════════════════════════════════════════════════

def phase2_backup_transcript(session_page_id: str, raw_transcript: str):
    """
    Save the raw transcript text to the Session page's 逐字稿 field.
    """
    print(f"  [Phase 2] Backing up transcript to session page")

    # Notion rich_text has a 2000 char limit per element
    chunks = [raw_transcript[i:i+2000] for i in range(0, len(raw_transcript), 2000)]
    rich_text = [{"text": {"content": chunk}} for chunk in chunks]

    notion.update_page(session_page_id, {
        "逐字稿": {"rich_text": rich_text}
    })

    print(f"  [Phase 2] ✅ Transcript backed up ({len(raw_transcript)} chars)")


# ═══════════════════════════════════════════════════════════════════════
# Phase 3: Teaching Quality Feedback → 教学质量跟踪
# ═══════════════════════════════════════════════════════════════════════

def phase3_teaching_quality(trigger_meta: dict, structured_data: dict):
    """
    Create an entry in 教学质量跟踪 with teaching quality analysis.
    """
    print(f"  [Phase 3] Writing teaching quality feedback")

    tq = structured_data.get("teaching_quality", {})
    student = trigger_meta.get("student", "")
    teacher = trigger_meta.get("teacher", "")
    subject = trigger_meta.get("subject", "")
    exam = trigger_meta.get("exam", "")
    date = trigger_meta.get("date", "")

    title = f"{student}-{teacher}-{subject}-{date}-教学反馈"

    properties = {
        "记录标题": {"title": [{"text": {"content": title}}]},
        "正面评价": {"rich_text": [{"text": {"content": tq.get("highlights", "暂无")[:2000]}}]},
        "负面评价": {"rich_text": [{"text": {"content": tq.get("improvements", "暂无")[:2000]}}]},
        "改进建议": {"rich_text": [{"text": {"content": _format_improvements(tq)[:2000]}}]},
    }

    # Optional selects
    if teacher:
        properties["教师"] = {"select": {"name": teacher}}
    if subject:
        properties["科目"] = {"select": {"name": subject}}
    if exam:
        properties["考试"] = {"select": {"name": exam}}

    page = notion.create_page(
        parent={"database_id": QUALITY_DB},
        properties=properties,
    )

    print(f"  [Phase 3] ✅ Teaching quality entry created: {page['id']}")
    return page


def _format_improvements(tq: dict) -> str:
    """Format teaching quality scores and language errors into text."""
    parts = []
    scores = tq.get("scores", {})
    if scores:
        parts.append("评分：")
        for k, v in scores.items():
            parts.append(f"  {k}: {v}")

    errors = tq.get("language_errors", [])
    if errors:
        parts.append("\n老师语言错误：")
        for e in errors:
            parts.append(f"  ❌ {e.get('error', '')} → ✅ {e.get('correction', '')}（{e.get('context', '')}）")

    return "\n".join(parts) if parts else "暂无具体建议"


# ═══════════════════════════════════════════════════════════════════════
# Phase 4: Student Tracking → 学情记录
# ═══════════════════════════════════════════════════════════════════════

def phase4_student_tracking(trigger_meta: dict, structured_data: dict):
    """
    Create entries in 学情记录 for student performance observations.
    Positive and negative observations are recorded as separate entries.
    """
    print(f"  [Phase 4] Writing student tracking records")

    st = structured_data.get("student_tracking", {})
    student = trigger_meta.get("student", "")
    teacher = trigger_meta.get("teacher", "")
    subject = trigger_meta.get("subject", "")

    entries_created = 0

    # Positive observations
    for note in st.get("positive_notes", []):
        title = f"{student}-{teacher}-{subject}-👌-{note[:30]}"
        notion.create_page(
            parent={"database_id": TRACKING_DB},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "学员关联": {"rich_text": [{"text": {"content": student}}]},
                "Status": {"select": {"name": "Excellent 🚀"}},
                "Updates": {"rich_text": [{"text": {"content": note[:2000]}}]},
                "Solution ": {"rich_text": [{"text": {"content": "继续保持"}}]},
            },
        )
        entries_created += 1

    # Negative observations
    for note in st.get("negative_notes", []):
        title = f"{student}-{teacher}-{subject}-⚠️-{note[:30]}"
        solution = st.get("skills_progress", "需要进一步跟进")
        notion.create_page(
            parent={"database_id": TRACKING_DB},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "学员关联": {"rich_text": [{"text": {"content": student}}]},
                "Status": {"select": {"name": "Caution ⚠️"}},
                "Updates": {"rich_text": [{"text": {"content": note[:2000]}}]},
                "Solution ": {"rich_text": [{"text": {"content": solution[:2000]}}]},
            },
        )
        entries_created += 1

    print(f"  [Phase 4] ✅ Created {entries_created} student tracking entries")


# ═══════════════════════════════════════════════════════════════════════
# Status Management
# ═══════════════════════════════════════════════════════════════════════

def update_trigger_status(page_id: str, status: str):
    """Update the 清洗状态 of a trigger entry."""
    notion.update_page(page_id, {
        "清洗状态": {"status": {"name": status}}
    })
    print(f"  [Status] Updated trigger entry to: {status}")


def extract_trigger_metadata(page: dict) -> dict:
    """Extract key metadata from a trigger entry's properties."""
    props = page.get("properties", {})

    def _text(prop_name):
        prop = props.get(prop_name, {})
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", []))
        elif prop.get("type") == "rich_text":
            return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
        return ""

    def _select(prop_name):
        prop = props.get(prop_name, {})
        sel = prop.get("select", {})
        return sel.get("name", "") if sel else ""

    def _multi_select(prop_name):
        prop = props.get(prop_name, {})
        return [o.get("name", "") for o in prop.get("multi_select", [])]

    def _date(prop_name):
        prop = props.get(prop_name, {})
        d = prop.get("date", {})
        return d.get("start", "") if d else ""

    return {
        "title": _text("课程名称"),
        "date": _date("日期"),
        "student": ", ".join(_multi_select("学生")),
        "teacher": ", ".join(_multi_select("教师")),
        "subject": _select("科目"),
        "exam": _select("考试类型"),
        "summary": _text("摘要"),
    }


# ═══════════════════════════════════════════════════════════════════════
# Notion Block Builders
# ═══════════════════════════════════════════════════════════════════════

def _rich_text(text: str) -> list:
    """Build rich_text array, handling bold markers (**)."""
    parts = []
    import re
    segments = re.split(r'(\*\*.*?\*\*)', text)
    for seg in segments:
        if seg.startswith('**') and seg.endswith('**'):
            parts.append({
                "type": "text",
                "text": {"content": seg[2:-2]},
                "annotations": {"bold": True}
            })
        elif seg:
            parts.append({"type": "text", "text": {"content": seg}})
    return parts


def _heading2(text: str) -> dict:
    return {"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}}


def _heading3(text: str) -> dict:
    return {"type": "heading_3", "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": _rich_text(text)}}


def _bullet(text: str) -> dict:
    return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rich_text(text)}}


def _quote(text: str) -> dict:
    return {"type": "quote", "quote": {"rich_text": _rich_text(text)}}


def _callout(text: str, emoji: str = "💡", color: str = "gray_background") -> dict:
    return {
        "type": "callout",
        "callout": {
            "rich_text": _rich_text(text),
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
        }
    }


def _table(headers: list, rows: list) -> list:
    """Build a Notion table block with header row and data rows."""
    table_rows = []

    # Header row
    table_rows.append({
        "type": "table_row",
        "table_row": {
            "cells": [[{"type": "text", "text": {"content": h}}] for h in headers]
        }
    })

    # Data rows
    for row in rows:
        table_rows.append({
            "type": "table_row",
            "table_row": {
                "cells": [[{"type": "text", "text": {"content": str(cell)}}] for cell in row]
            }
        })

    return [{
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows,
        }
    }]

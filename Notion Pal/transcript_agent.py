#!/usr/bin/env python3
"""
Autonomous Notion Transcript Agent

Polls 教学逐字稿记录 for entries with 清洗状态 = 待清洗,
reads the raw transcript, and executes the 5-phase processing pipeline.

The AI analysis step (transcript → structured notes) is designed to be
performed by Antigravity's internal compute. This script handles the
Notion CRUD orchestration.

Usage:
  # Single-shot: process all pending entries once
  python transcript_agent.py --once

  # Polling mode: check every 30 seconds
  python transcript_agent.py

  # Process a specific entry by page ID
  python transcript_agent.py --page-id <PAGE_ID>

  # Create test data for verification
  python transcript_agent.py --create-test
"""

import argparse
import json
import sys
import time
import traceback
from datetime import datetime

import notion_api as notion
from config import (
    TRIGGER_DB, SCHEDULE_DB, QUALITY_DB, TRACKING_DB,
    STATUS_PENDING, STATUS_PROCESSING, STATUS_DONE,
    POLL_INTERVAL_SECONDS,
)
from transcript_processor import (
    phase0_find_session,
    phase1_write_notes,
    phase2_backup_transcript,
    phase3_teaching_quality,
    phase4_student_tracking,
    update_trigger_status,
    extract_trigger_metadata,
)


def find_pending_entries() -> list:
    """Query the trigger database for entries with 清洗状态 = 待清洗."""
    results = notion.query_database(
        TRIGGER_DB,
        filter={
            "property": "清洗状态",
            "status": {"equals": STATUS_PENDING}
        }
    )
    print(f"Found {len(results)} pending entries")
    return results


def read_transcript(page_id: str) -> str:
    """Read the raw transcript text from a trigger entry's page body."""
    return notion.get_page_text(page_id)


def process_entry(page: dict, structured_data: dict = None):
    """
    Process a single trigger entry through the 5-phase pipeline.

    If structured_data is provided, skip AI analysis and use it directly.
    If not provided, read transcript and output it for external processing.
    """
    page_id = page["id"]
    meta = extract_trigger_metadata(page)

    print(f"\n{'='*60}")
    print(f"Processing: {meta['title']}")
    print(f"  Student: {meta['student']}")
    print(f"  Subject: {meta['subject']}")
    print(f"  Date: {meta['date']}")
    print(f"  Teacher: {meta['teacher']}")
    print(f"  Exam: {meta['exam']}")
    print(f"{'='*60}")

    # Lock the entry
    update_trigger_status(page_id, STATUS_PROCESSING)

    try:
        # Read raw transcript
        raw_transcript = read_transcript(page_id)
        print(f"\n  Raw transcript length: {len(raw_transcript)} chars")

        if not structured_data:
            # No AI data provided — output transcript for external processing
            print("\n" + "="*60)
            print("TRANSCRIPT CONTENT (for AI analysis):")
            print("="*60)
            print(raw_transcript)
            print("="*60)
            print("\nTo complete processing, re-run with --structured-data <json_file>")
            print(f"  Page ID: {page_id}")
            # Keep status as 清洗中 so we can resume
            return {"status": "awaiting_analysis", "page_id": page_id, "meta": meta}

        # Phase 0 + Phase 2 (parallel in concept, sequential in script)
        session_page = None
        if meta["date"]:
            session_page = phase0_find_session(meta["date"])

        if not session_page:
            # Create a new Session page if none found
            print("  [Phase 0] Creating new session page...")
            session_page = notion.create_page(
                parent={"database_id": SCHEDULE_DB},
                properties={
                    "Session": {"title": [{"text": {"content": f"{meta['date']} {meta['subject']}课"}}]},
                    "Date/Period": {"date": {"start": meta["date"]}} if meta["date"] else {},
                },
            )
            print(f"  [Phase 0] ✅ Created session page: {session_page['id']}")

        session_id = session_page["id"]

        # Phase 1: Write structured notes
        phase1_write_notes(session_id, structured_data)

        # Phase 2: Backup transcript
        phase2_backup_transcript(session_id, raw_transcript)

        # Phase 3 + Phase 4 (parallel in concept)
        phase3_teaching_quality(meta, structured_data)
        phase4_student_tracking(meta, structured_data)

        # Mark as done
        update_trigger_status(page_id, STATUS_DONE)

        # Update summary on trigger entry
        if structured_data.get("highlights"):
            notion.update_page(page_id, {
                "摘要": {"rich_text": [{"text": {"content": structured_data["highlights"][:2000]}}]}
            })

        print(f"\n✅ All phases complete for: {meta['title']}")
        return {"status": "complete", "page_id": page_id}

    except Exception as e:
        print(f"\n❌ Error processing {meta['title']}: {e}")
        traceback.print_exc()
        # Revert status on failure
        try:
            update_trigger_status(page_id, STATUS_PENDING)
        except Exception:
            pass
        return {"status": "error", "page_id": page_id, "error": str(e)}


def create_test_data():
    """Create test entries for verification."""
    print("Creating test data...")

    # 1. Create a Session page in 小楷课表
    print("\n1. Creating test Session in 小楷课表...")
    session = notion.create_page(
        parent={"database_id": SCHEDULE_DB},
        properties={
            "Session": {"title": [{"text": {"content": "2026-02-25 写作正课"}}]},
            "Date/Period": {"date": {"start": "2026-02-25"}},
        },
    )
    print(f"   ✅ Session created: {session['id']}")

    # 2. Create a transcript entry in 教学逐字稿记录
    print("\n2. Creating test transcript entry...")
    test_transcript = _get_test_transcript()

    entry = notion.create_page(
        parent={"database_id": TRIGGER_DB},
        properties={
            "课程名称": {"title": [{"text": {"content": "小楷-写作-2026-02-25-正课-滕达"}}]},
            "日期": {"date": {"start": "2026-02-25"}},
            "学生": {"multi_select": [{"name": "小楷"}]},
            "教师": {"multi_select": [{"name": "滕达"}]},
            "科目": {"select": {"name": "写作"}},
            "考试类型": {"select": {"name": "雅思"}},
            "清洗状态": {"status": {"name": STATUS_PENDING}},
        },
    )
    print(f"   ✅ Transcript entry created: {entry['id']}")

    # Write transcript content to page body
    notion.append_blocks(entry["id"], [
        {"type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": chunk}}]
        }}
        for chunk in [test_transcript[i:i+2000] for i in range(0, len(test_transcript), 2000)]
    ])
    print(f"   ✅ Transcript body written ({len(test_transcript)} chars)")

    print(f"\n{'='*60}")
    print("Test data created successfully!")
    print(f"  Session ID: {session['id']}")
    print(f"  Trigger entry ID: {entry['id']}")
    print(f"{'='*60}")

    return {"session_id": session["id"], "entry_id": entry["id"]}


def _get_test_transcript() -> str:
    """Return a mock teaching transcript for testing."""
    return """滕达：好，小楷，我们今天来看雅思小作文，柱状图。你先看看这个题目，描述一下你看到了什么。

小楷：嗯...这个图表显示了五个国家在2015年和2020年的旅游收入。

滕达：对，那你觉得最大的特点是什么？

小楷：美国两年都是最高的，然后中国增长最多。

滕达：很好！你抓住了最核心的趋势。现在我们来把它写出来。先写opening paragraph，你试试看。

小楷：The bar chart shows the tourism revenue of five countries in 2015 and 2020.

滕达：OK，这个句子语法没问题，但太简单了。我们可以用 illustrates 替换 shows，用 income generated from tourism 替换 tourism revenue。而且要加上 the given 来修饰 bar chart。来，你再写一遍。

小楷：The given bar chart illustrates the income generated from tourism in five countries in 2015 and 2020.

滕达：好多了！现在来写overview。记住我们之前讲的——overview一定要写两个主要趋势，不要写数字。

小楷：Overall, the United States had the highest tourism income in both years, while China shows the most significant increase.

滕达：注意！"shows"这里要用过去式 "showed"，因为我们描述的是过去的数据。还有，"the most significant increase"可以升级为 "witnessed the most remarkable surge"。

滕达：💡 记住这个替换：increase → surge，这是一个B2到C1的升级，考官看到会加分的。

小楷：明白了。

滕达：好，现在来写body paragraph。记住分组原则——把趋势相似的国家放在一起。你觉得怎么分？

小楷：美国和法国一组，因为它们都很高？

滕达：思路是对的，但分组依据应该是趋势方向，不只是数值高低。美国、法国和英国可以一组——它们增长幅度适中。中国和日本一组——中国大幅增长，日本略有下降。这叫"对比分组法"。

滕达：💡 "永远记住，分组不是看谁大谁小，是看谁跟谁走势像"

滕达：好了，今天课后任务：
1. 把今天这篇柱状图小作文重新写一遍完整版
2. 把替换词表里的词造三个句子
3. 预习下节课的饼图模板

滕达：💡 "写作这个东西，不是你会多少词，而是你能不能在20分钟内把对的词用在对的地方。量不重要，准确度才重要。"

滕达：💡 "你今天overview写得很好，说明你已经学会找主趋势了，这是一个很大的进步。"

滕达：下课，辛苦了小楷！"""


def poll_loop():
    """Main polling loop — checks for pending entries every N seconds."""
    print(f"Starting polling loop (interval: {POLL_INTERVAL_SECONDS}s)")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            entries = find_pending_entries()
            for entry in entries:
                result = process_entry(entry)
                if result["status"] == "awaiting_analysis":
                    print("⏸️  Entry awaiting AI analysis — skipping for now")
        except KeyboardInterrupt:
            print("\nPolling stopped.")
            break
        except Exception as e:
            print(f"Error in poll loop: {e}")
            traceback.print_exc()

        time.sleep(POLL_INTERVAL_SECONDS)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Notion Transcript Agent")
    parser.add_argument("--once", action="store_true", help="Process all pending entries once, then exit")
    parser.add_argument("--page-id", type=str, help="Process a specific entry by page ID")
    parser.add_argument("--create-test", action="store_true", help="Create test data for verification")
    parser.add_argument("--structured-data", type=str, help="Path to JSON file with structured analysis data")
    args = parser.parse_args()

    if args.create_test:
        create_test_data()
        return

    structured_data = None
    if args.structured_data:
        with open(args.structured_data, "r") as f:
            structured_data = json.load(f)

    if args.page_id:
        page = notion.get_page(args.page_id)
        result = process_entry(page, structured_data)
        print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return

    if args.once:
        entries = find_pending_entries()
        for entry in entries:
            result = process_entry(entry, structured_data)
            print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return

    poll_loop()


if __name__ == "__main__":
    main()

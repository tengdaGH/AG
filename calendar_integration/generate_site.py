#!/usr/bin/env python3
"""
generate_site.py — Fetches iCloud ICS feeds and generates a self-contained
static HTML calendar page for GitHub Pages deployment.
"""

import re
import datetime
import zoneinfo
import requests
import os
import html as html_mod
import concurrent.futures
import json

SHANGHAI_TZ = zoneinfo.ZoneInfo("Asia/Shanghai")

ICS_FEEDS = {
    "Miya": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjgoiOkv5PFGc8AbHw6VVae6__dE6CfiFmiu9BoMcUHNwgq4C2AeVeJbuTwRlWZaoU",
    "Rita": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUngnLMbawCT_bon3iWGIba7YM84yuUlE7Idh5jWX1bDCHZKbzA8hrxpLI2_Xowoz3NU",
    "月月": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnhjf_1D8Xs4kSFfKit5JqAv6xA4A4idWDEIz-quwP9634_Qo0Wp21-tGyBGvEpEi5g",
    "达哥": "https://p235-caldav.icloud.com.cn/published/2/ODE0NTU3NDA4NzgxNDU1N5a7oJG6Offg5NzyJNtGUnjL2uWOtR1ag7v1hzo5u_PgGOG5Sa6gmMjGSlEVV_JFPYzif3IWvBkmDfpwwWeiT-k",
}

TEACHER_COLORS = {
    "Miya": {"bg": "#7c3aed", "light": "rgba(124,58,237,0.15)", "border": "rgba(124,58,237,0.5)"},
    "Rita": {"bg": "#f43f5e", "light": "rgba(244,63,94,0.15)", "border": "rgba(244,63,94,0.5)"},
    "月月": {"bg": "#f97316", "light": "rgba(249,115,22,0.15)", "border": "rgba(249,115,22,0.5)"},
    "达哥": {"bg": "#0ea5e9", "light": "rgba(14,165,233,0.15)", "border": "rgba(14,165,233,0.5)"},
}

WEEKDAY_NAMES_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def parse_ics_date(date_str):
    """Parse an ICS date string into a naive datetime, treating it as Shanghai time."""
    if "T" in date_str:
        clean = date_str.replace("Z", "")[:15]
        dt = datetime.datetime.strptime(clean, "%Y%m%dT%H%M%S")
        return dt, False
    else:
        dt = datetime.datetime.strptime(date_str[:8], "%Y%m%d")
        return dt, True


def fetch_events(teacher, url, week_start, week_end):
    """Fetch + parse a single ICS feed, returning events within the date window."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        content = resp.text.replace("\r\n ", "").replace("\n ", "")
    except Exception as e:
        print(f"  [Error fetching {teacher}]: {e}")
        return []

    blocks = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", content, re.DOTALL)
    events = []
    for block in blocks:
        dtstart_m = re.search(r"DTSTART.*?:(\d{8}T?\d{0,6}Z?)", block)
        dtend_m = re.search(r"DTEND.*?:(\d{8}T?\d{0,6}Z?)", block)
        summary_m = re.search(r"SUMMARY:(.*?)(?:\r?\n|$)", block)
        if not dtstart_m or not summary_m:
            continue

        start_dt, is_all_day = parse_ics_date(dtstart_m.group(1).strip())
        if dtend_m:
            end_dt, _ = parse_ics_date(dtend_m.group(1).strip())
        else:
            end_dt = start_dt + datetime.timedelta(hours=1)

        if start_dt.date() < week_start or start_dt.date() > week_end:
            continue

        summary_text = summary_m.group(1).strip()
        if "休息" in summary_text:
            is_all_day = True

        events.append({
            "teacher": teacher,
            "summary": summary_text,
            "start": start_dt,
            "end": end_dt,
            "is_all_day": is_all_day,
        })

    return events


def generate_html(all_events, now_shanghai):
    """Generate the full self-contained HTML page."""

    # Determine the current week (Mon–Sun)
    today = now_shanghai.date()
    week_start = today - datetime.timedelta(days=today.weekday())  # Monday
    week_end = week_start + datetime.timedelta(days=6)  # Sunday

    # Build day columns
    days = [week_start + datetime.timedelta(days=i) for i in range(7)]

    # Events grouped by day
    events_by_day = {d: [] for d in days}
    today_events_by_teacher = {}
    for ev in sorted(all_events, key=lambda e: e["start"]):
        d = ev["start"].date()
        if d in events_by_day:
            events_by_day[d].append(ev)
        if d == today:
            teacher = ev["teacher"]
            if teacher not in today_events_by_teacher:
                today_events_by_teacher[teacher] = []
            today_events_by_teacher[teacher].append(ev)

    # Build the grid HTML
    HOUR_START = 8
    HOUR_END = 22
    HOUR_HEIGHT = 60  # px per hour

    def compute_overlap_layout(day_events):
        """Assign horizontal slot positions to overlapping events.
        Returns list of (event, slot_index, total_slots) tuples."""
        timed = [e for e in day_events if not e["is_all_day"]]
        timed.sort(key=lambda e: (e["start"], e["end"]))
        if not timed:
            return []

        # Group into overlap clusters
        clusters = []
        current_cluster = [timed[0]]
        cluster_end = timed[0]["end"]
        for ev in timed[1:]:
            if ev["start"] < cluster_end:  # overlaps
                current_cluster.append(ev)
                if ev["end"] > cluster_end:
                    cluster_end = ev["end"]
            else:
                clusters.append(current_cluster)
                current_cluster = [ev]
                cluster_end = ev["end"]
        clusters.append(current_cluster)

        # Assign slots within each cluster
        result = []
        for cluster in clusters:
            total = len(cluster)
            for idx, ev in enumerate(cluster):
                result.append((ev, idx, total))
        return result

    def event_to_block(ev, slot_idx, total_slots):
        if ev["is_all_day"]:
            return ""
        h_start = ev["start"].hour + ev["start"].minute / 60
        h_end = ev["end"].hour + ev["end"].minute / 60
        if h_start < HOUR_START:
            h_start = HOUR_START
        if h_end > HOUR_END:
            h_end = HOUR_END
        top = (h_start - HOUR_START) * HOUR_HEIGHT
        height = max((h_end - h_start) * HOUR_HEIGHT, 24)
        colors = TEACHER_COLORS.get(ev["teacher"], TEACHER_COLORS["Miya"])
        time_str = f"{ev['start'].strftime('%H:%M')}–{ev['end'].strftime('%H:%M')}"
        summary_escaped = html_mod.escape(ev["summary"])

        # Calculate horizontal position
        width_pct = 100 / total_slots
        left_pct = slot_idx * width_pct
        # Add small gap between slots
        gap = 2  # px
        style_pos = f"top:{top}px;height:{height}px;left:calc({left_pct}% + {gap}px);width:calc({width_pct}% - {gap * 2}px);"

        return f'''<div class="ev" style="{style_pos}
            background:{colors['light']};border-left:3px solid {colors['bg']};
            " data-teacher="{html_mod.escape(ev['teacher'])}"
            title="{summary_escaped}  {time_str}">
            <span class="ev-time">{time_str}</span>
            <span class="ev-title">{summary_escaped}</span>
        </div>'''

    # Column HTML
    col_html_parts = []
    for i, d in enumerate(days):
        is_today = d == today
        day_label = f'{d.month}/{d.day}'
        weekday_label = WEEKDAY_NAMES_CN[d.weekday()]
        today_cls = ' today-col' if is_today else ''
        today_dot = '<span class="today-dot"></span>' if is_today else ''

        layout = compute_overlap_layout(events_by_day[d])
        blocks_html = ""
        for ev, slot_idx, total_slots in layout:
            blocks_html += event_to_block(ev, slot_idx, total_slots)

        col_html_parts.append(f'''
        <div class="day-col{today_cls}" data-date="{d.isoformat()}">
            <div class="day-header">
                <span class="weekday">{weekday_label}</span>
                <span class="date-num">{today_dot}{day_label}</span>
            </div>
            <div class="day-body" style="height:{(HOUR_END - HOUR_START) * HOUR_HEIGHT}px;">
                {blocks_html}
            </div>
        </div>''')

    # Time gutter
    gutter_html = ""
    for h in range(HOUR_START, HOUR_END):
        gutter_html += f'<div class="time-label" style="top:{(h - HOUR_START) * HOUR_HEIGHT}px;">{h:02d}:00</div>'

    # Today summary sidebar
    sidebar_items = ""
    for teacher_name in ["Miya", "Rita", "月月", "达哥"]:
        evts = today_events_by_teacher.get(teacher_name, [])
        if not evts:
            continue
        colors = TEACHER_COLORS[teacher_name]
        sidebar_items += f'<div class="sidebar-teacher"><div class="sidebar-teacher-name" style="color:{colors["bg"]}"><span class="dot" style="background:{colors["bg"]}"></span>{html_mod.escape(teacher_name)} ({len(evts)}节)</div>'
        for ev in evts:
            time_str = f"{ev['start'].strftime('%H:%M')}–{ev['end'].strftime('%H:%M')}" if not ev["is_all_day"] else "全天"
            sidebar_items += f'<div class="sidebar-ev" style="background:{colors["light"]} !important; border-left: 3px solid {colors["bg"]} !important;"><span class="sidebar-time">{time_str}</span><span class="sidebar-title">{html_mod.escape(ev["summary"])}</span></div>'
        sidebar_items += '</div>'

    if not sidebar_items:
        sidebar_items = '<div class="sidebar-empty">今天没有课程安排 🎉</div>'

    # Teacher filter tabs
    tab_html = '<button class="tab active" data-filter="all">全部</button>'
    for t in ["Miya", "Rita", "月月", "达哥"]:
        c = TEACHER_COLORS[t]["bg"]
        tab_html += f'<button class="tab" data-filter="{html_mod.escape(t)}" style="--tab-color:{c}">{html_mod.escape(t)}</button>'

    sync_time = now_shanghai.strftime("%Y-%m-%d %H:%M:%S")
    week_label = f"{week_start.strftime('%m月%d日')} – {week_end.strftime('%m月%d日')}"

    # All-day events bar
    all_day_html = ""
    for d in days:
        all_day_evs = [e for e in events_by_day[d] if e["is_all_day"]]
        if all_day_evs:
            pills = ""
            for ev in all_day_evs:
                c = TEACHER_COLORS.get(ev["teacher"], TEACHER_COLORS["Miya"])
                pills += f'<span class="allday-pill" style="background:{c["light"]};border:1px solid {c["border"]};color:{c["bg"]}" data-teacher="{html_mod.escape(ev["teacher"])}">{html_mod.escape(ev["summary"])}</span>'
            all_day_html += f'<div class="allday-cell">{pills}</div>'
        else:
            all_day_html += '<div class="allday-cell"></div>'

    return rf'''<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>纽约课教师课表</title>
    <meta name="description" content="纽约课教师课表实时日程总览">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link
        href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Lora:wght@400;500;600&display=swap"
        rel="stylesheet">
    <style>
        *,
        *::before,
        *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0
        }}

        :root {{
            /* Anthropic palette */
            --bg: #faf9f5;
            --surface: #f0efe8;
            --surface2: #e8e6dc;
            --border: #dcd9cf;
            --text: #141413;
            --text2: #5a584f;
            --text3: #b0aea5;
            --radius: 10px;
            --radius-sm: 7px;

            /* Teacher accents — earthy, muted */
            --miya: #d97757;
            --rita: #6a9bcc;
            --yueyue: #788c5d;
            --dage: #8b6f5c;

            /* Fonts */
            --font-heading: 'Poppins', system-ui, -apple-system, sans-serif;
            --font-body: 'Lora', Georgia, serif;
        }}

        body {{
            font-family: var(--font-body);
            background: var(--bg);
            color: var(--text);
            min-height: 100vh
        }}

        h1 {{
            font-family: var(--font-heading);
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.01em
        }}

        /* Layout */
        .shell {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden
        }}

        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 28px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
            background: var(--bg);
            position: sticky;
            top: 0;
            z-index: 10
        }}

        .topbar-left {{
            display: flex;
            align-items: center;
            gap: 14px
        }}

        .topbar-right {{
            display: flex;
            align-items: center;
            gap: 12px
        }}

        .sync-badge {{
            font-family: var(--font-heading);
            font-size: 0.7rem;
            color: var(--text3);
            background: var(--surface2);
            padding: 4px 12px;
            border-radius: 20px;
            white-space: nowrap;
            letter-spacing: 0.01em
        }}

        .sync-badge::before {{
            content: '';
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #788c5d;
            border-radius: 50%;
            margin-right: 7px;
            animation: pulse 2.5s ease-in-out infinite
        }}

        @keyframes pulse {{

            0%,
            100% {{
                opacity: 1
            }}

            50% {{
                opacity: .35
            }}
        }}

        /* Tabs — Anthropic pill nav */
        .tabs {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap
        }}

        .tab {{
            padding: 6px 16px;
            border-radius: 20px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text2);
            font-size: 0.78rem;
            font-weight: 500;
            cursor: pointer;
            transition: all .25s ease;
            font-family: var(--font-heading);
            letter-spacing: 0.01em
        }}

        .tab:hover {{
            background: var(--surface2);
            color: var(--text);
            border-color: var(--text3)
        }}

        .tab.active {{
            background: var(--text);
            color: var(--bg);
            border-color: var(--text)
        }}

        /* Main area */
        .main {{
            display: flex;
            flex: 1;
            overflow: hidden
        }}

        .calendar-area {{
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
            padding: 0;
            display: flex;
            flex-direction: column;
        }}

        /* Fixed header row above the scrollable grid */
        .day-headers-row {{
            display: flex;
            flex-shrink: 0;
            border-bottom: 1px solid var(--border);
        }}

        .day-headers-row .header-gutter {{
            width: 58px;
            flex-shrink: 0;
            border-right: 1px solid var(--border);
        }}

        .day-headers-row .header-cells {{
            display: flex;
            flex: 1;
        }}

        .day-headers-row .header-cell {{
            flex: 1;
            text-align: center;
            padding: 10px 4px 8px;
            border-right: 1px solid var(--border);
        }}

        .day-headers-row .header-cell:last-child {{
            border-right: none;
        }}

        .grid-scroll {{
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
        }}

        .sidebar {{
            width: 280px;
            flex-shrink: 0;
            border-left: 1px solid var(--border);
            overflow-y: auto;
            padding: 22px;
            background: var(--surface)
        }}

        /* Week header */
        .week-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 28px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0
        }}

        .week-label {{
            font-family: var(--font-heading);
            font-size: 0.88rem;
            font-weight: 600;
            color: var(--text2)
        }}

        /* Grid */
        .grid-wrap {{
            display: flex;
            position: relative;
            min-width: 700px
        }}

        .time-gutter {{
            width: 58px;
            flex-shrink: 0;
            position: relative;
            border-right: 1px solid var(--border)
        }}

        .time-label {{
            position: absolute;
            right: 12px;
            font-family: var(--font-heading);
            font-size: 0.68rem;
            color: var(--text3);
            transform: translateY(-50%);
            font-variant-numeric: tabular-nums
        }}

        .days-container {{
            display: flex;
            flex: 1
        }}

        .day-col {{
            flex: 1;
            min-width: 0;
            border-right: 1px solid var(--border);
            position: relative
        }}

        .day-col:last-child {{
            border-right: none
        }}

        .day-header {{
            display: none;
        }}

        .weekday {{
            display: block;
            font-family: var(--font-heading);
            font-size: 0.7rem;
            color: var(--text3);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.06em
        }}

        .date-num {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: var(--font-heading);
            font-size: 0.84rem;
            font-weight: 600;
            color: var(--text2);
            margin-top: 2px
        }}

        .today-col .weekday {{
            color: var(--text)
        }}

        .today-col .date-num {{
            color: #fff;
            background: var(--miya);
            padding: 2px 10px;
            border-radius: 20px
        }}

        .today-dot {{
            display: none
        }}

        .day-body {{
            position: relative;
        }}

        /* Hour gridlines */
        .day-body::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: repeating-linear-gradient(to bottom, transparent, transparent 59px, var(--border) 59px, var(--border) 60px);
            pointer-events: none;
            z-index: 0;
        }}

        /* Event block */
        .ev {{
            position: absolute;
            border-radius: var(--radius-sm);
            padding: 3px 7px;
            overflow: hidden;
            cursor: default;
            z-index: 1;
            display: flex;
            flex-direction: column;
            gap: 1px;
            transition: opacity .3s ease, box-shadow .3s ease, left .35s ease, width .35s ease;
        }}

        /* Hover-expand: in-place full-width pop */
        .ev:hover {{
            z-index: 20;
            width: calc(100% - 4px) !important;
            left: calc(0% + 2px) !important;
            box-shadow: 0 6px 24px rgba(20, 20, 19, 0.22);
            overflow: visible;
        }}

        .ev:hover .ev-title {{
            -webkit-line-clamp: unset;
            line-clamp: unset;
            overflow: visible;
        }}

        .ev-time {{
            font-family: var(--font-heading);
            font-size: 0.64rem;
            font-weight: 600;
            opacity: 0.65;
            white-space: nowrap
        }}

        .ev-title {{
            font-size: 0.72rem;
            font-weight: 500;
            line-height: 1.35;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden
        }}

        /* Formatted title spans */
        .ev-teacher {{
            font-weight: 600;
            opacity: 0.7;
            font-size: 0.64rem
        }}

        .ev-student {{
            font-weight: 600
        }}

        .ev-meta {{
            opacity: 0.7;
            font-size: 0.65rem
        }}

        .ev-sep {{
            opacity: 0.35;
            margin: 0 2px
        }}

        .ev.hidden {{
            opacity: 0.06;
            pointer-events: none
        }}

        /* Day column hidden */
        .day-col.col-hidden {{
            display: none
        }}

        /* Tomorrow sidebar divider */
        .sidebar-divider {{
            height: 1px;
            background: var(--border);
            margin: 16px 0;
        }}

        /* All-day row */
        .allday-row {{
            display: flex;
            min-height: 28px;
            border-bottom: 1px solid var(--border)
        }}

        .allday-gutter {{
            width: 58px;
            flex-shrink: 0;
            border-right: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
            font-family: var(--font-heading);
            font-size: 0.65rem;
            color: var(--text3)
        }}

        .allday-cells {{
            display: flex;
            flex: 1
        }}

        .allday-cell {{
            flex: 1;
            min-width: 0;
            border-right: 1px solid var(--border);
            padding: 4px;
            display: flex;
            flex-wrap: wrap;
            gap: 3px;
            align-items: center
        }}

        .allday-cell:last-child {{
            border-right: none
        }}

        .allday-pill {{
            font-family: var(--font-heading);
            font-size: 0.65rem;
            padding: 2px 8px;
            border-radius: 12px;
            white-space: nowrap;
            font-weight: 500
        }}

        .allday-pill.hidden {{
            opacity: 0.06
        }}

        /* Sidebar */
        .sidebar-title-main {{
            font-family: var(--font-heading);
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 8px
        }}

        .sidebar-title-main::before {{
            content: '📋'
        }}

        .sidebar-teacher {{
            margin-bottom: 18px
        }}

        .sidebar-teacher-name {{
            font-family: var(--font-heading);
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 7px;
            display: flex;
            align-items: center;
            gap: 7px
        }}

        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0
        }}

        .sidebar-ev {{
            display: flex;
            flex-direction: column;
            padding: 9px 12px;
            background: var(--surface2);
            border-radius: var(--radius-sm);
            margin-bottom: 5px;
            transition: opacity .3s ease
        }}

        .sidebar-ev.hidden {{
            opacity: 0.06
        }}

        .sidebar-time {{
            font-family: var(--font-heading);
            font-size: 0.68rem;
            color: var(--text3);
            font-variant-numeric: tabular-nums;
            font-weight: 500
        }}

        .sidebar-title {{
            font-size: 0.78rem;
            font-weight: 500;
            margin-top: 2px
        }}

        .sidebar-empty {{
            color: var(--text3);
            font-size: 0.85rem;
            text-align: center;
            padding: 40px 0
        }}

        /* Now line — terracotta */
        .now-line {{
            position: absolute;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--miya);
            z-index: 3;
            pointer-events: none
        }}

        .now-line::before {{
            content: '';
            position: absolute;
            left: -4px;
            top: -3px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--miya)
        }}

        /* Mobile */
        @media(max-width:860px) {{
            .sidebar {{
                display: none
            }}

            .topbar {{
                padding: 12px 16px;
                flex-wrap: wrap;
                gap: 8px
            }}

            .tabs {{
                order: 3;
                width: 100%
            }}

            .grid-wrap {{
                min-width: 580px
            }}
        }}

        @media(max-width:600px) {{
            .grid-wrap {{
                min-width: 480px
            }}

            .time-gutter {{
                width: 42px
            }}

            .time-label {{
                font-size: 0.6rem;
                right: 6px
            }}

            .ev-title {{
                font-size: 0.65rem
            }}

            .day-header {{
                padding: 6px 2px 4px
            }}
        }}
    </style>
</head>

<body>
    <div class="shell">
        <div class="topbar">
            <div class="topbar-left">
                <h1>纽约课教师课表</h1>
                <div class="tabs" id="tabs">{tab_html}</div>
            </div>
            <div class="topbar-right">
                <span class="sync-badge">同步于 {sync_time}</span>
            </div>
        </div>

        <div class="week-header">
            <span class="week-label">{week_label}</span>
        </div>

        <div class="main">
            <div class="calendar-area">
                <!-- All-day row -->
                <div class="allday-row">
                    <div class="allday-gutter">全天</div>
                    <div class="allday-cells">{all_day_html}</div>
                </div>

                <!-- Time grid -->
                <div class="grid-wrap">
                    <div class="time-gutter" style="height:{{(HOUR_END - HOUR_START) * HOUR_HEIGHT}}px;">
                        {gutter_html}
                    </div>
                    <div class="days-container">
                        {"".join(col_html_parts)}
                    </div>
                </div>
            </div>

            <div class="sidebar">
                <div class="sidebar-title-main">今日课程总览</div>
                {sidebar_items}
            </div>
        </div>
    </div>

    <script>
        (function () {{
            // ── Known teachers ──
            const TEACHERS = ['miya', 'Miya', 'Rita', 'rita', '月月', '达哥'];
            const TEACHER_PREFIXES = ['miya', 'Rita', 'rita', '达哥', '🈷️'];
            const TESTS = ['新托福', '托福', '雅思'];
            const SKILLS = ['阅读', '写作', '口语', '听力'];
            const TYPES = ['模考正课', '模考', '正课'];
            const TEACHER_COLORS = {json.dumps(TEACHER_COLORS)};
            const START_HOUR = {HOUR_START};

            // ── Today/Tomorrow helpers ──
            const now = new Date();
            const todayStr = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
            const tomorrow = new Date(now); tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = tomorrow.getFullYear() + '-' + String(tomorrow.getMonth() + 1).padStart(2, '0') + '-' + String(tomorrow.getDate()).padStart(2, '0');
            const twoDaysAgo = new Date(now); twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);
            const cutoffStr = twoDaysAgo.getFullYear() + '-' + String(twoDaysAgo.getMonth() + 1).padStart(2, '0') + '-' + String(twoDaysAgo.getDate()).padStart(2, '0');

            // ── 1. Hide day columns older than 2 days ago ──
            const allCols = document.querySelectorAll('.day-col');
            let visibleDates = [];
            allCols.forEach(col => {{
                const d = col.dataset.date;
                if (d < cutoffStr) {{
                    col.classList.add('col-hidden');
                }} else {{
                    visibleDates.push(d);
                }}
            }});
            // Update week header label
            if (visibleDates.length) {{
                const first = visibleDates[0], last = visibleDates[visibleDates.length - 1];
                const fmt = d => {{ const [, m, dd] = d.split('-'); return parseInt(m) + '月' + parseInt(dd) + '日'; }};
                const weekLabel = document.querySelector('.week-label');
                if (weekLabel) weekLabel.textContent = fmt(first) + ' – ' + fmt(last);
            }}
            // Also hide corresponding allday cells
            const alldayCells = document.querySelectorAll('.allday-cell');
            let cellIdx = 0;
            allCols.forEach(col => {{
                if (alldayCells[cellIdx]) {{
                    if (col.classList.contains('col-hidden')) alldayCells[cellIdx].style.display = 'none';
                }}
                cellIdx++;
            }});

            // ── 1b. Build fixed header row above scrollable grid ──
            const calArea = document.querySelector('.calendar-area');
            const alldayRow = document.querySelector('.allday-row');
            const gridWrap = document.querySelector('.grid-wrap');
            if (calArea && gridWrap) {{
                // Create header row
                const headerRow = document.createElement('div');
                headerRow.className = 'day-headers-row';
                const hGutter = document.createElement('div');
                hGutter.className = 'header-gutter';
                headerRow.appendChild(hGutter);
                const hCells = document.createElement('div');
                hCells.className = 'header-cells';
                allCols.forEach(col => {{
                    if (col.classList.contains('col-hidden')) return;
                    const dh = col.querySelector('.day-header');
                    const cell = document.createElement('div');
                    cell.className = 'header-cell';
                    if (col.classList.contains('today-col')) cell.classList.add('today-col');
                    if (dh) cell.innerHTML = dh.innerHTML;
                    hCells.appendChild(cell);
                }});
                headerRow.appendChild(hCells);

                // Wrap allday + grid in a scrollable container
                const scrollDiv = document.createElement('div');
                scrollDiv.className = 'grid-scroll';
                if (alldayRow) scrollDiv.appendChild(alldayRow);
                scrollDiv.appendChild(gridWrap);

                // Insert header row then scrollDiv into calendar area
                calArea.appendChild(headerRow);
                calArea.appendChild(scrollDiv);
            }}

            // ── 1c. Make hovered .ev fully opaque ──
            // Events have rgba(..., 0.12) backgrounds. On hover, inflate alpha to ~0.95 for readability.
            function rgbaToSolid(rgba) {{
                const m = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
                if (!m) return rgba;
                const r = parseInt(m[1]), g = parseInt(m[2]), b = parseInt(m[3]);
                // Blend with cream bg (#f7f2ea) at high alpha
                const a = 0.92;
                const bg = {{ r: 247, g: 242, b: 234 }};
                const nr = Math.round(r * a + bg.r * (1 - a));
                const ng = Math.round(g * a + bg.g * (1 - a));
                const nb = Math.round(b * a + bg.b * (1 - a));
                return 'rgb(' + nr + ',' + ng + ',' + nb + ')';
            }}
            document.querySelectorAll('.ev').forEach(ev => {{
                // Pre-compute solid background equivalent for each event
                const bgStr = ev.style.background || '';
                const rgbaMatch = bgStr.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)/);
                if (rgbaMatch) {{
                    const r = parseInt(rgbaMatch[1]);
                    const g = parseInt(rgbaMatch[2]);
                    const b = parseInt(rgbaMatch[3]);
                    const a = parseFloat(rgbaMatch[4] || '1');
                    // Blend with cream (#f7f2ea = 247,242,234) to get solid equivalent
                    const cream = {{ r: 247, g: 242, b: 234 }};
                    const sr = Math.round(r * a + cream.r * (1 - a));
                    const sg = Math.round(g * a + cream.g * (1 - a));
                    const sb = Math.round(b * a + cream.b * (1 - a));
                    ev._solidBg = 'rgb(' + sr + ',' + sg + ',' + sb + ')';
                    ev._origBg = ev.style.background;
                }}
                ev.addEventListener('mouseenter', () => {{
                    if (ev._solidBg) ev.style.background = ev._solidBg;
                }});
                ev.addEventListener('mouseleave', () => {{
                    if (ev._origBg) ev.style.background = ev._origBg;
                }});
            }});

            // ── 2. Trim empty hour rows from the bottom ──
            let latestEndPx = 0;
            document.querySelectorAll('.ev').forEach(ev => {{
                const top = parseFloat(ev.style.top) || 0;
                const height = parseFloat(ev.style.height) || 0;
                const end = top + height;
                if (end > latestEndPx) latestEndPx = end;
            }});
            // Add 1 hour buffer, round up to next hour boundary
            const latestEndHour = Math.ceil(latestEndPx / 60) + START_HOUR + 1;
            const gridEndHour = Math.min(22, Math.max(latestEndHour, START_HOUR + 4)); // at least 4 hours shown
            const totalHours = gridEndHour - START_HOUR;
            const gridHeight = totalHours * 60;

            // Adjust time gutter — remove labels past gridEndHour
            const gutter = document.querySelector('.time-gutter');
            if (gutter) {{
                gutter.style.height = gridHeight + 'px';
                Array.from(gutter.querySelectorAll('.time-label')).forEach(lbl => {{
                    const hr = parseInt(lbl.textContent);
                    if (hr >= gridEndHour) lbl.style.display = 'none';
                }});
            }}
            // Adjust all day-body heights
            document.querySelectorAll('.day-body').forEach(db => db.style.height = gridHeight + 'px');

            // ── Parse title helpers ──
            function parseTitle(raw, teacherAttr) {{
                if (!raw) return {{ special: raw || '' }};
                let s = raw.trim();
                if (s.includes('休息')) return {{ teacher: teacherAttr, student: s.replace(/^(miya|Rita|达哥|🈷️)\s*/i, ''), special: null }};
                if (s.startsWith('🈷️')) s = s.replace(/^🈷️\s*/, '');
                let teacher = teacherAttr || '';
                for (const t of TEACHER_PREFIXES) {{
                    if (s.startsWith(t + ' ') || s.startsWith(t)) {{
                        s = s.replace(new RegExp('^' + t.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&') + '\\s*'), '');
                        break;
                    }}
                }}
                let type = '';
                for (const ty of TYPES) {{ if (s.endsWith(ty)) {{ type = ty; s = s.slice(0, -ty.length); break; }} }}
                let skill = '';
                for (const sk of SKILLS) {{ if (s.includes(sk)) {{ skill = sk; s = s.replace(sk, ''); break; }} }}
                let test = '';
                for (const te of TESTS) {{ if (s.includes(te)) {{ test = te; s = s.replace(te, ''); break; }} }}
                let student = s.trim();
                return {{ teacher, student, test, skill, type, special: null }};
            }}

            function formatTitle(parsed, showTeacher) {{
                if (parsed.special !== null && parsed.special !== undefined) return parsed.special;
                let parts = [];
                if (showTeacher && parsed.teacher) parts.push('<span class="ev-teacher">' + parsed.teacher + '</span>');
                if (parsed.student) {{
                    if (parts.length) parts.push('<span class="ev-sep">·</span>');
                    parts.push('<span class="ev-student">' + parsed.student + '</span>');
                }}
                let meta = [parsed.test, parsed.skill].filter(Boolean).join(' ');
                if (parsed.type && parsed.type !== '正课') meta += ' ' + parsed.type;
                if (meta) {{
                    if (parts.length) parts.push('<span class="ev-sep">·</span>');
                    parts.push('<span class="ev-meta">' + meta + '</span>');
                }}
                return parts.join('');
            }}

            // ── Parse all events on page load ──
            let currentFilter = 'all';
            document.querySelectorAll('.ev').forEach(ev => {{
                const raw = ev.querySelector('.ev-title')?.textContent || '';
                const teacherAttr = ev.dataset.teacher || '';
                const parsed = parseTitle(raw, teacherAttr);
                ev._parsed = parsed;
                ev._rawTitle = raw;
                ev.dataset.origLeft = ev.style.left;
                ev.dataset.origWidth = ev.style.width;
                ev.querySelector('.ev-title').innerHTML = formatTitle(parsed, true);
            }});

            // Also parse sidebar titles
            document.querySelectorAll('.sidebar-title').forEach(st => {{
                const raw = st.textContent || '';
                const parsed = parseTitle(raw, '');
                st._parsed = parsed;
                st._rawTitle = raw;
                st.innerHTML = formatTitle(parsed, true);
            }});

            // ── 3. Build tomorrow sidebar ──
            const tomorrowCol = document.querySelector('.day-col[data-date="' + tomorrowStr + '"]');
            if (tomorrowCol) {{
                const sidebar = document.querySelector('.sidebar');
                if (sidebar) {{
                    // Add divider
                    const divider = document.createElement('div');
                    divider.className = 'sidebar-divider';
                    sidebar.appendChild(divider);

                    // Title
                    const title = document.createElement('div');
                    title.className = 'sidebar-title-main';
                    title.textContent = '明日课程总览';
                    sidebar.appendChild(title);

                    // Gather tomorrow's events by teacher
                    const tEvs = Array.from(tomorrowCol.querySelectorAll('.ev'));
                    const byTeacher = {{}};
                    tEvs.forEach(ev => {{
                        const t = ev.dataset.teacher || '其他';
                        if (!byTeacher[t]) byTeacher[t] = [];
                        byTeacher[t].push(ev);
                    }});

                    const teacherOrder = ['Miya', 'Rita', '月月', '达哥'];
                    teacherOrder.forEach(tName => {{
                        const evList = byTeacher[tName];
                        if (!evList || !evList.length) return;
                        const block = document.createElement('div');
                        block.className = 'sidebar-teacher';
                        const colorObj = TEACHER_COLORS[tName] || {{bg: '#888', light: '#f0f0f0'}};
                        const nameEl = document.createElement('div');
                        nameEl.className = 'sidebar-teacher-name';
                        nameEl.style.color = colorObj.bg;
                        nameEl.innerHTML = '<span class="dot" style="background:' + colorObj.bg + '"></span>' + tName + ' (' + evList.length + '节)';
                        block.appendChild(nameEl);

                        evList.forEach(ev => {{
                            const time = ev.querySelector('.ev-time')?.textContent || '';
                            const parsed = ev._parsed;
                            const evEl = document.createElement('div');
                            evEl.className = 'sidebar-ev';
                            evEl.style.cssText = 'background: ' + colorObj.light + ' !important; border-left: 3px solid ' + colorObj.bg + ' !important;';
                            evEl.innerHTML = '<span class="sidebar-time">' + time + '</span><span class="sidebar-title">' + formatTitle(parsed, false) + '</span>';
                            block.appendChild(evEl);
                        }});
                        sidebar.appendChild(block);
                    }});

                    if (tEvs.length === 0) {{
                        const empty = document.createElement('div');
                        empty.className = 'sidebar-empty';
                        empty.textContent = '明日暂无课程';
                        sidebar.appendChild(empty);
                    }}
                }}
            }}

            // ── Collision recalc ──
            function recalcColumn(col, filter) {{
                const evs = Array.from(col.querySelectorAll('.ev'));
                if (filter === 'all') {{
                    evs.forEach(ev => {{ ev.style.left = ev.dataset.origLeft; ev.style.width = ev.dataset.origWidth; }});
                    return;
                }}
                const visible = evs.filter(ev => !ev.classList.contains('hidden'));
                if (!visible.length) return;
                const items = visible.map(ev => ({{ el: ev, top: parseFloat(ev.style.top), height: parseFloat(ev.style.height) }}));
                items.sort((a, b) => a.top - b.top || a.height - b.height);
                const columns = [];
                items.forEach(item => {{
                    let placed = false;
                    for (let c = 0; c < columns.length; c++) {{
                        const last = columns[c][columns[c].length - 1];
                        if (item.top >= last.top + last.height) {{ columns[c].push(item); item.col = c; placed = true; break; }}
                    }}
                    if (!placed) {{ item.col = columns.length; columns.push([item]); }}
                }});
                const numCols = columns.length;
                items.forEach(item => {{
                    const pct = 100 / numCols;
                    item.el.style.left = 'calc(' + (item.col * pct) + '% + 2px)';
                    item.el.style.width = 'calc(' + pct + '% - 4px)';
                }});
            }}

            function updateTitles(filter) {{
                const showTeacher = (filter === 'all');
                document.querySelectorAll('.ev').forEach(ev => {{
                    if (ev._parsed) ev.querySelector('.ev-title').innerHTML = formatTitle(ev._parsed, showTeacher);
                }});
            }}

            // ── Teacher filter ──
            document.getElementById('tabs').addEventListener('click', e => {{
                const btn = e.target.closest('.tab');
                if (!btn) return;
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                btn.classList.add('active');
                const filter = btn.dataset.filter;
                currentFilter = filter;
                document.querySelectorAll('.ev').forEach(el => el.classList.toggle('hidden', filter !== 'all' && el.dataset.teacher !== filter));
                document.querySelectorAll('.allday-pill').forEach(el => el.classList.toggle('hidden', filter !== 'all' && el.dataset.teacher !== filter));
                document.querySelectorAll('.day-col:not(.col-hidden)').forEach(col => recalcColumn(col, filter));
                updateTitles(filter);
            }});

            // ── Now line ──
            (function () {{
                const col = document.querySelector('.day-col[data-date="' + todayStr + '"]');
                if (!col) return;
                const body = col.querySelector('.day-body');
                const h = now.getHours() + now.getMinutes() / 60;
                if (h < START_HOUR || h > gridEndHour) return;
                const top = (h - START_HOUR) * 60;
                const line = document.createElement('div');
                line.className = 'now-line';
                line.style.top = top + 'px';
                body.appendChild(line);
                const area = document.querySelector('.calendar-area');
                if (area) area.scrollTop = Math.max(0, top - 120);
            }})();
        }})();
    </script>
</body>

</html></html>'''


def main():
    now_shanghai = datetime.datetime.now(datetime.timezone.utc).astimezone(SHANGHAI_TZ)
    today = now_shanghai.date()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    print(f"Generating calendar page for week {week_start} – {week_end}...")

    all_events = []
    
    # Fetch feeds concurrently to minimize network I/O time
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ICS_FEEDS)) as executor:
        future_to_teacher = {
            executor.submit(fetch_events, teacher, url, week_start, week_end): teacher
            for teacher, url in ICS_FEEDS.items()
        }
        for future in concurrent.futures.as_completed(future_to_teacher):
            teacher = future_to_teacher[future]
            try:
                events = future.result()
                print(f"  Fetched {teacher} → {len(events)} events this week")
                all_events.extend(events)
            except Exception as exc:
                print(f"  [Error fetching {teacher}]: {exc}")

    html_content = generate_html(all_events, now_shanghai)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "schedule.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n✅ Generated {out_path} ({len(html_content)} bytes)")
    print(f"   Total events this week: {len(all_events)}")


if __name__ == "__main__":
    main()

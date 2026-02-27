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

        events.append({
            "teacher": teacher,
            "summary": summary_m.group(1).strip(),
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

    def event_to_block(ev, col_idx):
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
        return f'''<div class="ev" style="top:{top}px;height:{height}px;
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

        blocks_html = ""
        for ev in events_by_day[d]:
            blocks_html += event_to_block(ev, i)

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
            sidebar_items += f'<div class="sidebar-ev"><span class="sidebar-time">{time_str}</span><span class="sidebar-title">{html_mod.escape(ev["summary"])}</span></div>'
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

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>教师课表日程</title>
<meta name="description" content="NYK 教师课表实时日程总览">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0f1117;--surface:#1a1d27;--surface2:#232733;--border:#2a2e3a;
  --text:#e4e6ed;--text2:#9ca0ae;--text3:#6b7080;
  --radius:12px;--radius-sm:8px;
}}
body{{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;}}
h1{{font-size:1.4rem;font-weight:700;letter-spacing:-0.02em}}

/* Layout */
.shell{{display:flex;flex-direction:column;height:100vh;overflow:hidden}}
.topbar{{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--border);flex-shrink:0;backdrop-filter:blur(12px);background:rgba(15,17,23,0.85);position:sticky;top:0;z-index:10}}
.topbar-left{{display:flex;align-items:center;gap:12px}}
.topbar-right{{display:flex;align-items:center;gap:12px}}
.sync-badge{{font-size:0.72rem;color:var(--text3);background:var(--surface2);padding:4px 10px;border-radius:20px;white-space:nowrap}}
.sync-badge::before{{content:'';display:inline-block;width:6px;height:6px;background:#22c55e;border-radius:50%;margin-right:6px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}

/* Tabs */
.tabs{{display:flex;gap:6px;flex-wrap:wrap}}
.tab{{padding:6px 14px;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--text2);
  font-size:0.8rem;font-weight:500;cursor:pointer;transition:all .2s;font-family:inherit}}
.tab:hover{{background:var(--surface2);color:var(--text)}}
.tab.active{{background:var(--text);color:var(--bg);border-color:var(--text)}}

/* Main area */
.main{{display:flex;flex:1;overflow:hidden}}
.calendar-area{{flex:1;overflow-y:auto;overflow-x:auto;padding:0}}
.sidebar{{width:280px;flex-shrink:0;border-left:1px solid var(--border);overflow-y:auto;padding:20px;background:var(--surface)}}

/* Week header */
.week-header{{display:flex;align-items:center;justify-content:space-between;padding:12px 24px;border-bottom:1px solid var(--border);flex-shrink:0}}
.week-label{{font-size:0.9rem;font-weight:600;color:var(--text2)}}

/* Grid */
.grid-wrap{{display:flex;position:relative;min-width:700px}}
.time-gutter{{width:56px;flex-shrink:0;position:relative;border-right:1px solid var(--border)}}
.time-label{{position:absolute;right:12px;font-size:0.7rem;color:var(--text3);transform:translateY(-50%);font-variant-numeric:tabular-nums}}
.days-container{{display:flex;flex:1}}
.day-col{{flex:1;min-width:0;border-right:1px solid var(--border);position:relative}}
.day-col:last-child{{border-right:none}}
.day-header{{text-align:center;padding:10px 4px 8px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg);z-index:2}}
.weekday{{display:block;font-size:0.72rem;color:var(--text3);font-weight:500;text-transform:uppercase;letter-spacing:0.05em}}
.date-num{{display:inline-flex;align-items:center;gap:4px;font-size:0.85rem;font-weight:600;color:var(--text2);margin-top:2px}}
.today-col .weekday{{color:var(--text)}}
.today-col .date-num{{color:#fff;background:#7c3aed;padding:2px 10px;border-radius:20px}}
.today-dot{{display:none}}
.day-body{{position:relative;}}

/* Hour gridlines */
.day-body::before{{
  content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(to bottom,transparent,transparent 59px,var(--border) 59px,var(--border) 60px);
  pointer-events:none;z-index:0;
}}

/* Event block */
.ev{{position:absolute;left:3px;right:3px;border-radius:var(--radius-sm);padding:4px 8px;overflow:hidden;
  cursor:default;z-index:1;display:flex;flex-direction:column;gap:1px;transition:opacity .25s,transform .15s;}}
.ev:hover{{transform:scale(1.02);z-index:5;box-shadow:0 4px 20px rgba(0,0,0,0.4)}}
.ev-time{{font-size:0.65rem;font-weight:600;opacity:0.7;white-space:nowrap}}
.ev-title{{font-size:0.72rem;font-weight:500;line-height:1.3;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.ev.hidden{{opacity:0.08;pointer-events:none;transform:scale(0.95)}}

/* All-day row */
.allday-row{{display:flex;min-height:28px;border-bottom:1px solid var(--border)}}
.allday-gutter{{width:56px;flex-shrink:0;border-right:1px solid var(--border);display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:0.65rem;color:var(--text3)}}
.allday-cells{{display:flex;flex:1}}
.allday-cell{{flex:1;min-width:0;border-right:1px solid var(--border);padding:4px;display:flex;flex-wrap:wrap;gap:3px;align-items:center}}
.allday-cell:last-child{{border-right:none}}
.allday-pill{{font-size:0.65rem;padding:2px 8px;border-radius:12px;white-space:nowrap;font-weight:500}}
.allday-pill.hidden{{opacity:0.08}}

/* Sidebar */
.sidebar-title-main{{font-size:1rem;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.sidebar-title-main::before{{content:'📋'}}
.sidebar-teacher{{margin-bottom:16px}}
.sidebar-teacher-name{{font-size:0.82rem;font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.sidebar-ev{{display:flex;flex-direction:column;padding:8px 10px;background:var(--surface2);border-radius:var(--radius-sm);margin-bottom:4px;transition:opacity .25s}}
.sidebar-ev.hidden{{opacity:0.08}}
.sidebar-time{{font-size:0.7rem;color:var(--text3);font-variant-numeric:tabular-nums;font-weight:500}}
.sidebar-title{{font-size:0.78rem;font-weight:500;margin-top:2px}}
.sidebar-empty{{color:var(--text3);font-size:0.85rem;text-align:center;padding:40px 0}}

/* Now line */
.now-line{{position:absolute;left:0;right:0;height:2px;background:#f43f5e;z-index:3;pointer-events:none}}
.now-line::before{{content:'';position:absolute;left:-4px;top:-3px;width:8px;height:8px;border-radius:50%;background:#f43f5e}}

/* Mobile */
@media(max-width:860px){{
  .sidebar{{display:none}}
  .topbar{{padding:12px 16px;flex-wrap:wrap;gap:8px}}
  .tabs{{order:3;width:100%}}
  .grid-wrap{{min-width:580px}}
}}
@media(max-width:600px){{
  .grid-wrap{{min-width:480px}}
  .time-gutter{{width:40px}}
  .time-label{{font-size:0.6rem;right:6px}}
  .ev-title{{font-size:0.65rem}}
  .day-header{{padding:6px 2px 4px}}
}}
</style>
</head>
<body>
<div class="shell">
  <div class="topbar">
    <div class="topbar-left">
      <h1>教师课表日程</h1>
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
        <div class="time-gutter" style="height:{(HOUR_END - HOUR_START) * HOUR_HEIGHT}px;">
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
// Teacher filter
document.getElementById('tabs').addEventListener('click', e => {{
  const btn = e.target.closest('.tab');
  if (!btn) return;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  const filter = btn.dataset.filter;

  document.querySelectorAll('.ev').forEach(el => {{
    el.classList.toggle('hidden', filter !== 'all' && el.dataset.teacher !== filter);
  }});
  document.querySelectorAll('.allday-pill').forEach(el => {{
    el.classList.toggle('hidden', filter !== 'all' && el.dataset.teacher !== filter);
  }});
  document.querySelectorAll('.sidebar-teacher').forEach(el => {{
    // Show/hide sidebar sections
  }});
}});

// Now line
(function() {{
  const now = new Date();
  const todayStr = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0');
  const col = document.querySelector('.day-col[data-date="'+todayStr+'"]');
  if (!col) return;
  const body = col.querySelector('.day-body');
  const h = now.getHours() + now.getMinutes()/60;
  const startH = {HOUR_START};
  if (h < startH || h > {HOUR_END}) return;
  const top = (h - startH) * {HOUR_HEIGHT};
  const line = document.createElement('div');
  line.className = 'now-line';
  line.style.top = top + 'px';
  body.appendChild(line);

  // Auto-scroll to now line
  const area = document.querySelector('.calendar-area');
  if (area) area.scrollTop = Math.max(0, top - 120);
}})();
</script>
</body>
</html>'''


def main():
    now_shanghai = datetime.datetime.now(datetime.timezone.utc).astimezone(SHANGHAI_TZ)
    today = now_shanghai.date()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    print(f"Generating calendar page for week {week_start} – {week_end}...")

    all_events = []
    for teacher, url in ICS_FEEDS.items():
        print(f"  Fetching {teacher}...")
        events = fetch_events(teacher, url, week_start, week_end)
        print(f"    → {len(events)} events this week")
        all_events.extend(events)

    html_content = generate_html(all_events, now_shanghai)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n✅ Generated {out_path} ({len(html_content)} bytes)")
    print(f"   Total events this week: {len(all_events)}")


if __name__ == "__main__":
    main()

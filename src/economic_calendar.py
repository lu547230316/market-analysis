"""经济数据日历 — 本周/下周关键事件"""
from datetime import datetime, timedelta

FOMC_DATES_2026 = [
    "2026-01-28", "2026-03-18", "2026-05-06",
    "2026-06-17", "2026-07-29", "2026-09-23",
    "2026-11-05", "2026-12-16",
]

WEEKLY_PATTERN = {
    "Monday":    [],
    "Tuesday":   ["JOLTS职位空缺 (10:00)"],
    "Wednesday": ["MBA抵押贷款申请 (07:00)", "EIA原油库存 (10:30)", "FOMC会议纪要 (14:00, 如有)"],
    "Thursday":  ["初请失业金人数 (08:30)", "续请失业金人数 (08:30)"],
    "Friday":    [],
    "Saturday":  [],
    "Sunday":    [],
}


def get_upcoming_events(days_ahead: int = 5) -> list:
    today = datetime.now()
    events = []

    for date_str in FOMC_DATES_2026:
        event_date = datetime.strptime(date_str, "%Y-%m-%d")
        delta = (event_date - today).days
        if 0 <= delta <= days_ahead:
            events.append({
                "date": date_str,
                "event": "FOMC利率决议",
                "importance": "极高",
                "days_away": delta,
            })

    for day_offset in range(days_ahead + 1):
        check_date = today + timedelta(days=day_offset)
        weekday = check_date.strftime("%A")

        if check_date.weekday() == 4 and check_date.day <= 7:
            events.append({
                "date": check_date.strftime("%Y-%m-%d"),
                "event": "非农就业报告 (NFP)",
                "importance": "极高",
                "days_away": day_offset,
            })

        if 10 <= check_date.day <= 15 and check_date.weekday() in [2, 3]:
            events.append({
                "date": check_date.strftime("%Y-%m-%d"),
                "event": "CPI 消费者物价指数",
                "importance": "极高",
                "days_away": day_offset,
            })

        weekly_events = WEEKLY_PATTERN.get(weekday, [])
        for evt in weekly_events:
            events.append({
                "date": check_date.strftime("%Y-%m-%d"),
                "event": evt,
                "importance": "中",
                "days_away": day_offset,
            })

    seen = set()
    unique = []
    for e in events:
        key = (e["date"], e["event"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    unique.sort(key=lambda x: (x["days_away"], 0 if x["importance"] == "极高" else 1))

    return unique


def get_earnings_calendar(days_ahead: int = 5) -> list:
    key_earners = [
        ("NVDA", "2026-05-28"), ("CRM", "2026-05-29"), ("ORCL", "2026-06-10"),
        ("ADBE", "2026-06-12"), ("FDX", "2026-06-18"), ("MU", "2026-06-25"),
        ("NKE", "2026-06-26"), ("PEP", "2026-07-08"), ("DAL", "2026-07-10"),
    ]
    today = datetime.now()
    upcoming = []
    for symbol, date_str in key_earners:
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            delta = (event_date - today).days
            if -1 <= delta <= days_ahead:
                label = "(今天)" if delta == 0 else f"(距今{days_ahead}天)" if delta > 0 else "(已发布)"
                upcoming.append(f"{date_str}: {symbol} 财报 {label}")
        except Exception:
            pass
    return upcoming


def format_calendar_for_prompt(days_ahead: int = 5) -> str:
    events = get_upcoming_events(days_ahead)
    earnings = get_earnings_calendar(days_ahead)

    lines = []
    if events:
        lines.append("### 未来关键经济事件")
        for e in events[:15]:
            emoji = "[极高]" if e["importance"] == "极高" else "[中]"
            days = "(今天)" if e["days_away"] == 0 else f"(+{e['days_away']}天)"
            lines.append(f"- {emoji} {e['date']} {days}: {e['event']}")

    if earnings:
        lines.append("\n### 即将发布财报")
        for e in earnings[:10]:
            lines.append(f"- {e}")

    return "\n".join(lines) if lines else "暂无近期关键经济事件或财报"
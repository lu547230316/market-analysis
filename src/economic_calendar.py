"""经济日历 — 基于固定关键事件 + AKShare 补充 v3.0"""
import akshare as ak
from datetime import datetime, timedelta


def format_calendar_for_prompt(days_ahead: int = 5) -> str:
    """生成经济日历文本"""
    today = datetime.now()
    lines = ["## 近期关键经济事件\n"]

    # Key US economic events (manual schedule)
    key_events = {
        (today + timedelta(days=1)).strftime("%A"): "关注周度失业数据",
        "周三": "EIA原油库存（美东10:30）",
        "周四": "周度初请失业金（美东8:30）",
        "周五": "关注美联储官员讲话",
    }

    for day_offset in range(days_ahead):
        event_date = today + timedelta(days=day_offset)
        day_name = event_date.strftime("%A")
        date_str = event_date.strftime("%m/%d")
        events = []

        # Add fixed weekly events
        for key, event in key_events.items():
            if key in day_name:
                events.append(event)

        if events:
            lines.append(f"\n**{date_str} ({day_name})**")
            for e in events:
                lines.append(f"  - {e}")

    # Try to get China economic calendar
    try:
        df = ak.macro_china_market_reference()
        if not df.empty:
            lines.append("\n## 中国市场参考")
            lines.append(str(df.tail(3).to_string()))
    except Exception:
        pass

    lines.append("\n> 注: 完整经济日历请参考 investing.com/economic-calendar")
    return "\n".join(lines)

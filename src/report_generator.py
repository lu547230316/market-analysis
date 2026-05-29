"""报告生成编排器 — 协调数据采集 → AI分析 → 邮件发送"""
import traceback
from datetime import datetime

from .data_collector import get_market_summary, get_top_movers, get_weekly_summary
from .news_collector import fetch_all_news, fetch_yfinance_news
from .macro_data import get_macro_data, get_interest_rates_summary
from .ai_analyzer import generate_daily_report, generate_weekly_report
from .email_sender import send_daily_report, send_weekly_report


def run_daily() -> bool:
    print(f"[{datetime.now()}] === 日报流程启动 ===")
    try:
        print("[1/5] 采集行情数据...")
        market = get_market_summary()

        print("[2/5] 扫描异动个股...")
        movers = get_top_movers(top_n=10)

        print("[3/5] 采集宏观数据...")
        macro = get_macro_data()

        print("[4/5] 采集新闻...")
        news_api = fetch_all_news(days=1, max_articles=50)
        news_yf = fetch_yfinance_news()
        all_news = news_api + news_yf
        seen = set()
        news_deduped = []
        for n in all_news:
            key = n["title"][:80]
            if key not in seen:
                seen.add(key)
                news_deduped.append(n)
        news_deduped.sort(key=lambda x: x.get("score", 0), reverse=True)
        print(f"  获取新闻 {len(news_deduped)} 条")

        print("[5/5] AI 分析 + 邮件发送...")
        report = generate_daily_report(market, movers, macro, news_deduped[:40])
        success = send_daily_report(report)
        print(f"[{datetime.now()}] === 日报流程完成 ===")
        return success
    except Exception as e:
        print(f"[{datetime.now()}] 日报流程失败: {e}")
        traceback.print_exc()
        return False


def run_weekly() -> bool:
    print(f"[{datetime.now()}] === 周报流程启动 ===")
    try:
        print("[1/4] 采集周度行情...")
        weekly = get_weekly_summary()

        print("[2/4] 采集宏观数据...")
        macro = get_macro_data()

        print("[3/4] 采集本周新闻...")
        news = fetch_all_news(days=7, max_articles=80)

        print("[4/4] AI 分析 + 邮件发送...")
        report = generate_weekly_report(weekly, macro, news[:60])
        success = send_weekly_report(report)
        print(f"[{datetime.now()}] === 周报流程完成 ===")
        return success
    except Exception as e:
        print(f"[{datetime.now()}] 周报流程失败: {e}")
        traceback.print_exc()
        return False
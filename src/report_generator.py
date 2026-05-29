"""报告生成编排器 — v2.0 四维数据分析"""
import traceback
from datetime import datetime

from .data_collector import get_market_summary, get_top_movers, get_weekly_summary, get_valuation_data, get_sector_flows
from .news_collector import fetch_all_news, fetch_yfinance_news
from .macro_data import get_macro_data, get_interest_rates_summary
from .technical_analyzer import get_index_technicals
from .sentiment_data import get_market_sentiment
from .economic_calendar import format_calendar_for_prompt
from .ai_analyzer import generate_daily_report, generate_weekly_report
from .email_sender import send_daily_report, send_weekly_report


def run_daily() -> bool:
    print(f"[{datetime.now()}] === 日报流程启动 (v2.0) ===")
    try:
        print("[1/7] 采集行情数据...")
        market = get_market_summary()

        print("[2/7] 技术面分析...")
        technicals = get_index_technicals()

        print("[3/7] 情绪数据...")
        sentiment = get_market_sentiment()

        print("[4/7] 资金流 + 估值...")
        fund_flows = get_sector_flows()
        valuations = get_valuation_data()

        print("[5/7] 异动扫描 + 宏观 + 日历...")
        movers = get_top_movers(top_n=10)
        macro = get_macro_data()
        calendar = format_calendar_for_prompt(days_ahead=5)

        print("[6/7] 新闻采集...")
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

        print("[7/7] AI 分析 + 邮件发送...")
        report = generate_daily_report(
            market, movers, macro, news_deduped[:40],
            technical_data=technicals,
            sentiment_data=sentiment,
            fund_flow_data=fund_flows,
            valuation_data=valuations,
            calendar_data=calendar,
        )
        success = send_daily_report(report)
        print(f"[{datetime.now()}] === 日报流程完成 ===")
        return success
    except Exception as e:
        print(f"[{datetime.now()}] 日报流程失败: {e}")
        traceback.print_exc()
        return False


def run_weekly() -> bool:
    print(f"[{datetime.now()}] === 周报流程启动 (v2.0) ===")
    try:
        print("[1/6] 周度行情...")
        weekly = get_weekly_summary()

        print("[2/6] 技术面 + 情绪...")
        technicals = get_index_technicals()
        sentiment = get_market_sentiment()

        print("[3/6] 资金流 + 宏观 + 日历...")
        fund_flows = get_sector_flows()
        macro = get_macro_data()
        calendar = format_calendar_for_prompt(days_ahead=7)

        print("[4/6] 新闻采集...")
        news = fetch_all_news(days=7, max_articles=80)

        print("[5/6] AI 分析 + 邮件发送...")
        report = generate_weekly_report(
            weekly, macro, news[:60],
            technical_data=technicals,
            sentiment_data=sentiment,
            fund_flow_data=fund_flows,
            calendar_data=calendar,
        )
        success = send_weekly_report(report)
        print(f"[{datetime.now()}] === 周报流程完成 ===")
        return success
    except Exception as e:
        print(f"[{datetime.now()}] 周报流程失败: {e}")
        traceback.print_exc()
        return False
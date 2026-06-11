"""报告生成编排 v5.0 — 多 Agent 并行架构 + 纠错验证"""
import traceback
from datetime import datetime

from .data_cache import get_cache, reset_cache
from .parallel_runner import ParallelRunner
from .data_collector import (
    get_market_summary, get_top_movers, get_weekly_summary,
    get_valuation_data, get_sector_flows, INDICES, WATCHLIST, SECTOR_STOCKS,
)
from .news_collector import fetch_all_news
from .macro_data import get_macro_data
from .technical_analyzer import get_index_technicals
from .sentiment_data import get_market_sentiment
from .economic_calendar import format_calendar_for_prompt
from .kol_collector import get_kol_opinions, format_kol_for_prompt
from .news_analyzer import analyze_news_sentiment, format_news_sentiment_for_prompt
from .mag7_analyzer import (
    analyze_mag7, analyze_soxx,
    format_mag7_for_prompt, format_soxx_for_prompt,
    MAGNIFICENT_7, SOXX_HOLDINGS,
)
from .error_checker import run_full_check, format_error_check_for_prompt
from .ai_analyzer import generate_daily_report, generate_weekly_report
from .email_sender import send_daily_report, send_weekly_report


def _prefetch_cache():
    """预热缓存 — 集中预取所有数据"""
    cache = get_cache()
    all_stocks = set(WATCHLIST)
    for stocks in SECTOR_STOCKS.values():
        all_stocks.update(stocks)
    # 加入 SOXX 权重股
    all_stocks.update(SOXX_HOLDINGS.keys())
    all_stocks.add("SOXX")
    all_indices = set(INDICES.values())
    cache.prefetch_all(list(all_stocks), list(all_indices))
    print(f"  预取完成: {cache.get_stats()}")
    return cache


def run_daily() -> bool:
    print(f"\n{'='*70}")
    print(f"[{datetime.now()}] === 日报流程启动 (v5.0 多Agent并行架构) ===")
    print(f"{'='*70}\n")

    try:
        # Phase 1: 预热缓存
        print("[Phase 0] 预热数据缓存...")
        cache = _prefetch_cache()

        # Phase 2: 多 Agent 并行数据采集
        runner = ParallelRunner(max_workers=8)

        # 添加所有并行任务
        runner.add("市场行情", get_market_summary)
        runner.add("技术分析", get_index_technicals)
        runner.add("情绪数据", get_market_sentiment)
        runner.add("资金流向", get_sector_flows)
        runner.add("估值数据", get_valuation_data)
        runner.add("异动扫描", get_top_movers, 10)
        runner.add("宏观数据", get_macro_data)
        runner.add("经济日历", format_calendar_for_prompt, 5)
        runner.add("新闻采集", fetch_all_news, 1, 60)
        runner.add("七姐妹分析", analyze_mag7, timeout=180)
        runner.add("SOXX分析", analyze_soxx, timeout=180)

        # 并行执行
        results = runner.run_all()

        # 提取结果
        market = results.get("市场行情", {"indices": [], "sectors": [], "futures": []})
        technicals = results.get("技术分析", {})
        sentiment = results.get("情绪数据", {"sentiment": "中性", "risk_score": 4, "vix": {}, "breadth": {}})
        fund_flows = results.get("资金流向", {})
        valuations = results.get("估值数据", [])
        movers = results.get("异动扫描", {"gainers": [], "losers": [], "volume_anomalies": []})
        macro = results.get("宏观数据", {"indicators": []})
        calendar = results.get("经济日历", "")
        news = results.get("新闻采集", [])
        mag7_data = results.get("七姐妹分析", [])
        soxx_data = results.get("SOXX分析", {})

        # Phase 3: 后处理 Agent（依赖新闻数据）
        print("[Phase 2] 后处理 Agent...")
        post_runner = ParallelRunner(max_workers=4)
        post_runner.add("KOL观点提取", get_kol_opinions, news)
        post_runner.add("新闻情绪分析", analyze_news_sentiment, news)
        post_results = post_runner.run_all()

        kol_data = post_results.get("KOL观点提取", {"opinions": [], "summary": {}})
        news_sentiment = post_results.get("新闻情绪分析", {"overall_sentiment": "中性", "bullish_news": [], "bearish_news": []})

        # Phase 4: AI 分析生成
        print("[Phase 3] AI 分析生成...")
        report = generate_daily_report(
            market_data=market,
            movers=movers,
            macro_data=macro,
            news=news[:40],
            technical_data=technicals,
            sentiment_data=sentiment,
            fund_flow_data=fund_flows,
            valuation_data=valuations,
            calendar_data=calendar,
            kol_data=kol_data,
            news_sentiment=news_sentiment,
            mag7_data=mag7_data,
            soxx_data=soxx_data,
        )

        # Phase 5: 纠错验证
        print("[Phase 4] 纠错验证...")
        error_check = run_full_check(
            market_data=market,
            technicals=technicals,
            sentiment=sentiment,
            news_data={"articles": news, "sentiment": news_sentiment},
            report=report,
        )

        # 如果有关键错误，附加纠错报告
        if error_check["overall_status"] == "FAIL":
            error_section = format_error_check_for_prompt(error_check)
            report += f"\n\n---\n\n{error_section}"

        # Phase 6: 发送邮件
        print("[Phase 5] 邮件发送...")
        success = send_daily_report(report)

        print(f"\n[{datetime.now()}] === 日报流程完成 ===")
        print(f"Agent 执行摘要:\n{runner.get_summary()}")
        return success

    except Exception as e:
        print(f"[{datetime.now()}] 日报流程失败: {e}")
        traceback.print_exc()
        return False
    finally:
        reset_cache()


def run_weekly() -> bool:
    print(f"\n{'='*70}")
    print(f"[{datetime.now()}] === 周报流程启动 (v5.0 多Agent并行架构) ===")
    print(f"{'='*70}\n")

    try:
        # Phase 1: 预热缓存
        print("[Phase 0] 预热数据缓存...")
        cache = _prefetch_cache()

        # Phase 2: 多 Agent 并行数据采集
        runner = ParallelRunner(max_workers=8)

        runner.add("周度行情", get_weekly_summary)
        runner.add("技术分析", get_index_technicals)
        runner.add("情绪数据", get_market_sentiment)
        runner.add("资金流向", get_sector_flows)
        runner.add("宏观数据", get_macro_data)
        runner.add("经济日历", format_calendar_for_prompt, 7)
        runner.add("新闻采集", fetch_all_news, 7, 80)
        runner.add("七姐妹分析", analyze_mag7, timeout=180)
        runner.add("SOXX分析", analyze_soxx, timeout=180)

        results = runner.run_all()

        weekly = results.get("周度行情", {"indices": [], "sectors": [], "futures": []})
        technicals = results.get("技术分析", {})
        sentiment = results.get("情绪数据", {})
        fund_flows = results.get("资金流向", {})
        macro = results.get("宏观数据", {"indicators": []})
        calendar = results.get("经济日历", "")
        news = results.get("新闻采集", [])
        mag7_data = results.get("七姐妹分析", [])
        soxx_data = results.get("SOXX分析", {})

        # Phase 3: 后处理
        print("[Phase 2] 后处理 Agent...")
        post_runner = ParallelRunner(max_workers=4)
        post_runner.add("KOL观点提取", get_kol_opinions, news)
        post_runner.add("新闻情绪分析", analyze_news_sentiment, news)
        post_results = post_runner.run_all()

        kol_data = post_results.get("KOL观点提取", {"opinions": [], "summary": {}})
        news_sentiment = post_results.get("新闻情绪分析", {})

        # Phase 4: AI 分析
        print("[Phase 3] AI 分析生成...")
        report = generate_weekly_report(
            weekly_data=weekly,
            macro_data=macro,
            news=news[:60],
            technical_data=technicals,
            sentiment_data=sentiment,
            fund_flow_data=fund_flows,
            calendar_data=calendar,
            kol_data=kol_data,
            news_sentiment=news_sentiment,
            mag7_data=mag7_data,
            soxx_data=soxx_data,
        )

        # Phase 5: 纠错验证
        print("[Phase 4] 纠错验证...")
        error_check = run_full_check(
            market_data=weekly,
            technicals=technicals,
            sentiment=sentiment,
            news_data={"articles": news, "sentiment": news_sentiment},
            report=report,
        )

        if error_check["overall_status"] == "FAIL":
            error_section = format_error_check_for_prompt(error_check)
            report += f"\n\n---\n\n{error_section}"

        # Phase 6: 发送
        print("[Phase 5] 邮件发送...")
        success = send_weekly_report(report)

        print(f"\n[{datetime.now()}] === 周报流程完成 ===")
        print(f"Agent 执行摘要:\n{runner.get_summary()}")
        return success

    except Exception as e:
        print(f"[{datetime.now()}] 周报流程失败: {e}")
        traceback.print_exc()
        return False
    finally:
        reset_cache()

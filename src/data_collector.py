"""行情数据采集 — yfinance 美股指数、板块、期货、异动股"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# 主要指数
INDICES = {
    "标普500": "^GSPC",
    "纳斯达克": "^IXIC",
    "道琼斯": "^DJI",
    "罗素2000": "^RUT",
}

# 板块 ETF
SECTORS = {
    "科技": "XLK",
    "金融": "XLF",
    "能源": "XLE",
    "医疗": "XLV",
    "工业": "XLI",
    "消费必需品": "XLP",
    "可选消费": "XLY",
    "原材料": "XLB",
    "公用事业": "XLU",
    "房地产": "XLRE",
    "通信": "XLC",
}

# 期货（盘前参考）
FUTURES = {
    "标普期货": "ES=F",
    "纳指期货": "NQ=F",
    "道指期货": "YM=F",
    "原油": "CL=F",
    "黄金": "GC=F",
}

# 高关注度个股
WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AMD", "INTC", "AVGO", "SMCI", "PLTR", "SNOW", "CRWD",
    "JPM", "GS", "BAC", "C", "WFC",
    "XOM", "CVX", "COP",
    "LLY", "UNH", "JNJ", "PFE",
    "BA", "CAT", "GE",
]


def _ticker_info(ticker: str) -> dict:
    """获取单只标的快照"""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="2d")
        if hist.empty:
            return {}
        close_today = float(hist["Close"].iloc[-1])
        prev_close = info.get("previousClose", float(hist["Close"].iloc[-2]) if len(hist) > 1 else close_today)
        change_pct = ((close_today - prev_close) / prev_close) * 100 if prev_close else 0
        return {
            "symbol": ticker,
            "name": info.get("shortName", info.get("longName", ticker)),
            "price": round(close_today, 2),
            "change_pct": round(change_pct, 2),
            "volume": info.get("volume", 0),
            "avg_volume": info.get("averageVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        }
    except Exception:
        return {}


def get_market_summary() -> dict:
    """获取大盘摘要：指数 + 板块 + 期货"""
    result = {"indices": [], "sectors": [], "futures": [], "timestamp": datetime.now().isoformat()}

    for name, sym in INDICES.items():
        info = _ticker_info(sym)
        if info:
            info["display_name"] = name
            result["indices"].append(info)

    for name, sym in SECTORS.items():
        info = _ticker_info(sym)
        if info:
            info["display_name"] = name
            result["sectors"].append(info)

    for name, sym in FUTURES.items():
        info = _ticker_info(sym)
        if info:
            info["display_name"] = name
            result["futures"].append(info)

    return result


def get_top_movers(top_n: int = 10) -> dict:
    """扫描异动个股 — 从观察列表 + 板块成分股找涨跌幅最大"""
    all_stocks = set(WATCHLIST)
    for sym in ["SPY", "QQQ", "IWM"]:
        try:
            t = yf.Ticker(sym)
            holdings = t.info.get("holdings", [])
            for h in holdings[:20]:
                s = h.get("symbol", "")
                if s:
                    all_stocks.add(s)
        except Exception:
            pass

    stocks_data = []
    for sym in list(all_stocks)[:80]:
        info = _ticker_info(sym)
        if info and info.get("change_pct") is not None:
            stocks_data.append(info)

    stocks_data.sort(key=lambda x: x.get("change_pct", 0), reverse=True)
    gainers = [s for s in stocks_data if s["change_pct"] > 0][:top_n]
    losers = sorted(
        [s for s in stocks_data if s["change_pct"] < 0],
        key=lambda x: x["change_pct"],
    )[:top_n]

    volume_anomalies = []
    for s in stocks_data:
        avg_vol = s.get("avg_volume", 0)
        cur_vol = s.get("volume", 0)
        if avg_vol > 0 and cur_vol > avg_vol * 2:
            volume_anomalies.append({**s, "vol_ratio": round(cur_vol / avg_vol, 1)})
    volume_anomalies.sort(key=lambda x: x["vol_ratio"], reverse=True)

    return {
        "gainers": gainers,
        "losers": losers,
        "volume_anomalies": volume_anomalies[:top_n],
    }


def get_weekly_summary() -> dict:
    """获取周度数据"""
    result = {"indices": [], "sectors": [], "timestamp": datetime.now().isoformat()}

    for name, sym in INDICES.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="5d")
            if hist.empty:
                continue
            close_last = float(hist["Close"].iloc[-1])
            close_first = float(hist["Close"].iloc[0])
            week_change = ((close_last - close_first) / close_first) * 100
            week_high = float(hist["High"].max())
            week_low = float(hist["Low"].min())
            result["indices"].append({
                "display_name": name,
                "symbol": sym,
                "price": round(close_last, 2),
                "week_change_pct": round(week_change, 2),
                "week_high": round(week_high, 2),
                "week_low": round(week_low, 2),
            })
        except Exception:
            pass

    for name, sym in SECTORS.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="5d")
            if hist.empty:
                continue
            week_change = ((float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[0])) / float(hist["Close"].iloc[0])) * 100
            result["sectors"].append({
                "display_name": name,
                "symbol": sym,
                "week_change_pct": round(week_change, 2),
            })
        except Exception:
            pass

    result["sectors"].sort(key=lambda x: x["week_change_pct"], reverse=True)
    return result


def get_valuation_data(tickers: list[str] = None) -> list[dict]:
    """获取关键估值指标"""
    if tickers is None:
        tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
    result = []
    for sym in tickers:
        try:
            t = yf.Ticker(sym)
            info = t.info
            result.append({
                "symbol": sym,
                "name": info.get("shortName", sym),
                "pe_ttm": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "eps_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
                "market_cap": info.get("marketCap"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
            })
        except Exception:
            pass
    return result


def get_sector_flows() -> dict:
    """板块资金流 — 通过量价关系推算"""
    sectors_flow = {}
    for name, sym in SECTORS.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="1mo")
            if hist.empty or len(hist) < 5:
                continue
            vol_5d = float(hist["Volume"].iloc[-5:].mean())
            vol_20d = float(hist["Volume"].iloc[-20:].mean()) if len(hist) >= 20 else vol_5d
            vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
            price_change_5d = (float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[-5])) / float(hist["Close"].iloc[-5]) * 100

            if price_change_5d > 0 and vol_ratio > 1.2:
                flow = "显著流入"
            elif price_change_5d > 0 and vol_ratio > 1:
                flow = "温和流入"
            elif price_change_5d < 0 and vol_ratio > 1.2:
                flow = "显著流出"
            elif price_change_5d < 0 and vol_ratio > 1:
                flow = "温和流出"
            else:
                flow = "持平"

            sectors_flow[name] = {
                "5d_change_pct": round(price_change_5d, 2),
                "vol_ratio": round(vol_ratio, 2),
                "flow": flow,
            }
        except Exception:
            pass
    return sectors_flow
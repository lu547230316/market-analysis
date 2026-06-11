"""行情数据采集 — AKShare 国内源 v4.0（带缓存优化）"""
import pandas as pd
from datetime import datetime
from .data_cache import get_cache

INDICES = {
    "标普500": ".INX",
    "纳斯达克": ".IXIC",
    "道琼斯": ".DJI",
}

SECTOR_STOCKS = {
    "科技": ["AAPL", "MSFT", "NVDA"],
    "金融": ["JPM", "GS", "BAC"],
    "能源": ["XOM", "CVX", "COP"],
    "医疗": ["LLY", "UNH", "JNJ"],
    "消费": ["AMZN", "WMT", "COST"],
    "通信": ["META", "GOOGL", "NFLX"],
    "工业": ["BA", "CAT", "GE"],
}

WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AMD", "INTC", "AVGO", "SMCI", "PLTR", "SNOW", "CRWD",
    "JPM", "GS", "BAC", "C", "WFC",
    "XOM", "CVX", "COP",
    "LLY", "UNH", "JNJ", "PFE",
    "BA", "CAT", "GE",
]


def get_market_summary() -> dict:
    cache = get_cache()
    result = {"indices": [], "sectors": [], "futures": [], "timestamp": datetime.now().isoformat()}

    for name, sym in INDICES.items():
        df = cache.get_index(sym)
        if df is None or df.empty:
            continue
        hist = df.tail(5)
        close_last = float(hist["close"].iloc[-1])
        close_first = float(hist["close"].iloc[0])
        week_change = ((close_last - close_first) / close_first) * 100 if close_first else 0
        week_high = float(hist["high"].max())
        week_low = float(hist["low"].min())
        result["indices"].append({
            "display_name": name, "symbol": sym,
            "price": round(close_last, 2), "week_change_pct": round(week_change, 2),
            "week_high": round(week_high, 2), "week_low": round(week_low, 2),
        })

    for sector, stocks in SECTOR_STOCKS.items():
        changes = []
        for s in stocks:
            df = cache.get_stock(s)
            if df is not None and len(df) >= 2:
                c = (float(df["close"].iloc[-1]) - float(df["close"].iloc[-2])) / float(df["close"].iloc[-2]) * 100
                changes.append(c)
        if changes:
            result["sectors"].append({
                "display_name": sector, "symbol": sector,
                "week_change_pct": round(sum(changes) / len(changes), 2),
            })
    result["sectors"].sort(key=lambda x: x["week_change_pct"], reverse=True)
    return result


def get_weekly_summary() -> dict:
    result = {"indices": [], "sectors": [], "futures": [], "timestamp": datetime.now().isoformat()}
    cache = get_cache()
    for name, sym in INDICES.items():
        df = cache.get_index(sym)
        if df is None or df.empty:
            continue
        hist = df.tail(5) if len(df) >= 5 else df
        close_last = float(hist["close"].iloc[-1])
        close_first = float(hist["close"].iloc[0])
        week_change = ((close_last - close_first) / close_first) * 100 if close_first else 0
        week_high = float(hist["high"].max())
        week_low = float(hist["low"].min())
        result["indices"].append({
            "display_name": name, "symbol": sym,
            "price": round(close_last, 2), "week_change_pct": round(week_change, 2),
            "week_high": round(week_high, 2), "week_low": round(week_low, 2),
        })
    for sector, stocks in SECTOR_STOCKS.items():
        changes = []
        for s in stocks:
            df = cache.get_stock(s)
            if df is not None and len(df) >= 5:
                c = (float(df["close"].iloc[-1]) - float(df["close"].iloc[0])) / float(df["close"].iloc[0]) * 100
                changes.append(c)
        if changes:
            result["sectors"].append({
                "display_name": sector, "symbol": sector,
                "week_change_pct": round(sum(changes) / len(changes), 2),
            })
    result["sectors"].sort(key=lambda x: x["week_change_pct"], reverse=True)
    return result


def get_top_movers(top_n: int = 10) -> dict:
    cache = get_cache()
    gainers, losers = [], []
    for sym in WATCHLIST:
        df = cache.get_stock(sym)
        if df is None or len(df) < 2:
            continue
        price = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0
        volume_today = int(df["volume"].iloc[-1]) if "volume" in df.columns else 0
        avg_vol = int(df["volume"].tail(20).mean()) if "volume" in df.columns and len(df) >= 20 else volume_today
        high_52w = float(df["high"].max()) if "high" in df.columns else price
        low_52w = float(df["low"].min()) if "low" in df.columns else price
        info = {
            "symbol": sym, "name": sym, "price": round(price, 2),
            "change_pct": round(change_pct, 2), "volume": volume_today,
            "avg_volume": avg_vol, "52w_high": round(high_52w, 2), "52w_low": round(low_52w, 2),
        }
        (gainers if change_pct > 0 else losers).append(info)
    gainers.sort(key=lambda x: x["change_pct"], reverse=True)
    losers.sort(key=lambda x: x["change_pct"])
    volume_anomalies = []
    for sym in WATCHLIST:
        df = cache.get_stock(sym)
        if df is not None and "volume" in df.columns and len(df) >= 20:
            vol_t = int(df["volume"].iloc[-1])
            avg_v = int(df["volume"].tail(20).mean())
            if avg_v > 0 and vol_t / avg_v > 2.0:
                volume_anomalies.append({"symbol": sym, "vol_ratio": round(vol_t / avg_v, 1)})
    volume_anomalies.sort(key=lambda x: x["vol_ratio"], reverse=True)
    return {"gainers": gainers[:top_n], "losers": losers[:top_n], "volume_anomalies": volume_anomalies[:top_n]}


def get_valuation_data(tickers: list = None) -> list:
    if tickers is None:
        tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
    cache = get_cache()
    result = []
    for sym in tickers:
        try:
            df = cache.get_valuation(sym)
            if df is None or df.empty:
                result.append({"symbol": sym, "name": sym})
                continue
            row = df.iloc[-1] if len(df) > 0 else {}
            result.append({
                "symbol": sym, "name": sym,
                "pe_ttm": row.get("pe", row.get("市盈率", "N/A")),
                "pe_forward": "N/A", "peg_ratio": "N/A",
                "market_cap": row.get("market_cap", "N/A"),
            })
        except Exception:
            result.append({"symbol": sym, "name": sym})
    return result


def get_sector_flows() -> dict:
    cache = get_cache()
    sectors_flow = {}
    for name, stocks in SECTOR_STOCKS.items():
        changes, vol_changes = [], []
        for s in stocks:
            df = cache.get_stock(s)
            if df is not None and len(df) >= 20:
                pc = (float(df["close"].iloc[-1]) - float(df["close"].iloc[-5])) / float(df["close"].iloc[-5]) * 100
                changes.append(pc)
                if "volume" in df.columns:
                    v5 = df["volume"].iloc[-5:].mean()
                    v20 = df["volume"].iloc[-20:].mean()
                    vol_changes.append(v5 / v20 if v20 > 0 else 1)
        if changes:
            avg_price_change = sum(changes) / len(changes)
            avg_vol_ratio = sum(vol_changes) / len(vol_changes) if vol_changes else 1
            if avg_price_change > 0 and avg_vol_ratio > 1.1:
                flow = "流入"
            elif avg_price_change < 0 and avg_vol_ratio > 1.1:
                flow = "流出"
            else:
                flow = "持平"
            sectors_flow[name] = {"5d_change_pct": round(avg_price_change, 2), "vol_ratio": round(avg_vol_ratio, 2), "flow": flow}
    return sectors_flow

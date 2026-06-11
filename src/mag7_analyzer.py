"""七姐妹 + SOXX 权重股深度分析 v5.0 — 新闻 + 技术面 + 估值"""
import numpy as np
from datetime import datetime

from .data_cache import get_cache

# 美股七姐妹 (Magnificent 7)
MAGNIFICENT_7 = {
    "AAPL": {"name": "苹果 Apple", "sector": "消费电子/软件", "weight_in_sp500": 7.0},
    "MSFT": {"name": "微软 Microsoft", "sector": "云计算/软件", "weight_in_sp500": 6.8},
    "NVDA": {"name": "英伟达 NVIDIA", "sector": "半导体/AI芯片", "weight_in_sp500": 5.5},
    "GOOGL": {"name": "谷歌 Alphabet", "sector": "搜索/云计算/AI", "weight_in_sp500": 3.8},
    "AMZN": {"name": "亚马逊 Amazon", "sector": "电商/云计算", "weight_in_sp500": 3.5},
    "META": {"name": "Meta Platforms", "sector": "社交媒体/AI", "weight_in_sp500": 2.5},
    "TSLA": {"name": "特斯拉 Tesla", "sector": "电动车/能源/AI", "weight_in_sp500": 1.8},
}

# SOXX (半导体ETF) 主要权重股
SOXX_HOLDINGS = {
    "NVDA": {"name": "英伟达 NVIDIA", "soxx_weight": 10.5, "subsector": "AI/GPU"},
    "AVGO": {"name": "博通 Broadcom", "soxx_weight": 9.0, "subsector": "网络/存储芯片"},
    "AMD": {"name": "AMD", "soxx_weight": 5.5, "subsector": "CPU/GPU"},
    "QCOM": {"name": "高通 Qualcomm", "soxx_weight": 5.0, "subsector": "移动芯片/5G"},
    "INTC": {"name": "英特尔 Intel", "soxx_weight": 4.0, "subsector": "CPU/代工"},
    "TXN": {"name": "德州仪器 TI", "soxx_weight": 4.5, "subsector": "模拟芯片"},
    "MRVL": {"name": "Marvell", "soxx_weight": 3.5, "subsector": "网络/数据中心芯片"},
    "MU": {"name": "美光 Micron", "soxx_weight": 3.5, "subsector": "存储芯片"},
    "KLAC": {"name": "KLA", "soxx_weight": 3.0, "subsector": "半导体设备"},
    "LRCX": {"name": "Lam Research", "soxx_weight": 3.0, "subsector": "半导体设备"},
    "AMAT": {"name": "应用材料 Applied", "soxx_weight": 3.0, "subsector": "半导体设备"},
    "ASML": {"name": "ASML", "soxx_weight": 3.5, "subsector": "光刻机"},
    "ON": {"name": "安森美 ON Semi", "soxx_weight": 2.0, "subsector": "功率半导体"},
    "NXPI": {"name": "恩智浦 NXP", "soxx_weight": 2.0, "subsector": "汽车芯片"},
    "ADI": {"name": "ADI", "soxx_weight": 2.5, "subsector": "模拟芯片"},
    "TSM": {"name": "台积电 TSMC", "soxx_weight": 5.0, "subsector": "晶圆代工"},
}


def _compute_stock_technicals(closes: list) -> dict:
    """计算个股技术指标"""
    if len(closes) < 30:
        return {"error": "数据不足"}

    price = closes[-1]

    # RSI
    deltas = np.diff(closes)
    period = 14
    if len(deltas) >= period:
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
        rsi = round(rsi, 1)
    else:
        rsi = 50

    # 均线
    sma20 = np.mean(closes[-20:]) if len(closes) >= 20 else price
    sma50 = np.mean(closes[-50:]) if len(closes) >= 50 else None
    sma200 = np.mean(closes[-200:]) if len(closes) >= 200 else None

    # MACD
    def ema(data, period):
        result = [data[0]]
        alpha = 2 / (period + 1)
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[-1])
        return np.array(result)

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12[-1] - ema26[-1]
    signal_line = ema(list(ema12 - ema26), 9)[-1] if len(closes) > 26 else 0
    macd_hist = macd_line - signal_line

    # 布林带
    bb_period = 20
    if len(closes) >= bb_period:
        bb_mid = np.mean(closes[-bb_period:])
        bb_std = np.std(closes[-bb_period:])
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        bb_position = "上轨附近" if price > bb_upper * 0.98 else ("下轨附近" if price < bb_lower * 1.02 else "中轨附近")
    else:
        bb_upper = bb_lower = bb_mid = price
        bb_position = "N/A"

    # 支撑阻力
    recent_20 = closes[-20:]
    support = round(min(recent_20), 2)
    resistance = round(max(recent_20), 2)

    # 52周高低
    high_52w = round(max(closes[-252:]), 2) if len(closes) >= 252 else round(max(closes), 2)
    low_52w = round(min(closes[-252:]), 2) if len(closes) >= 252 else round(min(closes), 2)
    pct_from_high = round((price - high_52w) / high_52w * 100, 2)
    pct_from_low = round((price - low_52w) / low_52w * 100, 2)

    # 趋势判断
    if sma50 and price > sma50 and (sma200 is None or sma50 > sma200):
        trend = "强势上升"
    elif sma50 and price > sma50:
        trend = "上升"
    elif sma50 and price < sma50 and (sma200 is None or sma50 < sma200):
        trend = "强势下降"
    elif sma50 and price < sma50:
        trend = "下降"
    else:
        trend = "震荡"

    # 信号汇总
    signals = []
    if rsi > 70:
        signals.append("RSI超买")
    elif rsi < 30:
        signals.append("RSI超卖")
    if macd_line > 0 and macd_hist > 0:
        signals.append("MACD金叉")
    elif macd_line < 0 and macd_hist < 0:
        signals.append("MACD死叉")
    if sma200 and price > sma200:
        signals.append("站上200日均线")
    elif sma200 and price < sma200:
        signals.append("跌破200日均线")
    if price < bb_lower:
        signals.append("布林带下轨突破")
    elif price > bb_upper:
        signals.append("布林带上轨突破")

    return {
        "price": round(price, 2),
        "rsi": rsi,
        "rsi_signal": "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性"),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2) if sma50 else "N/A",
        "sma200": round(sma200, 2) if sma200 else "N/A",
        "macd": {"value": round(macd_line, 2), "signal": round(signal_line, 2), "histogram": round(macd_hist, 2), "bullish": macd_line > 0},
        "bollinger": {"upper": round(bb_upper, 2), "mid": round(bb_mid, 2), "lower": round(bb_lower, 2), "position": bb_position},
        "support": support,
        "resistance": resistance,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "pct_from_high": pct_from_high,
        "pct_from_low": pct_from_low,
        "trend": trend,
        "signals": signals,
    }


def analyze_mag7() -> list[dict]:
    """分析七姐妹 — 技术面 + 行情"""
    cache = get_cache()
    results = []

    for symbol, info in MAGNIFICENT_7.items():
        try:
            df = cache.get_stock(symbol)
            if df is None or df.empty:
                results.append({"symbol": symbol, "name": info["name"], "error": "数据不可用"})
                continue

            closes = [float(c) for c in df["close"].values]
            technials = _compute_stock_technicals(closes)

            # 日涨跌
            daily_change = 0
            if len(closes) >= 2:
                daily_change = round((closes[-1] - closes[-2]) / closes[-2] * 100, 2)

            # 周涨跌
            week_change = 0
            if len(closes) >= 5:
                week_change = round((closes[-1] - closes[-5]) / closes[-5] * 100, 2)

            # 月涨跌
            month_change = 0
            if len(closes) >= 22:
                month_change = round((closes[-1] - closes[-22]) / closes[-22] * 100, 2)

            # 成交量分析
            vol_info = {}
            if "volume" in df.columns and len(df) >= 20:
                vol_today = int(df["volume"].iloc[-1])
                vol_avg_20 = int(df["volume"].tail(20).mean())
                vol_ratio = round(vol_today / vol_avg_20, 2) if vol_avg_20 > 0 else 1
                vol_info = {"volume": vol_today, "avg_volume_20d": vol_avg_20, "vol_ratio": vol_ratio}

            results.append({
                "symbol": symbol,
                "name": info["name"],
                "sector": info["sector"],
                "weight_in_sp500": info["weight_in_sp500"],
                "daily_change": daily_change,
                "week_change": week_change,
                "month_change": month_change,
                "technicals": technials,
                "volume": vol_info,
            })
        except Exception as e:
            results.append({"symbol": symbol, "name": info["name"], "error": str(e)})

    return results


def analyze_soxx() -> dict:
    """分析 SOXX 半导体 ETF 及其权重股"""
    cache = get_cache()
    results = {"etf": {}, "holdings": [], "timestamp": datetime.now().isoformat()}

    # SOXX ETF 本身
    try:
        df = cache.get_stock("SOXX")
        if df is not None and not df.empty:
            closes = [float(c) for c in df["close"].values]
            tech = _compute_stock_technicals(closes)
            daily_change = round((closes[-1] - closes[-2]) / closes[-2] * 100, 2) if len(closes) >= 2 else 0
            week_change = round((closes[-1] - closes[-5]) / closes[-5] * 100, 2) if len(closes) >= 5 else 0
            results["etf"] = {
                "symbol": "SOXX",
                "name": "iShares Semiconductor ETF",
                "price": tech.get("price", 0),
                "daily_change": daily_change,
                "week_change": week_change,
                "technicals": tech,
            }
    except Exception as e:
        results["etf"] = {"error": str(e)}

    # SOXX 权重股
    for symbol, info in SOXX_HOLDINGS.items():
        try:
            df = cache.get_stock(symbol)
            if df is None or df.empty:
                results["holdings"].append({"symbol": symbol, "name": info["name"], "error": "数据不可用"})
                continue

            closes = [float(c) for c in df["close"].values]
            tech = _compute_stock_technicals(closes)
            daily_change = round((closes[-1] - closes[-2]) / closes[-2] * 100, 2) if len(closes) >= 2 else 0
            week_change = round((closes[-1] - closes[-5]) / closes[-5] * 100, 2) if len(closes) >= 5 else 0

            vol_info = {}
            if "volume" in df.columns and len(df) >= 20:
                vol_today = int(df["volume"].iloc[-1])
                vol_avg = int(df["volume"].tail(20).mean())
                vol_info = {"volume": vol_today, "avg_volume_20d": vol_avg, "vol_ratio": round(vol_today / vol_avg, 2) if vol_avg > 0 else 1}

            results["holdings"].append({
                "symbol": symbol,
                "name": info["name"],
                "soxx_weight": info["soxx_weight"],
                "subsector": info["subsector"],
                "price": tech.get("price", 0),
                "daily_change": daily_change,
                "week_change": week_change,
                "technicals": tech,
                "volume": vol_info,
            })
        except Exception as e:
            results["holdings"].append({"symbol": symbol, "name": info["name"], "error": str(e)})

    # 按 SOXX 权重排序
    results["holdings"].sort(key=lambda x: x.get("soxx_weight", 0), reverse=True)
    return results


def _format_single_stock(stock: dict) -> str:
    """格式化单只股票分析"""
    if stock.get("error"):
        return f"- **{stock['symbol']}** ({stock.get('name', '')}): 数据不可用 — {stock['error']}"

    lines = []
    tech = stock.get("technicals", {})
    daily = stock.get("daily_change", 0)
    week = stock.get("week_change", 0)
    sign_d = "+" if daily >= 0 else ""
    sign_w = "+" if week >= 0 else ""

    lines.append(f"- **{stock['symbol']}** ({stock.get('name', '')}): ${tech.get('price', 'N/A')} | 日{sign_d}{daily}% | 周{sign_w}{week}%")
    lines.append(f"  RSI: {tech.get('rsi', 'N/A')} ({tech.get('rsi_signal', '')}) | 趋势: {tech.get('trend', 'N/A')}")
    lines.append(f"  支撑: {tech.get('support', 'N/A')} | 阻力: {tech.get('resistance', 'N/A')}")

    macd = tech.get("macd", {})
    lines.append(f"  MACD: {'看涨' if macd.get('bullish') else '看跌'} ({macd.get('value', 'N/A')})")

    bb = tech.get("bollinger", {})
    if bb.get("position"):
        lines.append(f"  布林带: {bb.get('position', 'N/A')}")

    signals = tech.get("signals", [])
    if signals:
        lines.append(f"  信号: {', '.join(signals)}")

    vol = stock.get("volume", {})
    if vol.get("vol_ratio"):
        ratio = vol["vol_ratio"]
        vol_signal = "放量" if ratio > 1.5 else ("缩量" if ratio < 0.7 else "正常")
        lines.append(f"  量比: {ratio}x ({vol_signal})")

    pct_high = tech.get("pct_from_high", 0)
    pct_low = tech.get("pct_from_low", 0)
    lines.append(f"  距52周高点: {pct_high}% | 距52周低点: +{pct_low}%")

    return "\n".join(lines)


def format_mag7_for_prompt(mag7_data: list) -> str:
    """格式化七姐妹分析为 prompt 文本"""
    if not mag7_data:
        return "暂无七姐妹数据"

    lines = ["### 美股七姐妹 (Magnificent 7) 深度分析\n"]
    for stock in mag7_data:
        lines.append(_format_single_stock(stock))
        lines.append("")
    return "\n".join(lines)


def format_soxx_for_prompt(soxx_data: dict) -> str:
    """格式化 SOXX 分析为 prompt 文本"""
    if not soxx_data:
        return "暂无 SOXX 数据"

    lines = []

    # SOXX ETF
    etf = soxx_data.get("etf", {})
    if etf and not etf.get("error"):
        tech = etf.get("technicals", {})
        lines.append(f"### SOXX 半导体 ETF 概览")
        lines.append(f"- 价格: ${tech.get('price', 'N/A')} | 日涨跌: {etf.get('daily_change', 0):+.2f}% | 周涨跌: {etf.get('week_change', 0):+.2f}%")
        lines.append(f"- RSI: {tech.get('rsi', 'N/A')} | 趋势: {tech.get('trend', 'N/A')}")
        signals = tech.get("signals", [])
        if signals:
            lines.append(f"- 信号: {', '.join(signals)}")
        lines.append("")

    # 权重股
    lines.append("### SOXX 权重股详情\n")
    for stock in soxx_data.get("holdings", []):
        weight = stock.get("soxx_weight", 0)
        sub = stock.get("subsector", "")
        line = _format_single_stock(stock)
        lines.append(f"[权重 {weight}% | {sub}]")
        lines.append(line)
        lines.append("")

    return "\n".join(lines)


def get_mag7_news_keywords() -> list[str]:
    """获取七姐妹相关的新闻搜索关键词"""
    return [
        "Apple AAPL", "Microsoft MSFT", "NVIDIA NVDA",
        "Google Alphabet GOOGL", "Amazon AMZN", "Meta META",
        "Tesla TSLA", "Magnificent 7", "七姐妹",
        "SOXX semiconductor", "chip stocks", "半导体",
    ]

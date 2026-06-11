"""技术分析 — 基于缓存数据计算 v4.0"""
import numpy as np
from .data_cache import get_cache

INDICES = {"标普500": ".INX", "纳斯达克": ".IXIC", "道琼斯": ".DJI"}


def _compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50, "数据不足"
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain, avg_loss = np.mean(gains[-period:]), np.mean(losses[-period:])
    if avg_loss == 0:
        rsi = 100
    else:
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    rsi = round(rsi, 1)
    return rsi, "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")


def _sma(data, period):
    if len(data) < period:
        return None
    return np.mean(data[-period:])


def _ema(data, period):
    result, alpha = [data[0]], 2 / (period + 1)
    for i in range(1, len(data)):
        result.append(alpha * data[i] + (1 - alpha) * result[-1])
    return np.array(result)


def get_index_technicals() -> dict:
    cache = get_cache()
    result = {}
    for name, sym in INDICES.items():
        try:
            df = cache.get_index(sym)
            if df is None or df.empty or len(df) < 30:
                result[name] = {"error": "数据不足"}
                continue
            closes = [float(c) for c in df["close"].values]
            current_price = closes[-1]
            rsi, rsi_signal = _compute_rsi(closes)
            ema12, ema26 = _ema(closes, 12), _ema(closes, 26)
            macd_line = ema12[-1] - ema26[-1]
            sma50 = _sma(closes, 50)
            sma200 = _sma(closes, 200) if len(closes) >= 200 else None
            recent_20 = closes[-20:]
            support, resistance = round(min(recent_20), 2), round(max(recent_20), 2)
            trend = "上升趋势" if sma50 and current_price > sma50 else ("下降趋势" if sma50 else "N/A")
            signals = []
            if rsi > 70:
                signals.append("RSI超买")
            elif rsi < 30:
                signals.append("RSI超卖")
            signals.append("MACD看涨" if macd_line > 0 else "MACD看跌")
            result[name] = {
                "price": round(current_price, 2), "rsi": rsi, "rsi_signal": rsi_signal,
                "sma50": round(sma50, 2) if sma50 else "N/A",
                "sma200": round(sma200, 2) if sma200 else "N/A",
                "support": support, "resistance": resistance,
                "macd": {"value": round(macd_line, 2), "bullish": macd_line > 0, "signal": "看涨" if macd_line > 0 else "看跌"},
                "trend": trend, "signals": signals,
            }
        except Exception as e:
            result[name] = {"error": str(e)}
    return result

"""技术指标计算 — RSI, MACD, 均线, 布林带, 支撑阻力"""
import numpy as np
import yfinance as yf
from typing import Optional


def compute_rsi(prices: np.ndarray, period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - 100 / (1 + rs))


def compute_macd(prices: np.ndarray) -> dict:
    if len(prices) < 26:
        return {"macd": 0, "signal": 0, "histogram": 0, "bullish": False}
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    macd_line = ema12 - ema26
    macd_series = np.zeros_like(prices)
    for i in range(len(prices)):
        e12 = _ema(prices[:i+1], 12)[-1]
        e26 = _ema(prices[:i+1], 26)[-1]
        macd_series[i] = e12 - e26
    signal = float(_ema(macd_series, 9)[-1])
    histogram = float(macd_line[-1] - signal)
    return {
        "macd": round(float(macd_line[-1]), 4),
        "signal": round(signal, 4),
        "histogram": round(histogram, 4),
        "bullish": histogram > 0,
    }


def _ema(data: np.ndarray, period: int) -> np.ndarray:
    alpha = 2 / (period + 1)
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    return result


def compute_sma(prices: np.ndarray, period: int) -> float:
    if len(prices) < period:
        return float(prices[-1])
    return float(np.mean(prices[-period:]))


def compute_bollinger(prices: np.ndarray, period: int = 20) -> dict:
    sma = compute_sma(prices, period)
    if len(prices) < period:
        return {"upper": sma, "middle": sma, "lower": sma, "width_pct": 0, "position": 50}
    std = float(np.std(prices[-period:]))
    upper = sma + 2 * std
    lower = sma - 2 * std
    current = float(prices[-1])
    position = (current - lower) / (upper - lower) * 100 if (upper - lower) > 0 else 50
    return {
        "upper": round(upper, 2),
        "middle": round(sma, 2),
        "lower": round(lower, 2),
        "width_pct": round((upper - lower) / sma * 100, 1),
        "position": round(position, 1),
    }


def find_support_resistance(prices: np.ndarray, window: int = 20) -> dict:
    if len(prices) < window:
        current = float(prices[-1])
        return {"support": round(current * 0.97, 2), "resistance": round(current * 1.03, 2)}
    recent = prices[-window:]
    local_max = []
    local_min = []
    for i in range(2, len(recent) - 2):
        if recent[i] > recent[i-1] and recent[i] > recent[i-2] and recent[i] > recent[i+1] and recent[i] > recent[i+2]:
            local_max.append(recent[i])
        if recent[i] < recent[i-1] and recent[i] < recent[i-2] and recent[i] < recent[i+1] and recent[i] < recent[i+2]:
            local_min.append(recent[i])
    current = float(prices[-1])
    resistances = [r for r in local_max if r > current]
    supports = [s for s in local_min if s < current]
    return {
        "support": round(max(supports), 2) if supports else round(current * 0.97, 2),
        "resistance": round(min(resistances), 2) if resistances else round(current * 1.03, 2),
    }


def get_technical_summary(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="6mo")
        if hist.empty or len(hist) < 30:
            return {"error": f"{ticker}: 数据不足"}
        closes = hist["Close"].values
        current = float(closes[-1])
        rsi = compute_rsi(closes)
        macd = compute_macd(closes)
        sma50 = compute_sma(closes, 50)
        sma200 = compute_sma(closes, 200) if len(closes) >= 200 else current
        bb = compute_bollinger(closes)
        sr = find_support_resistance(closes)

        signals = []
        if rsi < 30:
            signals.append("RSI超卖")
        elif rsi > 70:
            signals.append("RSI超买")
        if macd["bullish"] and macd["histogram"] > 0:
            signals.append("MACD金叉看涨")
        elif not macd["bullish"]:
            signals.append("MACD死叉看跌")
        if current > sma50:
            signals.append("站上50日均线")
        else:
            signals.append("跌破50日均线")
        if current > sma200:
            signals.append("站上200日均线(牛市)")
        else:
            signals.append("跌破200日均线(熊市)")

        return {
            "symbol": ticker,
            "price": current,
            "rsi": round(rsi, 1),
            "rsi_signal": "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性"),
            "macd": macd,
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "bollinger": bb,
            "support": sr["support"],
            "resistance": sr["resistance"],
            "signals": signals,
            "trend": "bullish" if current > sma50 and current > sma200 else ("bearish" if current < sma50 and current < sma200 else "mixed"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_index_technicals() -> dict:
    return {
        "标普500": get_technical_summary("^GSPC"),
        "纳斯达克": get_technical_summary("^IXIC"),
        "道琼斯": get_technical_summary("^DJI"),
    }
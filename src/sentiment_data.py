"""市场情绪数据 — Put/Call比, VIX结构, 做空数据"""
import yfinance as yf
import numpy as np
from datetime import datetime


def get_vix_structure() -> dict:
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1mo")
        if hist.empty:
            return {"current": None, "trend": "unknown", "contango": "unknown", "risk_level": "unknown"}

        current = float(hist["Close"].iloc[-1])
        sma10 = float(np.mean(hist["Close"].iloc[-10:])) if len(hist) >= 10 else current

        try:
            vix_futures = yf.Ticker("VX=F")
            vix_fut_info = vix_futures.info
            fut_price = vix_fut_info.get("regularMarketPrice", current)
        except Exception:
            fut_price = current

        contango = "contango(正常)" if fut_price > current else "backwardation(风险预警)"
        trend = "上升(恐慌加剧)" if current > sma10 else "下降(恐慌缓解)"

        if current < 15:
            risk_level = "低"
        elif current < 25:
            risk_level = "中"
        elif current < 35:
            risk_level = "高"
        else:
            risk_level = "极高"

        return {
            "current": round(current, 2),
            "trend": trend,
            "contango": contango,
            "futures_price": round(fut_price, 2) if fut_price != current else None,
            "risk_level": risk_level,
        }
    except Exception as e:
        return {"error": str(e)}


def get_sp500_breadth() -> dict:
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="3mo")
        if hist.empty:
            return {"breadth": None}
        closes = hist["Close"].values
        sma50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else float(closes[-1])
        current = float(closes[-1])
        pct_from_50ma = (current - sma50) / sma50 * 100
        return {
            "spy_vs_50ma_pct": round(pct_from_50ma, 2),
            "signal": "bullish" if pct_from_50ma > 0 else "bearish",
        }
    except Exception as e:
        return {"error": str(e)}


def get_market_sentiment() -> dict:
    vix = get_vix_structure()
    breadth = get_sp500_breadth()

    risk_score = 0
    if vix.get("current"):
        if vix["current"] < 15:
            risk_score += 1
        elif vix["current"] < 20:
            risk_score += 2
        elif vix["current"] < 30:
            risk_score += 3
        else:
            risk_score += 4

    if breadth.get("spy_vs_50ma_pct") is not None:
        if breadth["spy_vs_50ma_pct"] > 3:
            risk_score += 1
        elif breadth["spy_vs_50ma_pct"] > 0:
            risk_score += 2
        elif breadth["spy_vs_50ma_pct"] > -3:
            risk_score += 3
        else:
            risk_score += 4

    if risk_score <= 3:
        sentiment = "Risk-On（积极）"
    elif risk_score <= 5:
        sentiment = "中性偏积极"
    elif risk_score <= 7:
        sentiment = "中性偏谨慎"
    else:
        sentiment = "Risk-Off（防御）"

    return {
        "vix": vix,
        "breadth": breadth,
        "risk_score": risk_score,
        "sentiment": sentiment,
        "timestamp": datetime.now().isoformat(),
    }


def get_fedwatch_probability() -> dict:
    try:
        t_note = yf.Ticker("^IRX")
        hist_2y = t_note.history(period="1mo")
        current_2y = float(hist_2y["Close"].iloc[-1]) if not hist_2y.empty else None

        ff = yf.Ticker("ZQ=F")
        ff_info = ff.info
        ff_price = ff_info.get("regularMarketPrice", None)

        return {
            "current_2y_yield": round(current_2y, 2) if current_2y else None,
            "ff_futures_price": ff_price,
            "hike_probability": "低（市场定价维稳或降息）" if current_2y and current_2y < 4.5 else "需关注",
        }
    except Exception as e:
        return {"error": str(e)}
"""市场情绪 — 缓存数据计算 v4.0"""
import numpy as np
from .data_cache import get_cache


def get_market_sentiment() -> dict:
    cache = get_cache()
    result = {"sentiment": "中性", "risk_score": 4, "vix": {}, "breadth": {}}
    try:
        df = cache.get_index(".INX")
        if df is None or df.empty or len(df) < 20:
            return result
        closes = [float(c) for c in df["close"].values]
        current = closes[-1]
        returns = [((closes[i] - closes[i - 1]) / closes[i - 1]) * 100 for i in range(1, len(closes))]
        vol_20d = round(np.std(returns[-20:]) * np.sqrt(252), 1)
        vol_5d = round(np.std(returns[-5:]) * np.sqrt(252), 1) if len(returns) >= 5 else vol_20d
        if vol_20d < 15:
            risk_level = "低波动"
        elif vol_20d < 25:
            risk_level = "中等波动"
        elif vol_20d < 35:
            risk_level = "高波动"
        else:
            risk_level = "极高波动"
        contango = "正向（波动上升）" if vol_5d > vol_20d * 1.2 else ("反向（波动下降）" if vol_5d < vol_20d * 0.8 else "持平")
        result["vix"] = {"current": vol_20d, "contango": contango, "trend": "上升" if vol_5d > vol_20d else "下降", "risk_level": risk_level}
        if len(closes) >= 50:
            sma50 = np.mean(closes[-50:])
            pct = round(((current - sma50) / sma50) * 100, 2)
            if pct > 5:
                signal = "牛市区间"
            elif pct > 0:
                signal = "温和看涨"
            elif pct > -5:
                signal = "温和看跌"
            else:
                signal = "熊市区间"
            result["breadth"] = {"spy_vs_50ma_pct": pct, "signal": signal}
        # Overall rating
        risk_score = 4
        if vol_20d < 15:
            risk_score -= 2
        elif vol_20d < 20:
            risk_score -= 1
        elif vol_20d > 30:
            risk_score += 2
        elif vol_20d > 25:
            risk_score += 1
        if result.get("breadth"):
            b = result["breadth"]["spy_vs_50ma_pct"]
            if b > 5:
                risk_score -= 1
            elif b < -5:
                risk_score += 1
        result["risk_score"] = max(1, min(8, risk_score))
        result["sentiment"] = "乐观" if risk_score <= 3 else ("中性" if risk_score <= 5 else "谨慎")
    except Exception:
        pass
    return result
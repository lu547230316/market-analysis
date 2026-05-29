"""宏观数据 — VIX、美债收益率、美元指数"""
import yfinance as yf
from datetime import datetime


MACRO_TICKERS = {
    "VIX恐慌指数": "^VIX",
    "10年期美债收益率": "^TNX",
    "2年期美债收益率": "^IRX",
    "30年期美债收益率": "^TYX",
    "美元指数": "DX-Y.NYB",
}


def get_macro_data() -> dict:
    result = {"indicators": [], "timestamp": datetime.now().isoformat()}

    for name, sym in MACRO_TICKERS.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="5d")
            if hist.empty:
                continue
            current = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-5]) if len(hist) >= 5 else float(hist["Close"].iloc[0])
            change = current - prev
            result["indicators"].append({
                "name": name,
                "symbol": sym,
                "value": round(current, 2),
                "change": round(change, 2),
                "change_pct": round((change / prev) * 100, 2) if prev else 0,
            })
        except Exception:
            pass

    for ind in result["indicators"]:
        if ind["symbol"] == "^VIX":
            vix = ind["value"]
            if vix < 15:
                ind["interpretation"] = "极度平静，市场自满"
            elif vix < 20:
                ind["interpretation"] = "正常波动区间"
            elif vix < 30:
                ind["interpretation"] = "恐慌上升，避险情绪升温"
            else:
                ind["interpretation"] = "极度恐慌，市场剧烈动荡"

    return result


def get_interest_rates_summary() -> str:
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="1mo")
        if hist.empty:
            return "利率数据暂不可用"
        current = float(hist["Close"].iloc[-1])
        month_ago = float(hist["Close"].iloc[0])
        direction = "上行" if current > month_ago else "下行"
        return f"10年期美债收益率 {current:.2f}%，近一月{direction}{abs(current - month_ago):.0f}bp"
    except Exception:
        return "利率数据暂不可用"
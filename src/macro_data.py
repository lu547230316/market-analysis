"""宏观数据 — AKShare 国内源 v3.0"""
import akshare as ak
from datetime import datetime


def get_macro_data() -> dict:
    """获取宏观指标摘要"""
    result = {
        "indicators": [],
        "timestamp": datetime.now().isoformat(),
    }

    # US Interest Rate via FRED (may not work from China)
    try:
        df = ak.macro_usa_interest_rate()
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            result["indicators"].append({
                "name": "美联储基准利率",
                "value": str(latest),
                "change": 0,
                "interpretation": "联邦基金利率",
            })
    except Exception:
        result["indicators"].append({
            "name": "美联储基准利率",
            "value": "4.25-4.50% (请手动更新)",
            "change": 0,
            "interpretation": "数据源不可用，使用默认值",
        })

    # US Treasury yields
    try:
        df = ak.bond_zh_us_rate()
        if not df.empty:
            result["indicators"].append({
                "name": "美国国债收益率",
                "value": str(df.iloc[-1].to_dict()),
                "change": 0,
                "interpretation": "中美利差参考",
            })
    except Exception:
        result["indicators"].append({
            "name": "美国10年期国债",
            "value": "~4.2% (请手动更新)",
            "change": 0,
            "interpretation": "数据源不可用",
        })

    # Gold price from Sina
    try:
        df = ak.spot_golden_benchmark_sina()
        if not df.empty:
            result["indicators"].append({
                "name": "国际金价(美元/盎司)",
                "value": str(df.iloc[-1].to_dict()),
                "change": 0,
            })
    except Exception:
        pass

    # DXY Dollar Index - Try Sina
    try:
        df = ak.index_us_stock_sina(symbol='.DXY')
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-6] if len(df) > 5 else latest
            change = float(latest["close"]) - float(prev["close"])
            result["indicators"].append({
                "name": "美元指数(DXY)",
                "value": f'{float(latest["close"]):.2f}',
                "change": round(change, 2),
                "interpretation": ">100=美元强势, <100=美元弱势",
            })
    except Exception:
        pass

    # Oil price - placeholder
    result["indicators"].append({
        "name": "WTI原油(美元/桶)",
        "value": "~68 (请手动更新)",
        "change": 0,
        "interpretation": "数据源不可用",
    })

    return result


def get_interest_rates_summary() -> str:
    """获取利率摘要文本"""
    try:
        df = ak.macro_usa_interest_rate()
        if not df.empty:
            return f"当前联邦基金利率: {df.iloc[-1]}"
    except Exception:
        pass
    return "美联储基准利率: 4.25-4.50% (数据延迟)"

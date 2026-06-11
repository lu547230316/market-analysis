"""美股 KOL 观点采集 v5.0 — 著名市场评论员观点聚合"""
import re
import hashlib
from datetime import datetime, timedelta

from .data_cache import get_cache


# 知名美股 KOL 列表及其特征关键词
KOL_PROFILES = {
    "Jim Cramer (Mad Money)": {
        "keywords": ["cramer", "mad money", "jim cramer"],
        "stance_keywords_bull": ["buy", "love", "own", "back up the truck", "charitable trust"],
        "stance_keywords_bear": ["sell", "too expensive", "take profits", "ring the register"],
        "weight": 0.8,
        "description": "CNBC Mad Money 主持人，华尔街最有影响力的散户风向标",
    },
    "Cathie Wood (ARK Invest)": {
        "keywords": ["cathie wood", "ark invest", "arkk", "cathie"],
        "stance_keywords_bull": ["disruptive", "innovation", "conviction", "add", "buy the dip"],
        "stance_keywords_bear": ["trim", "rotation", "valuation concern"],
        "weight": 0.9,
        "description": "ARK Invest CEO，颠覆性创新投资旗手",
    },
    "Ray Dalio (Bridgewater)": {
        "keywords": ["ray dalio", "bridgewater", "dalio"],
        "stance_keywords_bull": ["paradigm shift", "buy", "gold", "tangible assets"],
        "stance_keywords_bear": ["debt cycle", "cash is trash", "bubble", "cautious"],
        "weight": 0.95,
        "description": "桥水基金创始人，全球最大对冲基金",
    },
    "Warren Buffett (Berkshire)": {
        "keywords": ["buffett", "berkshire hathaway", "warren buffett", "berkshire"],
        "stance_keywords_bull": ["buy", "hold", "long term", "moat", "value"],
        "stance_keywords_bear": ["sell", "overvalued", "too much speculation", "cash pile"],
        "weight": 1.0,
        "description": "伯克希尔哈撒韦 CEO，价值投资之神",
    },
    "Jamie Dimon (JPMorgan)": {
        "keywords": ["jamie dimon", "jpmorgan", "dimon"],
        "stance_keywords_bull": ["strong economy", "resilient", "growth"],
        "stance_keywords_bear": ["storm clouds", "recession risk", "geopolitical risk", "cautious"],
        "weight": 0.9,
        "description": "摩根大通 CEO，华尔街最具影响力的银行家",
    },
    "Elon Musk (Tesla/SpaceX)": {
        "keywords": ["elon musk", "musk", "tesla ceo"],
        "stance_keywords_bull": ["buy", "undervalued", "long term"],
        "stance_keywords_bear": ["overvalued", "bubble"],
        "weight": 0.7,
        "description": "特斯拉/SpaceX CEO，科技界最具影响力人物",
    },
    "Michael Burry (Scion Asset)": {
        "keywords": ["michael burry", "burry", "scion asset", "big short"],
        "stance_keywords_bull": ["buy", "value", "contrarian"],
        "stance_keywords_bear": ["bubble", "sell", "short", "crash", "puts"],
        "weight": 0.85,
        "description": "《大空头》原型，逆向投资大师",
    },
    "Stanley Druckenmiller": {
        "keywords": ["druckenmiller", "stanley druckenmiller", "duquesne"],
        "stance_keywords_bull": ["buy", "growth", "innovation"],
        "stance_keywords_bear": ["risk", "cautious", "hedging"],
        "weight": 0.9,
        "description": "Duquesne Capital 创始人，传奇宏观交易员",
    },
}


def _detect_kol_mentions(text: str) -> list[dict]:
    """从新闻文本中检测 KOL 提及"""
    text_lower = text.lower()
    mentions = []
    for kol_name, profile in KOL_PROFILES.items():
        for keyword in profile["keywords"]:
            if keyword.lower() in text_lower:
                # 判断立场
                bull_score = sum(1 for kw in profile["stance_keywords_bull"] if kw in text_lower)
                bear_score = sum(1 for kw in profile["stance_keywords_bear"] if kw in text_lower)
                if bull_score > bear_score:
                    stance = "看多"
                elif bear_score > bull_score:
                    stance = "看空"
                else:
                    stance = "中性"
                mentions.append({
                    "kol": kol_name,
                    "description": profile["description"],
                    "stance": stance,
                    "weight": profile["weight"],
                    "bull_score": bull_score,
                    "bear_score": bear_score,
                })
                break
    return mentions


def _extract_kol_opinions_from_news(articles: list[dict]) -> list[dict]:
    """从新闻列表中提取 KOL 观点"""
    kol_articles = []
    seen_kols = set()

    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        full_text = f"{title} {summary}"

        mentions = _detect_kol_mentions(full_text)
        for mention in mentions:
            if mention["kol"] not in seen_kols:
                seen_kols.add(mention["kol"])
                kol_articles.append({
                    "kol": mention["kol"],
                    "description": mention["description"],
                    "stance": mention["stance"],
                    "weight": mention["weight"],
                    "headline": title[:200],
                    "source": article.get("source", "未知"),
                    "published": article.get("published", ""),
                })
    return kol_articles


def get_kol_opinions(articles: list[dict] = None) -> dict:
    """获取 KOL 观点汇总 — 主入口"""
    if articles is None:
        cache = get_cache()
        raw = cache.get_all_news()
        articles = []
        if raw is not None:
            import pandas as pd
            for _, row in raw.iterrows():
                title = str(row.iloc[1]) if len(row) > 1 else str(row.iloc[0])
                summary = str(row.iloc[2]) if len(row) > 2 else ""
                articles.append({"title": title, "summary": summary, "source": "东方财富"})

    opinions = _extract_kol_opinions_from_news(articles)

    # 汇总统计
    bull_count = sum(1 for o in opinions if o["stance"] == "看多")
    bear_count = sum(1 for o in opinions if o["stance"] == "看空")
    neutral_count = sum(1 for o in opinions if o["stance"] == "中性")

    # 加权立场
    weighted_bull = sum(o["weight"] for o in opinions if o["stance"] == "看多")
    weighted_bear = sum(o["weight"] for o in opinions if o["stance"] == "看空")

    if weighted_bull > weighted_bear * 1.3:
        overall = "KOL 整体偏多"
    elif weighted_bear > weighted_bull * 1.3:
        overall = "KOL 整体偏空"
    else:
        overall = "KOL 观点分歧"

    return {
        "opinions": opinions,
        "summary": {
            "total_mentions": len(opinions),
            "bullish": bull_count,
            "bearish": bear_count,
            "neutral": neutral_count,
            "weighted_bull": round(weighted_bull, 2),
            "weighted_bear": round(weighted_bear, 2),
            "overall_stance": overall,
        },
        "timestamp": datetime.now().isoformat(),
    }


def format_kol_for_prompt(kol_data: dict) -> str:
    """格式化 KOL 观点为 prompt 文本"""
    if not kol_data or not kol_data.get("opinions"):
        return "暂无 KOL 观点数据"

    lines = []
    summary = kol_data["summary"]
    lines.append(f"### KOL 观点汇总")
    lines.append(f"- 总提及: {summary['total_mentions']} | 看多: {summary['bullish']} | 看空: {summary['bearish']} | 中性: {summary['neutral']}")
    lines.append(f"- 加权立场: 多头 {summary['weighted_bull']} vs 空头 {summary['weighted_bear']}")
    lines.append(f"- **整体判断: {summary['overall_stance']}**\n")

    for op in kol_data["opinions"]:
        stance_emoji = "+" if op["stance"] == "看多" else ("-" if op["stance"] == "看空" else "=")
        lines.append(f"- **{op['kol']}** [{stance_emoji}{op['stance']}] — {op['headline'][:100]}")

    return "\n".join(lines)

"""利多/利空新闻分析 v5.0 — 过去24h新闻情绪分类"""
import re
from datetime import datetime, timedelta
from collections import defaultdict


# 利多关键词及权重
BULLISH_KEYWORDS = {
    # 宏观利多
    "rate cut": 3, "降息": 3, "dovish": 2, "鸽派": 2, "stimulus": 2, "刺激": 2,
    "easing": 2, "宽松": 2, "liquidity": 1, "流动性": 1,
    # 经济数据利多
    "beat expectations": 2, "超预期": 2, "strong gdp": 2, "gdp beat": 2,
    "job growth": 1, "就业增长": 1, "consumer confidence": 1, "消费者信心": 1,
    "retail sales beat": 2, "零售超预期": 2,
    # 市场利多
    "rally": 2, "反弹": 2, "surge": 2, "暴涨": 2, "bullish": 2, "看涨": 2,
    "breakout": 2, "突破": 2, "new high": 3, "新高": 3, "record high": 3,
    "all-time high": 3, "buyback": 1, "回购": 1, "dividend increase": 1,
    # 个股利多
    "earnings beat": 3, "盈利超预期": 3, "revenue beat": 2, "营收超预期": 2,
    "upgrade": 2, "上调评级": 2, "price target raised": 2, "上调目标价": 2,
    "guidance raised": 3, "上调指引": 3, "outperform": 1,
    # 行业利多
    "ai breakthrough": 2, "ai 突破": 2, "semiconductor demand": 2, "芯片需求": 2,
    "cloud growth": 1, "云计算增长": 1, "ev demand": 1, "电动车需求": 1,
    # 地缘利多
    "trade deal": 2, "贸易协议": 2, "ceasefire": 2, "停火": 2,
    "de-escalation": 2, "缓和": 2, "peace": 1,
}

# 利空关键词及权重
BEARISH_KEYWORDS = {
    # 宏观利空
    "rate hike": 3, "加息": 3, "hawkish": 2, "鹰派": 2, "tightening": 2, "紧缩": 2,
    "inflation surge": 3, "通胀飙升": 3, "cpi hot": 3, "cpi 超预期": 3,
    # 经济数据利空
    "miss expectations": 2, "不及预期": 2, "recession": 3, "衰退": 3,
    "unemployment rise": 2, "失业率上升": 2, "slowdown": 2, "放缓": 2,
    "consumer weakness": 1, "消费者疲软": 1,
    # 市场利空
    "crash": 3, "暴跌": 3, "plunge": 3, "崩盘": 3, "bearish": 2, "看跌": 2,
    "sell-off": 2, "抛售": 2, "correction": 1, "回调": 1, "panic": 3, "恐慌": 3,
    "breakdown": 2, "跌破": 2, "new low": 2, "新低": 2,
    # 个股利空
    "earnings miss": 3, "盈利不及预期": 3, "revenue miss": 2, "营收不及预期": 2,
    "downgrade": 2, "下调评级": 2, "price target cut": 2, "下调目标价": 2,
    "guidance lowered": 3, "下调指引": 3, "lawsuit": 1, "诉讼": 1,
    "sec investigation": 2, "sec 调查": 2, "fraud": 3, "欺诈": 3,
    # 行业利空
    "chip ban": 3, "芯片禁令": 3, "tariff": 2, "关税": 2, "sanction": 2, "制裁": 2,
    "supply chain": 1, "供应链": 1, "oversupply": 2, "供应过剩": 2,
    # 地缘利空
    "war": 3, "战争": 3, "conflict": 2, "冲突": 2, "escalation": 2, "升级": 2,
    "geopolitical risk": 2, "地缘风险": 2,
}


def _analyze_single_article(article: dict) -> dict:
    """分析单篇新闻的利多/利空倾向"""
    title = article.get("title", "")
    summary = article.get("summary", "")
    full_text = f"{title} {summary}".lower()

    bull_score = 0
    bear_score = 0
    bull_hits = []
    bear_hits = []

    for keyword, weight in BULLISH_KEYWORDS.items():
        if keyword.lower() in full_text:
            bull_score += weight
            bull_hits.append(keyword)

    for keyword, weight in BEARISH_KEYWORDS.items():
        if keyword.lower() in full_text:
            bear_score += weight
            bear_hits.append(keyword)

    # 净情绪得分
    net_score = bull_score - bear_score
    if net_score >= 3:
        sentiment = "利多"
    elif net_score <= -3:
        sentiment = "利空"
    elif abs(net_score) >= 1:
        sentiment = "偏多" if net_score > 0 else "偏空"
    else:
        sentiment = "中性"

    return {
        "title": title[:200],
        "summary": summary[:300],
        "source": article.get("source", "未知"),
        "published": article.get("published", ""),
        "sentiment": sentiment,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "net_score": net_score,
        "bull_keywords": bull_hits[:5],
        "bear_keywords": bear_hits[:5],
        "confidence": min(10, max(1, abs(net_score))),
    }


def analyze_news_sentiment(articles: list[dict]) -> dict:
    """分析所有新闻的利多/利空分布 — 主入口"""
    analyzed = [_analyze_single_article(a) for a in articles]

    # 分类
    bullish = [a for a in analyzed if a["sentiment"] in ("利多", "偏多")]
    bearish = [a for a in analyzed if a["sentiment"] in ("利空", "偏空")]
    neutral = [a for a in analyzed if a["sentiment"] == "中性"]

    # 按置信度排序
    bullish.sort(key=lambda x: x["net_score"], reverse=True)
    bearish.sort(key=lambda x: x["net_score"])

    # 总体情绪
    total_bull = sum(a["bull_score"] for a in analyzed)
    total_bear = sum(a["bear_score"] for a in analyzed)

    if total_bull > total_bear * 1.5:
        overall = "整体利多"
    elif total_bear > total_bull * 1.5:
        overall = "整体利空"
    elif total_bull > total_bear:
        overall = "偏利多"
    elif total_bear > total_bull:
        overall = "偏利空"
    else:
        overall = "多空平衡"

    return {
        "overall_sentiment": overall,
        "total_bull_score": total_bull,
        "total_bear_score": total_bear,
        "bullish_news": bullish[:15],
        "bearish_news": bearish[:15],
        "neutral_count": len(neutral),
        "total_analyzed": len(analyzed),
        "timestamp": datetime.now().isoformat(),
    }


def format_news_sentiment_for_prompt(sentiment_data: dict) -> str:
    """格式化新闻情绪为 prompt 文本"""
    if not sentiment_data:
        return "暂无新闻情绪数据"

    lines = []
    lines.append(f"### 新闻情绪分析 (共 {sentiment_data['total_analyzed']} 篇)")
    lines.append(f"- **总体判断: {sentiment_data['overall_sentiment']}**")
    lines.append(f"- 利多总分: {sentiment_data['total_bull_score']} | 利空总分: {sentiment_data['total_bear_score']}")
    lines.append(f"- 利多新闻: {len(sentiment_data['bullish_news'])} 篇 | 利空新闻: {len(sentiment_data['bearish_news'])} 篇 | 中性: {sentiment_data['neutral_count']} 篇\n")

    if sentiment_data["bullish_news"]:
        lines.append("**TOP 利多新闻:**")
        for n in sentiment_data["bullish_news"][:8]:
            kw = ", ".join(n["bull_keywords"][:3]) if n["bull_keywords"] else ""
            lines.append(f"  - [{n['sentiment']}] {n['title'][:100]} (关键词: {kw})")

    if sentiment_data["bearish_news"]:
        lines.append("\n**TOP 利空新闻:**")
        for n in sentiment_data["bearish_news"][:8]:
            kw = ", ".join(n["bear_keywords"][:3]) if n["bear_keywords"] else ""
            lines.append(f"  - [{n['sentiment']}] {n['title'][:100]} (关键词: {kw})")

    return "\n".join(lines)

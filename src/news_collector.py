"""新闻采集 — AKShare 东方财富全球财经新闻 v3.0"""
import akshare as ak
import hashlib
import re
import html as html_mod
from datetime import datetime, timedelta


def _clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", str(text))
    clean = html_mod.unescape(clean)
    return clean.strip()


def _score_news(title: str) -> int:
    """新闻相关性打分"""
    if not title:
        return 0
    keywords = [
        "fed", "fomc", "inflation", "cpi", "gdp", "earnings", "revenue",
        "stock", "market", "rally", "sell-off", "crash", "surge", "plunge",
        "rate", "yield", "treasury", "bond", "dollar", "oil", "gold",
        "nvidia", "apple", "microsoft", "tesla", "amazon", "meta", "google",
        "ai", "chip", "semiconductor", "tech", "bank", "energy",
        "jobs", "unemployment", "payroll", "housing", "consumer",
        "china", "trade", "tariff", "geopolitical", "war", "sanction",
        "美股", "标普", "纳斯达克", "道琼斯", "美联储", "加息", "降息",
        "科技", "芯片", "半导体", "能源", "银行", "医药",
        "苹果", "微软", "英伟达", "特斯拉", "谷歌",
    ]
    t = str(title).lower()
    return sum(1 for kw in keywords if kw in t)


def fetch_em_global_news() -> list[dict]:
    """从东方财富获取全球财经新闻"""
    try:
        df = ak.stock_info_global_em()
        if df.empty:
            return []
        articles = []
        for _, row in df.iterrows():
            title = str(row.iloc[1]) if len(row) > 1 else str(row.iloc[0])
            if not title or title == "nan":
                continue
            summary = str(row.iloc[2]) if len(row) > 2 else ""
            url = str(row.iloc[3]) if len(row) > 3 else ""
            articles.append({
                "title": _clean_html(title),
                "summary": _clean_html(summary)[:300],
                "source": "东方财富",
                "url": url if url != "nan" else "",
                "published": datetime.now().isoformat(),
                "score": _score_news(title),
            })
        return articles
    except Exception:
        return []


def fetch_yfinance_news(tickers: list[str] = None, max_per_ticker: int = 3) -> list[dict]:
    """yfinance 新闻 (不可用时的替代) — 返回空列表"""
    return []


def fetch_all_news(days: int = 1, max_articles: int = 60) -> list[dict]:
    """获取所有新闻 (主入口)"""
    all_articles = []

    # Primary source: East Money global news
    em_news = fetch_em_global_news()
    all_articles.extend(em_news)

    # Dedup by title
    seen = set()
    deduped = []
    for a in all_articles:
        key = hashlib.md5(a["title"][:80].encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            deduped.append(a)

    # Sort by score
    deduped.sort(key=lambda x: x.get("score", 0), reverse=True)

    top = [a for a in deduped if a["score"] > 0][:max_articles]
    filler = [a for a in deduped if a["score"] == 0][:15]
    result = top + filler
    return result[:max_articles]
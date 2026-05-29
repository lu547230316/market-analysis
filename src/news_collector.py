"""新闻采集 — NewsAPI + RSS 英文财经源"""
import re
import html as html_mod
import hashlib
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Optional

from .config import NEWSAPI_KEY

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "https://feeds.marketwatch.com/marketwatch/topstories",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.investing.com/rss/news.rss",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _clean_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text)
    clean = html_mod.unescape(clean)
    return clean.strip()


def _score_news(title: str) -> int:
    keywords = [
        "fed", "fomc", "inflation", "cpi", "gdp", "earnings", "revenue",
        "stock", "market", "rally", "sell-off", "crash", "surge", "plunge",
        "rate", "yield", "treasury", "bond", "dollar", "oil", "gold",
        "nvidia", "apple", "microsoft", "tesla", "amazon", "meta", "google",
        "ai", "chip", "semiconductor", "tech", "bank", "energy",
        "jobs", "unemployment", "payroll", "housing", "consumer",
        "china", "trade", "tariff", "geopolitical", "war", "sanction",
    ]
    t = title.lower()
    return sum(1 for kw in keywords if kw in t)


def fetch_newsapi(query: str = "stock market OR wall street", days: int = 1) -> list[dict]:
    if not NEWSAPI_KEY:
        return []
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": NEWSAPI_KEY,
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "summary": _clean_html(a.get("description", "")),
                "source": a.get("source", {}).get("name", ""),
                "url": a.get("url", ""),
                "published": a.get("publishedAt", ""),
                "score": _score_news(a.get("title", "")),
            }
            for a in articles
            if a.get("title")
        ]
    except Exception:
        return []


def fetch_rss(feed_url: str, max_items: int = 15) -> list[dict]:
    try:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "")
            summary = _clean_html(entry.get("summary", entry.get("description", "")))
            items.append({
                "title": title,
                "summary": summary[:300] if summary else "",
                "source": feed.feed.get("title", feed_url),
                "url": entry.get("link", ""),
                "published": entry.get("published", entry.get("updated", "")),
                "score": _score_news(title),
            })
        return items
    except Exception:
        return []


def fetch_all_news(days: int = 1, max_articles: int = 60) -> list[dict]:
    all_articles = []

    api_articles = fetch_newsapi(days=days)
    all_articles.extend(api_articles)

    for feed_url in RSS_FEEDS:
        rss_articles = fetch_rss(feed_url)
        all_articles.extend(rss_articles)

    seen = set()
    deduped = []
    for a in all_articles:
        key = hashlib.md5(a["title"][:80].encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            deduped.append(a)

    deduped.sort(key=lambda x: x.get("score", 0), reverse=True)

    top = [a for a in deduped if a["score"] > 0][:max_articles]
    filler = [a for a in deduped if a["score"] == 0][:10]
    result = top + filler
    return result[:max_articles]


def fetch_yfinance_news(tickers: list[str] = None, max_per_ticker: int = 3) -> list[dict]:
    if tickers is None:
        tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA"]
    articles = []
    for sym in tickers:
        try:
            import yfinance as yf
            t = yf.Ticker(sym)
            news = t.news[:max_per_ticker]
            for n in news:
                title = n.get("title", "")
                articles.append({
                    "title": title,
                    "summary": n.get("content", {}).get("summary", "")[:300],
                    "source": n.get("content", {}).get("source", ""),
                    "url": n.get("content", {}).get("canonicalUrl", {}).get("url", ""),
                    "published": n.get("content", {}).get("pubDate", ""),
                    "score": _score_news(title),
                })
        except Exception:
            pass
    return articles
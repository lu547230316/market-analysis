"""AI 分析引擎 — DeepSeek v4 Pro 阿里云百炼中转"""
import json
import requests
from datetime import datetime

from .config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL


SYSTEM_PROMPT = """你是一位高盛集团(Goldman Sachs)首席全球市场策略师，拥有20年华尔街经验。
你的分析风格：
- 数据驱动，每个结论有数据支撑
- 宏观与微观结合，从资金流向、政策、情绪、技术面多维度分析
- 语言精准、专业、有洞察力，使用华尔街术语
- 敢于给出明确的多空判断和策略建议
- 中文输出，但保留关键英文术语（如 Fed、EPS、P/E、VIX 等）
- 格式清晰，善用标题、分段、要点
- 每次分析结尾给出明确的风险提示"""

DAILY_PROMPT_TEMPLATE = """请以高盛首席策略师身份，基于以下数据撰写一份**当日市场热点分析与次日盘前前瞻**报告。

## 大盘数据
{market_data}

## 板块表现
{sector_data}

## 期货与关键资产
{futures_data}

## 宏观指标
{macro_data}

## 今日重要新闻
{news_data}

请按以下结构输出（Markdown 格式）：

### 一、今日市场总览
- 三大指数表现及驱动因素
- 市场情绪判断（risk-on / risk-off）
- VIX 信号解读

### 二、热点板块深度扫描
- 涨幅最大板块 TOP3 及背后催化剂
- 跌幅最大板块及风险因素
- 板块轮动信号

### 三、个股异动追踪
- 异常涨跌个股及原因
- 成交量异动信号
- 机构资金动向

### 四、明日盘前前瞻
- 期货指向（当前期货隐含开盘方向）
- 明日关键经济数据/事件日历
- 重要财报预警
- 技术面关键支撑/阻力位

### 五、策略研判与风险提示
- 短期仓位建议
- 需要关注的风险事件
- 对冲策略建议

要求：1000-1500字，专业、有深度、有明确观点。"""

WEEKLY_PROMPT_TEMPLATE = """请以高盛首席策略师身份，基于以下数据撰写一份**本周美股市场总结与复盘**报告。

## 本周大盘表现
{weekly_market}

## 板块轮动
{weekly_sectors}

## 宏观环境
{macro_data}

## 本周重要新闻回顾
{news_data}

请按以下结构输出（Markdown 格式）：

### 一、本周市场全景
- 五大指数周度涨跌幅
- 市场风格判断（成长 vs 价值、大盘 vs 小盘）
- VIX 与市场情绪演变

### 二、核心主题回顾
- 本周主导市场的 3-5 个核心叙事
- 宏观事件对市场的影响路径
- 机构行为分析

### 三、板块与资金流向
- 板块轮动图谱
- 资金在板块间的迁移方向
- 风格切换信号

### 四、关键个股与事件
- 本周财报亮点/雷点
- 重大个股事件
- 内部人交易/机构持仓变动

### 五、下周前瞻
- 下周关键经济数据日历
- 重要财报预览
- 技术面关键位分析

### 六、策略研判
- 中期市场方向判断
- 行业超配/低配建议
- 尾部风险预警
- 具体交易策略建议

要求：1500-2000字，专业、有深度、有明确观点。"""


def call_deepseek(prompt: str, max_tokens: int = 4096) -> str:
    """调用 DeepSeek v4 Pro API"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DASHSCOPE_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.6,
    }

    resp = requests.post(
        f"{DASHSCOPE_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return content


def _format_market_section(data: dict) -> str:
    lines = []
    for idx in data.get("indices", []):
        pct = idx.get("change_pct") or idx.get("week_change_pct", 0)
        sign = "+" if pct >= 0 else ""
        if "week_change_pct" in idx:
            label = "周涨跌"
        else:
            label = ""
        lines.append(f"- {idx['display_name']}: {idx['price']} ({sign}{pct:.2f}%{f' {label}' if label else ''})")
    return "\n".join(lines)


def _format_sector_section(data: dict) -> str:
    lines = []
    sectors = sorted(data.get("sectors", []), key=lambda x: x.get("change_pct") or x.get("week_change_pct") or 0, reverse=True)
    for s in sectors:
        pct = s.get("change_pct") or s.get("week_change_pct") or 0
        sign = "+" if pct >= 0 else ""
        lines.append(f"- {s['display_name']}: {sign}{pct:.2f}%")
    return "\n".join(lines)


def _format_futures_section(data: dict) -> str:
    lines = []
    for f in data.get("futures", []):
        sign = "+" if f.get("change_pct", 0) >= 0 else ""
        lines.append(f"- {f['display_name']}: {f['price']} ({sign}{f['change_pct']:.2f}%)")
    return "\n".join(lines)


def _format_macro_section(data: dict) -> str:
    lines = []
    for ind in data.get("indicators", []):
        change_str = f"{ind['change']:+.2f}" if ind.get("change") else "N/A"
        extra = f" — {ind['interpretation']}" if ind.get("interpretation") else ""
        lines.append(f"- {ind['name']}: {ind['value']} (周变化 {change_str}){extra}")
    return "\n".join(lines)


def _format_news_section(articles: list, max_items: int = 30) -> str:
    lines = []
    for i, a in enumerate(articles[:max_items], 1):
        source = a.get("source", "Unknown")
        lines.append(f"{i}. [{source}] {a['title']}")
        if a.get("summary"):
            lines.append(f"   > {a['summary'][:200]}")
    return "\n".join(lines)


def generate_daily_report(
    market_data: dict,
    movers: dict,
    macro_data: dict,
    news: list,
) -> str:
    md = _format_market_section(market_data)
    sd = _format_sector_section(market_data)
    fd = _format_futures_section(market_data)
    macd = _format_macro_section(macro_data)
    nd = _format_news_section(news)

    movers_text = ""
    if movers.get("gainers"):
        movers_text += "\n### 今日涨幅居前\n"
        for g in movers["gainers"][:5]:
            movers_text += f"- {g['symbol']} ({g.get('name','')}): +{g['change_pct']}%\n"
    if movers.get("losers"):
        movers_text += "\n### 今日跌幅居前\n"
        for l in movers["losers"][:5]:
            movers_text += f"- {l['symbol']} ({l.get('name','')}): {l['change_pct']}%\n"
    if movers.get("volume_anomalies"):
        movers_text += "\n### 成交量异常放大\n"
        for v in movers["volume_anomalies"][:5]:
            movers_text += f"- {v['symbol']}: 成交量 {v['vol_ratio']}x 均值\n"

    prompt = DAILY_PROMPT_TEMPLATE.format(
        market_data=md,
        sector_data=sd + movers_text,
        futures_data=fd,
        macro_data=macd,
        news_data=nd,
    )
    return call_deepseek(prompt)


def generate_weekly_report(
    weekly_data: dict,
    macro_data: dict,
    news: list,
) -> str:
    wm = _format_market_section(weekly_data)
    ws = _format_sector_section(weekly_data)
    macd = _format_macro_section(macro_data)
    nd = _format_news_section(news, max_items=40)

    prompt = WEEKLY_PROMPT_TEMPLATE.format(
        weekly_market=wm,
        weekly_sectors=ws,
        macro_data=macd,
        news_data=nd,
    )
    return call_deepseek(prompt, max_tokens=6144)
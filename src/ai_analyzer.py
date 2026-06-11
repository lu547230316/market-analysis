"""AI 分析引擎 — DeepSeek v4 Pro 阿里云百炼中转 — v5.0 多维度增强"""
import json
import requests
from datetime import datetime

from .config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL


SYSTEM_PROMPT = """你是一位高盛集团(Goldman Sachs)全球首席市场策略师，拥有20年华尔街经验。

## 分析框架
你必须使用四维交叉验证框架，每个核心结论至少从以下4个维度中引用2个维度来支撑：

1. **技术面** — RSI、MACD、均线(50/200日)、布林带位置、支撑/阻力位
2. **基本面** — P/E、EPS增速、PEG、营收增长、利润率趋势
3. **情绪/资金面** — VIX期限结构、Put/Call隐含情绪、板块资金流向、成交量异动、KOL观点倾向
4. **宏观/事件面** — 利率概率、经济日历、地缘政治、政策事件、利多/利空新闻密度

## 写作风格
- 每个核心论点必须标注置信度：**[高置信度]** / **[中置信度]** / **[低置信度]**
- 重要判断列出多空双方观点，格式：「多头认为... vs 空头认为... → 我方判断...」
- 给出具体的交易策略建议，包含明确的入场/出场参考价位
- 关键数字用粗体标注
- 报告开头给出 100-150 字执行摘要（Executive Summary）
- 中文输出，保留关键英文术语（Fed、EPS、P/E、VIX、MACD、RSI等）
- 结尾给出明确的风险提示和止损建议

## 禁止
- 模糊表述如「可能」「或许」「值得关注」（改成具体判断+置信度）
- 没有数据支撑的空泛结论
- 片面看多或看空，必须呈现对立观点"""


DAILY_PROMPT_TEMPLATE = """以高盛首席策略师身份，基于以下多维度数据撰写**当日市场热点分析与次日盘前前瞻**。

## 技术面数据
{technical_data}

## 大盘与板块数据
{market_data}
{sector_data}

## 期货与关键资产
{futures_data}

## 宏观与情绪
{macro_data}
{sentiment_data}

## 资金流向
{fund_flow_data}

## 估值数据
{valuation_data}

## 经济日历
{calendar_data}

## KOL 观点聚合
{kol_data}

## 过去24h 利多/利空新闻分析
{news_sentiment}

## 美股七姐妹 (Magnificent 7) 深度分析
{mag7_data}

## SOXX 半导体板块分析
{soxx_data}

## 今日重要新闻
{news_data}

## 纠错 Agent 数据质量报告
{error_check}

按以下结构输出：

### Executive Summary
（100-150字核心摘要：今日市场一句话定调 + 明日最关键的1-2个关注点）

### 一、市场全景
- 三大指数表现与驱动归因
- VIX信号 + 市场情绪判断（给出情绪象限：亢奋/积极/中性/谨慎/恐慌）
- 置信度：**[高/中/低]**

### 二、技术面深度分析
- 标普500关键技术位：支撑/阻力/均线/RSI/MACD
- 多空双方技术论点
- 关键价位预警

### 三、板块与资金流
- 涨幅最大板块 TOP3 及催化剂（每板块标注置信度）
- 资金流向异常信号
- 板块轮动判断

### 四、KOL 观点与市场情绪
- 重要 KOL 观点汇总（看多/看空阵营）
- KOL 观点分歧点分析
- 对散户和机构的参考价值

### 五、利多/利空新闻解读
- TOP 利多新闻及影响分析（每条标注置信度）
- TOP 利空新闻及风险评估（每条标注置信度）
- 利多/利空力量对比判断
- 被市场低估的新闻事件

### 六、七姐妹与半导体板块
- 七姐妹个股技术面速览（RSI/MACD/趋势/信号）
- 七姐妹中谁最强/谁最弱 + 原因分析
- SOXX 半导体板块整体判断
- 半导体子板块轮动（AI芯片/存储/设备/代工）
- 重点个股操作建议（含具体价位）

### 七、个股异动
- 异常涨跌 + 技术信号 + 估值锚点
- 成交量异动 + 潜在原因

### 八、明日前瞻
- 期货指向（隐含开盘方向）
- 明日关键事件时间线
- 情景分析：
  - **Bull case (概率%)** — 触发条件 + 目标位
  - **Base case (概率%)** — 最可能路径
  - **Bear case (概率%)** — 风险触发条件
- 技术面关键支撑/阻力位

### 九、策略建议
- 短期仓位建议（具体到板块/风格）
- 七姐妹中推荐/回避标的
- 半导体板块操作策略
- 对冲策略建议
- 止损/止盈参考位
- **风险提示**

要求：2000-3000字，每一个判断都要有数据锚点。"""


WEEKLY_PROMPT_TEMPLATE = """以高盛首席策略师身份撰写**本周美股市场总结与下周前瞻**。

## 本周大盘表现
{weekly_market}

## 板块轮动
{weekly_sectors}

## 技术面综合
{technical_data}

## 宏观环境
{macro_data}

## 情绪与资金流
{sentiment_data}
{fund_flow_data}

## KOL 观点汇总
{kol_data}

## 本周利多/利空新闻分析
{news_sentiment}

## 七姐妹本周表现
{mag7_data}

## SOXX 半导体板块
{soxx_data}

## 本周重要新闻回顾
{news_data}

## 下周经济日历
{calendar_data}

按以下结构输出：

### Executive Summary
（150-200字：本周市场一句话总结 + 下周核心主题预判）

### 一、本周市场全景
- 指数周涨跌 + 技术面位置（相对于50/200日均线）
- 市场风格（成长vs价值、大盘vs小盘）
- VIX演变 + 情绪变化轨迹

### 二、核心主题回顾
- 本周3-5个主导叙事（每叙事标注置信度）
- 多空双方对每个叙事的解读
- 实际市场反应 vs 预期

### 三、板块与资金流深度
- 板块轮动图谱（用相对强度排序）
- 资金跨板块迁移方向
- 风格切换信号

### 四、KOL 观点与市场共识
- 本周 KOL 观点变化轨迹
- 机构 vs 散户情绪分歧
- 逆向指标信号

### 五、利多/利空力量复盘
- 本周利多/利空新闻统计
- 被市场消化的 vs 被忽视的信息
- 下周潜在催化剂

### 六、七姐妹与半导体板块周度复盘
- 七姐妹周涨跌排名 + 驱动因素
- 七姐妹技术面趋势变化
- SOXX 板块周度表现 + 子板块轮动
- 半导体供需动态
- AI 芯片需求信号

### 七、关键个股与事件
- 本周财报亮点/雷点 + 估值重定价
- 重大事件复盘

### 八、下周前瞻
- 关键经济数据日历（标注重要性）
- 重要财报预览 + 市场预期
- 三情景分析：
  - **Bull case** — 触发条件 + 标普目标位
  - **Base case** — 最可能路径 + 概率
  - **Bear case** — 风险触发条件 + 下行目标

### 九、策略研判
- 中期（1-3个月）市场方向判断 **[置信度: 高/中/低]**
- 行业超配/低配建议（给出具体板块权重）
- 七姐妹配置建议（超配/标配/低配）
- 半导体板块配置建议
- 尾部风险预警
- 具体交易策略（ETF/个股/对冲）

要求：2500-4000字，每个判断有数据支撑，多空观点平衡呈现。"""


def call_deepseek(prompt: str, max_tokens: int = 4096) -> str:
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
        timeout=180,
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
        label = " 周涨跌" if "week_change_pct" in idx else ""
        lines.append(f"- {idx['display_name']}: {idx['price']} ({sign}{pct:.2f}%{label})")
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


def _format_technical_section(data: dict) -> str:
    lines = []
    for name, tech in data.items():
        if isinstance(tech, dict) and "error" not in tech:
            lines.append(f"\n**{name}** ({tech.get('price', 'N/A')})")
            lines.append(f"  RSI: {tech.get('rsi', 'N/A')} ({tech.get('rsi_signal', '')})")
            lines.append(f"  50日均线: {tech.get('sma50', 'N/A')} | 200日均线: {tech.get('sma200', 'N/A')}")
            lines.append(f"  支撑: {tech.get('support', 'N/A')} | 阻力: {tech.get('resistance', 'N/A')}")
            macd_info = tech.get('macd', {})
            lines.append(f"  MACD: {'看涨' if macd_info.get('bullish') else '看跌'}")
            signals = tech.get('signals', [])
            if signals:
                lines.append(f"  信号: {', '.join(signals)}")
            lines.append(f"  趋势: {tech.get('trend', 'N/A')}")
    return "\n".join(lines) if lines else "技术面数据暂不可用"


def _format_sentiment_section(data: dict) -> str:
    lines = []
    sentiment = data.get('sentiment', 'N/A')
    risk = data.get('risk_score', 'N/A')
    lines.append(f"综合情绪: {sentiment} (风险评分: {risk}/8)")

    vix_data = data.get('vix', {})
    if vix_data.get('current'):
        lines.append(f"VIX: {vix_data['current']} — 期限结构: {vix_data.get('contango', 'N/A')}")
        lines.append(f"VIX趋势: {vix_data.get('trend', 'N/A')}")
        lines.append(f"风险等级: {vix_data.get('risk_level', 'N/A')}")

    breadth = data.get('breadth', {})
    if breadth.get('spy_vs_50ma_pct') is not None:
        lines.append(f"标普500 vs 50日均线: {breadth['spy_vs_50ma_pct']:+.2f}% ({breadth.get('signal', '')})")
    return "\n".join(lines)


def _format_fundflow_section(data: dict) -> str:
    lines = []
    sorted_flows = sorted(data.items(), key=lambda x: x[1].get('5d_change_pct', 0), reverse=True)
    for name, info in sorted_flows[:8]:
        lines.append(f"- {name}: {info['5d_change_pct']:+.2f}% | 量比: {info['vol_ratio']}x | {info['flow']}")
    return "\n".join(lines) if lines else "资金流数据暂不可用"


def _format_valuation_section(data: list) -> str:
    lines = []
    for v in data[:10]:
        pe = f"P/E {v.get('pe_ttm', 'N/A')}" if v.get('pe_ttm') else ""
        peg = f"PEG {v.get('peg_ratio', 'N/A')}" if v.get('peg_ratio') else ""
        fwd = f"Fwd P/E {v.get('pe_forward', 'N/A')}" if v.get('pe_forward') else ""
        lines.append(f"- {v['symbol']} ({v.get('name', '')}): {pe} | {fwd} | {peg}")
    return "\n".join(lines) if lines else "估值数据暂不可用"


def _format_mag7_section(mag7_data: list) -> str:
    """格式化七姐妹数据"""
    if not mag7_data:
        return "暂无七姐妹数据"
    from .mag7_analyzer import format_mag7_for_prompt
    return format_mag7_for_prompt(mag7_data)


def _format_soxx_section(soxx_data: dict) -> str:
    """格式化 SOXX 数据"""
    if not soxx_data:
        return "暂无 SOXX 数据"
    from .mag7_analyzer import format_soxx_for_prompt
    return format_soxx_for_prompt(soxx_data)


def _format_kol_section(kol_data: dict) -> str:
    """格式化 KOL 数据"""
    if not kol_data:
        return "暂无 KOL 观点数据"
    from .kol_collector import format_kol_for_prompt
    return format_kol_for_prompt(kol_data)


def _format_news_sentiment_section(sentiment_data: dict) -> str:
    """格式化新闻情绪数据"""
    if not sentiment_data:
        return "暂无新闻情绪数据"
    from .news_analyzer import format_news_sentiment_for_prompt
    return format_news_sentiment_for_prompt(sentiment_data)


def _format_error_check_section(error_data: dict) -> str:
    """格式化纠错数据"""
    if not error_data:
        return "纠错检查通过"
    from .error_checker import format_error_check_for_prompt
    return format_error_check_for_prompt(error_data)


def generate_daily_report(
    market_data: dict,
    movers: dict,
    macro_data: dict,
    news: list,
    technical_data: dict = None,
    sentiment_data: dict = None,
    fund_flow_data: dict = None,
    valuation_data: list = None,
    calendar_data: str = "",
    kol_data: dict = None,
    news_sentiment: dict = None,
    mag7_data: list = None,
    soxx_data: dict = None,
) -> str:
    md = _format_market_section(market_data)
    sd = _format_sector_section(market_data)
    fd = _format_futures_section(market_data)
    macd = _format_macro_section(macro_data)
    nd = _format_news_section(news)

    td = _format_technical_section(technical_data) if technical_data else "技术面数据暂不可用"
    sentd = _format_sentiment_section(sentiment_data) if sentiment_data else "情绪数据暂不可用"
    ffd = _format_fundflow_section(fund_flow_data) if fund_flow_data else "资金流数据暂不可用"
    vd = _format_valuation_section(valuation_data) if valuation_data else "估值数据暂不可用"
    kold = _format_kol_section(kol_data) if kol_data else "暂无 KOL 观点"
    nsd = _format_news_sentiment_section(news_sentiment) if news_sentiment else "暂无新闻情绪分析"
    mag7d = _format_mag7_section(mag7_data) if mag7_data else "暂无七姐妹数据"
    soxxd = _format_soxx_section(soxx_data) if soxx_data else "暂无 SOXX 数据"

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
        technical_data=td,
        market_data=md,
        sector_data=sd + movers_text,
        futures_data=fd,
        macro_data=macd,
        sentiment_data=sentd,
        fund_flow_data=ffd,
        valuation_data=vd,
        calendar_data=calendar_data or "暂无近期关键事件",
        kol_data=kold,
        news_sentiment=nsd,
        mag7_data=mag7d,
        soxx_data=soxxd,
        news_data=nd,
        error_check="纠错检查将在报告生成后执行",
    )
    return call_deepseek(prompt, max_tokens=6144)


def generate_weekly_report(
    weekly_data: dict,
    macro_data: dict,
    news: list,
    technical_data: dict = None,
    sentiment_data: dict = None,
    fund_flow_data: dict = None,
    calendar_data: str = "",
    kol_data: dict = None,
    news_sentiment: dict = None,
    mag7_data: list = None,
    soxx_data: dict = None,
) -> str:
    wm = _format_market_section(weekly_data)
    ws = _format_sector_section(weekly_data)
    macd = _format_macro_section(macro_data)
    nd = _format_news_section(news, max_items=40)
    td = _format_technical_section(technical_data) if technical_data else "技术面数据暂不可用"
    sentd = _format_sentiment_section(sentiment_data) if sentiment_data else "情绪数据暂不可用"
    ffd = _format_fundflow_section(fund_flow_data) if fund_flow_data else "资金流数据暂不可用"
    kold = _format_kol_section(kol_data) if kol_data else "暂无 KOL 观点"
    nsd = _format_news_sentiment_section(news_sentiment) if news_sentiment else "暂无新闻情绪分析"
    mag7d = _format_mag7_section(mag7_data) if mag7_data else "暂无七姐妹数据"
    soxxd = _format_soxx_section(soxx_data) if soxx_data else "暂无 SOXX 数据"

    prompt = WEEKLY_PROMPT_TEMPLATE.format(
        weekly_market=wm,
        weekly_sectors=ws,
        technical_data=td,
        macro_data=macd,
        sentiment_data=sentd,
        fund_flow_data=ffd,
        kol_data=kold,
        news_sentiment=nsd,
        mag7_data=mag7d,
        soxx_data=soxxd,
        news_data=nd,
        calendar_data=calendar_data or "暂无近期关键事件",
    )
    return call_deepseek(prompt, max_tokens=8192)

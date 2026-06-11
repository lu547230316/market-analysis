全自动市场热点分析系统 v5.0 — 多Agent并行架构
=================================================

v5.0 核心升级:
1. 多Agent并行处理 — 8个数据采集Agent + 2个后处理Agent同时运行
2. 纠错Agent — 数据质量验证 + 技术指标一致性检查 + AI报告质量审核
3. KOL观点聚合 — 8位华尔街顶级KOL观点实时追踪
4. 利多/利空新闻分析 — 过去24h新闻情绪分类 + 关键词加权打分
5. 七姐妹深度分析 — Magnificent 7 技术面 + 估值 + 成交量
6. SOXX半导体分析 — 16只权重股 + 子板块轮动 + AI芯片需求信号

项目结构:
├── .github/workflows/
│   ├── daily_report.yml       — 每个交易日 21:00 (BJT) 触发
│   └── weekly_report.yml      — 每周六 09:00 (BJT) 触发
├── src/
│   ├── __init__.py            — 版本 v5.0.0
│   ├── config.py              — 环境变量配置
│   ├── parallel_runner.py     — [新] 多Agent并行执行框架
│   ├── data_cache.py          — 统一数据缓存层
│   ├── data_collector.py      — yfinance 行情采集
│   ├── technical_analyzer.py  — 指数技术分析
│   ├── sentiment_data.py      — 市场情绪计算
│   ├── macro_data.py          — 宏观数据采集
│   ├── economic_calendar.py   — 经济日历
│   ├── news_collector.py      — 新闻采集 (东方财富)
│   ├── kol_collector.py       — [新] KOL观点聚合 (8位华尔街大佬)
│   ├── news_analyzer.py       — [新] 利多/利空新闻分类
│   ├── mag7_analyzer.py       — [新] 七姐妹 + SOXX深度分析
│   ├── error_checker.py       — [新] 纠错Agent
│   ├── ai_analyzer.py         — AI分析引擎 (DeepSeek v4 Pro)
│   ├── report_generator.py    — 主编排器 (v5.0 并行架构)
│   └── email_sender.py        — QQ邮箱 SMTP 发送
├── main_daily.py              — 日报入口
├── main_weekly.py             — 周报入口
└── requirements.txt           — Python 依赖

并行执行架构:
====================

Phase 0: 预热缓存
  └── 集中预取所有股票/指数数据 (含SOXX权重股)

Phase 1: 多Agent并行采集 (8路并发)
  ├── Agent 1: 市场行情 (指数/板块/期货)
  ├── Agent 2: 技术分析 (RSI/MACD/均线)
  ├── Agent 3: 情绪数据 (VIX/波动率/广度)
  ├── Agent 4: 资金流向 (板块资金流)
  ├── Agent 5: 估值数据 (P/E/PEG)
  ├── Agent 6: 异动扫描 (涨跌幅/成交量异常)
  ├── Agent 7: 七姐妹分析 (技术面+估值)
  └── Agent 8: SOXX分析 (半导体ETF+16只权重股)

Phase 2: 后处理Agent (4路并发)
  ├── Agent 9:  KOL观点提取 (依赖新闻数据)
  └── Agent 10: 利多/利空新闻分类 (依赖新闻数据)

Phase 3: AI分析生成
  └── DeepSeek v4 Pro 生成完整报告

Phase 4: 纠错验证
  ├── 数据质量检查 (空值/异常)
  ├── 价格异常检测 (涨跌幅阈值)
  ├── 技术指标一致性 (RSI vs MACD 矛盾)
  ├── AI报告质量审核 (长度/章节/多空平衡)
  └── 数据-报告一致性 (价格是否被引用)

Phase 5: 邮件发送
  └── 高盛风格 HTML 邮件

KOL 观点追踪:
====================
- Warren Buffett (伯克希尔) — 价值投资之神
- Ray Dalio (桥水基金) — 全球最大对冲基金
- Cathie Wood (ARK Invest) — 颠覆性创新旗手
- Jim Cramer (CNBC Mad Money) — 散户风向标
- Jamie Dimon (摩根大通) — 华尔街最有影响力的银行家
- Michael Burry (Scion Asset) — 《大空头》原型
- Stanley Druckenmiller (Duquesne) — 传奇宏观交易员
- Elon Musk (特斯拉/SpaceX) — 科技界最具影响力

七姐妹 (Magnificent 7):
====================
AAPL (苹果) | MSFT (微软) | NVDA (英伟达) | GOOGL (谷歌)
AMZN (亚马逊) | META (Meta) | TSLA (特斯拉)

SOXX 半导体权重股:
====================
NVDA (10.5%) | AVGO (9.0%) | TSM (5.0%) | AMD (5.5%) | QCOM (5.0%)
INTC (4.0%) | TXN (4.5%) | MRVL (3.5%) | MU (3.5%) | ASML (3.5%)
KLAC (3.0%) | LRCX (3.0%) | AMAT (3.0%) | ADI (2.5%) | ON (2.0%) | NXPI (2.0%)

报告新增章节:
====================
日报 (9大章节):
  1. Executive Summary (执行摘要)
  2. 市场全景 (指数/情绪)
  3. 技术面深度分析
  4. 板块与资金流
  5. KOL观点与市场情绪 [新增]
  6. 利多/利空新闻解读 [新增]
  7. 七姐妹与半导体板块 [新增]
  8. 个股异动
  9. 明日前瞻 + 策略建议

周报 (9大章节):
  1. Executive Summary
  2. 本周市场全景
  3. 核心主题回顾
  4. 板块与资金流深度
  5. KOL观点与市场共识 [新增]
  6. 利多/利空力量复盘 [新增]
  7. 七姐妹与半导体板块周度复盘 [新增]
  8. 关键个股与事件
  9. 下周前瞻 + 策略研判

部署步骤:
====================
1. 将代码推送到 GitHub 私有仓库
2. 设置 Secrets:
   - QQ_EMAIL: 547230316@qq.com
   - QQ_SMTP_AUTH: QQ邮箱授权码
   - DASHSCOPE_API_KEY: 阿里云百炼 API Key
   - NEWSAPI_KEY: (可选) NewsAPI key
3. GitHub Actions 自动按 cron 运行
4. 支持手动触发 workflow_dispatch

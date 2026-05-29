全自动市场热点分析系统 — 文件说明
=====================================

项目结构:
├── .github/workflows/
│   ├── daily_report.yml       — GitHub Actions 日报定时任务 (每个交易日 21:00 BJT)
│   └── weekly_report.yml      — GitHub Actions 周报定时任务 (每周六 09:00 BJT)
├── src/
│   ├── config.py              — 环境变量配置
│   ├── data_collector.py      — yfinance 行情数据采集
│   ├── news_collector.py      — 新闻聚合 (NewsAPI + RSS)
│   ├── macro_data.py          — 宏观数据 (VIX/利率/美元指数)
│   ├── ai_analyzer.py         — DeepSeek v4 Pro 分析引擎
│   ├── email_sender.py        — QQ邮箱 SMTP 发送器
│   └── report_generator.py    — 主编排器 (日报/周报)
├── main_daily.py              — 日报入口
├── main_weekly.py             — 周报入口
└── requirements.txt           — Python 依赖

部署步骤:
1. 在 GitHub 创建私有仓库
2. 设置 Secrets:
   - QQ_EMAIL: 547230316@qq.com
   - QQ_SMTP_AUTH: 你的QQ邮箱授权码
   - DASHSCOPE_API_KEY: 阿里云百炼 API Key
   - NEWSAPI_KEY: (可选) NewsAPI key from newsapi.org
3. 推送代码到 GitHub
4. GitHub Actions 自动按 cron 运行

定时说明:
- 日报: 北京时间周一至周五 21:00 发送
- 周报: 北京时间周六 09:00 发送
- 均支持手动触发 (workflow_dispatch)

NewsAPI 获取: https://newsapi.org/register (免费版 100次/天)
如果不用 NewsAPI，系统会自动回退到 RSS 源获取新闻。
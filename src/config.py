"""配置管理 — 所有密钥从环境变量读取"""
import os

# QQ邮箱 SMTP
QQ_EMAIL = os.environ["QQ_EMAIL"]
QQ_SMTP_AUTH = os.environ["QQ_SMTP_AUTH"]
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465

# 阿里云百炼 DeepSeek v4 Pro
DASHSCOPE_API_KEY = os.environ["DASHSCOPE_API_KEY"]
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL = "deepseek-v4-pro"

# NewsAPI (可选，无 key 时回退到 RSS)
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")

# 邮件接收
TO_EMAIL = os.environ.get("TO_EMAIL", QQ_EMAIL)

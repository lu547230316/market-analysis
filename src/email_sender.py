"""邮件发送 — QQ邮箱 SMTP SSL"""
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
import traceback

from .config import QQ_EMAIL, QQ_SMTP_AUTH, SMTP_SERVER, SMTP_PORT, TO_EMAIL


def _markdown_to_html(md_text: str) -> str:
    """Markdown → 高盛风格 HTML 邮件"""
    lines = md_text.split("\n")
    html_parts = []

    css = """
    <style>
        body { font-family: 'Georgia', 'Times New Roman', serif; background: #f5f5f0; margin: 0; padding: 0; }
        .container { max-width: 680px; margin: 0 auto; background: #ffffff; }
        .header { background: linear-gradient(135deg, #0f3460 0%, #16213e 100%); color: white; padding: 30px 40px; }
        .header h1 { font-size: 22px; margin: 0; font-weight: bold; letter-spacing: 1px; }
        .header .subtitle { font-size: 13px; opacity: 0.85; margin-top: 8px; }
        .header .date { font-size: 12px; opacity: 0.7; margin-top: 4px; }
        .dashboard { background: #f8f9fa; padding: 20px 40px; border-bottom: 3px solid #e94560; }
        .dashboard table { width: 100%; border-collapse: collapse; font-size: 14px; }
        .dashboard td { padding: 6px 12px; }
        .dashboard .up { color: #16a34a; font-weight: bold; }
        .dashboard .down { color: #dc2626; font-weight: bold; }
        .content { padding: 30px 40px; }
        .content p { line-height: 1.9; color: #333; font-size: 15px; margin: 10px 0; }
        .content h2 { color: #0f3460; font-size: 19px; border-left: 4px solid #e94560; padding-left: 12px; margin: 28px 0 14px 0; }
        .content h3 { color: #16213e; font-size: 16px; margin: 20px 0 10px 0; }
        .content strong { color: #0f3460; }
        .content ul { padding-left: 20px; }
        .content li { line-height: 1.8; margin: 4px 0; color: #444; }
        .content blockquote { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 10px 16px; margin: 12px 0; color: #92400e; }
        .confidence-high { background: #dcfce7; color: #166534; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
        .confidence-mid { background: #fef3c7; color: #92400e; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
        .confidence-low { background: #fee2e2; color: #991b1b; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
        .footer { background: #1a1a2e; color: #999; padding: 20px 40px; font-size: 12px; text-align: center; }
        .footer a { color: #e94560; text-decoration: none; }
        .signal-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 16px; border-radius: 6px; margin: 8px 0; }
        .risk-box { background: #fef2f2; border: 1px solid #fecaca; padding: 12px 16px; border-radius: 6px; margin: 8px 0; }
        hr { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }
    </style>
    """

    html_parts.append(css)
    html_parts.append('<div class="container">')

    in_list = False
    header_done = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        if not header_done:
            header_done = True
            title_text = stripped.strip("# ").strip("【】")
            html_parts.append(f'<div class="header"><h1>{title_text}</h1>')
            html_parts.append('<div class="subtitle">Goldman Sachs-Style Market Intelligence</div>')
            html_parts.append('<div class="date">全自动AI生成 · 仅供参考 · 不构成投资建议</div></div>')
            continue

        if stripped.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith("# "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<h2>{stripped[2:]}</h2>')
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped[2:])
            text = text.replace("[高置信度]", '<span class="confidence-high">高置信度</span>')
            text = text.replace("[中置信度]", '<span class="confidence-mid">中置信度</span>')
            text = text.replace("[低置信度]", '<span class="confidence-low">低置信度</span>')
            html_parts.append(f"<li>{text}</li>")
        elif stripped.startswith("> "):
            html_parts.append(f'<blockquote>{stripped[2:]}</blockquote>')
        elif stripped == "---":
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append("<hr>")
        elif stripped.startswith("**Bull case") or stripped.startswith("**Bear case"):
            box_class = "signal-box" if "Bull" in stripped else "risk-box"
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            text = text.replace("[高置信度]", '<span class="confidence-high">高置信度</span>')
            text = text.replace("[中置信度]", '<span class="confidence-mid">中置信度</span>')
            text = text.replace("[低置信度]", '<span class="confidence-low">低置信度</span>')
            html_parts.append(f'<div class="{box_class}"><p style="margin:0;">{text}</p></div>')
        elif stripped.startswith("### Executive Summary"):
            html_parts.append(f'<div class="signal-box"><h3 style="margin-top:0;">{stripped[4:]}</h3>')
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            text = text.replace("[高置信度]", '<span class="confidence-high">高置信度</span>')
            text = text.replace("[中置信度]", '<span class="confidence-mid">中置信度</span>')
            text = text.replace("[低置信度]", '<span class="confidence-low">低置信度</span>')
            html_parts.append(f"<p>{text}</p>")

    if in_list:
        html_parts.append("</ul>")

    html_parts.append("</div>")  # close content area
    html_parts.append('<div class="footer">本报告由AI全自动生成，仅供研究参考，不构成投资建议。<br>数据来源: Yahoo Finance, Reuters, CNBC, Bloomberg, MarketWatch<br>Powered by DeepSeek v4 Pro · <a href="https://github.com/lu547230316/market-analysis">Market Analysis System v2.0</a></div>')
    html_parts.append("</div>")  # close container

    return "\n".join(html_parts)


def send_report(subject: str, body: str, is_html: bool = False) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = QQ_EMAIL
        msg["To"] = TO_EMAIL
        msg["Subject"] = Header(subject, "utf-8")

        if is_html:
            html_content = _markdown_to_html(body)
            html_part = MIMEText(html_content, "html", "utf-8")
            plain_part = MIMEText(body, "plain", "utf-8")
            msg.attach(plain_part)
            msg.attach(html_part)
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.login(QQ_EMAIL, QQ_SMTP_AUTH)
            server.sendmail(QQ_EMAIL, [TO_EMAIL], msg.as_string())

        print(f"[{datetime.now()}] 邮件发送成功: {subject}")
        return True

    except Exception as e:
        print(f"[{datetime.now()}] 邮件发送失败: {e}")
        traceback.print_exc()
        return False


def send_daily_report(report_body: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"【市场热点日报】{today} 美股盘前前瞻 — 高盛级别分析"
    return send_report(subject, report_body, is_html=True)


def send_weekly_report(report_body: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"【美股周度复盘】{today} 本周总结与下周前瞻 — 高盛级别分析"
    return send_report(subject, report_body, is_html=True)
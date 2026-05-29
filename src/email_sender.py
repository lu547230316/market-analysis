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
    lines = md_text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br>")
            continue

        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h3 style="color:#1a1a2e;margin-top:20px;">{stripped[4:]}</h3>')
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h2 style="color:#16213e;border-bottom:2px solid #e94560;padding-bottom:5px;">{stripped[3:]}</h2>')
        elif stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<h1 style="color:#0f3460;">{stripped[2:]}</h1>')
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append('<ul style="line-height:1.8;">')
                in_list = True
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("> "):
            html_lines.append(f'<blockquote style="color:#555;border-left:3px solid #e94560;padding-left:10px;margin:5px 0;">{stripped[2:]}</blockquote>')
        elif stripped.startswith("---"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
            html_lines.append(f"<p style='line-height:1.8;'>{text}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


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
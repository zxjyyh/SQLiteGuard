import smtplib
from email.mime.text import MIMEText
from database.db import get_db


def send_email(subject, body):
    """统一邮件发送函数，自动根据端口选择SSL/STARTTLS"""
    conn = get_db()
    smtp = conn.execute("SELECT * FROM smtp_config WHERE id = 1").fetchone()
    conn.close()

    if not smtp or not smtp['host'] or not smtp['username']:
        return False, '邮件服务未配置'

    recipient = smtp['recipient_email'] or smtp['username']
    sender = smtp['from_addr'] or smtp['username']

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        port = smtp['port']

        # 465端口使用SSL直连，其他端口使用STARTTLS
        if port == 465:
            server = smtplib.SMTP_SSL(smtp['host'], port, timeout=10)
        else:
            server = smtplib.SMTP(smtp['host'], port, timeout=10)
            server.starttls()

        server.login(smtp['username'], smtp['password'])
        server.sendmail(sender, [recipient], msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)

"""邮件通知服务"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Mailer:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", 587))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.from_email = os.environ.get("FROM_EMAIL", self.smtp_user)

    def send(self, to, subject, body):
        """发送邮件"""
        if not self.smtp_user or not self.smtp_pass:
            return {"ok": False, "error": "邮件未配置。设置环境变量: SMTP_USER, SMTP_PASS"}

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to
            msg["Subject"] = f"[NebulaCraft] {subject}"

            msg.attach(MIMEText(body, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            return {"ok": True, "message": "邮件已发送"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def send_summary(self, to, summary_data):
        """发送每日摘要"""
        html = f"""
        <h2>📊 NebulaCraft 每日摘要</h2>
        <p>日期: {summary_data.get('date', '')}</p>
        <p>对话数: {summary_data.get('total', 0)}</p>
        <hr>
        <p style="color:#666;font-size:12px">由 NebulaCraft v7.0 自动生成</p>
        """
        return self.send(to, "每日摘要", html)

    def get_status(self):
        return {
            "ok": True,
            "configured": bool(self.smtp_user and self.smtp_pass),
            "from": self.from_email,
            "tip": "设置环境变量: SMTP_USER, SMTP_PASS, SMTP_HOST(可选), SMTP_PORT(可选)",
        }


mailer = Mailer()
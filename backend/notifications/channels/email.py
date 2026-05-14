import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from channels.base import BaseChannel, SendResult
from core.config import SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


class EmailChannel(BaseChannel):
    def send(self, recipient: str, subject: str, message: str) -> SendResult:
        if not SMTP_USER or not SMTP_PASSWORD:
            return SendResult(success=False, error="SMTP credentials not configured")

        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_FROM
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, recipient, msg.as_string())

            return SendResult(success=True)
        except Exception as e:
            return SendResult(success=False, error=str(e))

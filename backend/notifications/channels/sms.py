import os

from channels.base import BaseChannel, SendResult


SMS_API_KEY = os.getenv("SMS_API_KEY", "")
SMS_SENDER = os.getenv("SMS_SENDER", "ZHSK")


class SMSChannel(BaseChannel):
    def send(self, recipient: str, subject: str, message: str) -> SendResult:
        # TODO: реализовать через провайдера SMS (например, SMSC.ru или SMS.ru)
        # recipient = номер телефона в формате 79XXXXXXXXX
        if not SMS_API_KEY:
            return SendResult(success=False, error="SMS_API_KEY not configured")

        # import requests
        # resp = requests.get("https://smsc.ru/sys/send.php", params={
        #     "login": SMS_SENDER, "psw": SMS_API_KEY,
        #     "phones": recipient, "mes": message,
        # })
        return SendResult(success=False, error="SMS channel not implemented yet")

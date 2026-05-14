from channels.base import BaseChannel, SendResult
from channels.email import EmailChannel
from channels.sms import SMSChannel
from channels.vk import VKChannel


def get_channel(channel_type: str) -> BaseChannel:
    if channel_type == "email":
        return EmailChannel()
    if channel_type == "vk":
        return VKChannel()
    if channel_type == "sms":
        return SMSChannel()
    raise ValueError(f"Unknown notification channel: {channel_type!r}")


def dispatch(
    channel_type: str,
    recipient: str,
    subject: str,
    message: str,
) -> SendResult:
    channel = get_channel(channel_type)
    return channel.send(recipient, subject, message)

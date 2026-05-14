import os

from channels.base import BaseChannel, SendResult


VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN", "")


class VKChannel(BaseChannel):
    def send(self, recipient: str, subject: str, message: str) -> SendResult:
        # TODO: реализовать через VK Messages API
        # https://dev.vk.com/ru/method/messages.send
        # recipient = vk_id пользователя
        if not VK_ACCESS_TOKEN:
            return SendResult(success=False, error="VK_ACCESS_TOKEN not configured")

        # import vk_api
        # vk = vk_api.VkApi(token=VK_ACCESS_TOKEN)
        # vk.method("messages.send", {"user_id": recipient, "message": message, "random_id": 0})
        return SendResult(success=False, error="VK channel not implemented yet")

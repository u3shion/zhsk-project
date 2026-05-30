"""
VK-канал уведомлений.

Отправляет сообщения от имени VK-сообщества (группы) через API messages.send.

Требования:
1. Создать сообщество ВКонтакте.
2. В настройках сообщества → Работа с API → создать ключ доступа
   с правами: «Сообщения сообщества» + «Управление сообществом».
3. Разрешить отправку сообщений: Управление → Сообщения → включить.
4. Каждый пользователь должен сначала написать в сообщество сам
   (или нажать «Разрешить отправку сообщений») — иначе VK вернёт ошибку 901.
5. В профиле жильца поле vk_id должно содержать числовой ID страницы ВКонтакте
   (не короткое имя, а именно id — его можно найти через vk.com/id123456).
"""
import random

import httpx

from channels.base import BaseChannel, SendResult
from core.config import VK_API_VERSION, VK_GROUP_TOKEN


VK_API_BASE = "https://api.vk.com/method"

VK_ERROR_MESSAGES = {
    5: "Invalid or expired token (VK error 5)",
    7: "Permission denied — check token permissions (VK error 7)",
    9: "Flood control — too many messages sent (VK error 9)",
    15: "Access denied to this user (VK error 15)",
    901: "User has not allowed messages from this community (VK error 901)",
    902: "User is in the community's blacklist (VK error 902)",
}


class VKChannel(BaseChannel):
    def send(self, recipient: str, subject: str, message: str) -> SendResult:
        """
        recipient — числовой VK user_id (строка), например "123456789".
        subject включается в текст сообщения первой строкой.
        """
        if not VK_GROUP_TOKEN:
            return SendResult(success=False, error="VK_GROUP_TOKEN is not configured")

        if not recipient or not recipient.strip().lstrip("-").isdigit():
            return SendResult(
                success=False,
                error=f"Invalid vk_id {recipient!r} — must be a numeric VK user ID",
            )

        text = f"📢 {subject}\n\n{message}" if subject else message

        try:
            response = httpx.post(
                f"{VK_API_BASE}/messages.send",
                params={
                    "user_id": recipient,
                    "message": text,
                    "random_id": random.randint(1, 2**31),
                    "access_token": VK_GROUP_TOKEN,
                    "v": VK_API_VERSION,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                code = data["error"].get("error_code", 0)
                default_msg = data["error"].get("error_msg", "Unknown VK error")
                error_text = VK_ERROR_MESSAGES.get(code, f"{default_msg} (VK error {code})")
                return SendResult(success=False, error=error_text)

            return SendResult(success=True)

        except httpx.TimeoutException:
            return SendResult(success=False, error="VK API request timed out")
        except httpx.HTTPStatusError as e:
            return SendResult(success=False, error=f"VK API HTTP error: {e.response.status_code}")
        except Exception as e:
            return SendResult(success=False, error=str(e))

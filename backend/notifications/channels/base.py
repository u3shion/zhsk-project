from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendResult:
    success: bool
    error: str | None = None


class BaseChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, message: str) -> SendResult:
        """
        recipient — email, телефон или vk_id в зависимости от канала.
        Возвращает SendResult с флагом success и текстом ошибки при неудаче.
        """
        ...

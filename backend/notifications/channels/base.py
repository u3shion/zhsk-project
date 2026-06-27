from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendResult:
    success: bool
    error: str | None = None


class BaseChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, message: str) -> SendResult:
        ...

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SendRequest(BaseModel):
    user_id: int
    subject: str
    message: str


class BroadcastRequest(BaseModel):
    subject: str
    message: str


class NotificationLogResponse(BaseModel):
    id: int
    user_id: int
    channel: str
    recipient: str
    subject: str
    message: str
    status: str
    error: Optional[str]
    trigger: str
    sent_by_admin_id: Optional[int]
    sent_at: datetime

    model_config = {"from_attributes": True}


class NotificationHistoryResponse(BaseModel):
    logs: list[NotificationLogResponse]
    total: int

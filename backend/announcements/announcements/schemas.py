from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class AnnouncementType(str, Enum):
    news = "news"
    ad = "ad"


class AnnouncementSubtype(str, Enum):
    service = "service"
    noise = "noise"


class AnnouncementCreate(BaseModel):
    type: AnnouncementType
    subtype: Optional[AnnouncementSubtype] = None
    title: str
    content: str

    @field_validator("subtype")
    @classmethod
    def subtype_required_for_ad(cls, v, info):
        if info.data.get("type") == AnnouncementType.ad and v is None:
            raise ValueError("subtype is required for ads (service or noise)")
        return v


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    subtype: Optional[AnnouncementSubtype] = None


class AnnouncementResponse(BaseModel):
    id: int
    author_id: int
    author_role: str
    type: str
    subtype: Optional[str]
    title: str
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementsListResponse(BaseModel):
    items: list[AnnouncementResponse]
    total: int
    page: int
    page_size: int

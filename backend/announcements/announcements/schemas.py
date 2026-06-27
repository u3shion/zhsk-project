from datetime import datetime

from pydantic import BaseModel, field_validator


class AnnouncementResponse(BaseModel):
    id: int
    author_id: int
    author_role: str
    type: str
    title: str
    content: str
    photo_urls: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("photo_urls", mode="before")
    @classmethod
    def parse_photo_urls(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return []
        return []


class AnnouncementsListResponse(BaseModel):
    items: list[AnnouncementResponse]
    total: int
    page: int
    page_size: int

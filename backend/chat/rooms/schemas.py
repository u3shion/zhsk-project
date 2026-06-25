from pydantic import BaseModel
from datetime import datetime


class RoomCreate(BaseModel):
    name: str
    description: str | None = None


class RoomInvite(BaseModel):
    user_id: int


class RoomResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_by: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomMemberResponse(BaseModel):
    user_id: int
    joined_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    content: str
    created_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}

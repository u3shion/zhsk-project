from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from core.config import SERVICE_KEY
from core.database import get_db
from models.user import User


router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    apartment: Optional[str] = None
    notification_channel: Optional[Literal["email", "sms", "vk"]] = None
    phone: Optional[str] = None
    vk_id: Optional[str] = None


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "apartment": user.apartment,
        "notification_channel": user.notification_channel,
        "phone": user.phone,
        "vk_id": user.vk_id,
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _user_to_dict(current_user)


@router.put("/me")
def update_me(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    return {"message": "updated"}

def _check_service_key(x_service_key: Optional[str] = Header(None)):
    if x_service_key != SERVICE_KEY:
        raise HTTPException(status_code=403, detail="Invalid service key")


@router.get("/internal/contact/{user_id}", include_in_schema=False)
def get_user_contact(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(_check_service_key),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_dict(user)


@router.get("/internal/contacts/residents", include_in_schema=False)
def get_all_residents(
    db: Session = Depends(get_db),
    _: None = Depends(_check_service_key),
):
    residents = db.query(User).filter(User.role == "resident").all()
    return [_user_to_dict(u) for u in residents]

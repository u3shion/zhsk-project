from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
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
    email: Optional[str] = None


class RoleUpgrade(BaseModel):
    admin_secret: str


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
        "avatar_url": getattr(user, 'avatar_url', None),
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
    update_data = data.model_dump(exclude_none=True)

    if "email" in update_data:
        new_email = update_data["email"]
        existing = db.query(User).filter(
            User.email == new_email,
            User.id != current_user.id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = new_email

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    return {"message": "updated"}


@router.post("/me/upgrade-role")
def upgrade_role(
    data: RoleUpgrade,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from core.config import ADMIN_SECRET

    if data.admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    if current_user.role == "admin":
        return {"message": "already admin", "role": "admin"}

    current_user.role = "admin"
    db.add(current_user)
    db.commit()
    return {"message": "Права повышены", "role": "admin"}

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


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from storage import upload_photo

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    contents = await file.read()
    avatar_url = upload_photo(contents, file.filename or "avatar.jpg", file.content_type)

    current_user.avatar_url = avatar_url
    db.add(current_user)
    db.commit()
    return {"avatar_url": avatar_url}

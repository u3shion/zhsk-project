from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from models.user import User
from auth.dependencies import get_current_user


router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    full_name: str
    apartment: str


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "apartment": current_user.apartment,
    }


@router.put("/me")
def update_me(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.full_name = data.full_name
    current_user.apartment = data.apartment

    db.add(current_user)
    db.commit()
    return {"message": "updated"}
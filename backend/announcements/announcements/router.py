from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth.dependencies import TokenData, get_current_user
from core.database import get_db
from models.announcement import Announcement
from announcements.schemas import (
    AnnouncementResponse,
    AnnouncementsListResponse,
)
from storage import delete_photo, upload_photo


ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024


router = APIRouter(prefix="/announcements", tags=["announcements"])


def _validate_photo_type(photo: UploadFile | None) -> None:
    if photo is None:
        return
    if photo.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {photo.content_type}. Allowed: JPEG, PNG, WebP.",
        )


@router.post("/", response_model=AnnouncementResponse, status_code=201)
async def create_announcement(
    type: str = Form(...),
    subtype: Optional[str] = Form(None),
    title: str = Form(...),
    content: str = Form(...),
    photo: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.role == "resident" and type != "news":
        raise HTTPException(status_code=403, detail="Residents can only create ads")

    if type == "ad" and subtype not in ("service", "noise"):
        raise HTTPException(
            status_code=400,
            detail="subtype is required for ads (service or noise)",
        )

    _validate_photo_type(photo)

    photo_url: Optional[str] = None
    if photo is not None:
        content_bytes = await photo.read()
        if len(content_bytes) > MAX_PHOTO_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(content_bytes)} bytes. Maximum: {MAX_PHOTO_SIZE_BYTES} bytes.",
            )
        photo_url = upload_photo(
            content_bytes,
            photo.filename or "photo.jpg",
            photo.content_type or "image/jpeg",
        )

    announcement = Announcement(
        author_id=current_user.user_id,
        author_role=current_user.role,
        type=type,
        subtype=subtype,
        title=title,
        content=content,
        photo_url=photo_url,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.get("/", response_model=AnnouncementsListResponse)
def list_announcements(
    type: Optional[str] = None,
    subtype: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(Announcement).filter(Announcement.is_active == True)

    if type:
        query = query.filter(Announcement.type == type)
    if subtype:
        query = query.filter(Announcement.subtype == subtype)

    total = query.count()
    items = (
        query.order_by(Announcement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.is_active == True,
    ).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    title: Optional[str] = Form(default=None),
    content: Optional[str] = Form(default=None),
    subtype: Optional[str] = Form(default=None),
    photo: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.is_active == True,
    ).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if announcement.author_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to edit this announcement")

    _validate_photo_type(photo)

    if title is not None:
        announcement.title = title
    if content is not None:
        announcement.content = content
    if subtype is not None:
        announcement.subtype = subtype

    if photo is not None:
        content_bytes = await photo.read()
        if len(content_bytes) > MAX_PHOTO_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(content_bytes)} bytes. Maximum: {MAX_PHOTO_SIZE_BYTES} bytes.",
            )
        if announcement.photo_url:
            delete_photo(announcement.photo_url)
        announcement.photo_url = upload_photo(
            content_bytes,
            photo.filename or "photo.jpg",
            photo.content_type or "image/jpeg",
        )

    db.commit()
    db.refresh(announcement)
    return announcement


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.is_active == True,
    ).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if announcement.author_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this announcement")

    if announcement.photo_url:
        delete_photo(announcement.photo_url)

    announcement.is_active = False
    db.commit()
    return {"message": "Announcement deleted", "id": announcement_id}

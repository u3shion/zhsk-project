from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
import json

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


async def _upload_single_photo(photo: UploadFile) -> str:
    content_bytes = await photo.read()
    if len(content_bytes) > MAX_PHOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content_bytes)} bytes. Maximum: {MAX_PHOTO_SIZE_BYTES} bytes.",
        )
    return upload_photo(
        content_bytes,
        photo.filename or "photo.jpg",
        photo.content_type or "image/jpeg",
    )


@router.post("/", response_model=AnnouncementResponse, status_code=201)
async def create_announcement(
    type: str = Form(...),
    subtype: Optional[str] = Form(None),
    title: str = Form(...),
    content: str = Form(...),
    photos: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.role == "resident" and type == "news":
        raise HTTPException(status_code=403, detail="Only admins can publish news")

    for photo in photos:
        _validate_photo_type(photo)

    photo_urls: list[str] = []
    for photo in photos:
        try:
            photo_urls.append(await _upload_single_photo(photo))
        except HTTPException:
            raise
        except Exception as e:
            import logging
            logging.warning(f"Failed to upload photo: {e}")

    announcement = Announcement(
        author_id=current_user.user_id,
        author_role=current_user.role,
        type=type,
        subtype=subtype,
        title=title,
        content=content,
        photo_urls=json.dumps(photo_urls) if photo_urls else None,
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
        old_urls: list[str] = []
        if announcement.photo_urls:
            try:
                old_urls = json.loads(announcement.photo_urls)
            except Exception:
                pass
        for url in old_urls:
            delete_photo(url)
        new_url = upload_photo(
            content_bytes,
            photo.filename or "photo.jpg",
            photo.content_type or "image/jpeg",
        )
        announcement.photo_urls = json.dumps([new_url])

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

    if announcement.photo_urls:
        try:
            urls: list[str] = json.loads(announcement.photo_urls)
            for url in urls:
                delete_photo(url)
        except Exception:
            pass

    announcement.is_active = False
    db.commit()
    return {"message": "Announcement deleted", "id": announcement_id}

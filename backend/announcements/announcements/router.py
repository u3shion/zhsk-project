from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import TokenData, get_current_user
from core.database import get_db
from models.announcement import Announcement
from announcements.schemas import (
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementsListResponse,
    AnnouncementType,
    AnnouncementUpdate,
)


router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.post("/", response_model=AnnouncementResponse, status_code=201)
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.role == "resident" and data.type != AnnouncementType.ad:
        raise HTTPException(
            status_code=403,
            detail="Residents can only create ads",
        )

    announcement = Announcement(
        author_id=current_user.user_id,
        author_role=current_user.role,
        type=data.type,
        subtype=data.subtype,
        title=data.title,
        content=data.content,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.get("/", response_model=AnnouncementsListResponse)
def list_announcements(
    type: Optional[str] = None,
    subtype: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
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

    if data.title is not None:
        announcement.title = data.title
    if data.content is not None:
        announcement.content = data.content
    if data.subtype is not None:
        announcement.subtype = data.subtype

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

    announcement.is_active = False
    db.commit()
    return {"message": "Announcement deleted", "id": announcement_id}

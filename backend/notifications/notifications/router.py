from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import TokenData, require_admin
from channels.dispatcher import dispatch
from core.config import SERVICE_KEY, USERS_SERVICE_URL
from core.database import get_db
from models.notification_log import NotificationLog
from notifications.schemas import (
    BroadcastRequest,
    NotificationHistoryResponse,
    ResidentsResponse,
    SendRequest,
)


router = APIRouter(prefix="/notifications", tags=["notifications"])

SERVICE_HEADERS = {"x-service-key": SERVICE_KEY}


def _get_user_contact(user_id: int) -> dict:
    resp = httpx.get(
        f"{USERS_SERVICE_URL}/users/internal/contact/{user_id}",
        headers=SERVICE_HEADERS,
        timeout=5.0,
    )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    resp.raise_for_status()
    return resp.json()


def _get_all_residents() -> list[dict]:
    resp = httpx.get(
        f"{USERS_SERVICE_URL}/users/internal/contacts/residents",
        headers=SERVICE_HEADERS,
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()


@router.get("/residents", response_model=ResidentsResponse)
def get_residents(
    current_user: TokenData = Depends(require_admin),
):
    residents = _get_all_residents()
    return {"residents": residents}


def _send_and_log(
    db: Session,
    user: dict,
    subject: str,
    message: str,
    trigger: str,
    sent_by_admin_id: Optional[int] = None,
) -> NotificationLog:
    channel = user.get("notification_channel", "email")
    recipient_map = {"email": user.get("email"), "sms": user.get("phone"), "vk": user.get("vk_id")}
    recipient = recipient_map.get(channel)

    if not recipient:
        status, error = "failed", f"No {channel} contact set for user {user['id']}"
        result_obj = None
    else:
        result_obj = dispatch(channel, recipient, subject, message)
        status = "sent" if result_obj.success else "failed"
        error = result_obj.error if result_obj else None

    log = NotificationLog(
        user_id=user["id"],
        channel=channel,
        recipient=recipient or "",
        subject=subject,
        message=message,
        status=status,
        error=error,
        trigger=trigger,
        sent_by_admin_id=sent_by_admin_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.post("/send")
def send_to_user(
    data: SendRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    user = _get_user_contact(data.user_id)
    log = _send_and_log(
        db, user, data.subject, data.message,
        trigger="manual", sent_by_admin_id=current_user.user_id,
    )
    return {
        "status": log.status,
        "channel": log.channel,
        "recipient": log.recipient,
        "error": log.error,
    }


@router.post("/broadcast")
def broadcast(
    data: BroadcastRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    residents = _get_all_residents()
    if not residents:
        return {"sent": 0, "failed": 0, "results": []}

    results = []
    for user in residents:
        log = _send_and_log(
            db, user, data.subject, data.message,
            trigger="manual", sent_by_admin_id=current_user.user_id,
        )
        results.append({"user_id": user["id"], "status": log.status, "channel": log.channel})

    sent = sum(1 for r in results if r["status"] == "sent")
    return {"sent": sent, "failed": len(results) - sent, "results": results}


@router.get("/history", response_model=NotificationHistoryResponse)
def get_history(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    trigger: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    query = db.query(NotificationLog)
    if user_id:
        query = query.filter(NotificationLog.user_id == user_id)
    if status:
        query = query.filter(NotificationLog.status == status)
    if trigger:
        query = query.filter(NotificationLog.trigger == trigger)

    total = query.count()
    logs = (
        query.order_by(NotificationLog.sent_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"logs": logs, "total": total}

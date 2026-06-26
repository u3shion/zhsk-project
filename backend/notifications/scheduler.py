import logging

import httpx
from sqlalchemy.orm import Session

from channels.dispatcher import dispatch
from core.config import METERS_SERVICE_URL, SERVICE_KEY, USERS_SERVICE_URL
from core.database import SessionLocal
from models.notification_log import NotificationLog


logger = logging.getLogger(__name__)

SERVICE_HEADERS = {"x-service-key": SERVICE_KEY}

VERIFICATION_SUBJECT = "Приближается дата поверки счётчика воды"
VERIFICATION_MESSAGE_TEMPLATE = (
    "Уважаемый жилец кв. {apartment}!\n\n"
    "Счётчик {meter_type} воды (серийный номер {serial_number}) "
    "требует поверки {next_verification_at} (осталось {days_left} дн.).\n\n"
    "Пожалуйста, запишитесь на поверку заблаговременно.\n\n"
    "С уважением, управление ЖСК"
)


def check_meter_verifications():
    logger.info("Scheduler: checking meter verifications...")
    db: Session = SessionLocal()

    try:
        resp = httpx.get(
            f"{METERS_SERVICE_URL}/water-meters/expiring-soon",
            headers=SERVICE_HEADERS,
            params={"days": 7},
            timeout=10.0,
        )
        resp.raise_for_status()
        expiring = resp.json()
    except Exception as e:
        logger.error(f"Scheduler: failed to fetch expiring meters: {e}")
        db.close()
        return

    for meter in expiring:
        user_id = meter["user_id"]
        try:
            user_resp = httpx.get(
                f"{USERS_SERVICE_URL}/users/internal/contact/{user_id}",
                headers=SERVICE_HEADERS,
                timeout=5.0,
            )
            user_resp.raise_for_status()
            user = user_resp.json()
        except Exception as e:
            logger.error(f"Scheduler: failed to fetch user {user_id}: {e}")
            continue

        channel = user.get("notification_channel", "email")
        recipient_map = {
            "email": user.get("email"),
            "sms": user.get("phone"),
            "vk": user.get("vk_id"),
        }
        recipient = recipient_map.get(channel)
        message = VERIFICATION_MESSAGE_TEMPLATE.format(**meter)

        if not recipient:
            status, error = "failed", f"No {channel} contact set"
        else:
            result = dispatch(channel, recipient, VERIFICATION_SUBJECT, message)
            status = "sent" if result.success else "failed"
            error = result.error

        log = NotificationLog(
            user_id=user_id,
            channel=channel,
            recipient=recipient or "",
            subject=VERIFICATION_SUBJECT,
            message=message,
            status=status,
            error=error,
            trigger="scheduler",
        )
        db.add(log)
        logger.info(f"Scheduler: user {user_id} — {status} via {channel}")

    db.commit()
    db.close()
    logger.info("Scheduler: done.")

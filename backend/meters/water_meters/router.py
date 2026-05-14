from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import TokenData, get_current_user, require_admin
from core.config import SERVICE_KEY
from core.database import get_db
from models.water_meter import WaterMeter
from water_meters.schemas import WaterMeterCreate, WaterMeterResponse, WaterMeterUpdate


router = APIRouter(prefix="/water-meters", tags=["water-meters"])

VERIFICATION_WARNING_DAYS = 60


def _check_service_key(x_service_key: Optional[str] = Header(None)):
    if x_service_key != SERVICE_KEY:
        raise HTTPException(status_code=403, detail="Invalid service key")


@router.post("/", response_model=WaterMeterResponse, status_code=201)
def register_meter(
    data: WaterMeterCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    meter = WaterMeter(user_id=current_user.user_id, **data.model_dump())
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@router.get("/me", response_model=list[WaterMeterResponse])
def get_my_meters(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    return (
        db.query(WaterMeter)
        .filter(WaterMeter.user_id == current_user.user_id, WaterMeter.is_active == True)
        .order_by(WaterMeter.next_verification_at)
        .all()
    )


@router.put("/{meter_id}", response_model=WaterMeterResponse)
def update_verification(
    meter_id: int,
    data: WaterMeterUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    meter = db.query(WaterMeter).filter(
        WaterMeter.id == meter_id,
        WaterMeter.user_id == current_user.user_id,
    ).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    meter.last_verified_at = data.last_verified_at
    meter.next_verification_at = data.next_verification_at
    db.commit()
    db.refresh(meter)
    return meter


@router.delete("/{meter_id}")
def deactivate_meter(
    meter_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    meter = db.query(WaterMeter).filter(
        WaterMeter.id == meter_id,
        WaterMeter.user_id == current_user.user_id,
    ).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    meter.is_active = False
    db.commit()
    return {"message": "Meter deactivated", "id": meter_id}


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    meters = (
        db.query(WaterMeter)
        .filter(WaterMeter.is_active == True)
        .order_by(WaterMeter.next_verification_at)
        .all()
    )
    today = date.today()
    warning_threshold = today + timedelta(days=VERIFICATION_WARNING_DAYS)

    result = []
    for m in meters:
        days_left = (m.next_verification_at - today).days
        result.append({
            "id": m.id,
            "apartment": m.apartment,
            "meter_type": m.meter_type,
            "serial_number": m.serial_number,
            "next_verification_at": m.next_verification_at.isoformat(),
            "days_until_verification": days_left,
            "needs_attention": days_left <= VERIFICATION_WARNING_DAYS,
            "overdue": days_left < 0,
        })

    overdue = [r for r in result if r["overdue"]]
    needs_attention = [r for r in result if r["needs_attention"] and not r["overdue"]]

    return {
        "total": len(result),
        "overdue_count": len(overdue),
        "needs_attention_count": len(needs_attention),
        "meters": result,
    }


@router.get("/expiring-soon", include_in_schema=False)
def get_expiring_soon(
    days: int = Query(60, ge=1, le=365),
    db: Session = Depends(get_db),
    _: None = Depends(_check_service_key),
):
    """Внутренний эндпоинт для сервиса уведомлений."""
    today = date.today()
    deadline = today + timedelta(days=days)

    meters = (
        db.query(WaterMeter)
        .filter(
            WaterMeter.is_active == True,
            WaterMeter.next_verification_at <= deadline,
        )
        .order_by(WaterMeter.next_verification_at)
        .all()
    )

    return [
        {
            "user_id": m.user_id,
            "apartment": m.apartment,
            "meter_type": m.meter_type,
            "serial_number": m.serial_number,
            "next_verification_at": m.next_verification_at.isoformat(),
            "days_left": (m.next_verification_at - today).days,
        }
        for m in meters
    ]

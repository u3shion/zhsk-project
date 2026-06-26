from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import TokenData, get_current_user, require_admin
from core.database import get_db
from models.reading import MeterReading
from readings.schemas import MeterType, ReadingCreate, ReadingResponse, ReadingsListResponse
from services.external_client import external_client


router = APIRouter(prefix="/readings", tags=["readings"])

ALL_METER_TYPES = [t.value for t in MeterType]


@router.post("/", response_model=ReadingResponse, status_code=201)
async def submit_reading(
    data: ReadingCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    existing = db.query(MeterReading).filter(
        MeterReading.user_id == current_user.user_id,
        MeterReading.period == data.period,
        MeterReading.meter_type == data.meter_type,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Reading already submitted for this period and meter type",
        )

    reading = MeterReading(
        user_id=current_user.user_id,
        apartment=data.apartment,
        period=data.period,
        meter_type=data.meter_type,
        value=data.value,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    try:
        await external_client.submit_reading(
            meter_type=data.meter_type,
            value=data.value,
            period=data.period,
            apartment=data.apartment,
            user_id=current_user.user_id,
        )
    except Exception:
        pass

    return reading


@router.get("/me", response_model=ReadingsListResponse)
def get_my_readings(
    period: Optional[str] = None,
    meter_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(MeterReading).filter(
        MeterReading.user_id == current_user.user_id,
    )
    if period:
        query = query.filter(MeterReading.period == period)
    if meter_type:
        query = query.filter(MeterReading.meter_type == meter_type)
    items = query.order_by(MeterReading.period.desc(), MeterReading.submitted_at.desc()).all()
    return {"readings": items, "total": len(items)}


@router.get("/summary")
def get_summary(
    period: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    readings = db.query(MeterReading).filter(MeterReading.period == period).all()

    by_apartment: dict[str, list[str]] = {}
    for r in readings:
        by_apartment.setdefault(r.apartment, []).append(r.meter_type)

    apartments = []
    for apt in sorted(by_apartment.keys()):
        submitted = by_apartment[apt]
        apartments.append({
            "apartment": apt,
            "submitted": submitted,
            "missing": [t for t in ALL_METER_TYPES if t not in submitted],
            "complete": len(submitted) == len(ALL_METER_TYPES),
        })

    total = len(apartments)
    complete = sum(1 for a in apartments if a["complete"])

    return {
        "period": period,
        "total_apartments": total,
        "complete": complete,
        "incomplete": total - complete,
        "apartments": apartments,
    }

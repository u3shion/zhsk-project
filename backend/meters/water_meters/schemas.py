from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class WaterMeterType(str, Enum):
    cold = "cold"
    hot = "hot"


class WaterMeterCreate(BaseModel):
    apartment: str
    meter_type: WaterMeterType
    serial_number: str
    installed_at: date
    last_verified_at: Optional[date] = None
    next_verification_at: date

    @field_validator("next_verification_at")
    @classmethod
    def verify_date_after_install(cls, v: date, info) -> date:
        installed = info.data.get("installed_at")
        if installed and v <= installed:
            raise ValueError("next_verification_at must be after installed_at")
        return v


class WaterMeterUpdate(BaseModel):
    last_verified_at: date
    next_verification_at: date

    @field_validator("next_verification_at")
    @classmethod
    def verify_date_after_last(cls, v: date, info) -> date:
        last = info.data.get("last_verified_at")
        if last and v <= last:
            raise ValueError("next_verification_at must be after last_verified_at")
        return v


class WaterMeterVerificationResponse(BaseModel):
    id: int
    apartment: str
    meter_type: str
    serial_number: str
    last_verified_at: Optional[date]
    next_verification_at: date
    is_active: bool

    model_config = {"from_attributes": True}


class WaterMeterVerificationListResponse(BaseModel):
    verifications: list[WaterMeterVerificationResponse]
    total: int


class WaterMeterResponse(BaseModel):
    id: int
    user_id: int
    apartment: str
    meter_type: str
    serial_number: str
    installed_at: date
    last_verified_at: Optional[date]
    next_verification_at: date
    is_active: bool

    model_config = {"from_attributes": True}

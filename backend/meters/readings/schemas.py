import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator


class MeterType(str, Enum):
    electricity = "electricity"
    cold_water = "cold_water"
    hot_water = "hot_water"
    heating = "heating"
    gas = "gas"


class ReadingCreate(BaseModel):
    apartment: str
    period: str
    meter_type: MeterType
    value: float

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("period must be in YYYY-MM format")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        if v < 0:
            raise ValueError("value must be non-negative")
        return v


class ReadingResponse(BaseModel):
    id: int
    user_id: int
    apartment: str
    period: str
    meter_type: str
    value: float
    submitted_at: datetime

    model_config = {"from_attributes": True}


class ReadingsListResponse(BaseModel):
    readings: list[ReadingResponse]
    total: int


class ReadingsAllResponse(BaseModel):
    readings: list[ReadingResponse]
    total: int

"""
Mock-сервис, имитирующий внешнюю службу сбора показаний.
В реальности здесь будет вызов реального API (например, ГИС ЖКХ, поставщика услуг).
"""
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock External Meter Service")


class MeterReadingSubmission(BaseModel):
    """Формат данных, которые принимает внешняя служба."""
    provider_id: str
    provider_name: str
    meter_type: Literal["electricity", "cold_water", "hot_water", "heating", "gas"]
    meter_number: str
    value: float
    period: str  # YYYY-MM
    submitted_at: str
    apartment: str
    resident_id: str


class ExternalSubmissionResponse(BaseModel):
    status: str
    external_id: str
    received_at: str
    message: str


# In-memory хранилище принятых показаний
_submissions: list[dict] = []


@app.post("/submit", response_model=ExternalSubmissionResponse)
async def submit_reading(data: MeterReadingSubmission):
    """Принять показание и сохранить в моковом хранилище."""
    logger.info(
        "[MOCK EXTERNAL] Received reading: provider=%s meter=%s value=%.2f period=%s apartment=%s",
        data.provider_id,
        data.meter_number,
        data.value,
        data.period,
        data.apartment,
    )

    received_at = datetime.utcnow().isoformat() + "Z"
    external_id = f"ext-{len(_submissions) + 1:06d}"

    record = {
        "external_id": external_id,
        "received_at": received_at,
        "data": data.model_dump(),
        "status": "accepted",
    }
    _submissions.append(record)

    return ExternalSubmissionResponse(
        status="accepted",
        external_id=external_id,
        received_at=received_at,
        message="Показание успешно принято внешней службой",
    )


@app.get("/submissions")
async def list_submissions():
    """Список всех принятых показаний (для отладки/проверки)."""
    return {"total": len(_submissions), "submissions": _submissions}


@app.get("/health")
async def health():
    return {"status": "ok"}

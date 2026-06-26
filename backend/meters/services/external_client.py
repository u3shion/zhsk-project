"""
HTTP-клиент для отправки показаний во внешнюю службу сбора показаний.
"""
import logging
from datetime import datetime
from typing import Literal

import httpx
from pydantic import BaseModel

from core.config import EXTERNAL_SERVICE_URL, EXTERNAL_SERVICE_PROVIDER_ID, EXTERNAL_SERVICE_PROVIDER_NAME

logger = logging.getLogger(__name__)


class ExternalSubmissionResponse(BaseModel):
    status: str
    external_id: str
    received_at: str
    message: str


class ExternalServiceClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or EXTERNAL_SERVICE_URL or "").rstrip("/")
        self.timeout = timeout

    def _build_payload(
        self,
        meter_type: Literal["electricity", "cold_water", "hot_water", "heating", "gas"],
        value: float,
        period: str,
        apartment: str,
        user_id: int,
    ) -> dict:
        return {
            "provider_id": EXTERNAL_SERVICE_PROVIDER_ID,
            "provider_name": EXTERNAL_SERVICE_PROVIDER_NAME,
            "meter_type": meter_type,
            "meter_number": f"APT-{apartment}-{meter_type}",
            "value": value,
            "period": period,
            "submitted_at": datetime.utcnow().isoformat() + "Z",
            "apartment": apartment,
            "resident_id": str(user_id),
        }

    async def submit_reading(
        self,
        meter_type: Literal["electricity", "cold_water", "hot_water", "heating", "gas"],
        value: float,
        period: str,
        apartment: str,
        user_id: int,
    ) -> ExternalSubmissionResponse:
        if not self.base_url:
            logger.warning(
                "[ExternalServiceClient] EXTERNAL_SERVICE_URL not configured — skipping forwarding"
            )
            return ExternalSubmissionResponse(
                status="skipped",
                external_id="",
                received_at=datetime.utcnow().isoformat() + "Z",
                message="Внешний сервис не настроен (forwarding пропущен)",
            )

        payload = self._build_payload(meter_type, value, period, apartment, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/submit",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                logger.info(
                    "[ExternalServiceClient] Forwarded reading: meter=%s value=%.2f → external_id=%s",
                    meter_type,
                    value,
                    data.get("external_id", "?"),
                )
                return ExternalSubmissionResponse(**data)
        except httpx.HTTPStatusError as e:
            logger.error(
                "[ExternalServiceClient] External service returned %d: %s",
                e.response.status_code,
                e.response.text,
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "[ExternalServiceClient] Failed to reach external service at %s: %s",
                self.base_url,
                e,
            )
            raise


# Singleton-экземпляр для reuse между запросами
external_client = ExternalServiceClient()

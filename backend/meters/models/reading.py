from sqlalchemy import Column, Integer, String, Float, DateTime, func, UniqueConstraint

from core.database import Base


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    apartment = Column(String, nullable=False, index=True)
    period = Column(String, nullable=False)
    meter_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "period", "meter_type", name="uq_reading_user_period_type"),
    )

from sqlalchemy import Column, Integer, String, Date, DateTime, func, UniqueConstraint

from core.database import Base


class MeterVerification(Base):
    __tablename__ = "meter_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    apartment = Column(String, nullable=False, index=True)
    meter_type = Column(String, nullable=False)
    verification_date = Column(Date, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "apartment", "meter_type", name="uq_verification_user_apt_type"),
    )

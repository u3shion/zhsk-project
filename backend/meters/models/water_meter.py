from sqlalchemy import Column, Integer, String, Date, Boolean

from core.database import Base


class WaterMeter(Base):
    __tablename__ = "water_meters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    apartment = Column(String, nullable=False, index=True)
    meter_type = Column(String, nullable=False)
    serial_number = Column(String, nullable=False)
    installed_at = Column(Date, nullable=False)
    last_verified_at = Column(Date, nullable=True)
    next_verification_at = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

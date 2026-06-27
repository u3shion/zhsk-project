from sqlalchemy import Column, DateTime, Integer, String, func

from core.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    channel = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error = Column(String, nullable=True)
    trigger = Column(String, nullable=False)
    sent_by_admin_id = Column(Integer, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

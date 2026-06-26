from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, nullable=False, index=True)
    author_role = Column(String, nullable=False)
    type = Column(String, nullable=False, index=True)   # news | ad
    subtype = Column(String, nullable=True)             # service | noise  (только для ad)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    photo_urls = Column(Text, nullable=True)            # JSON array of URLs в MinIO
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

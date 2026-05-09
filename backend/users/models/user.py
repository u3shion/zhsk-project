from sqlalchemy import Column, Integer, String
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    role = Column(String, default="resident")
    full_name = Column(String, nullable=True)
    apartment = Column(String, nullable=True)
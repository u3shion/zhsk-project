from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Test(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True)
    name = Column(String)
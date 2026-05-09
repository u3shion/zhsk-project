from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    admin_secret: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

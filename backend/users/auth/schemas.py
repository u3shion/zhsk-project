import re
from typing import Optional
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    email: str
    password: str
    admin_secret: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not v or ' ' in v or not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

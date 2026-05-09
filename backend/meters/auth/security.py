from jose import jwt

from core.config import SECRET_KEY

ALGORITHM = "HS256"


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

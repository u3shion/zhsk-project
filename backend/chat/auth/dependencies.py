from fastapi import Depends, HTTPException, status, Query
from jose import JWTError

from auth.security import decode_token


class TokenData:
    def __init__(self, user_id: int, role: str):
        self.user_id = user_id
        self.role = role


def _parse_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return TokenData(user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Query(..., alias="token")) -> TokenData:
    """For WebSocket connections — token passed as query param."""
    return _parse_token(token)


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user

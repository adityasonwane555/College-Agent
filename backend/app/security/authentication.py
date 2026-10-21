import secrets
from typing import Set
from fastapi import HTTPException, Header, status
from ..config import settings


# In-memory store of active admin session tokens
ACTIVE_ADMIN_TOKENS: Set[str] = set()


def authenticate_admin(username: str, password: str) -> str:
    """Validates admin credentials and issues a secure session token."""
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        token = secrets.token_hex(24)
        ACTIVE_ADMIN_TOKENS.add(token)
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid administrator credentials."
    )


def verify_admin_token(authorization: str = Header(None)) -> bool:
    """FastAPI dependency to protect admin endpoints."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required."
        )
    token = authorization.replace("Bearer ", "").strip()
    if token not in ACTIVE_ADMIN_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired administrative token."
        )
    return True

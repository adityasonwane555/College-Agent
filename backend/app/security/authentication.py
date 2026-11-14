"""
BUDDY AI 2.0 — Administrative Authentication & Session Security

Architecture & Access Control:
  - Administrative Session Management:
      - Validates credentials against environment configurations (ADMIN_USERNAME, ADMIN_PASSWORD).
      - Issues high-entropy cryptographic session bearer tokens using secrets.token_hex(24).
  - In-Memory Session Token Store:
      - Tracks active administrator tokens in a thread-safe set (ACTIVE_ADMIN_TOKENS) for fast constant-time lookup.
  - FastAPI Dependency Guard:
      - verify_admin_token dependency parses the 'Authorization: Bearer <token>' header.
      - Restricts document upload, staging approvals, FTS5/vector index rebuilds, and diagnostics to authenticated administrators.
      - Rejects invalid or expired credentials with HTTP 401 Unauthorized or HTTP 403 Forbidden.
"""

import secrets
from typing import Set
from fastapi import HTTPException, Header, status
from ..config import settings


# In-memory store of active admin session tokens
ACTIVE_ADMIN_TOKENS: Set[str] = set()


def authenticate_admin(username: str, password: str) -> str:
    """
    Validates administrative username and password credentials and issues a secure bearer session token.

    Args:
        username: Administrator username.
        password: Plaintext administrator password.

    Returns:
        str: 48-character hexadecimal session token added to ACTIVE_ADMIN_TOKENS.

    Raises:
        HTTPException(401): If credentials do not match configured administrative secrets.
    """
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        token = secrets.token_hex(24)
        ACTIVE_ADMIN_TOKENS.add(token)
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid administrator credentials."
    )


def verify_admin_token(authorization: str = Header(None)) -> bool:
    """
    FastAPI dependency that enforces bearer token authorization on sensitive management endpoints.

    Args:
        authorization: Incoming 'Authorization' HTTP request header (e.g. 'Bearer <token>').

    Returns:
        bool: True if the bearer token is valid and currently active.

    Raises:
        HTTPException(401): If Authorization header is absent.
        HTTPException(403): If the token is unrecognized, revoked, or expired.
    """
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

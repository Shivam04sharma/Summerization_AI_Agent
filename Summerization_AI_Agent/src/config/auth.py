"""JWT auth dependency — controlled by AUTH_ENABLED in .env."""

from __future__ import annotations

from config import settings
from fastapi import HTTPException, Request, status


async def verify_token(request: Request) -> None:
    if not settings.auth_enabled:
        return

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
        )

    try:
        import jwt

        jwt.decode(
            auth.split(" ", 1)[1],
            settings.onified_jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

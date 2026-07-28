"""JWT and password hashing utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a password against stored hash.

    Supports bcrypt (new registrations) and legacy SHA-256 hex digests
    from the DML seed script (faker.sha256), which cannot be reversed —
    those accounts must re-register or have their hash reset.
    """
    if hashed.startswith("$2"):  # bcrypt
        return pwd_context.verify(plain, hashed)
    # Seed data used raw SHA-256 hex; reject interactive login for those.
    return False


def create_access_token(
    subject: str | int,
    *,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
) -> tuple[str, int]:
    settings = get_settings()
    expire_delta = expires_minutes or settings.jwt_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_delta)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expire_delta * 60


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

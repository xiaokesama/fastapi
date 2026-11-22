from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plain-text password with Argon2."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely compare a plain-text password with its stored hash."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a signed JWT whose subject is the user id."""
    now = datetime.now(UTC)
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
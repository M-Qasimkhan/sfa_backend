import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_session_key() -> str:
    return secrets.token_urlsafe(32)


def get_session_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

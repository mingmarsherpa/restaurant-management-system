from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY
from ..models.user import User


password_hash = PasswordHash.recommended()


def _jwt_secret_key() -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not set")
    return JWT_SECRET_KEY


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "exp": expires_at,
    }
    return jwt.encode(payload, _jwt_secret_key(), algorithm=JWT_ALGORITHM)

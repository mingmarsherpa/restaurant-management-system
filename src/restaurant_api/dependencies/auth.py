from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import JWT_ALGORITHM, JWT_SECRET_KEY
from ..database import get_db
from ..models.user import Role, User


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        if not JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not set")
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise unauthorized
        user_id_int = int(user_id)
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized

    user = await session.scalar(select(User).where(User.id == user_id_int))
    if user is None or not user.is_active:
        raise unauthorized
    return user


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role is not Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


async def require_staff(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role not in {Role.ADMIN, Role.KITCHEN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return user

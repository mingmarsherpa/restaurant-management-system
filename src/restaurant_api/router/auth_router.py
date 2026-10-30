from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.user import LoginRequest, Token, UserRead
from ..services.auth import create_access_token, verify_password


router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    user = await session.scalar(
        select(User).where(
            or_(
                User.username == payload.identifier,
                User.email == payload.identifier,
            )
        )
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(
        access_token=create_access_token(user),
        role=user.role,
    )


@router.get("/me", response_model=UserRead)
async def current_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user

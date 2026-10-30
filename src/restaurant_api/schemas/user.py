# schemas/auth.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from ..models.user import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: Role
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1)
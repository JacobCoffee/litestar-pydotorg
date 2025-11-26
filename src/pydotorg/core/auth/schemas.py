"""Authentication DTOs and schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(default="", max_length=150)
    last_name: str = Field(default="", max_length=150)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    email_verified: bool
    date_joined: datetime
    last_login: datetime | None
    has_membership: bool
    oauth_provider: str | None = None
    oauth_id: str | None = None

    class Config:
        from_attributes = True


class SendVerificationRequest(BaseModel):
    email: EmailStr


class VerifyEmailResponse(BaseModel):
    message: str


class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)

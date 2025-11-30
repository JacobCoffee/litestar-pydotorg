"""Authentication DTOs and schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "guido_van_rossum",
                "password": "SecurePass123!",
            }
        }
    )

    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "guido_van_rossum",
                "email": "guido@python.org",
                "password": "SecurePass123!",
                "first_name": "Guido",
                "last_name": "van Rossum",
            }
        }
    )

    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(default="", max_length=150)
    last_name: str = Field(default="", max_length=150)


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MzI4NzY4MDB9.x5Z9KqN1MpY4g8VkWjE2_rP3sB7cD9fH2mO6tL8uN0Q",
                "refresh_token": "rt_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }
    )

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "rt_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            }
        }
    )

    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "guido_van_rossum",
                "email": "guido@python.org",
                "first_name": "Guido",
                "last_name": "van Rossum",
                "is_active": True,
                "is_staff": True,
                "is_superuser": False,
                "email_verified": True,
                "date_joined": "2024-01-15T10:30:00Z",
                "last_login": "2024-11-29T14:22:00Z",
                "has_membership": True,
                "oauth_provider": None,
                "oauth_id": None,
            }
        },
    )

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


class SendVerificationRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "user@example.com"}})

    email: EmailStr


class VerifyEmailResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"message": "Email verified successfully"}})

    message: str


class OAuthCallbackRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "4/0AX4XfWj...",
                "state": "abc123xyz789",
            }
        }
    )

    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "user@example.com"}})

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecureP@ss123!",
            }
        }
    )

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

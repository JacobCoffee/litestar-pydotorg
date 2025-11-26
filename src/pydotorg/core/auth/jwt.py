"""JWT token creation and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt

from pydotorg.config import settings


class JWTService:
    @staticmethod
    def create_access_token(
        user_id: UUID,
        *,
        expires_delta: timedelta | None = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)

        expire = datetime.now(UTC) + expires_delta
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "access",
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(user_id: UUID) -> str:
        expires_delta = timedelta(days=30)
        expire = datetime.now(UTC) + expires_delta
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_verification_token(user_id: UUID, email: str) -> str:
        expires_delta = timedelta(hours=settings.email_verification_expire_hours)
        expire = datetime.now(UTC) + expires_delta
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "verify_email",
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        except JWTError as e:
            raise ValueError("Invalid token") from e

    @staticmethod
    def verify_token_type(payload: dict[str, Any], expected_type: str) -> None:
        token_type = payload.get("type")
        if token_type != expected_type:
            raise ValueError(f"Invalid token type: expected {expected_type}, got {token_type}")

    @staticmethod
    def get_user_id_from_token(token: str, token_type: str = "access") -> UUID:  # noqa: S107
        payload = JWTService.decode_token(token)
        JWTService.verify_token_type(payload, token_type)

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Token does not contain user ID")

        try:
            return UUID(user_id_str)
        except (TypeError, ValueError) as e:
            raise ValueError("Invalid user ID in token") from e


jwt_service = JWTService()

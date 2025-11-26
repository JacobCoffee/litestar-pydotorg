"""Authentication endpoints controller."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from litestar import Controller, post
from litestar.di import Provide
from litestar.exceptions import NotFoundException, PermissionDeniedException
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.core.auth.guards import require_authenticated
from pydotorg.core.auth.jwt import jwt_service
from pydotorg.core.auth.password import password_service
from pydotorg.core.auth.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(connection: ASGIConnection) -> User:
    if not connection.user:
        raise NotFoundException("User not found")
    return connection.user


class AuthController(Controller):
    path = "/api/auth"
    tags = ["auth"]
    dependencies = {"current_user": Provide(get_current_user)}

    @post("/register")
    async def register(
        self,
        data: RegisterRequest,
        db_session: AsyncSession,
    ) -> TokenResponse:
        result = await db_session.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == data.username:
                raise PermissionDeniedException("Username already exists")
            raise PermissionDeniedException("Email already registered")

        is_valid, error_message = password_service.validate_password_strength(data.password)
        if not is_valid:
            raise PermissionDeniedException(error_message or "Password does not meet requirements")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=password_service.hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=True,
            last_login=datetime.now(UTC),
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        access_token = jwt_service.create_access_token(user.id)
        refresh_token = jwt_service.create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60,
        )

    @post("/login")
    async def login(
        self,
        data: LoginRequest,
        db_session: AsyncSession,
    ) -> TokenResponse:
        result = await db_session.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()

        if not user or not password_service.verify_password(data.password, user.password_hash):
            raise PermissionDeniedException("Invalid credentials")

        if not user.is_active:
            raise PermissionDeniedException("Account is inactive")

        user.last_login = datetime.now(UTC)
        await db_session.commit()

        access_token = jwt_service.create_access_token(user.id)
        refresh_token = jwt_service.create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60,
        )

    @post("/refresh")
    async def refresh_token(
        self,
        data: RefreshTokenRequest,
        db_session: AsyncSession,
    ) -> TokenResponse:
        try:
            user_id = jwt_service.get_user_id_from_token(data.refresh_token, token_type="refresh")  # noqa: S106
        except ValueError as e:
            raise PermissionDeniedException("Invalid refresh token") from e

        result = await db_session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        user = result.scalar_one_or_none()

        if not user:
            raise PermissionDeniedException("User not found or inactive")

        access_token = jwt_service.create_access_token(user.id)
        refresh_token = jwt_service.create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60,
        )

    @post("/logout", guards=[require_authenticated])
    async def logout(self) -> dict[str, str]:
        return {"message": "Successfully logged out"}

    @post("/me", guards=[require_authenticated])
    async def get_me(self, current_user: User) -> UserResponse:
        return UserResponse.model_validate(current_user)

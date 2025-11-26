"""Session-based authentication using Redis."""

from __future__ import annotations

import secrets
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from redis import Redis
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from sqlalchemy.ext.asyncio import AsyncSession


class SessionService:
    def __init__(self, redis_url: str = settings.redis_url) -> None:
        self.redis_client = Redis.from_url(redis_url, decode_responses=True)
        self.session_prefix = "session:"

    def create_session(self, user_id: UUID) -> str:
        """Create a new session and return session ID."""
        session_id = secrets.token_urlsafe(32)
        session_key = f"{self.session_prefix}{session_id}"
        expire_seconds = settings.session_expire_minutes * 60

        self.redis_client.setex(
            session_key,
            timedelta(seconds=expire_seconds),
            str(user_id),
        )

        return session_id

    def get_user_id_from_session(self, session_id: str) -> UUID | None:
        """Retrieve user ID from session, return None if invalid or expired."""
        session_key = f"{self.session_prefix}{session_id}"
        user_id_str = self.redis_client.get(session_key)

        if not user_id_str:
            return None

        try:
            return UUID(user_id_str)
        except (TypeError, ValueError):
            return None

    def refresh_session(self, session_id: str) -> bool:
        """Extend session expiration time."""
        session_key = f"{self.session_prefix}{session_id}"
        expire_seconds = settings.session_expire_minutes * 60

        return bool(self.redis_client.expire(session_key, expire_seconds))

    def destroy_session(self, session_id: str) -> bool:
        """Delete session from Redis."""
        session_key = f"{self.session_prefix}{session_id}"
        return bool(self.redis_client.delete(session_key))

    def validate_session(self, session_id: str) -> bool:
        """Check if session exists and is valid."""
        session_key = f"{self.session_prefix}{session_id}"
        return bool(self.redis_client.exists(session_key))


class SessionAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        session_id = self._extract_session_id(connection)

        if not session_id:
            return AuthenticationResult(user=None, auth=None)

        session_service = SessionService()
        user_id = session_service.get_user_id_from_session(session_id)

        if not user_id:
            return AuthenticationResult(user=None, auth=None)

        plugin = connection.app.plugins.get(SQLAlchemyPlugin)
        async with plugin.get_session() as db_session:
            db_session: AsyncSession
            result = await db_session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
            user = result.scalar_one_or_none()

            if not user:
                return AuthenticationResult(user=None, auth=None)

            session_service.refresh_session(session_id)

            return AuthenticationResult(user=user, auth=session_id)

    @staticmethod
    def _extract_session_id(connection: ASGIConnection) -> str | None:
        """Extract session ID from cookie."""
        return connection.cookies.get(settings.session_cookie_name)


session_service = SessionService()

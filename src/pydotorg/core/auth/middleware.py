"""JWT and session authentication middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.core.auth.jwt import jwt_service
from pydotorg.core.auth.session import session_service
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from sqlalchemy.ext.asyncio import AsyncSession


class JWTAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        token = self._extract_token(connection)

        if token:
            try:
                user_id = jwt_service.get_user_id_from_token(token)
                user = await self._get_user(connection, user_id)
                if user:
                    return AuthenticationResult(user=user, auth=token)
            except ValueError:
                pass

        session_id = self._extract_session_id(connection)
        if session_id:
            user_id = session_service.get_user_id_from_session(session_id)
            if user_id:
                user = await self._get_user(connection, user_id)
                if user:
                    session_service.refresh_session(session_id)
                    return AuthenticationResult(user=user, auth=session_id)

        return AuthenticationResult(user=None, auth=None)

    @staticmethod
    async def _get_user(connection: ASGIConnection, user_id) -> User | None:
        """Retrieve active user from database."""
        plugin = connection.app.plugins.get(SQLAlchemyPlugin)
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:
            db_session: AsyncSession
            result = await db_session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
            return result.scalar_one_or_none()

    @staticmethod
    def _extract_token(connection: ASGIConnection) -> str | None:
        """Extract JWT token from Authorization header or cookie."""
        auth_header = connection.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

        token_cookie = connection.cookies.get("access_token")
        if token_cookie:
            return token_cookie

        return None

    @staticmethod
    def _extract_session_id(connection: ASGIConnection) -> str | None:
        """Extract session ID from cookie."""
        return connection.cookies.get(settings.session_cookie_name)

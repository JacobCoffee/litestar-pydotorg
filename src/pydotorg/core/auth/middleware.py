"""JWT authentication middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from sqlalchemy import select

from pydotorg.core.auth.jwt import jwt_service
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from sqlalchemy.ext.asyncio import AsyncSession


class JWTAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        token = self._extract_token(connection)

        if not token:
            return AuthenticationResult(user=None, auth=None)

        try:
            user_id = jwt_service.get_user_id_from_token(token)
        except ValueError:
            return AuthenticationResult(user=None, auth=None)

        plugin = connection.app.plugins.get(SQLAlchemyPlugin)
        async with plugin.get_session() as db_session:
            db_session: AsyncSession
            result = await db_session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
            user = result.scalar_one_or_none()

            if not user:
                return AuthenticationResult(user=None, auth=None)

            return AuthenticationResult(user=user, auth=token)

    @staticmethod
    def _extract_token(connection: ASGIConnection) -> str | None:
        auth_header = connection.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]

        token_cookie = connection.cookies.get("access_token")
        if token_cookie:
            return token_cookie

        return None

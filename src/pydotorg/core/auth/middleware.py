"""JWT, session, and API key authentication middleware."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.connection import Request
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult, MiddlewareProtocol
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.core.auth.jwt import jwt_service
from pydotorg.core.auth.session import session_service
from pydotorg.domains.users.api_keys import APIKey
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.connection import ASGIConnection
    from litestar.types import ASGIApp, Receive, Scope, Send
    from sqlalchemy.ext.asyncio import AsyncSession

API_KEY_HEADER = "X-API-Key"


class UserPopulationMiddleware(MiddlewareProtocol):
    """Middleware that always populates user in scope, regardless of exclude_from_auth.

    This runs BEFORE the auth middleware and ensures user is available in templates
    for showing admin buttons etc.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            # Try to populate user from session/token
            user = await self._get_user_from_request(scope)
            if user:
                scope["user"] = user
        await self.app(scope, receive, send)

    async def _get_user_from_request(self, scope: Scope) -> User | None:
        """Try to get user from API key, session, or JWT token."""
        request = Request(scope)

        # Try API key first (highest priority for programmatic access)
        api_key_header = request.headers.get(API_KEY_HEADER)
        if api_key_header:
            user = await self._get_user_from_api_key(scope, api_key_header)
            if user:
                scope["auth_method"] = "api_key"
                return user

        # Try JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                user_id = jwt_service.get_user_id_from_token(token)
                return await self._get_user(scope, user_id)
            except ValueError:
                pass

        # Try token from cookie
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            try:
                user_id = jwt_service.get_user_id_from_token(token_cookie)
                return await self._get_user(scope, user_id)
            except ValueError:
                pass

        # Try session
        session_id = request.cookies.get(settings.session_cookie_name)
        if session_id:
            user_id = session_service.get_user_id_from_session(session_id)
            if user_id:
                return await self._get_user(scope, user_id)

        return None

    @staticmethod
    async def _get_user_from_api_key(scope: Scope, raw_key: str) -> User | None:
        """Validate API key and return associated user."""
        app: Litestar = scope["app"]
        plugin = app.plugins.get(SQLAlchemyPlugin)
        if plugin is None:
            return None
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:
            db_session: AsyncSession
            key_hash = APIKey.hash_key(raw_key)
            result = await db_session.execute(
                select(APIKey)
                .where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
                .options()
            )
            api_key = result.scalar_one_or_none()
            if api_key is None:
                return None
            if api_key.is_expired:
                return None
            # Update last_used_at
            api_key.last_used_at = datetime.now(tz=UTC)
            await db_session.commit()
            # Get the user
            user_result = await db_session.execute(
                select(User).where(User.id == api_key.user_id, User.is_active.is_(True))
            )
            return user_result.scalar_one_or_none()

    @staticmethod
    async def _get_user(scope: Scope, user_id) -> User | None:
        """Retrieve active user from database."""
        app: Litestar = scope["app"]
        plugin = app.plugins.get(SQLAlchemyPlugin)
        if plugin is None:
            return None
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:  # type: ignore[union-attr]
            db_session: AsyncSession
            result = await db_session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
            return result.scalar_one_or_none()


class JWTAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        # Check if user was already populated by UserPopulationMiddleware
        existing_user = connection.scope.get("user")
        if existing_user:
            auth_method = connection.scope.get("auth_method", "session")
            return AuthenticationResult(user=existing_user, auth=auth_method)

        # Try API key first
        api_key = self._extract_api_key(connection)
        if api_key:
            user = await self._get_user_from_api_key(connection, api_key)
            if user:
                return AuthenticationResult(user=user, auth="api_key")

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
        if plugin is None:
            return None
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:  # type: ignore[union-attr]
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

    @staticmethod
    def _extract_api_key(connection: ASGIConnection) -> str | None:
        """Extract API key from X-API-Key header."""
        return connection.headers.get(API_KEY_HEADER)

    @staticmethod
    async def _get_user_from_api_key(connection: ASGIConnection, raw_key: str) -> User | None:
        """Validate API key and return associated user."""
        plugin = connection.app.plugins.get(SQLAlchemyPlugin)
        if plugin is None:
            return None
        config = plugin.config[0] if isinstance(plugin.config, list) else plugin.config
        async with config.get_session() as db_session:
            db_session: AsyncSession
            key_hash = APIKey.hash_key(raw_key)
            result = await db_session.execute(
                select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
            )
            api_key = result.scalar_one_or_none()
            if api_key is None:
                return None
            if api_key.is_expired:
                return None
            # Update last_used_at
            api_key.last_used_at = datetime.now(tz=UTC)
            await db_session.commit()
            # Get the user
            user_result = await db_session.execute(
                select(User).where(User.id == api_key.user_id, User.is_active.is_(True))
            )
            return user_result.scalar_one_or_none()

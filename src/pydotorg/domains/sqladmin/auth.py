"""SQLAdmin authentication backend."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pydotorg.config import settings
from pydotorg.core.auth.session import SessionService
from pydotorg.domains.users.models import User
from pydotorg.domains.users.security import verify_password

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)


class AdminAuthBackend(AuthenticationBackend):
    """Authentication backend for SQLAdmin panel.

    Ensures only superusers can access the admin interface.
    Uses its own database session since SQLAdmin runs outside Litestar's DI.

    Also checks for existing Litestar session to provide seamless SSO
    between the main admin panel and SQLAdmin.
    """

    def __init__(self, secret_key: str) -> None:
        super().__init__(secret_key)
        self._engine = create_async_engine(str(settings.database_url))
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine, expire_on_commit=False
        )
        self._litestar_session_service = SessionService()

    async def login(self, request: Request) -> bool:
        """Authenticate user login and create session."""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        async with self._session_maker() as db_session:
            result = await db_session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()

            if not user:
                return False

            if not user.is_superuser:
                return False

            if not user.password_hash:
                return False

            if not verify_password(password, user.password_hash):
                return False

            request.session.update({"user_id": str(user.id), "is_admin": True})
            return True

    async def logout(self, request: Request) -> bool:
        """Clear user session."""
        request.session.clear()
        return True

    async def _check_litestar_session(self, request: Request) -> User | None:
        """Check if user has valid Litestar session (SSO from main admin).

        Returns:
            User if authenticated via Litestar session and is superuser, None otherwise.
        """
        litestar_session_id = request.cookies.get(settings.session_cookie_name)
        if not litestar_session_id:
            return None

        user_id = self._litestar_session_service.get_user_id_from_session(litestar_session_id)
        if not user_id:
            return None

        async with self._session_maker() as db_session:
            result = await db_session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user and user.is_superuser and user.is_active:
                return user

        return None

    async def authenticate(self, request: Request) -> bool:
        """Verify user is authenticated and is a superuser.

        First checks for a valid Litestar session (SSO from main admin panel).
        Falls back to SQLAdmin's own session if Litestar session not present.
        """
        litestar_user = await self._check_litestar_session(request)
        if litestar_user:
            logger.debug("SQLAdmin auth via Litestar session for user %s", litestar_user.username)
            request.session.update({"user_id": str(litestar_user.id), "is_admin": True})
            return True

        user_id = request.session.get("user_id")
        is_admin = request.session.get("is_admin")

        if not user_id or not is_admin:
            return False

        async with self._session_maker() as db_session:
            try:
                uid = UUID(str(user_id))
            except (TypeError, ValueError):
                return False

            result = await db_session.execute(select(User).where(User.id == uid))
            user = result.scalar_one_or_none()

            return bool(user and user.is_superuser and user.is_active)

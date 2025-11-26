"""SQLAdmin authentication backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from passlib.hash import pbkdf2_sha256
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select

from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from litestar import Request
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminAuthBackend(AuthenticationBackend):
    """Authentication backend for SQLAdmin panel.

    Ensures only superusers can access the admin interface.
    """

    async def login(self, request: Request) -> bool:
        """Authenticate user login and create session."""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        db_session: AsyncSession = request.state.db_session

        result = await db_session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return False

        if not user.is_superuser:
            return False

        if not user.password_hash:
            return False

        if not pbkdf2_sha256.verify(password, user.password_hash):
            return False

        request.session.update({"user_id": str(user.id), "is_admin": True})
        return True

    async def logout(self, request: Request) -> bool:
        """Clear user session."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Verify user is authenticated and is a superuser."""
        user_id = request.session.get("user_id")
        is_admin = request.session.get("is_admin")

        if not user_id or not is_admin:
            return False

        db_session: AsyncSession = request.state.db_session

        result = await db_session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        return bool(user and user.is_superuser and user.is_active)

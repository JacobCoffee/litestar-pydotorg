"""User domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.users.models import Membership, User, UserGroup

if TYPE_CHECKING:
    from uuid import UUID


class UserRepository(SQLAlchemyAsyncRepository[User]):
    """Repository for User database operations."""

    model_type = User

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: The email address to search for.

        Returns:
            The user if found, None otherwise.
        """
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username.

        Args:
            username: The username to search for.

        Returns:
            The user if found, None otherwise.
        """
        statement = select(User).where(User.username == username)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if a user exists by email.

        Args:
            email: The email address to check.

        Returns:
            True if a user with this email exists, False otherwise.
        """
        user = await self.get_by_email(email)
        return user is not None

    async def exists_by_username(self, username: str) -> bool:
        """Check if a user exists by username.

        Args:
            username: The username to check.

        Returns:
            True if a user with this username exists, False otherwise.
        """
        user = await self.get_by_username(username)
        return user is not None


class MembershipRepository(SQLAlchemyAsyncRepository[Membership]):
    """Repository for Membership database operations."""

    model_type = Membership

    async def get_by_user_id(self, user_id: UUID) -> Membership | None:
        """Get a membership by user ID.

        Args:
            user_id: The user ID to search for.

        Returns:
            The membership if found, None otherwise.
        """
        statement = select(Membership).where(Membership.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class UserGroupRepository(SQLAlchemyAsyncRepository[UserGroup]):
    """Repository for UserGroup database operations."""

    model_type = UserGroup

    async def list_approved(self, limit: int = 100, offset: int = 0) -> list[UserGroup]:
        """List approved user groups.

        Args:
            limit: Maximum number of groups to return.
            offset: Number of groups to skip.

        Returns:
            List of approved user groups.
        """
        statement = select(UserGroup).where(UserGroup.approved.is_(True)).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_trusted(self, limit: int = 100, offset: int = 0) -> list[UserGroup]:
        """List trusted user groups.

        Args:
            limit: Maximum number of groups to return.
            offset: Number of groups to skip.

        Returns:
            List of trusted user groups.
        """
        statement = select(UserGroup).where(UserGroup.trusted.is_(True)).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

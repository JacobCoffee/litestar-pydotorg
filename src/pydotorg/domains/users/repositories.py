"""User domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.users.api_keys import APIKey
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


class APIKeyRepository(SQLAlchemyAsyncRepository[APIKey]):
    """Repository for API key database operations."""

    model_type = APIKey

    async def get_by_hash(self, key_hash: str) -> APIKey | None:
        """Get an API key by its hash.

        Args:
            key_hash: The SHA-256 hash of the API key.

        Returns:
            The API key if found, None otherwise.
        """
        statement = select(APIKey).where(APIKey.key_hash == key_hash)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_prefix(self, key_prefix: str) -> APIKey | None:
        """Get an API key by its prefix.

        Args:
            key_prefix: The first 12 characters of the key.

        Returns:
            The API key if found, None otherwise.
        """
        statement = select(APIKey).where(APIKey.key_prefix == key_prefix)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[APIKey]:
        """List all API keys for a user.

        Args:
            user_id: The user ID.

        Returns:
            List of API keys.
        """
        statement = select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_active_by_user(self, user_id: UUID) -> list[APIKey]:
        """List active API keys for a user.

        Args:
            user_id: The user ID.

        Returns:
            List of active API keys.
        """
        statement = (
            select(APIKey)
            .where(APIKey.user_id == user_id, APIKey.is_active.is_(True))
            .order_by(APIKey.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoke all API keys for a user.

        Args:
            user_id: The user ID.

        Returns:
            Number of keys revoked.
        """
        keys = await self.list_active_by_user(user_id)
        for key in keys:
            key.is_active = False
        return len(keys)

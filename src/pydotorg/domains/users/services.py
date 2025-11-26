"""User domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.users.models import Membership, User, UserGroup
from pydotorg.domains.users.repositories import MembershipRepository, UserGroupRepository, UserRepository
from pydotorg.domains.users.security import hash_password

if TYPE_CHECKING:
    from uuid import UUID

    from pydotorg.domains.users.schemas import UserCreate


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    """Service for User business logic."""

    repository_type = UserRepository
    match_fields = ["email", "username"]

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user with hashed password.

        Args:
            data: User creation data including plain-text password.

        Returns:
            The created user instance.

        Raises:
            ValueError: If email or username already exists.
        """
        if await self.repository.exists_by_email(data.email):
            msg = f"User with email {data.email} already exists"
            raise ValueError(msg)

        if await self.repository.exists_by_username(data.username):
            msg = f"User with username {data.username} already exists"
            raise ValueError(msg)

        user_data = data.model_dump(exclude={"password"})
        user_data["password_hash"] = hash_password(data.password)

        return await self.create(user_data)

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: The email address to search for.

        Returns:
            The user if found, None otherwise.
        """
        return await self.repository.get_by_email(email)

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username.

        Args:
            username: The username to search for.

        Returns:
            The user if found, None otherwise.
        """
        return await self.repository.get_by_username(username)

    async def deactivate(self, user_id: UUID) -> User:
        """Deactivate a user account.

        Args:
            user_id: The ID of the user to deactivate.

        Returns:
            The updated user instance.
        """
        user = await self.get(user_id)
        user.is_active = False
        return await self.update(user_id, {"is_active": False})

    async def reactivate(self, user_id: UUID) -> User:
        """Reactivate a user account.

        Args:
            user_id: The ID of the user to reactivate.

        Returns:
            The updated user instance.
        """
        user = await self.get(user_id)
        user.is_active = True
        return await self.update(user_id, {"is_active": True})


class MembershipService(SQLAlchemyAsyncRepositoryService[Membership]):
    """Service for Membership business logic."""

    repository_type = MembershipRepository
    match_fields = ["user_id"]

    async def get_by_user_id(self, user_id: UUID) -> Membership | None:
        """Get a membership by user ID.

        Args:
            user_id: The user ID to search for.

        Returns:
            The membership if found, None otherwise.
        """
        return await self.repository.get_by_user_id(user_id)

    async def create_for_user(self, user_id: UUID, membership_data: dict) -> Membership:
        """Create a membership for a specific user.

        Args:
            user_id: The ID of the user to create membership for.
            membership_data: The membership data.

        Returns:
            The created membership instance.

        Raises:
            ValueError: If user already has a membership.
        """
        existing = await self.get_by_user_id(user_id)
        if existing:
            msg = f"User {user_id} already has a membership"
            raise ValueError(msg)

        membership_data["user_id"] = user_id
        return await self.create(membership_data)


class UserGroupService(SQLAlchemyAsyncRepositoryService[UserGroup]):
    """Service for UserGroup business logic."""

    repository_type = UserGroupRepository
    match_fields = ["name"]

    async def list_approved(self, limit: int = 100, offset: int = 0) -> list[UserGroup]:
        """List approved user groups.

        Args:
            limit: Maximum number of groups to return.
            offset: Number of groups to skip.

        Returns:
            List of approved user groups.
        """
        return await self.repository.list_approved(limit=limit, offset=offset)

    async def list_trusted(self, limit: int = 100, offset: int = 0) -> list[UserGroup]:
        """List trusted user groups.

        Args:
            limit: Maximum number of groups to return.
            offset: Number of groups to skip.

        Returns:
            List of trusted user groups.
        """
        return await self.repository.list_trusted(limit=limit, offset=offset)

    async def approve(self, group_id: UUID) -> UserGroup:
        """Approve a user group.

        Args:
            group_id: The ID of the group to approve.

        Returns:
            The updated group instance.
        """
        return await self.update(group_id, {"approved": True})

    async def revoke_approval(self, group_id: UUID) -> UserGroup:
        """Revoke approval of a user group.

        Args:
            group_id: The ID of the group to revoke approval.

        Returns:
            The updated group instance.
        """
        return await self.update(group_id, {"approved": False})

    async def mark_trusted(self, group_id: UUID) -> UserGroup:
        """Mark a user group as trusted.

        Args:
            group_id: The ID of the group to mark as trusted.

        Returns:
            The updated group instance.
        """
        return await self.update(group_id, {"trusted": True})

    async def revoke_trust(self, group_id: UUID) -> UserGroup:
        """Revoke trust of a user group.

        Args:
            group_id: The ID of the group to revoke trust.

        Returns:
            The updated group instance.
        """
        return await self.update(group_id, {"trusted": False})

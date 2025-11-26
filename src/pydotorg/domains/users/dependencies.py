"""User domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.users.repositories import MembershipRepository, UserGroupRepository, UserRepository
from pydotorg.domains.users.services import MembershipService, UserGroupService, UserService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_user_repository(db_session: AsyncSession) -> AsyncGenerator[UserRepository, None]:
    """Provide a UserRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A UserRepository instance.
    """
    async with UserRepository(session=db_session) as repo:
        yield repo


async def provide_user_service(
    user_repository: UserRepository,
) -> AsyncGenerator[UserService, None]:
    """Provide a UserService instance.

    Args:
        user_repository: The user repository.

    Yields:
        A UserService instance.
    """
    async with UserService(repository=user_repository) as service:
        yield service


async def provide_membership_repository(db_session: AsyncSession) -> AsyncGenerator[MembershipRepository, None]:
    """Provide a MembershipRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A MembershipRepository instance.
    """
    async with MembershipRepository(session=db_session) as repo:
        yield repo


async def provide_membership_service(
    membership_repository: MembershipRepository,
) -> AsyncGenerator[MembershipService, None]:
    """Provide a MembershipService instance.

    Args:
        membership_repository: The membership repository.

    Yields:
        A MembershipService instance.
    """
    async with MembershipService(repository=membership_repository) as service:
        yield service


async def provide_user_group_repository(db_session: AsyncSession) -> AsyncGenerator[UserGroupRepository, None]:
    """Provide a UserGroupRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A UserGroupRepository instance.
    """
    async with UserGroupRepository(session=db_session) as repo:
        yield repo


async def provide_user_group_service(
    user_group_repository: UserGroupRepository,
) -> AsyncGenerator[UserGroupService, None]:
    """Provide a UserGroupService instance.

    Args:
        user_group_repository: The user group repository.

    Yields:
        A UserGroupService instance.
    """
    async with UserGroupService(repository=user_group_repository) as service:
        yield service


def get_user_dependencies() -> dict:
    """Get all user domain dependency providers.

    Returns:
        Dictionary of dependency providers for the user domain.
    """
    return {
        "user_repository": provide_user_repository,
        "user_service": provide_user_service,
        "membership_repository": provide_membership_repository,
        "membership_service": provide_membership_service,
        "user_group_repository": provide_user_group_repository,
        "user_group_service": provide_user_group_service,
    }

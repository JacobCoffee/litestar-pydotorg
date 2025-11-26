"""User domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.users.repositories import MembershipRepository, UserGroupRepository, UserRepository
from pydotorg.domains.users.services import MembershipService, UserGroupService, UserService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_user_repository(db_session: AsyncSession) -> UserRepository:
    """Provide a UserRepository instance."""
    return UserRepository(session=db_session)


async def provide_user_service(db_session: AsyncSession) -> UserService:
    """Provide a UserService instance."""
    return UserService(session=db_session)


async def provide_membership_repository(db_session: AsyncSession) -> MembershipRepository:
    """Provide a MembershipRepository instance."""
    return MembershipRepository(session=db_session)


async def provide_membership_service(db_session: AsyncSession) -> MembershipService:
    """Provide a MembershipService instance."""
    return MembershipService(session=db_session)


async def provide_user_group_repository(db_session: AsyncSession) -> UserGroupRepository:
    """Provide a UserGroupRepository instance."""
    return UserGroupRepository(session=db_session)


async def provide_user_group_service(db_session: AsyncSession) -> UserGroupService:
    """Provide a UserGroupService instance."""
    return UserGroupService(session=db_session)


def get_user_dependencies() -> dict:
    """Get all user domain dependency providers."""
    return {
        "user_repository": provide_user_repository,
        "user_service": provide_user_service,
        "membership_repository": provide_membership_repository,
        "membership_service": provide_membership_service,
        "user_group_repository": provide_user_group_repository,
        "user_group_service": provide_user_group_service,
    }

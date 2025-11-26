"""Work Groups domain dependency injection providers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.domains.work_groups.repositories import WorkGroupRepository
from pydotorg.domains.work_groups.services import WorkGroupService


async def provide_work_group_repository(db_session: AsyncSession) -> WorkGroupRepository:
    """Provide a WorkGroupRepository instance."""
    return WorkGroupRepository(session=db_session)


async def provide_work_group_service(db_session: AsyncSession) -> WorkGroupService:
    """Provide a WorkGroupService instance."""
    return WorkGroupService(session=db_session)


def get_work_groups_dependencies() -> dict:
    """Get all work groups domain dependency providers."""
    return {
        "work_group_repository": provide_work_group_repository,
        "work_group_service": provide_work_group_service,
    }

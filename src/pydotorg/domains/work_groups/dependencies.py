"""Work Groups domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.work_groups.repositories import WorkGroupRepository
from pydotorg.domains.work_groups.services import WorkGroupService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_work_group_repository(db_session: AsyncSession) -> AsyncGenerator[WorkGroupRepository, None]:
    """Provide a WorkGroupRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A WorkGroupRepository instance.
    """
    async with WorkGroupRepository(session=db_session) as repo:
        yield repo


async def provide_work_group_service(
    work_group_repository: WorkGroupRepository,
) -> AsyncGenerator[WorkGroupService, None]:
    """Provide a WorkGroupService instance.

    Args:
        work_group_repository: The work group repository.

    Yields:
        A WorkGroupService instance.
    """
    async with WorkGroupService(repository=work_group_repository) as service:
        yield service


def get_work_groups_dependencies() -> dict:
    """Get all work groups domain dependency providers.

    Returns:
        Dictionary of dependency providers for the work groups domain.
    """
    return {
        "work_group_repository": provide_work_group_repository,
        "work_group_service": provide_work_group_service,
    }

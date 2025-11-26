"""Work Groups domain services for business logic."""

from __future__ import annotations

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.work_groups.models import WorkGroup
from pydotorg.domains.work_groups.repositories import WorkGroupRepository


class WorkGroupService(SQLAlchemyAsyncRepositoryService[WorkGroup]):
    """Service for WorkGroup business logic."""

    repository_type = WorkGroupRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> WorkGroup | None:
        """Get a work group by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The work group if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_active_work_groups(self, limit: int = 100, offset: int = 0) -> list[WorkGroup]:
        """Get active work groups.

        Args:
            limit: Maximum number of work groups to return.
            offset: Number of work groups to skip.

        Returns:
            List of active work groups.
        """
        return await self.repository.get_active_work_groups(limit=limit, offset=offset)

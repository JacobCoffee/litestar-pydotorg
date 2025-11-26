"""Work Groups domain repositories for database access."""

from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.work_groups.models import WorkGroup


class WorkGroupRepository(SQLAlchemyAsyncRepository[WorkGroup]):
    """Repository for WorkGroup database operations."""

    model_type = WorkGroup

    async def get_by_slug(self, slug: str) -> WorkGroup | None:
        """Get a work group by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The work group if found, None otherwise.
        """
        statement = select(WorkGroup).where(WorkGroup.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_work_groups(self, limit: int = 100, offset: int = 0) -> list[WorkGroup]:
        """Get active work groups.

        Args:
            limit: Maximum number of work groups to return.
            offset: Number of work groups to skip.

        Returns:
            List of active work groups ordered by name.
        """
        statement = (
            select(WorkGroup).where(WorkGroup.active.is_(True)).order_by(WorkGroup.name).limit(limit).offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

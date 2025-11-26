"""Minutes domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.minutes.repositories import MinutesRepository

if TYPE_CHECKING:
    import datetime


class MinutesService(SQLAlchemyAsyncRepositoryService[Minutes]):
    """Service for Minutes business logic."""

    repository_type = MinutesRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> Minutes | None:
        """Get minutes by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The minutes if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_published_minutes(self, limit: int = 100, offset: int = 0) -> list[Minutes]:
        """Get published minutes.

        Args:
            limit: Maximum number of minutes to return.
            offset: Number of minutes to skip.

        Returns:
            List of published minutes.
        """
        return await self.repository.get_published_minutes(limit=limit, offset=offset)

    async def get_by_date(self, date: datetime.date) -> Minutes | None:
        """Get minutes by date.

        Args:
            date: The date to search for.

        Returns:
            The minutes if found, None otherwise.
        """
        return await self.repository.get_by_date(date)

    async def get_by_date_range(
        self, start_date: datetime.date, end_date: datetime.date, limit: int = 100
    ) -> list[Minutes]:
        """Get minutes by date range.

        Args:
            start_date: The start date.
            end_date: The end date.
            limit: Maximum number of minutes to return.

        Returns:
            List of minutes.
        """
        return await self.repository.get_by_date_range(start_date, end_date, limit=limit)

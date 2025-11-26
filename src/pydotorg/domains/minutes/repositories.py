"""Minutes domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.minutes.models import Minutes

if TYPE_CHECKING:
    import datetime


class MinutesRepository(SQLAlchemyAsyncRepository[Minutes]):
    """Repository for Minutes database operations."""

    model_type = Minutes

    async def get_by_slug(self, slug: str) -> Minutes | None:
        """Get minutes by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The minutes if found, None otherwise.
        """
        statement = select(Minutes).where(Minutes.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_published_minutes(self, limit: int = 100, offset: int = 0) -> list[Minutes]:
        """Get published minutes.

        Args:
            limit: Maximum number of minutes to return.
            offset: Number of minutes to skip.

        Returns:
            List of published minutes ordered by date descending.
        """
        statement = (
            select(Minutes)
            .where(Minutes.is_published.is_(True))
            .order_by(Minutes.date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_date(self, date: datetime.date) -> Minutes | None:
        """Get minutes by date.

        Args:
            date: The date to search for.

        Returns:
            The minutes if found, None otherwise.
        """
        statement = select(Minutes).where(Minutes.date == date)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self, start_date: datetime.date, end_date: datetime.date, limit: int = 100
    ) -> list[Minutes]:
        """Get minutes by date range.

        Args:
            start_date: The start date.
            end_date: The end date.
            limit: Maximum number of minutes to return.

        Returns:
            List of minutes ordered by date descending.
        """
        statement = (
            select(Minutes)
            .where(Minutes.date >= start_date, Minutes.date <= end_date, Minutes.is_published.is_(True))
            .order_by(Minutes.date.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

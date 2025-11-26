"""Sponsors domain repositories for database access."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel, SponsorshipStatus

if TYPE_CHECKING:
    from uuid import UUID


class SponsorshipLevelRepository(SQLAlchemyAsyncRepository[SponsorshipLevel]):
    """Repository for SponsorshipLevel database operations."""

    model_type = SponsorshipLevel

    async def get_by_slug(self, slug: str) -> SponsorshipLevel | None:
        """Get a sponsorship level by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The sponsorship level if found, None otherwise.
        """
        statement = select(SponsorshipLevel).where(SponsorshipLevel.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_ordered(self, limit: int = 100, offset: int = 0) -> list[SponsorshipLevel]:
        """List sponsorship levels ordered by order field.

        Args:
            limit: Maximum number of levels to return.
            offset: Number of levels to skip.

        Returns:
            List of sponsorship levels ordered by order field.
        """
        statement = select(SponsorshipLevel).order_by(SponsorshipLevel.order.asc()).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def exists_by_slug(self, slug: str) -> bool:
        """Check if a sponsorship level exists by slug.

        Args:
            slug: The slug to check.

        Returns:
            True if a level with this slug exists, False otherwise.
        """
        level = await self.get_by_slug(slug)
        return level is not None


class SponsorRepository(SQLAlchemyAsyncRepository[Sponsor]):
    """Repository for Sponsor database operations."""

    model_type = Sponsor

    async def get_by_slug(self, slug: str) -> Sponsor | None:
        """Get a sponsor by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The sponsor if found, None otherwise.
        """
        statement = select(Sponsor).where(Sponsor.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_with_active_sponsorships(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsor]:
        """List sponsors with active sponsorships.

        Args:
            limit: Maximum number of sponsors to return.
            offset: Number of sponsors to skip.

        Returns:
            List of sponsors with active sponsorships.
        """
        statement = (
            select(Sponsor)
            .join(Sponsorship, Sponsor.id == Sponsorship.sponsor_id)
            .where(Sponsorship.status == SponsorshipStatus.FINALIZED)
            .distinct()
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def exists_by_slug(self, slug: str) -> bool:
        """Check if a sponsor exists by slug.

        Args:
            slug: The slug to check.

        Returns:
            True if a sponsor with this slug exists, False otherwise.
        """
        sponsor = await self.get_by_slug(slug)
        return sponsor is not None


class SponsorshipRepository(SQLAlchemyAsyncRepository[Sponsorship]):
    """Repository for Sponsorship database operations."""

    model_type = Sponsorship

    async def list_by_sponsor_id(
        self,
        sponsor_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships for a specific sponsor.

        Args:
            sponsor_id: The sponsor ID to filter by.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships for the sponsor.
        """
        statement = select(Sponsorship).where(Sponsorship.sponsor_id == sponsor_id).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_by_level_id(
        self,
        level_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships for a specific level.

        Args:
            level_id: The level ID to filter by.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships for the level.
        """
        statement = select(Sponsorship).where(Sponsorship.level_id == level_id).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: SponsorshipStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Sponsorship]:
        """List sponsorships by status.

        Args:
            status: The status to filter by.
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of sponsorships with the given status.
        """
        statement = select(Sponsorship).where(Sponsorship.status == status).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Sponsorship]:
        """List active sponsorships.

        Args:
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of active sponsorships.
        """
        today = datetime.now(tz=UTC).date()
        statement = (
            select(Sponsorship)
            .where(Sponsorship.status == SponsorshipStatus.FINALIZED)
            .where(Sponsorship.start_date <= today)
            .where(Sponsorship.end_date >= today)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

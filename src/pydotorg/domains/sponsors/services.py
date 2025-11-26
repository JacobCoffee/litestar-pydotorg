"""Sponsors domain services for business logic."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel, SponsorshipStatus
from pydotorg.domains.sponsors.repositories import (
    SponsorRepository,
    SponsorshipLevelRepository,
    SponsorshipRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from pydotorg.domains.sponsors.schemas import (
        SponsorCreate,
        SponsorshipCreate,
        SponsorshipLevelCreate,
    )


class SponsorshipLevelService(SQLAlchemyAsyncRepositoryService[SponsorshipLevel]):
    """Service for SponsorshipLevel business logic."""

    repository_type = SponsorshipLevelRepository
    match_fields = ["slug"]

    async def create_level(self, data: SponsorshipLevelCreate) -> SponsorshipLevel:
        """Create a new sponsorship level.

        Args:
            data: Sponsorship level creation data.

        Returns:
            The created sponsorship level instance.

        Raises:
            ValueError: If slug already exists.
        """
        if data.slug and await self.repository.exists_by_slug(data.slug):
            msg = f"Sponsorship level with slug {data.slug} already exists"
            raise ValueError(msg)

        level_data = data.model_dump()
        if not level_data.get("slug") and level_data.get("name"):
            level_data["slug"] = SponsorshipLevel.generate_slug(level_data["name"])

        return await self.create(level_data)

    async def get_by_slug(self, slug: str) -> SponsorshipLevel | None:
        """Get a sponsorship level by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The sponsorship level if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def list_ordered(self, limit: int = 100, offset: int = 0) -> list[SponsorshipLevel]:
        """List sponsorship levels ordered by order field.

        Args:
            limit: Maximum number of levels to return.
            offset: Number of levels to skip.

        Returns:
            List of sponsorship levels ordered by order field.
        """
        return await self.repository.list_ordered(limit=limit, offset=offset)


class SponsorService(SQLAlchemyAsyncRepositoryService[Sponsor]):
    """Service for Sponsor business logic."""

    repository_type = SponsorRepository
    match_fields = ["slug"]

    async def create_sponsor(self, data: SponsorCreate) -> Sponsor:
        """Create a new sponsor.

        Args:
            data: Sponsor creation data.

        Returns:
            The created sponsor instance.

        Raises:
            ValueError: If slug already exists.
        """
        if data.slug and await self.repository.exists_by_slug(data.slug):
            msg = f"Sponsor with slug {data.slug} already exists"
            raise ValueError(msg)

        sponsor_data = data.model_dump()
        if not sponsor_data.get("slug") and sponsor_data.get("name"):
            sponsor_data["slug"] = Sponsor.generate_slug(sponsor_data["name"])

        return await self.create(sponsor_data)

    async def get_by_slug(self, slug: str) -> Sponsor | None:
        """Get a sponsor by its slug.

        Args:
            slug: The slug to search for.

        Returns:
            The sponsor if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

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
        return await self.repository.list_with_active_sponsorships(limit=limit, offset=offset)


class SponsorshipService(SQLAlchemyAsyncRepositoryService[Sponsorship]):
    """Service for Sponsorship business logic."""

    repository_type = SponsorshipRepository
    match_fields = ["sponsor_id", "level_id"]

    async def create_sponsorship(self, data: SponsorshipCreate) -> Sponsorship:
        """Create a new sponsorship.

        Args:
            data: Sponsorship creation data.

        Returns:
            The created sponsorship instance.
        """
        sponsorship_data = data.model_dump()
        if not sponsorship_data.get("applied_on"):
            sponsorship_data["applied_on"] = datetime.now(tz=UTC).date()

        return await self.create(sponsorship_data)

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
        return await self.repository.list_by_sponsor_id(sponsor_id, limit=limit, offset=offset)

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
        return await self.repository.list_by_level_id(level_id, limit=limit, offset=offset)

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
        return await self.repository.list_by_status(status, limit=limit, offset=offset)

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Sponsorship]:
        """List active sponsorships.

        Args:
            limit: Maximum number of sponsorships to return.
            offset: Number of sponsorships to skip.

        Returns:
            List of active sponsorships.
        """
        return await self.repository.list_active(limit=limit, offset=offset)

    async def approve(self, sponsorship_id: UUID) -> Sponsorship:
        """Approve a sponsorship.

        Args:
            sponsorship_id: The ID of the sponsorship to approve.

        Returns:
            The updated sponsorship instance.
        """
        return await self.update(
            sponsorship_id,
            {
                "status": SponsorshipStatus.APPROVED,
                "approved_on": datetime.now(tz=UTC).date(),
            },
        )

    async def reject(self, sponsorship_id: UUID) -> Sponsorship:
        """Reject a sponsorship.

        Args:
            sponsorship_id: The ID of the sponsorship to reject.

        Returns:
            The updated sponsorship instance.
        """
        return await self.update(
            sponsorship_id,
            {
                "status": SponsorshipStatus.REJECTED,
                "rejected_on": datetime.now(tz=UTC).date(),
            },
        )

    async def finalize(self, sponsorship_id: UUID) -> Sponsorship:
        """Finalize a sponsorship.

        Args:
            sponsorship_id: The ID of the sponsorship to finalize.

        Returns:
            The updated sponsorship instance.
        """
        return await self.update(
            sponsorship_id,
            {
                "status": SponsorshipStatus.FINALIZED,
                "finalized_on": datetime.now(tz=UTC).date(),
            },
        )

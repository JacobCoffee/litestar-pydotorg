"""Admin sponsor management service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel, SponsorshipStatus

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SponsorAdminService:
    """Service for admin sponsor management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_sponsorships(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Sponsorship], int]:
        """List sponsorships with filtering and pagination.

        Args:
            limit: Maximum number of sponsorships to return
            offset: Number of sponsorships to skip
            status: Filter by sponsorship status
            search: Search query for sponsor name

        Returns:
            Tuple of (sponsorships list, total count)
        """
        query = select(Sponsorship).options(
            selectinload(Sponsorship.sponsor),
            selectinload(Sponsorship.level),
            selectinload(Sponsorship.submitted_by),
        )

        if status:
            status_enum = SponsorshipStatus(status)
            query = query.where(Sponsorship.status == status_enum)

        if search:
            search_term = f"%{search}%"
            query = query.join(Sponsorship.sponsor).where(
                or_(
                    Sponsor.name.ilike(search_term),
                    Sponsor.description.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Sponsorship.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        sponsorships = list(result.scalars().all())

        return sponsorships, total

    async def list_sponsors(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> tuple[list[Sponsor], int]:
        """List sponsors with filtering and pagination.

        Args:
            limit: Maximum number of sponsors to return
            offset: Number of sponsors to skip
            search: Search query for sponsor name

        Returns:
            Tuple of (sponsors list, total count)
        """
        query = select(Sponsor)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Sponsor.name.ilike(search_term),
                    Sponsor.description.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Sponsor.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        sponsors = list(result.scalars().all())

        return sponsors, total

    async def get_sponsorship(self, sponsorship_id: UUID) -> Sponsorship | None:
        """Get a sponsorship by ID.

        Args:
            sponsorship_id: Sponsorship ID

        Returns:
            Sponsorship if found, None otherwise
        """
        query = (
            select(Sponsorship)
            .where(Sponsorship.id == sponsorship_id)
            .options(
                selectinload(Sponsorship.sponsor),
                selectinload(Sponsorship.level),
                selectinload(Sponsorship.submitted_by),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_sponsor(self, sponsor_id: UUID) -> Sponsor | None:
        """Get a sponsor by ID.

        Args:
            sponsor_id: Sponsor ID

        Returns:
            Sponsor if found, None otherwise
        """
        query = (
            select(Sponsor)
            .where(Sponsor.id == sponsor_id)
            .options(selectinload(Sponsor.sponsorships).selectinload(Sponsorship.level))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def approve_sponsorship(self, sponsorship_id: UUID) -> Sponsorship | None:
        """Approve a sponsorship.

        Args:
            sponsorship_id: Sponsorship ID

        Returns:
            Updated sponsorship if found, None otherwise
        """
        sponsorship = await self.get_sponsorship(sponsorship_id)
        if not sponsorship:
            return None

        sponsorship.status = SponsorshipStatus.APPROVED
        sponsorship.approved_on = datetime.now(tz=UTC).date()
        await self.session.commit()
        await self.session.refresh(sponsorship)
        return sponsorship

    async def reject_sponsorship(self, sponsorship_id: UUID) -> Sponsorship | None:
        """Reject a sponsorship.

        Args:
            sponsorship_id: Sponsorship ID

        Returns:
            Updated sponsorship if found, None otherwise
        """
        sponsorship = await self.get_sponsorship(sponsorship_id)
        if not sponsorship:
            return None

        sponsorship.status = SponsorshipStatus.REJECTED
        sponsorship.rejected_on = datetime.now(tz=UTC).date()
        await self.session.commit()
        await self.session.refresh(sponsorship)
        return sponsorship

    async def finalize_sponsorship(
        self,
        sponsorship_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Sponsorship | None:
        """Finalize a sponsorship.

        Args:
            sponsorship_id: Sponsorship ID
            start_date: Optional start date override
            end_date: Optional end date override

        Returns:
            Updated sponsorship if found, None otherwise
        """
        sponsorship = await self.get_sponsorship(sponsorship_id)
        if not sponsorship:
            return None

        sponsorship.status = SponsorshipStatus.FINALIZED
        sponsorship.finalized_on = datetime.now(tz=UTC).date()

        if start_date:
            sponsorship.start_date = start_date.date() if isinstance(start_date, datetime) else start_date
        if end_date:
            sponsorship.end_date = end_date.date() if isinstance(end_date, datetime) else end_date

        await self.session.commit()
        await self.session.refresh(sponsorship)
        return sponsorship

    async def get_stats(self) -> dict:
        """Get sponsor statistics.

        Returns:
            Dictionary with sponsor stats
        """
        total_sponsors_query = select(func.count()).select_from(Sponsor)
        total_sponsors_result = await self.session.execute(total_sponsors_query)
        total_sponsors = total_sponsors_result.scalar() or 0

        total_sponsorships_query = select(func.count()).select_from(Sponsorship)
        total_sponsorships_result = await self.session.execute(total_sponsorships_query)
        total_sponsorships = total_sponsorships_result.scalar() or 0

        pending_query = select(func.count()).where(Sponsorship.status == SponsorshipStatus.APPLIED)
        pending_result = await self.session.execute(pending_query)
        pending_sponsorships = pending_result.scalar() or 0

        approved_query = select(func.count()).where(Sponsorship.status == SponsorshipStatus.APPROVED)
        approved_result = await self.session.execute(approved_query)
        approved_sponsorships = approved_result.scalar() or 0

        finalized_query = select(func.count()).where(Sponsorship.status == SponsorshipStatus.FINALIZED)
        finalized_result = await self.session.execute(finalized_query)
        finalized_sponsorships = finalized_result.scalar() or 0

        rejected_query = select(func.count()).where(Sponsorship.status == SponsorshipStatus.REJECTED)
        rejected_result = await self.session.execute(rejected_query)
        rejected_sponsorships = rejected_result.scalar() or 0

        return {
            "total_sponsors": total_sponsors,
            "total_sponsorships": total_sponsorships,
            "pending_sponsorships": pending_sponsorships,
            "approved_sponsorships": approved_sponsorships,
            "finalized_sponsorships": finalized_sponsorships,
            "rejected_sponsorships": rejected_sponsorships,
        }

    async def list_levels(self) -> list[SponsorshipLevel]:
        """List all sponsorship levels.

        Returns:
            List of sponsorship levels ordered by order field
        """
        query = select(SponsorshipLevel).order_by(SponsorshipLevel.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

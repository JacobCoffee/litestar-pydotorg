"""Dashboard service for admin statistics and monitoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from pydotorg.domains.admin.schemas import DashboardStats, PendingModeration, RecentActivity
from pydotorg.domains.events.models import Event
from pydotorg.domains.jobs.models import Job, JobStatus
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipStatus
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DashboardService:
    """Service for admin dashboard statistics and monitoring."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the dashboard service.

        Args:
            session: Database session
        """
        self.session = session

    async def get_stats(self) -> DashboardStats:
        """Get aggregate dashboard statistics.

        Returns:
            Dashboard statistics
        """
        total_users = await self._count_total_users()
        active_users = await self._count_active_users()
        staff_users = await self._count_staff_users()

        total_jobs = await self._count_total_jobs()
        pending_jobs = await self._count_pending_jobs()
        approved_jobs = await self._count_approved_jobs()

        total_events = await self._count_total_events()
        upcoming_events = await self._count_upcoming_events()

        total_sponsors = await self._count_total_sponsors()
        active_sponsors = await self._count_active_sponsors()

        return DashboardStats(
            total_users=total_users,
            active_users=active_users,
            staff_users=staff_users,
            total_jobs=total_jobs,
            pending_jobs=pending_jobs,
            approved_jobs=approved_jobs,
            total_events=total_events,
            upcoming_events=upcoming_events,
            total_sponsors=total_sponsors,
            active_sponsors=active_sponsors,
        )

    async def get_pending_items(self) -> PendingModeration:
        """Get summary of pending moderation items.

        Returns:
            Pending moderation summary
        """
        pending_jobs = await self._count_pending_jobs()
        pending_events = await self._count_pending_events()
        pending_sponsors = await self._count_pending_sponsors()
        recent_signups = await self._count_recent_signups(days=7)

        return PendingModeration(
            pending_jobs_count=pending_jobs,
            pending_events_count=pending_events,
            pending_sponsors_count=pending_sponsors,
            recent_signups_count=recent_signups,
        )

    async def get_recent_activity(self, limit: int = 20) -> list[RecentActivity]:
        """Get recent activity (signups, submissions, approvals).

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of recent activities
        """
        recent_users_stmt = select(User).where(User.is_active == True).order_by(User.date_joined.desc()).limit(limit)  # noqa: E712
        result = await self.session.execute(recent_users_stmt)
        recent_users = result.scalars().all()

        activities = [
            RecentActivity(
                id=user.id,
                activity_type="user_signup",
                description=f"New user registered: {user.username}",
                timestamp=user.date_joined,
                user_id=user.id,
                username=user.username,
            )
            for user in recent_users
        ]

        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]

    async def _count_total_users(self) -> int:
        """Count total registered users."""
        stmt = select(func.count()).select_from(User)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_active_users(self) -> int:
        """Count active users."""
        stmt = select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_staff_users(self) -> int:
        """Count staff and superusers."""
        stmt = select(func.count()).select_from(User).where((User.is_staff == True) | (User.is_superuser == True))  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_total_jobs(self) -> int:
        """Count total job postings."""
        stmt = select(func.count()).select_from(Job)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_pending_jobs(self) -> int:
        """Count pending job postings."""
        stmt = select(func.count()).select_from(Job).where(Job.status == JobStatus.REVIEW)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_approved_jobs(self) -> int:
        """Count approved job postings."""
        stmt = select(func.count()).select_from(Job).where(Job.status == JobStatus.APPROVED)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_total_events(self) -> int:
        """Count total events."""
        stmt = select(func.count()).select_from(Event)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_upcoming_events(self) -> int:
        """Count upcoming events."""
        stmt = select(func.count()).select_from(Event)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_total_sponsors(self) -> int:
        """Count total sponsors."""
        stmt = select(func.count()).select_from(Sponsor)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_active_sponsors(self) -> int:
        """Count sponsors with active sponsorships (finalized and within date range)."""
        today = datetime.now(UTC).date()
        stmt = (
            select(func.count(func.distinct(Sponsorship.sponsor_id)))
            .select_from(Sponsorship)
            .where(
                (Sponsorship.status == SponsorshipStatus.FINALIZED)
                & (Sponsorship.start_date <= today)
                & ((Sponsorship.end_date == None) | (Sponsorship.end_date >= today))  # noqa: E711
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_pending_events(self) -> int:
        """Count pending events (not yet featured)."""
        stmt = select(func.count()).select_from(Event).where(Event.featured == False)  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_pending_sponsors(self) -> int:
        """Count sponsors with pending sponsorship applications (applied status)."""
        stmt = (
            select(func.count(func.distinct(Sponsorship.sponsor_id)))
            .select_from(Sponsorship)
            .where(Sponsorship.status == SponsorshipStatus.APPLIED)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _count_recent_signups(self, days: int = 7) -> int:
        """Count recent user signups.

        Args:
            days: Number of days to look back

        Returns:
            Count of recent signups
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(func.count()).select_from(User).where(User.date_joined >= cutoff)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

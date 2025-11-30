"""Admin download analytics service."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from pydotorg.domains.downloads.models import (
    OS,
    DownloadStatistic,
    Release,
    ReleaseFile,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DownloadAnalyticsService:
    """Service for download analytics in the admin dashboard."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the analytics service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_total_downloads(self) -> int:
        """Get total download count from database.

        Returns:
            Total download count
        """
        result = await self.session.execute(select(func.sum(DownloadStatistic.download_count)))
        return result.scalar() or 0

    async def get_downloads_by_period(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get download counts grouped by date.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: today)

        Returns:
            List of dicts with date and count
        """
        if not end_date:
            end_date = datetime.now(UTC).date()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        result = await self.session.execute(
            select(
                DownloadStatistic.date,
                func.sum(DownloadStatistic.download_count).label("count"),
            )
            .where(DownloadStatistic.date >= start_date)
            .where(DownloadStatistic.date <= end_date)
            .group_by(DownloadStatistic.date)
            .order_by(DownloadStatistic.date)
        )

        return [{"date": row.date.isoformat(), "count": row.count} for row in result]

    async def get_downloads_by_version(self) -> list[dict[str, Any]]:
        """Get download counts grouped by Python version.

        Returns:
            List of dicts with version and count
        """
        result = await self.session.execute(
            select(
                Release.version,
                func.sum(DownloadStatistic.download_count).label("count"),
            )
            .join(ReleaseFile, ReleaseFile.release_id == Release.id)
            .join(DownloadStatistic, DownloadStatistic.release_file_id == ReleaseFile.id)
            .group_by(Release.version)
            .order_by(func.sum(DownloadStatistic.download_count).desc())
        )

        return [{"version": row.version.value, "count": row.count} for row in result]

    async def get_downloads_by_os(self) -> list[dict[str, Any]]:
        """Get download counts grouped by OS.

        Returns:
            List of dicts with OS name and count
        """
        result = await self.session.execute(
            select(
                OS.name,
                func.sum(DownloadStatistic.download_count).label("count"),
            )
            .join(ReleaseFile, ReleaseFile.os_id == OS.id)
            .join(DownloadStatistic, DownloadStatistic.release_file_id == ReleaseFile.id)
            .group_by(OS.name)
            .order_by(func.sum(DownloadStatistic.download_count).desc())
        )

        return [{"os": row.name, "count": row.count} for row in result]

    async def get_top_releases(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top downloaded releases.

        Args:
            limit: Maximum number of releases to return

        Returns:
            List of dicts with release info and count
        """
        result = await self.session.execute(
            select(
                Release.name,
                Release.version,
                func.sum(DownloadStatistic.download_count).label("count"),
            )
            .join(ReleaseFile, ReleaseFile.release_id == Release.id)
            .join(DownloadStatistic, DownloadStatistic.release_file_id == ReleaseFile.id)
            .group_by(Release.id, Release.name, Release.version)
            .order_by(func.sum(DownloadStatistic.download_count).desc())
            .limit(limit)
        )

        return [{"name": row.name, "version": row.version.value, "count": row.count} for row in result]

    async def get_top_files(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top downloaded files.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of dicts with file info and count
        """
        result = await self.session.execute(
            select(
                ReleaseFile.name,
                Release.name.label("release_name"),
                OS.name.label("os_name"),
                func.sum(DownloadStatistic.download_count).label("count"),
            )
            .join(Release, ReleaseFile.release_id == Release.id)
            .join(OS, ReleaseFile.os_id == OS.id)
            .join(DownloadStatistic, DownloadStatistic.release_file_id == ReleaseFile.id)
            .group_by(ReleaseFile.id, ReleaseFile.name, Release.name, OS.name)
            .order_by(func.sum(DownloadStatistic.download_count).desc())
            .limit(limit)
        )

        return [
            {
                "name": row.name,
                "release": row.release_name,
                "os": row.os_name,
                "count": row.count,
            }
            for row in result
        ]

    async def get_recent_downloads(self, days: int = 7) -> int:
        """Get download count for recent period.

        Args:
            days: Number of days to look back

        Returns:
            Download count for the period
        """
        start_date = datetime.now(UTC).date() - timedelta(days=days)
        result = await self.session.execute(
            select(func.sum(DownloadStatistic.download_count)).where(DownloadStatistic.date >= start_date)
        )
        return result.scalar() or 0

    async def get_analytics_summary(self) -> dict[str, Any]:
        """Get comprehensive analytics summary for dashboard.

        Returns:
            Dict with all analytics data
        """
        today = datetime.now(UTC).date()
        month_ago = today - timedelta(days=30)

        return {
            "total_downloads": await self.get_total_downloads(),
            "downloads_this_week": await self.get_recent_downloads(7),
            "downloads_this_month": await self.get_recent_downloads(30),
            "downloads_by_day": await self.get_downloads_by_period(month_ago, today),
            "downloads_by_version": await self.get_downloads_by_version(),
            "downloads_by_os": await self.get_downloads_by_os(),
            "top_releases": await self.get_top_releases(10),
            "top_files": await self.get_top_files(10),
        }

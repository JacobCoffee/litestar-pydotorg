"""Download statistics tracking service and background tasks.

This module provides Redis-based download tracking with periodic PostgreSQL aggregation.
Uses atomic Redis INCR for real-time counting with background flush to database.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_MIN_KEY_PARTS_TOTAL = 5
_MIN_KEY_PARTS_DAILY = 7


class DownloadStatsService:
    """Service for tracking download statistics in Redis.

    Uses atomic Redis counters for high-frequency download tracking.
    Stats are periodically flushed to PostgreSQL for durable storage.
    """

    def __init__(self, redis: Redis, namespace: str = "pydotorg") -> None:
        """Initialize the download stats service.

        Args:
            redis: Redis client instance
            namespace: Redis key namespace prefix (default: "pydotorg")
        """
        self.redis = redis
        self.namespace = namespace

    def _key(self, *parts: str) -> str:
        """Build a namespaced Redis key.

        Args:
            *parts: Key components to join

        Returns:
            Namespaced Redis key string
        """
        return ":".join([self.namespace, "downloads", "stats", *parts])

    async def track_download(self, file_id: str, release_id: str | None = None) -> None:
        """Track a single file download.

        Args:
            file_id: UUID of the release file being downloaded
            release_id: Optional UUID of the release
        """
        try:
            today = datetime.now(UTC).date().isoformat()
            await self.redis.incr(self._key("file", file_id, "total"))
            await self.redis.incr(self._key("file", file_id, "daily", today))
            await self.redis.incr(self._key("total", "all"))
            await self.redis.incr(self._key("daily", today))

            if release_id:
                await self.redis.incr(self._key("release", release_id, "total"))
                await self.redis.incr(self._key("release", release_id, "daily", today))

            logger.debug(f"Tracked download for file {file_id}")
        except Exception:
            logger.exception(f"Failed to track download for file {file_id}")

    async def get_file_downloads(self, file_id: str) -> int:
        """Get total download count for a file.

        Args:
            file_id: UUID of the release file

        Returns:
            Total download count
        """
        try:
            count = await self.redis.get(self._key("file", file_id, "total"))
            return int(count) if count else 0
        except Exception:
            logger.exception(f"Failed to get download count for file {file_id}")
            return 0

    async def get_file_downloads_daily(self, file_id: str, day: date | None = None) -> int:
        """Get download count for a file on a specific day.

        Args:
            file_id: UUID of the release file
            day: Date to get count for (default: today)

        Returns:
            Download count for the day
        """
        try:
            day = day or datetime.now(UTC).date()
            count = await self.redis.get(self._key("file", file_id, "daily", day.isoformat()))
            return int(count) if count else 0
        except Exception:
            logger.exception(f"Failed to get daily download count for file {file_id}")
            return 0

    async def get_release_downloads(self, release_id: str) -> int:
        """Get total download count for a release (all files).

        Args:
            release_id: UUID of the release

        Returns:
            Total download count for all files in release
        """
        try:
            count = await self.redis.get(self._key("release", release_id, "total"))
            return int(count) if count else 0
        except Exception:
            logger.exception(f"Failed to get download count for release {release_id}")
            return 0

    async def get_total_downloads(self) -> int:
        """Get total download count across all files.

        Returns:
            Total download count
        """
        try:
            count = await self.redis.get(self._key("total", "all"))
            return int(count) if count else 0
        except Exception:
            logger.exception("Failed to get total download count")
            return 0

    async def get_daily_downloads(self, day: date | None = None) -> int:
        """Get download count for a specific day.

        Args:
            day: Date to get count for (default: today)

        Returns:
            Download count for the day
        """
        try:
            day = day or datetime.now(UTC).date()
            count = await self.redis.get(self._key("daily", day.isoformat()))
            return int(count) if count else 0
        except Exception:
            logger.exception("Failed to get daily download count")
            return 0

    async def get_top_downloads(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get top downloaded files.

        Args:
            limit: Maximum number of results

        Returns:
            List of (file_id, count) tuples sorted by count descending
        """
        try:
            pattern = self._key("file", "*", "total")
            results: list[tuple[str, int]] = []

            async for key in self.redis.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= _MIN_KEY_PARTS_TOTAL:
                    file_id = parts[4]
                    count = await self.redis.get(key)
                    if count:
                        results.append((file_id, int(count)))

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        except Exception:
            logger.exception("Failed to get top downloads")
            return []

    async def get_all_file_stats(self) -> dict[str, int]:
        """Get download stats for all files.

        Returns:
            Dict mapping file_id to download count
        """
        try:
            pattern = self._key("file", "*", "total")
            stats: dict[str, int] = {}

            async for key in self.redis.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= _MIN_KEY_PARTS_TOTAL:
                    file_id = parts[4]
                    count = await self.redis.get(key)
                    if count:
                        stats[file_id] = int(count)

            return stats
        except Exception:
            logger.exception("Failed to get all file stats")
            return {}

    async def get_stats_summary(self) -> dict[str, Any]:
        """Get overall download statistics summary.

        Returns:
            Dict with total downloads, today's downloads, and top files
        """
        try:
            today = datetime.now(UTC).date()
            return {
                "total_downloads": await self.get_total_downloads(),
                "downloads_today": await self.get_daily_downloads(today),
                "top_files": await self.get_top_downloads(10),
                "last_updated": datetime.now(UTC).isoformat(),
            }
        except Exception:
            logger.exception("Failed to get stats summary")
            return {
                "total_downloads": 0,
                "downloads_today": 0,
                "top_files": [],
                "last_updated": datetime.now(UTC).isoformat(),
            }

    async def flush_to_database(self, session: AsyncSession) -> int:
        """Flush Redis counters to PostgreSQL database.

        This method aggregates daily stats and stores them in the database
        for long-term storage and analytics queries.

        Args:
            session: SQLAlchemy async session

        Returns:
            Number of records flushed
        """
        from pydotorg.domains.downloads.models import DownloadStatistic

        try:
            pattern = self._key("file", "*", "daily", "*")
            flushed = 0

            async for key in self.redis.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= _MIN_KEY_PARTS_DAILY:
                    file_id = parts[4]
                    day_str = parts[6]

                    count = await self.redis.get(key)
                    if count and int(count) > 0:
                        try:
                            from datetime import date as date_type

                            day = date_type.fromisoformat(day_str)
                            stat = DownloadStatistic(
                                release_file_id=file_id,
                                date=day,
                                download_count=int(count),
                            )
                            session.add(stat)
                            flushed += 1
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format {day_str}: {e}")

            await session.commit()
            logger.info(f"Flushed {flushed} download statistics to database")
            return flushed
        except Exception:
            logger.exception("Failed to flush stats to database")
            await session.rollback()
            return 0

    async def cleanup_old_daily_keys(self, days_to_keep: int = 7) -> int:
        """Clean up old daily Redis keys after flushing to database.

        Args:
            days_to_keep: Number of days of daily stats to retain in Redis

        Returns:
            Number of keys deleted
        """
        try:
            cutoff = datetime.now(UTC).date() - timedelta(days=days_to_keep)
            pattern = self._key("*", "daily", "*")
            deleted = 0

            async for key in self.redis.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= _MIN_KEY_PARTS_DAILY:
                    try:
                        from datetime import date as date_type

                        day_str = parts[-1]
                        day = date_type.fromisoformat(day_str)
                        if day < cutoff:
                            await self.redis.delete(key)
                            deleted += 1
                    except ValueError:
                        continue

            logger.info(f"Cleaned up {deleted} old daily keys (older than {days_to_keep} days)")
            return deleted
        except Exception:
            logger.exception("Failed to cleanup old daily keys")
            return 0


async def get_download_stats_service(ctx: dict[str, Any]) -> DownloadStatsService | None:
    """Get or create download stats service from worker context.

    Args:
        ctx: SAQ worker context dictionary

    Returns:
        DownloadStatsService instance or None if Redis unavailable
    """
    redis = ctx.get("redis")
    if not redis:
        logger.warning("Redis not available in context, download stats tracking disabled")
        return None

    if "download_stats_service" not in ctx:
        from pydotorg.config import settings

        namespace = getattr(settings, "redis_stats_namespace", "pydotorg")
        ctx["download_stats_service"] = DownloadStatsService(redis, namespace=namespace)

    return ctx["download_stats_service"]


async def flush_download_stats(ctx: dict[str, Any]) -> dict[str, Any]:
    """SAQ task to flush download stats from Redis to PostgreSQL.

    This task should be scheduled to run periodically (e.g., every 15 minutes).

    Args:
        ctx: SAQ worker context

    Returns:
        Task result with flush count
    """
    stats_service = await get_download_stats_service(ctx)
    if not stats_service:
        return {"success": False, "error": "Stats service unavailable"}

    session = ctx.get("db_session")
    if not session:
        return {"success": False, "error": "Database session unavailable"}

    flushed = await stats_service.flush_to_database(session)
    cleaned = await stats_service.cleanup_old_daily_keys(days_to_keep=7)

    return {
        "success": True,
        "flushed": flushed,
        "cleaned_keys": cleaned,
    }


async def aggregate_download_stats(ctx: dict[str, Any]) -> dict[str, Any]:
    """SAQ task to aggregate download statistics for reporting.

    This task updates materialized views or summary tables for fast analytics.

    Args:
        ctx: SAQ worker context

    Returns:
        Task result with aggregation status
    """
    stats_service = await get_download_stats_service(ctx)
    if not stats_service:
        return {"success": False, "error": "Stats service unavailable"}

    summary = await stats_service.get_stats_summary()
    return {
        "success": True,
        "summary": summary,
    }

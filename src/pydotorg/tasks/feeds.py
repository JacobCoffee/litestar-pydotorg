"""Feed aggregation background tasks for SAQ."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from saq.job import CronJob

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

logger = logging.getLogger(__name__)


async def refresh_all_feeds(ctx: Mapping[str, Any]) -> dict[str, int]:
    """Refresh all active feeds.

    This task fetches and parses all active RSS feeds, creating or updating
    BlogEntry records for each feed item.

    Args:
        ctx: Task context containing dependencies (session_maker, etc.).

    Returns:
        Dict with success_count and error_count.
    """
    from pydotorg.domains.blogs.services import FeedService  # noqa: PLC0415

    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            feed_service = FeedService(session=session)
            feeds = await feed_service.get_active_feeds(limit=1000)
            logger.info(f"Refreshing {len(feeds)} active feeds")

            success_count = 0
            error_count = 0

            for feed in feeds:
                feed_name = feed.name
                try:
                    entries = await feed_service.fetch_feed(feed)
                    success_count += 1
                    logger.info(f"Successfully refreshed feed '{feed_name}' - {len(entries)} entries")
                except Exception:
                    error_count += 1
                    logger.exception(f"Failed to refresh stale feed '{feed_name}'")

            logger.info(f"Feed refresh complete: {success_count} successful, {error_count} errors")

            return {
                "success_count": success_count,
                "error_count": error_count,
                "total_feeds": len(feeds),
            }

    except Exception:
        logger.exception("Critical error in refresh_all_feeds task")
        raise


async def refresh_stale_feeds(ctx: Mapping[str, Any], *, max_age_hours: int = 1) -> dict[str, int]:
    """Refresh only feeds that haven't been updated recently.

    This task is more efficient than refresh_all_feeds as it only processes
    feeds that are older than the specified max_age.

    Args:
        ctx: Task context containing dependencies.
        max_age_hours: Only refresh feeds not fetched in this many hours.

    Returns:
        Dict with success_count, error_count, and cutoff_time.
    """
    from pydotorg.domains.blogs.services import FeedService  # noqa: PLC0415

    session_maker = ctx["session_maker"]

    try:
        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)

        async with session_maker() as session:
            feed_service = FeedService(session=session)
            feeds = await feed_service.get_feeds_needing_update(cutoff_time=cutoff_time, limit=1000)

            logger.info(
                f"Refreshing {len(feeds)} stale feeds (older than {max_age_hours}h, cutoff: {cutoff_time.isoformat()})"
            )

            success_count = 0
            error_count = 0

            for feed in feeds:
                feed_name = feed.name
                try:
                    entries = await feed_service.fetch_feed(feed)
                    success_count += 1
                    logger.info(f"Successfully refreshed stale feed '{feed_name}' - {len(entries)} entries")
                except Exception:
                    error_count += 1
                    logger.exception(f"Failed to refresh stale feed '{feed_name}'")

            logger.info(f"Stale feed refresh complete: {success_count} successful, {error_count} errors")

            return {
                "success_count": success_count,
                "error_count": error_count,
                "total_feeds": len(feeds),
                "cutoff_time": cutoff_time.isoformat(),
                "max_age_hours": max_age_hours,
            }

    except Exception:
        logger.exception("Critical error in refresh_stale_feeds task")
        raise


async def refresh_single_feed(ctx: Mapping[str, Any], *, feed_id: str) -> dict[str, Any]:
    """Refresh a specific feed by ID.

    This task is useful for on-demand feed refresh triggered by user actions
    or administrative tasks.

    Args:
        ctx: Task context containing dependencies.
        feed_id: UUID of the feed to refresh (as string).

    Returns:
        Dict with feed info and entry count.
    """
    from pydotorg.domains.blogs.services import FeedService  # noqa: PLC0415

    session_maker = ctx["session_maker"]

    try:
        feed_uuid = UUID(feed_id)
        logger.info(f"Refreshing single feed: {feed_id}")

        async with session_maker() as session:
            feed_service = FeedService(session=session)

            feed = await feed_service.get(feed_uuid)
            if not feed:
                error_msg = f"Feed {feed_id} not found"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "feed_id": feed_id,
                }

            if not feed.is_active:
                error_msg = f"Feed {feed_id} is not active"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "feed_id": feed_id,
                    "feed_name": feed.name,
                }

            entries = await feed_service.fetch_feed(feed)
            logger.info(f"Successfully refreshed feed '{feed.name}' - {len(entries)} entries")

            return {
                "success": True,
                "feed_id": feed_id,
                "feed_name": feed.name,
                "entry_count": len(entries),
                "last_fetched": feed.last_fetched.isoformat() if feed.last_fetched else None,
            }

    except ValueError:
        error_msg = f"Invalid feed_id format: {feed_id}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "feed_id": feed_id,
        }
    except Exception:
        logger.exception(f"Failed to refresh feed {feed_id}")
        raise


cron_refresh_feeds = CronJob(
    refresh_stale_feeds,
    cron="*/15 * * * *",
    kwargs={"max_age_hours": 1},
    timeout=600,
)

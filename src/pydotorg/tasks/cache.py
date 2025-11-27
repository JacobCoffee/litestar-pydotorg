"""Cache warming background tasks for SAQ."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from saq import CronJob

from pydotorg.domains.admin.services.pages import PageAdminService
from pydotorg.domains.blogs.services import BlogEntryService
from pydotorg.domains.downloads.services import ReleaseService
from pydotorg.domains.events.services import EventService

if TYPE_CHECKING:
    from redis.asyncio import Redis

Context = dict[str, Any]

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "pydotorg:cache"
TTL_HOMEPAGE = 300
TTL_RELEASES = 3600
TTL_EVENTS = 900
TTL_BLOGS = 1800
TTL_PAGES = 600


async def _get_redis(ctx: Context) -> Redis:
    """Get Redis client from context.

    Args:
        ctx: SAQ context containing Redis connection.

    Returns:
        Redis client instance.
    """
    return ctx["redis"]


def _get_session_maker(ctx: Context):
    """Get database session maker from context.

    Args:
        ctx: SAQ context containing session maker.

    Returns:
        Session maker callable.
    """
    return ctx["session_maker"]


async def _get_db_session(ctx: Context):
    """Get a database session from context.

    Args:
        ctx: SAQ context containing session maker.

    Returns:
        Database session instance.
    """
    session_maker = _get_session_maker(ctx)
    return session_maker()


async def _set_cache(
    redis: Redis,
    key: str,
    value: Any,
    ttl: int = 300,
) -> None:
    """Set cache value with TTL.

    Args:
        redis: Redis client.
        key: Cache key with prefix.
        value: Value to cache (will be JSON serialized).
        ttl: Time-to-live in seconds.
    """
    try:
        serialized = json.dumps(value, default=str)
        await redis.set(key, serialized, ex=ttl)
        logger.debug(f"Cached {key} with TTL {ttl}s")
    except Exception:
        logger.exception(f"Failed to cache {key}")


async def _get_cache(redis: Redis, key: str) -> Any | None:
    """Get cache value.

    Args:
        redis: Redis client.
        key: Cache key with prefix.

    Returns:
        Cached value or None if not found.
    """
    try:
        data = await redis.get(key)
        if data:
            return json.loads(data)
    except Exception:
        logger.exception(f"Failed to get cache {key}")
    return None


def _make_key(*parts: str) -> str:
    """Build cache key with prefix.

    Args:
        *parts: Key components to join.

    Returns:
        Full cache key.
    """
    return f"{CACHE_KEY_PREFIX}:{':'.join(parts)}"


async def warm_homepage_cache(ctx: Context) -> dict[str, int]:
    """Pre-cache homepage data for fast page loads.

    Caches:
    - Recent blog entries (3)
    - Upcoming events (3)
    - Latest Python release

    Args:
        ctx: SAQ context.

    Returns:
        Statistics about cached items.
    """
    redis = await _get_redis(ctx)
    session_maker = _get_session_maker(ctx)

    cached_count = 0
    errors = 0

    async with session_maker() as session:
        try:
            blog_service = BlogEntryService(session=session)
            recent_blogs = await blog_service.get_recent_entries(limit=3)
            blog_data = [
                {
                    "id": str(entry.id),
                    "title": entry.title,
                    "summary": entry.summary,
                    "url": entry.url,
                    "pub_date": entry.pub_date.isoformat(),
                }
                for entry in recent_blogs
            ]
            await _set_cache(redis, _make_key("homepage", "recent_blogs"), blog_data, TTL_HOMEPAGE)
            cached_count += 1
        except Exception:
            logger.exception("Failed to cache homepage blogs")
            errors += 1

        try:
            event_service = EventService(session=session)
            upcoming_events = await event_service.get_upcoming(limit=3)
            event_data = [
                {
                    "id": str(event.id),
                    "name": event.name,
                    "title": event.title,
                    "description": event.description,
                    "featured": event.featured,
                }
                for event in upcoming_events
            ]
            await _set_cache(redis, _make_key("homepage", "upcoming_events"), event_data, TTL_HOMEPAGE)
            cached_count += 1
        except Exception:
            logger.exception("Failed to cache homepage events")
            errors += 1

        try:
            release_service = ReleaseService(session=session)
            latest_release = await release_service.get_latest()
            if latest_release:
                release_data = {
                    "id": str(latest_release.id),
                    "name": latest_release.name,
                    "slug": latest_release.slug,
                    "version": str(latest_release.version),
                    "is_latest": latest_release.is_latest,
                    "release_date": latest_release.release_date.isoformat(),
                }
                await _set_cache(redis, _make_key("homepage", "latest_release"), release_data, TTL_HOMEPAGE)
                cached_count += 1
        except Exception:
            logger.exception("Failed to cache latest release")
            errors += 1

    logger.info(f"Homepage cache warmed: {cached_count} items cached, {errors} errors")
    return {"cached": cached_count, "errors": errors}


async def warm_releases_cache(ctx: Context) -> dict[str, int]:
    """Cache Python releases data.

    Caches:
    - Latest stable release
    - All published releases
    - Download page releases

    Args:
        ctx: SAQ context.

    Returns:
        Statistics about cached items.
    """
    redis = await _get_redis(ctx)
    session = await _get_db_session(ctx)

    cached_count = 0
    errors = 0

    try:
        release_service = ReleaseService(session=session)

        latest_release = await release_service.get_latest()
        if latest_release:
            release_data = {
                "id": str(latest_release.id),
                "name": latest_release.name,
                "slug": latest_release.slug,
                "version": str(latest_release.version),
                "is_latest": latest_release.is_latest,
                "release_date": latest_release.release_date.isoformat(),
                "release_page": latest_release.release_page,
            }
            await _set_cache(redis, _make_key("releases", "latest"), release_data, TTL_RELEASES)
            cached_count += 1
    except Exception:
        logger.exception("Failed to cache latest release")
        errors += 1

    try:
        release_service = ReleaseService(session=session)
        published_releases = await release_service.get_published(limit=50)
        releases_data = [
            {
                "id": str(release.id),
                "name": release.name,
                "slug": release.slug,
                "version": str(release.version),
                "is_latest": release.is_latest,
                "release_date": release.release_date.isoformat(),
            }
            for release in published_releases
        ]
        await _set_cache(redis, _make_key("releases", "all_published"), releases_data, TTL_RELEASES)
        cached_count += 1
    except Exception:
        logger.exception("Failed to cache published releases")
        errors += 1

    try:
        release_service = ReleaseService(session=session)
        download_releases = await release_service.get_for_download_page(limit=20)
        download_data = [
            {
                "id": str(release.id),
                "name": release.name,
                "slug": release.slug,
                "version": str(release.version),
                "release_date": release.release_date.isoformat(),
            }
            for release in download_releases
        ]
        await _set_cache(redis, _make_key("releases", "download_page"), download_data, TTL_RELEASES)
        cached_count += 1
    except Exception:
        logger.exception("Failed to cache download page releases")
        errors += 1

    logger.info(f"Releases cache warmed: {cached_count} items cached, {errors} errors")
    return {"cached": cached_count, "errors": errors}


async def warm_events_cache(ctx: Context) -> dict[str, int]:
    """Cache upcoming events data.

    Caches:
    - Next 30 days of events
    - Featured events

    Args:
        ctx: SAQ context.

    Returns:
        Statistics about cached items.
    """
    redis = await _get_redis(ctx)
    session = await _get_db_session(ctx)

    cached_count = 0
    errors = 0

    try:
        event_service = EventService(session=session)
        start_date = datetime.now(tz=UTC)
        upcoming_events = await event_service.get_upcoming(start_date=start_date, limit=50)
        event_data = [
            {
                "id": str(event.id),
                "name": event.name,
                "slug": event.slug,
                "title": event.title,
                "description": event.description,
                "featured": event.featured,
            }
            for event in upcoming_events
        ]
        await _set_cache(redis, _make_key("events", "upcoming_30days"), event_data, TTL_EVENTS)
        cached_count += 1
    except Exception:
        logger.exception("Failed to cache upcoming events")
        errors += 1

    try:
        event_service = EventService(session=session)
        featured_events = await event_service.get_featured(limit=10)
        featured_data = [
            {
                "id": str(event.id),
                "name": event.name,
                "slug": event.slug,
                "title": event.title,
                "description": event.description,
            }
            for event in featured_events
        ]
        await _set_cache(redis, _make_key("events", "featured"), featured_data, TTL_EVENTS)
        cached_count += 1
    except Exception:
        logger.exception("Failed to cache featured events")
        errors += 1

    logger.info(f"Events cache warmed: {cached_count} items cached, {errors} errors")
    return {"cached": cached_count, "errors": errors}


async def warm_blogs_cache(ctx: Context) -> dict[str, int]:
    """Cache blog content.

    Caches:
    - Recent blog entries (20)

    Args:
        ctx: SAQ context.

    Returns:
        Statistics about cached items.
    """
    redis = await _get_redis(ctx)
    session = await _get_db_session(ctx)

    cached_count = 0
    errors = 0

    try:
        blog_service = BlogEntryService(session=session)
        recent_entries = await blog_service.get_recent_entries(limit=20)
        blog_data = [
            {
                "id": str(entry.id),
                "title": entry.title,
                "summary": entry.summary,
                "url": entry.url,
                "pub_date": entry.pub_date.isoformat(),
                "feed_id": str(entry.feed_id),
            }
            for entry in recent_entries
        ]
        await _set_cache(redis, _make_key("blogs", "recent_20"), blog_data, TTL_BLOGS)
        cached_count += 1
    except Exception:
        logger.exception("Failed to cache recent blogs")
        errors += 1

    logger.info(f"Blogs cache warmed: {cached_count} items cached, {errors} errors")
    return {"cached": cached_count, "errors": errors}


async def warm_pages_cache(
    ctx: Context,
    *,
    page_paths: list[str] | None = None,
) -> dict[str, int]:
    """Cache specific pages by path.

    Default high-traffic pages:
    - Homepage
    - Downloads
    - About
    - Community

    Args:
        ctx: SAQ context.
        page_paths: Optional list of page paths to cache.

    Returns:
        Statistics about cached items.
    """
    redis = await _get_redis(ctx)
    session = await _get_db_session(ctx)

    if page_paths is None:
        page_paths = ["/", "/downloads", "/about", "/community"]

    cached_count = 0
    errors = 0

    page_service = PageAdminService(session=session)

    for path in page_paths:
        try:
            page = await page_service.get_page_by_path(path)
            if page and page.is_published:
                page_data = {
                    "id": str(page.id),
                    "title": page.title,
                    "path": page.path,
                    "content": page.content,
                    "content_type": page.content_type.value,
                    "description": page.description,
                }
                await _set_cache(redis, _make_key("pages", "path", path.lstrip("/")), page_data, TTL_PAGES)
                cached_count += 1
        except Exception:
            logger.exception(f"Failed to cache page {path}")
            errors += 1

    logger.info(f"Pages cache warmed: {cached_count} items cached, {errors} errors")
    return {"cached": cached_count, "errors": errors}


async def clear_cache(
    ctx: Context,
    *,
    pattern: str = "*",
) -> dict[str, int]:
    """Clear cache by pattern using SCAN + DEL.

    Args:
        ctx: SAQ context.
        pattern: Redis key pattern to match (default: all pydotorg cache keys).

    Returns:
        Count of cleared keys.
    """
    redis = await _get_redis(ctx)

    full_pattern = f"{CACHE_KEY_PREFIX}:{pattern}"
    cleared = 0

    try:
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=full_pattern, count=100)
            if keys:
                await redis.delete(*keys)
                cleared += len(keys)
            if cursor == 0:
                break

        logger.info(f"Cache cleared: {cleared} keys matching pattern '{full_pattern}'")
    except Exception:
        logger.exception(f"Failed to clear cache with pattern {full_pattern}")

    return {"cleared": cleared}


async def get_cache_stats(ctx: Context) -> dict[str, Any]:
    """Get cache statistics.

    Returns:
    - Total key count
    - Memory usage
    - Hit/miss rates if available

    Args:
        ctx: SAQ context.

    Returns:
        Cache statistics dictionary.
    """
    redis = await _get_redis(ctx)

    stats = {
        "total_keys": 0,
        "pydotorg_keys": 0,
        "memory_used": "unknown",
        "memory_peak": "unknown",
    }

    try:
        info = await redis.info("stats")
        stats["keyspace_hits"] = info.get("keyspace_hits", 0)
        stats["keyspace_misses"] = info.get("keyspace_misses", 0)

        total_ops = stats["keyspace_hits"] + stats["keyspace_misses"]
        if total_ops > 0:
            stats["hit_rate"] = round(stats["keyspace_hits"] / total_ops * 100, 2)
        else:
            stats["hit_rate"] = 0.0
    except Exception:
        logger.exception("Failed to get cache hit/miss stats")

    try:
        memory_info = await redis.info("memory")
        stats["memory_used"] = memory_info.get("used_memory_human", "unknown")
        stats["memory_peak"] = memory_info.get("used_memory_peak_human", "unknown")
    except Exception:
        logger.exception("Failed to get memory stats")

    try:
        cursor = 0
        total_keys = 0
        pydotorg_keys = 0

        while True:
            cursor, keys = await redis.scan(cursor, count=1000)
            total_keys += len(keys)
            pydotorg_keys += sum(1 for key in keys if key.decode("utf-8").startswith(CACHE_KEY_PREFIX))
            if cursor == 0:
                break

        stats["total_keys"] = total_keys
        stats["pydotorg_keys"] = pydotorg_keys
    except Exception:
        logger.exception("Failed to count keys")

    logger.info(f"Cache stats: {stats}")
    return stats


cron_warm_homepage_cache = CronJob(
    function=warm_homepage_cache,
    cron="*/5 * * * *",
    timeout=60,
)

cron_warm_releases_cache = CronJob(
    function=warm_releases_cache,
    cron="0 * * * *",
    timeout=120,
)

"""SAQ worker configuration for async task processing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from saq import Queue

from pydotorg.config import settings
from pydotorg.core.database.base import AuditBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

queue = Queue.from_url(settings.redis_url)


async def startup(ctx: dict[str, Any]) -> None:
    """Initialize worker resources on startup.

    Sets up database engine, session maker, and Redis client
    that will be available throughout worker lifecycle.

    Args:
        ctx: SAQ worker context dictionary for storing shared resources
    """
    logger.info("SAQ worker starting up...")

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=str(settings.database_url),
        metadata=AuditBase.metadata,
        create_all=False,
    )

    engine = sqlalchemy_config.get_engine()
    session_maker = sqlalchemy_config.create_session_maker()

    ctx["engine"] = engine
    ctx["session_maker"] = session_maker

    from redis.asyncio import Redis  # noqa: PLC0415

    redis_client = Redis.from_url(settings.redis_url, decode_responses=False)
    ctx["redis"] = redis_client

    logger.info(
        "SAQ worker initialized",
        extra={
            "database_url": str(settings.database_url).split("@")[-1],
            "redis_url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url,
            "concurrency": settings.worker_concurrency,
        },
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    """Cleanup worker resources on shutdown.

    Properly disposes database engine, closes Redis connection,
    and cleans up any other resources.

    Args:
        ctx: SAQ worker context dictionary
    """
    logger.info("SAQ worker shutting down...")

    engine: AsyncEngine | None = ctx.get("engine")
    if engine:
        await engine.dispose()
        logger.info("Database engine disposed")

    redis = ctx.get("redis")
    if redis:
        await redis.aclose()
        logger.info("Redis connection closed")

    logger.info("SAQ worker shutdown complete")


async def before_process(ctx: dict[str, Any]) -> None:
    """Hook called before processing each task.

    Logs task execution start and can be used for per-task setup.

    Args:
        ctx: SAQ worker context dictionary
    """
    job = ctx.get("job")
    if job:
        logger.info(
            "Processing task",
            extra={
                "task_name": job.function,
                "task_id": job.key,
                "attempts": job.attempts,
            },
        )


async def after_process(ctx: dict[str, Any]) -> None:
    """Hook called after processing each task.

    Logs task completion and can be used for cleanup.

    Args:
        ctx: SAQ worker context dictionary
    """
    job = ctx.get("job")
    if job:
        logger.info(
            "Task completed",
            extra={
                "task_name": job.function,
                "task_id": job.key,
            },
        )


async def test_failing_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """A test task that always fails with a traceback for debugging purposes.

    Args:
        ctx: SAQ worker context.

    Returns:
        Never returns - always raises.

    Raises:
        RuntimeError: Always raises to test error handling.
    """

    def level_5_deepest(data: dict[str, Any]) -> None:
        """Deepest level - raises the actual error."""
        value = data.get("key", "default")
        msg = f"Test failure in level_5_deepest: Processing failed for value '{value}'"
        raise RuntimeError(msg)

    def level_4_processor(items: list[str]) -> None:
        """Level 4 - processes items."""
        for i, item in enumerate(items):
            if i == 2:
                level_5_deepest({"key": item, "index": i})

    def level_3_validator(config: dict[str, Any]) -> None:
        """Level 3 - validates configuration."""
        items = config.get("items", [])
        level_4_processor(items)

    def level_2_handler(request_data: dict[str, Any]) -> None:
        """Level 2 - handles the request."""
        config = {"items": ["alpha", "beta", "gamma", "delta"], "timeout": 30}
        config.update(request_data)
        level_3_validator(config)

    def level_1_entry(ctx: dict[str, Any]) -> None:
        """Level 1 - entry point."""
        request_data = {"source": "test_failing_task", "timestamp": "2024-01-01T00:00:00Z"}
        level_2_handler(request_data)

    level_1_entry(ctx)
    return {"status": "should never reach here"}


def get_task_functions() -> list[Callable[..., Any]]:
    """Get all task functions dynamically to avoid circular imports."""
    from pydotorg.tasks.cache import (  # noqa: PLC0415
        clear_cache,
        get_cache_stats,
        warm_blogs_cache,
        warm_events_cache,
        warm_homepage_cache,
        warm_pages_cache,
        warm_releases_cache,
    )
    from pydotorg.tasks.email import (  # noqa: PLC0415
        send_bulk_email,
        send_event_reminder_email,
        send_job_approved_email,
        send_job_rejected_email,
        send_password_reset_email,
        send_verification_email,
    )
    from pydotorg.tasks.events import check_event_reminders, cleanup_past_occurrences  # noqa: PLC0415
    from pydotorg.tasks.feeds import (  # noqa: PLC0415
        refresh_all_feeds,
        refresh_single_feed,
        refresh_stale_feeds,
    )
    from pydotorg.tasks.jobs import archive_old_jobs, cleanup_draft_jobs, expire_jobs  # noqa: PLC0415
    from pydotorg.tasks.search import (  # noqa: PLC0415
        index_all_blogs,
        index_all_events,
        index_all_jobs,
        index_all_pages,
        index_blog_entry,
        index_content,
        index_event,
        index_job,
        index_page,
        rebuild_search_index,
        remove_job_from_index,
    )

    return [
        archive_old_jobs,
        check_event_reminders,
        cleanup_draft_jobs,
        cleanup_past_occurrences,
        clear_cache,
        expire_jobs,
        get_cache_stats,
        index_all_blogs,
        index_all_events,
        index_all_jobs,
        index_all_pages,
        index_blog_entry,
        index_content,
        index_event,
        index_job,
        index_page,
        rebuild_search_index,
        refresh_all_feeds,
        refresh_single_feed,
        refresh_stale_feeds,
        remove_job_from_index,
        send_bulk_email,
        send_event_reminder_email,
        send_job_approved_email,
        send_job_rejected_email,
        send_password_reset_email,
        send_verification_email,
        test_failing_task,
        warm_blogs_cache,
        warm_events_cache,
        warm_homepage_cache,
        warm_pages_cache,
        warm_releases_cache,
    ]


def get_cron_jobs() -> list[Any]:
    """Get all cron jobs dynamically to avoid circular imports."""
    from pydotorg.tasks.cache import (  # noqa: PLC0415
        cron_warm_homepage_cache,
        cron_warm_releases_cache,
    )
    from pydotorg.tasks.events import (  # noqa: PLC0415
        cron_cleanup_past_occurrences,
        cron_event_reminders,
    )
    from pydotorg.tasks.feeds import cron_refresh_feeds  # noqa: PLC0415
    from pydotorg.tasks.jobs import (  # noqa: PLC0415
        cron_archive_old_jobs,
        cron_cleanup_draft_jobs,
        cron_expire_jobs,
    )
    from pydotorg.tasks.search import cron_rebuild_indexes  # noqa: PLC0415

    return [
        cron_archive_old_jobs,
        cron_cleanup_draft_jobs,
        cron_cleanup_past_occurrences,
        cron_event_reminders,
        cron_expire_jobs,
        cron_rebuild_indexes,
        cron_refresh_feeds,
        cron_warm_homepage_cache,
        cron_warm_releases_cache,
    ]


TASK_FUNCTIONS: list[Callable[..., Any]] = []
CRON_JOBS: list[Any] = []

# SAQ worker settings - use with: uv run saq pydotorg.tasks.worker.saq_settings
saq_settings = {
    "queue": queue,
    "functions": get_task_functions(),
    "concurrency": settings.worker_concurrency,
    "cron_jobs": get_cron_jobs(),
    "startup": startup,
    "shutdown": shutdown,
    "before_process": before_process,
    "after_process": after_process,
}

"""SAQ worker configuration for async task processing."""

from __future__ import annotations

import logging
import os
import sys
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


def _mask_url(url: str) -> str:
    """Mask sensitive parts of URLs for display."""
    if "@" in url:
        protocol, rest = url.split("://", 1) if "://" in url else ("", url)
        if "@" in rest:
            _, host_part = rest.rsplit("@", 1)
            return f"{protocol}://*****@{host_part}" if protocol else f"*****@{host_part}"
    return url


def _print_startup_banner(task_count: int, cron_count: int) -> None:
    """Print a nice startup banner for the worker."""
    db_display = _mask_url(str(settings.database_url))
    redis_display = _mask_url(settings.redis_url)

    banner = f"""
\033[94m╔══════════════════════════════════════════════════════════════╗
║                \033[93m⚡ Python.org Task Worker ⚡\033[94m                  ║
╚══════════════════════════════════════════════════════════════╝\033[0m

\033[1mWorker Configuration:\033[0m
  PID:              {os.getpid()}
  Concurrency:      {settings.worker_concurrency} workers
  Tasks:            {task_count} registered
  Cron Jobs:        {cron_count} scheduled

\033[1mConnections:\033[0m
  Database:         {db_display}
  Redis:            {redis_display}

\033[1mEnvironment:\033[0m
  Mode:             {settings.environment.upper()}
  Debug:            {settings.debug}
  Log Level:        {settings.log_level}

\033[92m✓ Worker ready and listening for tasks...\033[0m
"""
    sys.stdout.write(banner)
    sys.stdout.flush()


async def startup(ctx: dict[str, Any]) -> None:
    """Initialize worker resources on startup.

    Sets up database engine, session maker, and Redis client
    that will be available throughout worker lifecycle.

    Args:
        ctx: SAQ worker context dictionary for storing shared resources
    """
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

    task_count = len(get_task_functions())
    cron_count = len(get_cron_jobs())
    _print_startup_banner(task_count, cron_count)

    logger.debug(
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
    sys.stdout.write("\n\033[93m⏹ Shutting down worker...\033[0m\n")
    sys.stdout.flush()

    engine: AsyncEngine | None = ctx.get("engine")
    if engine:
        await engine.dispose()
        logger.debug("Database engine disposed")

    redis = ctx.get("redis")
    if redis:
        await redis.aclose()
        logger.debug("Redis connection closed")

    sys.stdout.write("\033[92m✓ Worker shutdown complete\033[0m\n")
    sys.stdout.flush()


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

    Logs task completion, tracks persistent statistics, and can be used for cleanup.

    Args:
        ctx: SAQ worker context dictionary
    """
    job = ctx.get("job")
    if not job:
        return

    from pydotorg.tasks.stats import get_stats_service  # noqa: PLC0415

    stats_service = await get_stats_service(ctx)

    if job.error:
        logger.info(
            "Task failed",
            extra={
                "task_name": job.function,
                "task_id": job.key,
                "error": str(job.error)[:200],
            },
        )
        if stats_service:
            await stats_service.increment_failed(job.function)
    else:
        logger.info(
            "Task completed",
            extra={
                "task_name": job.function,
                "task_id": job.key,
            },
        )
        if stats_service:
            await stats_service.increment_complete(job.function)


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
        target_index = 2
        for i, item in enumerate(items):
            if i == target_index:
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
        invalidate_page_response_cache,
        warm_blogs_cache,
        warm_events_cache,
        warm_homepage_cache,
        warm_pages_cache,
        warm_releases_cache,
    )
    from pydotorg.tasks.downloads import (  # noqa: PLC0415
        aggregate_download_stats,
        flush_download_stats,
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
        aggregate_download_stats,
        flush_download_stats,
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
        invalidate_page_response_cache,
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

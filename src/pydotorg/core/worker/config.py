"""Litestar-SAQ plugin configuration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar_saq import QueueConfig, SAQConfig, SAQPlugin
from saq import CronJob

from pydotorg.config import settings
from pydotorg.core.database.base import AuditBase
from pydotorg.tasks.cache import (
    clear_cache as cache_clear,
)
from pydotorg.tasks.cache import (
    get_cache_stats,
    warm_blogs_cache,
    warm_events_cache,
    warm_homepage_cache,
    warm_pages_cache,
    warm_releases_cache,
)
from pydotorg.tasks.email import (
    send_bulk_email,
    send_event_reminder_email,
    send_job_approved_email,
    send_job_rejected_email,
    send_password_reset_email,
    send_verification_email,
)
from pydotorg.tasks.feeds import refresh_all_feeds, refresh_single_feed, refresh_stale_feeds
from pydotorg.tasks.jobs import archive_old_jobs, cleanup_draft_jobs, expire_jobs
from pydotorg.tasks.search import (
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

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    """Initialize worker resources on startup.

    Sets up database engine, session maker, and service instances
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

    logger.info(
        "SAQ worker initialized",
        extra={
            "database_url": str(settings.database_url).split("@")[-1],
            "redis_url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url,
            "concurrency": settings.saq_worker_concurrency,
        },
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    """Cleanup worker resources on shutdown.

    Properly disposes database engine and cleans up any other resources.

    Args:
        ctx: SAQ worker context dictionary
    """
    logger.info("SAQ worker shutting down...")

    engine: AsyncEngine | None = ctx.get("engine")
    if engine:
        await engine.dispose()
        logger.info("Database engine disposed")

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


TASK_FUNCTIONS = [
    refresh_all_feeds,
    refresh_single_feed,
    refresh_stale_feeds,
    index_content,
    rebuild_search_index,
    index_all_jobs,
    index_all_events,
    index_all_pages,
    index_all_blogs,
    index_job,
    index_event,
    index_page,
    index_blog_entry,
    remove_job_from_index,
    expire_jobs,
    archive_old_jobs,
    cleanup_draft_jobs,
    send_verification_email,
    send_password_reset_email,
    send_job_approved_email,
    send_job_rejected_email,
    send_event_reminder_email,
    send_bulk_email,
    warm_homepage_cache,
    warm_releases_cache,
    warm_events_cache,
    warm_blogs_cache,
    warm_pages_cache,
    cache_clear,
    get_cache_stats,
]

SCHEDULED_TASKS = [
    CronJob(
        function=refresh_stale_feeds,
        cron="*/15 * * * *",
        kwargs={"max_age_hours": 1},
        timeout=600,
        unique=True,
    ),
    CronJob(
        function=refresh_all_feeds,
        cron="0 */6 * * *",
        unique=True,
    ),
    CronJob(
        function=rebuild_search_index,
        cron="0 3 * * 0",
        unique=True,
    ),
    CronJob(
        function=expire_jobs,
        cron="0 2 * * *",
        unique=True,
    ),
    CronJob(
        function=archive_old_jobs,
        cron="0 0 * * 0",
        kwargs={"days_old": 90},
        timeout=600,
        unique=True,
    ),
    CronJob(
        function=cleanup_draft_jobs,
        cron="0 0 1 * *",
        kwargs={"days_old": 30},
        timeout=300,
        unique=True,
    ),
    CronJob(
        function=warm_homepage_cache,
        cron="*/5 * * * *",
        timeout=60,
        unique=True,
    ),
    CronJob(
        function=warm_releases_cache,
        cron="0 * * * *",
        timeout=120,
        unique=True,
    ),
]

default_queue_config = QueueConfig(
    name="default",
    dsn=settings.redis_url,
    tasks=TASK_FUNCTIONS,
    scheduled_tasks=SCHEDULED_TASKS,
    concurrency=settings.saq_worker_concurrency,
    startup=startup,
    shutdown=shutdown,
    before_process=before_process,
    after_process=after_process,
)

saq_config = SAQConfig(
    queue_configs=[default_queue_config],
    web_enabled=settings.saq_web_enabled,
)

saq_plugin = SAQPlugin(config=saq_config)

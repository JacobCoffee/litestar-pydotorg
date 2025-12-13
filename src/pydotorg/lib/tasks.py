"""Task queue helpers for SAQ background tasks.

This module provides utilities for enqueueing background tasks from
service layers. It handles lazy imports to avoid circular dependencies
and provides consistent error handling.

Example:
    from pydotorg.lib.tasks import enqueue_task

    async def approve_job(self, job_id: UUID) -> Job:
        job = await self.repository.update(job_id, status=JobStatus.APPROVED)

        # Enqueue background tasks - best effort
        await enqueue_task("index_job", job_id=str(job.id))
        await enqueue_task(
            "send_job_approved_email",
            to_email=job.creator.email,
            job_title=job.job_title,
            company_name=job.company_name,
            job_url=f"/jobs/{job.slug}/"
        )

        return job
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from saq import Queue

logger = logging.getLogger(__name__)

DEFAULT_RETRIES: Final = 3


def get_queue() -> Queue:
    """Get the SAQ queue lazily to avoid circular imports.

    Returns:
        Configured SAQ Queue instance
    """
    from pydotorg.tasks.worker import queue  # noqa: PLC0415

    return queue


async def enqueue_task(
    task_name: str,
    *,
    timeout: int | None = None,
    retries: int = DEFAULT_RETRIES,
    **kwargs: Any,
) -> str | None:
    """Enqueue a background task by name.

    This is the primary helper for enqueueing tasks from service layers.
    Provides error handling and returns the job key for tracking.

    The task function must be registered in the worker's get_task_functions().
    Task arguments should match the function signature (keyword-only args after ctx).

    Args:
        task_name: Name of the task function to enqueue (must be registered).
            Available tasks:
            - Email: send_verification_email, send_password_reset_email,
                     send_job_submitted_email, send_job_approved_email,
                     send_job_rejected_email, send_event_reminder_email,
                     send_bulk_email
            - Search: index_job, index_event, index_page, index_blog_entry,
                      index_all_jobs, index_all_events, index_all_pages,
                      index_all_blogs, remove_job_from_index, rebuild_search_index
            - Jobs: expire_jobs, archive_old_jobs, cleanup_draft_jobs
            - Feeds: refresh_all_feeds, refresh_stale_feeds, refresh_single_feed
            - Cache: warm_homepage_cache, warm_releases_cache, warm_events_cache,
                     warm_blogs_cache, warm_pages_cache, clear_cache, get_cache_stats
        timeout: Optional task timeout in seconds
        retries: Number of retry attempts (default: 3)
        **kwargs: Task-specific arguments passed to the task function

    Returns:
        Job key (str) if successful, None if enqueue failed

    Example:
        # Enqueue email after user registration
        job_key = await enqueue_task(
            "send_verification_email",
            to_email=user.email,
            username=user.username,
            verification_link=verification_link,
        )
        if job_key:
            logger.info(f"Verification email queued: {job_key}")

        # Enqueue search indexing after job approval
        await enqueue_task("index_job", job_id=str(job.id))
    """
    queue = get_queue()

    try:
        job_kwargs = kwargs.copy()
        if timeout:
            job_kwargs["timeout"] = timeout
        if retries != DEFAULT_RETRIES:
            job_kwargs["retries"] = retries

        job = await queue.enqueue(task_name, **job_kwargs)

        if job is None:
            logger.warning(
                "Task enqueue returned None (may already be enqueued)",
                extra={"task_name": task_name, "kwargs": kwargs},
            )
            return None
    except Exception:
        logger.exception(
            "Failed to enqueue task",
            extra={"task_name": task_name, "kwargs": kwargs},
        )
        return None
    else:
        return job.key


async def enqueue_task_safe(
    task_name: str,
    *,
    timeout: int | None = None,
    retries: int = DEFAULT_RETRIES,
    **kwargs: Any,
) -> tuple[bool, str | None]:
    """Enqueue a task and return success status with optional job key.

    Variant of enqueue_task that returns a tuple for easier error handling
    in conditional flows.

    Args:
        task_name: Name of the task function to enqueue
        timeout: Optional task timeout in seconds
        retries: Number of retry attempts
        **kwargs: Task-specific arguments

    Returns:
        Tuple of (success: bool, job_key: str | None)

    Example:
        success, job_key = await enqueue_task_safe(
            "send_email",
            to_email="user@example.com"
        )
        if not success:
            # Handle failure - maybe log or retry later
            pass
    """
    job_key = await enqueue_task(task_name, timeout=timeout, retries=retries, **kwargs)
    return (job_key is not None, job_key)

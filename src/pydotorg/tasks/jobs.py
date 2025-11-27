"""Background tasks for job posting management."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from saq import CronJob

from pydotorg.domains.jobs.models import JobStatus
from pydotorg.domains.jobs.services import JobService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def expire_jobs(ctx: dict[str, Any]) -> dict[str, int]:
    """Mark expired job postings as EXPIRED.

    This task finds all approved jobs that have passed their expiration date
    and updates their status to EXPIRED.

    Args:
        ctx: SAQ worker context with database session maker

    Returns:
        dict with count of expired jobs
    """
    session_maker = ctx["session_maker"]

    async with session_maker() as session:
        session: AsyncSession
        job_service = JobService(session=session)

        try:
            expired_jobs = await job_service.mark_expired_jobs()
            count = len(expired_jobs)

            logger.info(
                "Job expiration task completed",
                extra={
                    "expired_count": count,
                    "job_ids": [str(job.id) for job in expired_jobs],
                },
            )

            return {"count": count}

        except Exception:
            logger.exception("Failed to expire jobs")
            raise


async def archive_old_jobs(ctx: dict[str, Any], *, days_old: int = 90) -> dict[str, int]:
    """Archive jobs older than specified days.

    This task finds expired and rejected jobs older than the specified number
    of days and archives them to keep the active job listings clean.

    Args:
        ctx: SAQ worker context with database session maker
        days_old: Number of days after which to archive jobs (default: 90)

    Returns:
        dict with count of archived jobs
    """
    session_maker = ctx["session_maker"]

    async with session_maker() as session:
        session: AsyncSession
        job_service = JobService(session=session)

        try:
            cutoff_date = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=days_old)

            expired_jobs = await job_service.list_by_status(JobStatus.EXPIRED, limit=1000)
            rejected_jobs = await job_service.list_by_status(JobStatus.REJECTED, limit=1000)

            jobs_to_archive = [
                job
                for job in expired_jobs + rejected_jobs
                if job.updated_at and job.updated_at.replace(tzinfo=datetime.UTC) < cutoff_date
            ]

            archived_count = 0
            for job in jobs_to_archive:
                await job_service.archive_job(job.id)
                archived_count += 1

            logger.info(
                "Job archival task completed",
                extra={
                    "days_old": days_old,
                    "cutoff_date": cutoff_date.isoformat(),
                    "archived_count": archived_count,
                    "expired_archived": len([j for j in jobs_to_archive if j.status == JobStatus.EXPIRED]),
                    "rejected_archived": len([j for j in jobs_to_archive if j.status == JobStatus.REJECTED]),
                },
            )

            return {"count": archived_count}

        except Exception:
            logger.exception("Failed to archive old jobs", extra={"days_old": days_old})
            raise


async def cleanup_draft_jobs(ctx: dict[str, Any], *, days_old: int = 30) -> dict[str, int]:
    """Clean up old draft jobs that were never submitted.

    This task finds draft jobs that haven't been updated in the specified
    number of days and archives them to prevent database clutter.

    Args:
        ctx: SAQ worker context with database session maker
        days_old: Number of days of inactivity before cleanup (default: 30)

    Returns:
        dict with count of cleaned up jobs
    """
    session_maker = ctx["session_maker"]

    async with session_maker() as session:
        session: AsyncSession
        job_service = JobService(session=session)

        try:
            cutoff_date = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=days_old)

            draft_jobs = await job_service.list_by_status(JobStatus.DRAFT, limit=1000)

            stale_drafts = [
                job
                for job in draft_jobs
                if job.updated_at and job.updated_at.replace(tzinfo=datetime.UTC) < cutoff_date
            ]

            cleanup_count = 0
            for job in stale_drafts:
                await job_service.archive_job(job.id)
                cleanup_count += 1

            logger.info(
                "Draft job cleanup task completed",
                extra={
                    "days_old": days_old,
                    "cutoff_date": cutoff_date.isoformat(),
                    "cleanup_count": cleanup_count,
                },
            )

            return {"count": cleanup_count}

        except Exception:
            logger.exception("Failed to cleanup draft jobs", extra={"days_old": days_old})
            raise


cron_expire_jobs = CronJob(
    function=expire_jobs,
    cron="0 0 * * *",
    timeout=300,
)

cron_archive_old_jobs = CronJob(
    function=archive_old_jobs,
    cron="0 0 * * 0",
    kwargs={"days_old": 90},
    timeout=600,
)

cron_cleanup_draft_jobs = CronJob(
    function=cleanup_draft_jobs,
    cron="0 0 1 * *",
    kwargs={"days_old": 30},
    timeout=300,
)

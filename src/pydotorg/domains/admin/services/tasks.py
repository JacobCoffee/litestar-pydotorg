"""Admin task monitoring service for SAQ."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from saq import Queue
    from saq.job import Job

logger = logging.getLogger(__name__)


def _get_queue() -> Queue:
    """Get the SAQ queue lazily to avoid circular imports."""
    from pydotorg.tasks.worker import queue  # noqa: PLC0415

    return queue


def _get_task_functions() -> list[Any]:
    """Get task functions lazily to avoid circular imports."""
    from pydotorg.tasks.worker import TASK_FUNCTIONS  # noqa: PLC0415

    return TASK_FUNCTIONS


class TaskAdminService:
    """Service for admin task monitoring and management operations."""

    def __init__(self) -> None:
        self._queue: Queue | None = None

    @property
    def queue(self) -> Queue:
        """Lazily get the SAQ queue."""
        if self._queue is None:
            self._queue = _get_queue()
        return self._queue

    async def get_queue_info(self) -> dict[str, Any]:
        """Get queue information including job counts and worker status.

        Returns:
            Dict with queue stats including queued, active, scheduled, workers, etc.
        """
        try:
            info = await self.queue.info(jobs=True)
            return {
                "name": self.queue.name or "default",
                "workers": info.get("workers", 0),
                "queued": info.get("queued", 0),
                "active": info.get("active", 0),
                "scheduled": info.get("scheduled", 0),
                "latency_ms": info.get("latency_ms", 0),
                "uptime": info.get("uptime", 0),
            }
        except Exception:
            logger.exception("Failed to get queue info")
            return {
                "name": self.queue.name or "default",
                "workers": 0,
                "queued": 0,
                "active": 0,
                "scheduled": 0,
                "error": "Failed to retrieve queue information",
            }

    async def get_all_jobs(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get all jobs from the queue with optional status filter.

        Args:
            status: Optional status filter (queued, active, complete, failed)
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries with details
        """
        try:
            jobs: list[Job] = []
            job_dicts: list[dict[str, Any]] = []

            if status == "queued" or status is None:
                jobs.extend(await self.queue.queued(limit=limit))

            if status == "active" or status is None:
                active_jobs = await self.queue.active(limit=limit)
                jobs.extend(active_jobs)

            for job in jobs[:limit]:
                job_dict = await self._job_to_dict(job)
                if status is None or job_dict.get("status") == status:
                    job_dicts.append(job_dict)
        except Exception:
            logger.exception("Failed to get jobs")
            return []
        else:
            return job_dicts

    async def get_job_info(self, job_key: str) -> dict[str, Any] | None:
        """Get detailed information about a specific job.

        Args:
            job_key: The job key/ID

        Returns:
            Job details dict or None if not found
        """
        try:
            job = await self.queue.job(job_key)
            if not job:
                return None
            return await self._job_to_dict(job, include_details=True)
        except Exception:
            logger.exception(f"Failed to get job info for {job_key}")
            return None

    async def retry_job(self, job_key: str) -> bool:
        """Retry a failed or aborted job.

        Args:
            job_key: The job key/ID

        Returns:
            True if successful, False otherwise
        """
        try:
            job = await self.queue.job(job_key)
            if not job:
                logger.warning(f"Job {job_key} not found for retry")
                return False

            await job.retry()
            logger.info(f"Job {job_key} enqueued for retry")
        except Exception:
            logger.exception(f"Failed to retry job {job_key}")
            return False
        else:
            return True

    async def abort_job(self, job_key: str) -> bool:
        """Abort an active job.

        Args:
            job_key: The job key/ID

        Returns:
            True if successful, False otherwise
        """
        try:
            job = await self.queue.job(job_key)
            if not job:
                logger.warning(f"Job {job_key} not found for abort")
                return False

            await job.abort()
            logger.info(f"Job {job_key} aborted")
        except Exception:
            logger.exception(f"Failed to abort job {job_key}")
            return False
        else:
            return True

    async def enqueue_task(self, task_name: str, **kwargs: Any) -> str | None:
        """Enqueue a task by name.

        Args:
            task_name: Name of the task function to enqueue
            **kwargs: Task arguments

        Returns:
            Job key if successful, None otherwise
        """
        try:
            task_functions = _get_task_functions()
            task_func = None
            for func in task_functions:
                if func.__name__ == task_name:
                    task_func = func
                    break

            if not task_func:
                logger.error(f"Task function '{task_name}' not found")
                return None

            job = await self.queue.enqueue(task_name, **kwargs)
            if job is None:
                logger.error(f"Failed to enqueue task '{task_name}' - job was None")
                return None
        except Exception:
            logger.exception(f"Failed to enqueue task '{task_name}'")
            return None
        else:
            logger.info(f"Enqueued task '{task_name}' with key {job.key}")
            return job.key

    async def get_available_tasks(self) -> list[dict[str, str]]:
        """Get list of available task functions.

        Returns:
            List of task info dicts with name and docstring
        """
        task_functions = _get_task_functions()
        tasks = [
            {
                "name": func.__name__,
                "description": (func.__doc__ or "No description").split("\n")[0].strip(),
            }
            for func in task_functions
        ]
        return sorted(tasks, key=lambda x: x["name"])

    async def get_stats(self) -> dict[str, Any]:
        """Get overall queue statistics.

        Returns:
            Dict with comprehensive queue stats
        """
        try:
            info = await self.get_queue_info()
            jobs = await self.get_all_jobs(limit=1000)

            failed = sum(1 for j in jobs if j.get("status") == "failed")
            complete = sum(1 for j in jobs if j.get("status") == "complete")
            queued = info.get("queued", 0)
            active = info.get("active", 0)

            return {
                "total_jobs": len(jobs),
                "queued": queued,
                "active": active,
                "complete": complete,
                "failed": failed,
                "workers": info.get("workers", 0),
                "latency_ms": info.get("latency_ms", 0),
                "available_tasks": len(_get_task_functions()),
            }
        except Exception:
            logger.exception("Failed to get queue stats")
            return {
                "total_jobs": 0,
                "queued": 0,
                "active": 0,
                "complete": 0,
                "failed": 0,
                "workers": 0,
                "latency_ms": 0,
                "available_tasks": len(_get_task_functions()),
                "error": "Failed to retrieve statistics",
            }

    async def _job_to_dict(self, job: Job, *, include_details: bool = False) -> dict[str, Any]:
        """Convert a SAQ Job to a dictionary.

        Args:
            job: SAQ Job instance
            include_details: Include full job details

        Returns:
            Job data as dictionary
        """
        job_dict = {
            "key": job.key,
            "function": job.function,
            "status": job.status,
            "queued": job.queued.isoformat() if job.queued else None,
            "started": job.started.isoformat() if job.started else None,
            "completed": job.completed.isoformat() if job.completed else None,
            "attempts": job.attempts,
        }

        if include_details:
            job_dict.update(
                {
                    "kwargs": job.kwargs,
                    "result": job.result,
                    "error": job.error,
                    "stuck": job.stuck,
                    "timeout": job.timeout,
                    "heartbeat": job.heartbeat,
                    "progress": job.progress,
                }
            )

        return job_dict

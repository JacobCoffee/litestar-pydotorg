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
    from pydotorg.tasks.worker import get_task_functions  # noqa: PLC0415

    return get_task_functions()


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
            workers_info = info.get("workers", {})
            worker_count = len(workers_info) if isinstance(workers_info, dict) else int(workers_info or 0)
            return {
                "name": self.queue.name or "default",
                "workers": worker_count,
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

    async def get_all_jobs(
        self,
        status: str | None = None,
        limit: int = 100,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[dict[str, Any]]:
        """Get all jobs from the queue with optional status filter and sorting.

        Args:
            status: Optional status filter (queued, active, complete, failed, scheduled)
            limit: Maximum number of jobs to return
            sort_by: Field to sort by (function, status, started, attempts)
            sort_order: Sort order (asc or desc)

        Returns:
            List of job dictionaries with details
        """
        try:
            job_dicts: list[dict[str, Any]] = []
            count = 0

            async for job in self.queue.iter_jobs():
                if count >= limit:
                    break
                job_dict = await self._job_to_dict(job)
                if status is None or job_dict.get("status") == status:
                    job_dicts.append(job_dict)
                    count += 1

            if sort_by:
                reverse = sort_order == "desc"
                if sort_by == "function":
                    job_dicts.sort(key=lambda x: x.get("function", ""), reverse=reverse)
                elif sort_by == "status":
                    job_dicts.sort(key=lambda x: x.get("status", ""), reverse=reverse)
                elif sort_by == "started":
                    job_dicts.sort(key=lambda x: x.get("started") or "", reverse=reverse)
                elif sort_by == "attempts":
                    job_dicts.sort(key=lambda x: x.get("attempts") or 0, reverse=reverse)
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

            await job.retry("Manual retry from admin")
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
            Dict with comprehensive queue stats including persistent counters
        """
        try:
            info = await self.get_queue_info()
            jobs = await self.get_all_jobs(limit=1000)

            queued = info.get("queued", 0)
            active = info.get("active", 0)

            persistent_stats = await self._get_persistent_stats()

            return {
                "total_jobs": len(jobs),
                "queued": queued,
                "active": active,
                "complete": persistent_stats.get("complete", 0),
                "failed": persistent_stats.get("failed", 0),
                "retried": persistent_stats.get("retried", 0),
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
                "retried": 0,
                "workers": 0,
                "latency_ms": 0,
                "available_tasks": len(_get_task_functions()),
                "error": "Failed to retrieve statistics",
            }

    async def _get_persistent_stats(self) -> dict[str, int]:
        """Get persistent statistics from Redis.

        Returns:
            Dict with complete, failed, retried counts
        """
        try:
            from redis.asyncio import Redis  # noqa: PLC0415

            from pydotorg.config import settings  # noqa: PLC0415
            from pydotorg.tasks.stats import TaskStatsService  # noqa: PLC0415

            redis = Redis.from_url(settings.redis_url, decode_responses=True)
            try:
                namespace = getattr(settings, "redis_stats_namespace", "pydotorg")
                stats_service = TaskStatsService(redis, namespace=namespace)
                return await stats_service.get_stats()
            finally:
                await redis.aclose()
        except Exception:
            logger.exception("Failed to get persistent stats")
            return {"complete": 0, "failed": 0, "retried": 0}

    async def _job_to_dict(self, job: Job, *, include_details: bool = False) -> dict[str, Any]:
        """Convert a SAQ Job to a dictionary.

        Args:
            job: SAQ Job instance
            include_details: Include full job details

        Returns:
            Job data as dictionary
        """
        from datetime import UTC, datetime  # noqa: PLC0415

        ms_threshold = 1e12

        def _format_timestamp(ts: int | float | None) -> str | None:
            """Convert Unix timestamp (seconds or milliseconds) to ISO format string."""
            if ts is None or ts == 0:
                return None
            try:
                if isinstance(ts, (int, float)):
                    ts_float = float(ts)
                    if ts_float > ms_threshold:
                        ts_float = ts_float / 1000
                    return datetime.fromtimestamp(ts_float, tz=UTC).isoformat()
                return str(ts)
            except (OSError, ValueError):
                return str(ts)

        status = job.status
        scheduled_ts = getattr(job, "scheduled", None)
        if status == "queued" and scheduled_ts and scheduled_ts > datetime.now(tz=UTC).timestamp():
            status = "scheduled"

        job_dict = {
            "key": job.key,
            "function": job.function,
            "status": status,
            "queued": _format_timestamp(job.queued),
            "started": _format_timestamp(job.started),
            "completed": _format_timestamp(job.completed),
            "scheduled": _format_timestamp(scheduled_ts) if scheduled_ts else None,
            "attempts": job.attempts,
            "is_cron": job.key.startswith("cron:"),
        }

        if include_details:
            error_str = job.error
            traceback_str = None
            if error_str and "Traceback" in error_str:
                parts = error_str.split("Traceback", 1)
                error_str = parts[0].strip() if parts[0].strip() else "Task failed"
                traceback_str = "Traceback" + parts[1]

            job_dict.update(
                {
                    "kwargs": job.kwargs,
                    "result": job.result,
                    "error": error_str,
                    "traceback": traceback_str,
                    "stuck": job.stuck,
                    "timeout": job.timeout,
                    "heartbeat": job.heartbeat,
                    "progress": job.progress,
                }
            )

        return job_dict

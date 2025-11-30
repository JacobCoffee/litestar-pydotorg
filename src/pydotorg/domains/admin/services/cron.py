"""Admin cron job monitoring service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from croniter import croniter

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from saq import CronJob

logger = logging.getLogger(__name__)


def _get_cron_jobs() -> list[CronJob]:
    """Get cron jobs lazily to avoid circular imports."""
    from pydotorg.tasks.worker import get_cron_jobs  # noqa: PLC0415

    return get_cron_jobs()


def _get_cron_job_metadata(cron_job: CronJob) -> dict[str, Any]:
    """Extract metadata from a SAQ CronJob.

    Args:
        cron_job: SAQ CronJob instance.

    Returns:
        Dictionary with cron job metadata.
    """
    func = cron_job.function
    func_name = func.__name__ if callable(func) else str(func)
    func_doc = (func.__doc__ or "No description").split("\n")[0].strip() if callable(func) else ""

    return {
        "function_name": func_name,
        "description": func_doc,
        "cron_expression": cron_job.cron,
        "timeout": cron_job.timeout,
        "kwargs": cron_job.kwargs or {},
    }


def _parse_cron_schedule(cron_expression: str, base_time: datetime | None = None) -> dict[str, Any]:
    """Parse cron expression and return schedule info.

    Args:
        cron_expression: Cron expression string (e.g., "0 0 * * *").
        base_time: Base time for calculation (default: now).

    Returns:
        Dictionary with next_run, previous_run, and human-readable schedule.
    """
    if base_time is None:
        base_time = datetime.now(UTC)

    try:
        cron = croniter(cron_expression, base_time)
        next_run = cron.get_next(datetime)
        prev_run = croniter(cron_expression, base_time).get_prev(datetime)

        schedule_desc = _cron_to_human(cron_expression)

        return {
            "next_run": next_run.isoformat() if next_run else None,
            "previous_run": prev_run.isoformat() if prev_run else None,
            "schedule_description": schedule_desc,
            "is_valid": True,
        }
    except (ValueError, KeyError) as e:
        logger.warning(f"Invalid cron expression '{cron_expression}': {e}")
        return {
            "next_run": None,
            "previous_run": None,
            "schedule_description": f"Invalid: {cron_expression}",
            "is_valid": False,
        }


def _cron_to_human(cron_expression: str) -> str:  # noqa: PLR0911
    """Convert cron expression to human-readable description.

    Args:
        cron_expression: Cron expression string.

    Returns:
        Human-readable schedule description.
    """
    parts = cron_expression.split()
    if len(parts) != 5:  # noqa: PLR2004
        return cron_expression

    minute, hour, day, _month, weekday = parts

    if minute.startswith("*/"):
        interval = minute[2:]
        return f"Every {interval} minutes"

    if hour.startswith("*/"):
        interval = hour[2:]
        return f"Every {interval} hours"

    if minute == "0" and hour == "*":
        return "Every hour at minute 0"

    if minute == "0" and day == "1" and weekday == "*":
        if hour != "*":
            return f"Monthly on 1st at {hour}:00"
        return "Monthly on 1st"

    if minute == "0" and weekday == "0":
        if hour != "*":
            return f"Weekly on Sunday at {hour}:00"
        return "Weekly on Sunday"

    if minute == "0" and day == "*" and weekday == "*":
        if hour != "*":
            return f"Daily at {hour}:00"
        return "Daily"

    return cron_expression


class CronJobService:
    """Service for monitoring cron jobs and their execution statistics."""

    def __init__(self, redis: Redis | None = None) -> None:
        """Initialize the cron job service.

        Args:
            redis: Optional Redis client for stats retrieval.
        """
        self._redis = redis

    async def get_all_cron_jobs(self) -> list[dict[str, Any]]:
        """Get all registered cron jobs with their metadata and stats.

        Returns:
            List of cron job info dictionaries.
        """
        cron_jobs = _get_cron_jobs()
        now = datetime.now(UTC)
        result = []

        for cron_job in cron_jobs:
            metadata = _get_cron_job_metadata(cron_job)
            schedule = _parse_cron_schedule(metadata["cron_expression"], now)

            stats = await self._get_function_stats(metadata["function_name"])

            job_info = {
                **metadata,
                **schedule,
                "stats": stats,
            }
            result.append(job_info)

        result.sort(key=lambda x: x.get("next_run") or "9999-12-31")
        return result

    async def get_cron_job(self, function_name: str) -> dict[str, Any] | None:
        """Get details for a specific cron job by function name.

        Args:
            function_name: Name of the cron job function.

        Returns:
            Cron job info dictionary or None if not found.
        """
        cron_jobs = _get_cron_jobs()
        now = datetime.now(UTC)

        for cron_job in cron_jobs:
            func = cron_job.function
            func_name = func.__name__ if callable(func) else str(func)

            if func_name == function_name:
                metadata = _get_cron_job_metadata(cron_job)
                schedule = _parse_cron_schedule(metadata["cron_expression"], now)
                stats = await self._get_function_stats(function_name)

                return {
                    **metadata,
                    **schedule,
                    "stats": stats,
                }

        return None

    async def _get_function_stats(self, function_name: str) -> dict[str, int]:
        """Get persistent statistics for a function.

        Args:
            function_name: Name of the task function.

        Returns:
            Dictionary with complete, failed, retried counts.
        """
        if not self._redis:
            return {"complete": 0, "failed": 0, "retried": 0, "success_rate": 0.0}

        from pydotorg.tasks.stats import TaskStatsService  # noqa: PLC0415

        try:
            stats_service = TaskStatsService(self._redis, namespace="pydotorg")
            stats = await stats_service.get_function_stats(function_name)

            total = stats.get("complete", 0) + stats.get("failed", 0)
            success_rate = round((stats.get("complete", 0) / total * 100), 1) if total > 0 else 100.0
        except Exception:
            logger.exception(f"Failed to get stats for {function_name}")
            return {"complete": 0, "failed": 0, "retried": 0, "total": 0, "success_rate": 0.0}
        else:
            return {
                **stats,
                "total": total,
                "success_rate": success_rate,
            }

    async def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics across all cron jobs.

        Returns:
            Dictionary with aggregate statistics.
        """
        cron_jobs = await self.get_all_cron_jobs()

        total_complete = sum(job["stats"].get("complete", 0) for job in cron_jobs)
        total_failed = sum(job["stats"].get("failed", 0) for job in cron_jobs)
        total_executions = total_complete + total_failed

        next_runs = [job["next_run"] for job in cron_jobs if job.get("next_run")]
        next_scheduled = min(next_runs) if next_runs else None

        return {
            "total_cron_jobs": len(cron_jobs),
            "total_executions": total_executions,
            "total_complete": total_complete,
            "total_failed": total_failed,
            "overall_success_rate": round((total_complete / total_executions * 100), 1)
            if total_executions > 0
            else 100.0,
            "next_scheduled_run": next_scheduled,
        }

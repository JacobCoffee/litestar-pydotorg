"""Persistent job statistics tracking for SAQ tasks.

This module provides Redis-based persistent statistics tracking for SAQ jobs.
SAQ deletes completed jobs after TTL (600s default), so we track stats separately.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class TaskStatsService:
    """Service for tracking persistent job statistics in Redis.

    Stores atomic counters for job completion/failure across application restarts.
    Uses Redis INCR for atomic updates and separate keys for total vs per-function stats.
    """

    def __init__(self, redis: Redis, namespace: str = "pydotorg") -> None:
        """Initialize the stats service.

        Args:
            redis: Redis client instance (from worker context)
            namespace: Redis key namespace prefix (default: "pydotorg")
        """
        self.redis = redis
        self.namespace = namespace

    def _key(self, *parts: str) -> str:
        """Build a namespaced Redis key.

        Args:
            *parts: Key components to join

        Returns:
            Namespaced Redis key string
        """
        return ":".join([self.namespace, "tasks", "stats", *parts])

    async def increment_complete(self, function_name: str | None = None) -> None:
        """Increment completed job counter.

        Args:
            function_name: Optional function name for per-function stats
        """
        try:
            await self.redis.incr(self._key("total", "complete"))
            if function_name:
                await self.redis.incr(self._key("func", function_name, "complete"))
            logger.debug(f"Incremented complete counter for {function_name or 'total'}")
        except Exception:
            logger.exception(f"Failed to increment complete counter for {function_name}")

    async def increment_failed(self, function_name: str | None = None) -> None:
        """Increment failed job counter.

        Args:
            function_name: Optional function name for per-function stats
        """
        try:
            await self.redis.incr(self._key("total", "failed"))
            if function_name:
                await self.redis.incr(self._key("func", function_name, "failed"))
            logger.debug(f"Incremented failed counter for {function_name or 'total'}")
        except Exception:
            logger.exception(f"Failed to increment failed counter for {function_name}")

    async def increment_retried(self, function_name: str | None = None) -> None:
        """Increment retried job counter.

        Args:
            function_name: Optional function name for per-function stats
        """
        try:
            await self.redis.incr(self._key("total", "retried"))
            if function_name:
                await self.redis.incr(self._key("func", function_name, "retried"))
            logger.debug(f"Incremented retried counter for {function_name or 'total'}")
        except Exception:
            logger.exception(f"Failed to increment retried counter for {function_name}")

    async def get_stats(self) -> dict[str, int]:
        """Get total job statistics.

        Returns:
            Dict with complete, failed, and retried counts
        """
        try:
            complete = await self.redis.get(self._key("total", "complete"))
            failed = await self.redis.get(self._key("total", "failed"))
            retried = await self.redis.get(self._key("total", "retried"))

            return {
                "complete": int(complete) if complete else 0,
                "failed": int(failed) if failed else 0,
                "retried": int(retried) if retried else 0,
            }
        except Exception:
            logger.exception("Failed to get total stats")
            return {"complete": 0, "failed": 0, "retried": 0}

    async def get_function_stats(self, function_name: str) -> dict[str, int]:
        """Get statistics for a specific function.

        Args:
            function_name: Name of the task function

        Returns:
            Dict with complete, failed, and retried counts for this function
        """
        try:
            complete = await self.redis.get(self._key("func", function_name, "complete"))
            failed = await self.redis.get(self._key("func", function_name, "failed"))
            retried = await self.redis.get(self._key("func", function_name, "retried"))

            return {
                "complete": int(complete) if complete else 0,
                "failed": int(failed) if failed else 0,
                "retried": int(retried) if retried else 0,
            }
        except Exception:
            logger.exception(f"Failed to get stats for function {function_name}")
            return {"complete": 0, "failed": 0, "retried": 0}

    async def get_all_function_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all functions.

        Returns:
            Dict mapping function names to their stats
        """
        try:
            pattern = self._key("func", "*", "complete")
            stats: dict[str, dict[str, int]] = {}
            expected_key_parts = 6

            async for key in self.redis.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= expected_key_parts:
                    function_name = parts[4]
                    if function_name not in stats:
                        stats[function_name] = await self.get_function_stats(function_name)

            return stats
        except Exception:
            logger.exception("Failed to get all function stats")
            return {}

    async def reset_stats(self) -> None:
        """Reset all statistics counters (admin operation)."""
        try:
            pattern = self._key("*")
            keys_deleted = 0

            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
                keys_deleted += 1

            logger.info(f"Reset task statistics ({keys_deleted} keys deleted)")
        except Exception:
            logger.exception("Failed to reset stats")


async def get_stats_service(ctx: dict[str, Any]) -> TaskStatsService | None:
    """Get or create stats service from worker context.

    Args:
        ctx: SAQ worker context dictionary

    Returns:
        TaskStatsService instance or None if Redis unavailable
    """
    redis = ctx.get("redis")
    if not redis:
        logger.warning("Redis not available in context, stats tracking disabled")
        return None

    if "stats_service" not in ctx:
        from pydotorg.config import settings  # noqa: PLC0415

        namespace = getattr(settings, "redis_stats_namespace", "pydotorg")
        ctx["stats_service"] = TaskStatsService(redis, namespace=namespace)

    return ctx["stats_service"]

"""Background tasks for litestar-pydotorg using SAQ.

This module provides access to all background tasks. To avoid circular imports,
access the queue and settings through the worker module directly:

    from pydotorg.tasks.worker import queue, settings_dict, get_task_functions

The ALL_TASKS and ALL_CRON_JOBS lists are populated lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "ALL_CRON_JOBS",
    "ALL_TASKS",
    "get_all_cron_jobs",
    "get_all_tasks",
]


def get_all_tasks() -> list[Callable[..., Any]]:
    """Get all task functions lazily to avoid circular imports."""
    from pydotorg.tasks.worker import get_task_functions  # noqa: PLC0415

    return get_task_functions()


def get_all_cron_jobs() -> list[Any]:
    """Get all cron jobs lazily to avoid circular imports."""
    from pydotorg.tasks.worker import get_cron_jobs  # noqa: PLC0415

    return get_cron_jobs()


ALL_TASKS: list[Callable[..., Any]] = []
ALL_CRON_JOBS: list[Any] = []

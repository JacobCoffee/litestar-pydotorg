"""Core application dependency providers."""

from __future__ import annotations

from typing import Annotated

from advanced_alchemy.filters import LimitOffset
from litestar.di import Provide
from litestar.params import Parameter

from pydotorg.config import settings
from pydotorg.core.features import FeatureFlags


async def provide_limit_offset(
    current_page: Annotated[int, Parameter(ge=1, default=1, query="currentPage")],
    page_size: Annotated[int, Parameter(ge=1, le=100, default=10, query="pageSize")],
) -> LimitOffset:
    """Provide LimitOffset pagination from query parameters.

    Args:
        current_page: Current page number (1-indexed, minimum 1).
        page_size: Number of items per page (1-100).

    Returns:
        LimitOffset instance for pagination.
    """
    return LimitOffset(page_size, page_size * (current_page - 1))


def provide_feature_flags() -> FeatureFlags:
    """Provide feature flags instance from settings.

    Returns:
        FeatureFlags instance configured from application settings
    """
    return FeatureFlags(
        enable_oauth=settings.features.enable_oauth,
        enable_jobs=settings.features.enable_jobs,
        enable_sponsors=settings.features.enable_sponsors,
        enable_search=settings.features.enable_search,
        maintenance_mode=settings.features.maintenance_mode,
    )


def get_core_dependencies() -> dict:
    """Get all core dependency providers.

    Returns:
        Dictionary of dependency providers for core functionality
    """
    return {
        "feature_flags": Provide(provide_feature_flags, sync_to_thread=False),
        "limit_offset": Provide(provide_limit_offset),
    }

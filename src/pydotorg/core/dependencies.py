"""Core application dependency providers."""

from __future__ import annotations

from litestar.di import Provide

from pydotorg.config import settings
from pydotorg.core.features import FeatureFlags


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
    }

"""Feature flags system for conditional functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.exceptions import ServiceUnavailableException

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler


class FeatureFlags:
    """Feature flags management for conditional functionality.

    Attributes:
        enable_oauth: OAuth authentication support
        enable_jobs: Job listings functionality
        enable_sponsors: Sponsorship management
        enable_search: Site-wide search functionality
        maintenance_mode: Application-wide maintenance mode
    """

    def __init__(
        self,
        *,
        enable_oauth: bool = True,
        enable_jobs: bool = True,
        enable_sponsors: bool = True,
        enable_search: bool = True,
        maintenance_mode: bool = False,
    ) -> None:
        self.enable_oauth = enable_oauth
        self.enable_jobs = enable_jobs
        self.enable_sponsors = enable_sponsors
        self.enable_search = enable_search
        self.maintenance_mode = maintenance_mode

    def is_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_name: Name of the feature to check

        Returns:
            True if feature is enabled, False otherwise

        Raises:
            AttributeError: If feature name does not exist
        """
        if not hasattr(self, feature_name):
            raise AttributeError(f"Unknown feature: {feature_name}")
        return bool(getattr(self, feature_name))

    def to_dict(self) -> dict[str, bool]:
        """Export feature flags as dictionary for template context.

        Returns:
            Dictionary of feature flag names and their values
        """
        return {
            "enable_oauth": self.enable_oauth,
            "enable_jobs": self.enable_jobs,
            "enable_sponsors": self.enable_sponsors,
            "enable_search": self.enable_search,
            "maintenance_mode": self.maintenance_mode,
        }


def require_feature(feature_name: str):
    """Guard decorator factory to require a feature to be enabled.

    Args:
        feature_name: Name of the feature flag to check

    Returns:
        Guard function that validates feature is enabled

    Example:
        ```python
        @get("/oauth/login", guards=[require_feature("enable_oauth")])
        async def oauth_login() -> dict:
            return {"message": "OAuth login"}
        ```
    """

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        """Validate that the specified feature is enabled.

        Args:
            connection: The ASGI connection
            _: The route handler (unused)

        Raises:
            ServiceUnavailableException: If feature is disabled or in maintenance mode
        """
        feature_flags: FeatureFlags = connection.app.state.feature_flags

        if feature_flags.maintenance_mode:
            raise ServiceUnavailableException("Application is in maintenance mode")

        if not feature_flags.is_enabled(feature_name):
            raise ServiceUnavailableException(f"Feature '{feature_name}' is currently disabled")

    return guard

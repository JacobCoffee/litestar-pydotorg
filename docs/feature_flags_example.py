"""Example usage of feature flags system.

This file demonstrates how to use the feature flags system in controllers,
guards, and templates.
"""

from __future__ import annotations

from litestar import Controller, get

from pydotorg.core.features import FeatureFlags, require_feature


class ExampleController(Controller):
    """Example controller demonstrating feature flag usage."""

    path = "/examples"

    @get("/oauth", guards=[require_feature("enable_oauth")])
    async def oauth_endpoint(self) -> dict[str, str]:
        """This endpoint is only accessible when OAuth is enabled.

        The require_feature guard will automatically return 503 if:
        - enable_oauth is False
        - maintenance_mode is True
        """
        return {"message": "OAuth endpoint accessible"}

    @get("/jobs", guards=[require_feature("enable_jobs")])
    async def jobs_endpoint(self) -> dict[str, str]:
        """This endpoint is only accessible when jobs feature is enabled."""
        return {"message": "Jobs endpoint accessible"}

    @get("/conditional", guards=[require_feature("enable_search")])
    async def conditional_logic(self, feature_flags: FeatureFlags) -> dict:
        """Example showing programmatic feature flag checks.

        You can inject feature_flags as a dependency and check flags manually
        for more complex conditional logic.
        """
        response = {"message": "Search is enabled"}

        if feature_flags.is_enabled("enable_jobs"):
            response["jobs_available"] = True

        if feature_flags.is_enabled("enable_sponsors"):
            response["sponsors_available"] = True

        return response

    @get("/status")
    async def status_endpoint(self, feature_flags: FeatureFlags) -> dict:
        """Public endpoint showing feature availability.

        This endpoint doesn't use guards, so it's always accessible.
        It returns the current state of all feature flags.
        """
        return {
            "features": feature_flags.to_dict(),
            "message": "Feature status retrieved successfully",
        }

"""Admin endpoints for system configuration and monitoring."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, get
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

from pydotorg.config import get_config_summary

if TYPE_CHECKING:
    from typing import Any

    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler


def require_admin_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Admin guard - inline to avoid circular import."""
    if not connection.user:
        raise NotAuthorizedException("Authentication required")

    user = connection.user
    if not user.is_superuser:
        raise PermissionDeniedException("Administrator privileges required")


class AdminController(Controller):
    """Admin-only system endpoints."""

    path = "/api/admin"
    tags = ["Admin"]
    guards = [require_admin_guard]
    include_in_schema = False

    @get("/config")
    async def get_config(self) -> dict[str, Any]:
        """
        Get non-sensitive configuration summary.

        Requires admin privileges.

        Returns:
            Configuration summary with non-sensitive settings
        """
        return get_config_summary()

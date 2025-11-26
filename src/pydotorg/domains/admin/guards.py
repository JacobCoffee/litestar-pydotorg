"""Admin-specific authorization guards and permissions."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler

    from pydotorg.domains.users.models import User


class AdminPermission(StrEnum):
    """Admin panel permissions."""

    VIEW_DASHBOARD = "view_dashboard"
    MANAGE_USERS = "manage_users"
    MODERATE_JOBS = "moderate_jobs"
    MODERATE_EVENTS = "moderate_events"
    MODERATE_SPONSORS = "moderate_sponsors"
    MANAGE_CONTENT = "manage_content"
    VIEW_SYSTEM = "view_system"
    MANAGE_SYSTEM = "manage_system"


def require_any_admin_access(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Require user to be staff or superuser.

    Args:
        connection: The ASGI connection
        _: The route handler (unused)

    Raises:
        NotAuthorizedException: If user is not authenticated
        PermissionDeniedException: If user is neither staff nor superuser
    """
    if not connection.user:
        raise NotAuthorizedException("Authentication required")

    user: User = connection.user

    if not (user.is_staff or user.is_superuser):
        raise PermissionDeniedException("Staff or administrator privileges required")


def require_permission(permission: AdminPermission) -> Callable[[ASGIConnection, BaseRouteHandler], None]:
    """Factory function to create permission guards.

    Args:
        permission: The required admin permission

    Returns:
        A guard function that checks for the specified permission

    Example:
        @get("/admin/users", guards=[require_permission(AdminPermission.MANAGE_USERS)])
        async def manage_users(self) -> Template:
            ...
    """

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        """Check if user has the required permission.

        Args:
            connection: The ASGI connection
            _: The route handler (unused)

        Raises:
            NotAuthorizedException: If user is not authenticated
            PermissionDeniedException: If user lacks the required permission
        """
        if not connection.user:
            raise NotAuthorizedException("Authentication required")

        user: User = connection.user

        if user.is_superuser:
            return

        if not user.is_staff:
            raise PermissionDeniedException("Staff or administrator privileges required")

        permission_map = {
            AdminPermission.VIEW_DASHBOARD: user.is_staff,
            AdminPermission.MANAGE_USERS: user.is_superuser,
            AdminPermission.MODERATE_JOBS: user.is_staff,
            AdminPermission.MODERATE_EVENTS: user.is_staff,
            AdminPermission.MODERATE_SPONSORS: user.is_staff,
            AdminPermission.MANAGE_CONTENT: user.is_staff,
            AdminPermission.VIEW_SYSTEM: user.is_staff,
            AdminPermission.MANAGE_SYSTEM: user.is_superuser,
        }

        if not permission_map.get(permission, False):
            raise PermissionDeniedException(f"Permission required: {permission.value}")

    return guard

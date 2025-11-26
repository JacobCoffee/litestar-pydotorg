"""Admin dashboard controller."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from litestar import Controller, get
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.schemas import (  # noqa: TC001
    DashboardStats,
    PendingModeration,
    RecentActivity,
)
from pydotorg.domains.admin.services import DashboardService  # noqa: TC001

if TYPE_CHECKING:
    from litestar import Request


def _admin_auth_exception_handler(request: Request, exc: NotAuthorizedException) -> Response:
    """Redirect to login page when user is not authenticated."""
    next_url = quote(str(request.url), safe="")
    return Redirect(f"/auth/login?next={next_url}")


def _admin_permission_exception_handler(request: Request, exc: PermissionDeniedException) -> Response:
    """Show 403 template when user lacks permissions."""
    return Template(
        template_name="errors/403.html.jinja2",
        context={
            "title": "Access Denied",
            "message": str(exc.detail) if exc.detail else "You do not have permission to access this page.",
        },
        status_code=403,
    )


class AdminDashboardController(Controller):
    """Controller for admin dashboard and overview."""

    path = urls.ADMIN
    tags = ["Admin"]
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def dashboard(
        self,
        dashboard_service: DashboardService,
    ) -> Template:
        """Render admin dashboard page.

        Args:
            dashboard_service: Dashboard service for statistics

        Returns:
            Admin dashboard template
        """
        stats = await dashboard_service.get_stats()
        pending = await dashboard_service.get_pending_items()
        recent_activity = await dashboard_service.get_recent_activity(limit=10)

        return Template(
            template_name="admin/dashboard.html.jinja2",
            context={
                "title": "Admin Dashboard",
                "description": "Administrative control panel",
                "stats": stats,
                "pending": pending,
                "recent_activity": recent_activity,
            },
        )

    @get("/api/stats")
    async def get_stats_json(
        self,
        dashboard_service: DashboardService,
    ) -> DashboardStats:
        """Get dashboard statistics as JSON.

        Args:
            dashboard_service: Dashboard service for statistics

        Returns:
            Dashboard statistics
        """
        return await dashboard_service.get_stats()

    @get("/api/pending")
    async def get_pending_json(
        self,
        dashboard_service: DashboardService,
    ) -> PendingModeration:
        """Get pending moderation items as JSON.

        Args:
            dashboard_service: Dashboard service for statistics

        Returns:
            Pending moderation summary
        """
        return await dashboard_service.get_pending_items()

    @get("/api/activity")
    async def get_activity_json(
        self,
        dashboard_service: DashboardService,
    ) -> list[RecentActivity]:
        """Get recent activity as JSON.

        Args:
            dashboard_service: Dashboard service for statistics

        Returns:
            List of recent activities
        """
        return await dashboard_service.get_recent_activity(limit=20)

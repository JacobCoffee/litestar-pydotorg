"""Admin analytics controller for download statistics."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.downloads import DownloadAnalyticsService

if TYPE_CHECKING:
    from litestar import Request
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_download_analytics_service(
    db_session: AsyncSession,
) -> DownloadAnalyticsService:
    """Provide download analytics service.

    Args:
        db_session: Database session from DI

    Returns:
        DownloadAnalyticsService instance
    """
    return DownloadAnalyticsService(session=db_session)


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


class AdminAnalyticsController(Controller):
    """Controller for admin analytics dashboard."""

    path = urls.ADMIN_ANALYTICS
    include_in_schema = False
    guards = [require_staff]
    dependencies = {"analytics_service": Provide(provide_download_analytics_service)}
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def analytics_index(self) -> Redirect:
        """Redirect to downloads analytics.

        Returns:
            Redirect to downloads analytics page
        """
        return Redirect("/admin/analytics/downloads")

    @get("/downloads")
    async def downloads_analytics(
        self,
        analytics_service: DownloadAnalyticsService,
    ) -> Template:
        """Render download analytics dashboard.

        Args:
            analytics_service: Injected analytics service

        Returns:
            Download analytics template
        """
        summary = await analytics_service.get_analytics_summary()
        return Template(
            template_name="admin/analytics/downloads.html.jinja2",
            context={
                "title": "Download Analytics",
                "description": "View download statistics and trends",
                "stats": summary,
            },
        )

    @get("/downloads/json")
    async def downloads_analytics_json(
        self,
        analytics_service: DownloadAnalyticsService,
    ) -> dict:
        """Get download analytics as JSON for charts.

        Args:
            analytics_service: Injected analytics service

        Returns:
            JSON dict with analytics data
        """
        return await analytics_service.get_analytics_summary()

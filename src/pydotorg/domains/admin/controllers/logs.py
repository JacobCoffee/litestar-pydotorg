"""Admin logs controller for activity and audit trail."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from litestar import Controller, get
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls

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


class AdminLogsController(Controller):
    """Controller for admin activity logs and audit trail."""

    path = urls.ADMIN_LOGS
    tags = ["Admin"]
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def logs_page(self) -> Template:
        """Render activity logs page.

        Returns:
            Activity logs template
        """
        return Template(
            template_name="admin/logs/index.html.jinja2",
            context={
                "title": "Activity Logs",
                "description": "View system activity and audit trail",
            },
        )

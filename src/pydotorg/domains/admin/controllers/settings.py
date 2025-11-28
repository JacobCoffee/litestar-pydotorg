"""Admin settings controller for site configuration management."""

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


class AdminSettingsController(Controller):
    """Controller for admin site settings management."""

    path = urls.ADMIN_SETTINGS
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def settings_page(self) -> Template:
        """Render site settings page.

        Returns:
            Site settings template
        """
        return Template(
            template_name="admin/settings/index.html.jinja2",
            context={
                "title": "Site Settings",
                "description": "Manage site configuration",
            },
        )

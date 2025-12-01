"""Admin pages controller for content page management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID  # noqa: TC003

from litestar import Controller, delete, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.pages import PageAdminService  # noqa: TC001

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


class AdminPagesController(Controller):
    """Controller for admin content page management."""

    path = urls.ADMIN_PAGES
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_pages(
        self,
        page_admin_service: PageAdminService,
        content_type: Annotated[str | None, Parameter(description="Filter by content type")] = None,
        published: Annotated[str | None, Parameter(description="Filter by publish status (true/false)")] = None,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render pages list page.

        Args:
            page_admin_service: Page admin service
            content_type: Filter by content type
            published: Filter by publish status (true/false string)
            q: Search query
            limit: Maximum pages per page
            offset: Pagination offset

        Returns:
            Pages list template
        """
        is_published: bool | None = None
        if published == "true":
            is_published = True
        elif published == "false":
            is_published = False

        pages, total = await page_admin_service.list_pages(
            limit=limit,
            offset=offset,
            content_type=content_type,
            search=q,
            is_published=is_published,
        )
        stats = await page_admin_service.get_stats()

        return Template(
            template_name="admin/pages/list.html.jinja2",
            context={
                "title": "Content Page Management",
                "description": "Manage content pages and publications",
                "pages": pages,
                "stats": stats,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/{page_id:uuid}")
    async def get_page_detail(
        self,
        page_admin_service: PageAdminService,
        page_id: UUID,
    ) -> Template | Response:
        """Render page detail/edit page.

        Args:
            page_admin_service: Page admin service
            page_id: Page ID

        Returns:
            Page detail template or redirect if not found
        """
        page = await page_admin_service.get_page(page_id)
        if not page:
            return Redirect("/admin/pages")

        return Template(
            template_name="admin/pages/detail.html.jinja2",
            context={
                "title": f"{page.title} - Page Details",
                "description": f"Edit page: {page.title}",
                "page": page,
            },
        )

    @get("/{page_id:uuid}/preview")
    async def get_page_preview(
        self,
        page_admin_service: PageAdminService,
        page_id: UUID,
    ) -> Template | Response:
        """Render page preview partial for modal.

        Args:
            page_admin_service: Page admin service
            page_id: Page ID

        Returns:
            Page preview partial or error response
        """
        page = await page_admin_service.get_page(page_id)
        if not page:
            return Response(content="Page not found", status_code=404)

        return Template(
            template_name="admin/pages/partials/page_preview.html.jinja2",
            context={"page": page},
        )

    @post("/{page_id:uuid}/publish")
    async def publish_page(
        self,
        request: Request,
        page_admin_service: PageAdminService,
        page_id: UUID,
    ) -> Template | Response:
        """Publish a page.

        Args:
            request: HTTP request
            page_admin_service: Page admin service
            page_id: Page ID

        Returns:
            Updated page row partial or error response
        """
        page = await page_admin_service.publish_page(page_id)
        if not page:
            return Response(content="Page not found", status_code=404)

        return Template(
            template_name="admin/pages/partials/page_row.html.jinja2",
            context={"page": page},
        )

    @post("/{page_id:uuid}/unpublish")
    async def unpublish_page(
        self,
        request: Request,
        page_admin_service: PageAdminService,
        page_id: UUID,
    ) -> Template | Response:
        """Unpublish a page.

        Args:
            request: HTTP request
            page_admin_service: Page admin service
            page_id: Page ID

        Returns:
            Updated page row partial or error response
        """
        page = await page_admin_service.unpublish_page(page_id)
        if not page:
            return Response(content="Page not found", status_code=404)

        return Template(
            template_name="admin/pages/partials/page_row.html.jinja2",
            context={"page": page},
        )

    @delete("/{page_id:uuid}", status_code=200)
    async def delete_page(
        self,
        request: Request,
        page_admin_service: PageAdminService,
        page_id: UUID,
    ) -> Response:
        """Delete a page.

        Args:
            request: HTTP request
            page_admin_service: Page admin service
            page_id: Page ID

        Returns:
            Success response or error response
        """
        deleted = await page_admin_service.delete_page(page_id)
        if not deleted:
            return Response(content="Page not found", status_code=404)

        return Response(
            content="",
            status_code=200,
            headers={"HX-Redirect": "/admin/pages"},
        )

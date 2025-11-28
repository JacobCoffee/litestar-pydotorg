"""Admin blogs controller for blog feed and entry management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID  # noqa: TC003

from litestar import Controller, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.blogs import BlogAdminService  # noqa: TC001

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


class AdminBlogsController(Controller):
    """Controller for admin blog feed and entry management."""

    path = urls.ADMIN_BLOGS
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_feeds(
        self,
        blog_admin_service: BlogAdminService,
        is_active: Annotated[bool | None, Parameter(description="Filter by active status")] = None,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render blog feeds list page.

        Args:
            blog_admin_service: Blog admin service
            is_active: Filter by active status
            q: Search query
            limit: Maximum feeds per page
            offset: Pagination offset

        Returns:
            Blog feeds list template
        """
        feeds, total = await blog_admin_service.list_feeds(
            limit=limit,
            offset=offset,
            is_active=is_active,
            search=q,
        )
        stats = await blog_admin_service.get_stats()

        return Template(
            template_name="admin/blogs/list.html.jinja2",
            context={
                "title": "Blog Feed Management",
                "description": "Manage blog feeds and entries",
                "feeds": feeds,
                "stats": stats,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/entries")
    async def list_entries(
        self,
        blog_admin_service: BlogAdminService,
        feed_id: Annotated[UUID | None, Parameter(description="Filter by feed")] = None,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render blog entries list page.

        Args:
            blog_admin_service: Blog admin service
            feed_id: Filter by feed ID
            q: Search query
            limit: Maximum entries per page
            offset: Pagination offset

        Returns:
            Blog entries list template
        """
        entries, total = await blog_admin_service.list_entries(
            limit=limit,
            offset=offset,
            feed_id=feed_id,
            search=q,
        )
        stats = await blog_admin_service.get_stats()
        feeds, _ = await blog_admin_service.list_feeds(limit=100)

        return Template(
            template_name="admin/blogs/entries_list.html.jinja2",
            context={
                "title": "Blog Entries",
                "description": "View and manage blog entries",
                "entries": entries,
                "feeds": feeds,
                "stats": stats,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/{feed_id:uuid}")
    async def get_feed_detail(
        self,
        blog_admin_service: BlogAdminService,
        feed_id: UUID,
    ) -> Template | Response:
        """Render blog feed detail page.

        Args:
            blog_admin_service: Blog admin service
            feed_id: Feed ID

        Returns:
            Blog feed detail template or redirect if not found
        """
        feed = await blog_admin_service.get_feed(feed_id)
        if not feed:
            return Redirect("/admin/blogs")

        return Template(
            template_name="admin/blogs/detail.html.jinja2",
            context={
                "title": f"{feed.name} - Feed Details",
                "description": f"Review feed: {feed.name}",
                "feed": feed,
            },
        )

    @get("/{feed_id:uuid}/preview")
    async def get_feed_preview(
        self,
        blog_admin_service: BlogAdminService,
        feed_id: UUID,
    ) -> Template | Response:
        """Render blog feed preview partial for modal.

        Args:
            blog_admin_service: Blog admin service
            feed_id: Feed ID

        Returns:
            Blog feed preview partial or error response
        """
        feed = await blog_admin_service.get_feed(feed_id)
        if not feed:
            return Response(content="Feed not found", status_code=404)

        return Template(
            template_name="admin/blogs/partials/feed_preview.html.jinja2",
            context={"feed": feed},
        )

    @post("/{feed_id:uuid}/activate")
    async def activate_feed(
        self,
        request: Request,
        blog_admin_service: BlogAdminService,
        feed_id: UUID,
    ) -> Template | Response:
        """Activate a blog feed.

        Args:
            request: HTTP request
            blog_admin_service: Blog admin service
            feed_id: Feed ID

        Returns:
            Updated feed row partial or error response
        """
        feed = await blog_admin_service.activate_feed(feed_id)
        if not feed:
            return Response(content="Feed not found", status_code=404)

        return Template(
            template_name="admin/blogs/partials/feed_row.html.jinja2",
            context={"feed": feed},
        )

    @post("/{feed_id:uuid}/deactivate")
    async def deactivate_feed(
        self,
        request: Request,
        blog_admin_service: BlogAdminService,
        feed_id: UUID,
    ) -> Template | Response:
        """Deactivate a blog feed.

        Args:
            request: HTTP request
            blog_admin_service: Blog admin service
            feed_id: Feed ID

        Returns:
            Updated feed row partial or error response
        """
        feed = await blog_admin_service.deactivate_feed(feed_id)
        if not feed:
            return Response(content="Feed not found", status_code=404)

        return Template(
            template_name="admin/blogs/partials/feed_row.html.jinja2",
            context={"feed": feed},
        )

    @get("/entry/{entry_id:uuid}")
    async def get_entry_detail(
        self,
        blog_admin_service: BlogAdminService,
        entry_id: UUID,
    ) -> Template | Response:
        """Render blog entry detail page.

        Args:
            blog_admin_service: Blog admin service
            entry_id: Entry ID

        Returns:
            Blog entry detail template or redirect if not found
        """
        entry = await blog_admin_service.get_entry(entry_id)
        if not entry:
            return Redirect("/admin/blogs/entries")

        return Template(
            template_name="admin/blogs/entry_detail.html.jinja2",
            context={
                "title": f"{entry.title} - Entry Details",
                "description": f"Review entry: {entry.title}",
                "entry": entry,
            },
        )

"""Admin sponsors controller for sponsor management."""

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
from pydotorg.domains.admin.services.sponsors import SponsorAdminService  # noqa: TC001

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


class AdminSponsorsController(Controller):
    """Controller for admin sponsor management."""

    path = urls.ADMIN_SPONSORS
    tags = ["Admin"]
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_sponsorships(
        self,
        sponsor_admin_service: SponsorAdminService,
        status: Annotated[str | None, Parameter(description="Filter by status")] = None,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render sponsorship list page.

        Args:
            sponsor_admin_service: Sponsor admin service
            status: Filter by sponsorship status
            q: Search query
            limit: Maximum sponsorships per page
            offset: Pagination offset

        Returns:
            Sponsorship list template
        """
        sponsorships, total = await sponsor_admin_service.list_sponsorships(
            limit=limit,
            offset=offset,
            status=status,
            search=q,
        )
        stats = await sponsor_admin_service.get_stats()
        levels = await sponsor_admin_service.list_levels()

        return Template(
            template_name="admin/sponsors/list.html.jinja2",
            context={
                "title": "Sponsor Management",
                "description": "Manage sponsor applications and sponsorships",
                "sponsorships": sponsorships,
                "levels": levels,
                "stats": stats,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/sponsors")
    async def list_sponsors(
        self,
        sponsor_admin_service: SponsorAdminService,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render sponsors list page.

        Args:
            sponsor_admin_service: Sponsor admin service
            q: Search query
            limit: Maximum sponsors per page
            offset: Pagination offset

        Returns:
            Sponsors list template
        """
        sponsors, total = await sponsor_admin_service.list_sponsors(
            limit=limit,
            offset=offset,
            search=q,
        )
        stats = await sponsor_admin_service.get_stats()

        return Template(
            template_name="admin/sponsors/sponsors_list.html.jinja2",
            context={
                "title": "All Sponsors",
                "description": "View and manage all sponsors",
                "sponsors": sponsors,
                "stats": stats,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/{sponsorship_id:uuid}")
    async def get_sponsorship_detail(
        self,
        sponsor_admin_service: SponsorAdminService,
        sponsorship_id: UUID,
    ) -> Template | Response:
        """Render sponsorship detail page.

        Args:
            sponsor_admin_service: Sponsor admin service
            sponsorship_id: Sponsorship ID

        Returns:
            Sponsorship detail template or redirect if not found
        """
        sponsorship = await sponsor_admin_service.get_sponsorship(sponsorship_id)
        if not sponsorship:
            return Redirect("/admin/sponsors")

        return Template(
            template_name="admin/sponsors/detail.html.jinja2",
            context={
                "title": f"{sponsorship.sponsor.name} - Sponsorship Review",
                "description": f"Review sponsorship: {sponsorship.sponsor.name}",
                "sponsorship": sponsorship,
            },
        )

    @get("/{sponsorship_id:uuid}/preview")
    async def get_sponsorship_preview(
        self,
        sponsor_admin_service: SponsorAdminService,
        sponsorship_id: UUID,
    ) -> Template | Response:
        """Render sponsorship preview partial for modal.

        Args:
            sponsor_admin_service: Sponsor admin service
            sponsorship_id: Sponsorship ID

        Returns:
            Sponsorship preview partial or error response
        """
        sponsorship = await sponsor_admin_service.get_sponsorship(sponsorship_id)
        if not sponsorship:
            return Response(content="Sponsorship not found", status_code=404)

        return Template(
            template_name="admin/sponsors/partials/sponsorship_preview.html.jinja2",
            context={"sponsorship": sponsorship},
        )

    @post("/{sponsorship_id:uuid}/approve")
    async def approve_sponsorship(
        self,
        request: Request,
        sponsor_admin_service: SponsorAdminService,
        sponsorship_id: UUID,
    ) -> Template | Response:
        """Approve a sponsorship.

        Args:
            request: HTTP request
            sponsor_admin_service: Sponsor admin service
            sponsorship_id: Sponsorship ID

        Returns:
            Updated sponsorship row partial or error response
        """
        sponsorship = await sponsor_admin_service.approve_sponsorship(sponsorship_id)
        if not sponsorship:
            return Response(content="Sponsorship not found", status_code=404)

        return Template(
            template_name="admin/sponsors/partials/sponsorship_row.html.jinja2",
            context={"sponsorship": sponsorship},
        )

    @post("/{sponsorship_id:uuid}/reject")
    async def reject_sponsorship(
        self,
        request: Request,
        sponsor_admin_service: SponsorAdminService,
        sponsorship_id: UUID,
    ) -> Template | Response:
        """Reject a sponsorship.

        Args:
            request: HTTP request
            sponsor_admin_service: Sponsor admin service
            sponsorship_id: Sponsorship ID

        Returns:
            Updated sponsorship row partial or error response
        """
        sponsorship = await sponsor_admin_service.reject_sponsorship(sponsorship_id)
        if not sponsorship:
            return Response(content="Sponsorship not found", status_code=404)

        return Template(
            template_name="admin/sponsors/partials/sponsorship_row.html.jinja2",
            context={"sponsorship": sponsorship},
        )

    @post("/{sponsorship_id:uuid}/finalize")
    async def finalize_sponsorship(
        self,
        request: Request,
        sponsor_admin_service: SponsorAdminService,
        sponsorship_id: UUID,
    ) -> Template | Response:
        """Finalize a sponsorship.

        Args:
            request: HTTP request
            sponsor_admin_service: Sponsor admin service
            sponsorship_id: Sponsorship ID

        Returns:
            Updated sponsorship row partial or error response
        """
        sponsorship = await sponsor_admin_service.finalize_sponsorship(sponsorship_id)
        if not sponsorship:
            return Response(content="Sponsorship not found", status_code=404)

        return Template(
            template_name="admin/sponsors/partials/sponsorship_row.html.jinja2",
            context={"sponsorship": sponsorship},
        )

    @get("/sponsor/{sponsor_id:uuid}")
    async def get_sponsor_detail(
        self,
        sponsor_admin_service: SponsorAdminService,
        sponsor_id: UUID,
    ) -> Template | Response:
        """Render sponsor detail page.

        Args:
            sponsor_admin_service: Sponsor admin service
            sponsor_id: Sponsor ID

        Returns:
            Sponsor detail template or redirect if not found
        """
        sponsor = await sponsor_admin_service.get_sponsor(sponsor_id)
        if not sponsor:
            return Redirect("/admin/sponsors/sponsors")

        return Template(
            template_name="admin/sponsors/sponsor_detail.html.jinja2",
            context={
                "title": f"{sponsor.name} - Sponsor Details",
                "description": f"View sponsor: {sponsor.name}",
                "sponsor": sponsor,
            },
        )

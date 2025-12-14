"""Admin banners controller for banner management."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID  # noqa: TC003

from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_admin
from pydotorg.domains.admin import urls
from pydotorg.domains.banners.services import BannerService  # noqa: TC001

if TYPE_CHECKING:
    from litestar import Request


def _parse_date(date_str: str) -> datetime.date:
    """Parse a date string safely."""
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=datetime.UTC).date()


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


class AdminBannersController(Controller):
    """Controller for admin banner management."""

    path = urls.ADMIN_BANNERS
    include_in_schema = False
    guards = [require_admin]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_banners(
        self,
        request: Request,
        banner_service: BannerService,
        status: Annotated[str | None, Parameter(description="Filter by status")] = None,
        toast: Annotated[str | None, Parameter(description="Toast message type")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render banner management list page."""
        banners, total = await banner_service.list_and_count()

        if status == "active":
            banners = [b for b in banners if b.is_active]
            total = len(banners)
        elif status == "inactive":
            banners = [b for b in banners if not b.is_active]
            total = len(banners)

        active_count = sum(1 for b in banners if b.is_active) if status is None else None
        inactive_count = sum(1 for b in banners if not b.is_active) if status is None else None
        if status is None:
            all_banners, _ = await banner_service.list_and_count()
            active_count = sum(1 for b in all_banners if b.is_active)
            inactive_count = sum(1 for b in all_banners if not b.is_active)

        toast_message = None
        if toast == "created":
            toast_message = {"message": "Banner created successfully", "type": "success"}
        elif toast == "updated":
            toast_message = {"message": "Banner updated successfully", "type": "success"}
        elif toast == "deleted":
            toast_message = {"message": "Banner deleted successfully", "type": "success"}

        context = {
            "title": "Banner Management",
            "description": "Create and manage sitewide announcement banners",
            "banners": banners,
            "stats": {
                "total_banners": total,
                "active_banners": active_count,
                "inactive_banners": inactive_count,
            },
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
            "toast": toast_message,
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"
        if is_htmx and not is_boosted:
            return Template(
                template_name="admin/banners/partials/banners_list.html.jinja2",
                context=context,
            )

        return Template(
            template_name="admin/banners/list.html.jinja2",
            context=context,
        )

    @get("/{banner_id:uuid}")
    async def get_banner_detail(
        self,
        banner_service: BannerService,
        banner_id: UUID,
    ) -> Template | Response:
        """Render banner detail page."""
        banner = await banner_service.get(banner_id)
        if not banner:
            return Redirect("/admin/banners")

        return Template(
            template_name="admin/banners/detail.html.jinja2",
            context={
                "title": f"{banner.name} - Banner Detail",
                "description": f"View banner: {banner.name}",
                "banner": banner,
            },
        )

    @get("/new")
    async def new_banner_form(self) -> Template:
        """Render new banner creation form."""
        return Template(
            template_name="admin/banners/form.html.jinja2",
            context={
                "title": "Create New Banner",
                "description": "Create a new sitewide announcement banner",
                "banner": None,
                "is_new": True,
            },
        )

    @get("/{banner_id:uuid}/edit")
    async def edit_banner_form(
        self,
        banner_service: BannerService,
        banner_id: UUID,
    ) -> Template | Response:
        """Render banner edit form."""
        banner = await banner_service.get(banner_id)
        if not banner:
            return Redirect("/admin/banners")

        return Template(
            template_name="admin/banners/form.html.jinja2",
            context={
                "title": f"Edit Banner - {banner.name}",
                "description": f"Edit banner: {banner.name}",
                "banner": banner,
                "is_new": False,
            },
        )

    @post("/")
    async def create_banner(
        self,
        request: Request,
        banner_service: BannerService,
    ) -> Response:
        """Create a new banner."""
        form_data = await request.form()

        paths_raw = str(form_data.get("paths", "")).strip()
        paths = paths_raw if paths_raw else None

        banner_data = {
            "name": str(form_data.get("name", "")),
            "title": str(form_data.get("title", "")),
            "message": str(form_data.get("message", "")),
            "link": str(form_data.get("link", "")) or None,
            "link_text": str(form_data.get("link_text", "")) or None,
            "banner_type": str(form_data.get("banner_type", "info")),
            "target": str(form_data.get("target", "frontend")),
            "paths": paths,
            "is_active": form_data.get("is_active") == "on",
            "is_dismissible": form_data.get("is_dismissible") == "on",
            "is_sitewide": form_data.get("is_sitewide") == "on",
        }

        start_date = form_data.get("start_date")
        if start_date:
            banner_data["start_date"] = _parse_date(str(start_date))

        end_date = form_data.get("end_date")
        if end_date:
            banner_data["end_date"] = _parse_date(str(end_date))

        await banner_service.create(banner_data, auto_commit=True)

        return Response(
            content="",
            status_code=200,
            headers={
                "HX-Redirect": "/admin/banners?toast=created",
            },
        )

    @put("/{banner_id:uuid}")
    async def update_banner(
        self,
        request: Request,
        banner_service: BannerService,
        banner_id: UUID,
    ) -> Response:
        """Update a banner."""
        form_data = await request.form()

        paths_raw = str(form_data.get("paths", "")).strip()
        paths = paths_raw if paths_raw else None

        banner_data = {
            "name": str(form_data.get("name", "")),
            "title": str(form_data.get("title", "")),
            "message": str(form_data.get("message", "")),
            "link": str(form_data.get("link", "")) or None,
            "link_text": str(form_data.get("link_text", "")) or None,
            "banner_type": str(form_data.get("banner_type", "info")),
            "target": str(form_data.get("target", "frontend")),
            "paths": paths,
            "is_active": form_data.get("is_active") == "on",
            "is_dismissible": form_data.get("is_dismissible") == "on",
            "is_sitewide": form_data.get("is_sitewide") == "on",
        }

        start_date = form_data.get("start_date")
        if start_date:
            banner_data["start_date"] = _parse_date(str(start_date))
        else:
            banner_data["start_date"] = None

        end_date = form_data.get("end_date")
        if end_date:
            banner_data["end_date"] = _parse_date(str(end_date))
        else:
            banner_data["end_date"] = None

        await banner_service.update(banner_data, item_id=banner_id, auto_commit=True)

        return Response(
            content="",
            status_code=200,
            headers={
                "HX-Redirect": "/admin/banners?toast=updated",
            },
        )

    @post("/{banner_id:uuid}/toggle")
    async def toggle_banner_active(
        self,
        request: Request,
        banner_service: BannerService,
        banner_id: UUID,
    ) -> Template | Response:
        """Toggle banner active status."""
        banner = await banner_service.get(banner_id)
        if not banner:
            return Response(content="Banner not found", status_code=404)

        await banner_service.update({"is_active": not banner.is_active}, item_id=banner_id, auto_commit=True)
        updated_banner = await banner_service.get(banner_id)

        return Template(
            template_name="admin/banners/partials/banner_row.html.jinja2",
            context={"banner": updated_banner},
        )

    @delete("/{banner_id:uuid}", status_code=200)
    async def delete_banner(
        self,
        banner_service: BannerService,
        banner_id: UUID,
    ) -> Response:
        """Delete a banner."""
        banner = await banner_service.get(banner_id)
        if not banner:
            return Response(content="Banner not found", status_code=404)

        await banner_service.delete(banner_id, auto_commit=True)

        return Response(
            content="Deleted",
            status_code=200,
            headers={
                "HX-Trigger": '{"showToast": {"message": "Banner deleted", "type": "success"}}',
            },
        )

    @get("/{banner_id:uuid}/preview")
    async def get_banner_preview(
        self,
        banner_service: BannerService,
        banner_id: UUID,
    ) -> Template | Response:
        """Render banner preview partial for modal."""
        banner = await banner_service.get(banner_id)
        if not banner:
            return Response(content="Banner not found", status_code=404)

        return Template(
            template_name="admin/banners/partials/banner_preview.html.jinja2",
            context={"banner": banner},
        )

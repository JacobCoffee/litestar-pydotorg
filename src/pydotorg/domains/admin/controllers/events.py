"""Admin events controller for event management."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote
from uuid import UUID

from litestar import Controller, get, post
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.params import Parameter
from litestar.response import Redirect, Response, Template

from pydotorg.core.auth.guards import require_staff
from pydotorg.domains.admin import urls
from pydotorg.domains.admin.services.events import EventAdminService  # noqa: TC001

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


class AdminEventsController(Controller):
    """Controller for admin event management."""

    path = urls.ADMIN_EVENTS
    include_in_schema = False
    guards = [require_staff]
    exception_handlers = {
        NotAuthorizedException: _admin_auth_exception_handler,
        PermissionDeniedException: _admin_permission_exception_handler,
    }

    @get("/")
    async def list_events(
        self,
        request: Request,
        event_admin_service: EventAdminService,
        calendar_id: Annotated[str | None, Parameter(description="Filter by calendar")] = None,
        featured: Annotated[bool | None, Parameter(description="Filter by featured status")] = None,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        filter_type: Annotated[str | None, Parameter(description="Filter type", query="filter")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render events list page.

        Args:
            event_admin_service: Event admin service
            calendar_id: Filter by calendar ID
            featured: Filter by featured status
            q: Search query
            filter: Filter type (featured, upcoming)
            limit: Maximum events per page
            offset: Pagination offset

        Returns:
            Events list template
        """
        if q == "":
            q = None
        calendar_uuid: UUID | None = None
        if calendar_id and calendar_id.strip():
            with contextlib.suppress(ValueError):
                calendar_uuid = UUID(calendar_id)
        upcoming: bool | None = None
        if filter_type == "featured":
            featured = True
        elif filter_type == "upcoming":
            upcoming = True
        events, total = await event_admin_service.list_events(
            limit=limit,
            offset=offset,
            calendar_id=calendar_uuid,
            featured=featured,
            upcoming=upcoming,
            search=q,
        )
        stats = await event_admin_service.get_stats()
        calendars, _ = await event_admin_service.list_calendars(limit=100)

        context = {
            "title": "Event Management",
            "description": "Manage events and calendars",
            "events": events,
            "calendars": calendars,
            "stats": stats,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"
        if is_htmx and not is_boosted:
            return Template(
                template_name="admin/events/partials/events_list.html.jinja2",
                context=context,
            )

        return Template(
            template_name="admin/events/list.html.jinja2",
            context=context,
        )

    @get("/calendars")
    async def list_calendars(
        self,
        event_admin_service: EventAdminService,
        q: Annotated[str | None, Parameter(description="Search query")] = None,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template:
        """Render calendars list page.

        Args:
            event_admin_service: Event admin service
            q: Search query
            limit: Maximum calendars per page
            offset: Pagination offset

        Returns:
            Calendars list template
        """
        if q == "":
            q = None
        calendars, total = await event_admin_service.list_calendars(
            limit=limit,
            offset=offset,
            search=q,
        )
        stats = await event_admin_service.get_stats()

        return Template(
            template_name="admin/events/calendars_list.html.jinja2",
            context={
                "title": "Event Calendars",
                "description": "View and manage event calendars",
                "calendars": calendars,
                "stats": stats,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                },
            },
        )

    @get("/{event_id:uuid}")
    async def get_event_detail(
        self,
        event_admin_service: EventAdminService,
        event_id: UUID,
    ) -> Template | Response:
        """Render event detail page.

        Args:
            event_admin_service: Event admin service
            event_id: Event ID

        Returns:
            Event detail template or redirect if not found
        """
        event = await event_admin_service.get_event(event_id)
        if not event:
            return Redirect("/admin/events")

        return Template(
            template_name="admin/events/detail.html.jinja2",
            context={
                "title": f"{event.title} - Event Details",
                "description": f"Review event: {event.title}",
                "event": event,
            },
        )

    @get("/{event_id:uuid}/preview")
    async def get_event_preview(
        self,
        event_admin_service: EventAdminService,
        event_id: UUID,
    ) -> Template | Response:
        """Render event preview partial for modal.

        Args:
            event_admin_service: Event admin service
            event_id: Event ID

        Returns:
            Event preview partial or error response
        """
        event = await event_admin_service.get_event(event_id)
        if not event:
            return Response(content="Event not found", status_code=404)

        return Template(
            template_name="admin/events/partials/event_preview.html.jinja2",
            context={"event": event},
        )

    @post("/{event_id:uuid}/feature")
    async def feature_event(
        self,
        request: Request,
        event_admin_service: EventAdminService,
        event_id: UUID,
    ) -> Template | Response:
        """Feature an event.

        Args:
            request: HTTP request
            event_admin_service: Event admin service
            event_id: Event ID

        Returns:
            Updated event row partial or error response
        """
        event = await event_admin_service.feature_event(event_id)
        if not event:
            return Response(content="Event not found", status_code=404)

        return Template(
            template_name="admin/events/partials/event_row.html.jinja2",
            context={"event": event},
        )

    @post("/{event_id:uuid}/unfeature")
    async def unfeature_event(
        self,
        request: Request,
        event_admin_service: EventAdminService,
        event_id: UUID,
    ) -> Template | Response:
        """Unfeature an event.

        Args:
            request: HTTP request
            event_admin_service: Event admin service
            event_id: Event ID

        Returns:
            Updated event row partial or error response
        """
        event = await event_admin_service.unfeature_event(event_id)
        if not event:
            return Response(content="Event not found", status_code=404)

        return Template(
            template_name="admin/events/partials/event_row.html.jinja2",
            context={"event": event},
        )

    @get("/calendars/{calendar_id:uuid}")
    async def get_calendar_detail(
        self,
        request: Request,
        event_admin_service: EventAdminService,
        calendar_id: UUID,
        limit: Annotated[int, Parameter(ge=1, le=100, description="Page size")] = 20,
        offset: Annotated[int, Parameter(ge=0, description="Offset")] = 0,
    ) -> Template | Response:
        """Render calendar detail page with paginated events.

        Args:
            request: HTTP request
            event_admin_service: Event admin service
            calendar_id: Calendar ID
            limit: Maximum events per page
            offset: Pagination offset

        Returns:
            Calendar detail template or redirect if not found
        """
        calendar = await event_admin_service.get_calendar(calendar_id)
        if not calendar:
            return Redirect("/admin/events/calendars")

        events, total = await event_admin_service.get_calendar_events(
            calendar_id=calendar_id,
            limit=limit,
            offset=offset,
        )

        context = {
            "title": f"{calendar.name} - Calendar Details",
            "description": f"View calendar: {calendar.name}",
            "calendar": calendar,
            "events": events,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }

        is_htmx = request.headers.get("HX-Request") == "true"
        is_boosted = request.headers.get("HX-Boosted") == "true"
        if is_htmx and not is_boosted:
            return Template(
                template_name="admin/events/partials/calendar_events_list.html.jinja2",
                context=context,
            )

        return Template(
            template_name="admin/events/calendar_detail.html.jinja2",
            context=context,
        )

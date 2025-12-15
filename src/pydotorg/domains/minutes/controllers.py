"""Minutes domain API and page controllers."""

from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.domains.minutes.schemas import (
    MinutesCreate,
    MinutesList,
    MinutesRead,
    MinutesUpdate,
)
from pydotorg.domains.minutes.services import MinutesService


class MinutesController(Controller):
    """Controller for Minutes CRUD operations."""

    path = "/api/v1/minutes"
    tags = ["Minutes"]

    @get("/")
    async def list_minutes(
        self,
        minutes_service: MinutesService,
        limit_offset: LimitOffset,
    ) -> list[MinutesList]:
        """List all minutes with pagination."""
        minutes, _total = await minutes_service.list_and_count(limit_offset)
        return [MinutesList.model_validate(minute) for minute in minutes]

    @get("/{minutes_id:uuid}")
    async def get_minutes(
        self,
        minutes_service: MinutesService,
        minutes_id: Annotated[UUID, Parameter(title="Minutes ID", description="The minutes ID")],
    ) -> MinutesRead:
        """Get minutes by ID."""
        minutes = await minutes_service.get(minutes_id)
        return MinutesRead.model_validate(minutes)

    @get("/slug/{slug:str}")
    async def get_minutes_by_slug(
        self,
        minutes_service: MinutesService,
        slug: Annotated[str, Parameter(title="Slug", description="The minutes slug")],
    ) -> MinutesRead:
        """Get minutes by slug."""
        minutes = await minutes_service.get_by_slug(slug)
        if not minutes:
            raise NotFoundException(f"Minutes with slug {slug} not found")
        return MinutesRead.model_validate(minutes)

    @get("/published")
    async def list_published_minutes(
        self,
        minutes_service: MinutesService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[MinutesList]:
        """List published minutes."""
        minutes = await minutes_service.get_published_minutes(limit=limit, offset=offset)
        return [MinutesList.model_validate(minute) for minute in minutes]

    @get("/date/{date:str}")
    async def get_minutes_by_date(
        self,
        minutes_service: MinutesService,
        date: Annotated[datetime.date, Parameter(title="Date", description="The meeting date (YYYY-MM-DD)")],
    ) -> MinutesRead:
        """Get minutes by date."""
        minutes = await minutes_service.get_by_date(date)
        if not minutes:
            raise NotFoundException(f"Minutes for date {date} not found")
        return MinutesRead.model_validate(minutes)

    @post("/")
    async def create_minutes(
        self,
        minutes_service: MinutesService,
        data: Annotated[MinutesCreate, Body(title="Minutes", description="Meeting minutes to create")],
    ) -> MinutesRead:
        """Create new minutes."""
        minutes = await minutes_service.create(data.model_dump())
        return MinutesRead.model_validate(minutes)

    @put("/{minutes_id:uuid}")
    async def update_minutes(
        self,
        minutes_service: MinutesService,
        data: Annotated[MinutesUpdate, Body(title="Minutes", description="Meeting minutes data to update")],
        minutes_id: Annotated[UUID, Parameter(title="Minutes ID", description="The minutes ID")],
    ) -> MinutesRead:
        """Update minutes."""
        update_data = data.model_dump(exclude_unset=True)
        minutes = await minutes_service.update(update_data, item_id=minutes_id)
        return MinutesRead.model_validate(minutes)

    @delete("/{minutes_id:uuid}")
    async def delete_minutes(
        self,
        minutes_service: MinutesService,
        minutes_id: Annotated[UUID, Parameter(title="Minutes ID", description="The minutes ID")],
    ) -> None:
        """Delete minutes."""
        await minutes_service.delete(minutes_id)


class MinutesPageController(Controller):
    """Controller for minutes HTML pages."""

    path = "/psf/records/board/minutes"
    include_in_schema = False

    @get("/")
    async def minutes_index(
        self,
        minutes_service: MinutesService,
    ) -> Template:
        """Render the PSF board minutes index page."""
        minutes_list = await minutes_service.get_published_minutes(limit=100)

        return Template(
            template_name="minutes/index.html.jinja2",
            context={
                "minutes_list": minutes_list,
                "page_title": "PSF Board Meeting Minutes",
            },
        )

    @get("/{slug:str}/")
    async def minutes_detail(
        self,
        minutes_service: MinutesService,
        slug: str,
    ) -> Template:
        """Render the minutes detail page."""
        minutes = await minutes_service.get_by_slug(slug)
        if not minutes:
            raise NotFoundException(f"Minutes with slug {slug} not found")

        return Template(
            template_name="minutes/detail.html.jinja2",
            context={
                "minutes": minutes,
                "page_title": f"Minutes - {minutes.date}",
            },
        )

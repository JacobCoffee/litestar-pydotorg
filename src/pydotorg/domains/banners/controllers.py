"""Banners domain API and page controllers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.domains.banners.schemas import (
    BannerCreate,
    BannerList,
    BannerRead,
    BannerUpdate,
)
from pydotorg.domains.banners.services import BannerService


class BannerController(Controller):
    """Controller for Banner CRUD operations."""

    path = "/api/v1/banners"
    tags = ["Banners"]

    @get("/")
    async def list_banners(
        self,
        banner_service: BannerService,
        limit_offset: LimitOffset,
    ) -> list[BannerList]:
        """List all banners with pagination."""
        banners, _total = await banner_service.list_and_count(limit_offset)
        return [BannerList.model_validate(banner) for banner in banners]

    @get("/{banner_id:uuid}")
    async def get_banner(
        self,
        banner_service: BannerService,
        banner_id: Annotated[UUID, Parameter(title="Banner ID", description="The banner ID")],
    ) -> BannerRead:
        """Get a banner by ID."""
        banner = await banner_service.get(banner_id)
        return BannerRead.model_validate(banner)

    @get("/name/{name:str}")
    async def get_banner_by_name(
        self,
        banner_service: BannerService,
        name: Annotated[str, Parameter(title="Name", description="The banner name")],
    ) -> BannerRead:
        """Get a banner by name."""
        banner = await banner_service.get_by_name(name)
        if not banner:
            raise NotFoundException(f"Banner with name {name} not found")
        return BannerRead.model_validate(banner)

    @get("/active")
    async def list_active_banners(
        self,
        banner_service: BannerService,
        check_dates: Annotated[bool, Parameter(description="Whether to check start/end dates")] | None = None,
    ) -> list[BannerRead]:
        """List active banners."""
        should_check_dates = check_dates if check_dates is not None else True
        current_date = datetime.now(UTC).date() if should_check_dates else None
        banners = await banner_service.get_active_banners(current_date=current_date)
        return [BannerRead.model_validate(banner) for banner in banners]

    @post("/")
    async def create_banner(
        self,
        banner_service: BannerService,
        data: Annotated[BannerCreate, Body(title="Banner", description="Banner to create")],
    ) -> BannerRead:
        """Create a new banner."""
        banner = await banner_service.create(data.model_dump())
        return BannerRead.model_validate(banner)

    @put("/{banner_id:uuid}")
    async def update_banner(
        self,
        banner_service: BannerService,
        data: Annotated[BannerUpdate, Body(title="Banner", description="Banner data to update")],
        banner_id: Annotated[UUID, Parameter(title="Banner ID", description="The banner ID")],
    ) -> BannerRead:
        """Update a banner."""
        update_data = data.model_dump(exclude_unset=True)
        banner = await banner_service.update(banner_id, update_data)
        return BannerRead.model_validate(banner)

    @delete("/{banner_id:uuid}")
    async def delete_banner(
        self,
        banner_service: BannerService,
        banner_id: Annotated[UUID, Parameter(title="Banner ID", description="The banner ID")],
    ) -> None:
        """Delete a banner."""
        await banner_service.delete(banner_id)


class BannersPageController(Controller):
    """Controller for banners HTML pages (admin preview)."""

    path = "/admin/banners"
    include_in_schema = False

    @get("/")
    async def banners_index(
        self,
        banner_service: BannerService,
    ) -> Template:
        """Render the banners admin preview page."""
        banners, _ = await banner_service.list_and_count()
        active_banners = await banner_service.get_active_banners()

        return Template(
            template_name="banners/index.html.jinja2",
            context={
                "banners": banners,
                "active_banners": active_banners,
                "page_title": "Banner Management",
            },
        )

    @get("/{name:str}/preview/")
    async def banner_preview(
        self,
        banner_service: BannerService,
        name: str,
    ) -> Template:
        """Render the banner preview page."""
        banner = await banner_service.get_by_name(name)
        if not banner:
            raise NotFoundException(f"Banner with name {name} not found")

        return Template(
            template_name="banners/preview.html.jinja2",
            context={
                "banner": banner,
                "page_title": f"Banner Preview - {banner.name}",
            },
        )

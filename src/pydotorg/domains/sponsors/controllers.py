"""Sponsors domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

from pydotorg.domains.sponsors.models import SponsorshipStatus
from pydotorg.domains.sponsors.schemas import (
    SponsorCreate,
    SponsorPublic,
    SponsorRead,
    SponsorshipCreate,
    SponsorshipLevelCreate,
    SponsorshipLevelRead,
    SponsorshipLevelUpdate,
    SponsorshipPublic,
    SponsorshipRead,
    SponsorshipUpdate,
    SponsorUpdate,
)
from pydotorg.domains.sponsors.services import (
    SponsorService,
    SponsorshipLevelService,
    SponsorshipService,
)


class SponsorshipLevelController(Controller):
    """Controller for SponsorshipLevel CRUD operations."""

    path = "/api/v1/sponsorship-levels"
    tags = ["Sponsors"]

    @get("/")
    async def list_levels(
        self,
        level_service: SponsorshipLevelService,
        limit_offset: LimitOffset,
    ) -> list[SponsorshipLevelRead]:
        """List all sponsorship levels with pagination."""
        levels, _total = await level_service.list_and_count(limit_offset)
        return [SponsorshipLevelRead.model_validate(level) for level in levels]

    @get("/ordered")
    async def list_ordered_levels(
        self,
        level_service: SponsorshipLevelService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipLevelRead]:
        """List sponsorship levels ordered by order field."""
        levels = await level_service.list_ordered(limit=limit, offset=offset)
        return [SponsorshipLevelRead.model_validate(level) for level in levels]

    @get("/{level_id:uuid}")
    async def get_level(
        self,
        level_service: SponsorshipLevelService,
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
    ) -> SponsorshipLevelRead:
        """Get a sponsorship level by ID."""
        level = await level_service.get(level_id)
        return SponsorshipLevelRead.model_validate(level)

    @get("/by-slug/{slug:str}")
    async def get_level_by_slug(
        self,
        level_service: SponsorshipLevelService,
        slug: Annotated[str, Parameter(title="Slug", description="The level slug")],
    ) -> SponsorshipLevelRead:
        """Get a sponsorship level by slug."""
        level = await level_service.get_by_slug(slug)
        if not level:
            msg = f"Sponsorship level with slug {slug} not found"
            raise NotFoundException(msg)
        return SponsorshipLevelRead.model_validate(level)

    @post("/")
    async def create_level(
        self,
        level_service: SponsorshipLevelService,
        data: SponsorshipLevelCreate,
    ) -> SponsorshipLevelRead:
        """Create a new sponsorship level."""
        level = await level_service.create_level(data)
        return SponsorshipLevelRead.model_validate(level)

    @put("/{level_id:uuid}")
    async def update_level(
        self,
        level_service: SponsorshipLevelService,
        data: SponsorshipLevelUpdate,
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
    ) -> SponsorshipLevelRead:
        """Update a sponsorship level."""
        update_data = data.model_dump(exclude_unset=True)
        level = await level_service.update(level_id, update_data)
        return SponsorshipLevelRead.model_validate(level)

    @delete("/{level_id:uuid}")
    async def delete_level(
        self,
        level_service: SponsorshipLevelService,
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
    ) -> None:
        """Delete a sponsorship level."""
        await level_service.delete(level_id)


class SponsorController(Controller):
    """Controller for Sponsor CRUD operations."""

    path = "/api/v1/sponsors"
    tags = ["Sponsors"]

    @get("/")
    async def list_sponsors(
        self,
        sponsor_service: SponsorService,
        limit_offset: LimitOffset,
    ) -> list[SponsorRead]:
        """List all sponsors with pagination."""
        sponsors, _total = await sponsor_service.list_and_count(limit_offset)
        return [SponsorRead.model_validate(sponsor) for sponsor in sponsors]

    @get("/active")
    async def list_active_sponsors(
        self,
        sponsor_service: SponsorService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorPublic]:
        """List sponsors with active sponsorships."""
        sponsors = await sponsor_service.list_with_active_sponsorships(limit=limit, offset=offset)
        return [SponsorPublic.model_validate(sponsor) for sponsor in sponsors]

    @get("/{sponsor_id:uuid}")
    async def get_sponsor(
        self,
        sponsor_service: SponsorService,
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
    ) -> SponsorRead:
        """Get a sponsor by ID."""
        sponsor = await sponsor_service.get(sponsor_id)
        return SponsorRead.model_validate(sponsor)

    @get("/by-slug/{slug:str}")
    async def get_sponsor_by_slug(
        self,
        sponsor_service: SponsorService,
        slug: Annotated[str, Parameter(title="Slug", description="The sponsor slug")],
    ) -> SponsorPublic:
        """Get a sponsor by slug."""
        sponsor = await sponsor_service.get_by_slug(slug)
        if not sponsor:
            msg = f"Sponsor with slug {slug} not found"
            raise NotFoundException(msg)
        return SponsorPublic.model_validate(sponsor)

    @post("/")
    async def create_sponsor(
        self,
        sponsor_service: SponsorService,
        data: SponsorCreate,
    ) -> SponsorRead:
        """Create a new sponsor."""
        sponsor = await sponsor_service.create_sponsor(data)
        return SponsorRead.model_validate(sponsor)

    @put("/{sponsor_id:uuid}")
    async def update_sponsor(
        self,
        sponsor_service: SponsorService,
        data: SponsorUpdate,
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
    ) -> SponsorRead:
        """Update a sponsor."""
        update_data = data.model_dump(exclude_unset=True)
        sponsor = await sponsor_service.update(sponsor_id, update_data)
        return SponsorRead.model_validate(sponsor)

    @delete("/{sponsor_id:uuid}")
    async def delete_sponsor(
        self,
        sponsor_service: SponsorService,
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
    ) -> None:
        """Delete a sponsor."""
        await sponsor_service.delete(sponsor_id)


class SponsorshipController(Controller):
    """Controller for Sponsorship CRUD operations."""

    path = "/api/v1/sponsorships"
    tags = ["Sponsors"]

    @get("/")
    async def list_sponsorships(
        self,
        sponsorship_service: SponsorshipService,
        limit_offset: LimitOffset,
    ) -> list[SponsorshipRead]:
        """List all sponsorships with pagination."""
        sponsorships, _total = await sponsorship_service.list_and_count(limit_offset)
        return [SponsorshipRead.model_validate(sponsorship) for sponsorship in sponsorships]

    @get("/active")
    async def list_active_sponsorships(
        self,
        sponsorship_service: SponsorshipService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipPublic]:
        """List active sponsorships."""
        sponsorships = await sponsorship_service.list_active(limit=limit, offset=offset)
        return [SponsorshipPublic.model_validate(sponsorship) for sponsorship in sponsorships]

    @get("/by-sponsor/{sponsor_id:uuid}")
    async def list_by_sponsor(
        self,
        sponsorship_service: SponsorshipService,
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipRead]:
        """List sponsorships for a specific sponsor."""
        sponsorships = await sponsorship_service.list_by_sponsor_id(
            sponsor_id,
            limit=limit,
            offset=offset,
        )
        return [SponsorshipRead.model_validate(sponsorship) for sponsorship in sponsorships]

    @get("/by-level/{level_id:uuid}")
    async def list_by_level(
        self,
        sponsorship_service: SponsorshipService,
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipRead]:
        """List sponsorships for a specific level."""
        sponsorships = await sponsorship_service.list_by_level_id(
            level_id,
            limit=limit,
            offset=offset,
        )
        return [SponsorshipRead.model_validate(sponsorship) for sponsorship in sponsorships]

    @get("/by-status/{status:str}")
    async def list_by_status(
        self,
        sponsorship_service: SponsorshipService,
        status: Annotated[str, Parameter(title="Status", description="The sponsorship status")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipRead]:
        """List sponsorships by status."""
        try:
            status_enum = SponsorshipStatus(status)
        except ValueError as e:
            msg = f"Invalid status: {status}"
            raise ValueError(msg) from e

        sponsorships = await sponsorship_service.list_by_status(
            status_enum,
            limit=limit,
            offset=offset,
        )
        return [SponsorshipRead.model_validate(sponsorship) for sponsorship in sponsorships]

    @get("/{sponsorship_id:uuid}")
    async def get_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> SponsorshipRead:
        """Get a sponsorship by ID."""
        sponsorship = await sponsorship_service.get(sponsorship_id)
        return SponsorshipRead.model_validate(sponsorship)

    @post("/")
    async def create_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        data: SponsorshipCreate,
    ) -> SponsorshipRead:
        """Create a new sponsorship."""
        sponsorship = await sponsorship_service.create_sponsorship(data)
        return SponsorshipRead.model_validate(sponsorship)

    @put("/{sponsorship_id:uuid}")
    async def update_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        data: SponsorshipUpdate,
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> SponsorshipRead:
        """Update a sponsorship."""
        update_data = data.model_dump(exclude_unset=True)
        sponsorship = await sponsorship_service.update(sponsorship_id, update_data)
        return SponsorshipRead.model_validate(sponsorship)

    @patch("/{sponsorship_id:uuid}/approve")
    async def approve_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> SponsorshipRead:
        """Approve a sponsorship."""
        sponsorship = await sponsorship_service.approve(sponsorship_id)
        return SponsorshipRead.model_validate(sponsorship)

    @patch("/{sponsorship_id:uuid}/reject")
    async def reject_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> SponsorshipRead:
        """Reject a sponsorship."""
        sponsorship = await sponsorship_service.reject(sponsorship_id)
        return SponsorshipRead.model_validate(sponsorship)

    @patch("/{sponsorship_id:uuid}/finalize")
    async def finalize_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> SponsorshipRead:
        """Finalize a sponsorship."""
        sponsorship = await sponsorship_service.finalize(sponsorship_id)
        return SponsorshipRead.model_validate(sponsorship)

    @delete("/{sponsorship_id:uuid}")
    async def delete_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> None:
        """Delete a sponsorship."""
        await sponsorship_service.delete(sponsorship_id)


class SponsorRenderController(Controller):
    """Controller for rendering sponsor pages as HTML."""

    path = "/sponsors"
    include_in_schema = False

    @get("/")
    async def render_sponsors_list(
        self,
        sponsor_service: SponsorService,
        sponsorship_service: SponsorshipService,
    ) -> Template:
        """Render sponsors list page."""
        sponsors = await sponsor_service.list_with_active_sponsorships(limit=100)
        active_sponsorships = await sponsorship_service.list_active(limit=100)

        return Template(
            template_name="sponsors/list.html.jinja2",
            context={
                "sponsors": sponsors,
                "active_sponsorships": active_sponsorships,
                "title": "Our Sponsors",
                "description": "Companies and organizations that support Python",
            },
        )

    @get("/{slug:str}")
    async def render_sponsor_detail(
        self,
        sponsor_service: SponsorService,
        sponsorship_service: SponsorshipService,
        slug: Annotated[str, Parameter(title="Slug", description="The sponsor slug")],
    ) -> Template:
        """Render a sponsor detail page."""
        sponsor = await sponsor_service.get_by_slug(slug)
        if not sponsor:
            msg = f"Sponsor with slug {slug} not found"
            raise NotFoundException(msg)

        sponsorships = await sponsorship_service.list_by_sponsor_id(sponsor.id, limit=100)

        return Template(
            template_name="sponsors/detail.html.jinja2",
            context={
                "sponsor": sponsor,
                "sponsorships": sponsorships,
                "title": sponsor.name,
                "description": sponsor.description,
            },
        )

    @get("/apply/")
    async def render_apply_form(self) -> Template:
        """Render sponsor application form."""
        return Template(
            template_name="sponsors/apply.html.jinja2",
            context={
                "title": "Become a Sponsor",
                "description": "Support the Python community by becoming a sponsor",
            },
        )

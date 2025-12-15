"""Sponsors domain API controllers."""

from __future__ import annotations

import datetime
import re
from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.domains.sponsors.models import SponsorshipStatus
from pydotorg.domains.sponsors.schemas import (
    SponsorApplicationCreate,
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
        """List all sponsorship levels with pagination.

        Retrieves a paginated list of sponsorship tiers available for sponsors.
        Levels define benefits, pricing, and visibility for each sponsorship tier.

        Args:
            level_service: Service for sponsorship level database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of sponsorship levels with benefits and pricing.
        """
        levels, _total = await level_service.list_and_count(limit_offset)
        return [SponsorshipLevelRead.model_validate(level) for level in levels]

    @get("/ordered")
    async def list_ordered_levels(
        self,
        level_service: SponsorshipLevelService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipLevelRead]:
        """List sponsorship levels in display order.

        Retrieves sponsorship levels sorted by their display order field.
        Useful for rendering sponsor tiers in the correct hierarchy.

        Args:
            level_service: Service for sponsorship level database operations.
            limit: Maximum number of levels to return (1-1000).
            offset: Number of levels to skip for pagination.

        Returns:
            List of sponsorship levels sorted by display order.
        """
        levels = await level_service.list_ordered(limit=limit, offset=offset)
        return [SponsorshipLevelRead.model_validate(level) for level in levels]

    @get("/{level_id:uuid}")
    async def get_level(
        self,
        level_service: SponsorshipLevelService,
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
    ) -> SponsorshipLevelRead:
        """Retrieve a specific sponsorship level by its unique identifier.

        Fetches complete sponsorship level information including name, benefits,
        pricing, and display order.

        Args:
            level_service: Service for sponsorship level database operations.
            level_id: The unique UUID identifier of the sponsorship level.

        Returns:
            Complete sponsorship level details.

        Raises:
            NotFoundException: If no sponsorship level with the given ID exists.
        """
        level = await level_service.get(level_id)
        return SponsorshipLevelRead.model_validate(level)

    @get("/by-slug/{slug:str}")
    async def get_level_by_slug(
        self,
        level_service: SponsorshipLevelService,
        slug: Annotated[str, Parameter(title="Slug", description="The level slug")],
    ) -> SponsorshipLevelRead:
        """Look up a sponsorship level by its URL slug.

        Searches for a sponsorship level with the specified slug (e.g., "gold",
        "platinum") and returns its complete details.

        Args:
            level_service: Service for sponsorship level database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Complete sponsorship level details.

        Raises:
            NotFoundException: If no sponsorship level with the given slug exists.
        """
        level = await level_service.get_by_slug(slug)
        if not level:
            msg = f"Sponsorship level with slug {slug} not found"
            raise NotFoundException(msg)
        return SponsorshipLevelRead.model_validate(level)

    @post("/")
    async def create_level(
        self,
        level_service: SponsorshipLevelService,
        data: Annotated[
            SponsorshipLevelCreate, Body(title="Sponsorship Level", description="Sponsorship level to create")
        ],
    ) -> SponsorshipLevelRead:
        """Create a new sponsorship level tier.

        Creates a new sponsorship tier with the specified name, benefits,
        pricing, and display order. Levels organize sponsors by contribution.

        Args:
            level_service: Service for sponsorship level database operations.
            data: Sponsorship level creation payload with tier details.

        Returns:
            The newly created sponsorship level.

        Raises:
            ConflictError: If a level with the same slug exists.
        """
        level = await level_service.create_level(data)
        return SponsorshipLevelRead.model_validate(level)

    @put("/{level_id:uuid}")
    async def update_level(
        self,
        level_service: SponsorshipLevelService,
        data: Annotated[
            SponsorshipLevelUpdate, Body(title="Sponsorship Level", description="Sponsorship level data to update")
        ],
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
    ) -> SponsorshipLevelRead:
        """Update an existing sponsorship level.

        Modifies sponsorship level fields with the provided values. Can update
        name, benefits, pricing, and display order.

        Args:
            level_service: Service for sponsorship level database operations.
            data: Partial level update payload with fields to modify.
            level_id: The unique UUID identifier of the level to update.

        Returns:
            The updated sponsorship level with all current fields.

        Raises:
            NotFoundException: If no sponsorship level with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        level = await level_service.update(update_data, item_id=level_id)
        return SponsorshipLevelRead.model_validate(level)

    @delete("/{level_id:uuid}")
    async def delete_level(
        self,
        level_service: SponsorshipLevelService,
        level_id: Annotated[UUID, Parameter(title="Level ID", description="The level ID")],
    ) -> None:
        """Delete a sponsorship level.

        Permanently removes a sponsorship level from the system. Existing
        sponsorships using this level should be reassigned first.

        Args:
            level_service: Service for sponsorship level database operations.
            level_id: The unique UUID identifier of the level to delete.

        Raises:
            NotFoundException: If no sponsorship level with the given ID exists.
        """
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
        """List all sponsors with pagination.

        Retrieves a paginated list of all sponsor organizations including
        those with active and inactive sponsorships.

        Args:
            sponsor_service: Service for sponsor database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of sponsors with organization details.
        """
        sponsors, _total = await sponsor_service.list_and_count(limit_offset)
        return [SponsorRead.model_validate(sponsor) for sponsor in sponsors]

    @get("/active")
    async def list_active_sponsors(
        self,
        sponsor_service: SponsorService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorPublic]:
        """List sponsors with currently active sponsorships.

        Retrieves only sponsors that have at least one active sponsorship.
        Useful for displaying current supporters on the website.

        Args:
            sponsor_service: Service for sponsor database operations.
            limit: Maximum number of sponsors to return (1-1000).
            offset: Number of sponsors to skip for pagination.

        Returns:
            List of public sponsor profiles with active sponsorships.
        """
        sponsors = await sponsor_service.list_with_active_sponsorships(limit=limit, offset=offset)
        return [SponsorPublic.model_validate(sponsor) for sponsor in sponsors]

    @get("/{sponsor_id:uuid}")
    async def get_sponsor(
        self,
        sponsor_service: SponsorService,
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
    ) -> SponsorRead:
        """Retrieve a specific sponsor by their unique identifier.

        Fetches complete sponsor information including organization name,
        description, logo, website, and contact details.

        Args:
            sponsor_service: Service for sponsor database operations.
            sponsor_id: The unique UUID identifier of the sponsor.

        Returns:
            Complete sponsor details.

        Raises:
            NotFoundException: If no sponsor with the given ID exists.
        """
        sponsor = await sponsor_service.get(sponsor_id)
        return SponsorRead.model_validate(sponsor)

    @get("/by-slug/{slug:str}")
    async def get_sponsor_by_slug(
        self,
        sponsor_service: SponsorService,
        slug: Annotated[str, Parameter(title="Slug", description="The sponsor slug")],
    ) -> SponsorPublic:
        """Look up a sponsor by their URL slug.

        Searches for a sponsor with the specified slug and returns their
        public profile information.

        Args:
            sponsor_service: Service for sponsor database operations.
            slug: The URL-friendly slug identifier.

        Returns:
            Public sponsor profile information.

        Raises:
            NotFoundException: If no sponsor with the given slug exists.
        """
        sponsor = await sponsor_service.get_by_slug(slug)
        if not sponsor:
            msg = f"Sponsor with slug {slug} not found"
            raise NotFoundException(msg)
        return SponsorPublic.model_validate(sponsor)

    @post("/")
    async def create_sponsor(
        self,
        sponsor_service: SponsorService,
        data: Annotated[SponsorCreate, Body(title="Sponsor", description="Sponsor to create")],
    ) -> SponsorRead:
        """Create a new sponsor organization.

        Creates a new sponsor record with organization details including
        name, description, logo, and contact information.

        Args:
            sponsor_service: Service for sponsor database operations.
            data: Sponsor creation payload with organization details.

        Returns:
            The newly created sponsor.

        Raises:
            ConflictError: If a sponsor with the same slug exists.
        """
        sponsor = await sponsor_service.create_sponsor(data)
        return SponsorRead.model_validate(sponsor)

    @put("/{sponsor_id:uuid}")
    async def update_sponsor(
        self,
        sponsor_service: SponsorService,
        data: Annotated[SponsorUpdate, Body(title="Sponsor", description="Sponsor data to update")],
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
    ) -> SponsorRead:
        """Update an existing sponsor's information.

        Modifies sponsor fields with the provided values. Can update
        organization name, description, logo, and contact details.

        Args:
            sponsor_service: Service for sponsor database operations.
            data: Partial sponsor update payload with fields to modify.
            sponsor_id: The unique UUID identifier of the sponsor to update.

        Returns:
            The updated sponsor with all current fields.

        Raises:
            NotFoundException: If no sponsor with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        sponsor = await sponsor_service.update(update_data, item_id=sponsor_id)
        return SponsorRead.model_validate(sponsor)

    @delete("/{sponsor_id:uuid}")
    async def delete_sponsor(
        self,
        sponsor_service: SponsorService,
        sponsor_id: Annotated[UUID, Parameter(title="Sponsor ID", description="The sponsor ID")],
    ) -> None:
        """Permanently delete a sponsor organization.

        Removes a sponsor and disassociates their sponsorships from the
        system. This action is irreversible.

        Args:
            sponsor_service: Service for sponsor database operations.
            sponsor_id: The unique UUID identifier of the sponsor to delete.

        Raises:
            NotFoundException: If no sponsor with the given ID exists.
        """
        await sponsor_service.delete(sponsor_id)

    @post("/apply")
    async def apply_for_sponsorship(
        self,
        sponsor_service: SponsorService,
        sponsorship_service: SponsorshipService,
        sponsorship_level_service: SponsorshipLevelService,
        data: Annotated[
            SponsorApplicationCreate, Body(title="Sponsor Application", description="Sponsorship application data")
        ],
    ) -> dict:
        """Submit a sponsorship application.

        Creates a new sponsor record and sponsorship application with APPLIED status.

        Args:
            sponsor_service: Service for sponsor database operations.
            sponsorship_service: Service for sponsorship database operations.
            sponsorship_level_service: Service for sponsorship level database operations.
            data: Application form data including company info and contact details.

        Returns:
            Success confirmation message with sponsor ID.
        """
        slug = re.sub(r"[^a-z0-9]+", "-", data.company_name.lower()).strip("-")

        sponsor_data = SponsorCreate(
            name=data.company_name,
            slug=slug,
            description=data.description,
            landing_page_url=data.website,
            twitter_handle=data.twitter_handle,
            linked_in_page_url=data.linkedin_url,
            primary_phone=data.contact_phone,
            mailing_address_line_1=data.mailing_address,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
        )
        sponsor = await sponsor_service.create(sponsor_data.model_dump(exclude_unset=True))

        level = await sponsorship_level_service.get_by_slug(data.sponsorship_level)
        if not level:
            levels = await sponsorship_level_service.list_ordered(limit=1)
            level = levels[0] if levels else None

        if level:
            today = datetime.datetime.now(tz=datetime.UTC).date()
            sponsorship_data = SponsorshipCreate(
                sponsor_id=sponsor.id,
                level_id=level.id,
                status=SponsorshipStatus.APPLIED,
                applied_on=today,
                year=today.year,
            )
            await sponsorship_service.create(sponsorship_data.model_dump(exclude_unset=True))

        return {
            "message": "Thank you for your interest in sponsoring Python! Your application has been received and will be reviewed by our team within 5-7 business days.",
            "status": "success",
            "sponsor_id": str(sponsor.id),
        }


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
        """List all sponsorships with pagination.

        Retrieves a paginated list of all sponsorship agreements including
        pending, active, and expired sponsorships.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            limit_offset: Pagination parameters for limiting and offsetting results.

        Returns:
            List of sponsorships with status and term details.
        """
        sponsorships, _total = await sponsorship_service.list_and_count(limit_offset)
        return [SponsorshipRead.model_validate(sponsorship) for sponsorship in sponsorships]

    @get("/active")
    async def list_active_sponsorships(
        self,
        sponsorship_service: SponsorshipService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[SponsorshipPublic]:
        """List currently active sponsorships.

        Retrieves only sponsorships that are currently active and within
        their term dates. Useful for displaying current supporters.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            limit: Maximum number of sponsorships to return (1-1000).
            offset: Number of sponsorships to skip for pagination.

        Returns:
            List of active public sponsorship information.
        """
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
        """List all sponsorships for a specific sponsor.

        Retrieves the sponsorship history for an organization, including
        past, current, and pending sponsorships.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            sponsor_id: The unique UUID identifier of the sponsor.
            limit: Maximum number of sponsorships to return (1-1000).
            offset: Number of sponsorships to skip for pagination.

        Returns:
            List of sponsorships for the specified sponsor.
        """
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
        """List all sponsorships at a specific tier level.

        Retrieves sponsorships grouped by their sponsorship tier (e.g.,
        all Gold sponsors or all Platinum sponsors).

        Args:
            sponsorship_service: Service for sponsorship database operations.
            level_id: The unique UUID identifier of the sponsorship level.
            limit: Maximum number of sponsorships to return (1-1000).
            offset: Number of sponsorships to skip for pagination.

        Returns:
            List of sponsorships at the specified tier level.
        """
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
        """List sponsorships filtered by status.

        Retrieves sponsorships with a specific status such as pending,
        approved, active, or expired.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            status: The sponsorship status to filter by.
            limit: Maximum number of sponsorships to return (1-1000).
            offset: Number of sponsorships to skip for pagination.

        Returns:
            List of sponsorships with the specified status.

        Raises:
            ValueError: If the provided status is not a valid status value.
        """
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
        """Retrieve a specific sponsorship by its unique identifier.

        Fetches complete sponsorship information including sponsor, level,
        status, term dates, and benefits.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            sponsorship_id: The unique UUID identifier of the sponsorship.

        Returns:
            Complete sponsorship details.

        Raises:
            NotFoundException: If no sponsorship with the given ID exists.
        """
        sponsorship = await sponsorship_service.get(sponsorship_id)
        return SponsorshipRead.model_validate(sponsorship)

    @post("/")
    async def create_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        data: Annotated[SponsorshipCreate, Body(title="Sponsorship", description="Sponsorship to create")],
    ) -> SponsorshipRead:
        """Create a new sponsorship agreement.

        Creates a new sponsorship record associating a sponsor with a
        sponsorship level. Initially created in pending status.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            data: Sponsorship creation payload with sponsor and level IDs.

        Returns:
            The newly created sponsorship in pending status.

        Raises:
            NotFoundException: If the sponsor or level does not exist.
        """
        sponsorship = await sponsorship_service.create_sponsorship(data)
        return SponsorshipRead.model_validate(sponsorship)

    @put("/{sponsorship_id:uuid}")
    async def update_sponsorship(
        self,
        sponsorship_service: SponsorshipService,
        data: Annotated[SponsorshipUpdate, Body(title="Sponsorship", description="Sponsorship data to update")],
        sponsorship_id: Annotated[
            UUID,
            Parameter(title="Sponsorship ID", description="The sponsorship ID"),
        ],
    ) -> SponsorshipRead:
        """Update an existing sponsorship.

        Modifies sponsorship fields with the provided values. Can update
        level, term dates, and other agreement details.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            data: Partial sponsorship update payload with fields to modify.
            sponsorship_id: The unique UUID identifier of the sponsorship.

        Returns:
            The updated sponsorship with all current fields.

        Raises:
            NotFoundException: If no sponsorship with the given ID exists.
        """
        update_data = data.model_dump(exclude_unset=True)
        sponsorship = await sponsorship_service.update(update_data, item_id=sponsorship_id)
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
        """Approve a pending sponsorship application.

        Transitions a sponsorship from pending to approved status. Approved
        sponsorships can then be activated when the term begins.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            sponsorship_id: The unique UUID identifier of the sponsorship.

        Returns:
            The sponsorship with approved status.

        Raises:
            NotFoundException: If no sponsorship with the given ID exists.
            ValidationError: If the sponsorship is not in pending status.
        """
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
        """Reject a pending sponsorship application.

        Transitions a sponsorship from pending to rejected status. The
        sponsor will be notified of the rejection.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            sponsorship_id: The unique UUID identifier of the sponsorship.

        Returns:
            The sponsorship with rejected status.

        Raises:
            NotFoundException: If no sponsorship with the given ID exists.
            ValidationError: If the sponsorship is not in pending status.
        """
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
        """Finalize and activate an approved sponsorship.

        Transitions an approved sponsorship to active status, making it
        visible on the sponsors page and activating benefits.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            sponsorship_id: The unique UUID identifier of the sponsorship.

        Returns:
            The sponsorship with active status.

        Raises:
            NotFoundException: If no sponsorship with the given ID exists.
            ValidationError: If the sponsorship is not in approved status.
        """
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
        """Permanently delete a sponsorship record.

        Removes a sponsorship from the system. This action is irreversible.
        The sponsor organization record remains intact.

        Args:
            sponsorship_service: Service for sponsorship database operations.
            sponsorship_id: The unique UUID identifier of the sponsorship.

        Raises:
            NotFoundException: If no sponsorship with the given ID exists.
        """
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

"""Nominations domain API controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, Request, delete, get, patch, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Template

from pydotorg.core.auth.guards import require_authenticated
from pydotorg.domains.nominations.models import ElectionStatus
from pydotorg.domains.nominations.schemas import (
    ElectionCreate,
    ElectionRead,
    ElectionUpdate,
    NominationCreate,
    NominationRead,
    NomineeCreate,
    NomineeRead,
)
from pydotorg.domains.nominations.services import (
    ElectionService,
    NominationService,
    NomineeService,
)


class ElectionController(Controller):
    """Controller for Election CRUD operations."""

    path = "/api/v1/elections"
    tags = ["Nominations"]

    @get("/")
    async def list_elections(
        self,
        election_service: ElectionService,
        limit_offset: LimitOffset,
        status: Annotated[ElectionStatus | None, Parameter(description="Filter by election status")] = None,
    ) -> list[ElectionRead]:
        """List all elections with pagination."""
        if status:
            elections = await election_service.get_by_status(
                status, limit=limit_offset.limit, offset=limit_offset.offset
            )
            return [ElectionRead.model_validate(e) for e in elections]

        elections, _total = await election_service.list_and_count(limit_offset)
        return [ElectionRead.model_validate(e) for e in elections]

    @get("/active")
    async def list_active_elections(
        self,
        election_service: ElectionService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[ElectionRead]:
        """List active elections."""
        elections = await election_service.get_active_elections(limit=limit, offset=offset)
        return [ElectionRead.model_validate(e) for e in elections]

    @get("/{election_id:uuid}")
    async def get_election(
        self,
        election_service: ElectionService,
        election_id: Annotated[UUID, Parameter(title="Election ID", description="The election ID")],
    ) -> ElectionRead:
        """Get an election by ID."""
        election = await election_service.get(election_id)
        return ElectionRead.model_validate(election)

    @post("/")
    async def create_election(
        self,
        election_service: ElectionService,
        data: Annotated[ElectionCreate, Body(title="Election", description="Election to create")],
    ) -> ElectionRead:
        """Create a new election (staff only)."""
        election = await election_service.create_election(data)
        return ElectionRead.model_validate(election)

    @put("/{election_id:uuid}")
    async def update_election(
        self,
        election_service: ElectionService,
        data: Annotated[ElectionUpdate, Body(title="Election", description="Election data to update")],
        election_id: Annotated[UUID, Parameter(title="Election ID", description="The election ID")],
    ) -> ElectionRead:
        """Update an election (staff only)."""
        update_data = data.model_dump(exclude_unset=True)
        election = await election_service.update(election_id, update_data)
        return ElectionRead.model_validate(election)

    @delete("/{election_id:uuid}")
    async def delete_election(
        self,
        election_service: ElectionService,
        election_id: Annotated[UUID, Parameter(title="Election ID", description="The election ID")],
    ) -> None:
        """Delete an election (staff only)."""
        await election_service.delete(election_id)


class NomineeController(Controller):
    """Controller for Nominee CRUD operations."""

    path = "/api/v1/nominees"
    tags = ["Nominations"]

    @get("/")
    async def list_nominees(
        self,
        nominee_service: NomineeService,
        limit_offset: LimitOffset,
        election_id: Annotated[UUID | None, Parameter(description="Filter by election ID")] = None,
    ) -> list[NomineeRead]:
        """List all nominees with pagination."""
        if election_id:
            nominees = await nominee_service.get_by_election(
                election_id, limit=limit_offset.limit, offset=limit_offset.offset
            )
            return [NomineeRead.model_validate(n) for n in nominees]

        nominees, _total = await nominee_service.list_and_count(limit_offset)
        return [NomineeRead.model_validate(n) for n in nominees]

    @get("/{nominee_id:uuid}")
    async def get_nominee(
        self,
        nominee_service: NomineeService,
        nominee_id: Annotated[UUID, Parameter(title="Nominee ID", description="The nominee ID")],
    ) -> NomineeRead:
        """Get a nominee by ID."""
        nominee = await nominee_service.get(nominee_id)
        return NomineeRead.model_validate(nominee)

    @get("/elections/{election_id:uuid}/accepted")
    async def list_accepted_nominees(
        self,
        nominee_service: NomineeService,
        election_id: Annotated[UUID, Parameter(title="Election ID", description="The election ID")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[NomineeRead]:
        """List accepted nominees for an election."""
        nominees = await nominee_service.get_accepted_nominees(election_id, limit=limit, offset=offset)
        return [NomineeRead.model_validate(n) for n in nominees]

    @post("/")
    async def create_nominee(
        self,
        nominee_service: NomineeService,
        data: Annotated[NomineeCreate, Body(title="Nominee", description="Nominee to create")],
    ) -> NomineeRead:
        """Create a new nominee."""
        nominee = await nominee_service.create_nominee(data.election_id, data.user_id)
        return NomineeRead.model_validate(nominee)

    @patch("/{nominee_id:uuid}/accept")
    async def accept_nomination(
        self,
        nominee_service: NomineeService,
        nominee_id: Annotated[UUID, Parameter(title="Nominee ID", description="The nominee ID")],
    ) -> NomineeRead:
        """Accept a nomination."""
        nominee = await nominee_service.accept_nomination(nominee_id)
        return NomineeRead.model_validate(nominee)

    @patch("/{nominee_id:uuid}/decline")
    async def decline_nomination(
        self,
        nominee_service: NomineeService,
        nominee_id: Annotated[UUID, Parameter(title="Nominee ID", description="The nominee ID")],
    ) -> None:
        """Decline a nomination."""
        await nominee_service.decline_nomination(nominee_id)

    @delete("/{nominee_id:uuid}")
    async def delete_nominee(
        self,
        nominee_service: NomineeService,
        nominee_id: Annotated[UUID, Parameter(title="Nominee ID", description="The nominee ID")],
    ) -> None:
        """Delete a nominee."""
        await nominee_service.delete(nominee_id)


class NominationController(Controller):
    """Controller for Nomination CRUD operations."""

    path = "/api/v1/nominations"
    tags = ["Nominations"]

    @get("/")
    async def list_nominations(
        self,
        nomination_service: NominationService,
        limit_offset: LimitOffset,
        nominee_id: Annotated[UUID | None, Parameter(description="Filter by nominee ID")] = None,
    ) -> list[NominationRead]:
        """List all nominations with pagination."""
        if nominee_id:
            nominations = await nomination_service.get_by_nominee(
                nominee_id, limit=limit_offset.limit, offset=limit_offset.offset
            )
            return [NominationRead.model_validate(n) for n in nominations]

        nominations, _total = await nomination_service.list_and_count(limit_offset)
        return [NominationRead.model_validate(n) for n in nominations]

    @get("/{nomination_id:uuid}")
    async def get_nomination(
        self,
        nomination_service: NominationService,
        nomination_id: Annotated[UUID, Parameter(title="Nomination ID", description="The nomination ID")],
    ) -> NominationRead:
        """Get a nomination by ID."""
        nomination = await nomination_service.get(nomination_id)
        return NominationRead.model_validate(nomination)

    @post("/", guards=[require_authenticated])
    async def create_nomination(
        self,
        request: Request,
        nomination_service: NominationService,
        data: Annotated[NominationCreate, Body(title="Nomination", description="Nomination to create")],
    ) -> NominationRead:
        """Create a new nomination."""
        nomination = await nomination_service.create_nomination(
            nominee_id=data.nominee_id,
            nominator_id=request.user.id,
            endorsement=data.endorsement,
        )
        return NominationRead.model_validate(nomination)

    @delete("/{nomination_id:uuid}")
    async def delete_nomination(
        self,
        nomination_service: NominationService,
        nomination_id: Annotated[UUID, Parameter(title="Nomination ID", description="The nomination ID")],
    ) -> None:
        """Delete a nomination."""
        await nomination_service.delete(nomination_id)


class NominationsRenderController(Controller):
    """Controller for rendering nominations as HTML."""

    path = "/nominations"
    include_in_schema = False

    @get("/")
    async def list_elections_html(
        self,
        election_service: ElectionService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 50,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> Template:
        """Render elections listing page."""
        elections = await election_service.get_active_elections(limit=limit, offset=offset)

        return Template(
            template_name="nominations/list.html.jinja2",
            context={
                "elections": elections,
                "title": "PSF Board Elections",
                "description": "View active PSF board elections and nominations",
            },
        )

    @get("/{slug:str}")
    async def get_election_html(
        self,
        election_service: ElectionService,
        nominee_service: NomineeService,
        slug: Annotated[str, Parameter(title="Election Slug", description="The election URL slug")],
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
    ) -> Template:
        """Render election detail page."""
        election = await election_service.get_by_slug(slug)

        if not election:
            msg = "Election not found"
            raise NotFoundException(msg)

        nominees = await nominee_service.get_accepted_nominees(election.id, limit=limit)

        return Template(
            template_name="nominations/detail.html.jinja2",
            context={
                "election": election,
                "nominees": nominees,
                "title": election.name,
                "description": election.description or f"PSF Board Election: {election.name}",
            },
        )

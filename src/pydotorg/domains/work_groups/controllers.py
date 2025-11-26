"""Work Groups domain API and page controllers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.response import Template

from pydotorg.domains.work_groups.schemas import (
    WorkGroupCreate,
    WorkGroupList,
    WorkGroupRead,
    WorkGroupUpdate,
)
from pydotorg.domains.work_groups.services import WorkGroupService


class WorkGroupController(Controller):
    """Controller for WorkGroup CRUD operations."""

    path = "/api/v1/work-groups"
    tags = ["work-groups"]

    @get("/")
    async def list_work_groups(
        self,
        work_group_service: WorkGroupService,
        limit_offset: LimitOffset,
    ) -> list[WorkGroupList]:
        """List all work groups with pagination."""
        work_groups, _total = await work_group_service.list_and_count(limit_offset)
        return [WorkGroupList.model_validate(work_group) for work_group in work_groups]

    @get("/{work_group_id:uuid}")
    async def get_work_group(
        self,
        work_group_service: WorkGroupService,
        work_group_id: Annotated[UUID, Parameter(title="Work Group ID", description="The work group ID")],
    ) -> WorkGroupRead:
        """Get a work group by ID."""
        work_group = await work_group_service.get(work_group_id)
        return WorkGroupRead.model_validate(work_group)

    @get("/slug/{slug:str}")
    async def get_work_group_by_slug(
        self,
        work_group_service: WorkGroupService,
        slug: Annotated[str, Parameter(title="Slug", description="The work group slug")],
    ) -> WorkGroupRead:
        """Get a work group by slug."""
        work_group = await work_group_service.get_by_slug(slug)
        if not work_group:
            raise NotFoundException(f"Work group with slug {slug} not found")
        return WorkGroupRead.model_validate(work_group)

    @get("/active")
    async def list_active_work_groups(
        self,
        work_group_service: WorkGroupService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[WorkGroupList]:
        """List active work groups."""
        work_groups = await work_group_service.get_active_work_groups(limit=limit, offset=offset)
        return [WorkGroupList.model_validate(work_group) for work_group in work_groups]

    @post("/")
    async def create_work_group(
        self,
        work_group_service: WorkGroupService,
        data: WorkGroupCreate,
    ) -> WorkGroupRead:
        """Create a new work group."""
        work_group = await work_group_service.create(data.model_dump())
        return WorkGroupRead.model_validate(work_group)

    @put("/{work_group_id:uuid}")
    async def update_work_group(
        self,
        work_group_service: WorkGroupService,
        data: WorkGroupUpdate,
        work_group_id: Annotated[UUID, Parameter(title="Work Group ID", description="The work group ID")],
    ) -> WorkGroupRead:
        """Update a work group."""
        update_data = data.model_dump(exclude_unset=True)
        work_group = await work_group_service.update(work_group_id, update_data)
        return WorkGroupRead.model_validate(work_group)

    @delete("/{work_group_id:uuid}")
    async def delete_work_group(
        self,
        work_group_service: WorkGroupService,
        work_group_id: Annotated[UUID, Parameter(title="Work Group ID", description="The work group ID")],
    ) -> None:
        """Delete a work group."""
        await work_group_service.delete(work_group_id)


class WorkGroupsPageController(Controller):
    """Controller for work groups HTML pages."""

    path = "/psf/workgroups"

    @get("/")
    async def work_groups_index(
        self,
        work_group_service: WorkGroupService,
    ) -> Template:
        """Render the work groups index page."""
        active_groups = await work_group_service.get_active_work_groups(limit=100)

        return Template(
            template_name="work_groups/index.html.jinja2",
            context={
                "work_groups": active_groups,
                "page_title": "PSF Work Groups",
            },
        )

    @get("/{slug:str}/")
    async def work_group_detail(
        self,
        work_group_service: WorkGroupService,
        slug: str,
    ) -> Template:
        """Render the work group detail page."""
        work_group = await work_group_service.get_by_slug(slug)
        if not work_group:
            raise NotFoundException(f"Work group with slug {slug} not found")

        return Template(
            template_name="work_groups/detail.html.jinja2",
            context={
                "work_group": work_group,
                "page_title": work_group.name,
            },
        )

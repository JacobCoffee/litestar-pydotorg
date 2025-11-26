"""Code Samples domain API controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from pydotorg.domains.codesamples.schemas import (
    CodeSampleCreate,
    CodeSampleList,
    CodeSampleRead,
    CodeSampleUpdate,
)

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import LimitOffset

    from pydotorg.domains.codesamples.services import CodeSampleService


class CodeSampleController(Controller):
    """Controller for CodeSample CRUD operations."""

    path = "/api/v1/code-samples"
    tags = ["code-samples"]

    @get("/")
    async def list_code_samples(
        self,
        code_sample_service: CodeSampleService,
        limit_offset: LimitOffset,
    ) -> list[CodeSampleList]:
        """List all code samples with pagination."""
        samples, _total = await code_sample_service.list_and_count(limit_offset)
        return [CodeSampleList.model_validate(sample) for sample in samples]

    @get("/{sample_id:uuid}")
    async def get_code_sample(
        self,
        code_sample_service: CodeSampleService,
        sample_id: Annotated[UUID, Parameter(title="Sample ID", description="The code sample ID")],
    ) -> CodeSampleRead:
        """Get a code sample by ID."""
        sample = await code_sample_service.get(sample_id)
        return CodeSampleRead.model_validate(sample)

    @get("/slug/{slug:str}")
    async def get_code_sample_by_slug(
        self,
        code_sample_service: CodeSampleService,
        slug: Annotated[str, Parameter(title="Slug", description="The code sample slug")],
    ) -> CodeSampleRead:
        """Get a code sample by slug."""
        sample = await code_sample_service.get_by_slug(slug)
        if not sample:
            raise NotFoundException(f"Code sample with slug {slug} not found")
        return CodeSampleRead.model_validate(sample)

    @get("/published")
    async def list_published_code_samples(
        self,
        code_sample_service: CodeSampleService,
        limit: Annotated[int, Parameter(ge=1, le=1000)] = 100,
        offset: Annotated[int, Parameter(ge=0)] = 0,
    ) -> list[CodeSampleList]:
        """List published code samples."""
        samples = await code_sample_service.get_published_samples(limit=limit, offset=offset)
        return [CodeSampleList.model_validate(sample) for sample in samples]

    @post("/")
    async def create_code_sample(
        self,
        code_sample_service: CodeSampleService,
        data: CodeSampleCreate,
    ) -> CodeSampleRead:
        """Create a new code sample."""
        sample = await code_sample_service.create(data.model_dump())
        return CodeSampleRead.model_validate(sample)

    @put("/{sample_id:uuid}")
    async def update_code_sample(
        self,
        code_sample_service: CodeSampleService,
        data: CodeSampleUpdate,
        sample_id: Annotated[UUID, Parameter(title="Sample ID", description="The code sample ID")],
    ) -> CodeSampleRead:
        """Update a code sample."""
        update_data = data.model_dump(exclude_unset=True)
        sample = await code_sample_service.update(sample_id, update_data)
        return CodeSampleRead.model_validate(sample)

    @delete("/{sample_id:uuid}")
    async def delete_code_sample(
        self,
        code_sample_service: CodeSampleService,
        sample_id: Annotated[UUID, Parameter(title="Sample ID", description="The code sample ID")],
    ) -> None:
        """Delete a code sample."""
        await code_sample_service.delete(sample_id)

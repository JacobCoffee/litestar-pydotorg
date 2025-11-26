"""Code Samples domain services for business logic."""

from __future__ import annotations

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.codesamples.models import CodeSample
from pydotorg.domains.codesamples.repositories import CodeSampleRepository


class CodeSampleService(SQLAlchemyAsyncRepositoryService[CodeSample]):
    """Service for CodeSample business logic."""

    repository_type = CodeSampleRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> CodeSample | None:
        """Get a code sample by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The code sample if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_published_samples(self, limit: int = 100, offset: int = 0) -> list[CodeSample]:
        """Get published code samples.

        Args:
            limit: Maximum number of samples to return.
            offset: Number of samples to skip.

        Returns:
            List of published code samples.
        """
        return await self.repository.get_published_samples(limit=limit, offset=offset)

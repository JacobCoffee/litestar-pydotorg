"""Code Samples domain repositories for database access."""

from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.codesamples.models import CodeSample


class CodeSampleRepository(SQLAlchemyAsyncRepository[CodeSample]):
    """Repository for CodeSample database operations."""

    model_type = CodeSample

    async def get_by_slug(self, slug: str) -> CodeSample | None:
        """Get a code sample by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The code sample if found, None otherwise.
        """
        statement = select(CodeSample).where(CodeSample.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_published_samples(self, limit: int = 100, offset: int = 0) -> list[CodeSample]:
        """Get published code samples.

        Args:
            limit: Maximum number of samples to return.
            offset: Number of samples to skip.

        Returns:
            List of published code samples ordered by created_at descending.
        """
        statement = (
            select(CodeSample)
            .where(CodeSample.is_published.is_(True))
            .order_by(CodeSample.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

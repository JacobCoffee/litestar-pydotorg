"""Success Stories domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.successstories.models import Story, StoryCategory

if TYPE_CHECKING:
    from uuid import UUID


class StoryCategoryRepository(SQLAlchemyAsyncRepository[StoryCategory]):
    """Repository for StoryCategory database operations."""

    model_type = StoryCategory

    async def get_by_slug(self, slug: str) -> StoryCategory | None:
        """Get a story category by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The story category if found, None otherwise.
        """
        statement = select(StoryCategory).where(StoryCategory.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class StoryRepository(SQLAlchemyAsyncRepository[Story]):
    """Repository for Story database operations."""

    model_type = Story

    async def get_by_slug(self, slug: str) -> Story | None:
        """Get a story by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The story if found, None otherwise.
        """
        statement = select(Story).where(Story.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_published_stories(self, limit: int = 100, offset: int = 0) -> list[Story]:
        """Get published stories.

        Args:
            limit: Maximum number of stories to return.
            offset: Number of stories to skip.

        Returns:
            List of published stories ordered by created_at descending.
        """
        statement = (
            select(Story)
            .where(Story.is_published.is_(True))
            .order_by(Story.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_featured_stories(self, limit: int = 10) -> list[Story]:
        """Get featured stories.

        Args:
            limit: Maximum number of stories to return.

        Returns:
            List of featured stories ordered by created_at descending.
        """
        statement = (
            select(Story)
            .where(Story.is_published.is_(True), Story.featured.is_(True))
            .order_by(Story.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_category_id(self, category_id: UUID, limit: int = 100, offset: int = 0) -> list[Story]:
        """Get stories by category.

        Args:
            category_id: The category ID to search for.
            limit: Maximum number of stories to return.
            offset: Number of stories to skip.

        Returns:
            List of stories ordered by created_at descending.
        """
        statement = (
            select(Story)
            .where(Story.category_id == category_id, Story.is_published.is_(True))
            .order_by(Story.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

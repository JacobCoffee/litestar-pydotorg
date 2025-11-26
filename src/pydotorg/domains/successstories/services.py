"""Success Stories domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.successstories.repositories import StoryCategoryRepository, StoryRepository

if TYPE_CHECKING:
    from uuid import UUID


class StoryCategoryService(SQLAlchemyAsyncRepositoryService[StoryCategory]):
    """Service for StoryCategory business logic."""

    repository_type = StoryCategoryRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> StoryCategory | None:
        """Get a story category by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The story category if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)


class StoryService(SQLAlchemyAsyncRepositoryService[Story]):
    """Service for Story business logic."""

    repository_type = StoryRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> Story | None:
        """Get a story by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The story if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_published_stories(self, limit: int = 100, offset: int = 0) -> list[Story]:
        """Get published stories.

        Args:
            limit: Maximum number of stories to return.
            offset: Number of stories to skip.

        Returns:
            List of published stories.
        """
        return await self.repository.get_published_stories(limit=limit, offset=offset)

    async def get_featured_stories(self, limit: int = 10) -> list[Story]:
        """Get featured stories.

        Args:
            limit: Maximum number of stories to return.

        Returns:
            List of featured stories.
        """
        return await self.repository.get_featured_stories(limit=limit)

    async def get_by_category_id(self, category_id: UUID, limit: int = 100, offset: int = 0) -> list[Story]:
        """Get stories by category.

        Args:
            category_id: The category ID to search for.
            limit: Maximum number of stories to return.
            offset: Number of stories to skip.

        Returns:
            List of stories.
        """
        return await self.repository.get_by_category_id(category_id, limit=limit, offset=offset)

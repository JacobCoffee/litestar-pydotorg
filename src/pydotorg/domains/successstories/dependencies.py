"""Success Stories domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.successstories.repositories import StoryCategoryRepository, StoryRepository
from pydotorg.domains.successstories.services import StoryCategoryService, StoryService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_story_category_repository(db_session: AsyncSession) -> StoryCategoryRepository:
    """Provide a StoryCategoryRepository instance."""
    return StoryCategoryRepository(session=db_session)


async def provide_story_category_service(db_session: AsyncSession) -> StoryCategoryService:
    """Provide a StoryCategoryService instance."""
    return StoryCategoryService(session=db_session)


async def provide_story_repository(db_session: AsyncSession) -> StoryRepository:
    """Provide a StoryRepository instance."""
    return StoryRepository(session=db_session)


async def provide_story_service(db_session: AsyncSession) -> StoryService:
    """Provide a StoryService instance."""
    return StoryService(session=db_session)


def get_successstories_dependencies() -> dict:
    """Get all success stories domain dependency providers."""
    return {
        "story_category_repository": provide_story_category_repository,
        "story_category_service": provide_story_category_service,
        "story_repository": provide_story_repository,
        "story_service": provide_story_service,
    }

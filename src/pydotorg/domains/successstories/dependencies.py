"""Success Stories domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.successstories.repositories import StoryCategoryRepository, StoryRepository
from pydotorg.domains.successstories.services import StoryCategoryService, StoryService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_story_category_repository(
    db_session: AsyncSession,
) -> AsyncGenerator[StoryCategoryRepository, None]:
    """Provide a StoryCategoryRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A StoryCategoryRepository instance.
    """
    async with StoryCategoryRepository(session=db_session) as repo:
        yield repo


async def provide_story_category_service(
    story_category_repository: StoryCategoryRepository,
) -> AsyncGenerator[StoryCategoryService, None]:
    """Provide a StoryCategoryService instance.

    Args:
        story_category_repository: The story category repository.

    Yields:
        A StoryCategoryService instance.
    """
    async with StoryCategoryService(repository=story_category_repository) as service:
        yield service


async def provide_story_repository(db_session: AsyncSession) -> AsyncGenerator[StoryRepository, None]:
    """Provide a StoryRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A StoryRepository instance.
    """
    async with StoryRepository(session=db_session) as repo:
        yield repo


async def provide_story_service(
    story_repository: StoryRepository,
) -> AsyncGenerator[StoryService, None]:
    """Provide a StoryService instance.

    Args:
        story_repository: The story repository.

    Yields:
        A StoryService instance.
    """
    async with StoryService(repository=story_repository) as service:
        yield service


def get_successstories_dependencies() -> dict:
    """Get all success stories domain dependency providers.

    Returns:
        Dictionary of dependency providers for the success stories domain.
    """
    return {
        "story_category_repository": provide_story_category_repository,
        "story_category_service": provide_story_category_service,
        "story_repository": provide_story_repository,
        "story_service": provide_story_service,
    }

"""Community domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.community.repositories import LinkRepository, PhotoRepository, PostRepository, VideoRepository
from pydotorg.domains.community.services import LinkService, PhotoService, PostService, VideoService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_post_repository(db_session: AsyncSession) -> AsyncGenerator[PostRepository, None]:
    """Provide a PostRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A PostRepository instance.
    """
    async with PostRepository(session=db_session) as repo:
        yield repo


async def provide_post_service(
    post_repository: PostRepository,
) -> AsyncGenerator[PostService, None]:
    """Provide a PostService instance.

    Args:
        post_repository: The post repository.

    Yields:
        A PostService instance.
    """
    async with PostService(repository=post_repository) as service:
        yield service


async def provide_photo_repository(db_session: AsyncSession) -> AsyncGenerator[PhotoRepository, None]:
    """Provide a PhotoRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A PhotoRepository instance.
    """
    async with PhotoRepository(session=db_session) as repo:
        yield repo


async def provide_photo_service(
    photo_repository: PhotoRepository,
) -> AsyncGenerator[PhotoService, None]:
    """Provide a PhotoService instance.

    Args:
        photo_repository: The photo repository.

    Yields:
        A PhotoService instance.
    """
    async with PhotoService(repository=photo_repository) as service:
        yield service


async def provide_video_repository(db_session: AsyncSession) -> AsyncGenerator[VideoRepository, None]:
    """Provide a VideoRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A VideoRepository instance.
    """
    async with VideoRepository(session=db_session) as repo:
        yield repo


async def provide_video_service(
    video_repository: VideoRepository,
) -> AsyncGenerator[VideoService, None]:
    """Provide a VideoService instance.

    Args:
        video_repository: The video repository.

    Yields:
        A VideoService instance.
    """
    async with VideoService(repository=video_repository) as service:
        yield service


async def provide_link_repository(db_session: AsyncSession) -> AsyncGenerator[LinkRepository, None]:
    """Provide a LinkRepository instance.

    Args:
        db_session: The database session.

    Yields:
        A LinkRepository instance.
    """
    async with LinkRepository(session=db_session) as repo:
        yield repo


async def provide_link_service(
    link_repository: LinkRepository,
) -> AsyncGenerator[LinkService, None]:
    """Provide a LinkService instance.

    Args:
        link_repository: The link repository.

    Yields:
        A LinkService instance.
    """
    async with LinkService(repository=link_repository) as service:
        yield service


def get_community_dependencies() -> dict:
    """Get all community domain dependency providers.

    Returns:
        Dictionary of dependency providers for the community domain.
    """
    return {
        "post_repository": provide_post_repository,
        "post_service": provide_post_service,
        "photo_repository": provide_photo_repository,
        "photo_service": provide_photo_service,
        "video_repository": provide_video_repository,
        "video_service": provide_video_service,
        "link_repository": provide_link_repository,
        "link_service": provide_link_service,
    }

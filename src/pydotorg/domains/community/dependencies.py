"""Community domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.community.repositories import LinkRepository, PhotoRepository, PostRepository, VideoRepository
from pydotorg.domains.community.services import LinkService, PhotoService, PostService, VideoService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_post_repository(db_session: AsyncSession) -> PostRepository:
    """Provide a PostRepository instance."""
    return PostRepository(session=db_session)


async def provide_post_service(db_session: AsyncSession) -> PostService:
    """Provide a PostService instance."""
    return PostService(session=db_session)


async def provide_photo_repository(db_session: AsyncSession) -> PhotoRepository:
    """Provide a PhotoRepository instance."""
    return PhotoRepository(session=db_session)


async def provide_photo_service(db_session: AsyncSession) -> PhotoService:
    """Provide a PhotoService instance."""
    return PhotoService(session=db_session)


async def provide_video_repository(db_session: AsyncSession) -> VideoRepository:
    """Provide a VideoRepository instance."""
    return VideoRepository(session=db_session)


async def provide_video_service(db_session: AsyncSession) -> VideoService:
    """Provide a VideoService instance."""
    return VideoService(session=db_session)


async def provide_link_repository(db_session: AsyncSession) -> LinkRepository:
    """Provide a LinkRepository instance."""
    return LinkRepository(session=db_session)


async def provide_link_service(db_session: AsyncSession) -> LinkService:
    """Provide a LinkService instance."""
    return LinkService(session=db_session)


def get_community_dependencies() -> dict:
    """Get all community domain dependency providers."""
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

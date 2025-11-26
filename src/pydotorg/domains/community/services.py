"""Community domain services for business logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.community.repositories import LinkRepository, PhotoRepository, PostRepository, VideoRepository

if TYPE_CHECKING:
    from uuid import UUID


class PostService(SQLAlchemyAsyncRepositoryService[Post]):
    """Service for Post business logic."""

    repository_type = PostRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> Post | None:
        """Get a post by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The post if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_published_posts(self, limit: int = 100, offset: int = 0) -> list[Post]:
        """Get published posts.

        Args:
            limit: Maximum number of posts to return.
            offset: Number of posts to skip.

        Returns:
            List of published posts.
        """
        return await self.repository.get_published_posts(limit=limit, offset=offset)

    async def get_by_creator_id(self, creator_id: UUID, limit: int = 100) -> list[Post]:
        """Get posts by creator.

        Args:
            creator_id: The creator ID to search for.
            limit: Maximum number of posts to return.

        Returns:
            List of posts.
        """
        return await self.repository.get_by_creator_id(creator_id, limit=limit)


class PhotoService(SQLAlchemyAsyncRepositoryService[Photo]):
    """Service for Photo business logic."""

    repository_type = PhotoRepository

    async def get_by_post_id(self, post_id: UUID) -> list[Photo]:
        """Get photos by post ID.

        Args:
            post_id: The post ID to search for.

        Returns:
            List of photos.
        """
        return await self.repository.get_by_post_id(post_id)

    async def get_standalone_photos(self, limit: int = 100) -> list[Photo]:
        """Get standalone photos not attached to posts.

        Args:
            limit: Maximum number of photos to return.

        Returns:
            List of standalone photos.
        """
        return await self.repository.get_standalone_photos(limit=limit)


class VideoService(SQLAlchemyAsyncRepositoryService[Video]):
    """Service for Video business logic."""

    repository_type = VideoRepository

    async def get_by_post_id(self, post_id: UUID) -> list[Video]:
        """Get videos by post ID.

        Args:
            post_id: The post ID to search for.

        Returns:
            List of videos.
        """
        return await self.repository.get_by_post_id(post_id)

    async def get_standalone_videos(self, limit: int = 100) -> list[Video]:
        """Get standalone videos not attached to posts.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of standalone videos.
        """
        return await self.repository.get_standalone_videos(limit=limit)


class LinkService(SQLAlchemyAsyncRepositoryService[Link]):
    """Service for Link business logic."""

    repository_type = LinkRepository

    async def get_by_post_id(self, post_id: UUID) -> list[Link]:
        """Get links by post ID.

        Args:
            post_id: The post ID to search for.

        Returns:
            List of links.
        """
        return await self.repository.get_by_post_id(post_id)

    async def get_standalone_links(self, limit: int = 100) -> list[Link]:
        """Get standalone links not attached to posts.

        Args:
            limit: Maximum number of links to return.

        Returns:
            List of standalone links.
        """
        return await self.repository.get_standalone_links(limit=limit)

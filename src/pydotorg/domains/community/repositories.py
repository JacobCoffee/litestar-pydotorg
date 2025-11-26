"""Community domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.community.models import Link, Photo, Post, Video

if TYPE_CHECKING:
    from uuid import UUID


class PostRepository(SQLAlchemyAsyncRepository[Post]):
    """Repository for Post database operations."""

    model_type = Post

    async def get_by_slug(self, slug: str) -> Post | None:
        """Get a post by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The post if found, None otherwise.
        """
        statement = select(Post).where(Post.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_published_posts(self, limit: int = 100, offset: int = 0) -> list[Post]:
        """Get published posts.

        Args:
            limit: Maximum number of posts to return.
            offset: Number of posts to skip.

        Returns:
            List of published posts ordered by created_at descending.
        """
        statement = (
            select(Post).where(Post.is_published.is_(True)).order_by(Post.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_creator_id(self, creator_id: UUID, limit: int = 100) -> list[Post]:
        """Get posts by creator.

        Args:
            creator_id: The creator ID to search for.
            limit: Maximum number of posts to return.

        Returns:
            List of posts ordered by created_at descending.
        """
        statement = select(Post).where(Post.creator_id == creator_id).order_by(Post.created_at.desc()).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class PhotoRepository(SQLAlchemyAsyncRepository[Photo]):
    """Repository for Photo database operations."""

    model_type = Photo

    async def get_by_post_id(self, post_id: UUID) -> list[Photo]:
        """Get photos by post ID.

        Args:
            post_id: The post ID to search for.

        Returns:
            List of photos.
        """
        statement = select(Photo).where(Photo.post_id == post_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_standalone_photos(self, limit: int = 100) -> list[Photo]:
        """Get standalone photos not attached to posts.

        Args:
            limit: Maximum number of photos to return.

        Returns:
            List of standalone photos.
        """
        statement = select(Photo).where(Photo.post_id.is_(None)).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class VideoRepository(SQLAlchemyAsyncRepository[Video]):
    """Repository for Video database operations."""

    model_type = Video

    async def get_by_post_id(self, post_id: UUID) -> list[Video]:
        """Get videos by post ID.

        Args:
            post_id: The post ID to search for.

        Returns:
            List of videos.
        """
        statement = select(Video).where(Video.post_id == post_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_standalone_videos(self, limit: int = 100) -> list[Video]:
        """Get standalone videos not attached to posts.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of standalone videos.
        """
        statement = select(Video).where(Video.post_id.is_(None)).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class LinkRepository(SQLAlchemyAsyncRepository[Link]):
    """Repository for Link database operations."""

    model_type = Link

    async def get_by_post_id(self, post_id: UUID) -> list[Link]:
        """Get links by post ID.

        Args:
            post_id: The post ID to search for.

        Returns:
            List of links.
        """
        statement = select(Link).where(Link.post_id == post_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_standalone_links(self, limit: int = 100) -> list[Link]:
        """Get standalone links not attached to posts.

        Args:
            limit: Maximum number of links to return.

        Returns:
            List of standalone links.
        """
        statement = select(Link).where(Link.post_id.is_(None)).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

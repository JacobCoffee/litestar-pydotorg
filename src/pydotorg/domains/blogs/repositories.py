"""Blogs domain repositories for database access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import select

from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog

if TYPE_CHECKING:
    import datetime
    from uuid import UUID


class FeedRepository(SQLAlchemyAsyncRepository[Feed]):
    """Repository for Feed database operations."""

    model_type = Feed

    async def get_by_feed_url(self, feed_url: str) -> Feed | None:
        """Get a feed by URL.

        Args:
            feed_url: The feed URL to search for.

        Returns:
            The feed if found, None otherwise.
        """
        statement = select(Feed).where(Feed.feed_url == feed_url)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_feeds(self, limit: int = 100) -> list[Feed]:
        """Get all active feeds.

        Args:
            limit: Maximum number of feeds to return.

        Returns:
            List of active feeds.
        """
        statement = select(Feed).where(Feed.is_active.is_(True)).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_feeds_needing_update(self, cutoff_time: datetime.datetime, limit: int = 100) -> list[Feed]:
        """Get feeds that need to be updated.

        Args:
            cutoff_time: Feeds not fetched since this time will be returned.
            limit: Maximum number of feeds to return.

        Returns:
            List of feeds needing update.
        """
        statement = (
            select(Feed)
            .where(
                Feed.is_active.is_(True),
                (Feed.last_fetched.is_(None)) | (Feed.last_fetched < cutoff_time),
            )
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class BlogEntryRepository(SQLAlchemyAsyncRepository[BlogEntry]):
    """Repository for BlogEntry database operations."""

    model_type = BlogEntry

    async def get_by_guid(self, guid: str) -> BlogEntry | None:
        """Get a blog entry by GUID.

        Args:
            guid: The GUID to search for.

        Returns:
            The blog entry if found, None otherwise.
        """
        statement = select(BlogEntry).where(BlogEntry.guid == guid)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_feed_id(self, feed_id: UUID, limit: int = 100, offset: int = 0) -> list[BlogEntry]:
        """Get all entries for a specific feed.

        Args:
            feed_id: The feed ID to search for.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of blog entries ordered by pub_date descending.
        """
        statement = (
            select(BlogEntry)
            .where(BlogEntry.feed_id == feed_id)
            .order_by(BlogEntry.pub_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_recent_entries(self, limit: int = 20, offset: int = 0) -> list[BlogEntry]:
        """Get recent blog entries across all feeds.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of recent blog entries ordered by pub_date descending.
        """
        statement = (
            select(BlogEntry)
            .join(BlogEntry.feed)
            .where(Feed.is_active.is_(True))
            .order_by(BlogEntry.pub_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_entries_by_feed_ids(self, feed_ids: list[UUID], limit: int = 100) -> list[BlogEntry]:
        """Get entries from multiple feeds.

        Args:
            feed_ids: List of feed IDs to get entries from.
            limit: Maximum number of entries to return.

        Returns:
            List of blog entries ordered by pub_date descending.
        """
        statement = (
            select(BlogEntry).where(BlogEntry.feed_id.in_(feed_ids)).order_by(BlogEntry.pub_date.desc()).limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_featured_entries(self, limit: int = 5) -> list[BlogEntry]:
        """Get featured blog entries (returns recent entries from active feeds).

        Args:
            limit: Maximum number of featured entries to return.

        Returns:
            List of recent blog entries ordered by pub_date descending.
        """
        statement = (
            select(BlogEntry)
            .join(BlogEntry.feed)
            .where(Feed.is_active.is_(True))
            .order_by(BlogEntry.pub_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class FeedAggregateRepository(SQLAlchemyAsyncRepository[FeedAggregate]):
    """Repository for FeedAggregate database operations."""

    model_type = FeedAggregate

    async def get_by_slug(self, slug: str) -> FeedAggregate | None:
        """Get a feed aggregate by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The feed aggregate if found, None otherwise.
        """
        statement = select(FeedAggregate).where(FeedAggregate.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()


class RelatedBlogRepository(SQLAlchemyAsyncRepository[RelatedBlog]):
    """Repository for RelatedBlog database operations."""

    model_type = RelatedBlog

    async def get_all_active(self, limit: int = 100) -> list[RelatedBlog]:
        """Get all related blogs.

        Args:
            limit: Maximum number of blogs to return.

        Returns:
            List of related blogs ordered by blog name.
        """
        statement = select(RelatedBlog).order_by(RelatedBlog.blog_name).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

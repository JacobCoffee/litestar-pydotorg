"""Blogs domain services for business logic."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import feedparser
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog
from pydotorg.domains.blogs.repositories import (
    BlogEntryRepository,
    FeedAggregateRepository,
    FeedRepository,
    RelatedBlogRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


class FeedService(SQLAlchemyAsyncRepositoryService[Feed]):
    """Service for Feed business logic."""

    repository_type = FeedRepository

    async def get_by_feed_url(self, feed_url: str) -> Feed | None:
        """Get a feed by URL.

        Args:
            feed_url: The feed URL to search for.

        Returns:
            The feed if found, None otherwise.
        """
        return await self.repository.get_by_feed_url(feed_url)

    async def get_active_feeds(self, limit: int = 100) -> list[Feed]:
        """Get all active feeds.

        Args:
            limit: Maximum number of feeds to return.

        Returns:
            List of active feeds.
        """
        return await self.repository.get_active_feeds(limit=limit)

    async def get_feeds_needing_update(self, cutoff_time: datetime, limit: int = 100) -> list[Feed]:
        """Get feeds that need to be updated.

        Args:
            cutoff_time: Feeds not fetched since this time will be returned.
            limit: Maximum number of feeds to return.

        Returns:
            List of feeds needing update.
        """
        return await self.repository.get_feeds_needing_update(cutoff_time=cutoff_time, limit=limit)

    async def fetch_feed(self, feed: Feed) -> list[BlogEntry]:
        """Fetch and parse a feed, creating or updating blog entries.

        Args:
            feed: The feed to fetch.

        Returns:
            List of blog entries created or updated.
        """
        try:
            parsed = feedparser.parse(feed.feed_url)

            if parsed.bozo:
                logger.warning(f"Feed {feed.name} has errors: {parsed.bozo_exception}")

            entries = []
            for entry in parsed.entries:
                guid = getattr(entry, "id", entry.link)
                pub_date_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)

                pub_date = datetime(*pub_date_struct[:6], tzinfo=UTC) if pub_date_struct else datetime.now(UTC)

                entry_data = {
                    "feed_id": feed.id,
                    "title": getattr(entry, "title", "Untitled"),
                    "summary": getattr(entry, "summary", None),
                    "content": getattr(entry, "content", [{}])[0].get("value") if hasattr(entry, "content") else None,
                    "url": entry.link,
                    "pub_date": pub_date,
                    "guid": guid,
                }

                try:
                    existing_entry = await self.repository.session.scalar(
                        self.repository.select_query().where(BlogEntry.guid == guid)
                    )

                    if existing_entry:
                        for key, value in entry_data.items():
                            if key not in {"feed_id", "guid"}:
                                setattr(existing_entry, key, value)
                        entries.append(existing_entry)
                    else:
                        new_entry = BlogEntry(**entry_data)
                        self.repository.session.add(new_entry)
                        entries.append(new_entry)

                except Exception:
                    logger.exception(f"Error processing entry {guid}")
                    continue

            feed.last_fetched = datetime.now(UTC)
            await self.repository.update(feed)
            await self.repository.session.commit()
        except Exception:
            logger.exception(f"Error fetching feed {feed.name}")
            return []
        else:
            return entries

    async def mark_feed_as_updated(self, feed_id: UUID) -> Feed:
        """Mark a feed as updated.

        Args:
            feed_id: The feed ID to update.

        Returns:
            The updated feed.
        """
        feed = await self.get(feed_id)
        if feed:
            feed.last_fetched = datetime.now(UTC)
            await self.repository.update(feed)
        return feed


class BlogEntryService(SQLAlchemyAsyncRepositoryService[BlogEntry]):
    """Service for BlogEntry business logic."""

    repository_type = BlogEntryRepository

    async def get_by_guid(self, guid: str) -> BlogEntry | None:
        """Get a blog entry by GUID.

        Args:
            guid: The GUID to search for.

        Returns:
            The blog entry if found, None otherwise.
        """
        return await self.repository.get_by_guid(guid)

    async def get_by_feed_id(self, feed_id: UUID, limit: int = 100, offset: int = 0) -> list[BlogEntry]:
        """Get all entries for a specific feed.

        Args:
            feed_id: The feed ID to search for.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of blog entries.
        """
        return await self.repository.get_by_feed_id(feed_id, limit=limit, offset=offset)

    async def get_recent_entries(self, limit: int = 20, offset: int = 0) -> list[BlogEntry]:
        """Get recent blog entries across all feeds.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of recent blog entries.
        """
        return await self.repository.get_recent_entries(limit=limit, offset=offset)

    async def get_entries_by_feed_ids(self, feed_ids: list[UUID], limit: int = 100) -> list[BlogEntry]:
        """Get entries from multiple feeds.

        Args:
            feed_ids: List of feed IDs to get entries from.
            limit: Maximum number of entries to return.

        Returns:
            List of blog entries.
        """
        return await self.repository.get_entries_by_feed_ids(feed_ids, limit=limit)


class FeedAggregateService(SQLAlchemyAsyncRepositoryService[FeedAggregate]):
    """Service for FeedAggregate business logic."""

    repository_type = FeedAggregateRepository
    match_fields = ["slug"]

    async def get_by_slug(self, slug: str) -> FeedAggregate | None:
        """Get a feed aggregate by slug.

        Args:
            slug: The slug to search for.

        Returns:
            The feed aggregate if found, None otherwise.
        """
        return await self.repository.get_by_slug(slug)

    async def get_entries_for_aggregate(
        self, aggregate_id: UUID, limit: int = 100
    ) -> tuple[FeedAggregate | None, list[BlogEntry]]:
        """Get all entries for a feed aggregate.

        Args:
            aggregate_id: The aggregate ID.
            limit: Maximum number of entries to return.

        Returns:
            Tuple of (aggregate, entries).
        """
        aggregate = await self.get(aggregate_id)
        if not aggregate:
            return None, []

        feed_ids = [feed.id for feed in aggregate.feeds]
        entries = await BlogEntryRepository(session=self.repository.session).get_entries_by_feed_ids(
            feed_ids, limit=limit
        )

        return aggregate, entries


class RelatedBlogService(SQLAlchemyAsyncRepositoryService[RelatedBlog]):
    """Service for RelatedBlog business logic."""

    repository_type = RelatedBlogRepository

    async def get_all_active(self, limit: int = 100) -> list[RelatedBlog]:
        """Get all related blogs.

        Args:
            limit: Maximum number of blogs to return.

        Returns:
            List of related blogs.
        """
        return await self.repository.get_all_active(limit=limit)

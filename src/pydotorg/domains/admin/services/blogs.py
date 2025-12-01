"""Admin blog management service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from pydotorg.domains.blogs.models import BlogEntry, Feed

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class BlogAdminService:
    """Service for admin blog management operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_feeds(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        *,
        is_active: bool | None = None,
    ) -> tuple[list[Feed], int]:
        """List feeds with filtering and pagination.

        Args:
            limit: Maximum number of feeds to return
            offset: Number of feeds to skip
            search: Search query for feed name or URL
            is_active: Filter by active status

        Returns:
            Tuple of (feeds list, total count)
        """
        query = select(Feed)

        if is_active is not None:
            query = query.where(Feed.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Feed.name.ilike(search_term),
                    Feed.website_url.ilike(search_term),
                    Feed.feed_url.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Feed.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        feeds = list(result.scalars().all())

        return feeds, total

    async def list_entries(
        self,
        limit: int = 20,
        offset: int = 0,
        feed_id: UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[BlogEntry], int]:
        """List blog entries with filtering and pagination.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            feed_id: Filter by feed ID
            search: Search query for entry title or content

        Returns:
            Tuple of (entries list, total count)
        """
        query = select(BlogEntry).options(selectinload(BlogEntry.feed))

        if feed_id:
            query = query.where(BlogEntry.feed_id == feed_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    BlogEntry.title.ilike(search_term),
                    BlogEntry.summary.ilike(search_term),
                    BlogEntry.content.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(BlogEntry.pub_date.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        entries = list(result.scalars().all())

        return entries, total

    async def get_feed(self, feed_id: UUID) -> Feed | None:
        """Get a feed by ID.

        Args:
            feed_id: Feed ID

        Returns:
            Feed if found, None otherwise
        """
        query = select(Feed).where(Feed.id == feed_id).options(selectinload(Feed.entries))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_entry(self, entry_id: UUID) -> BlogEntry | None:
        """Get a blog entry by ID.

        Args:
            entry_id: Entry ID

        Returns:
            BlogEntry if found, None otherwise
        """
        query = select(BlogEntry).where(BlogEntry.id == entry_id).options(selectinload(BlogEntry.feed))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def activate_feed(self, feed_id: UUID) -> Feed | None:
        """Activate a feed.

        Args:
            feed_id: Feed ID

        Returns:
            Updated feed if found, None otherwise
        """
        feed = await self.get_feed(feed_id)
        if not feed:
            return None

        feed.is_active = True
        await self.session.commit()
        await self.session.refresh(feed)
        return feed

    async def deactivate_feed(self, feed_id: UUID) -> Feed | None:
        """Deactivate a feed.

        Args:
            feed_id: Feed ID

        Returns:
            Updated feed if found, None otherwise
        """
        feed = await self.get_feed(feed_id)
        if not feed:
            return None

        feed.is_active = False
        await self.session.commit()
        await self.session.refresh(feed)
        return feed

    async def feature_entry(self, entry_id: UUID) -> BlogEntry | None:
        """Feature a blog entry.

        Args:
            entry_id: Entry ID

        Returns:
            Updated entry if found, None otherwise
        """
        entry = await self.get_entry(entry_id)
        if not entry:
            return None

        entry.is_featured = True
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def unfeature_entry(self, entry_id: UUID) -> BlogEntry | None:
        """Unfeature a blog entry.

        Args:
            entry_id: Entry ID

        Returns:
            Updated entry if found, None otherwise
        """
        entry = await self.get_entry(entry_id)
        if not entry:
            return None

        entry.is_featured = False
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_stats(self) -> dict:
        """Get blog statistics.

        Returns:
            Dictionary with blog stats
        """
        total_feeds_query = select(func.count()).select_from(Feed)
        total_feeds_result = await self.session.execute(total_feeds_query)
        total_feeds = total_feeds_result.scalar() or 0

        active_feeds_query = select(func.count()).where(Feed.is_active)
        active_feeds_result = await self.session.execute(active_feeds_query)
        active_feeds = active_feeds_result.scalar() or 0

        inactive_feeds_query = select(func.count()).where(~Feed.is_active)
        inactive_feeds_result = await self.session.execute(inactive_feeds_query)
        inactive_feeds = inactive_feeds_result.scalar() or 0

        total_entries_query = select(func.count()).select_from(BlogEntry)
        total_entries_result = await self.session.execute(total_entries_query)
        total_entries = total_entries_result.scalar() or 0

        today = datetime.now(tz=UTC).date()
        today_start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
        entries_today_query = select(func.count()).where(BlogEntry.pub_date >= today_start)
        entries_today_result = await self.session.execute(entries_today_query)
        entries_today = entries_today_result.scalar() or 0

        featured_entries_query = select(func.count()).where(BlogEntry.is_featured)
        featured_entries_result = await self.session.execute(featured_entries_query)
        featured_entries = featured_entries_result.scalar() or 0

        return {
            "total_feeds": total_feeds,
            "active_feeds": active_feeds,
            "inactive_feeds": inactive_feeds,
            "total_entries": total_entries,
            "entries_today": entries_today,
            "featured_entries": featured_entries,
        }

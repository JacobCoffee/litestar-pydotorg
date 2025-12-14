#!/usr/bin/env python
"""Import news/blog entries from Python.org RSS feeds.

This script fetches blog entries from Python's official RSS feeds
and imports them into our database.

Usage:
    uv run python scripts/import_news.py [--dry-run] [--refresh-all]

The script:
1. Uses the feeds defined in seed.py or adds official Python.org feeds
2. Fetches RSS/Atom content using feedparser
3. Creates/updates BlogEntry records
4. Merges entries from multiple feeds sorted by date
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click
import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydotorg.core.database import get_async_session_factory
from pydotorg.domains.blogs.models import BlogEntry, Feed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OFFICIAL_FEEDS = [
    {
        "name": "Python Software Foundation Blog",
        "website_url": "https://pyfound.blogspot.com",
        "feed_url": "https://pyfound.blogspot.com/feeds/posts/default?alt=rss",
    },
    {
        "name": "Python Insider",
        "website_url": "https://blog.python.org",
        "feed_url": "https://blog.python.org/feeds/posts/default?alt=rss",
    },
    {
        "name": "Planet Python",
        "website_url": "https://planetpython.org",
        "feed_url": "https://planetpython.org/rss20.xml",
    },
]


def parse_date(entry: dict[str, Any]) -> datetime:
    """Parse publication date from feed entry."""
    if entry.get("published_parsed"):
        return datetime(*entry["published_parsed"][:6], tzinfo=UTC)
    if entry.get("updated_parsed"):
        return datetime(*entry["updated_parsed"][:6], tzinfo=UTC)
    return datetime.now(UTC)


def get_entry_content(entry: dict[str, Any]) -> str | None:
    """Extract content from feed entry."""
    if entry.get("content"):
        return entry["content"][0].get("value", "")
    if "summary" in entry:
        return entry["summary"]
    return None


def get_entry_guid(entry: dict[str, Any], feed_url: str) -> str:
    """Get unique identifier for entry."""
    if "id" in entry:
        return entry["id"]
    if "link" in entry:
        return entry["link"]
    return f"{feed_url}#{entry.get('title', 'unknown')}"


async def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """Fetch and parse RSS/Atom feed."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return feedparser.parse(response.content)


async def ensure_feeds_exist(session: AsyncSession) -> list[Feed]:
    """Ensure official feeds exist in database."""
    feeds = []

    for feed_data in OFFICIAL_FEEDS:
        result = await session.execute(select(Feed).where(Feed.feed_url == feed_data["feed_url"]))
        feed = result.scalar_one_or_none()

        if feed is None:
            feed = Feed(
                name=feed_data["name"],
                website_url=feed_data["website_url"],
                feed_url=feed_data["feed_url"],
                is_active=True,
            )
            session.add(feed)
            await session.flush()
            logger.info(f"Created feed: {feed_data['name']}")

        feeds.append(feed)

    return feeds


async def import_feed_entries(
    session: AsyncSession,
    feed: Feed,
    dry_run: bool = False,
) -> dict[str, int]:
    """Import entries from a single feed."""
    stats = {"created": 0, "updated": 0, "skipped": 0}

    logger.info(f"Fetching: {feed.name} ({feed.feed_url})")

    try:
        parsed = await fetch_feed(feed.feed_url)
    except Exception as e:
        logger.error(f"Failed to fetch {feed.feed_url}: {e}")
        return stats

    if not parsed.entries:
        logger.warning(f"No entries found in {feed.name}")
        return stats

    logger.info(f"Found {len(parsed.entries)} entries in {feed.name}")

    for entry in parsed.entries:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        guid = get_entry_guid(entry, feed.feed_url)
        summary = entry.get("summary", "")
        content = get_entry_content(entry)
        pub_date = parse_date(entry)

        result = await session.execute(select(BlogEntry).where(BlogEntry.guid == guid))
        existing = result.scalar_one_or_none()

        if existing:
            existing.title = title
            existing.summary = summary
            existing.content = content
            existing.url = link
            existing.pub_date = pub_date
            stats["updated"] += 1
        else:
            blog_entry = BlogEntry(
                feed_id=feed.id,
                title=title,
                summary=summary,
                content=content,
                url=link,
                pub_date=pub_date,
                guid=guid,
            )
            session.add(blog_entry)
            stats["created"] += 1
            logger.debug(f"Created entry: {title[:50]}")

    feed.last_fetched = datetime.now(UTC)

    return stats


async def import_all_feeds(
    session: AsyncSession,
    dry_run: bool = False,
    refresh_all: bool = False,
) -> dict[str, int]:
    """Import entries from all active feeds."""
    total_stats = {"created": 0, "updated": 0, "skipped": 0}

    if refresh_all:
        feeds = await ensure_feeds_exist(session)
    else:
        result = await session.execute(select(Feed).where(Feed.is_active == True))  # noqa: E712
        feeds = list(result.scalars().all())

    if not feeds:
        feeds = await ensure_feeds_exist(session)

    for feed in feeds:
        stats = await import_feed_entries(session, feed, dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]

    if not dry_run:
        await session.commit()
        logger.info("Changes committed to database")
    else:
        await session.rollback()
        logger.info("Dry run - changes rolled back")

    return total_stats


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't actually save changes to database",
)
@click.option(
    "--refresh-all",
    is_flag=True,
    help="Refresh all feeds including ensuring official feeds exist",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(dry_run: bool, refresh_all: bool, verbose: bool) -> None:
    """Import blog entries from Python.org RSS feeds."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    async def run() -> None:
        session_factory = get_async_session_factory()

        async with session_factory() as session:
            stats = await import_all_feeds(session, dry_run, refresh_all)

            logger.info("=" * 50)
            logger.info("Import complete!")
            logger.info(f"  Created: {stats['created']} entries")
            logger.info(f"  Updated: {stats['updated']} entries")
            logger.info(f"  Skipped: {stats['skipped']} entries")
            if dry_run:
                logger.info("  (DRY RUN - no changes saved)")

    asyncio.run(run())


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Import job postings from Python.org RSS feed.

This script fetches job listings from python.org/jobs/feed/rss/
and imports them into our database.

Usage:
    uv run python scripts/import_jobs.py [--dry-run] [--limit N]

The script:
1. Fetches the jobs RSS feed
2. Parses job entries using feedparser
3. Creates/updates Job records with appropriate categories
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
import feedparser
import httpx
from slugify import slugify
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydotorg.core.database import get_async_session_factory
from pydotorg.domains.jobs.models import Job, JobCategory, JobStatus
from pydotorg.domains.users.models import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

JOBS_RSS_URL = "https://www.python.org/jobs/feed/rss/"


def extract_company_name(title: str) -> str:
    """Extract company name from job title.

    Handles various formats:
    - "Job Title, Company Name"
    - "Job Title at Company Name"
    - "Job Title — Role, Company Name"
    """
    if " at " in title:
        parts = title.rsplit(" at ", 1)
        if len(parts) == 2:  # noqa: PLR2004
            return parts[1].strip()

    if ", " in title:
        parts = title.rsplit(", ", 1)
        if len(parts) == 2 and len(parts[1]) > 2:  # noqa: PLR2004
            return parts[1].strip()

    return "Company"


async def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """Fetch and parse RSS feed."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return feedparser.parse(response.content)


async def get_admin_user(session: AsyncSession) -> User:
    """Get the admin user for creating content."""
    result = await session.execute(select(User).where(User.is_superuser == True).limit(1))  # noqa: E712
    user = result.scalar_one_or_none()

    if not user:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

    if not user:
        msg = "No users found in database. Run 'make db-seed' first."
        raise RuntimeError(msg)

    return user


async def import_jobs(  # noqa: PLR0912, PLR0915
    session: AsyncSession,
    admin_user: User,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict[str, int]:
    """Import job postings from python.org RSS feed."""
    stats = {"created": 0, "updated": 0, "skipped": 0}

    logger.info(f"Fetching jobs from {JOBS_RSS_URL}")

    try:
        parsed = await fetch_feed(JOBS_RSS_URL)
    except Exception:
        logger.exception("Failed to fetch jobs feed")
        return stats

    if not parsed.entries:
        logger.warning("No job entries found in feed")
        return stats

    entries = parsed.entries[:limit] if limit else parsed.entries
    logger.info(f"Found {len(entries)} job entries")

    category_cache: dict[str, JobCategory] = {}

    for entry in entries:
        title = entry.get("title", "").strip()
        if not title:
            stats["skipped"] += 1
            continue

        link = entry.get("link", "")
        description = entry.get("summary", "") or entry.get("description", "")

        slug = slugify(title)[:200]
        if not slug:
            stats["skipped"] += 1
            continue

        result = await session.execute(select(Job).where(Job.slug == slug))
        existing = result.scalar_one_or_none()

        company_name = extract_company_name(title)

        categories = entry.get("tags", [])
        category_name = None
        for tag in categories:
            term = tag.get("term", "").lower()
            if term in ("python", "django", "web", "data", "ml", "ai"):
                category_name = term.title()
                break

        category = None
        if category_name:
            if category_name not in category_cache:
                cat_slug = slugify(category_name)[:50]
                result = await session.execute(select(JobCategory).where(JobCategory.slug == cat_slug))
                category = result.scalar_one_or_none()
                if category is None:
                    category = JobCategory(name=category_name, slug=cat_slug)
                    session.add(category)
                    await session.flush()
                    logger.info(f"Created category: {category_name}")
                category_cache[category_name] = category
            category = category_cache[category_name]

        if existing:
            existing.description = description
            existing.url = link
            stats["updated"] += 1
            logger.debug(f"Updated: {title[:50]}")
        else:
            job = Job(
                slug=slug,
                job_title=title[:200],
                company_name=company_name[:200],
                description=description,
                country="Remote",
                email="jobs@python.org",
                url=link,
                status=JobStatus.APPROVED,
                telecommuting=True,
                creator_id=admin_user.id,
                category_id=category.id if category else None,
            )
            session.add(job)
            stats["created"] += 1
            logger.info(f"Created: {title[:50]}")

    if not dry_run:
        await session.commit()
        logger.info("Changes committed to database")
    else:
        await session.rollback()
        logger.info("Dry run - changes rolled back")

    return stats


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't actually save changes to database",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit number of jobs to import",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(dry_run: bool, limit: int | None, verbose: bool) -> None:  # noqa: FBT001
    """Import job postings from python.org RSS feed."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    async def run() -> None:
        session_factory = get_async_session_factory()

        async with session_factory() as session:
            admin_user = await get_admin_user(session)
            logger.info(f"Using admin user: {admin_user.username}")

            stats = await import_jobs(session, admin_user, dry_run=dry_run, limit=limit)

            logger.info("=" * 50)
            logger.info("Import complete!")
            logger.info(f"  Created: {stats['created']} jobs")
            logger.info(f"  Updated: {stats['updated']} jobs")
            logger.info(f"  Skipped: {stats['skipped']} jobs")
            if dry_run:
                logger.info("  (DRY RUN - no changes saved)")

    asyncio.run(run())


if __name__ == "__main__":
    main()

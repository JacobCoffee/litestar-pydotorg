#!/usr/bin/env python
"""Import success stories from Python.org.

This script scrapes success stories from python.org/success-stories/
and imports them into our database.

Usage:
    uv run python scripts/import_success_stories.py [--dry-run] [--limit N]

The script:
1. Fetches the success stories index page
2. Extracts story URLs and categories
3. Fetches each story page for full content
4. Creates/updates StoryCategory and Story records
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from uuid import UUID

import click
import httpx
from bs4 import BeautifulSoup
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydotorg.core.database import get_async_session_factory
from pydotorg.domains.pages.models import ContentType
from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.users.models import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.python.org"
STORIES_URL = f"{BASE_URL}/success-stories/"


async def fetch_page(url: str) -> str:
    """Fetch a page and return HTML content."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def extract_story_links(html: str) -> list[dict[str, str]]:
    """Extract story links and categories from the index page."""
    soup = BeautifulSoup(html, "lxml")
    stories = []

    sections = soup.find_all("section", class_="success-stories")
    for section in sections:
        category_header = section.find(["h2", "h3"])
        category = category_header.get_text(strip=True) if category_header else "General"

        for link in section.find_all("a", href=True):
            href = link["href"]
            if "/success-stories/" in href and href != "/success-stories/":
                title = link.get_text(strip=True)
                if title and len(title) > 3:
                    full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    stories.append({
                        "title": title,
                        "url": full_url,
                        "category": category,
                    })

    if not stories:
        for li in soup.find_all("li"):
            link = li.find("a", href=True)
            if link and "/success-stories/" in link["href"]:
                href = link["href"]
                if href != "/success-stories/":
                    title = link.get_text(strip=True)
                    if title:
                        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                        stories.append({
                            "title": title,
                            "url": full_url,
                            "category": "General",
                        })

    return stories


def extract_story_content(html: str) -> dict[str, str | None]:
    """Extract content from a story page."""
    soup = BeautifulSoup(html, "lxml")

    title = ""
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    company_name = ""
    company_url = None

    author_section = soup.find(class_="author-info") or soup.find(class_="company-info")
    if author_section:
        company_link = author_section.find("a", href=True)
        if company_link:
            company_name = company_link.get_text(strip=True)
            company_url = company_link["href"]
        else:
            company_text = author_section.get_text(strip=True)
            if company_text:
                company_name = company_text

    if not company_name:
        meta_company = soup.find("meta", property="og:site_name")
        if meta_company:
            company_name = meta_company.get("content", "")

    article = soup.find("article") or soup.find(class_="article-content") or soup.find("main")
    content = ""
    if article:
        for tag in article.find_all(["script", "style", "nav", "footer"]):
            tag.decompose()
        content = article.get_text(separator="\n", strip=True)
    else:
        main_content = soup.find(id="content") or soup.find(class_="content")
        if main_content:
            content = main_content.get_text(separator="\n", strip=True)

    blockquote = soup.find("blockquote")
    pull_quote = ""
    if blockquote:
        pull_quote = blockquote.get_text(strip=True)

    image = None
    og_image = soup.find("meta", property="og:image")
    if og_image:
        image = og_image.get("content")
    else:
        img = soup.find("img", class_="story-image") or soup.find("article img")
        if img:
            image = img.get("src")
            if image and not image.startswith("http"):
                image = f"{BASE_URL}{image}"

    return {
        "title": title,
        "company_name": company_name or "Unknown Company",
        "company_url": company_url,
        "content": content,
        "pull_quote": pull_quote,
        "image": image,
    }


async def get_or_create_category(session: AsyncSession, name: str) -> StoryCategory:
    """Get or create a story category."""
    slug = slugify(name)[:50]
    result = await session.execute(
        select(StoryCategory).where(StoryCategory.slug == slug)
    )
    category = result.scalar_one_or_none()

    if category is None:
        category = StoryCategory(name=name, slug=slug)
        session.add(category)
        await session.flush()
        logger.info(f"Created category: {name}")

    return category


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


async def import_stories(
    session: AsyncSession,
    creator_id: UUID,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict[str, int]:
    """Import success stories from python.org."""
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    logger.info(f"Fetching index page: {STORIES_URL}")
    index_html = await fetch_page(STORIES_URL)

    story_links = extract_story_links(index_html)
    logger.info(f"Found {len(story_links)} story links")

    if limit:
        story_links = story_links[:limit]
        logger.info(f"Limited to {limit} stories")

    category_cache: dict[str, StoryCategory] = {}

    for i, story_info in enumerate(story_links, 1):
        logger.info(f"[{i}/{len(story_links)}] Processing: {story_info['title'][:50]}")

        try:
            story_html = await fetch_page(story_info["url"])
            story_data = extract_story_content(story_html)
        except Exception as e:
            logger.error(f"Failed to fetch {story_info['url']}: {e}")
            stats["errors"] += 1
            continue

        title = story_data["title"] or story_info["title"]
        slug = slugify(title)[:100]

        if not slug:
            logger.warning(f"Could not generate slug for: {title}")
            stats["skipped"] += 1
            continue

        result = await session.execute(select(Story).where(Story.slug == slug))
        existing = result.scalar_one_or_none()

        category_name = story_info["category"]
        if category_name not in category_cache:
            category_cache[category_name] = await get_or_create_category(session, category_name)
        category = category_cache[category_name]

        content = story_data["content"]
        if story_data["pull_quote"]:
            content = f"> {story_data['pull_quote']}\n\n{content}"

        if existing:
            existing.name = title
            existing.company_name = story_data["company_name"]
            existing.company_url = story_data["company_url"]
            existing.category_id = category.id
            existing.content = content
            existing.is_published = True
            if story_data["image"]:
                existing.image = story_data["image"]
            stats["updated"] += 1
            logger.debug(f"Updated: {title[:50]}")
        else:
            story = Story(
                name=title,
                slug=slug,
                company_name=story_data["company_name"],
                company_url=story_data["company_url"],
                category_id=category.id,
                content=content,
                content_type=ContentType.MARKDOWN,
                is_published=True,
                featured=i <= 3,
                image=story_data["image"],
                creator_id=creator_id,
            )
            session.add(story)
            stats["created"] += 1
            logger.info(f"Created: {title[:50]}")

        await asyncio.sleep(0.5)

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
    help="Limit number of stories to import",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(dry_run: bool, limit: int | None, verbose: bool) -> None:  # noqa: FBT001
    """Import success stories from python.org."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    async def run() -> None:
        session_factory = get_async_session_factory()

        async with session_factory() as session:
            admin_user = await get_admin_user(session)
            logger.info(f"Using admin user: {admin_user.username}")

            stats = await import_stories(session, admin_user.id, dry_run, limit)

            logger.info("=" * 50)
            logger.info("Import complete!")
            logger.info(f"  Created: {stats['created']} stories")
            logger.info(f"  Updated: {stats['updated']} stories")
            logger.info(f"  Skipped: {stats['skipped']} stories")
            logger.info(f"  Errors: {stats['errors']} stories")
            if dry_run:
                logger.info("  (DRY RUN - no changes saved)")

    asyncio.run(run())


if __name__ == "__main__":
    main()

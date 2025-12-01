"""Background tasks for syncing external content from Python.org.

This module provides SAQ tasks for periodically importing:
- Events from Python.org's Google Calendar ICS feed
- News/blog entries from official Python.org RSS feeds
- Success stories from python.org/success-stories/

These tasks reuse the logic from the scripts in scripts/ directory
but are designed to run as background workers.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import feedparser
import httpx
from bs4 import BeautifulSoup
from icalendar import Calendar as ICalendar
from saq import CronJob
from slugify import slugify
from sqlalchemy import select

from pydotorg.domains.blogs.models import BlogEntry, Feed
from pydotorg.domains.events.models import (
    Calendar,
    Event,
    EventCategory,
    EventLocation,
    EventOccurrence,
)
from pydotorg.domains.jobs.models import Job, JobCategory, JobStatus
from pydotorg.domains.pages.models import ContentType
from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

PYTHON_EVENTS_CALENDAR_URL = (
    "https://calendar.google.com/calendar/ical/"
    "j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com/public/basic.ics"
)

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
]

BASE_URL = "https://www.python.org"
STORIES_URL = f"{BASE_URL}/success-stories/"
JOBS_RSS_URL = f"{BASE_URL}/jobs/feed/rss/"

CATEGORY_PATTERNS = {
    "conference": [r"pycon", r"europython", r"scipy", r"pydata", r"djangocon", r"pycascades"],
    "meetup": [r"meetup", r"user group", r"usergroup"],
    "sprint": [r"sprint"],
    "workshop": [r"workshop", r"tutorial"],
    "hackathon": [r"hackathon", r"hack day"],
}


def _detect_category(title: str, description: str | None) -> str:
    """Detect event category from title and description."""
    text = f"{title} {description or ''}".lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return category
    return "conference"


def _extract_company_name(title: str) -> str:
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


def _parse_location(location_str: str | None) -> tuple[str, str | None, str | None]:
    """Parse location string into name, address, and URL."""
    if not location_str:
        return "TBD", None, None

    location_str = location_str.strip()

    if location_str.lower() in ("online", "virtual", "remote"):
        return "Online", None, "https://python.org/events"

    url = None
    url_match = re.search(r"https?://\S+", location_str)
    if url_match:
        url = url_match.group()
        location_str = location_str.replace(url, "").strip()

    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    if len(parts) >= 2:  # noqa: PLR2004
        name = parts[-1] if len(parts[-1]) > 3 else ", ".join(parts[-2:])  # noqa: PLR2004
        address = ", ".join(parts)
    else:
        name = location_str[:100] if location_str else "TBD"
        address = location_str if location_str else None

    return name, address, url


def _parse_datetime(dt_value: Any) -> datetime | None:
    """Parse iCalendar datetime to Python datetime."""
    from datetime import date  # noqa: PLC0415

    if dt_value is None:
        return None

    dt = dt_value.dt if hasattr(dt_value, "dt") else dt_value

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    if isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time(), tzinfo=UTC)

    return None


def _is_all_day(dt_value: Any) -> bool:
    """Check if the datetime represents an all-day event."""
    from datetime import date  # noqa: PLC0415

    if dt_value is None:
        return False
    dt = dt_value.dt if hasattr(dt_value, "dt") else dt_value
    return isinstance(dt, date) and not isinstance(dt, datetime)


async def _get_admin_user(session: AsyncSession) -> User:
    """Get the admin user for creating content."""
    result = await session.execute(select(User).where(User.is_superuser == True).limit(1))  # noqa: E712
    user = result.scalar_one_or_none()

    if not user:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

    if not user:
        msg = "No users found in database"
        raise RuntimeError(msg)

    return user


async def sync_events_from_ics(ctx: Mapping[str, Any]) -> dict[str, int]:  # noqa: PLR0912, PLR0915
    """Sync events from Python.org's Google Calendar ICS feed.

    Fetches the iCalendar feed and creates/updates Event records.

    Args:
        ctx: Task context containing dependencies.

    Returns:
        Dict with created/updated/skipped counts.
    """
    session_maker = ctx["session_maker"]
    stats = {"created": 0, "updated": 0, "skipped": 0, "occurrences": 0}

    logger.info(f"Fetching events from {PYTHON_EVENTS_CALENDAR_URL}")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(PYTHON_EVENTS_CALENDAR_URL)
            response.raise_for_status()
            ical_data = response.content
    except Exception:
        logger.exception("Failed to fetch ICS feed")
        return stats

    async with session_maker() as session:
        admin_user = await _get_admin_user(session)

        result = await session.execute(select(Calendar).where(Calendar.slug == "python-events"))
        calendar = result.scalar_one_or_none()

        if calendar is None:
            calendar = Calendar(name="Python Events", slug="python-events", creator_id=admin_user.id)
            session.add(calendar)
            await session.flush()
            logger.info("Created calendar: Python Events")

        ical = ICalendar.from_ical(ical_data)
        category_cache: dict[str, EventCategory] = {}
        location_cache: dict[str, EventLocation] = {}

        for component in ical.walk():
            if component.name != "VEVENT":
                continue

            uid = str(component.get("UID", ""))
            summary = str(component.get("SUMMARY", "Untitled Event"))
            description = str(component.get("DESCRIPTION", "")) or None
            location_str = str(component.get("LOCATION", "")) or None
            dtstart = component.get("DTSTART")
            dtend = component.get("DTEND")

            if not uid:
                stats["skipped"] += 1
                continue

            slug = slugify(summary)[:100]
            if not slug:
                slug = slugify(uid)[:100]

            result = await session.execute(
                select(Event).where(Event.slug == slug, Event.calendar_id == calendar.id)
            )
            existing_event = result.scalar_one_or_none()

            category_name = _detect_category(summary, description)
            if category_name not in category_cache:
                cat_slug = slugify(category_name)
                result = await session.execute(
                    select(EventCategory).where(
                        EventCategory.slug == cat_slug, EventCategory.calendar_id == calendar.id
                    )
                )
                category = result.scalar_one_or_none()
                if category is None:
                    category = EventCategory(name=category_name.title(), slug=cat_slug, calendar_id=calendar.id)
                    session.add(category)
                    await session.flush()
                category_cache[category_name] = category
            category = category_cache[category_name]

            loc_name, loc_address, loc_url = _parse_location(location_str)
            loc_key = slugify(loc_name)[:50]
            if loc_key not in location_cache:
                result = await session.execute(select(EventLocation).where(EventLocation.slug == loc_key))
                location = result.scalar_one_or_none()
                if location is None:
                    location = EventLocation(name=loc_name[:200], slug=loc_key, address=loc_address, url=loc_url)
                    session.add(location)
                    await session.flush()
                location_cache[loc_key] = location
            location = location_cache[loc_key]

            start_dt = _parse_datetime(dtstart)
            end_dt = _parse_datetime(dtend)
            all_day = _is_all_day(dtstart)

            if existing_event:
                existing_event.title = summary
                existing_event.description = description
                existing_event.venue_id = location.id
                stats["updated"] += 1
                event = existing_event
            else:
                event = Event(
                    name=slug,
                    slug=slug,
                    title=summary,
                    description=description,
                    calendar_id=calendar.id,
                    venue_id=location.id,
                    featured=False,
                    creator_id=admin_user.id,
                )
                session.add(event)
                await session.flush()
                stats["created"] += 1

            if start_dt:
                result = await session.execute(
                    select(EventOccurrence).where(
                        EventOccurrence.event_id == event.id,
                        EventOccurrence.dt_start == start_dt,
                    )
                )
                existing_occurrence = result.scalar_one_or_none()

                if not existing_occurrence:
                    occurrence = EventOccurrence(
                        event_id=event.id,
                        dt_start=start_dt,
                        dt_end=end_dt,
                        all_day=all_day,
                    )
                    session.add(occurrence)
                    stats["occurrences"] += 1

        await session.commit()

    logger.info(
        f"Events sync complete: {stats['created']} created, {stats['updated']} updated, "
        f"{stats['occurrences']} occurrences"
    )
    return stats


async def sync_news_from_feeds(ctx: Mapping[str, Any]) -> dict[str, int]:  # noqa: PLR0915
    """Sync news/blog entries from official Python.org RSS feeds.

    Fetches RSS feeds and creates/updates BlogEntry records.

    Args:
        ctx: Task context containing dependencies.

    Returns:
        Dict with created/updated counts.
    """
    session_maker = ctx["session_maker"]
    stats = {"created": 0, "updated": 0}

    async with session_maker() as session:
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

            logger.info(f"Fetching: {feed.name}")

            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(feed.feed_url)
                    response.raise_for_status()
                    parsed = feedparser.parse(response.content)
            except Exception:
                logger.exception(f"Failed to fetch {feed.feed_url}")
                continue

            if not parsed.entries:
                continue

            for entry in parsed.entries:
                title = entry.get("title", "Untitled")
                link = entry.get("link", "")
                guid = entry.get("id") or entry.get("link") or f"{feed.feed_url}#{title}"
                summary = entry.get("summary", "")

                content = None
                if entry.get("content"):
                    content = entry["content"][0].get("value", "")
                elif "summary" in entry:
                    content = entry["summary"]

                pub_date = datetime.now(UTC)
                if entry.get("published_parsed"):
                    pub_date = datetime(*entry["published_parsed"][:6], tzinfo=UTC)
                elif entry.get("updated_parsed"):
                    pub_date = datetime(*entry["updated_parsed"][:6], tzinfo=UTC)

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

            feed.last_fetched = datetime.now(UTC)

        await session.commit()

    logger.info(f"News sync complete: {stats['created']} created, {stats['updated']} updated")
    return stats


async def sync_success_stories(ctx: Mapping[str, Any]) -> dict[str, int]:  # noqa: PLR0912, PLR0915
    """Sync success stories from python.org/success-stories/.

    Scrapes the stories index and individual pages.

    Args:
        ctx: Task context containing dependencies.

    Returns:
        Dict with created/updated/error counts.
    """
    session_maker = ctx["session_maker"]
    stats = {"created": 0, "updated": 0, "errors": 0}

    logger.info(f"Fetching success stories index: {STORIES_URL}")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(STORIES_URL)
            response.raise_for_status()
            index_html = response.text
    except Exception:
        logger.exception("Failed to fetch stories index")
        return stats

    soup = BeautifulSoup(index_html, "lxml")
    stories = []

    sections = soup.find_all("section", class_="success-stories")
    for section in sections:
        category_header = section.find(["h2", "h3"])
        category = category_header.get_text(strip=True) if category_header else "General"

        for link in section.find_all("a", href=True):
            href = link["href"]
            if "/success-stories/" in href and href != "/success-stories/":
                title = link.get_text(strip=True)
                if title and len(title) > 3:  # noqa: PLR2004
                    full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    stories.append({"title": title, "url": full_url, "category": category})

    if not stories:
        for li in soup.find_all("li"):
            link = li.find("a", href=True)
            if link and "/success-stories/" in link["href"]:
                href = link["href"]
                if href != "/success-stories/":
                    title = link.get_text(strip=True)
                    if title:
                        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                        stories.append({"title": title, "url": full_url, "category": "General"})

    logger.info(f"Found {len(stories)} story links")

    async with session_maker() as session:
        admin_user = await _get_admin_user(session)
        category_cache: dict[str, StoryCategory] = {}

        for story_info in stories[:50]:
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(story_info["url"])
                    response.raise_for_status()
                    story_html = response.text
            except Exception:  # noqa: BLE001
                logger.warning(f"Failed to fetch {story_info['url']}")
                stats["errors"] += 1
                continue

            story_soup = BeautifulSoup(story_html, "lxml")

            title_tag = story_soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else story_info["title"]

            company_name = "Unknown Company"
            company_url = None
            author_section = story_soup.find(class_="author-info") or story_soup.find(class_="company-info")
            if author_section:
                company_link = author_section.find("a", href=True)
                if company_link:
                    company_name = company_link.get_text(strip=True)
                    company_url = company_link["href"]
                else:
                    company_text = author_section.get_text(strip=True)
                    if company_text:
                        company_name = company_text

            article = story_soup.find("article") or story_soup.find(class_="article-content") or story_soup.find("main")
            content = ""
            if article:
                for tag in article.find_all(["script", "style", "nav", "footer"]):
                    tag.decompose()
                content = article.get_text(separator="\n", strip=True)

            blockquote = story_soup.find("blockquote")
            if blockquote:
                pull_quote = blockquote.get_text(strip=True)
                content = f"> {pull_quote}\n\n{content}"

            image = None
            og_image = story_soup.find("meta", property="og:image")
            if og_image:
                image = og_image.get("content")

            slug = slugify(title)[:100]
            if not slug:
                continue

            result = await session.execute(select(Story).where(Story.slug == slug))
            existing = result.scalar_one_or_none()

            category_name = story_info["category"]
            if category_name not in category_cache:
                cat_slug = slugify(category_name)[:50]
                result = await session.execute(select(StoryCategory).where(StoryCategory.slug == cat_slug))
                category = result.scalar_one_or_none()
                if category is None:
                    category = StoryCategory(name=category_name, slug=cat_slug)
                    session.add(category)
                    await session.flush()
                category_cache[category_name] = category
            category = category_cache[category_name]

            if existing:
                existing.name = title
                existing.company_name = company_name
                existing.company_url = company_url
                existing.category_id = category.id
                existing.content = content
                existing.is_published = True
                if image:
                    existing.image = image
                stats["updated"] += 1
            else:
                story = Story(
                    name=title,
                    slug=slug,
                    company_name=company_name,
                    company_url=company_url,
                    category_id=category.id,
                    content=content,
                    content_type=ContentType.MARKDOWN,
                    is_published=True,
                    featured=False,
                    image=image,
                    creator_id=admin_user.id,
                )
                session.add(story)
                stats["created"] += 1

        await session.commit()

    logger.info(f"Stories sync complete: {stats['created']} created, {stats['updated']} updated")
    return stats


async def sync_jobs_from_rss(ctx: Mapping[str, Any]) -> dict[str, int]:  # noqa: PLR0912, PLR0915
    """Sync job postings from python.org/jobs/feed/rss/.

    Fetches job listings from the RSS feed and creates/updates Job records.

    Args:
        ctx: Task context containing dependencies.

    Returns:
        Dict with created/updated/skipped counts.
    """
    session_maker = ctx["session_maker"]
    stats = {"created": 0, "updated": 0, "skipped": 0}

    logger.info(f"Fetching jobs from {JOBS_RSS_URL}")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(JOBS_RSS_URL)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
    except Exception:
        logger.exception("Failed to fetch jobs RSS feed")
        return stats

    if not parsed.entries:
        logger.warning("No job entries found in feed")
        return stats

    logger.info(f"Found {len(parsed.entries)} job entries")

    async with session_maker() as session:
        admin_user = await _get_admin_user(session)
        category_cache: dict[str, JobCategory] = {}

        for entry in parsed.entries:
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

            company_name = _extract_company_name(title)
            location_parts = {"city": None, "region": None, "country": "Remote"}

            categories = entry.get("tags", [])
            category_name = None
            for tag in categories:
                term = tag.get("term", "").lower()
                if term in ("python", "django", "web", "data", "ml", "ai"):
                    category_name = term.title()
                    break

            if category_name:
                if category_name not in category_cache:
                    cat_slug = slugify(category_name)[:50]
                    result = await session.execute(select(JobCategory).where(JobCategory.slug == cat_slug))
                    category = result.scalar_one_or_none()
                    if category is None:
                        category = JobCategory(name=category_name, slug=cat_slug)
                        session.add(category)
                        await session.flush()
                    category_cache[category_name] = category
                category = category_cache[category_name]
            else:
                category = None

            if existing:
                existing.description = description
                existing.url = link
                stats["updated"] += 1
            else:
                job = Job(
                    slug=slug,
                    job_title=title[:200],
                    company_name=company_name[:200],
                    description=description,
                    city=location_parts["city"],
                    region=location_parts["region"],
                    country=location_parts["country"],
                    email="jobs@python.org",
                    url=link,
                    status=JobStatus.APPROVED,
                    telecommuting=True,
                    creator_id=admin_user.id,
                    category_id=category.id if category else None,
                )
                session.add(job)
                stats["created"] += 1

        await session.commit()

    logger.info(f"Jobs sync complete: {stats['created']} created, {stats['updated']} updated")
    return stats


async def sync_all_external_content(ctx: Mapping[str, Any]) -> dict[str, Any]:
    """Sync all external content (events, news, stories, jobs).

    This is a convenience task that runs all sync tasks.

    Args:
        ctx: Task context containing dependencies.

    Returns:
        Dict with results from all sync tasks.
    """
    logger.info("Starting full external content sync")

    events_stats = await sync_events_from_ics(ctx)
    news_stats = await sync_news_from_feeds(ctx)
    stories_stats = await sync_success_stories(ctx)
    jobs_stats = await sync_jobs_from_rss(ctx)

    logger.info("Full external content sync complete")

    return {
        "events": events_stats,
        "news": news_stats,
        "stories": stories_stats,
        "jobs": jobs_stats,
    }


cron_sync_events = CronJob(
    function=sync_events_from_ics,
    cron="0 */6 * * *",
    timeout=600,
)

cron_sync_news = CronJob(
    function=sync_news_from_feeds,
    cron="0 */2 * * *",
    timeout=300,
)

cron_sync_stories = CronJob(
    function=sync_success_stories,
    cron="0 0 * * 0",
    timeout=1800,
)

cron_sync_jobs = CronJob(
    function=sync_jobs_from_rss,
    cron="0 */4 * * *",
    timeout=300,
)

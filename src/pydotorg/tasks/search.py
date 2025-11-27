"""Search indexing tasks for Meilisearch."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from saq import CronJob
from sqlalchemy import select

from pydotorg.config import settings
from pydotorg.core.search.schemas import BlogDocument, EventDocument, JobDocument, PageDocument
from pydotorg.core.search.service import SearchService
from pydotorg.domains.blogs.models import BlogEntry
from pydotorg.domains.events.models import Event
from pydotorg.domains.jobs.models import Job, JobStatus
from pydotorg.domains.pages.models import Page

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _get_search_service() -> SearchService:
    """Get configured SearchService instance."""
    return SearchService(
        url=settings.meilisearch_url,
        api_key=settings.meilisearch_api_key,
        index_prefix=settings.meilisearch_index_prefix,
    )


async def index_all_jobs(ctx: dict[str, Any]) -> dict[str, Any]:
    """Full reindex of all approved jobs.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with indexing statistics.
    """
    start_time = time.time()
    logger.info("Starting full job reindexing")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(Job).where(Job.status == JobStatus.APPROVED).order_by(Job.created_at.desc())
            result = await session.execute(stmt)
            jobs = result.scalars().all()

            if not jobs:
                logger.info("No approved jobs found to index")
                return {"indexed": 0, "duration_seconds": time.time() - start_time}

            documents = []
            for job in jobs:
                doc = JobDocument(
                    id=str(job.id),
                    title=job.job_title,
                    description=job.description,
                    content=f"{job.description} {job.requirements or ''}".strip(),
                    url=f"/jobs/{job.slug}/",
                    content_type="job",
                    created=job.created_at,
                    modified=job.updated_at,
                    status=job.status.value,
                    tags=[],
                    searchable_text=f"{job.job_title} {job.company_name} {job.description} {job.requirements or ''}",
                    company_name=job.company_name,
                    location=f"{job.city}, {job.region}, {job.country}" if job.city else job.country,
                    remote=job.telecommuting,
                    job_types=[jt.name for jt in job.job_types] if job.job_types else [],
                )
                documents.append(doc)

            await search_service.clear_index("jobs")
            task_info = await search_service.index_documents("jobs", documents, primary_key="id")

            duration = time.time() - start_time
            logger.info(f"Indexed {len(documents)} jobs in {duration:.2f}s. Task: {task_info.task_uid}")

            return {
                "indexed": len(documents),
                "duration_seconds": duration,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception("Failed to index all jobs")
        raise
    finally:
        await search_service.close()


async def index_job(ctx: dict[str, Any], *, job_id: str) -> dict[str, Any]:
    """Index or update a single job in the search index.

    Args:
        ctx: SAQ worker context with database session maker.
        job_id: UUID of the job to index.

    Returns:
        Dictionary with indexing result.
    """
    logger.info(f"Indexing job: {job_id}")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(Job).where(Job.id == UUID(job_id))
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()

            if not job:
                logger.debug(f"Job {job_id} not found, removing from index if exists")
                await search_service.delete_documents("jobs", [job_id])
                return {"indexed": 0, "reason": "not_found", "action": "removed"}

            if job.status != JobStatus.APPROVED:
                logger.info(f"Job {job_id} is not approved (status: {job.status}), removing from index if exists")
                await search_service.delete_documents("jobs", [job_id])
                return {"indexed": 0, "reason": "not_approved", "action": "removed"}

            doc = JobDocument(
                id=str(job.id),
                title=job.job_title,
                description=job.description,
                content=f"{job.description} {job.requirements or ''}".strip(),
                url=f"/jobs/{job.slug}/",
                content_type="job",
                created=job.created_at,
                modified=job.updated_at,
                status=job.status.value,
                tags=[],
                searchable_text=f"{job.job_title} {job.company_name} {job.description} {job.requirements or ''}",
                company_name=job.company_name,
                location=f"{job.city}, {job.region}, {job.country}" if job.city else job.country,
                remote=job.telecommuting,
                job_types=[jt.name for jt in job.job_types] if job.job_types else [],
            )

            task_info = await search_service.update_documents("jobs", [doc], primary_key="id")

            logger.info(f"Indexed job {job_id}. Task: {task_info.task_uid}")

            return {
                "indexed": 1,
                "job_id": job_id,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception(f"Failed to index job {job_id}")
        raise
    finally:
        await search_service.close()


async def remove_job_from_index(ctx: dict[str, Any], *, job_id: str) -> dict[str, Any]:
    """Remove a job from the search index.

    Args:
        ctx: SAQ worker context with database session maker.
        job_id: UUID of the job to remove.

    Returns:
        Dictionary with removal result.
    """
    logger.info(f"Removing job from index: {job_id}")

    search_service = _get_search_service()

    try:
        task_info = await search_service.delete_documents("jobs", [job_id])

        logger.info(f"Removed job {job_id} from index. Task: {task_info.task_uid}")

        return {
            "removed": 1,
            "job_id": job_id,
            "task_uid": task_info.task_uid,
        }

    except Exception:
        logger.exception(f"Failed to remove job {job_id} from index")
        raise
    finally:
        await search_service.close()


async def index_all_events(ctx: dict[str, Any]) -> dict[str, Any]:
    """Full reindex of all published events.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with indexing statistics.
    """
    start_time = time.time()
    logger.info("Starting full event reindexing")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(Event).order_by(Event.created_at.desc())
            result = await session.execute(stmt)
            events = result.scalars().all()

            if not events:
                logger.info("No published events found to index")
                return {"indexed": 0, "duration_seconds": time.time() - start_time}

            documents = []
            for event in events:
                next_occurrence = event.occurrences[0] if event.occurrences else None
                venue_obj = event.venue

                doc = EventDocument(
                    id=str(event.id),
                    title=event.title,
                    description=event.description,
                    content=event.description,
                    url=f"/events/{event.slug}/",
                    content_type="event",
                    created=event.created_at,
                    modified=event.updated_at,
                    status="published",
                    tags=[cat.name for cat in event.categories] if event.categories else [],
                    searchable_text=f"{event.title} {event.description or ''}",
                    venue=venue_obj.name if venue_obj else None,
                    location=f"{venue_obj.address or ''} {venue_obj.city or ''} {venue_obj.state or ''}".strip()
                    if venue_obj
                    else None,
                    start_date=next_occurrence.dt_start if next_occurrence else None,
                    end_date=next_occurrence.dt_end if next_occurrence else None,
                )
                documents.append(doc)

            await search_service.clear_index("events")
            task_info = await search_service.index_documents("events", documents, primary_key="id")

            duration = time.time() - start_time
            logger.info(f"Indexed {len(documents)} events in {duration:.2f}s. Task: {task_info.task_uid}")

            return {
                "indexed": len(documents),
                "duration_seconds": duration,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception("Failed to index all events")
        raise
    finally:
        await search_service.close()


async def index_event(ctx: dict[str, Any], *, event_id: str) -> dict[str, Any]:
    """Index or update a single event in the search index.

    Args:
        ctx: SAQ worker context with database session maker.
        event_id: UUID of the event to index.

    Returns:
        Dictionary with indexing result.
    """
    logger.info(f"Indexing event: {event_id}")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(Event).where(Event.id == UUID(event_id))
            result = await session.execute(stmt)
            event = result.scalar_one_or_none()

            if not event:
                logger.debug(f"Event {event_id} not found, removing from index if exists")
                await search_service.delete_documents("events", [event_id])
                return {"indexed": 0, "reason": "not_found", "action": "removed"}

            next_occurrence = event.occurrences[0] if event.occurrences else None
            venue_obj = event.venue

            doc = EventDocument(
                id=str(event.id),
                title=event.title,
                description=event.description,
                content=event.description,
                url=f"/events/{event.slug}/",
                content_type="event",
                created=event.created_at,
                modified=event.updated_at,
                status="published",
                tags=[cat.name for cat in event.categories] if event.categories else [],
                searchable_text=f"{event.title} {event.description or ''}",
                venue=venue_obj.name if venue_obj else None,
                location=f"{venue_obj.address or ''} {venue_obj.city or ''} {venue_obj.state or ''}".strip()
                if venue_obj
                else None,
                start_date=next_occurrence.dt_start if next_occurrence else None,
                end_date=next_occurrence.dt_end if next_occurrence else None,
            )

            task_info = await search_service.update_documents("events", [doc], primary_key="id")

            logger.info(f"Indexed event {event_id}. Task: {task_info.task_uid}")

            return {
                "indexed": 1,
                "event_id": event_id,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception(f"Failed to index event {event_id}")
        raise
    finally:
        await search_service.close()


async def index_all_pages(ctx: dict[str, Any]) -> dict[str, Any]:
    """Full reindex of all published CMS pages.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with indexing statistics.
    """
    start_time = time.time()
    logger.info("Starting full page reindexing")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(Page).where(Page.is_published.is_(True)).order_by(Page.created_at.desc())
            result = await session.execute(stmt)
            pages = result.scalars().all()

            if not pages:
                logger.info("No published pages found to index")
                return {"indexed": 0, "duration_seconds": time.time() - start_time}

            documents = []
            for page in pages:
                doc = PageDocument(
                    id=str(page.id),
                    title=page.title,
                    description=page.description,
                    content=page.content,
                    url=page.path,
                    content_type="page",
                    created=page.created_at,
                    modified=page.updated_at,
                    status="published" if page.is_published else "draft",
                    tags=page.keywords.split(",") if page.keywords else [],
                    searchable_text=f"{page.title} {page.description or ''} {page.content or ''}",
                    path=page.path,
                )
                documents.append(doc)

            await search_service.clear_index("pages")
            task_info = await search_service.index_documents("pages", documents, primary_key="id")

            duration = time.time() - start_time
            logger.info(f"Indexed {len(documents)} pages in {duration:.2f}s. Task: {task_info.task_uid}")

            return {
                "indexed": len(documents),
                "duration_seconds": duration,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception("Failed to index all pages")
        raise
    finally:
        await search_service.close()


async def index_page(ctx: dict[str, Any], *, page_id: str) -> dict[str, Any]:
    """Index or update a single page in the search index.

    Args:
        ctx: SAQ worker context with database session maker.
        page_id: UUID of the page to index.

    Returns:
        Dictionary with indexing result.
    """
    logger.info(f"Indexing page: {page_id}")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(Page).where(Page.id == UUID(page_id))
            result = await session.execute(stmt)
            page = result.scalar_one_or_none()

            if not page:
                logger.debug(f"Page {page_id} not found, removing from index if exists")
                await search_service.delete_documents("pages", [page_id])
                return {"indexed": 0, "reason": "not_found", "action": "removed"}

            if not page.is_published:
                logger.info(f"Page {page_id} is not published, removing from index if exists")
                await search_service.delete_documents("pages", [page_id])
                return {"indexed": 0, "reason": "not_published", "action": "removed"}

            doc = PageDocument(
                id=str(page.id),
                title=page.title,
                description=page.description,
                content=page.content,
                url=page.path,
                content_type="page",
                created=page.created_at,
                modified=page.updated_at,
                status="published" if page.is_published else "draft",
                tags=page.keywords.split(",") if page.keywords else [],
                searchable_text=f"{page.title} {page.description or ''} {page.content or ''}",
                path=page.path,
            )

            task_info = await search_service.update_documents("pages", [doc], primary_key="id")

            logger.info(f"Indexed page {page_id}. Task: {task_info.task_uid}")

            return {
                "indexed": 1,
                "page_id": page_id,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception(f"Failed to index page {page_id}")
        raise
    finally:
        await search_service.close()


async def index_all_blogs(ctx: dict[str, Any]) -> dict[str, Any]:
    """Full reindex of all blog entries.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with indexing statistics.
    """
    start_time = time.time()
    logger.info("Starting full blog entry reindexing")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(BlogEntry).order_by(BlogEntry.pub_date.desc())
            result = await session.execute(stmt)
            entries = result.scalars().all()

            if not entries:
                logger.info("No blog entries found to index")
                return {"indexed": 0, "duration_seconds": time.time() - start_time}

            documents = []
            for entry in entries:
                doc = BlogDocument(
                    id=str(entry.id),
                    title=entry.title,
                    description=entry.summary,
                    content=entry.content or entry.summary,
                    url=entry.url,
                    content_type="blog",
                    created=entry.created_at,
                    modified=entry.updated_at,
                    status="published",
                    tags=[],
                    searchable_text=f"{entry.title} {entry.summary or ''} {entry.content or ''}",
                    author=None,
                    published=entry.pub_date,
                )
                documents.append(doc)

            await search_service.clear_index("blogs")
            task_info = await search_service.index_documents("blogs", documents, primary_key="id")

            duration = time.time() - start_time
            logger.info(f"Indexed {len(documents)} blog entries in {duration:.2f}s. Task: {task_info.task_uid}")

            return {
                "indexed": len(documents),
                "duration_seconds": duration,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception("Failed to index all blog entries")
        raise
    finally:
        await search_service.close()


async def index_blog_entry(ctx: dict[str, Any], *, entry_id: str) -> dict[str, Any]:
    """Index or update a single blog entry in the search index.

    Args:
        ctx: SAQ worker context with database session maker.
        entry_id: UUID of the blog entry to index.

    Returns:
        Dictionary with indexing result.
    """
    logger.info(f"Indexing blog entry: {entry_id}")

    search_service = _get_search_service()
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            stmt = select(BlogEntry).where(BlogEntry.id == UUID(entry_id))
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()

            if not entry:
                logger.debug(f"Blog entry {entry_id} not found, removing from index if exists")
                await search_service.delete_documents("blogs", [entry_id])
                return {"indexed": 0, "reason": "not_found", "action": "removed"}

            doc = BlogDocument(
                id=str(entry.id),
                title=entry.title,
                description=entry.summary,
                content=entry.content or entry.summary,
                url=entry.url,
                content_type="blog",
                created=entry.created_at,
                modified=entry.updated_at,
                status="published",
                tags=[],
                searchable_text=f"{entry.title} {entry.summary or ''} {entry.content or ''}",
                author=None,
                published=entry.pub_date,
            )

            task_info = await search_service.update_documents("blogs", [doc], primary_key="id")

            logger.info(f"Indexed blog entry {entry_id}. Task: {task_info.task_uid}")

            return {
                "indexed": 1,
                "entry_id": entry_id,
                "task_uid": task_info.task_uid,
            }

    except Exception:
        logger.exception(f"Failed to index blog entry {entry_id}")
        raise
    finally:
        await search_service.close()


async def rebuild_search_index(ctx: dict[str, Any]) -> dict[str, Any]:
    """Rebuild all search indexes from scratch.

    Creates indexes if they don't exist, configures index settings,
    and reindexes all content. This is a heavy operation and should
    be run during off-peak hours.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with rebuild statistics.
    """
    start_time = time.time()
    logger.info("Starting full search index rebuild")

    search_service = _get_search_service()

    try:
        indexes_config = {
            "jobs": {
                "searchable": ["title", "description", "company_name", "searchable_text"],
                "filterable": ["content_type", "status", "remote", "job_types", "created", "modified"],
                "sortable": ["created", "modified", "title"],
            },
            "events": {
                "searchable": ["title", "description", "venue", "searchable_text"],
                "filterable": ["content_type", "status", "tags", "start_date", "end_date", "created", "modified"],
                "sortable": ["created", "modified", "start_date", "title"],
            },
            "pages": {
                "searchable": ["title", "description", "content", "searchable_text"],
                "filterable": ["content_type", "status", "tags", "created", "modified"],
                "sortable": ["created", "modified", "title"],
            },
            "blogs": {
                "searchable": ["title", "description", "content", "searchable_text"],
                "filterable": ["content_type", "author", "published", "created", "modified"],
                "sortable": ["created", "modified", "published", "title"],
            },
        }

        for index_name, config in indexes_config.items():
            logger.info(f"Creating/configuring index: {index_name}")
            try:
                await search_service.create_index(index_name, primary_key="id")
            except Exception:  # noqa: BLE001
                logger.info(f"Index {index_name} may already exist, skipping creation")

            await search_service.configure_index(
                index=index_name,
                searchable_attributes=config["searchable"],
                filterable_attributes=config["filterable"],
                sortable_attributes=config["sortable"],
            )

        results = {}
        results["jobs"] = await index_all_jobs(ctx)
        results["events"] = await index_all_events(ctx)
        results["pages"] = await index_all_pages(ctx)
        results["blogs"] = await index_all_blogs(ctx)

        duration = time.time() - start_time
        total_indexed = sum(r.get("indexed", 0) for r in results.values())

        logger.info(
            "Search index rebuild complete",
            extra={
                "documents_indexed": total_indexed,
                "duration_seconds": duration,
            },
        )

        return {
            "total_indexed": total_indexed,
            "duration_seconds": duration,
            "results": results,
        }

    except Exception:
        logger.exception("Failed to rebuild all indexes")
        raise
    finally:
        await search_service.close()


async def index_content(ctx: dict[str, Any], content_type: str, content_id: str) -> dict[str, bool]:
    """Index a single piece of content.

    Args:
        ctx: SAQ worker context with database session maker.
        content_type: Type of content (page, blog, job, event).
        content_id: ID of the content to index.

    Returns:
        Dictionary with success status.
    """
    try:
        if content_type == "job":
            result = await index_job(ctx, job_id=content_id)
        elif content_type == "event":
            result = await index_event(ctx, event_id=content_id)
        elif content_type == "page":
            result = await index_page(ctx, page_id=content_id)
        elif content_type == "blog":
            result = await index_blog_entry(ctx, entry_id=content_id)
        else:
            logger.error(f"Unknown content type: {content_type}")
            return {"success": False, "error": f"Unknown content type: {content_type}"}

        logger.info(
            "Content indexed",
            extra={
                "content_type": content_type,
                "content_id": content_id,
                "result": result,
            },
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.exception(
            "Content indexing failed",
            extra={
                "content_type": content_type,
                "content_id": content_id,
            },
        )
        return {"success": False, "error": str(e)}


cron_rebuild_indexes = CronJob(
    function=rebuild_search_index,
    cron="0 3 * * 0",
    timeout=1800,
)

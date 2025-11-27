"""Background tasks for event management."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from saq import CronJob
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from pydotorg.config import settings
from pydotorg.domains.events.models import Event, EventOccurrence
from pydotorg.lib.tasks import enqueue_task

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_event_reminders(ctx: dict[str, Any]) -> dict[str, Any]:
    """Check for upcoming events and send reminder emails.

    Finds events occurring in the next 24 hours and sends reminder
    emails to registered attendees (if attendance tracking exists)
    or to the event creator.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with reminder statistics.
    """
    logger.info("Checking for upcoming events to send reminders")
    session_maker = ctx["session_maker"]

    reminders_sent = 0
    events_checked = 0

    try:
        async with session_maker() as session:
            session: AsyncSession

            now = datetime.now(UTC)
            reminder_window_start = now + timedelta(hours=23)
            reminder_window_end = now + timedelta(hours=25)

            stmt = (
                select(EventOccurrence)
                .where(
                    EventOccurrence.dt_start >= reminder_window_start,
                    EventOccurrence.dt_start <= reminder_window_end,
                )
                .options(selectinload(EventOccurrence.event).selectinload(Event.venue))
            )
            result = await session.execute(stmt)
            occurrences = result.scalars().all()

            events_checked = len(occurrences)
            logger.info(f"Found {events_checked} events occurring in ~24 hours")

            for occurrence in occurrences:
                event = occurrence.event
                if not event:
                    continue

                event_date = occurrence.dt_start.strftime("%B %d, %Y at %I:%M %p %Z")
                event_url = f"{settings.oauth_redirect_base_url}/events/{event.slug}/"

                job_key = await enqueue_task(
                    "send_event_reminder_email",
                    to_email=settings.smtp_from_email,
                    event_title=event.title,
                    event_date=event_date,
                    event_url=event_url,
                )

                if job_key:
                    reminders_sent += 1
                    logger.info(
                        f"Enqueued reminder for event: {event.title}",
                        extra={"event_id": str(event.id), "job_key": job_key},
                    )

        logger.info(
            "Event reminder check complete",
            extra={"events_checked": events_checked, "reminders_sent": reminders_sent},
        )

        return {
            "events_checked": events_checked,
            "reminders_sent": reminders_sent,
        }

    except Exception:
        logger.exception("Failed to check event reminders")
        raise


async def cleanup_past_occurrences(ctx: dict[str, Any]) -> dict[str, Any]:
    """Clean up event occurrences that are more than 90 days in the past.

    This helps keep the database clean by removing old occurrence records
    while preserving the event itself.

    Args:
        ctx: SAQ worker context with database session maker.

    Returns:
        Dictionary with cleanup statistics.
    """
    logger.info("Cleaning up past event occurrences")
    session_maker = ctx["session_maker"]

    try:
        async with session_maker() as session:
            session: AsyncSession

            cutoff_date = datetime.now(UTC) - timedelta(days=90)

            stmt = select(EventOccurrence).where(EventOccurrence.dt_end < cutoff_date)
            result = await session.execute(stmt)
            old_occurrences = result.scalars().all()

            deleted_count = len(old_occurrences)

            for occurrence in old_occurrences:
                await session.delete(occurrence)

            await session.commit()

            logger.info(
                "Past occurrences cleanup complete",
                extra={"deleted_count": deleted_count, "cutoff_date": cutoff_date.isoformat()},
            )

            return {
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

    except Exception:
        logger.exception("Failed to cleanup past occurrences")
        raise


cron_event_reminders = CronJob(
    function=check_event_reminders,
    cron="0 8 * * *",
    timeout=600,
)

cron_cleanup_past_occurrences = CronJob(
    function=cleanup_past_occurrences,
    cron="0 3 1 * *",
    timeout=1800,
)

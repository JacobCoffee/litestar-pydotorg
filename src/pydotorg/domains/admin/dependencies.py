"""Admin domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.admin.services import (
    BlogAdminService,
    CronJobService,
    DashboardService,
    EmailAdminService,
    EventAdminService,
    JobAdminService,
    PageAdminService,
    SponsorAdminService,
    TaskAdminService,
    UserAdminService,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_dashboard_service(db_session: AsyncSession) -> DashboardService:
    """Provide a DashboardService instance.

    Args:
        db_session: Database session

    Returns:
        DashboardService instance
    """
    return DashboardService(session=db_session)


async def provide_user_admin_service(db_session: AsyncSession) -> UserAdminService:
    """Provide a UserAdminService instance.

    Args:
        db_session: Database session

    Returns:
        UserAdminService instance
    """
    return UserAdminService(session=db_session)


async def provide_job_admin_service(db_session: AsyncSession) -> JobAdminService:
    """Provide a JobAdminService instance.

    Args:
        db_session: Database session

    Returns:
        JobAdminService instance
    """
    return JobAdminService(session=db_session)


async def provide_sponsor_admin_service(db_session: AsyncSession) -> SponsorAdminService:
    """Provide a SponsorAdminService instance.

    Args:
        db_session: Database session

    Returns:
        SponsorAdminService instance
    """
    return SponsorAdminService(session=db_session)


async def provide_event_admin_service(db_session: AsyncSession) -> EventAdminService:
    """Provide an EventAdminService instance.

    Args:
        db_session: Database session

    Returns:
        EventAdminService instance
    """
    return EventAdminService(session=db_session)


async def provide_page_admin_service(db_session: AsyncSession) -> PageAdminService:
    """Provide a PageAdminService instance.

    Args:
        db_session: Database session

    Returns:
        PageAdminService instance
    """
    return PageAdminService(session=db_session)


async def provide_blog_admin_service(db_session: AsyncSession) -> BlogAdminService:
    """Provide a BlogAdminService instance.

    Args:
        db_session: Database session

    Returns:
        BlogAdminService instance
    """
    return BlogAdminService(session=db_session)


async def provide_task_admin_service() -> TaskAdminService:
    """Provide a TaskAdminService instance.

    Returns:
        TaskAdminService instance
    """
    return TaskAdminService()


async def provide_email_admin_service(db_session: AsyncSession) -> EmailAdminService:
    """Provide an EmailAdminService instance.

    Args:
        db_session: Database session

    Returns:
        EmailAdminService instance
    """
    return EmailAdminService(session=db_session)


async def provide_cron_job_service() -> CronJobService:
    """Provide a CronJobService instance with Redis connection.

    Returns:
        CronJobService instance
    """
    from redis.asyncio import Redis  # noqa: PLC0415

    from pydotorg.config import settings  # noqa: PLC0415

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return CronJobService(redis=redis)


def get_admin_dependencies() -> dict:
    """Get all admin domain dependency providers.

    Returns:
        Dictionary mapping dependency names to provider functions
    """
    return {
        "dashboard_service": provide_dashboard_service,
        "user_admin_service": provide_user_admin_service,
        "job_admin_service": provide_job_admin_service,
        "sponsor_admin_service": provide_sponsor_admin_service,
        "event_admin_service": provide_event_admin_service,
        "page_admin_service": provide_page_admin_service,
        "blog_admin_service": provide_blog_admin_service,
        "task_admin_service": provide_task_admin_service,
        "email_admin_service": provide_email_admin_service,
        "cron_job_service": provide_cron_job_service,
    }

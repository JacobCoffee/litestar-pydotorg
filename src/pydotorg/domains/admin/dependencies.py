"""Admin domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.admin.services import (
    DashboardService,
    JobAdminService,
    SponsorAdminService,
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
    }

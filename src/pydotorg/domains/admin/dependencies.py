"""Admin domain dependency injection providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydotorg.domains.admin.services import DashboardService

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


def get_admin_dependencies() -> dict:
    """Get all admin domain dependency providers.

    Returns:
        Dictionary mapping dependency names to provider functions
    """
    return {
        "dashboard_service": provide_dashboard_service,
    }

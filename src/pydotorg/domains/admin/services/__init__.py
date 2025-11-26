"""Admin domain services."""

from pydotorg.domains.admin.services.dashboard import DashboardService
from pydotorg.domains.admin.services.jobs import JobAdminService
from pydotorg.domains.admin.services.sponsors import SponsorAdminService
from pydotorg.domains.admin.services.users import UserAdminService

__all__ = [
    "DashboardService",
    "JobAdminService",
    "SponsorAdminService",
    "UserAdminService",
]

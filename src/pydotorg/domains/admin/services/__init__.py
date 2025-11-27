"""Admin domain services."""

from pydotorg.domains.admin.services.blogs import BlogAdminService
from pydotorg.domains.admin.services.dashboard import DashboardService
from pydotorg.domains.admin.services.events import EventAdminService
from pydotorg.domains.admin.services.jobs import JobAdminService
from pydotorg.domains.admin.services.pages import PageAdminService
from pydotorg.domains.admin.services.sponsors import SponsorAdminService
from pydotorg.domains.admin.services.users import UserAdminService

__all__ = [
    "BlogAdminService",
    "DashboardService",
    "EventAdminService",
    "JobAdminService",
    "PageAdminService",
    "SponsorAdminService",
    "UserAdminService",
]

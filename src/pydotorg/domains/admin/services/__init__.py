"""Admin domain services."""

from pydotorg.domains.admin.services.blogs import BlogAdminService
from pydotorg.domains.admin.services.dashboard import DashboardService
from pydotorg.domains.admin.services.email import EmailAdminService
from pydotorg.domains.admin.services.events import EventAdminService
from pydotorg.domains.admin.services.jobs import JobAdminService
from pydotorg.domains.admin.services.pages import PageAdminService
from pydotorg.domains.admin.services.sponsors import SponsorAdminService
from pydotorg.domains.admin.services.tasks import TaskAdminService
from pydotorg.domains.admin.services.users import UserAdminService

__all__ = [
    "BlogAdminService",
    "DashboardService",
    "EmailAdminService",
    "EventAdminService",
    "JobAdminService",
    "PageAdminService",
    "SponsorAdminService",
    "TaskAdminService",
    "UserAdminService",
]

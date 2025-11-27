"""Admin domain - Dashboard, moderation, and system management."""

from pydotorg.domains.admin import urls
from pydotorg.domains.admin.controllers import (
    AdminBlogsController,
    AdminDashboardController,
    AdminEventsController,
    AdminJobsController,
    AdminLogsController,
    AdminPagesController,
    AdminSettingsController,
    AdminSponsorsController,
    AdminUsersController,
)
from pydotorg.domains.admin.dependencies import get_admin_dependencies
from pydotorg.domains.admin.guards import AdminPermission, require_any_admin_access
from pydotorg.domains.admin.schemas import (
    AdminUserRead,
    DashboardStats,
    PendingModeration,
    UserStaffUpdate,
)
from pydotorg.domains.admin.services import (
    BlogAdminService,
    DashboardService,
    EventAdminService,
    JobAdminService,
    PageAdminService,
    SponsorAdminService,
    UserAdminService,
)

__all__ = [
    "AdminBlogsController",
    "AdminDashboardController",
    "AdminEventsController",
    "AdminJobsController",
    "AdminLogsController",
    "AdminPagesController",
    "AdminPermission",
    "AdminSettingsController",
    "AdminSponsorsController",
    "AdminUserRead",
    "AdminUsersController",
    "BlogAdminService",
    "DashboardService",
    "DashboardStats",
    "EventAdminService",
    "JobAdminService",
    "PageAdminService",
    "PendingModeration",
    "SponsorAdminService",
    "UserAdminService",
    "UserStaffUpdate",
    "get_admin_dependencies",
    "require_any_admin_access",
    "urls",
]

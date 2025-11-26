"""Admin domain - Dashboard, moderation, and system management."""

from pydotorg.domains.admin import urls
from pydotorg.domains.admin.controllers import AdminDashboardController
from pydotorg.domains.admin.dependencies import get_admin_dependencies
from pydotorg.domains.admin.guards import AdminPermission, require_any_admin_access
from pydotorg.domains.admin.schemas import (
    AdminUserRead,
    DashboardStats,
    PendingModeration,
    UserStaffUpdate,
)
from pydotorg.domains.admin.services import DashboardService

__all__ = [
    "AdminDashboardController",
    "AdminPermission",
    "AdminUserRead",
    "DashboardService",
    "DashboardStats",
    "PendingModeration",
    "UserStaffUpdate",
    "get_admin_dependencies",
    "require_any_admin_access",
    "urls",
]

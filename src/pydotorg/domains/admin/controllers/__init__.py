"""Admin domain controllers."""

from pydotorg.domains.admin.controllers.dashboard import AdminDashboardController
from pydotorg.domains.admin.controllers.jobs import AdminJobsController
from pydotorg.domains.admin.controllers.sponsors import AdminSponsorsController
from pydotorg.domains.admin.controllers.users import AdminUsersController

__all__ = [
    "AdminDashboardController",
    "AdminJobsController",
    "AdminSponsorsController",
    "AdminUsersController",
]

"""Admin domain controllers."""

from pydotorg.domains.admin.controllers.analytics import AdminAnalyticsController
from pydotorg.domains.admin.controllers.blogs import AdminBlogsController
from pydotorg.domains.admin.controllers.dashboard import AdminDashboardController
from pydotorg.domains.admin.controllers.email import AdminEmailController
from pydotorg.domains.admin.controllers.events import AdminEventsController
from pydotorg.domains.admin.controllers.jobs import AdminJobsController
from pydotorg.domains.admin.controllers.logs import AdminLogsController
from pydotorg.domains.admin.controllers.pages import AdminPagesController
from pydotorg.domains.admin.controllers.settings import AdminSettingsController
from pydotorg.domains.admin.controllers.sponsors import AdminSponsorsController
from pydotorg.domains.admin.controllers.tasks import AdminTasksController
from pydotorg.domains.admin.controllers.users import AdminUsersController

__all__ = [
    "AdminAnalyticsController",
    "AdminBlogsController",
    "AdminDashboardController",
    "AdminEmailController",
    "AdminEventsController",
    "AdminJobsController",
    "AdminLogsController",
    "AdminPagesController",
    "AdminSettingsController",
    "AdminSponsorsController",
    "AdminTasksController",
    "AdminUsersController",
]

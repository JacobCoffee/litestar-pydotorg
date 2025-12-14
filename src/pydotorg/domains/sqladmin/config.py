"""SQLAdmin plugin configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from litestar.plugins.base import InitPluginProtocol
from sqladmin import Admin
from starlette.applications import Starlette

from pydotorg.domains.sqladmin.auth import AdminAuthBackend
from pydotorg.domains.sqladmin.views import (
    BannerAdmin,
    BlogEntryAdmin,
    CalendarAdmin,
    CodeSampleAdmin,
    CommunityLinkAdmin,
    CommunityPhotoAdmin,
    CommunityPostAdmin,
    CommunityVideoAdmin,
    DocumentFileAdmin,
    DownloadStatisticAdmin,
    ElectionAdmin,
    EmailLogAdmin,
    EmailTemplateAdmin,
    EventAdmin,
    EventCategoryAdmin,
    EventLocationAdmin,
    EventOccurrenceAdmin,
    FeedAdmin,
    FeedAggregateAdmin,
    ImageAdmin,
    JobAdmin,
    JobCategoryAdmin,
    JobReviewCommentAdmin,
    JobTypeAdmin,
    MembershipAdmin,
    MinutesAdmin,
    NominationAdmin,
    NomineeAdmin,
    OSAdmin,
    PageAdmin,
    RelatedBlogAdmin,
    ReleaseAdmin,
    ReleaseFileAdmin,
    SponsorAdmin,
    SponsorshipAdmin,
    SponsorshipLevelAdmin,
    StoryAdmin,
    StoryCategoryAdmin,
    UserAdmin,
    UserGroupAdmin,
    WorkGroupAdmin,
)

if TYPE_CHECKING:
    from litestar.config.app import AppConfig
    from litestar.types.asgi_types import Receive, Scope, Send
    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class SQLAdminConfig(InitPluginProtocol):
    """Custom SQLAdmin plugin configuration."""

    def __init__(
        self,
        engine: AsyncEngine,
        session_maker: async_sessionmaker,
        secret_key: str,
    ) -> None:
        """Initialize SQLAdmin configuration.

        Args:
            engine: SQLAlchemy async engine
            session_maker: SQLAlchemy async sessionmaker
            secret_key: Secret key for admin session encryption
        """
        self.engine = engine
        self.session_maker = session_maker
        self.secret_key = secret_key
        self.base_url = "/admin/db"

        self.starlette_app = Starlette()
        self.auth_backend = AdminAuthBackend(secret_key=secret_key)

        self.admin = Admin(
            app=self.starlette_app,
            engine=engine,
            session_maker=session_maker,
            base_url=self.base_url,
            title="Python.org Admin Panel",
            logo_url="/static/img/python-logo.png",
            authentication_backend=self.auth_backend,
            templates_dir=str(TEMPLATES_DIR),
        )

        self._register_views()

        self.starlette_app.router.redirect_slashes = False
        self.admin.admin.router.redirect_slashes = False

    def _register_views(self) -> None:
        """Register all model admin views."""
        views = [
            UserAdmin,
            MembershipAdmin,
            UserGroupAdmin,
            JobAdmin,
            JobTypeAdmin,
            JobCategoryAdmin,
            JobReviewCommentAdmin,
            EventAdmin,
            CalendarAdmin,
            EventCategoryAdmin,
            EventLocationAdmin,
            EventOccurrenceAdmin,
            SponsorAdmin,
            SponsorshipAdmin,
            SponsorshipLevelAdmin,
            PageAdmin,
            ImageAdmin,
            DocumentFileAdmin,
            BlogEntryAdmin,
            FeedAdmin,
            FeedAggregateAdmin,
            RelatedBlogAdmin,
            BannerAdmin,
            CodeSampleAdmin,
            CommunityPostAdmin,
            CommunityPhotoAdmin,
            CommunityVideoAdmin,
            CommunityLinkAdmin,
            OSAdmin,
            ReleaseAdmin,
            ReleaseFileAdmin,
            DownloadStatisticAdmin,
            EmailTemplateAdmin,
            EmailLogAdmin,
            MinutesAdmin,
            ElectionAdmin,
            NomineeAdmin,
            NominationAdmin,
            StoryCategoryAdmin,
            StoryAdmin,
            WorkGroupAdmin,
        ]
        for view in views:
            self.admin.add_view(view)

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Register the admin panel with Litestar."""
        from litestar import asgi

        mount_path = self.base_url.rstrip("/")

        @asgi(mount_path, is_mount=True)
        async def wrapped_app(scope: Scope, receive: Receive, send: Send) -> None:
            """Wrapper for the SQLAdmin app."""
            copied_scope = dict(scope)
            copied_scope["path"] = f"{mount_path}{scope['path']}"

            path = f"/{copied_scope['path'].lstrip('/').rstrip('/')}"
            if path == mount_path:
                path = f"{path}/"

            copied_scope["path"] = path
            copied_scope["raw_path"] = path.encode("utf-8")

            await self.starlette_app(copied_scope, receive, send)  # type: ignore[arg-type]

        app_config.route_handlers.append(wrapped_app)
        return app_config


def create_sqladmin_plugin(
    engine: AsyncEngine,
    session_maker: async_sessionmaker,
    secret_key: str,
) -> SQLAdminConfig:
    """Create and configure SQLAdmin plugin.

    Args:
        engine: SQLAlchemy async engine
        session_maker: SQLAlchemy async sessionmaker
        secret_key: Secret key for admin session encryption

    Returns:
        Configured SQLAdminConfig instance
    """
    return SQLAdminConfig(
        engine=engine,
        session_maker=session_maker,
        secret_key=secret_key,
    )

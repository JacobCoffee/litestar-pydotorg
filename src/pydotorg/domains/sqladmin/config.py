"""SQLAdmin plugin configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from litestar.plugins.base import InitPluginProtocol
from sqladmin import Admin
from starlette.applications import Starlette

from pydotorg.domains.sqladmin.auth import AdminAuthBackend
from pydotorg.domains.sqladmin.views import (
    BlogEntryAdmin,
    CalendarAdmin,
    DocumentFileAdmin,
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
    PageAdmin,
    RelatedBlogAdmin,
    SponsorAdmin,
    SponsorshipAdmin,
    SponsorshipLevelAdmin,
    UserAdmin,
    UserGroupAdmin,
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

        self.admin.add_view(UserAdmin)
        self.admin.add_view(MembershipAdmin)
        self.admin.add_view(UserGroupAdmin)
        self.admin.add_view(JobAdmin)
        self.admin.add_view(JobTypeAdmin)
        self.admin.add_view(JobCategoryAdmin)
        self.admin.add_view(JobReviewCommentAdmin)
        self.admin.add_view(EventAdmin)
        self.admin.add_view(CalendarAdmin)
        self.admin.add_view(EventCategoryAdmin)
        self.admin.add_view(EventLocationAdmin)
        self.admin.add_view(EventOccurrenceAdmin)
        self.admin.add_view(SponsorAdmin)
        self.admin.add_view(SponsorshipAdmin)
        self.admin.add_view(SponsorshipLevelAdmin)
        self.admin.add_view(PageAdmin)
        self.admin.add_view(ImageAdmin)
        self.admin.add_view(DocumentFileAdmin)
        self.admin.add_view(BlogEntryAdmin)
        self.admin.add_view(FeedAdmin)
        self.admin.add_view(FeedAggregateAdmin)
        self.admin.add_view(RelatedBlogAdmin)

        self.starlette_app.router.redirect_slashes = False
        self.admin.admin.router.redirect_slashes = False

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Register the admin panel with Litestar."""
        from litestar import asgi  # noqa: PLC0415

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

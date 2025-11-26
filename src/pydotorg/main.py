"""Litestar application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from litestar.datastructures import State

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar, get
from litestar.config.compression import CompressionConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme, Tag
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from litestar.template.config import TemplateConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.config import log_startup_banner, settings, validate_production_settings
from pydotorg.core.admin import AdminController
from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.database.base import AuditBase
from pydotorg.core.dependencies import get_core_dependencies
from pydotorg.core.exceptions import get_exception_handlers
from pydotorg.core.features import FeatureFlags
from pydotorg.core.logging import configure_structlog
from pydotorg.core.openapi import get_openapi_plugins
from pydotorg.domains.about import AboutRenderController
from pydotorg.domains.admin import (
    AdminDashboardController,
    AdminJobsController,
    AdminSponsorsController,
    AdminUsersController,
    get_admin_dependencies,
)
from pydotorg.domains.banners import (
    BannerController,
    BannersPageController,
    get_banners_dependencies,
)
from pydotorg.domains.blogs import (
    BlogEntryController,
    BlogsPageController,
    FeedAggregateController,
    FeedController,
    RelatedBlogController,
    get_blogs_dependencies,
)
from pydotorg.domains.blogs.services import BlogEntryService  # noqa: TC001
from pydotorg.domains.codesamples import (
    CodeSampleController,
    CodeSamplesPageController,
    get_codesamples_dependencies,
)
from pydotorg.domains.community import (
    CommunityPageController,
    LinkController,
    PhotoController,
    PostController,
    VideoController,
    get_community_dependencies,
)
from pydotorg.domains.docs import DocsRenderController
from pydotorg.domains.downloads import (
    DownloadsPageController,
    OSController,
    ReleaseController,
    ReleaseFileController,
    get_downloads_dependencies,
)
from pydotorg.domains.downloads.services import ReleaseService  # noqa: TC001
from pydotorg.domains.events import (
    CalendarController,
    EventCategoryController,
    EventController,
    EventLocationController,
    EventOccurrenceController,
    EventsPageController,
    get_events_dependencies,
)
from pydotorg.domains.events.services import EventService  # noqa: TC001
from pydotorg.domains.jobs import (
    JobCategoryController,
    JobController,
    JobRenderController,
    JobReviewCommentController,
    JobTypeController,
    get_jobs_dependencies,
)
from pydotorg.domains.minutes import (
    MinutesController,
    MinutesPageController,
    get_minutes_dependencies,
)
from pydotorg.domains.nominations import (
    ElectionController,
    NominationController,
    NominationsRenderController,
    NomineeController,
    get_nominations_dependencies,
)
from pydotorg.domains.pages import (
    DocumentFileController,
    ImageController,
    PageController,
    PageRenderController,
    get_page_dependencies,
)
from pydotorg.domains.search import (
    SearchAPIController,
    SearchRenderController,
    get_search_dependencies,
)
from pydotorg.domains.sponsors import (
    SponsorController,
    SponsorRenderController,
    SponsorshipController,
    SponsorshipLevelController,
)
from pydotorg.domains.sqladmin import create_sqladmin_plugin
from pydotorg.domains.successstories import (
    StoryCategoryController,
    StoryController,
    SuccessStoriesPageController,
    get_successstories_dependencies,
)
from pydotorg.domains.successstories.services import StoryService  # noqa: TC001
from pydotorg.domains.users import (
    MembershipController,
    UserController,
    UserGroupController,
    get_user_dependencies,
)
from pydotorg.domains.users.auth_controller import AuthController, AuthPageController
from pydotorg.domains.work_groups import (
    WorkGroupController,
    WorkGroupsPageController,
    get_work_groups_dependencies,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


@get("/", tags=["Application"], exclude_from_auth=True)
async def index(
    blog_entry_service: BlogEntryService,
    story_service: StoryService,
    event_service: EventService,
    release_service: ReleaseService,
) -> Template:
    """Render the home page with dynamic content."""

    recent_blog_entries = await blog_entry_service.get_recent_entries(limit=3)
    featured_stories = await story_service.get_featured_stories(limit=1)
    upcoming_events = await event_service.get_upcoming(limit=3)
    latest_release = await release_service.get_latest()

    return Template(
        template_name="pages/index.html.jinja2",
        context={
            "recent_blog_entries": recent_blog_entries,
            "featured_story": featured_stories[0] if featured_stories else None,
            "upcoming_events": upcoming_events,
            "latest_release": latest_release,
            "page_title": "Welcome to Python.org",
        },
    )


@get("/health", tags=["Application"], exclude_from_auth=True)
async def health_check(db_session: AsyncSession) -> tuple[dict[str, str | bool], int]:
    """Health check endpoint with database connectivity verification."""
    health_status = {
        "status": "healthy",
        "database": False,
    }

    try:
        await db_session.execute(text("SELECT 1"))
        health_status["database"] = True
        return health_status, HTTP_200_OK
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return health_status, HTTP_503_SERVICE_UNAVAILABLE


def get_all_dependencies() -> dict:
    """Aggregate all domain dependencies."""
    deps = {}
    deps.update(get_core_dependencies())
    deps.update(get_user_dependencies())
    deps.update(get_page_dependencies())
    deps.update(get_downloads_dependencies())
    deps.update(get_jobs_dependencies())
    deps.update(get_events_dependencies())
    deps.update(get_blogs_dependencies())
    deps.update(get_banners_dependencies())
    deps.update(get_codesamples_dependencies())
    deps.update(get_community_dependencies())
    deps.update(get_minutes_dependencies())
    deps.update(get_nominations_dependencies())
    deps.update(get_successstories_dependencies())
    deps.update(get_work_groups_dependencies())
    deps.update(get_search_dependencies())
    deps.update(get_admin_dependencies())
    return deps


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=str(settings.database_url),
    metadata=AuditBase.metadata,
    create_all=settings.create_all,
)

sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

sqladmin_plugin = create_sqladmin_plugin(
    engine=sqlalchemy_config.get_engine(),
    session_maker=sqlalchemy_config.create_session_maker(),
    secret_key=settings.session_secret_key,
)


def _derive_session_secret(key: str) -> bytes:
    """Derive a 32-byte secret key for session encryption."""
    import hashlib  # noqa: PLC0415

    return hashlib.sha256(key.encode()).digest()


session_config = CookieBackendConfig(
    secret=_derive_session_secret(settings.session_secret_key),
    max_age=settings.session_expire_minutes * 60,
)

templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent.parent.parent / "static"


def configure_template_engine(engine: JinjaTemplateEngine) -> None:
    """Configure the Jinja2 template engine with global context."""
    from datetime import datetime  # noqa: PLC0415

    feature_flags = FeatureFlags(
        enable_oauth=settings.features.enable_oauth,
        enable_jobs=settings.features.enable_jobs,
        enable_sponsors=settings.features.enable_sponsors,
        enable_search=settings.features.enable_search,
        maintenance_mode=settings.features.maintenance_mode,
    )
    engine.engine.globals.update(
        {
            "feature_flags": feature_flags.to_dict(),
            "site_name": settings.site_name,
            "now": datetime.now,
        }
    )


template_config = TemplateConfig(
    directory=templates_dir,
    engine=JinjaTemplateEngine,
    engine_callback=configure_template_engine,
)

flash_plugin = FlashPlugin(config=FlashConfig(template_config=template_config))

structlog_plugin = configure_structlog(
    log_level=settings.log_level,
    use_json=not settings.is_debug,
)


def on_app_init(app_config: AppConfig) -> AppConfig:
    """Initialize application state with feature flags."""
    if app_config.state is None:
        app_config.state = State()
    app_config.state["feature_flags"] = FeatureFlags(
        enable_oauth=settings.features.enable_oauth,
        enable_jobs=settings.features.enable_jobs,
        enable_sponsors=settings.features.enable_sponsors,
        enable_search=settings.features.enable_search,
        maintenance_mode=settings.features.maintenance_mode,
    )
    return app_config


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None]:
    """Application lifespan hook for startup and shutdown tasks."""
    logger.info("Application startup initiated")

    try:
        validate_production_settings()
        logger.info("Configuration validated successfully")
    except Exception:
        logger.exception("Configuration validation failed")
        raise

    log_startup_banner()

    yield

    logger.info("Application shutdown initiated")


app = Litestar(
    route_handlers=[
        index,
        health_check,
        AdminController,
        create_static_files_router(
            path="/static",
            directories=[static_dir] if static_dir.exists() else [],
            name="static",
        ),
        UserController,
        MembershipController,
        UserGroupController,
        AuthController,
        AuthPageController,
        PageController,
        PageRenderController,
        ImageController,
        DocumentFileController,
        OSController,
        ReleaseController,
        ReleaseFileController,
        DownloadsPageController,
        DocsRenderController,
        AboutRenderController,
        JobTypeController,
        JobCategoryController,
        JobController,
        JobRenderController,
        JobReviewCommentController,
        CalendarController,
        EventCategoryController,
        EventLocationController,
        EventController,
        EventOccurrenceController,
        EventsPageController,
        FeedController,
        BlogEntryController,
        FeedAggregateController,
        RelatedBlogController,
        BlogsPageController,
        SponsorshipLevelController,
        SponsorController,
        SponsorshipController,
        SponsorRenderController,
        BannerController,
        BannersPageController,
        CodeSampleController,
        CodeSamplesPageController,
        PostController,
        PhotoController,
        VideoController,
        LinkController,
        CommunityPageController,
        MinutesController,
        MinutesPageController,
        ElectionController,
        NomineeController,
        NominationController,
        NominationsRenderController,
        StoryCategoryController,
        StoryController,
        SuccessStoriesPageController,
        WorkGroupController,
        WorkGroupsPageController,
        SearchAPIController,
        SearchRenderController,
        AdminDashboardController,
        AdminJobsController,
        AdminSponsorsController,
        AdminUsersController,
    ],
    dependencies=get_all_dependencies(),
    exception_handlers=get_exception_handlers(),
    plugins=[sqlalchemy_plugin, sqladmin_plugin, flash_plugin, structlog_plugin],
    middleware=[session_config.middleware, JWTAuthMiddleware],
    template_config=template_config,
    openapi_config=OpenAPIConfig(
        title=settings.site_name,
        version="0.1.0",
        description=settings.site_description,
        path="/api",
        render_plugins=get_openapi_plugins(),
        components=Components(
            security_schemes={
                "BearerAuth": SecurityScheme(
                    type="http",
                    scheme="bearer",
                    bearer_format="JWT",
                    description="JWT token from /api/auth/login or OAuth (/api/auth/oauth/github)",
                ),
            }
        ),
        security=[{"BearerAuth": []}],
        tags=[
            Tag(name="Application", description="Core application endpoints"),
            Tag(name="Authentication", description="User authentication and registration"),
            Tag(name="Users", description="User management"),
            Tag(name="Pages", description="CMS pages and content"),
            Tag(name="Downloads", description="Python releases and downloads"),
            Tag(name="Jobs", description="Job board"),
            Tag(name="Events", description="Community events and calendar"),
            Tag(name="Blogs", description="Blog posts and feeds"),
            Tag(name="Sponsors", description="PSF sponsors"),
            Tag(name="Banners", description="Site banners"),
            Tag(name="Code Samples", description="Python code examples"),
            Tag(name="Community", description="Community content"),
            Tag(name="Minutes", description="PSF meeting minutes"),
            Tag(name="Success Stories", description="Python success stories"),
            Tag(name="Work Groups", description="PSF work groups"),
            Tag(name="Search", description="Site-wide search"),
            Tag(name="Admin", description="Admin dashboard and management"),
        ],
    ),
    compression_config=CompressionConfig(backend="gzip", gzip_compress_level=6),
    debug=settings.is_debug,
    on_app_init=[on_app_init],
    lifespan=[lifespan],
)

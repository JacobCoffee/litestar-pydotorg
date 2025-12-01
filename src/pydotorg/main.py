"""Litestar application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from litestar.datastructures import State
from litestar.exceptions import TooManyRequestsException
from litestar.stores.redis import RedisStore

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

from advanced_alchemy.extensions.litestar import AlembicAsyncConfig, SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar, get
from litestar.config.compression import CompressionConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import (
    Components,
    Contact,
    ExternalDocumentation,
    License,
    SecurityScheme,
    Server,
    Tag,
)
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from litestar.template.config import TemplateConfig
from litestar_vite import ViteConfig, VitePlugin
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.config import log_startup_banner, settings, validate_production_settings
from pydotorg.core.admin import AdminController
from pydotorg.core.auth.middleware import JWTAuthMiddleware, UserPopulationMiddleware
from pydotorg.core.banners_middleware import APIBannerMiddleware, SitewideBannerMiddleware
from pydotorg.core.cache import create_response_cache_config
from pydotorg.core.database.base import AuditBase
from pydotorg.core.dependencies import get_core_dependencies
from pydotorg.core.exceptions import get_exception_handlers
from pydotorg.core.features import FeatureFlags
from pydotorg.core.logging import configure_structlog
from pydotorg.core.openapi import get_openapi_plugins
from pydotorg.core.ratelimit import create_rate_limit_config, rate_limit_exception_handler
from pydotorg.core.security.csrf import create_csrf_config
from pydotorg.core.worker import saq_plugin
from pydotorg.domains.about import AboutRenderController, PSFRenderController
from pydotorg.domains.admin import (
    AdminAnalyticsController,
    AdminBannersController,
    AdminBlogsController,
    AdminDashboardController,
    AdminEmailController,
    AdminEventsController,
    AdminJobsController,
    AdminLogsController,
    AdminPagesController,
    AdminSettingsController,
    AdminSponsorsController,
    AdminTasksController,
    AdminUsersController,
    get_admin_dependencies,
)
from pydotorg.domains.banners import (
    BannerController,
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
from pydotorg.domains.mailing import (
    EmailLogController,
    EmailTemplateController,
    get_mailing_dependencies,
)
from pydotorg.domains.minutes import (
    MinutesController,
    MinutesPageController,
    get_minutes_dependencies,
)
from pydotorg.domains.nominations import (
    ElectionController,
    NominationController,
    NominationsHTMXController,
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
    deps.update(get_mailing_dependencies())
    deps.update(get_admin_dependencies())
    return deps


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=str(settings.database_url),
    metadata=AuditBase.metadata,
    create_all=settings.create_all,
    alembic_config=AlembicAsyncConfig(
        script_location="src/pydotorg/db/migrations",
        version_table_name="alembic_version",
    ),
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
resources_dir = Path(__file__).parent.parent.parent / "resources"

vite_plugin = VitePlugin(
    config=ViteConfig(
        bundle_dir=static_dir,
        resource_dir=resources_dir,
        public_dir=static_dir,
        dev_mode=settings.is_debug,
        hot_reload=settings.is_debug,
        port=5173,
        host="localhost",
        set_static_folders=False,
    )
)


def configure_template_engine(engine: JinjaTemplateEngine) -> None:  # noqa: PLR0915
    """Configure the Jinja2 template engine with global context."""
    from datetime import UTC, datetime  # noqa: PLC0415

    import cmarkgfm  # noqa: PLC0415

    ms_threshold = 1e12
    minute = 60
    hour = 3600
    day = 86400
    week_days = 7

    def _parse_timestamp(value: str | datetime | int | float | None) -> datetime | None:  # noqa: PLR0911
        """Parse various timestamp formats into a datetime object.

        Handles ISO strings, datetime objects, and Unix timestamps (seconds or milliseconds).
        """
        if value is None or value == 0:
            return None
        try:
            if isinstance(value, str):
                if "T" in value:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))  # noqa: FURB162
                return None
            if isinstance(value, (int, float)):
                if value == 0:
                    return None
                ts = float(value)
                if ts > ms_threshold:
                    ts = ts / 1000
                return datetime.fromtimestamp(ts, tz=UTC)
            if isinstance(value, datetime):
                return value if value.tzinfo else value.replace(tzinfo=UTC)
            return None
        except (ValueError, TypeError, OSError):
            return None

    def friendly_date(value: str | datetime | int | float | None, fmt: str = "%b %d, %Y at %I:%M %p") -> str:
        """Format a date/timestamp as a friendly string.

        Handles ISO strings, datetime objects, and Unix timestamps.
        """
        dt = _parse_timestamp(value)
        if dt is None:
            return "N/A" if value is None or value == 0 else str(value)
        return dt.strftime(fmt)

    def time_ago(value: str | datetime | int | float | None) -> str:  # noqa: PLR0911
        """Format a date/timestamp as relative time (e.g., '5 minutes ago' or 'in 2 hours')."""
        dt = _parse_timestamp(value)
        if dt is None:
            return "N/A" if value is None or value == 0 else str(value)

        now = datetime.now(tz=UTC)
        diff = now - dt
        seconds = diff.total_seconds()

        if seconds < 0:
            future_seconds = -seconds
            if future_seconds < minute:
                return "in a moment"
            if future_seconds < hour:
                mins = int(future_seconds / minute)
                return f"in {mins} min{'s' if mins != 1 else ''}"
            if future_seconds < day:
                hours = int(future_seconds / hour)
                return f"in {hours} hour{'s' if hours != 1 else ''}"
            days = int(future_seconds / day)
            if days == 1:
                return "tomorrow"
            if days < week_days:
                return f"in {days} days"
            return dt.strftime("%b %d, %Y")
        if seconds < minute:
            return "just now"
        if seconds < hour:
            mins = int(seconds / minute)
            return f"{mins} min{'s' if mins != 1 else ''} ago"
        if seconds < day:
            hours = int(seconds / hour)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = int(seconds / day)
        if days == 1:
            return "yesterday"
        if days < week_days:
            return f"{days} days ago"
        return dt.strftime("%b %d, %Y")

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

    def pretty_json(value: dict | list | str | None) -> str:
        """Format a value as pretty-printed JSON."""
        import json  # noqa: PLC0415

        if value is None:
            return "null"
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2, default=str)
        return str(value)

    def format_traceback(value: str | None) -> str:
        """Format a traceback string for better readability with proper line breaks."""
        if not value:
            return ""
        return value.replace("\\n", "\n")

    def render_markdown(content: str | None) -> str:
        """Render markdown content to HTML using GitHub-flavored markdown.

        Args:
            content: The markdown content to render.

        Returns:
            Rendered HTML string, or empty string if content is None/empty.
        """
        if not content:
            return ""
        return cmarkgfm.github_flavored_markdown_to_html(content)

    engine.engine.filters["friendly_date"] = friendly_date
    engine.engine.filters["time_ago"] = time_ago
    engine.engine.filters["pretty_json"] = pretty_json
    engine.engine.filters["format_traceback"] = format_traceback
    engine.engine.filters["markdown"] = render_markdown


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

csrf_config = create_csrf_config()
rate_limit_config = create_rate_limit_config(settings)
response_cache_config = create_response_cache_config()


def get_exception_handlers_with_rate_limit() -> dict:
    """Get exception handlers including rate limit handler."""
    handlers = get_exception_handlers()
    handlers[TooManyRequestsException] = rate_limit_exception_handler
    return handlers


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
    import sys  # noqa: PLC0415

    try:
        validate_production_settings()
    except Exception:
        logger.exception("Configuration validation failed")
        raise

    log_startup_banner()

    async with sqlalchemy_config.get_engine().connect() as conn:
        try:
            await conn.execute(text("SELECT 1"))
        except Exception as e:
            error_msg = str(e)
            sys.stderr.write("\n")
            sys.stderr.write("\033[91m" + "=" * 60 + "\033[0m\n")
            sys.stderr.write("\033[91m❌ DATABASE CONNECTION FAILED\033[0m\n")
            sys.stderr.write("\033[91m" + "=" * 60 + "\033[0m\n\n")

            if "Connection refused" in error_msg:
                sys.stderr.write("\033[93mPostgreSQL is not running.\033[0m\n\n")
                sys.stderr.write("To start the database, run:\n")
                sys.stderr.write("\033[96m  make infra-up\033[0m\n\n")
            elif "password authentication failed" in error_msg:
                sys.stderr.write("\033[93mDatabase authentication failed.\033[0m\n\n")
                sys.stderr.write("Check your DATABASE_URL environment variable.\n")
            elif "does not exist" in error_msg:
                sys.stderr.write("\033[93mDatabase does not exist.\033[0m\n\n")
                sys.stderr.write("Run migrations or create the database:\n")
                sys.stderr.write("\033[96m  make db-migrate\033[0m\n\n")
            else:
                sys.stderr.write(f"\033[93m{error_msg}\033[0m\n\n")

            db_url_str = str(settings.database_url)
            obscured = (
                db_url_str.replace(db_url_str.split("@")[0].split(":")[-1], "***") if "@" in db_url_str else db_url_str
            )
            sys.stderr.write(f"Connection string: {obscured}\n")
            sys.stderr.write("\033[91m" + "=" * 60 + "\033[0m\n\n")
            sys.stderr.flush()
            raise

    yield

    sys.stdout.write("\n\033[93m⏹ Shutting down application...\033[0m\n")
    sys.stdout.flush()


app = Litestar(
    route_handlers=[
        index,
        health_check,
        AdminController,
        AdminAnalyticsController,
        AdminBannersController,
        AdminBlogsController,
        AdminDashboardController,
        AdminEmailController,
        AdminEventsController,
        AdminJobsController,
        AdminLogsController,
        AdminPagesController,
        AdminSettingsController,
        AdminSponsorsController,
        AdminTasksController,
        AdminUsersController,
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
        PSFRenderController,
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
        NominationsHTMXController,
        NominationsRenderController,
        StoryCategoryController,
        StoryController,
        SuccessStoriesPageController,
        WorkGroupController,
        WorkGroupsPageController,
        SearchAPIController,
        SearchRenderController,
        EmailTemplateController,
        EmailLogController,
    ],
    dependencies=get_all_dependencies(),
    exception_handlers=get_exception_handlers_with_rate_limit(),
    plugins=[sqlalchemy_plugin, sqladmin_plugin, flash_plugin, structlog_plugin, saq_plugin, vite_plugin],
    middleware=[
        session_config.middleware,
        SitewideBannerMiddleware,
        APIBannerMiddleware,
        UserPopulationMiddleware,
        JWTAuthMiddleware,
        rate_limit_config.middleware,
    ],
    stores={
        "rate_limit": RedisStore.with_client(url=settings.redis_url),
        "response_cache": RedisStore.with_client(url=settings.redis_url, namespace="cache"),
    },
    response_cache_config=response_cache_config,
    template_config=template_config,
    openapi_config=OpenAPIConfig(
        title=settings.site_name,
        version="0.1.0",
        description=settings.site_description,
        path="/api",
        render_plugins=get_openapi_plugins(),
        contact=Contact(
            name="Python.org",
            url="https://www.python.org",
            email="webmaster@python.org",
        ),
        license=License(
            name="Apache 2.0",
            identifier="Apache-2.0",
            url="https://www.apache.org/licenses/LICENSE-2.0",
        ),
        external_docs=ExternalDocumentation(
            url="https://docs.python.org",
            description="Python Documentation",
        ),
        servers=[
            Server(url="http://localhost:8000", description="Development"),
            Server(url="https://staging.python.org", description="Staging"),
            Server(url="https://www.python.org", description="Production"),
        ],
        use_handler_docstrings=True,
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
            Tag(
                name="Application",
                description="Core application endpoints including health checks and system status",
            ),
            Tag(
                name="Authentication",
                description=(
                    "User authentication, registration, and session management. "
                    "Supports JWT tokens, cookie sessions, and OAuth (GitHub). "
                    "Use POST /api/auth/login for JWT tokens or POST /api/auth/session/login for cookies."
                ),
            ),
            Tag(
                name="Users",
                description=(
                    "User account management including profile retrieval, updates, and search. "
                    "Also includes user groups and memberships for permission management."
                ),
            ),
            Tag(
                name="Pages",
                description="Content management system for static pages, including images and document files",
            ),
            Tag(
                name="Downloads",
                description=(
                    "Python release downloads including OS-specific binaries, release notes, "
                    "and file metadata. Supports filtering by OS and Python version."
                ),
            ),
            Tag(
                name="Jobs",
                description=(
                    "Python job board for posting and browsing Python-related positions. "
                    "Includes job types, categories, and review workflow."
                ),
            ),
            Tag(
                name="Events",
                description=(
                    "Community events calendar including conferences, meetups, and workshops. "
                    "Supports recurring events, locations, and category filtering."
                ),
            ),
            Tag(
                name="Blogs",
                description="Aggregated Python community blog feeds and entries from various sources",
            ),
            Tag(
                name="Sponsors",
                description=(
                    "Python Software Foundation sponsors and sponsorship levels. "
                    "Includes sponsor details, logos, and sponsorship periods."
                ),
            ),
            Tag(name="Banners", description="Site-wide announcement banners with display scheduling"),
            Tag(
                name="Code Samples",
                description="Python code examples and snippets for educational purposes",
            ),
            Tag(
                name="Community",
                description="Community-contributed content including posts, photos, videos, and links",
            ),
            Tag(name="Minutes", description="PSF board meeting minutes and governance documentation"),
            Tag(
                name="Nominations",
                description="PSF board elections, nominee information, and voting records",
            ),
            Tag(
                name="Success Stories",
                description=(
                    "Python success stories showcasing real-world applications and case studies "
                    "from companies and individuals using Python."
                ),
            ),
            Tag(
                name="Work Groups",
                description="PSF work groups and special interest groups",
            ),
            Tag(
                name="Search",
                description=(
                    "Full-text search across all content types. "
                    "Supports filtering by content type and provides autocomplete suggestions."
                ),
            ),
            Tag(
                name="Admin",
                description="Administrative dashboard and management tools (staff access required)",
            ),
        ],
    ),
    compression_config=CompressionConfig(backend="gzip", gzip_compress_level=6),
    csrf_config=csrf_config,
    debug=settings.is_debug,
    on_app_init=[on_app_init],
    lifespan=[lifespan],
)

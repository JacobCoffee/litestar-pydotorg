"""Litestar application entry point."""

from __future__ import annotations

from pathlib import Path

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar, get
from litestar.config.compression import CompressionConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.openapi import OpenAPIConfig
from litestar.static_files import create_static_files_router
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from litestar.template.config import TemplateConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.config import settings
from pydotorg.core.database.base import AuditBase
from pydotorg.domains.blogs import (
    BlogEntryController,
    BlogsPageController,
    FeedAggregateController,
    FeedController,
    RelatedBlogController,
    get_blogs_dependencies,
)
from pydotorg.domains.downloads import (
    DownloadsPageController,
    OSController,
    ReleaseController,
    ReleaseFileController,
    get_downloads_dependencies,
)
from pydotorg.domains.events import (
    CalendarController,
    EventCategoryController,
    EventController,
    EventLocationController,
    EventOccurrenceController,
    EventsPageController,
    get_events_dependencies,
)
from pydotorg.domains.jobs import (
    JobCategoryController,
    JobController,
    JobRenderController,
    JobReviewCommentController,
    JobTypeController,
    get_jobs_dependencies,
)
from pydotorg.domains.pages import (
    DocumentFileController,
    ImageController,
    PageController,
    PageRenderController,
    get_page_dependencies,
)
from pydotorg.domains.sponsors import (
    SponsorController,
    SponsorRenderController,
    SponsorshipController,
    SponsorshipLevelController,
)
from pydotorg.domains.users import (
    AuthController,
    MembershipController,
    UserController,
    UserGroupController,
    get_user_dependencies,
)


@get("/", sync_to_thread=False)
def index() -> dict[str, str]:
    return {
        "name": settings.site_name,
        "description": settings.site_description,
        "version": "0.1.0",
    }


@get("/health")
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
    deps.update(get_user_dependencies())
    deps.update(get_page_dependencies())
    deps.update(get_downloads_dependencies())
    deps.update(get_jobs_dependencies())
    deps.update(get_events_dependencies())
    deps.update(get_blogs_dependencies())
    return deps


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=str(settings.database_url),
    metadata=AuditBase.metadata,
    create_all=settings.debug,
)

sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent.parent.parent / "static"


app = Litestar(
    route_handlers=[
        index,
        health_check,
        create_static_files_router(
            path="/static",
            directories=[static_dir] if static_dir.exists() else [],
            name="static",
        ),
        UserController,
        MembershipController,
        UserGroupController,
        AuthController,
        PageController,
        PageRenderController,
        ImageController,
        DocumentFileController,
        OSController,
        ReleaseController,
        ReleaseFileController,
        DownloadsPageController,
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
    ],
    dependencies=get_all_dependencies(),
    plugins=[sqlalchemy_plugin],
    template_config=TemplateConfig(
        directory=templates_dir,
        engine=JinjaTemplateEngine,
    ),
    openapi_config=OpenAPIConfig(
        title=settings.site_name,
        version="0.1.0",
        description=settings.site_description,
    ),
    compression_config=CompressionConfig(backend="gzip", gzip_compress_level=6),
    debug=settings.debug,
)

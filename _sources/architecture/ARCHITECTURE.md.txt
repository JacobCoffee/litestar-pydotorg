# Litestar Python.org Architecture

## Executive Summary

This document outlines the comprehensive architecture for migrating python.org from Django to Litestar. The migration preserves all functionality while modernizing the tech stack to leverage async Python, type safety, and modern architectural patterns.

**Status**: Proposed
**Version**: 1.0
**Date**: 2025-11-25
**Target Litestar Version**: 2.x
**Python Version**: 3.12+

---

## System Overview

### Current Django Architecture

The existing python.org Django application consists of:

- **17 Django Apps**: banners, blogs, boxes, cms, codesamples, community, companies, downloads, events, jobs, mailing, minutes, nominations, pages, sponsors, successstories, users, work_groups
- **41 Database Tables** (across all migrations)
- **Authentication**: django-allauth for OAuth and email/username auth
- **Background Tasks**: Celery with Redis broker
- **Search**: Haystack integration
- **Static Assets**: Django Pipeline for CSS/JS compilation
- **Cache Invalidation**: Fastly CDN integration
- **APIs**: Both Tastypie (v1) and Django REST Framework (v2)

### Target Litestar Architecture

The new architecture will be:

- **Modular Domain-Driven**: Each Django app becomes a domain module
- **Async-First**: Leveraging SQLAlchemy 2.0 async capabilities
- **Type-Safe**: Full type hints with Pydantic v2
- **Modern Tooling**: uv, Ruff, SAQ for background tasks
- **API-Centric**: RESTful API with automatic OpenAPI documentation
- **Cloud-Native**: Container-ready with proper health checks

---

## Technology Stack

### Core Framework Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Web Framework** | Litestar | 2.x | Modern async framework with excellent DX |
| **ORM** | SQLAlchemy | 2.0+ | Industry standard, async support, type-safe |
| **ORM Helper** | Advanced Alchemy | latest | Litestar-native database utilities |
| **Migrations** | Alembic | latest | SQLAlchemy's migration tool |
| **Validation** | Pydantic | 2.x | Type-safe data validation, Litestar native |
| **Templates** | Jinja2 | 3.x | Compatible with Django templates |
| **Background Tasks** | SAQ | latest | Async task queue, simpler than Celery |
| **Cache** | Redis | 7.x | Session storage, task queue backend |
| **Search** | Meilisearch | latest | Modern, fast alternative to Elasticsearch |
| **Package Manager** | uv | latest | Fast, reliable dependency management |

### Development & Quality Tools

| Tool | Purpose |
|------|---------|
| **Ruff** | Linting and formatting |
| **Mypy** | Static type checking |
| **Pytest** | Testing framework |
| **pytest-asyncio** | Async test support |
| **httpx** | Async HTTP client for testing |
| **Factory Boy** | Test data generation |
| **Faker** | Fake data generation |

### Infrastructure & DevOps

| Component | Technology |
|-----------|-----------|
| **Database** | PostgreSQL 15+ |
| **Container** | Docker with multi-stage builds |
| **Orchestration** | Docker Compose (dev), Kubernetes (prod) |
| **Reverse Proxy** | Nginx or Caddy |
| **CDN** | Fastly (maintained) |
| **Monitoring** | Prometheus + Grafana |
| **Logging** | Structured logging with Structlog |

---

## Project Structure

### Directory Layout

```
litestar-pydotorg/
├── pyproject.toml              # Project metadata & dependencies
├── uv.lock                     # Locked dependencies
├── .python-version             # Python version pin
├── alembic.ini                 # Database migration config
│
├── src/
│   └── pydotorg/
│       ├── __init__.py
│       ├── main.py             # Application entry point
│       ├── config.py           # Configuration management
│       ├── deps.py             # Dependency injection
│       │
│       ├── core/               # Core infrastructure
│       │   ├── __init__.py
│       │   ├── auth/           # Authentication & authorization
│       │   ├── cache/          # Caching utilities
│       │   ├── database/       # Database configuration
│       │   ├── exceptions/     # Custom exceptions
│       │   ├── middleware/     # Custom middleware
│       │   ├── security/       # Security utilities
│       │   └── templates/      # Template configuration
│       │
│       ├── lib/                # Shared utilities
│       │   ├── __init__.py
│       │   ├── dto/            # Data Transfer Objects
│       │   ├── guards/         # Route guards
│       │   ├── schemas/        # Pydantic schemas
│       │   └── utils/          # Helper functions
│       │
│       ├── domains/            # Domain modules (former Django apps)
│       │   ├── __init__.py
│       │   │
│       │   ├── users/
│       │   │   ├── __init__.py
│       │   │   ├── models.py       # SQLAlchemy models
│       │   │   ├── schemas.py      # Pydantic schemas
│       │   │   ├── services.py     # Business logic
│       │   │   ├── controllers.py  # HTTP handlers
│       │   │   ├── dependencies.py # Domain-specific deps
│       │   │   └── guards.py       # Domain-specific guards
│       │   │
│       │   ├── pages/
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── schemas.py
│       │   │   ├── services.py
│       │   │   ├── controllers.py
│       │   │   └── repositories.py # Data access layer
│       │   │
│       │   ├── downloads/
│       │   ├── events/
│       │   ├── jobs/
│       │   ├── community/
│       │   ├── sponsors/
│       │   ├── blogs/
│       │   └── [... other domains]
│       │
│       ├── tasks/              # Background tasks
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── downloads.py
│       │   ├── events.py
│       │   └── search.py
│       │
│       └── api/                # API versioning
│           ├── __init__.py
│           ├── v1/             # Legacy API compatibility
│           └── v2/             # Modern API
│
├── migrations/                 # Alembic migrations
│   ├── versions/
│   └── env.py
│
├── templates/                  # Jinja2 templates
│   ├── base.html
│   ├── users/
│   ├── pages/
│   └── [... domain templates]
│
├── static/                     # Static assets
│   ├── css/
│   ├── js/
│   └── img/
│
├── tests/                      # Test suite
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                    # Utility scripts
│   ├── import_django_data.py
│   └── setup_dev.sh
│
└── docs/                       # Documentation
    ├── architecture/
    ├── api/
    └── deployment/
```

### Module Organization Pattern

Each domain follows a consistent structure:

```python
# domains/example/models.py
from sqlalchemy.orm import Mapped, mapped_column
from pydotorg.core.database import Base

class Example(Base):
    __tablename__ = "example"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

# domains/example/schemas.py
from pydantic import BaseModel, ConfigDict

class ExampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class ExampleCreate(BaseModel):
    name: str

# domains/example/services.py
from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncSession

class ExampleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ExampleCreate) -> Example:
        ...

# domains/example/controllers.py
from litestar import Controller, get, post
from litestar.di import Provide

class ExampleController(Controller):
    path = "/examples"
    dependencies = {"service": Provide(get_example_service)}

    @get("/")
    async def list_examples(self, service: ExampleService) -> list[ExampleRead]:
        ...

    @post("/")
    async def create_example(
        self,
        data: ExampleCreate,
        service: ExampleService
    ) -> ExampleRead:
        ...
```

---

## Domain Model

### Domain Mapping (Django Apps → Litestar Domains)

| Django App | Litestar Domain | Primary Responsibility |
|------------|-----------------|------------------------|
| users | domains/users | User management, authentication, membership |
| pages | domains/pages | CMS pages, flat content |
| downloads | domains/downloads | Python releases, files, OS listings |
| events | domains/events | Calendar, events, recurring rules |
| jobs | domains/jobs | Job board postings, categories |
| community | domains/community | Posts, media (photos/videos/links) |
| sponsors | domains/sponsors | Sponsorship management |
| blogs | domains/blogs | Blog aggregation |
| boxes | domains/boxes | Content widgets/boxes |
| cms | domains/cms | Base CMS functionality (mixin patterns) |
| banners | domains/banners | Banner management |
| codesamples | domains/codesamples | Code snippet repository |
| companies | domains/companies | Company directory |
| mailing | domains/mailing | Mailing list integration |
| minutes | domains/minutes | Board meeting minutes |
| nominations | domains/nominations | PSF nominations |
| successstories | domains/successstories | Success story content |
| work_groups | domains/work_groups | PSF working groups |

### Cross-Domain Dependencies

```
users (core)
  ↑
  ├── pages (depends on users for creator)
  ├── events (depends on users for creator)
  ├── jobs (depends on users for submitter)
  ├── community (depends on users for creator)
  └── sponsors (depends on users for membership)

downloads
  ↑
  └── boxes (downloads box generation)

events
  ↑
  └── community (event posts)
```

**Design Principle**: Minimize circular dependencies. Core domains (users, cms) have no dependencies. Feature domains depend on core but not each other.

---

## Database Architecture

### Schema Design Principles

1. **Async SQLAlchemy 2.0**: Use `AsyncSession` throughout
2. **Type Annotations**: Full `Mapped[]` type hints
3. **Base Model Pattern**: Common fields in abstract base
4. **Indexes**: Strategic indexing for query patterns
5. **Constraints**: Database-level integrity enforcement

### Base Model

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base for all database models."""
    pass

class TimestampMixin:
    """Mixin for created/updated timestamps."""
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class CreatorMixin:
    """Mixin for creator tracking."""
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    last_modified_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
```

### Key Models Overview

#### Users Domain

```python
# users/models.py
from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    first_name: Mapped[Optional[str]] = mapped_column(String(150))
    last_name: Mapped[Optional[str]] = mapped_column(String(150))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Profile fields
    bio: Mapped[Optional[str]] = mapped_column(Text)
    bio_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")

    search_visibility: Mapped[int] = mapped_column(Integer, default=1)
    email_privacy: Mapped[int] = mapped_column(Integer, default=2)
    public_profile: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    membership: Mapped[Optional["Membership"]] = relationship(
        back_populates="creator",
        uselist=False
    )

class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )

    membership_type: Mapped[int] = mapped_column(Integer, default=0)
    legal_name: Mapped[str] = mapped_column(String(100))
    preferred_name: Mapped[str] = mapped_column(String(100))
    email_address: Mapped[str] = mapped_column(String(100))

    city: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))

    psf_code_of_conduct: Mapped[Optional[bool]]
    psf_announcements: Mapped[Optional[bool]]
    votes: Mapped[bool] = mapped_column(Boolean, default=False)
    last_vote_affirmation: Mapped[Optional[datetime]]

    creator: Mapped["User"] = relationship(back_populates="membership")
```

#### Pages Domain

```python
# pages/models.py
class Page(Base, TimestampMixin, CreatorMixin):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    keywords: Mapped[Optional[str]] = mapped_column(String(1000))
    description: Mapped[Optional[str]] = mapped_column(Text)

    path: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True
    )

    content: Mapped[str] = mapped_column(Text)
    content_markup_type: Mapped[str] = mapped_column(
        String(30),
        default="restructuredtext"
    )

    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    content_type: Mapped[str] = mapped_column(String(150), default="text/html")
    template_name: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index('ix_pages_path_published', 'path', 'is_published'),
    )
```

#### Downloads Domain

```python
# downloads/models.py
class OS(Base, TimestampMixin, CreatorMixin):
    __tablename__ = "operating_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)

    releases: Mapped[list["ReleaseFile"]] = relationship(back_populates="os")

class Release(Base, TimestampMixin, CreatorMixin):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)

    version: Mapped[int] = mapped_column(Integer, default=3)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    pre_release: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    show_on_download_page: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    release_page_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pages.id", ondelete="SET NULL")
    )
    release_notes_url: Mapped[Optional[str]] = mapped_column(String(200))

    content: Mapped[str] = mapped_column(Text, default="")
    content_markup_type: Mapped[str] = mapped_column(String(30), default="markdown")

    files: Mapped[list["ReleaseFile"]] = relationship(back_populates="release")

class ReleaseFile(Base, TimestampMixin, CreatorMixin):
    __tablename__ = "release_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)

    os_id: Mapped[int] = mapped_column(ForeignKey("operating_systems.id"))
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id"))

    description: Mapped[Optional[str]] = mapped_column(Text)
    is_source: Mapped[bool] = mapped_column(Boolean, default=False)
    url: Mapped[str] = mapped_column(String(500), unique=True, index=True)

    gpg_signature_file: Mapped[Optional[str]] = mapped_column(String(500))
    sigstore_signature_file: Mapped[Optional[str]] = mapped_column(String(500))
    sigstore_cert_file: Mapped[Optional[str]] = mapped_column(String(500))
    sigstore_bundle_file: Mapped[Optional[str]] = mapped_column(String(500))
    sbom_spdx2_file: Mapped[Optional[str]] = mapped_column(String(500))

    md5_sum: Mapped[Optional[str]] = mapped_column(String(200))
    filesize: Mapped[int] = mapped_column(Integer, default=0)
    download_button: Mapped[bool] = mapped_column(Boolean, default=False)

    os: Mapped["OS"] = relationship(back_populates="releases")
    release: Mapped["Release"] = relationship(back_populates="files")

    __table_args__ = (
        UniqueConstraint(
            'os_id', 'release_id',
            name='uq_one_download_per_os_per_release',
            sqlite_where='download_button = true'
        ),
    )
```

#### Events Domain

```python
# events/models.py
class Calendar(Base, TimestampMixin, CreatorMixin):
    __tablename__ = "calendars"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    url: Mapped[Optional[str]] = mapped_column(String(500))
    rss: Mapped[Optional[str]] = mapped_column(String(500))
    embed: Mapped[Optional[str]] = mapped_column(String(500))
    twitter: Mapped[Optional[str]] = mapped_column(String(500))

    events: Mapped[list["Event"]] = relationship(back_populates="calendar")

class Event(Base, TimestampMixin, CreatorMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[Optional[str]] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))

    calendar_id: Mapped[int] = mapped_column(ForeignKey("calendars.id"))
    venue_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("event_locations.id", ondelete="SET NULL")
    )

    description: Mapped[str] = mapped_column(Text)
    description_markup_type: Mapped[str] = mapped_column(
        String(30),
        default="restructuredtext"
    )

    featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    calendar: Mapped["Calendar"] = relationship(back_populates="events")
    venue: Mapped[Optional["EventLocation"]] = relationship()
    categories: Mapped[list["EventCategory"]] = relationship(
        secondary="event_category_associations"
    )
```

### Migration from Django

1. **Field Mapping**:
   - Django `CharField` → SQLAlchemy `String`
   - Django `TextField` → SQLAlchemy `Text`
   - Django `BooleanField` → SQLAlchemy `Boolean`
   - Django `DateTimeField` → SQLAlchemy `DateTime(timezone=True)`
   - Django `ForeignKey` → SQLAlchemy `ForeignKey` + `relationship`

2. **Default Values**:
   - Django `default=timezone.now` → SQLAlchemy `server_default=func.now()`
   - Python defaults → `default=` parameter

3. **Indexes**:
   - Django `db_index=True` → SQLAlchemy `index=True`
   - Composite indexes → `__table_args__`

---

## API Design

### API Architecture

The application provides two API versions:

1. **API v1** (Legacy Compatibility): Tastypie-compatible endpoints
2. **API v2** (Modern): RESTful with full OpenAPI documentation

### API v2 Design Principles

1. **RESTful Resource Design**
2. **Consistent Response Format**
3. **Pagination Built-in**
4. **Rate Limiting**
5. **OpenAPI Documentation**
6. **Versioning via URL Path**

### Response Format

```python
# Success Response
{
    "data": [...],
    "meta": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "has_next": true,
        "has_previous": false
    }
}

# Error Response
{
    "detail": "Error message",
    "status_code": 400,
    "extra": {
        "field": ["Field-specific error"]
    }
}
```

### Example API Routes

```python
# api/v2/downloads.py
from litestar import Controller, get, post
from litestar.params import Parameter
from litestar.pagination import OffsetPagination

class DownloadAPIController(Controller):
    path = "/api/v2/downloads"
    tags = ["downloads"]

    @get("/releases")
    async def list_releases(
        self,
        service: ReleaseService,
        version: int | None = Parameter(
            query="version",
            description="Filter by Python version (1, 2, 3)"
        ),
        is_latest: bool | None = Parameter(
            query="is_latest",
            description="Show only latest releases"
        ),
        limit: int = 20,
        offset: int = 0,
    ) -> OffsetPagination[ReleaseRead]:
        """List Python releases with filtering."""
        releases = await service.list_releases(
            version=version,
            is_latest=is_latest,
            limit=limit,
            offset=offset
        )
        return OffsetPagination(
            items=releases,
            total=await service.count_releases(version, is_latest),
            limit=limit,
            offset=offset
        )

    @get("/releases/{release_slug:str}")
    async def get_release(
        self,
        release_slug: str,
        service: ReleaseService
    ) -> ReleaseRead:
        """Get a specific release by slug."""
        release = await service.get_by_slug(release_slug)
        if not release:
            raise NotFoundException("Release not found")
        return release

    @get("/releases/{release_slug:str}/files")
    async def list_release_files(
        self,
        release_slug: str,
        service: ReleaseService,
        os_slug: str | None = None
    ) -> list[ReleaseFileRead]:
        """List files for a release, optionally filtered by OS."""
        return await service.list_files(release_slug, os_slug)
```

### OpenAPI Configuration

```python
# config.py
from litestar.openapi import OpenAPIConfig, OpenAPIController
from litestar.openapi.spec import Contact, License

openapi_config = OpenAPIConfig(
    title="Python.org API",
    version="2.0.0",
    description="Official Python.org API for releases, events, jobs, and more",
    contact=Contact(
        name="Python Software Foundation",
        url="https://www.python.org",
        email="pydotorg-www@python.org"
    ),
    license=License(
        name="Apache 2.0",
        url="https://www.apache.org/licenses/LICENSE-2.0.html"
    ),
    use_handler_docstrings=True,
    tags=[
        {"name": "downloads", "description": "Python release downloads"},
        {"name": "events", "description": "Community events"},
        {"name": "jobs", "description": "Job board"},
        {"name": "users", "description": "User management"},
    ]
)
```

---

## Authentication & Authorization

### Authentication Strategy

**Multi-Method Authentication**:

1. **Session-Based** (Web UI): Traditional cookie sessions
2. **Token-Based** (API): Bearer tokens for API access
3. **OAuth** (Social): GitHub, Google, etc. via Allauth-equivalent

### Implementation Approach

```python
# core/auth/models.py
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class AuthToken(Base):
    """API authentication tokens."""
    __tablename__ = "auth_tokens"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship()

# core/auth/guards.py
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from sqlalchemy import select

async def session_auth_guard(
    connection: ASGIConnection,
    _: Any
) -> None:
    """Require authenticated session."""
    if not connection.user:
        raise NotAuthorizedException("Authentication required")

async def api_token_guard(
    connection: ASGIConnection,
    _: Any
) -> None:
    """Require valid API token."""
    auth_header = connection.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise NotAuthorizedException("Invalid authorization header")

    token = auth_header[7:]

    async with connection.app.state.db_session() as session:
        result = await session.execute(
            select(AuthToken).where(AuthToken.key == token)
        )
        auth_token = result.scalar_one_or_none()

        if not auth_token:
            raise NotAuthorizedException("Invalid token")

        connection.user = auth_token.user

# core/auth/middleware.py
from litestar.middleware import AbstractAuthenticationMiddleware
from litestar.connection import ASGIConnection

class SessionAuthMiddleware(AbstractAuthenticationMiddleware):
    """Load user from session."""

    async def authenticate_request(
        self,
        connection: ASGIConnection
    ) -> User | None:
        session_id = connection.cookies.get("session_id")

        if not session_id:
            return None

        # Load user from session store (Redis)
        user_id = await connection.app.state.session_store.get(session_id)

        if not user_id:
            return None

        async with connection.app.state.db_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
```

### Authorization Patterns

```python
# lib/guards/permissions.py
from enum import Enum
from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException

class Permission(str, Enum):
    JOB_MODERATE = "jobs.can_moderate_jobs"
    PAGE_EDIT = "pages.can_edit_pages"
    RELEASE_PUBLISH = "downloads.can_publish_releases"

async def requires_permission(
    permission: Permission,
    connection: ASGIConnection,
    _: Any
) -> None:
    """Check if user has specific permission."""
    user = connection.user

    if not user:
        raise PermissionDeniedException("Authentication required")

    if user.is_superuser:
        return

    # Check user permissions (implement based on needs)
    if not await user.has_permission(permission):
        raise PermissionDeniedException(
            f"Missing required permission: {permission}"
        )

# Usage in controller
from functools import partial

class JobController(Controller):
    @post("/jobs/{job_id:int}/approve")
    @requires_permission(Permission.JOB_MODERATE)
    async def approve_job(self, job_id: int) -> JobRead:
        ...
```

---

## Configuration Management

### Environment-Based Configuration

```python
# config.py
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Application
    site_name: str = "Python.org"
    site_description: str = "The official home of the Python Programming Language"
    secret_key: str = Field(..., min_length=32)

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pythondotorg"
    )
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # Cache
    cache_ttl: int = 3600

    # Session
    session_cookie_name: str = "pydotorg_session"
    session_lifetime: int = 86400 * 14  # 14 days

    # Email
    email_backend: str = "smtp"
    email_host: str = "localhost"
    email_port: int = 587
    email_use_tls: bool = True
    email_username: str = ""
    email_password: str = ""
    default_from_email: str = "noreply@python.org"

    # Background Tasks
    saq_queue_name: str = "pydotorg"

    # CDN
    fastly_api_key: str | None = None
    fastly_service_id: str | None = None

    # Static Files
    static_url: str = "/static/"
    media_url: str = "/media/"
    static_root: Path = Path("static-root")
    media_root: Path = Path("media")

    # Search
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: str | None = None

    # Jobs
    job_threshold_days: int = 90
    job_from_email: str = "jobs@python.org"

    # Events
    events_to_email: str = "events@python.org"

    # Sponsors
    sponsorship_notification_from_email: str = "sponsors@python.org"
    sponsorship_notification_to_email: str = "psf-sponsors@python.org"

    # Rate Limiting
    rate_limit_anonymous: str = "100/day"
    rate_limit_authenticated: str = "3000/day"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
```

### Environment Files

```bash
# .env.example
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-min-32-chars-long

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pythondotorg
REDIS_URL=redis://localhost:6379/0

EMAIL_HOST=smtp.sendgrid.net
EMAIL_USERNAME=apikey
EMAIL_PASSWORD=your-sendgrid-api-key

FASTLY_API_KEY=
FASTLY_SERVICE_ID=

MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=
```

---

## Background Tasks

### SAQ Integration

```python
# tasks/base.py
from typing import Any
from saq import Queue
from saq.worker import Worker
from redis.asyncio import Redis
from pydotorg.config import get_settings

settings = get_settings()

# Create Redis connection
redis = Redis.from_url(str(settings.redis_url))

# Create queue
queue = Queue(redis, name=settings.saq_queue_name)

# Define worker
worker = Worker(
    queue=queue,
    functions=[
        # Register all task functions here
    ],
    concurrency=10,
)

# tasks/downloads.py
from saq import Job
from pydotorg.domains.downloads.services import ReleaseService
from .base import queue

async def update_download_boxes(ctx: dict[str, Any]) -> None:
    """Update homepage and download page boxes."""
    async with get_db_session() as session:
        service = ReleaseService(session)
        await service.update_download_boxes()

async def purge_download_cache(ctx: dict[str, Any], release_id: int) -> None:
    """Purge Fastly cache for download pages."""
    async with get_db_session() as session:
        service = ReleaseService(session)
        await service.purge_cache(release_id)

# Schedule tasks
async def schedule_update_boxes():
    """Schedule periodic box updates."""
    await queue.enqueue(
        "update_download_boxes",
        scheduled=int(time.time()) + 3600  # 1 hour from now
    )

# tasks/events.py
async def import_calendar_events(ctx: dict[str, Any], calendar_id: int) -> None:
    """Import events from iCal feed."""
    async with get_db_session() as session:
        from pydotorg.domains.events.importer import ICSImporter

        result = await session.execute(
            select(Calendar).where(Calendar.id == calendar_id)
        )
        calendar = result.scalar_one()

        importer = ICSImporter(calendar, session)
        await importer.import_events()
```

### Task Scheduling

```python
# main.py - Application startup
from saq.cron import cron

@app.on_startup
async def start_task_worker():
    """Start background task worker."""
    # Schedule periodic tasks
    await queue.schedule(
        "update_download_boxes",
        cron="0 */6 * * *",  # Every 6 hours
    )

    await queue.schedule(
        "cleanup_expired_jobs",
        cron="0 0 * * *",  # Daily at midnight
    )
```

---

## Migration Strategy

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Set up project structure and core infrastructure

- [ ] Initialize project with uv
- [ ] Configure Litestar application
- [ ] Set up SQLAlchemy with async support
- [ ] Configure Alembic migrations
- [ ] Implement base models and mixins
- [ ] Set up testing framework
- [ ] Configure CI/CD pipeline

### Phase 2: Core Domains (Weeks 3-5)

**Goal**: Migrate essential domains

Priority Order:
1. **Users Domain** (authentication foundation)
2. **CMS Domain** (base mixins and patterns)
3. **Pages Domain** (core content)
4. **Downloads Domain** (critical functionality)

For each domain:
- [ ] Create SQLAlchemy models
- [ ] Write Alembic migrations
- [ ] Define Pydantic schemas
- [ ] Implement services layer
- [ ] Build controllers
- [ ] Write unit tests
- [ ] Create integration tests

### Phase 3: Feature Domains (Weeks 6-9)

**Goal**: Migrate remaining domains

- [ ] Events
- [ ] Jobs
- [ ] Community
- [ ] Sponsors
- [ ] Blogs
- [ ] Boxes
- [ ] Banners
- [ ] Success Stories
- [ ] Nominations
- [ ] Minutes
- [ ] Work Groups
- [ ] Companies
- [ ] Code Samples
- [ ] Mailing

### Phase 4: Templates & Frontend (Weeks 10-11)

**Goal**: Port Django templates to Jinja2

- [ ] Convert base templates
- [ ] Implement template context processors
- [ ] Port domain-specific templates
- [ ] Integrate static asset pipeline
- [ ] Test responsive layouts
- [ ] Accessibility audit

### Phase 5: Background Tasks & Integration (Week 12)

**Goal**: Implement async tasks and integrations

- [ ] Set up SAQ task queue
- [ ] Port Celery tasks to SAQ
- [ ] Integrate Meilisearch
- [ ] Configure Fastly cache purging
- [ ] Email delivery setup
- [ ] OAuth provider integration

### Phase 6: Testing & Optimization (Weeks 13-14)

**Goal**: Ensure quality and performance

- [ ] End-to-end testing
- [ ] Performance benchmarking
- [ ] Load testing
- [ ] Security audit
- [ ] Database query optimization
- [ ] Cache strategy tuning

### Phase 7: Deployment & Cutover (Weeks 15-16)

**Goal**: Production deployment

- [ ] Staging environment deployment
- [ ] Data migration from Django
- [ ] Smoke testing in staging
- [ ] Performance monitoring setup
- [ ] Production deployment
- [ ] DNS cutover
- [ ] Post-deployment monitoring

### Data Migration Script

```python
# scripts/import_django_data.py
"""
Import data from Django database to Litestar database.

Usage:
    uv run python scripts/import_django_data.py --django-db postgresql://... --litestar-db postgresql://...
"""
import asyncio
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async def migrate_users(django_conn, litestar_session):
    """Migrate users from Django to Litestar."""
    # Read from Django
    django_users = django_conn.execute(
        "SELECT * FROM auth_user"
    ).fetchall()

    # Transform and insert into Litestar
    for du in django_users:
        user = User(
            id=du.id,
            username=du.username,
            email=du.email,
            password_hash=du.password,  # Keep Django password hashes
            first_name=du.first_name,
            last_name=du.last_name,
            is_active=du.is_active,
            is_staff=du.is_staff,
            is_superuser=du.is_superuser,
            created=du.date_joined,
        )
        litestar_session.add(user)

    await litestar_session.commit()

async def main():
    # Connect to both databases
    django_engine = create_engine("postgresql://...")
    litestar_engine = create_async_engine("postgresql+asyncpg://...")

    with django_engine.connect() as django_conn:
        async with AsyncSession(litestar_engine) as session:
            await migrate_users(django_conn, session)
            await migrate_pages(django_conn, session)
            await migrate_releases(django_conn, session)
            # ... continue for all domains

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Performance Considerations

### Database Optimization

1. **Connection Pooling**:
   ```python
   engine = create_async_engine(
       settings.database_url,
       pool_size=20,
       max_overflow=10,
       pool_pre_ping=True,
       echo=settings.database_echo
   )
   ```

2. **Query Optimization**:
   - Use `selectinload()` for relationships
   - Implement pagination for large result sets
   - Add indexes for common query patterns
   - Use `defer()` for large text fields

3. **Caching Strategy**:
   ```python
   # core/cache/decorator.py
   from functools import wraps
   from typing import Callable

   def cache_result(ttl: int = 3600):
       def decorator(func: Callable):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               cache_key = f"{func.__name__}:{args}:{kwargs}"

               # Try cache first
               cached = await redis.get(cache_key)
               if cached:
                   return json.loads(cached)

               # Execute function
               result = await func(*args, **kwargs)

               # Store in cache
               await redis.setex(
                   cache_key,
                   ttl,
                   json.dumps(result, default=str)
               )

               return result
           return wrapper
       return decorator
   ```

### Response Optimization

1. **Compression**: Enable gzip compression
2. **ETags**: Implement ETags for static content
3. **CDN**: Leverage Fastly for static assets and page caching

### Async Best Practices

1. **Non-blocking I/O**: Use `asyncio` for all I/O operations
2. **Task Concurrency**: Use `asyncio.gather()` for parallel tasks
3. **Connection Limits**: Configure appropriate pool sizes

---

## Security Architecture

### Security Principles

1. **Defense in Depth**
2. **Least Privilege**
3. **Secure by Default**
4. **Input Validation**
5. **Output Encoding**

### Implementation

```python
# core/security/middleware.py
from litestar.middleware import DefineMiddleware
from litestar.security.session_auth import SessionAuth

security_config = SessionAuth(
    secret=settings.secret_key,
    cookie_name=settings.session_cookie_name,
    cookie_httponly=True,
    cookie_secure=settings.is_production,
    cookie_samesite="lax",
)

# CORS configuration
cors_config = CORSConfig(
    allow_origins=["https://www.python.org"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

# CSP headers
csp_middleware = DefineMiddleware(
    CSPMiddleware,
    policy={
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:"],
    }
)
```

### Input Validation

```python
# All input validated via Pydantic
class JobCreate(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    url: HttpUrl
    description: str = Field(..., min_length=50)

    @field_validator('description')
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        """Strip dangerous HTML tags."""
        return bleach.clean(
            v,
            tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li'],
            strip=True
        )
```

### Rate Limiting

```python
# core/middleware/rate_limit.py
from litestar.middleware.rate_limit import RateLimitConfig

rate_limit_config = RateLimitConfig(
    rate_limit=("100", "minute"),
    exclude=["/health", "/static/*"],
)
```

---

## Appendices

### A. Technology Decision Records

#### ADR-001: Litestar over FastAPI

**Decision**: Use Litestar 2.x as the web framework

**Rationale**:
- Superior dependency injection system
- Better integration with SQLAlchemy
- Advanced Alchemy provides excellent database utilities
- Strong type safety enforcement
- Excellent OpenAPI documentation
- Active development and community

**Alternatives Considered**:
- FastAPI: Good but less integrated ecosystem
- Starlette: Too low-level, more boilerplate needed

#### ADR-002: SAQ over Celery

**Decision**: Use SAQ for background tasks

**Rationale**:
- Native async support
- Simpler configuration
- Better performance for async tasks
- Redis-native (already in stack)
- Lighter weight

**Trade-offs**:
- Less mature than Celery
- Smaller community
- Fewer integrations

#### ADR-003: Meilisearch over Elasticsearch

**Decision**: Use Meilisearch for search functionality

**Rationale**:
- Simpler deployment
- Better out-of-box relevance
- Lower resource usage
- Easier to maintain
- Good Python client

**Trade-offs**:
- Less flexible than Elasticsearch
- Smaller feature set

### B. File Templates

See `/docs/architecture/templates/` for:
- Model template
- Controller template
- Service template
- Schema template
- Test template

### C. Development Guidelines

See `/docs/architecture/DEVELOPMENT.md` for:
- Code style guide
- Testing standards
- Git workflow
- PR review process

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-25 | ARCHITECT Agent | Initial architecture document |

---

## References

- [Litestar Documentation](https://docs.litestar.dev/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Advanced Alchemy](https://docs.advanced-alchemy.litestar.dev/)
- [Pydantic V2](https://docs.pydantic.dev/)
- [SAQ Documentation](https://saq-py.readthedocs.io/)
- [Django pythondotorg Repository](https://github.com/python/pythondotorg)

---

**Document Path**: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/architecture/ARCHITECTURE.md`

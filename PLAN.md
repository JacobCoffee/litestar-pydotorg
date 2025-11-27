# Python.org Litestar Rebuild - Comprehensive Requirements & Task Assignment

## Project Overview

**Objective**: Rebuild Python.org from Django to Litestar with modern architecture
**Source**: `/Users/coffee/git/internal/python/pythondotorg` (Django)
**Target**: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg` (Litestar)

### Technology Stack

| Component | Old (Django) | New (Litestar) |
|-----------|-------------|----------------|
| Framework | Django 4.x | Litestar 2.14+ |
| ORM | Django ORM | SQLAlchemy 2.0 + Advanced Alchemy |
| Templates | Django Templates + Boxes | Jinja2 Templates |
| Server | Gunicorn/uWSGI | **Granian** |
| Styling | Bootstrap/Custom CSS | **TailwindCSS + DaisyUI** |
| Database | PostgreSQL | PostgreSQL (asyncpg) |
| Cache | Redis | Redis |
| Task Queue | Celery | SAQ |
| Search | Elasticsearch | Meilisearch |
| Build | setuptools | **uv_build** |

---

## Available Agents

| Agent | Specialty | Best For |
|-------|-----------|----------|
| `software-architect-advanced` | System design, architecture, patterns | High-level design, domain modeling |
| `software-architect` | Architecture decisions, technical specs | Module structure, API design |
| `python-backend-architect` | Python backend systems, optimization | Service layer, database design |
| `python-backend-engineer` | Python development, APIs, databases | Model/repo/service implementation |
| `ui-engineer` | Frontend code, UI components | Jinja templates, Tailwind/DaisyUI |
| `documentation-expert` | Sphinx docs, Diataxis framework | API docs, user guides |
| `Python Testing Expert` | Testing, QA, test automation | Unit/integration/e2e tests |
| `ui-comprehensive-tester` | UI testing, user flow validation | Template testing, accessibility |
| `ultrathink-debugger` | Deep debugging, root cause analysis | Complex bugs, integration issues |
| `github-git-expert` | Git operations, PR management | Branch management, releases |

---

## Phase 1: Foundation (COMPLETED ITEMS)

- [x] Initialize project with uv
- [x] Configure Litestar application
- [x] Set up SQLAlchemy with async support
- [x] Implement base models and mixins
- [x] Set up testing framework
- [x] Migrate to uv_build backend
- [x] Switch to Granian server

---

## Phase 2: Core Infrastructure

### Task 2.1: Database Layer Completion
**Agent**: `python-backend-architect`
**Priority**: CRITICAL
**Status**: ✅ COMPLETE (2025-11-26)

**Design Guide**:
- Use Advanced Alchemy's `SQLAlchemyAsyncRepository` pattern
- All models inherit from `base.UUIDAuditBase` for UUID PKs + timestamps
- Use `Mapped[]` type annotations for all fields
- Implement custom repositories for complex queries
- Follow Service-Repository-Model architecture

**Tasks**:
- [x] Complete Alembic migration setup with proper env.py
- [x] Create initial migration for existing 4 domains (users, pages, downloads, sponsors)
- [x] Create migration for all remaining domains (002_add_remaining_models.py)
- [x] Implement database seeding for development (db/seed.py - 1006 lines)
- [x] Add connection pooling configuration (pool_size=20, max_overflow=10)
- [x] Implement health check for database connectivity (/health endpoint)

**Files to Create/Modify**:
```
src/pydotorg/
├── db/
│   ├── __init__.py
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   └── seed.py
```

---

### Task 2.2: Authentication & Authorization System
**Agent**: `python-backend-architect`
**Priority**: CRITICAL
**Status**: ✅ COMPLETE (2025-11-27)

**Design Guide**:
```python
# Authentication flow using Litestar's AbstractAuthenticationMiddleware
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult

class JWTAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        # Extract JWT from header/cookie
        # Validate token
        # Return AuthenticationResult(user=user, auth=token)
```

**Tasks**:
- [x] Implement JWT authentication middleware (`core/auth/middleware.py`)
- [x] Create session-based authentication (fallback) (`core/auth/session.py`)
- [x] Implement password hashing service (bcrypt) (`domains/users/security.py`)
- [x] Create user registration flow (`domains/users/auth_controller.py`)
- [x] Implement email verification (JWT verification tokens)
- [x] Add OAuth2 social login (GitHub, Google) (`core/auth/oauth.py`)
- [x] Create role-based permission guards (`core/auth/guards.py`)
- [x] Implement CSRF protection for forms (`core/security/csrf.py`)

**Implementation Details** (2025-11-27):
- **JWT Service**: `JWTService` class with access/refresh/verification token support
  - Access tokens: configurable expiration (default 7 days)
  - Refresh tokens: 30 days expiration
  - Verification tokens: configurable (default 24 hours)
- **Middleware**: `JWTAuthMiddleware` + `UserPopulationMiddleware` for template context
- **Session Auth**: Redis-backed session service with configurable TTL
- **CSRF Config**: Litestar built-in CSRFConfig with exclusions for API routes
  - Excluded: `/api/auth/*`, `/api/v1/*`, `/health`, `/static/*`
- **Guards**: `require_authenticated`, `require_staff`, `require_superuser`, `require_any_admin_access`

**Tests Added** (38 tests):
- `tests/core/test_jwt.py` - 26 tests for JWTService
- `tests/core/test_csrf.py` - 12 tests for CSRF configuration

**Files Created/Modified**:
```
src/pydotorg/
├── core/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── middleware.py      # JWTAuthMiddleware + UserPopulationMiddleware
│   │   ├── guards.py          # Permission guards
│   │   ├── jwt.py             # JWT utilities (JWTService)
│   │   ├── password.py        # Password validation
│   │   ├── session.py         # Redis session service
│   │   ├── schemas.py         # Auth DTOs
│   │   └── oauth.py           # OAuth2 providers (GitHub, Google)
│   └── security/
│       ├── __init__.py
│       └── csrf.py            # CSRFConfig factory
├── domains/users/
│   ├── security.py            # Password hashing (bcrypt)
│   └── auth_controller.py     # Auth endpoints (JWT + session)
```

---

### Task 2.3: Configuration & Environment
**Agent**: `python-backend-engineer`
**Priority**: HIGH

**Design Guide**:
- Use pydantic-settings for all configuration
- Environment-specific configs (dev/staging/prod)
- Secrets management via environment variables
- Feature flags support

**Tasks**:
- [ ] Expand config.py with all necessary settings
- [ ] Add environment-specific configuration loading
- [ ] Implement feature flags system
- [ ] Add logging configuration (structlog)
- [ ] Create settings validation on startup

---

## Phase 3: Domain Implementation

### Domain Migration Order (by dependency)

```
1. users (no dependencies)                    ✅ DONE (models, repos, services, controllers)
2. boxes → SKIPPED (using pure Jinja2)        ✅ SKIPPED
3. pages (depends on: users)                  ✅ DONE (models, repos, services, controllers)
4. downloads (depends on: users, pages)       ✅ DONE (models, repos, services, controllers)
5. blogs (depends on: users)                  ✅ DONE (models, repos, services, controllers)
6. jobs (depends on: users, companies)        ✅ DONE (models, repos, services, controllers)
7. companies → merged into sponsors           ✅ MERGED
8. events (depends on: users)                 ✅ DONE (models, repos, services, controllers)
9. sponsors (depends on: users)               ✅ DONE (models, repos, services, controllers)
10. community (depends on: users)             ✅ DONE (models, repos, services, controllers)
11. successstories (depends on: users)        ✅ DONE (models, repos, services, controllers)
12. nominations (depends on: users)           ✅ DONE (models, repos, services, controllers)
13. codesamples (depends on: users)           ✅ DONE (models, repos, services, controllers)
14. minutes (depends on: users)               ✅ DONE (models, repos, services, controllers)
15. banners (depends on: users)               ✅ DONE (models, repos, services, controllers)
16. mailing (depends on: users)               ⏳ PENDING
17. work_groups (depends on: users)           ✅ DONE (models, repos, services, controllers)
```

---

### Task 3.1: Users Domain (Complete)
**Agent**: `python-backend-engineer`
**Priority**: CRITICAL
**Status**: Models exist, need services/controllers

**Django Models** (source of truth):
```python
# From pythondotorg/users/models.py
class User:
    username, email, password (AbstractUser)
    bio, public_email, search_visibility, email_privacy

class Membership:
    user (FK), membership_type, created, voted, psf_announcements

class UserGroup:
    name, location, url, location_coords, start_date, type
```

**Tasks**:
- [ ] Create UserRepository with custom queries
- [ ] Create UserService with business logic
- [ ] Create MembershipRepository/Service
- [ ] Create UserGroupRepository/Service
- [ ] Implement Pydantic schemas (UserCreate, UserUpdate, UserRead)
- [ ] Create UserController with CRUD endpoints
- [ ] Implement user profile endpoints
- [ ] Add user search functionality

**File Structure**:
```
src/pydotorg/domains/users/
├── __init__.py
├── models.py          # EXISTS
├── schemas.py         # CREATE: Pydantic DTOs
├── repositories.py    # CREATE: Data access
├── services.py        # CREATE: Business logic
├── controllers.py     # CREATE: HTTP handlers
└── dependencies.py    # CREATE: DI providers
```

---

### Task 3.2: Boxes Domain → SKIPPED (Pure Jinja Approach)
**Status**: ✅ SKIPPED - Using pure Jinja2 templates instead
**Decision Date**: 2025-11-26

**Rationale**:
Django Boxes were database-driven content widgets. For this rewrite, we're using:
- **Pure Jinja2 templates** for all content rendering
- **Jinja2 macros** (`templates/macros/`) for reusable components
- **Jinja2 partials** (`templates/partials/`) for shared sections
- **Domain models** (Page, Blog, etc.) for database-driven content

This eliminates the need for a separate Boxes/ContentBlock domain. If CMS-editable
content slots are needed later, we can either:
1. Add a simple `ContentSnippet` model
2. Integrate with Strapi CMS via `litestar-strapi` plugin

**What Exists Now**:
```
src/pydotorg/templates/
├── macros/
│   ├── forms.html.jinja2      ✅ Form components
│   ├── cards.html.jinja2      ✅ Card components
│   └── buttons.html.jinja2    ✅ Button components
├── partials/
│   ├── navbar.html.jinja2     ✅ Navigation
│   └── footer.html.jinja2     ✅ Footer
```

---

### Task 3.3: Pages Domain
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: Models exist, need completion

**Django Pages Model**:
```python
class Page(ContentManageable):
    title, keywords, description, path, content, content_markup_type
    is_published, template_name

class Image:
    page (FK), image, caption, creator

class DocumentFile:
    page (FK), document, creator
```

**Tasks**:
- [ ] Complete Page model with all fields
- [ ] Implement PageRepository with path-based lookups
- [ ] Create PageService with publishing logic
- [ ] Create ImageRepository/Service
- [ ] Create DocumentFileRepository/Service
- [ ] Implement page tree/hierarchy
- [ ] Create page rendering controller
- [ ] Add page caching (Redis)

---

### Task 3.4: Downloads Domain
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: Models exist, need services

**Django Downloads Models**:
```python
class OS:
    name, slug

class Release:
    name, slug, version, is_published, release_date
    release_page, release_notes_url, show_on_download_page
    pre_release, content, content_markup_type

class ReleaseFile:
    os (FK), release (FK), name, slug, description
    is_source, url, gpg_signature_file, md5_digest, filesize
    download_button_text
```

**Tasks**:
- [ ] Complete Release model with version comparison
- [ ] Implement ReleaseRepository with version queries
- [ ] Create ReleaseService with publishing logic
- [ ] Create ReleaseFileRepository/Service
- [ ] Implement download page logic
- [ ] Add download statistics tracking
- [ ] Create release API endpoints
- [ ] Implement GPG signature verification

---

### Task 3.5: Blogs Domain
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM

**Django Blogs Models**:
```python
class BlogEntry:
    title, summary, content, pub_date, url
    feed (FK)

class Feed:
    name, website_url, feed_url

class FeedAggregate:
    name, slug, description, feeds (M2M)

class RelatedBlog:
    blog_name, blog_website
```

**Tasks**:
- [ ] Create BlogEntry model
- [ ] Create Feed model with RSS parsing
- [ ] Implement feed aggregation service
- [ ] Create blog listing controller
- [ ] Implement feed refresh background task (SAQ)
- [ ] Add blog search functionality

---

### Task 3.6: Jobs Domain
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM

**Django Jobs Models**:
```python
class JobType:
    name, slug

class JobCategory:
    name, slug

class Job:
    creator (FK), company (FK), job_title, city, region, country
    description, requirements, contact, url, status
    telecommuting, agencies, created, updated, expires
    email, job_types (M2M)

class JobReviewComment:
    job (FK), comment, creator, created
```

**Tasks**:
- [ ] Create JobType, JobCategory models
- [ ] Create Job model with full workflow states
- [ ] Implement job approval workflow
- [ ] Create job search with filters
- [ ] Implement job expiration logic (SAQ task)
- [ ] Create job submission form
- [ ] Add email notifications

---

### Task 3.7: Events Domain
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM

**Django Events Models**:
```python
class Calendar:
    creator (FK), slug, name

class EventCategory:
    name, slug, calendar (FK)

class EventLocation:
    name, address, url

class Event:
    creator (FK), calendar (FK), title, description
    venue (FK to EventLocation), categories (M2M)
    featured, recurrence

class OccurringRule:
    event (FK), dt_start, dt_end

class RecurringRule:
    event (FK), begin, finish
    year, month, day, week, hour, minute, second

class Alarm:
    event (FK), trigger, description, action
```

**Tasks**:
- [ ] Create all event models
- [ ] Implement recurrence rule engine (dateutil.rrule)
- [ ] Create iCalendar export
- [ ] Implement event search with date filtering
- [ ] Create event submission workflow
- [ ] Add calendar feed (RSS/Atom)

---

### Task 3.8: Sponsors Domain
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: Basic models exist, complex system

**Django Sponsors Models** (complex):
```python
class Sponsor:
    name, description, primary_phone, mailing_address_line_1/2
    city, state, postal_code, country, country_of_incorporation
    state_of_incorporation, landing_page_url, twitter_handle
    linked_in_page_url, web_logo, print_logo, primary_contact (FK)

class SponsorshipProgram:
    name, slug, description

class SponsorshipPackage:
    name, slug, sponsorship_amount, year

class SponsorshipBenefit:
    program (FK), name, description, type, capacity
    soft_capacity, conflicts (M2M)

class Sponsorship:
    sponsor (FK), package (FK), status, start_date, end_date
    applied_on, approved_on, rejected_on, finalized_on

class Contract:
    sponsorship (FK), signed_date, document

class BenefitFeature:
    benefit (FK), name, value

class SponsorBenefit:
    sponsorship (FK), benefit (FK), status
```

**Tasks**:
- [ ] Complete all sponsor models
- [ ] Implement sponsorship workflow (apply -> approve -> finalize)
- [ ] Create benefit assignment logic
- [ ] Implement contract management
- [ ] Create sponsor listing page
- [ ] Add sponsor logo management
- [ ] Implement annual sponsorship renewal

---

### Task 3.9-3.17: Remaining Domains
**Agent**: `python-backend-engineer`
**Priority**: NORMAL

| Domain | Models | Complexity |
|--------|--------|------------|
| community | Post, Photo, Video, Link | Medium |
| companies | Company | Low |
| successstories | StoryCategory, Story | Low |
| nominations | Election, Nominee, Nomination | Medium |
| codesamples | CodeSample | Low |
| minutes | Minutes | Low |
| banners | Banner | Low |
| mailing | BaseEmailTemplate | Low |
| work_groups | WorkGroup | Low |

---

## Phase 4: Frontend (Jinja2 + TailwindCSS + DaisyUI)

### Task 4.1: Base Template System
**Agent**: `ui-engineer`
**Priority**: CRITICAL

**Design Guide**:
```html
<!-- Base template structure -->
<!DOCTYPE html>
<html data-theme="light" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Python.org{% endblock %}</title>
  <link href="/static/css/tailwind.css" rel="stylesheet">
  {% block head %}{% endblock %}
</head>
<body class="min-h-screen bg-base-100">
  {% include "partials/navbar.html.jinja2" %}

  <main class="container mx-auto px-4 py-8">
    {% block content %}{% endblock %}
  </main>

  {% include "partials/footer.html.jinja2" %}

  {% block scripts %}{% endblock %}
</body>
</html>
```

**Tasks**:
- [ ] Create base.html.jinja2 template
- [ ] Create navbar component (DaisyUI navbar)
- [ ] Create footer component
- [ ] Create sidebar component
- [ ] Set up Tailwind CSS build pipeline
- [ ] Configure DaisyUI theme (Python-branded colors)
- [ ] Create responsive layout system
- [ ] Implement dark mode toggle

**Files to Create**:
```
src/pydotorg/templates/
├── base.html.jinja2
├── partials/
│   ├── navbar.html.jinja2
│   ├── footer.html.jinja2
│   ├── sidebar.html.jinja2
│   └── breadcrumbs.html.jinja2
├── macros/
│   ├── forms.html.jinja2
│   ├── cards.html.jinja2
│   ├── buttons.html.jinja2
│   └── alerts.html.jinja2
static/
├── css/
│   └── tailwind.css
├── js/
│   └── main.js
tailwind.config.js
postcss.config.js
```

---

### Task 4.2: Component Library (DaisyUI)
**Agent**: `ui-engineer`
**Priority**: HIGH

**DaisyUI Components to Implement**:
```
Buttons: btn, btn-primary, btn-secondary, btn-accent
Cards: card, card-body, card-title, card-actions
Navigation: navbar, menu, breadcrumbs, tabs
Forms: input, select, textarea, checkbox, radio, toggle
Feedback: alert, toast, badge, progress
Layout: hero, drawer, modal, collapse
Data Display: table, stat, countdown, carousel
```

**Tasks**:
- [ ] Create button component macros
- [ ] Create card component macros
- [ ] Create form component macros (with HTMX support)
- [ ] Create table component macros
- [ ] Create modal component macros
- [ ] Create alert/toast component macros
- [ ] Create pagination component
- [ ] Create search component

---

### Task 4.3: Page Templates
**Agent**: `ui-engineer`
**Priority**: HIGH

**Templates Needed**:
```
Homepage:
├── index.html.jinja2 (hero, news, events, sponsors)

Downloads:
├── downloads/
│   ├── index.html.jinja2 (download buttons)
│   ├── release.html.jinja2 (release details)
│   └── files.html.jinja2 (file listing)

Documentation:
├── docs/
│   ├── index.html.jinja2
│   └── page.html.jinja2

Community:
├── community/
│   ├── index.html.jinja2
│   └── events.html.jinja2

Jobs:
├── jobs/
│   ├── index.html.jinja2 (job listing)
│   ├── detail.html.jinja2 (job detail)
│   └── submit.html.jinja2 (submission form)

Auth:
├── auth/
│   ├── login.html.jinja2
│   ├── register.html.jinja2
│   └── profile.html.jinja2

Admin:
├── admin/
│   └── ... (content management)
```

**Tasks**:
- [ ] Create homepage template with hero section
- [ ] Create downloads page with version selector
- [ ] Create documentation browser template
- [ ] Create community/events templates
- [ ] Create job board templates
- [ ] Create auth flow templates
- [ ] Create admin dashboard templates

---

### Task 4.4: Frontend Build Pipeline
**Agent**: `ui-engineer`
**Priority**: HIGH

**Tasks**:
- [ ] Set up Node.js/Bun for frontend build
- [ ] Configure Tailwind CSS with Python.org color palette
- [ ] Configure DaisyUI themes
- [ ] Set up PostCSS pipeline
- [ ] Create Makefile targets for frontend build
- [ ] Implement CSS purging for production
- [ ] Add source maps for development

**tailwind.config.js**:
```javascript
module.exports = {
  content: ["./src/pydotorg/templates/**/*.jinja2"],
  theme: {
    extend: {
      colors: {
        python: {
          blue: '#3776AB',
          yellow: '#FFD43B',
        }
      }
    }
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        python: {
          "primary": "#3776AB",
          "secondary": "#FFD43B",
          "accent": "#646464",
          "neutral": "#1D232A",
          "base-100": "#FFFFFF",
        }
      },
      "dark"
    ]
  }
}
```

---

## Phase 5: API Layer

### Task 5.1: REST API Endpoints
**Agent**: `python-backend-architect`
**Priority**: HIGH

**Design Guide**:
```python
from litestar import Controller, get, post, put, delete
from litestar.di import Provide

class UserController(Controller):
    path = "/api/v1/users"
    dependencies = {"service": Provide(provide_user_service)}

    @get("/")
    async def list_users(self, service: UserService) -> list[UserRead]:
        return await service.list()

    @get("/{user_id:uuid}")
    async def get_user(self, user_id: UUID, service: UserService) -> UserRead:
        return await service.get(user_id)

    @post("/")
    async def create_user(self, data: UserCreate, service: UserService) -> UserRead:
        return await service.create(data)
```

**API Structure**:
```
/api/v1/
├── users/
├── pages/
├── downloads/
│   ├── releases/
│   └── files/
├── jobs/
├── events/
├── sponsors/
├── blogs/
└── community/
```

**Tasks**:
- [ ] Implement User API endpoints
- [ ] Implement Pages API endpoints
- [ ] Implement Downloads API endpoints
- [ ] Implement Jobs API endpoints
- [ ] Implement Events API endpoints
- [ ] Implement Sponsors API endpoints
- [ ] Add OpenAPI documentation
- [ ] Implement API versioning
- [ ] Add rate limiting
- [ ] Add API authentication (API keys)

---

### Task 5.2: GraphQL API (Optional)
**Agent**: `python-backend-architect`
**Priority**: LOW

**Tasks**:
- [ ] Evaluate Strawberry GraphQL integration
- [ ] Create GraphQL schema
- [ ] Implement resolvers
- [ ] Add GraphQL playground

---

## Phase 6: Background Tasks & Integrations

### Task 6.1: SAQ Task Queue
**Agent**: `python-backend-engineer`
**Priority**: HIGH

**Tasks**:
- [ ] Configure SAQ worker
- [ ] Implement feed aggregation task (blogs)
- [ ] Implement job expiration task
- [ ] Implement email sending task
- [ ] Implement cache warming task
- [ ] Implement search indexing task
- [ ] Add task monitoring

**Files to Create**:
```
src/pydotorg/tasks/
├── __init__.py
├── worker.py          # SAQ configuration
├── feeds.py           # Blog feed tasks
├── jobs.py            # Job-related tasks
├── email.py           # Email tasks
├── cache.py           # Cache tasks
└── search.py          # Search indexing
```

---

### Task 6.2: Email System
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM

**Tasks**:
- [ ] Configure SMTP settings
- [ ] Create email templates (Jinja2)
- [ ] Implement email service
- [ ] Add email verification flow
- [ ] Add password reset flow
- [ ] Implement notification emails

---

### Task 6.3: Search (Meilisearch)
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM

**Tasks**:
- [ ] Set up Meilisearch client
- [ ] Create search indexes (pages, jobs, events, downloads)
- [ ] Implement search service
- [ ] Add search API endpoints
- [ ] Implement search UI
- [ ] Add faceted search

---

### Task 6.4: CDN Integration (Fastly)
**Agent**: `python-backend-engineer`
**Priority**: LOW

**Tasks**:
- [ ] Implement Fastly client
- [ ] Add cache purging on content update
- [ ] Configure surrogate keys
- [ ] Add CDN health monitoring

---

## Phase 7: Admin Interface
**Status**: ✅ COMPLETE (2025-11-26)
**Agent**: `python-backend-engineer`

### Completed Work

**Admin Infrastructure**:
- [x] SQLAdmin integration via `sqladmin-litestar-plugin`
- [x] 22 ModelViews for all domains (users, pages, downloads, jobs, events, etc.)
- [x] Custom AdminDashboardController with stats, pending moderation, recent activity
- [x] Admin guards (`require_staff`, `require_superuser`, `require_any_admin_access`)
- [x] Exception handlers for 401 (redirect to login) and 403 (access denied template)

**Admin Templates**:
- [x] `admin/base.html.jinja2` - Admin layout with sidebar navigation
- [x] `admin/dashboard.html.jinja2` - Dashboard with stats cards and activity feed
- [x] `admin/users.html.jinja2` - User management table
- [x] `admin/jobs.html.jinja2` - Job moderation queue
- [x] `errors/403.html.jinja2` - Access denied page

**Auth Flow Improvements (2025-11-26)**:
- [x] Flash messages integration with `FlashPlugin` + `CookieBackendConfig`
- [x] Native JavaScript fetch for all auth forms (login, register, forgot-password, reset-password)
- [x] Fixed SQLAlchemy greenlet error (capture user.id before commit)
- [x] Fixed form GET submission (method="POST" + action="javascript:void(0)")
- [x] Client-side password validation and error display

**Unit Tests**:
- [x] 28 tests for admin guards and config (`tests/unit/domains/admin/`)

---

## Phase 8: Testing
**Status**: ✅ COMPLETE (2025-11-27)

### Testing Infrastructure Added

**New Make Targets** (Updated 2025-11-27):
```bash
make test                # Run unit tests only (fast, no external deps) - ~5s
make test-fast           # Run unit tests in parallel - ~3s
make test-unit           # Alias for 'make test'
make test-integration    # Run integration tests (requires: make infra-up) - ~40s
make test-e2e            # Run E2E Playwright tests (requires: make serve)
make test-all            # Run all tests (unit + integration, skips E2E if no server)
make test-full           # Run all tests including E2E (requires server running)
make test-cov            # Run all tests with coverage
make test-watch          # Run unit tests in watch mode
make playwright-install  # Install Playwright browsers
```

**Test Suite Fixes** (2025-11-27):
- [x] Fixed E2E tests hanging - added server availability check, auto-skip when no server
- [x] Fixed Litestar sync callable warnings - added `sync_to_thread=False` to test handlers
- [x] Updated `make test` to run unit tests only (fast CI)

### Task 8.1: Unit Tests
**Agent**: `Python Testing Expert`
**Status**: ✅ COMPLETE (2025-11-26)

**Test Coverage**: 191 domain unit tests created

**Completed**:
- [x] Create test fixtures with polyfactory
- [x] Write admin domain tests (28 tests)
- [x] Write auth endpoint tests (13 tests)
- [x] Write User domain tests (46 tests: User, Membership, UserGroup)
- [x] Write Pages domain tests (9 tests)
- [x] Write Downloads domain tests (19 tests)
- [x] Write Jobs domain tests (15 tests)
- [x] Write Events domain tests (15 tests)
- [x] Write Sponsors domain tests (20 tests)
- [x] Write Blogs domain tests (12 tests)
- [x] Write Community domain tests (11 tests)

**Files Created**:
```
tests/unit/domains/
├── users/ (test_user_models.py, test_membership_models.py, test_usergroup_models.py)
├── pages/test_page_models.py
├── downloads/test_download_models.py
├── jobs/test_job_models.py
├── events/test_event_models.py
├── sponsors/test_sponsor_models.py
├── blogs/test_blog_models.py
└── community/test_community_models.py
```

---

### Task 8.2: Integration Tests
**Agent**: `Python Testing Expert`
**Status**: ✅ COMPLETE (2025-11-26)

**Test Coverage**: 40 integration tests created

**Completed**:
- [x] Set up test database (PostgreSQL via pytest-databases)
- [x] Write API endpoint tests (auth endpoints - 13 tests)
- [x] Test session_login with actual database user (16 tests)
- [x] Test session refresh and TTL management
- [x] Test auth middleware exception handlers (24 tests)
- [x] Test authorization guards (authenticated, staff, admin)
- [x] Test concurrent session management
- [x] Test Redis failure handling

**Files Created**:
```
tests/integration/
├── test_session_auth.py (16 tests)
└── test_auth_middleware.py (24 tests)
```

---

### Task 8.3: E2E Tests
**Agent**: `ui-comprehensive-tester`
**Status**: ✅ COMPLETE (2025-11-26)

**Test Coverage**: 38 Playwright E2E tests created

**Completed**:
- [x] Set up Playwright with pytest-playwright
- [x] **Auth form tests** (all 4 forms):
  - [x] Login form JSON submission, errors, redirects
  - [x] Register form validation, password strength, submission
  - [x] Forgot password form submission
  - [x] Reset password form submission
- [x] Form validation tests (required fields, password matching)
- [x] Loading state tests (spinners, button states)
- [x] Accessibility tests (labels, ARIA attributes)

**Files Created**:
```
tests/e2e/
├── conftest.py (Playwright fixtures)
└── test_auth_forms.py (38 tests)
```

**Dependencies Added** (pyproject.toml):
- playwright>=1.48.0
- pytest-playwright>=0.6.0

---

## Phase 9: Documentation

### Task 9.1: API Documentation
**Agent**: `documentation-expert`
**Priority**: HIGH

**Tasks**:
- [ ] Configure OpenAPI/Swagger UI
- [ ] Write API usage guides
- [ ] Create API examples
- [ ] Document authentication
- [ ] Generate SDK documentation

---

### Task 9.2: Developer Documentation
**Agent**: `documentation-expert`
**Priority**: MEDIUM

**Tasks**:
- [ ] Update ARCHITECTURE.md
- [ ] Create domain model documentation
- [ ] Write deployment guide
- [ ] Create contributing guide
- [ ] Write troubleshooting guide

---

## Phase 10: Admin Sub-Pages & Integration
**Status**: ✅ COMPLETE (2025-11-26)

### Task 10.0: Admin Fixes & Improvements (COMPLETED)
**Date**: 2025-11-26

**Completed**:
- [x] Fixed SQLAdmin auth - changed from `pbkdf2_sha256` to `bcrypt` (matching app password hashing)
- [x] Fixed `passlib` compatibility - replaced with direct `bcrypt` module in `domains/users/security.py`
- [x] Fixed admin/users list template - renamed `pagination` context var to `page_info` to avoid collision with imported macro
- [x] Added dev logging to Makefile (`make serve-log`, `make serve-debug`)
- [x] Merged SQLAdmin under `/admin/db` (was `/sqladmin`)
- [x] Added "Database Admin" link to admin sidebar
- [x] Created 14 unit tests for SQLAdmin auth (`tests/unit/domains/sqladmin/test_sqladmin_auth.py`)
- [x] Created `JobAdminService` with list/approve/reject/comment methods
- [x] Created `AdminJobsController` with moderation endpoints

**Files Modified**:
- `src/pydotorg/domains/sqladmin/auth.py` - Use bcrypt via verify_password
- `src/pydotorg/domains/users/security.py` - Replace passlib with direct bcrypt
- `src/pydotorg/domains/sqladmin/config.py` - Changed base_url to `/admin/db`
- `src/pydotorg/domains/admin/controllers/users.py` - Renamed pagination to page_info
- `src/pydotorg/templates/admin/users/list.html.jinja2` - Use page_info instead of pagination
- `src/pydotorg/templates/admin/partials/sidebar.html.jinja2` - Added Database Admin link
- `Makefile` - Added serve-log and serve-debug targets

**Files Created**:
- `src/pydotorg/domains/admin/services/jobs.py` - JobAdminService
- `src/pydotorg/domains/admin/controllers/jobs.py` - AdminJobsController
- `src/pydotorg/templates/admin/jobs/detail.html.jinja2` - Job detail view
- `src/pydotorg/templates/admin/jobs/partials/job_preview.html.jinja2` - Modal preview
- `tests/unit/domains/sqladmin/__init__.py`
- `tests/unit/domains/sqladmin/test_sqladmin_auth.py` - 16 tests (incl. SSO)
- `tests/unit/domains/admin/test_job_admin_service.py` - 15 tests

---

### Task 10.1: SQLAdmin/Litestar Auth Integration (COMPLETED)
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE (2025-11-26)

**Problem Solved**: SQLAdmin now shares auth with Litestar! Users logged into the main admin panel are automatically authenticated in SQLAdmin (Database Admin).

**Implementation** (Option A - Recommended approach):
- Modified `AdminAuthBackend.authenticate()` to first check for Litestar session cookie
- Uses `SessionService.get_user_id_from_session()` to validate existing sessions
- If valid superuser session exists, auto-authenticates without requiring SQLAdmin login
- Falls back to SQLAdmin's own session if no Litestar session present

**Files Modified**:
- `src/pydotorg/domains/sqladmin/auth.py` - Added `_check_litestar_session()` method, integrated SSO
- `tests/unit/domains/sqladmin/test_sqladmin_auth.py` - Added 2 new SSO tests (16 total)

**Key Code** (from `auth.py`):
```python
async def _check_litestar_session(self, request: Request) -> User | None:
    litestar_session_id = request.cookies.get(settings.session_cookie_name)
    if not litestar_session_id:
        return None
    user_id = self._litestar_session_service.get_user_id_from_session(litestar_session_id)
    # ... validate user is superuser and active
```

---

### Task 10.2: Admin Sub-Pages Implementation
**Agent**: `python-backend-engineer`
**Priority**: HIGH

| Route           | Status      | Description                                        |
|-----------------|-------------|----------------------------------------------------|
| /admin/users    | ✅ Done     | User management with CRUD, roles, activation       |
| /admin/jobs     | ✅ Done     | Job moderation queue with approve/reject/comment   |
| /admin/sponsors | ✅ Done     | Sponsor application management with workflow       |
| /admin/db       | ✅ Done     | Database Admin (SQLAdmin) with DaisyUI restyling   |
| /admin/events   | ✅ Done     | Event management with calendar, feature/unfeature  |
| /admin/pages    | ✅ Done     | CMS page management with publish/unpublish         |
| /admin/blogs    | ✅ Done     | Blog/feed management with activate/deactivate      |
| /admin/settings | ✅ Done     | Site settings (placeholder)                        |
| /admin/logs     | ✅ Done     | Activity audit log (placeholder)                   |

**Completed for /admin/jobs** (2025-11-26):
- [x] Registered `AdminJobsController` in `main.py` route_handlers
- [x] Added `JobAdminService` to dependencies in `domains/admin/dependencies.py`
- [x] Created job list template `admin/jobs/list.html.jinja2`
- [x] Created job detail template `admin/jobs/detail.html.jinja2`
- [x] Created job preview partial `admin/jobs/partials/job_preview.html.jinja2`
- [x] Created job row partial `admin/jobs/partials/job_row.html.jinja2`
- [x] Fixed status enum comparison (use `.value` for StrEnum)
- [x] Created 15 unit tests for JobAdminService
- [x] Fixed `NameError: JobAdminService not defined` - moved import outside TYPE_CHECKING block for runtime DI

**Completed for /admin/users** (2025-11-26):
- [x] Created `UserAdminService` with list/get/update/delete/toggle methods
- [x] Created `AdminUsersController` with CRUD endpoints
- [x] Created user list template with search and filters
- [x] Created user edit template with role management
- [x] Created 19 unit tests for UserAdminService

**Completed for /admin/sponsors** (2025-11-26):
- [x] Created `SponsorAdminService` with list/get/approve/reject/finalize methods
- [x] Created `AdminSponsorsController` with workflow endpoints
- [x] Created sponsor templates: `list.html.jinja2`, `detail.html.jinja2`, `sponsors_list.html.jinja2`, `sponsor_detail.html.jinja2`
- [x] Created sponsor partials: `sponsorship_row.html.jinja2`, `sponsorship_preview.html.jinja2`
- [x] Updated sidebar with sponsor links
- [x] Registered controller and dependency provider
- [x] Created 23 unit tests for SponsorAdminService

**Completed for /admin/db SQLAdmin Restyling** (2025-11-26):
- [x] Created custom DaisyUI templates (`templates/sqladmin/`)
- [x] Created `base.html` with TailwindCSS/DaisyUI styling
- [x] Created `layout.html` with sidebar navigation and theme toggle
- [x] Created `list.html` with DaisyUI table and pagination
- [x] Created `details.html` with DaisyUI cards
- [x] Created `create.html` and `edit.html` with DaisyUI forms
- [x] Created `login.html` with DaisyUI card layout
- [x] Created modal templates (`modals/delete.html`, `modals/list_action_confirmation.html`, `modals/details_action_confirmation.html`)
- [x] Updated SQLAdmin config to use custom templates directory
- [x] Added Vite bundling for admin JS/CSS (jQuery, Select2, Flatpickr, Lucide icons)
- [x] Converted all SQLAdmin templates to use Lucide icons site-wide

---

### Task 10.3: Docker Setup
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE (2025-11-27)

**Completed**:
- [x] Create Dockerfile (multi-stage with uv, Granian, non-root user)
- [x] Create Dockerfile.dev (development with hot-reload)
- [x] Create docker-compose.yml (dev profiles)
- [x] Create docker-compose.prod.yml
- [x] Add health checks to all services
- [x] Configure volume mounts for hot-reload
- [x] Add maildev service for email testing (port 1080 UI, 1025 SMTP)
- [x] Add meilisearch service (optional, full profile)
- [x] Add .dockerignore
- [x] Add .env.docker.example

**Files Created**:
```
Dockerfile                    # Production multi-stage build
Dockerfile.dev                # Development with hot-reload
docker-compose.yml            # Enhanced with app, worker, maildev, meilisearch
docker-compose.prod.yml       # Production overrides
.dockerignore                 # Build context optimization
.env.docker.example           # Environment template
```

**Docker Services**:
| Service     | Port(s)        | Profile | Description                    |
|-------------|----------------|---------|--------------------------------|
| postgres    | 5432           | dev/full| PostgreSQL 16 Alpine          |
| redis       | 6379           | dev/full| Redis 7 Alpine                |
| app         | 8000           | dev/full| Litestar app (Granian)        |
| worker      | -              | dev/full| SAQ background worker         |
| maildev     | 1080, 1025     | dev/full| Email testing (UI + SMTP)     |
| meilisearch | 7700           | full    | Search engine (optional)      |

**Usage**:
```bash
# Development (default profile)
make docker-up              # Start postgres, redis, app, worker, maildev

# Full stack (includes meilisearch)
docker compose --profile full up -d

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Email Testing with MailDev**:
- Web UI: http://localhost:1080 (view all sent emails)
- SMTP: localhost:1025 (configure in app)
- Set `SMTP_HOST=maildev` and `SMTP_PORT=1025` in development

---

### Task 10.4: CI/CD Pipeline
**Agent**: `github-git-expert`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE (2025-11-27)

**Completed**:
- [x] Create GitHub Actions CI workflow (ci.yml)
- [x] Add lint/format/type-check in unified validate job
- [x] Add unit test job (no containers needed)
- [x] Add integration test job (PostgreSQL + Redis service containers)
- [x] Add E2E test job (Playwright)
- [x] Add coverage job with Codecov upload
- [x] Add frontend build job (Bun/Vite/TailwindCSS)
- [x] Add security scanning (zizmor workflow security)
- [x] Add CI success gate job
- [x] Create release workflow (release.yml) - GitHub Release + Docker image
- [x] Create changelog workflow (cd.yml)
- [x] Create PR title linting (pr-title.yml)
- [x] Create docs workflow (docs.yml) - Sphinx + GitHub Pages
- [x] Update dependabot.yml (grouped updates)
- [x] Add release.yml for GitHub Release categories

**Files Created**:
```
.github/
├── workflows/
│   ├── ci.yml              # Main CI: validate, tests, coverage, frontend
│   ├── cd.yml              # Changelog generation on tags
│   ├── release.yml         # GitHub Release + Docker image on tags
│   ├── pr-title.yml        # Semantic PR title enforcement
│   └── docs.yml            # Documentation build + Pages deploy
├── dependabot.yml          # Grouped dependency updates
└── release.yml             # Release notes categories
```

**CI Workflow Structure** (matching litestar-workflows style):
1. **security** - zizmor workflow security scan
2. **validate** - ruff check, ruff format, codespell, ty type-check
3. **frontend** - Bun install, biome lint, Vite build, TailwindCSS
4. **test-unit** - Fast unit tests (no containers)
5. **test-integration** - PostgreSQL + Redis service containers
6. **test-e2e** - Playwright browser tests (after unit+integration pass)
7. **coverage** - Full coverage with Codecov upload
8. **ci-success** - Gate job for branch protection

**Note**: No PyPI publishing (this is an application, not a library)

---

## Agent Assignment Summary

| Phase | Primary Agent | Support Agent |
|-------|--------------|---------------|
| Phase 2 (Infrastructure) | `python-backend-architect` | `python-backend-engineer` |
| Phase 3 (Domains) | `python-backend-engineer` | `python-backend-architect` |
| Phase 4 (Frontend) | `ui-engineer` | `documentation-expert` |
| Phase 5 (API) | `python-backend-architect` | `python-backend-engineer` |
| Phase 6 (Tasks/Integrations) | `python-backend-engineer` | - |
| Phase 7 (Testing) | `Python Testing Expert` | `ui-comprehensive-tester` |
| Phase 8 (Documentation) | `documentation-expert` | - |
| Phase 9 (DevOps) | `github-git-expert` | `python-backend-engineer` |
| Debugging | `ultrathink-debugger` | - |

---

## Quick Reference: Litestar Patterns

### Controller Pattern
```python
from litestar import Controller, get, post
from litestar.di import Provide

class ItemController(Controller):
    path = "/items"
    dependencies = {"service": Provide(provide_service)}

    @get("/")
    async def list_items(self, service: ItemService) -> list[ItemRead]:
        return await service.list()
```

### Service Pattern (Advanced Alchemy)
```python
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

class ItemService(SQLAlchemyAsyncRepositoryService[Item]):
    class Repo(SQLAlchemyAsyncRepository[Item]):
        model_type = Item
    repository_type = Repo
```

### Template Response
```python
from litestar.response import Template

@get("/")
async def index() -> Template:
    return Template(template_name="index.html.jinja2", context={"title": "Home"})
```

### Auth Middleware
```python
from litestar.middleware import AbstractAuthenticationMiddleware

class AuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, conn: ASGIConnection) -> AuthenticationResult:
        # Validate token, return AuthenticationResult(user, auth)
```

---

## File Structure Target

```
src/pydotorg/
├── __init__.py
├── main.py                    # Litestar app
├── config.py                  # Settings
├── cli.py                     # CLI commands
│
├── core/
│   ├── auth/                  # Authentication
│   ├── database/              # DB config
│   ├── middleware/            # Custom middleware
│   └── security/              # Security utils
│
├── domains/
│   ├── users/                 # User management
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repositories.py
│   │   ├── services.py
│   │   └── controllers.py
│   ├── pages/                 # CMS pages
│   ├── downloads/             # Python releases
│   ├── jobs/                  # Job board
│   ├── events/                # Events
│   ├── blogs/                 # Blog aggregation
│   ├── sponsors/              # Sponsorships
│   ├── community/             # Community
│   └── ... (other domains)
│
├── templates/
│   ├── base.html.jinja2
│   ├── partials/
│   ├── macros/
│   ├── pages/
│   ├── downloads/
│   ├── jobs/
│   └── auth/
│
├── tasks/                     # SAQ background tasks
│
└── lib/                       # Shared utilities

static/
├── css/
├── js/
└── images/

tests/
├── unit/
├── integration/
└── e2e/
```

---

## Next Steps - Tiered Priority List

### Tier 1: CRITICAL (Must Complete for MVP)

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| **JWT Authentication Middleware** | 2.2 | CRITICAL | High | ✅ Done (JWTAuthMiddleware + JWTService) |
| **Session-based Auth (Fallback)** | 2.2 | CRITICAL | Medium | ✅ Done (SessionService with Redis) |
| **Password Hashing Service** | 2.2 | CRITICAL | Low | ✅ Done (bcrypt in security.py) |
| **CSRF Protection** | 2.2 | HIGH | Medium | ✅ Done (CSRFConfig enabled in main.py) |
| **Docker Setup** | 10.3 | HIGH | Medium | ✅ Done |
| **CI/CD Pipeline** | 10.4 | HIGH | Medium | ✅ Done |

### Tier 2: HIGH PRIORITY (Core Functionality)

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| ~~**Admin Events Page**~~ | 10.2 | ✅ DONE | Medium | `/admin/events` - Event moderation queue |
| ~~**Admin Pages (CMS)**~~ | 10.2 | ✅ DONE | High | `/admin/pages` - CMS page editing interface |
| **SAQ Task Queue** | 6.1 | HIGH | High | Background job processing (feed refresh, email) |
| **Email System** | 6.2 | HIGH | Medium | SMTP config + email templates |
| **User Registration Flow** | 2.2 | HIGH | Medium | ✅ Done (email verification tokens implemented) |
| ~~**CI/CD Pipeline**~~ | 10.4 | ✅ DONE | Medium | GitHub Actions for lint/test/deploy |

### Tier 3: MEDIUM PRIORITY (Enhanced Features)

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| ~~**Admin Blogs Page**~~ | 10.2 | ✅ DONE | Medium | `/admin/blogs` - Blog/feed management |
| ~~**Admin Settings**~~ | 10.2 | ✅ DONE | Low | `/admin/settings` - Site settings (placeholder) |
| ~~**Admin Logs/Audit**~~ | 10.2 | ✅ DONE | Medium | `/admin/logs` - Activity audit log (placeholder) |
| **Search (Meilisearch)** | 6.3 | MEDIUM | High | Full-text search for pages, jobs, events |
| **OAuth2 Social Login** | 2.2 | MEDIUM | Medium | GitHub, Google authentication |
| **API Rate Limiting** | 5.1 | MEDIUM | Low | Prevent API abuse |
| **API Documentation** | 9.1 | MEDIUM | Medium | OpenAPI/Swagger UI setup |
| **Mailing Domain** | 3.x | MEDIUM | Low | Last remaining domain (models/services) |

### Tier 4: LOW PRIORITY (Nice to Have)

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| **GraphQL API** | 5.2 | LOW | High | Optional alternative to REST |
| **CDN Integration (Fastly)** | 6.4 | LOW | Medium | Cache purging, surrogate keys |
| **Feature Flags** | 2.3 | LOW | Low | Runtime feature toggles |
| **Developer Documentation** | 9.2 | LOW | Medium | ARCHITECTURE.md, deployment guide |

### Skipped/Deferred Items

| Task | Phase | Status | Reason |
|------|-------|--------|--------|
| **Boxes Domain** | 3.2 | ✅ SKIPPED | Using pure Jinja2 templates instead |
| **Companies Domain** | 3.x | ✅ MERGED | Merged into Sponsors domain |

### Recommended Next Actions (In Order)

1. ~~**Complete Admin Sub-Pages**~~ ✅ DONE (2025-11-26)
   - All admin pages complete: users, jobs, sponsors, events, pages, blogs, settings, logs

2. **Docker Setup** (Tier 1)
   - Required for deployment
   - Enables testing in production-like environment

3. **CI/CD Pipeline** (Tier 2)
   - Automates testing/linting on PRs
   - Enables safer development workflow

4. **SAQ Task Queue** (Tier 2)
   - Foundation for background processing
   - Required for email, feed refresh, job expiration

5. **Email System** (Tier 2)
   - Enables user registration flow completion
   - Password reset functionality

---

*Document generated for Python.org Litestar rebuild project*
*Last updated: 2025-11-27*

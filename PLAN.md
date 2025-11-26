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
- [ ] Implement JWT authentication middleware
- [ ] Create session-based authentication (fallback)
- [ ] Implement password hashing service (passlib/bcrypt)
- [ ] Create user registration flow
- [ ] Implement email verification
- [ ] Add OAuth2 social login (GitHub, Google)
- [ ] Create role-based permission guards
- [ ] Implement CSRF protection for forms

**Files to Create**:
```
src/pydotorg/
├── core/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── middleware.py      # JWTAuthMiddleware
│   │   ├── guards.py          # Permission guards
│   │   ├── jwt.py             # JWT utilities
│   │   ├── password.py        # Password hashing
│   │   └── oauth.py           # OAuth2 providers
│   └── security/
│       ├── __init__.py
│       └── csrf.py
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
**Status**: ✅ COMPLETE (2025-11-26)

### Testing Infrastructure Added

**New Make Targets**:
```bash
make test-unit           # Run unit tests only (no Docker)
make test-integration    # Run integration tests (requires Docker)
make test-e2e            # Run E2E Playwright tests
make test-full           # Run all tests
make playwright-install  # Install Playwright browsers
```

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

## Phase 10: DevOps & Deployment

### Task 10.1: Docker Setup
**Agent**: `python-backend-engineer`
**Priority**: HIGH

**Tasks**:
- [ ] Create Dockerfile (multi-stage)
- [ ] Create docker-compose.yml (dev)
- [ ] Create docker-compose.prod.yml
- [ ] Add health checks
- [ ] Configure volume mounts

---

### Task 10.2: CI/CD Pipeline
**Agent**: `github-git-expert`
**Priority**: HIGH

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Add lint/format/type-check jobs
- [ ] Add test job with coverage
- [ ] Add security scanning
- [ ] Create release workflow
- [ ] Add deployment workflow

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

*Document generated for Python.org Litestar rebuild project*
*Last updated: 2025-11-26*

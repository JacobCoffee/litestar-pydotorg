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
**Status**: ✅ COMPLETE (2025-11-27)

**Design Guide**:
- Use pydantic-settings for all configuration
- Environment-specific configs (dev/staging/prod)
- Secrets management via environment variables
- Feature flags support

**Tasks**:
- [x] Expand config.py with all necessary settings (364 lines, comprehensive)
- [x] Add environment-specific configuration loading (`Environment` enum: DEV/STAGING/PROD)
- [x] Implement feature flags system (`FeatureFlagsConfig`, `core/features.py`)
- [x] Add logging configuration (structlog via `core/logging.py`)
- [x] Create settings validation on startup (`validate_production_settings()`)

**Implementation Details**:
- **Settings class**: Full pydantic-settings with validation
- **Environment enum**: DEV, STAGING, PROD with automatic debug/log level inference
- **Feature flags**: `FeatureFlagsConfig` nested model + `FeatureFlags` dataclass with guards
- **Validators**: Secret key length validation, database URL validation, production safety checks
- **Computed fields**: `is_debug`, `create_all`, `log_level`, `use_json_logging`, etc.

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

### Task 3.1: Users Domain
**Agent**: `python-backend-engineer`
**Priority**: CRITICAL
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create UserRepository with custom queries
- [x] Create UserService with business logic
- [x] Create MembershipRepository/Service
- [x] Create UserGroupRepository/Service
- [x] Implement Pydantic schemas (UserCreate, UserUpdate, UserRead)
- [x] Create UserController with CRUD endpoints
- [x] Implement user profile endpoints
- [x] Add user search functionality

**File Structure** (all files exist):
```
src/pydotorg/domains/users/
├── __init__.py
├── models.py
├── schemas.py
├── repositories.py
├── services.py
├── controllers.py
├── dependencies.py
├── security.py        # Password hashing (bcrypt)
└── auth_controller.py # Auth endpoints
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
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Complete Page model with all fields
- [x] Implement PageRepository with path-based lookups
- [x] Create PageService with publishing logic
- [x] Create ImageRepository/Service
- [x] Create DocumentFileRepository/Service
- [x] Implement page tree/hierarchy
- [x] Create page rendering controller
- [ ] Add page caching (Redis) - *Not yet implemented*

**Files**: models.py, repositories.py, services.py, controllers.py, dependencies.py, schemas.py (partial)

---

### Task 3.4: Downloads Domain
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Complete Release model with version comparison
- [x] Implement ReleaseRepository with version queries
- [x] Create ReleaseService with publishing logic
- [x] Create ReleaseFileRepository/Service
- [x] Implement download page logic
- [ ] Add download statistics tracking - *Not yet implemented*
- [x] Create release API endpoints
- [ ] Implement GPG signature verification - *Not yet implemented*

**Files**: models.py, repositories.py, services.py, controllers.py, dependencies.py, schemas.py

---

### Task 3.5: Blogs Domain
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create BlogEntry model
- [x] Create Feed model with RSS parsing
- [x] Implement feed aggregation service
- [x] Create blog listing controller
- [ ] Implement feed refresh background task (SAQ) - *SAQ not yet implemented*
- [x] Add blog search functionality

**Files**: models.py, repositories.py, services.py, controllers.py, dependencies.py

---

### Task 3.6: Jobs Domain
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create JobType, JobCategory models
- [x] Create Job model with full workflow states
- [x] Implement job approval workflow (via AdminJobsController)
- [x] Create job search with filters
- [ ] Implement job expiration logic (SAQ task) - *SAQ not yet implemented*
- [x] Create job submission form
- [ ] Add email notifications - *Basic email service exists, notifications not wired*

**Files**: models.py, repositories.py, services.py, controllers.py, dependencies.py

---

### Task 3.7: Events Domain
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create all event models
- [ ] Implement recurrence rule engine (dateutil.rrule) - *Basic model exists, no rrule logic*
- [ ] Create iCalendar export - *Not yet implemented*
- [x] Implement event search with date filtering
- [x] Create event submission workflow
- [ ] Add calendar feed (RSS/Atom) - *Not yet implemented*

**Files**: models.py, repositories.py, services.py, controllers.py, dependencies.py, schemas.py

---

### Task 3.8: Sponsors Domain
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Complete all sponsor models
- [x] Implement sponsorship workflow (apply -> approve -> finalize) via AdminSponsorsController
- [x] Create benefit assignment logic
- [ ] Implement contract management - *Basic model exists, full workflow not implemented*
- [x] Create sponsor listing page
- [x] Add sponsor logo management
- [ ] Implement annual sponsorship renewal - *Not yet implemented*

**Files**: models.py, repositories.py, services.py, controllers.py, dependencies.py, schemas.py

---

### Task 3.9-3.17: Remaining Domains
**Agent**: `python-backend-engineer`
**Priority**: NORMAL
**Status**: ✅ COMPLETE (except mailing)

| Domain | Status | Files |
|--------|--------|-------|
| community | ✅ DONE | models, repos, services, controllers, schemas, dependencies |
| companies | ✅ MERGED into sponsors | N/A |
| successstories | ✅ DONE | models, repos, services, controllers, schemas, dependencies |
| nominations | ✅ DONE | models, repos, services, controllers, schemas, dependencies |
| codesamples | ✅ DONE | models, repos, services, controllers, schemas, dependencies |
| minutes | ✅ DONE | models, repos, services, controllers, schemas, dependencies |
| banners | ✅ DONE | models, repos, services, controllers, schemas, dependencies |
| mailing | ⏳ PENDING | Only `__init__.py` exists |
| work_groups | ✅ DONE | models, repos, services, controllers, schemas, dependencies |

---

## Phase 4: Frontend (Jinja2 + TailwindCSS + DaisyUI)
**Status**: ✅ MOSTLY COMPLETE (2025-11-27)

### Task 4.1: Base Template System
**Agent**: `ui-engineer`
**Priority**: CRITICAL
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create base.html.jinja2 template
- [x] Create navbar component (DaisyUI navbar)
- [x] Create footer component
- [x] Create sidebar component
- [x] Set up Tailwind CSS build pipeline (`tailwind.config.js`)
- [x] Configure DaisyUI theme (Python-branded colors)
- [x] Create responsive layout system
- [x] Implement dark mode toggle

**Templates Created** (100+ templates):
```
src/pydotorg/templates/
├── partials/ (sidebar, breadcrumbs, alert)
├── macros/ (forms, cards, buttons, alerts)
├── components/
│   ├── sections/ (hero, features, news_feed, events_list, sponsors_grid, etc.)
│   ├── nav/ (main_menu, mobile_menu, footer_links, social_links)
│   ├── widgets/ (download_button, version_selector, search_box, newsletter_signup)
│   └── code/ (code_block, repl_demo)
├── auth/ (login, register, forgot_password, reset_password, profile)
├── admin/ (dashboard, users, jobs, sponsors, events, pages, blogs, settings, logs)
├── errors/ (403, 404, 500, generic)
└── [domain templates]/ (pages, downloads, jobs, events, blogs, sponsors, etc.)
```

---

### Task 4.2: Component Library (DaisyUI)
**Agent**: `ui-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create button component macros (`macros/buttons.html.jinja2`)
- [x] Create card component macros (`macros/cards.html.jinja2`)
- [x] Create form component macros (with HTMX support) (`macros/forms.html.jinja2`)
- [x] Create table component macros (`admin/partials/data_table.html.jinja2`)
- [x] Create modal component macros
- [x] Create alert/toast component macros (`macros/alerts.html.jinja2`)
- [x] Create pagination component
- [x] Create search component (`components/widgets/search_box.html.jinja2`)

---

### Task 4.3: Page Templates
**Agent**: `ui-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Create homepage template with hero section (`pages/index.html.jinja2`)
- [x] Create downloads page with version selector (`downloads/index.html.jinja2`, `release.html.jinja2`, etc.)
- [x] Create documentation browser template (`docs/index.html.jinja2`)
- [x] Create community/events templates (`community/`, `events/`)
- [x] Create job board templates (`jobs/index.html.jinja2`, `detail.html.jinja2`, `submit.html.jinja2`)
- [x] Create auth flow templates (`auth/login.html.jinja2`, `register.html.jinja2`, etc.)
- [x] Create admin dashboard templates (`admin/` - full suite)

**All Domain Templates Exist**:
- downloads: index, release, source, windows, macos
- jobs: index, detail, submit, preview
- events: index, detail, calendar, submit
- blogs: index, feed
- sponsors: list, detail, apply
- community: index, post_detail
- successstories: index, detail, category
- minutes: index, detail
- banners: index, preview
- codesamples: index, detail
- work_groups: index, detail
- nominations: list, detail
- search: index, results

---

### Task 4.4: Frontend Build Pipeline
**Agent**: `ui-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Set up Node.js/Bun for frontend build
- [x] Configure Tailwind CSS with Python.org color palette
- [x] Configure DaisyUI themes
- [x] Set up PostCSS pipeline
- [x] Create Makefile targets for frontend build (`make frontend`)
- [x] Implement CSS purging for production
- [x] Add source maps for development

**Files**:
- `tailwind.config.js` - TailwindCSS + DaisyUI configuration
- `postcss.config.js` - PostCSS pipeline
- `package.json` - Node.js dependencies (Bun)

---

## Phase 5: API Layer
**Status**: ✅ MOSTLY COMPLETE

### Task 5.1: REST API Endpoints
**Agent**: `python-backend-architect`
**Priority**: HIGH
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Implement User API endpoints (`domains/users/controllers.py`)
- [x] Implement Pages API endpoints (`domains/pages/controllers.py`)
- [x] Implement Downloads API endpoints (`domains/downloads/controllers.py`)
- [x] Implement Jobs API endpoints (`domains/jobs/controllers.py`)
- [x] Implement Events API endpoints (`domains/events/controllers.py`)
- [x] Implement Sponsors API endpoints (`domains/sponsors/controllers.py`)
- [x] Add OpenAPI documentation (configured in `main.py`)
- [ ] Implement API versioning - *Paths use /api/v1 but no version negotiation*
- [ ] Add rate limiting - *Not yet implemented*
- [ ] Add API authentication (API keys) - *JWT auth only, no API keys*

**All Domains Have Controllers**: users, pages, downloads, jobs, events, blogs, sponsors, banners, codesamples, community, minutes, nominations, successstories, work_groups, search

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

### Task 6.1: SAQ Task Queue - Core Infrastructure
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE (2025-11-27)

**Tasks**:
- [x] Configure SAQ worker (`tasks/worker.py`)
- [x] Implement feed aggregation task (`tasks/feeds.py` - refresh_all_feeds, refresh_stale_feeds)
- [x] Implement job expiration task (`tasks/jobs.py` - expire_jobs, index_all_jobs)
- [x] Implement email sending task (`tasks/email.py` - send_email, send_bulk_email)
- [x] Implement cache warming task (`tasks/cache.py` - warm_homepage_cache, warm_navigation_cache)
- [x] Implement search indexing task (`tasks/search.py` - reindex_all, index_document)
- [x] Add task monitoring admin UI (`/admin/tasks` - TaskAdminService + AdminTasksController)
- [x] Add admin sidebar link for Task Monitoring

**Implementation Summary** (31 tasks, 7 crons):
| File | Tasks | Lines | Description |
|------|-------|-------|-------------|
| `feeds.py` | 4 + 1 cron | 195 | Feed refresh (all, stale, single) |
| `jobs.py` | 4 + 2 crons | 181 | Job expiration, archival, draft cleanup |
| `cache.py` | 6 | 555 | Cache warming (homepage, releases, events, blogs, pages) |
| `search.py` | 12 | 729 | Meilisearch indexing (jobs, events, pages, blogs) |
| `email.py` | 6 | 439 | Transactional emails (verification, reset, notifications) |
| `worker.py` | config | 236 | Queue setup, startup/shutdown hooks, cron registration |

**Files Created**:
```
src/pydotorg/tasks/
├── __init__.py
├── worker.py          # SAQ queue config + get_task_functions()
├── feeds.py           # Blog feed refresh tasks
├── jobs.py            # Job expiration + search indexing
├── email.py           # Async email sending
├── cache.py           # Homepage/navigation cache warming
└── search.py          # Meilisearch indexing tasks

src/pydotorg/domains/admin/
├── services/tasks.py  # TaskAdminService
├── controllers/tasks.py # AdminTasksController
└── templates/admin/tasks/
    ├── index.html.jinja2
    └── partials/
        ├── queue_card.html.jinja2
        └── job_row.html.jinja2
```

**Bug Fixes Applied**:
- Fixed `_get_task_functions()` to call function instead of importing empty constant
- Fixed `get_all_jobs()` to use `queue.iter_jobs()` instead of non-existent `queue.queued()`
- Fixed SAQ `workers` info returning dict instead of int (extracted `len(workers_info)`)
- Fixed Jinja template sum filters with namespace pattern for dict iteration
- Fixed SAQ worker command: renamed `settings_dict` → `saq_settings` (was conflicting with pydantic Settings)
- Fixed timestamp conversion in `_job_to_dict()` - SAQ returns Unix timestamps as int, not datetime
- Fixed admin task button URLs: `/admin/tasks/enqueue/refresh-feeds`, `/admin/tasks/enqueue/rebuild-indexes`
- Added CSRF token injection for HTMX requests in `base.html.jinja2`

**Commands**:
```bash
make dev         # Start infra + show terminal instructions
make dev-all     # Start infra + worker (background) + server with labeled logs
make dev-tmux    # Start everything in tmux session (recommended)
make dev-stop    # Stop background processes
make serve       # Run web server only
make worker      # Run SAQ worker only
make infra-up    # Start postgres + redis + meilisearch
```

---

### Task 6.1b: SAQ Event-Driven Integration
**Agent**: `python-backend-engineer`
**Priority**: HIGH
**Status**: ✅ COMPLETE (2025-11-27)

**Problem Solved**: Tasks are now **wired to application events** with async task enqueueing.

**Implementation Summary**:

| Task | Trigger Event | Integration Point | Status |
|------|---------------|-------------------|--------|
| `send_verification_email` | User registration | `auth_controller.register()` | ✅ Done |
| `send_password_reset_email` | Password reset request | `auth_controller.forgot_password()` | ✅ Done |
| `send_job_approved_email` | Admin approves job | `JobAdminService.approve_job()` | ✅ Done |
| `send_job_rejected_email` | Admin rejects job | `JobAdminService.reject_job()` | ✅ Done |
| `send_event_reminder_email` | Event approaching | Cron job (daily at 8 AM) | ✅ Done |
| `index_job` | Job approved | `JobAdminService.approve_job()` | ✅ Done |
| `index_event` | Event created/updated | `EventService.create()/.update()` | ✅ Done |
| `index_page` | Page created/updated | `PageService.create()/.update()` | ✅ Done |
| `index_blog_entry` | Blog created/updated | `BlogService.create()/.update()` | ✅ Done |
| `remove_job_from_index` | Job deleted | `JobService.delete()` | ✅ Done |
| `cleanup_past_occurrences` | Monthly cleanup | Cron job (1st of month at 3 AM) | ✅ Done |

**Files Created**:
- `src/pydotorg/lib/tasks.py` - Central task enqueue helper (`enqueue_task()`, `enqueue_task_safe()`)
- `src/pydotorg/tasks/events.py` - Event reminder and cleanup cron jobs

**Files Modified**:
- `src/pydotorg/core/auth/jwt.py` - Added `create_password_reset_token()` method
- `src/pydotorg/core/auth/schemas.py` - Added `ForgotPasswordRequest`, `ResetPasswordRequest`
- `src/pydotorg/domains/users/auth_controller.py` - Async email task enqueueing for registration, verification, password reset
- `src/pydotorg/domains/admin/services/jobs.py` - Task enqueueing for approve/reject + search indexing
- `src/pydotorg/domains/admin/controllers/jobs.py` - Added rejection reason passing
- `src/pydotorg/domains/events/services.py` - Search indexing on create/update
- `src/pydotorg/domains/admin/services/events.py` - Search indexing on admin operations
- `src/pydotorg/domains/pages/services.py` - Search indexing on create/update
- `src/pydotorg/domains/admin/services/pages.py` - Search indexing on admin operations
- `src/pydotorg/domains/blogs/services.py` - Search indexing on create/update
- `src/pydotorg/tasks/worker.py` - Registered new event tasks and cron jobs

**Integration Tests Created**:
- `tests/integration/test_tasks_admin.py` - 14 tests for task wiring:
  - Auth flow email task enqueueing (3 tests)
  - Job admin task wiring (6 tests)
  - Graceful failure handling (2 tests)

**Implementation Pattern Used**:
```python
# In service layer after successful operation:
from pydotorg.lib.tasks import enqueue_task

async def approve_job(self, job_id: UUID) -> Job | None:
    job = await self.get_job(job_id)
    if not job:
        return None
    job.status = JobStatus.APPROVED
    await self.session.commit()

    # Enqueue email notification (best-effort, doesn't block)
    await enqueue_task("send_job_approved_email", to_email=job.creator.email, ...)
    # Enqueue search indexing
    await enqueue_task("index_job", job_id=str(job.id))
    return job
```

**Tasks Completed**:
- [x] Wire email tasks to auth flow (registration, password reset)
- [x] Wire email notifications to admin job approval/rejection
- [x] Wire search indexing to CRUD operations (jobs, events, pages, blogs)
- [x] Add event reminder cron job (daily at 8 AM)
- [x] Add event occurrence cleanup cron job (monthly)
- [x] Test all event-driven integrations (14 integration tests)

**CSRF Fix for Admin Task Buttons** (2025-11-27):
The "Refresh Feeds", "Rebuild Search Index", and "Retry Job" buttons on `/admin/tasks` were returning 403 CSRF errors. **RESOLVED**:
- Added CSRF meta tag with server-generated token in `base.html.jinja2`: `<meta name="csrf-token" content="{{ csrf_token() }}">`
- Updated JS to read from meta tag instead of cookie (Litestar uses 128-char tokens: 64 random + 64 HMAC)
- Excluded `/admin/tasks/*` from CSRF validation (these routes are protected by `require_admin` guard)

**HTMX Navigation Fix** (2025-11-27):
The "View All Jobs" link caused blank page with `ne().body is null` error. **RESOLVED**:
- Root cause: `hx-select="#task-dashboard"` on parent div was inherited by child links
- Fixed by moving HTMX auto-refresh attributes to inner `#task-dashboard` div
- Set `hx-boost="false"` on navigation links in `queue_card.html.jinja2`

**Toast Notifications** (2025-11-27):
Added success/error toast notifications for task enqueue buttons using `HX-Trigger` header:
```python
headers={"HX-Trigger": '{"showToast": {"message": "...", "type": "success"}}'}
```

---

### Task 6.2: Email System
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Configure SMTP settings (in `config.py`)
- [x] Create email templates (`core/email/templates.py`)
- [x] Implement email service (`core/email/service.py` - 104 lines)
- [x] Add email verification flow
- [x] Add password reset flow
- [ ] Implement notification emails - *Job/event notifications not wired*

**Files**:
- `core/email/__init__.py`
- `core/email/service.py` - EmailService with SMTP
- `core/email/templates.py` - HTML/text templates for verification and password reset

---

### Task 6.3: Search (Meilisearch)
**Agent**: `python-backend-engineer`
**Priority**: MEDIUM
**Status**: ✅ COMPLETE

**Tasks**:
- [x] Set up Meilisearch client (`meilisearch_python_sdk.AsyncClient`)
- [x] Create search indexes (pages, jobs, events, downloads)
- [x] Implement search service (`core/search/service.py` - 441 lines)
- [x] Add search API endpoints (`domains/search/`)
- [x] Implement search UI (`templates/search/`)
- [x] Add faceted search (filterable_attributes support)

**Files**:
- `core/search/__init__.py`
- `core/search/service.py` - Full SearchService with async Meilisearch
- `core/search/schemas.py` - SearchQuery, SearchResult, SearchHit, IndexedDocument
- `domains/search/` - Search controllers and templates

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

### Tier 1: CRITICAL (Must Complete for MVP) - ✅ ALL COMPLETE

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| **JWT Authentication Middleware** | 2.2 | CRITICAL | High | ✅ Done (JWTAuthMiddleware + JWTService) |
| **Session-based Auth (Fallback)** | 2.2 | CRITICAL | Medium | ✅ Done (SessionService with Redis) |
| **Password Hashing Service** | 2.2 | CRITICAL | Low | ✅ Done (bcrypt in security.py) |
| **CSRF Protection** | 2.2 | HIGH | Medium | ✅ Done (CSRFConfig enabled in main.py) |
| **Docker Setup** | 10.3 | HIGH | Medium | ✅ Done |
| **CI/CD Pipeline** | 10.4 | HIGH | Medium | ✅ Done |
| **Configuration System** | 2.3 | HIGH | Medium | ✅ Done (pydantic-settings + feature flags) |

### Tier 2: HIGH PRIORITY (Core Functionality) - ✅ ALL COMPLETE

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| ~~**SAQ Task Queue**~~ | 6.1 | ✅ DONE | High | Background job processing + admin UI |
| ~~**Email System**~~ | 6.2 | ✅ DONE | Medium | SMTP config + email templates |
| ~~**Search (Meilisearch)**~~ | 6.3 | ✅ DONE | High | Full-text search service |
| ~~**Admin Events Page**~~ | 10.2 | ✅ DONE | Medium | `/admin/events` - Event moderation queue |
| ~~**Admin Pages (CMS)**~~ | 10.2 | ✅ DONE | High | `/admin/pages` - CMS page editing interface |
| ~~**User Registration Flow**~~ | 2.2 | ✅ DONE | Medium | Email verification tokens implemented |
| ~~**CI/CD Pipeline**~~ | 10.4 | ✅ DONE | Medium | GitHub Actions for lint/test/deploy |

### Tier 3: MEDIUM PRIORITY (Enhanced Features)

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| ~~**SAQ Event-Driven Wiring**~~ | 6.1b | ✅ DONE | Medium | 31 tasks wired to app events |
| **API Rate Limiting** | 5.1 | MEDIUM | Low | Prevent API abuse |
| **API Documentation** | 9.1 | MEDIUM | Medium | OpenAPI/Swagger UI setup (basic exists) |
| **Mailing Domain** | 3.x | MEDIUM | Low | Last remaining domain (models/services) |
| **OAuth2 Providers** | 2.2 | MEDIUM | Medium | GitHub/Google providers exist, need testing |
| **Page Caching** | 3.3 | MEDIUM | Medium | Redis cache for pages |
| **Download Statistics** | 3.4 | MEDIUM | Medium | Track download counts |
| **iCalendar Export** | 3.7 | MEDIUM | Low | Events iCal feed |

### Tier 4: LOW PRIORITY (Nice to Have)

| Task | Phase | Priority | Effort | Description |
|------|-------|----------|--------|-------------|
| **GraphQL API** | 5.2 | LOW | High | Optional alternative to REST |
| **CDN Integration (Fastly)** | 6.4 | LOW | Medium | Cache purging, surrogate keys |
| **GPG Signature Verification** | 3.4 | LOW | Low | Download file integrity |
| **Recurrence Rules** | 3.7 | LOW | Medium | dateutil.rrule for events |
| **Calendar RSS/Atom** | 3.7 | LOW | Low | Event feed |
| **Developer Documentation** | 9.2 | LOW | Medium | ARCHITECTURE.md, deployment guide |
| **Contract Management** | 3.8 | LOW | Medium | Full sponsor contract workflow |
| **Template Refactor** | - | LOW | Medium | Move templates from `templates/` into domain folders (e.g., `domains/downloads/templates/`) |

### Skipped/Deferred Items

| Task | Phase | Status | Reason |
|------|-------|--------|--------|
| **Boxes Domain** | 3.2 | ✅ SKIPPED | Using pure Jinja2 templates instead |
| **Companies Domain** | 3.x | ✅ MERGED | Merged into Sponsors domain |

### Recommended Next Actions (In Order)

1. ~~**SAQ Event-Driven Wiring**~~ (Task 6.1b - ✅ COMPLETE)
   - ✅ Wire email tasks to auth flow (registration, password reset)
   - ✅ Wire email notifications to admin job approval/rejection
   - ✅ Wire search indexing to CRUD operations (job/event/page/blog)
   - ✅ Add event reminder cron job
   - **Impact**: 31 tasks now wired to application events

2. **API Rate Limiting** (Tier 3)
   - Protect public endpoints from abuse
   - Use Litestar's built-in rate limiting middleware

3. **Mailing Domain** (Tier 3)
   - Complete domain coverage
   - EmailTemplate model for newsletter/notifications

4. **OAuth2 Testing** (Tier 3)
   - Test GitHub/Google OAuth flows end-to-end
   - Add integration tests for OAuth callback handlers

5. **Page Caching** (Tier 3)
   - Redis cache for rendered pages
   - Cache invalidation on content updates

---

## Development Workflow

### Quick Start (Recommended)

```bash
# Option 1: tmux (best experience)
make dev-tmux                # Starts server, worker, CSS in tmux
tmux attach -t pydotorg      # Attach to session

# Option 2: Multiple terminals
make dev                     # Starts infra, prints instructions
# Then in separate terminals:
make serve                   # Terminal 1: Web server
make worker                  # Terminal 2: SAQ worker
make css-watch               # Terminal 3: TailwindCSS (optional)

# Option 3: Single terminal (worker logs to file)
make dev-all                 # Server in foreground, worker in background
tail -f logs/worker.log      # In another terminal to see worker logs
```

### Stopping Development

```bash
make dev-stop                # Stop server + worker processes
make infra-down              # Stop containers (postgres, redis, meilisearch)
```

### Infrastructure Services

| Service     | Port | Purpose                              |
|-------------|------|--------------------------------------|
| PostgreSQL  | 5432 | Primary database                     |
| Redis       | 6379 | Session store, task queue, cache     |
| Meilisearch | 7700 | Full-text search                     |
| MailDev     | 1080 | Email testing UI (docker only)       |

### Running Tests

```bash
make test                    # Unit tests only (~5s)
make test-integration        # Integration tests (requires infra-up)
make test-all                # All tests
make ci                      # Full CI: lint + fmt + type-check + test
```

---

*Document generated for Python.org Litestar rebuild project*
*Last updated: 2025-11-27 (SAQ fixes, CSRF fixes, HTMX navigation, dev workflow)*

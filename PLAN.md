# Python.org Litestar Rebuild - Active Work Tracker

> **Archive**: Completed phase details in [docs/internal/PLAN_ARCHIVE.md](docs/internal/PLAN_ARCHIVE.md)

## Project Overview

**Objective**: Rebuild Python.org from Django to Litestar
**Source**: `/Users/coffee/git/internal/python/pythondotorg` (Django)
**Target**: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg` (Litestar)

| Component | Old (Django) | New (Litestar) |
|-----------|-------------|----------------|
| Framework | Django 4.x | Litestar 2.14+ |
| ORM | Django ORM | SQLAlchemy 2.0 + Advanced Alchemy |
| Templates | Django Templates + Boxes | Jinja2 Templates |
| Server | Gunicorn/uWSGI | Granian |
| Styling | Bootstrap/Custom CSS | TailwindCSS + DaisyUI |
| Database | PostgreSQL | PostgreSQL (asyncpg) |
| Cache | Redis | Redis |
| Task Queue | Celery | SAQ |
| Search | Elasticsearch | Meilisearch |
| Build | setuptools | uv_build |

---

## Completed Phases (see [PLAN_ARCHIVE.md](docs/internal/PLAN_ARCHIVE.md) for details)

| Phase | Status | Summary |
|-------|--------|---------|
| 1. Foundation | ✅ | uv, Litestar, SQLAlchemy, base models, testing, Granian |
| 2. Core Infrastructure | ✅ | Database layer, JWT/session auth, CSRF, config, feature flags |
| 3. Domain Implementation | ✅ | All 17 domains: users, pages, downloads, blogs, jobs, events, sponsors, community, successstories, nominations, codesamples, minutes, banners, mailing, work_groups |
| 4. Frontend | ✅ | 100+ Jinja2 templates, DaisyUI components, TailwindCSS pipeline |
| 5. API Layer | ✅ | REST endpoints for all domains, OpenAPI docs |
| 6. Background Tasks | ✅ | SAQ queue (31 tasks, 7 crons), email system, Meilisearch |
| 7. Admin Interface | ✅ | SQLAdmin, 22 ModelViews, dashboard, guards |
| 8. Testing | ✅ | 191 unit, 495 integration, 38 E2E tests |
| 10. Admin Sub-Pages | ✅ | Users, jobs, sponsors, events, pages, blogs, email, settings, Docker, CI/CD |

---

## Remaining TODO Items

### Domain Feature Gaps
- [x] **Page caching** (Redis) - Task 3.3 ✅ Cache-Control middleware, Surrogate-Key headers, 404 caching
- [x] **GPG signature verification** for downloads - Task 3.4 ✅ SHA256 field, signature UI, verification instructions
- [x] **Feed refresh SAQ task** for blogs - Task 3.5 ✅ Already implemented: `refresh_stale_feeds` runs every 15 min via `cron_refresh_feeds`
- [x] **Job expiration SAQ task** - Task 3.6 ✅ Already implemented: `expire_jobs` (daily), `archive_old_jobs` (weekly), `cleanup_draft_jobs` (monthly)
- [x] **Email notifications** for jobs - Task 3.6 ✅ `send_job_submitted_email` (admin), `send_job_approved_email`, `send_job_rejected_email`
- [x] **Recurrence rule engine** (dateutil.rrule) for events - Task 3.7 ✅ RecurringRule model, recurrence.py utilities, 29 unit tests
- [x] **Calendar feed** (RSS/Atom) for events - Task 3.7 ✅ RSS 2.0 + Atom 1.0 feeds, per-calendar feeds, 21 unit tests
- [x] **Contract management** workflow for sponsors - Task 3.8 ✅ LegalClause, Contract models with workflow states (DRAFT→AWAITING_SIGNATURE→EXECUTED/NULLIFIED), ContractService with workflow methods, 24 unit tests
- [x] **Annual sponsorship renewal** - Task 3.8 ✅ `approve_with_renewal()`, `get_previous_sponsorship()`, `list_expiring_soon()`, `create_renewal()` service methods, repository support

### API Enhancements
- [x] **API versioning** - ✅ Version negotiation middleware (Accept header, URL path, query param), deprecation headers, 29 unit tests
- [x] **API keys** - ✅ Full API key authentication: model, service, middleware, guards, endpoints, 21 unit tests

### Infrastructure
- [x] **Fastly CDN** - ✅ Surrogate-Key middleware added, cache purging ready (needs Fastly API key config)
- [x] **Notification emails** - ✅ Job/event notifications wired to SAQ email tasks

### Documentation (Phase 9)
- [ ] Generate SDK documentation
- [ ] Update ARCHITECTURE.md
- [ ] Create domain model documentation
- [ ] Write deployment guide
- [ ] Create contributing guide
- [ ] Write troubleshooting guide

### Research TODO
- [ ] Research Litestar patterns for internal API namespacing (`/api/admin/*` vs `/api/_internal/*`)
- [ ] Evaluate authentication requirements for API docs visibility
- [ ] Review Litestar's `OpenAPIConfig` for multiple spec generation
- [ ] Consider `include_in_schema` per security level vs per route

### Page Implementations

#### About Section
- [x] **`/about/help`** - FAQ/Help page with common questions, getting started resources ✅
- [x] **`/about/apps`** - Python applications showcase (notable apps built with Python) ✅
- [x] **`/about/quotes`** - Testimonials and quotes from Python users/companies ✅
- [x] **`/about/gettingstarted`** - Beginner's guide to Python, installation, first steps ✅
- [x] **`/about/legal`** - Legal information, trademarks, licensing ✅

#### Downloads Section
- [x] **`/downloads/alternatives`** - Alternative Python implementations (PyPy, Jython, IronPython, etc.) ✅
- [x] **`/downloads/other`** - Other download resources (source tarballs, older versions, etc.) ✅

#### Community Section
- [x] **`/community/irc`** - IRC channels information (#python, #python-dev, etc.) ✅
- [x] **`/community/forums`** - Python forums (Discourse, Reddit, etc.) ✅
- [x] **`/community/lists`** - Mailing lists directory (python-list, python-dev, python-ideas, etc.) ✅

#### PSF Section
- [x] **`/psf/about`** - About the Python Software Foundation ✅
- [x] **`/psf/conduct`** - Code of Conduct (community guidelines, reporting) ✅
- [x] **`/psf/get-involved`** - How to contribute to Python/PSF ✅
  - Interactive Annual Impact Report
  - Volunteer opportunities
  - Working groups
  - Sponsorship tiers

---

## Known Issues / Bugs

### HIGH Priority
| Issue | Location | Description |
|-------|----------|-------------|
| ~~**Worker: `warm_homepage_cache` MissingGreenlet**~~ | ~~SAQ worker~~ | ✅ **FIXED**: Added `selectinload()` to `EventRepository.get_upcoming()` and `get_featured()`. |
| ~~**SQLAlchemy MissingGreenlet in async context**~~ | ~~DB operations~~ | ✅ **FIXED**: Added eager loading to all event-related queries in repositories and search tasks. |
| ~~**Worker: `index_event` EventLocation error**~~ | ~~`tasks/search.py`~~ | ✅ **FIXED**: Added `selectinload()` for `Event.venue`, `Event.occurrences`, `Event.categories` in `index_event()` and `index_all_events()`. |

### MEDIUM Priority
| Issue | Location | Description |
|-------|----------|-------------|
| ~~**`/blogs` sidebar feed filters**~~ | ~~`/blogs`~~ | ✅ **FIXED**: Added HTMX OOB swap for sidebar active state, explicit `hx-swap="innerHTML"`. |
| ~~**`/events` filters don't filter**~~ | ~~`/events`~~ | ✅ **FIXED**: Added `calendar`, `start_date`, `end_date` params to controller, filter badge display. |
| ~~**`/psf/membership` not implemented**~~ | ~~`/psf/membership`~~ | ✅ **DONE**: Created PSF membership page with membership levels (Basic, Supporting, Contributing, Managing, Fellow), benefits, FAQ accordion, and CTAs. Added `PSFPageController` with `/psf/membership/` route. |
| ~~**`/community/workshops` not implemented**~~ | ~~`/community/workshops`~~ | ✅ **DONE**: Created workshops & user groups page with links to Python Wiki, Meetup.com, event calendar. Includes event types, how to start a user group, and featured groups (PyLadies, Django Girls, Python Brasil). Added `/community/workshops/` route. |
| ~~**Feature: Sitewide announcement banner**~~ | ~~Sitewide~~ | ✅ **DONE**: Full banner system with targeting (`frontend`/`api`), path filtering, toast notifications. Admin UI at `/admin/banners`. API banners via `X-API-Notice` header. Persists across HTMX navigation. |
| ~~**Feature: Featured jobs**~~ | ~~`/jobs`, `/admin/jobs`~~ | ✅ **DONE**: Added `is_featured` field to Job model with migration, admin toggle button in `/admin/jobs`, featured jobs section on `/jobs` page with star badge styling. |
| ~~**Feature: Featured blog entries**~~ | ~~`/blogs`, `/admin/blogs`~~ | ✅ **DONE**: `is_featured` field already existed in BlogEntry, admin toggle in `/admin/blogs/entries`, featured section on `/blogs` page (shows when no feed filter active). |

### LOW Priority
| Issue | Location | Description |
|-------|----------|-------------|
| ~~**`/admin/events` default sort order**~~ | `/admin/events` | ✅ DONE - Already sorted by created_at DESC (newest first). |
| ~~**`/admin/jobs` preview modal UX**~~ | `/admin/jobs` | ✅ DONE - Fixed Location bug, added icons, improved layout. |
| ~~**`/admin/events` metadata columns**~~ | `/admin/events` | ✅ DONE - Added date added and last modified to event rows. |
| ~~**`/admin/blogs` search button layout**~~ | `/admin/blogs` | ✅ DONE - Used DaisyUI `join` class for inline search button. |
| ~~**SITEWIDE: Pagination first/last buttons**~~ | All paginated views | ✅ DONE - Added First/Last buttons to all 15 paginated templates. |
| ~~**SITEWIDE: Normalize page header sizes**~~ | All pages | ✅ DONE - Standardized: text-5xl (index), text-4xl (detail), text-3xl (admin). |
| ~~**`/community/posts` UX overhaul**~~ | `/community/posts` | ✅ DONE - New template with hero, featured posts, pagination, sidebar. |

---

## Planned Enhancements

| Enhancement | Priority | Description |
|-------------|----------|-------------|
| **Job auto-submit on creation** | LOW | Add `submit_immediately` flag to `create_job()` |
| **Investigate litestar-workflows** | MEDIUM | For job/event approval workflows |
| **Calendar detail pagination UI/UX** | LOW | Enhance with page dropdown, "Go to page" input |

---

## Tier Priority Summary

### Tier 3: MEDIUM (Enhanced Features) - Remaining
| Task | Effort | Description |
|------|--------|-------------|
| OAuth2 Providers Testing | Medium | GitHub/Google providers exist, need full testing |

### Tier 4: LOW (Nice to Have)
| Task | Effort | Description |
|------|--------|-------------|
| ~~CDN Integration (Fastly)~~ | ~~Medium~~ | ✅ Surrogate-Key middleware done |
| ~~GPG Signature Verification~~ | ~~Low~~ | ✅ SHA256, signature UI, verification info |
| ~~Recurrence Rules~~ | ~~Medium~~ | ✅ dateutil.rrule for events, 29 tests |
| ~~Calendar RSS/Atom~~ | ~~Low~~ | ✅ RSS 2.0 + Atom 1.0 feeds, 21 tests |
| Developer Documentation | Medium | ARCHITECTURE.md, deployment guide |
| ~~Contract Management~~ | ~~Medium~~ | ✅ Full sponsor contract workflow, 24 tests |
| ~~Template Refactor~~ | ~~Medium~~ | ✅ Moved 50 templates to domain folders, multi-directory support |

---

## Development Workflow

### Quick Start
```bash
# Option 1: tmux (best)
make dev-tmux && tmux attach -t pydotorg

# Option 2: Multiple terminals
make dev        # Starts infra
make serve      # Terminal 1: Web server
make worker     # Terminal 2: SAQ worker
make css-watch  # Terminal 3: TailwindCSS
```

### Database (Litestar CLI)
```bash
make litestar-db-upgrade     # Apply migrations
make litestar-db-make        # Create migration
make litestar-db-history     # Show history
```

### Frontend (Litestar Vite)
```bash
make assets-install          # Install deps
make assets-serve            # Vite dev server
make assets-build            # Production build
```

### Tests
```bash
make test                    # Unit tests
make test-integration        # Integration tests
make ci                      # Full CI pipeline
```

---

*Last updated: 2025-12-13*

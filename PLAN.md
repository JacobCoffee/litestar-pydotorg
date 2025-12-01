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
- [ ] **Page caching** (Redis) - Task 3.3
- [ ] **GPG signature verification** for downloads - Task 3.4
- [ ] **Feed refresh SAQ task** for blogs - Task 3.5
- [ ] **Job expiration SAQ task** - Task 3.6
- [ ] **Email notifications** for jobs - Task 3.6
- [ ] **Recurrence rule engine** (dateutil.rrule) for events - Task 3.7
- [ ] **Calendar feed** (RSS/Atom) for events - Task 3.7
- [ ] **Contract management** workflow for sponsors - Task 3.8
- [ ] **Annual sponsorship renewal** - Task 3.8

### API Enhancements
- [ ] **API versioning** - paths use /api/v1 but no version negotiation
- [ ] **API keys** - JWT auth only, no API key support

### Infrastructure
- [ ] **Fastly CDN** - cache purging, surrogate keys, health monitoring
- [ ] **Notification emails** - job/event notifications not wired

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
- [ ] **`/about/help`** - FAQ/Help page with common questions, getting started resources
- [ ] **`/about/apps`** - Python applications showcase (notable apps built with Python)
- [ ] **`/about/quotes`** - Testimonials and quotes from Python users/companies
- [ ] **`/about/gettingstarted`** - Beginner's guide to Python, installation, first steps
- [ ] **`/about/legal`** - Legal information, trademarks, licensing

#### Downloads Section
- [ ] **`/downloads/alternatives`** - Alternative Python implementations (PyPy, Jython, IronPython, etc.)
- [ ] **`/downloads/other`** - Other download resources (source tarballs, older versions, etc.)

#### Community Section
- [ ] **`/community/irc`** - IRC channels information (#python, #python-dev, etc.)
- [ ] **`/community/forums`** - Python forums (Discourse, Reddit, etc.)
- [ ] **`/community/lists`** - Mailing lists directory (python-list, python-dev, python-ideas, etc.)

#### PSF Section
- [ ] **`/psf/about`** - About the Python Software Foundation
- [ ] **`/psf/conduct`** - Code of Conduct (community guidelines, reporting)
- [ ] **`/psf/get-involved`** - How to contribute to Python/PSF
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
| **`/blogs` sidebar feed filters** | `/blogs` | Clicking feed links refreshes page instead of filtering. |
| **`/events` filters don't filter** | `/events` | Filter UI exists but doesn't filter listings. |
| **`/psf/membership` not implemented** | `/psf/membership` | Shows "not available yet". |
| **`/community/workshops` not implemented** | `/community/workshops` | Shows "not available yet". |
| ~~**Feature: Sitewide announcement banner**~~ | ~~Sitewide~~ | ✅ **DONE**: Full banner system with targeting (`frontend`/`api`), path filtering, toast notifications. Admin UI at `/admin/banners`. API banners via `X-API-Notice` header. Persists across HTMX navigation. |
| **Feature: Featured jobs** | `/jobs`, `/admin/jobs` | Add `is_featured` field, admin toggle, featured section. |
| **Feature: Featured blog entries** | `/blogs`, `/admin/blogs` | Add `is_featured` field, admin toggle, featured section. |

### LOW Priority
| Issue | Location | Description |
|-------|----------|-------------|
| **`/admin/events` default sort order** | `/admin/events` | Sorts oldest first; should sort newest first. |
| **`/admin/jobs` preview modal UX** | `/admin/jobs` | "Location: NoneRemote" bug, plain text layout, needs redesign. |
| **`/admin/events` metadata columns** | `/admin/events` | Need date added, submitted by, last modified columns. |
| **`/admin/blogs` search button layout** | `/admin/blogs` | Button under input instead of inline. |
| **SITEWIDE: Pagination first/last buttons** | All paginated views | Only Previous/Next, need First/Last. |
| **SITEWIDE: Normalize page header sizes** | All pages | Inconsistent header sizes. |
| **`/community/posts` UX overhaul** | `/community/posts` | Needs complete redesign. |

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
| CDN Integration (Fastly) | Medium | Cache purging, surrogate keys |
| GPG Signature Verification | Low | Download file integrity |
| Recurrence Rules | Medium | dateutil.rrule for events |
| Calendar RSS/Atom | Low | Event feed |
| Developer Documentation | Medium | ARCHITECTURE.md, deployment guide |
| Contract Management | Medium | Full sponsor contract workflow |
| Template Refactor | Medium | Move templates into domain folders |

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

*Last updated: 2025-12-01*

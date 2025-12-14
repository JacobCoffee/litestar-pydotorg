:orphan:

# Architecture Documentation

Welcome to the Litestar Python.org architecture documentation. This directory contains all architectural decisions, design documents, and technical specifications for migrating python.org from Django to Litestar.

## Quick Links

- [Main Architecture Document](./ARCHITECTURE.md) - Comprehensive architecture overview
- [Quick Start Guide](./QUICK_START.md) - Get started developing quickly
- [Database Schema](./DATABASE_SCHEMA.md) - Detailed database design
- Architecture Decision Records - See ADRs below documenting key decisions

## Document Index

### Core Architecture

| Document | Description | Status |
|----------|-------------|--------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Complete system architecture | Current |
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | Database design and models | Current |
| [QUICK_START.md](./QUICK_START.md) | Developer quick start guide | Current |

### Architecture Decision Records (ADRs)

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./adr/001-litestar-framework.md) | Use Litestar as Web Framework | Accepted | 2025-11-25 |
| [ADR-002](./adr/002-saq-background-tasks.md) | Use SAQ for Background Tasks | Accepted | 2025-11-25 |
| [Template](./adr/template.md) | ADR Template | - | - |

## Architecture at a Glance

### Technology Stack

```
┌─────────────────────────────────────────────────────┐
│                   Presentation                       │
│  Jinja2 Templates │ Static Assets │ CDN (Fastly)    │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                   Application                        │
│  Litestar 2.x │ Controllers │ Services │ DTOs       │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                   Data Access                        │
│  SQLAlchemy 2.0 │ Advanced Alchemy │ Alembic        │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                   Infrastructure                     │
│  PostgreSQL │ Redis │ SAQ │ Meilisearch             │
└─────────────────────────────────────────────────────┘
```

### Domain Organization

The application is organized into **17 domain modules**, each representing a business capability:

**Core Domains**:
- `users` - User authentication, profiles, membership
- `pages` - CMS flat pages
- `cms` - Base CMS functionality

**Content Domains**:
- `downloads` - Python releases and downloads
- `events` - Community events and calendars
- `blogs` - Blog feed aggregation
- `boxes` - Reusable content widgets

**Community Domains**:
- `jobs` - Job board
- `community` - Community posts and media
- `successstories` - Success story content
- `sponsors` - Sponsorship management

**Organization Domains**:
- `nominations` - PSF nominations
- `minutes` - Board meeting minutes
- `work_groups` - PSF working groups

**Support Domains**:
- `banners` - Site banners
- `codesamples` - Code examples
- `companies` - Company directory
- `mailing` - Mailing list integration

### Key Design Principles

1. **Async First**: All I/O operations use async/await
2. **Type Safe**: Full type hints with Pydantic validation
3. **Domain Driven**: Clear domain boundaries with minimal coupling
4. **Dependency Injection**: Leveraging Litestar's DI system
5. **API Centric**: REST API with automatic OpenAPI docs
6. **Test Driven**: Comprehensive test coverage at all levels
7. **Cloud Native**: Container-ready with proper health checks

## Migration Strategy

### Phased Approach

```
Phase 1: Foundation (Weeks 1-2)
  ├─ Project setup
  ├─ Core infrastructure
  └─ Testing framework

Phase 2: Core Domains (Weeks 3-5)
  ├─ users
  ├─ cms
  ├─ pages
  └─ downloads

Phase 3: Feature Domains (Weeks 6-9)
  ├─ events
  ├─ jobs
  ├─ community
  └─ sponsors

Phase 4: Templates & Frontend (Weeks 10-11)
  └─ Django → Jinja2 conversion

Phase 5: Background Tasks (Week 12)
  └─ Celery → SAQ migration

Phase 6: Testing & Optimization (Weeks 13-14)
  └─ Load testing, optimization

Phase 7: Deployment (Weeks 15-16)
  └─ Production rollout
```

### Success Criteria

- All Django functionality replicated
- API response time < 100ms (p95)
- Throughput > 10,000 requests/second
- Zero downtime deployment
- 90%+ test coverage
- All security audits passed

## Key Architectural Patterns

### 1. Domain Module Pattern

Each domain follows a consistent structure:

```
domains/example/
├── __init__.py
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas
├── services.py         # Business logic
├── controllers.py      # HTTP handlers
├── repositories.py     # Data access (optional)
├── dependencies.py     # Domain-specific DI
└── guards.py           # Domain-specific guards
```

### 2. Service Layer Pattern

Business logic is encapsulated in service classes:

```python
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, data: UserCreate) -> User:
        # Validation, business logic, persistence
        ...
```

### 3. Repository Pattern (When Needed)

Complex data access is abstracted:

```python
class ReleaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_by_version(self, version: int) -> Release | None:
        # Complex query logic
        ...
```

### 4. DTO Pattern

Data transfer between layers uses Pydantic schemas:

```python
class ReleaseRead(BaseModel):
    """Output schema for API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_latest: bool

class ReleaseCreate(BaseModel):
    """Input schema for creation."""
    name: str = Field(..., min_length=1)
    version: int = Field(..., ge=1, le=3)
```

## Development Guidelines

### Code Organization

- **One class per file** for models, services, controllers
- **Flat module structure** within domains
- **Explicit imports** - no `from module import *`
- **Type hints everywhere** - use mypy strict mode

### Testing Strategy

```
tests/
├── unit/              # Fast, isolated tests
│   └── domains/
│       └── users/
│           ├── test_models.py
│           ├── test_services.py
│           └── test_schemas.py
├── integration/       # Database, API tests
│   └── domains/
│       └── users/
│           ├── test_controllers.py
│           └── test_repositories.py
└── e2e/              # Full user journey tests
    └── test_user_registration.py
```

### Git Workflow

1. Create feature branch: `feature/domain-feature`
2. Implement with tests
3. Run quality checks: `ruff check`, `mypy`, `pytest`
4. Create PR with description
5. Pass CI checks
6. Get review approval
7. Squash and merge

## Performance Targets

### Response Times

| Endpoint Type | Target (p95) | Target (p99) |
|---------------|--------------|--------------|
| Simple GET | < 50ms | < 100ms |
| Complex GET | < 100ms | < 200ms |
| POST/PUT | < 100ms | < 250ms |
| Background Task | < 1s | < 5s |

### Throughput

- **API endpoints**: 10,000+ req/s
- **Static assets**: 50,000+ req/s (via CDN)
- **Database queries**: < 10ms average
- **Cache hit ratio**: > 90%

### Scalability

- **Horizontal scaling**: Stateless application servers
- **Database**: Read replicas for scaling reads
- **Cache**: Redis cluster for distributed cache
- **Tasks**: Multiple SAQ workers

## Security Considerations

### OWASP Top 10 Coverage

1. **Injection**: Parameterized queries (SQLAlchemy)
2. **Broken Authentication**: Token-based auth with secure hashing
3. **Sensitive Data Exposure**: HTTPS, encrypted at rest
4. **XML External Entities**: Not applicable (JSON API)
5. **Broken Access Control**: Route guards and permissions
6. **Security Misconfiguration**: Security headers, CSP
7. **XSS**: Template auto-escaping, Content-Type headers
8. **Insecure Deserialization**: Pydantic validation
9. **Known Vulnerabilities**: Automated dependency scanning
10. **Insufficient Logging**: Structured logging, audit trails

### Security Headers

- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Content-Security-Policy`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Monitoring & Observability

### Metrics

- **Application**: Request rate, latency, error rate
- **Database**: Query time, connection pool usage
- **Cache**: Hit ratio, eviction rate
- **Tasks**: Queue length, processing time, failure rate

### Logging

- **Structured logging** with JSON format
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation IDs** for request tracing
- **Sensitive data masking**

### Tracing

- Distributed tracing with OpenTelemetry
- Span correlation across services
- Performance bottleneck identification

## Deployment Architecture

### Container Strategy

```dockerfile
# Multi-stage build
FROM python:3.12-slim as builder
# ... build dependencies

FROM python:3.12-slim
# ... runtime
```

### Orchestration

- **Development**: Docker Compose
- **Production**: Kubernetes
- **Health checks**: `/health` endpoint
- **Graceful shutdown**: 30s timeout

### CI/CD Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   Lint   │ -> │   Test   │ -> │  Build   │ -> │  Deploy  │
│  (Ruff)  │    │ (Pytest) │    │ (Docker) │    │   (K8s)  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Contributing to Architecture

### Proposing Changes

1. Identify need for architectural decision
2. Research alternatives
3. Draft ADR using [template](./adr/template.md)
4. Discuss with team
5. Update ADR based on feedback
6. Get approval and mark as "Accepted"
7. Update relevant documentation

### Updating Documentation

- Keep documentation in sync with code
- Update diagrams when structure changes
- Version control all architecture documents
- Regular architecture reviews (quarterly)

## Resources

### External Documentation

- [Litestar Docs](https://docs.litestar.dev/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
- [Advanced Alchemy Docs](https://docs.advanced-alchemy.litestar.dev/)
- [Pydantic V2 Docs](https://docs.pydantic.dev/)
- [SAQ Docs](https://saq-py.readthedocs.io/)

### Internal Resources

- Project Wiki: `https://github.com/python/litestar-pydotorg/wiki`
- Team Slack: `#pydotorg-litestar`
- Mailing List: `pydotorg-www@python.org`
- Weekly Sync: Wednesdays 10am PT

## Frequently Asked Questions

### Q: Why Litestar over FastAPI?

**A**: See [ADR-001](./adr/001-litestar-framework.md). In summary: better SQLAlchemy integration, superior dependency injection, and more opinionated structure for large applications.

### Q: How do we handle Django's signals?

**A**: Use SQLAlchemy event listeners or domain events pattern. Example:

```python
from sqlalchemy import event

@event.listens_for(Release, 'after_insert')
def after_release_insert(mapper, connection, target):
    # Trigger cache update
    ...
```

### Q: What about Django's admin interface?

**A**: We'll build a custom admin using Litestar Admin or similar. The Django admin is tightly coupled to Django ORM and not easily portable.

### Q: How do we migrate data?

**A**: See migration scripts in `/scripts/`. We'll run parallel databases during transition, sync data, then cut over with minimal downtime.

### Q: What about existing Django templates?

**A**: Convert to Jinja2 (very similar syntax). Most templates require minimal changes. See [QUICK_START.md](./QUICK_START.md) for details.

### Q: How do we handle file uploads?

**A**: Litestar has built-in file upload support. For large files, we'll use direct-to-S3 uploads with pre-signed URLs.

### Q: What's the testing strategy?

**A**: Comprehensive testing at all levels:
- Unit tests for models, services, schemas
- Integration tests for controllers, repositories
- E2E tests for critical user journeys
- Target: 90%+ coverage

## Glossary

- **ADR**: Architecture Decision Record - documents architectural choices
- **ASGI**: Async Server Gateway Interface - async version of WSGI
- **DTO**: Data Transfer Object - object for transferring data between layers
- **DI**: Dependency Injection - pattern for managing dependencies
- **ORM**: Object-Relational Mapping - database abstraction layer
- **SAQ**: Simple Async Queue - async task queue library

---

## Document Metadata

- **Last Updated**: 2025-11-25
- **Maintained By**: Python.org Architecture Team
- **Review Cycle**: Quarterly
- **Next Review**: 2026-02-25

---

**Location**: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/architecture/README.md`

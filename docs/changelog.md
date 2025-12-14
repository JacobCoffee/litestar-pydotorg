# Changelog

All notable changes to the litestar-pydotorg project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Complete Litestar-based rewrite of python.org
- 17 domain modules migrated from Django
- Async SQLAlchemy 2.0 with Advanced-Alchemy
- Jinja2 templates replacing Django templates
- Tailwind CSS + DaisyUI for styling
- SAQ background task processing (31 tasks, 7 cron jobs)
- Comprehensive authentication (JWT, sessions, OAuth2)
- Full OpenAPI documentation
- MeiliSearch integration for search
- Rate limiting and API key authentication
- Admin interface with SQLAdmin

### Changed

- Framework: Django → Litestar
- ORM: Django ORM → SQLAlchemy 2.0
- Task Queue: Celery → SAQ
- Templates: Django Templates → Jinja2
- CSS: Bootstrap → Tailwind + DaisyUI

### Technical Details

- Python 3.12+ required
- PostgreSQL 15+ for database
- Redis 7+ for cache and task queue
- Full type hints throughout codebase
- 90%+ test coverage target

## [0.1.0] - 2025-01-01

### Added

- Initial project scaffolding
- Core infrastructure setup
- Development environment configuration

[Unreleased]: https://github.com/JacobCoffee/litestar-pydotorg/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JacobCoffee/litestar-pydotorg/releases/tag/v0.1.0

# Architecture

System design, domain models, database schema, and architectural decision records for litestar-pydotorg.

## Overview

The application is built on a domain-driven architecture with 17 business domains, each encapsulating related models, services, and controllers. This section documents the system design decisions and technical specifications.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} System Architecture
:link: ARCHITECTURE
:link-type: doc

Complete system architecture, technology stack, and design patterns.
:::

:::{grid-item-card} Database Schema
:link: DATABASE_SCHEMA
:link-type: doc

Database design, entity relationships, and migration strategy.
:::

:::{grid-item-card} Domain Models
:link: DOMAIN_MODELS
:link-type: doc

Comprehensive reference for all 17 domain models.
:::

:::{grid-item-card} Quick Start
:link: QUICK_START
:link-type: doc

Developer quick start for architecture navigation.
:::
::::

## Architecture Decision Records

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](adr/001-litestar-framework.md) | Use Litestar as Web Framework | Accepted |
| [ADR-002](adr/002-saq-background-tasks.md) | Use SAQ for Background Tasks | Accepted |

## API Documentation

- [API Tags Index](API_TAGS_INDEX.md) - Complete API tag reference
- [API Tags Structure](API_TAGS_STRUCTURE.md) - Tag organization and hierarchy
- [API Tags Best Practices](API_TAGS_BEST_PRACTICES.md) - Guidelines for API tagging
- [Rate Limiting](RATE_LIMITING_ARCHITECTURE.md) - Rate limiting design and configuration

```{toctree}
:maxdepth: 2
:hidden:

ARCHITECTURE
DATABASE_SCHEMA
DOMAIN_MODELS
QUICK_START
API_TAGS_INDEX
RATE_LIMITING_ARCHITECTURE
adr/001-litestar-framework
adr/002-saq-background-tasks
```

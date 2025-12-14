# Getting Started

Welcome to litestar-pydotorg! This section will help you get up and running quickly with the Python.org rewrite built on the Litestar framework.

## What is litestar-pydotorg?

litestar-pydotorg is a modern rewrite of the Python.org website, migrating from Django to Litestar. It features:

- **Litestar Framework** - Modern, high-performance ASGI web framework
- **SQLAlchemy 2.0** - Async ORM with Advanced-Alchemy integration
- **Jinja2 Templates** - Server-side rendering with powerful templating
- **Tailwind CSS + DaisyUI** - Modern utility-first CSS framework
- **SAQ** - Background task processing with Redis
- **Comprehensive Auth** - JWT and session-based authentication

## Quick Navigation

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: installation
:link-type: doc

Get the project installed and configured on your local machine.
:::

:::{grid-item-card} Quickstart
:link: quickstart
:link-type: doc

Build and run your first local instance in 5 minutes.
:::
::::

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - The language of choice
- **PostgreSQL 15+** - Primary database
- **Redis 7+** - Cache and task queue backend
- **uv** - Fast Python package manager
- **Git** - Version control
- **Docker** (optional) - For containerized development

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 2 GB free | 10+ GB free |
| OS | Linux, macOS, Windows (WSL2) | Linux, macOS |

## Next Steps

1. Follow the [Installation Guide](installation.md) to set up your development environment
2. Complete the [Quickstart](quickstart.md) to run your first local instance
3. Explore the [Architecture](../architecture/ARCHITECTURE.md) to understand the codebase
4. Check out the [Guides](../guides/index.md) for common development tasks


# litestar-pydotorg

```{rst-class} lead
Python.org rebuilt with [Litestar](https://litestar.dev/) - A modern, high-performance rewrite featuring Jinja2 templates and Tailwind CSS/DaisyUI.
```

---

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} {octicon}`rocket` Getting Started
:link: getting-started/index
:link-type: doc
:class-card: sd-border-0

Install, configure, and run your first local instance in minutes.
:::

:::{grid-item-card} {octicon}`book` Guides
:link: guides/index
:link-type: doc
:class-card: sd-border-0

Development workflows, testing, deployment, and best practices.
:::

:::{grid-item-card} {octicon}`code` API Reference
:link: api/index
:link-type: doc
:class-card: sd-border-0

Complete SDK documentation for all modules, classes, and functions.
:::

:::{grid-item-card} {octicon}`server` Architecture
:link: architecture/ARCHITECTURE
:link-type: doc
:class-card: sd-border-0

System design, domain models, database schema, and ADRs.
:::

:::{grid-item-card} {octicon}`mortar-board` Cookbook
:link: cookbook/index
:link-type: doc
:class-card: sd-border-0

Real-world recipes and patterns for common development tasks.
:::

::::

---

## Key Features

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} Litestar Framework
:class-card: sd-border-0

Modern, high-performance ASGI framework with first-class OpenAPI support.
:::

:::{grid-item-card} SQLAlchemy 2.0
:class-card: sd-border-0

Async ORM with Advanced-Alchemy integration, migrations, and repositories.
:::

:::{grid-item-card} 17 Domain Modules
:class-card: sd-border-0

Users, downloads, events, jobs, sponsors, blogs, and more - all implemented.
:::

:::{grid-item-card} Tailwind + DaisyUI
:class-card: sd-border-0

Modern utility-first CSS with pre-built components and Vite HMR.
:::

:::{grid-item-card} SAQ Background Tasks
:class-card: sd-border-0

31 async tasks and 7 cron jobs for cache, email, search, and more.
:::

:::{grid-item-card} Comprehensive Auth
:class-card: sd-border-0

JWT tokens, session auth, OAuth2 (GitHub/Google), and API keys.
:::

::::

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/JacobCoffee/litestar-pydotorg.git
cd litestar-pydotorg
make install

# Start infrastructure and run
make infra-up
make litestar-db-upgrade
make serve
```

The application will be available at:
- **UI**: http://127.0.0.1:8000/
- **API Docs**: http://127.0.0.1:8000/api/
- **Admin**: http://127.0.0.1:8000/admin/

---

## Development

```bash
# Run all CI checks (lint + type-check + test)
make ci

# Individual commands
make lint         # Ruff linting
make fmt          # Ruff formatting
make type-check   # ty type checking
make test         # pytest with coverage
```

---

```{toctree}
:maxdepth: 1
:caption: Getting Started
:hidden:

getting-started/index
getting-started/installation
getting-started/quickstart
```

```{toctree}
:maxdepth: 1
:caption: Guides
:hidden:

guides/development
guides/api-usage
guides/authentication
guides/testing
guides/configuration
guides/deployment
guides/troubleshooting
```

```{toctree}
:maxdepth: 1
:caption: Cookbook
:hidden:

cookbook/domain-patterns
cookbook/authentication-recipes
cookbook/database-recipes
cookbook/testing-recipes
```

```{toctree}
:maxdepth: 1
:caption: Architecture
:hidden:

architecture/ARCHITECTURE
architecture/DATABASE_SCHEMA
architecture/DOMAIN_MODELS
```

```{toctree}
:maxdepth: 1
:caption: API Reference
:hidden:

api/index
api-getting-started
api-authentication
```

```{toctree}
:maxdepth: 1
:caption: Resources
:hidden:

guides/contributing
POSTMAN_GUIDE
architecture/adr/001-litestar-framework
architecture/adr/002-saq-background-tasks
```

---

## Links

- [GitHub Repository](https://github.com/JacobCoffee/litestar-pydotorg)
- [Litestar Documentation](https://docs.litestar.dev/)
- [Python.org](https://python.org/)

---

## Indices and Tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`

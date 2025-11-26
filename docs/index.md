# litestar-pydotorg

Python.org rebuilt with [Litestar](https://litestar.dev/).

A modern rewrite of the Python.org website using the Litestar framework, featuring Jinja2 templates and Tailwind CSS/DaisyUI.

```{toctree}
:maxdepth: 2
:caption: Getting Started
:hidden:

architecture/README
architecture/QUICK_START
```

```{toctree}
:maxdepth: 2
:caption: Architecture
:hidden:

architecture/ARCHITECTURE
architecture/DATABASE_SCHEMA
```

```{toctree}
:maxdepth: 2
:caption: ADRs
:hidden:

architecture/adr/001-litestar-framework
architecture/adr/002-saq-background-tasks
```

```{toctree}
:maxdepth: 1
:caption: Development
:hidden:

changelog
```

## Features

- **Litestar Framework**: Modern, high-performance ASGI framework
- **SQLAlchemy 2.0**: Async ORM with Advanced-Alchemy integration
- **Jinja2 Templates**: Server-side rendering with powerful templating
- **Tailwind CSS + DaisyUI**: Modern utility-first CSS framework
- **SAQ**: Background task processing with Redis
- **Comprehensive Auth**: JWT-based authentication system

## Quick Start

```bash
# Clone the repository
git clone https://github.com/JacobCoffee/litestar-pydotorg.git
cd litestar-pydotorg

# Install dependencies
make install

# Start infrastructure (PostgreSQL, Redis)
make infra-up

# Run migrations
make db-migrate

# Start development server
make serve
```

## Development

```bash
# Run all CI checks
make ci

# Individual checks
make lint         # Run linter
make fmt          # Format code
make type-check   # Type checking
make test         # Run tests
```

## Links

- [GitHub Repository](https://github.com/JacobCoffee/litestar-pydotorg)
- [Litestar Documentation](https://docs.litestar.dev/)
- [Python.org](https://python.org/)

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
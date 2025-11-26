# Litestar Python.org

A modern reimplementation of [python.org](https://www.python.org) using [Litestar](https://litestar.dev).

## Overview

This project rebuilds the Python.org website using modern Python technologies:

- **Framework**: Litestar 2.x
- **ORM**: SQLAlchemy 2.0 with async support via Advanced Alchemy
- **Database**: PostgreSQL (asyncpg)
- **Templates**: Jinja2
- **Background Tasks**: SAQ
- **Package Manager**: uv
- **UI**: TailwindCSS, HTMX, AlpineJS, DaisyUI

## Quick Start

```bash
# Install dependencies
make install

# Run development server
make serve

# Run tests
make test

# Run all CI checks
make ci
```

## Development

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- uv (Python package manager)

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `make install`
4. Run `make db-migrate`
5. Run `make serve`

### Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make serve         # Run development server
make test          # Run tests
make lint          # Run linter
make fmt           # Format code
make type-check    # Run type checker
make ci            # Run all CI checks
```

### Git Workflow

```bash
# Create a feature branch worktree
make worktree NAME=feature-name

# List worktrees
make worktree-list

# Remove worktree
make worktree-remove NAME=feature-name
```

## Architecture

```
src/pydotorg/
├── main.py              # Application entry point
├── config.py            # Settings configuration
├── core/                # Infrastructure layer
│   ├── auth/            # Authentication
│   ├── database/        # SQLAlchemy config
│   ├── middleware/      # Custom middleware
│   └── security/        # Security utilities
├── domains/             # Domain modules
│   ├── users/           # User management
│   ├── pages/           # CMS pages
│   ├── downloads/       # Python releases
│   ├── events/          # Event calendar
│   ├── jobs/            # Job board
│   ├── sponsors/        # Sponsorship system
│   └── ...
├── lib/                 # Shared utilities
├── tasks/               # Background tasks
└── templates/           # Jinja2 templates
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

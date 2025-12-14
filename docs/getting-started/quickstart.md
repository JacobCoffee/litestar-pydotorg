# Quickstart

Get up and running with litestar-pydotorg in 5 minutes. This guide assumes you have completed the [Installation](installation.md) steps.

## TL;DR

```bash
# Clone and setup
git clone https://github.com/JacobCoffee/litestar-pydotorg.git
cd litestar-pydotorg
make install

# Start infrastructure
make infra-up

# Run migrations
make litestar-db-upgrade

# Start server
make serve
```

Visit [http://localhost:8000](http://localhost:8000)

## Step-by-Step Guide

### 1. Start Infrastructure

Start the required services (PostgreSQL and Redis):

```bash
make infra-up
```

Wait for services to be healthy:

```bash
docker-compose ps
```

### 2. Run Migrations

Apply database migrations:

```bash
make litestar-db-upgrade
```

### 3. Start the Development Server

```bash
make serve
```

The server starts with hot-reload enabled at [http://localhost:8000](http://localhost:8000).

### 4. Explore the Application

Open your browser and visit:

| URL | Description |
|-----|-------------|
| [http://localhost:8000](http://localhost:8000) | Main application |
| [http://localhost:8000/api/](http://localhost:8000/api/) | API documentation (Scalar) |
| [http://localhost:8000/api/swagger](http://localhost:8000/api/swagger) | Swagger UI |
| [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc) | ReDoc documentation |
| [http://localhost:8000/health](http://localhost:8000/health) | Health check endpoint |

### 5. Frontend Development

In a separate terminal, start the frontend asset watcher:

```bash
make frontend
```

This enables hot module replacement (HMR) for CSS and JavaScript changes.

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
uv run pytest tests/unit/domains/users/test_models.py -v
```

### Code Quality

```bash
# Run all CI checks (lint, type-check, test)
make ci

# Individual checks
make lint        # Ruff linting
make fmt         # Ruff formatting
make type-check  # Type checking with ty
```

### Database Operations

```bash
# Create new migration from model changes
make litestar-db-make

# Apply migrations
make litestar-db-upgrade

# Rollback one migration
make litestar-db-downgrade

# Show migration history
make litestar-db-history

# Seed development data
make db-seed
```

## Project Structure

```
litestar-pydotorg/
├── src/pydotorg/          # Main application code
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration
│   ├── core/              # Core infrastructure (auth, db, etc.)
│   ├── domains/           # Business domains
│   │   ├── users/         # User management
│   │   ├── pages/         # CMS pages
│   │   ├── downloads/     # Python releases
│   │   ├── jobs/          # Job board
│   │   ├── events/        # Community events
│   │   └── ...            # Other domains
│   ├── lib/               # Shared utilities
│   └── tasks/             # Background tasks
├── templates/             # Jinja2 templates
├── static/                # Static assets
├── migrations/            # Alembic migrations
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Making Your First Change

### 1. Create a New Route

Add a simple endpoint to test your setup:

```python
# src/pydotorg/domains/pages/controllers.py

from litestar import get

@get("/hello")
async def hello_world() -> dict[str, str]:
    """A simple hello world endpoint."""
    return {"message": "Hello from litestar-pydotorg!"}
```

### 2. Create a Template

```html
<!-- templates/hello.html -->
{% extends "base.html" %}

{% block content %}
<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Hello, World!</h1>
    <p>Welcome to litestar-pydotorg.</p>
</div>
{% endblock %}
```

### 3. Test Your Changes

```bash
# Run tests
make test

# Run linting
make lint

# Run all CI checks
make ci
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add hello world endpoint"
```

## Using the API

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

### Making Authenticated Requests

```bash
# Get current user (replace TOKEN with your access_token)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

### Python Example

```python
import httpx

# Login
response = httpx.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "testuser", "password": "SecurePass123!"}
)
tokens = response.json()

# Make authenticated request
response = httpx.post(
    "http://localhost:8000/api/auth/me",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
)
print(response.json())
```

## Common Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make serve` | Start development server |
| `make frontend` | Start frontend asset watcher |
| `make test` | Run test suite |
| `make ci` | Run all CI checks |
| `make lint` | Run linter |
| `make fmt` | Format code |
| `make type-check` | Run type checker |
| `make infra-up` | Start infrastructure services |
| `make infra-down` | Stop infrastructure services |
| `make litestar-db-upgrade` | Apply database migrations |
| `make litestar-db-make` | Create new migration |
| `make db-seed` | Seed development data |
| `make help` | Show all available commands |

## Next Steps

- Read the [Architecture Documentation](../architecture/ARCHITECTURE.md) to understand the codebase
- Check the [Development Guide](../guides/development.md) for coding standards
- Explore the [API Documentation](../api/index.md) for API usage
- Browse the [Cookbook](../cookbook/index.md) for real-world recipes

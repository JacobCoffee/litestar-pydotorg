# Installation

This guide walks you through installing litestar-pydotorg for local development.

## Install uv

[uv](https://github.com/astral-sh/uv) is a fast Python package manager that we use for dependency management.

::::{tab-set}

:::{tab-item} macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
:::

:::{tab-item} Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
:::

:::{tab-item} Homebrew
```bash
brew install uv
```
:::

::::

Verify the installation:

```bash
uv --version
```

## Clone the Repository

```bash
git clone https://github.com/JacobCoffee/litestar-pydotorg.git
cd litestar-pydotorg
```

## Set Up Python Environment

Create and activate a virtual environment:

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
# Install all dependencies (production + development)
uv pip install -e ".[dev]"
```

Or use the Makefile:

```bash
make install
```

## Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your local settings. At minimum, configure:

```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg

# Redis connection
REDIS_URL=redis://localhost:6379/0

# Secret key (generate a secure one)
SECRET_KEY=your-secure-secret-key-here

# Debug mode (enable for development)
DEBUG=true
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Start Infrastructure Services

### Option 1: Docker Compose (Recommended)

Start PostgreSQL and Redis using Docker Compose:

```bash
# Start all infrastructure services
make infra-up

# Or manually:
docker-compose up -d postgres redis
```

Verify services are running:

```bash
docker-compose ps
```

### Option 2: Local Installation

If you prefer to install services locally:

#### PostgreSQL

::::{tab-set}

:::{tab-item} macOS (Homebrew)
```bash
brew install postgresql@15
brew services start postgresql@15
createdb pydotorg
```
:::

:::{tab-item} Ubuntu/Debian
```bash
sudo apt install postgresql-15
sudo systemctl start postgresql
sudo -u postgres createdb pydotorg
```
:::

::::

#### Redis

::::{tab-set}

:::{tab-item} macOS (Homebrew)
```bash
brew install redis
brew services start redis
```
:::

:::{tab-item} Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl start redis
```
:::

::::

## Database Setup

Run database migrations:

```bash
# Using Makefile
make litestar-db-upgrade

# Or directly with Litestar CLI
LITESTAR_APP=pydotorg.main:app uv run litestar database upgrade
```

Optionally seed development data:

```bash
make db-seed
```

## Verify Installation

Start the development server:

```bash
make serve

# Or directly:
LITESTAR_APP=pydotorg.main:app uv run litestar run --reload
```

Visit [http://localhost:8000](http://localhost:8000) in your browser.

Check the API documentation at:
- **Scalar UI**: [http://localhost:8000/api/](http://localhost:8000/api/)
- **Swagger UI**: [http://localhost:8000/api/swagger](http://localhost:8000/api/swagger)
- **ReDoc**: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

## Frontend Assets

Install frontend dependencies and start the asset watcher:

```bash
# Install frontend dependencies
make assets-install

# Start Vite dev server with hot module replacement
make assets-serve
```

Or in a separate terminal while the backend is running:

```bash
make frontend
```

## Common Issues

### Database Connection Failed

Ensure PostgreSQL is running and the connection string is correct:

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Redis Connection Failed

Verify Redis is running:

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -u $REDIS_URL ping
```

### Import Errors

Reinstall dependencies:

```bash
uv pip install -e ".[dev]" --force-reinstall

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### Port Already in Use

If port 8000 is in use:

```bash
# Find the process using the port
lsof -i :8000

# Use a different port
LITESTAR_APP=pydotorg.main:app uv run litestar run --port 8001
```

## Next Steps

- Continue to the [Quickstart](quickstart.md) to start developing
- Read the [Architecture Overview](../architecture/ARCHITECTURE.md) to understand the codebase structure
- Check the [Development Guide](../guides/development.md) for coding standards and workflows

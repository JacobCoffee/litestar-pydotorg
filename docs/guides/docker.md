# Docker Guide

This guide covers using Docker for development and deployment of litestar-pydotorg.

## Development Setup

### Quick Start with Docker Compose

```bash
# Start all services (PostgreSQL, Redis)
make infra-up

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
make infra-down
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: pydotorg-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: pydotorg
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: pydotorg-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  meilisearch:
    image: getmeili/meilisearch:v1.5
    container_name: pydotorg-meilisearch
    ports:
      - "7700:7700"
    environment:
      MEILI_MASTER_KEY: your-master-key
    volumes:
      - meilisearch_data:/meili_data

volumes:
  postgres_data:
  redis_data:
  meilisearch_data:
```

## Managing Containers

### Basic Commands

```bash
# Start services in background
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# Stop all services
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v

# Restart a service
docker-compose restart postgres

# View logs
docker-compose logs postgres
docker-compose logs -f  # Follow logs
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d pydotorg

# Create a database backup
docker-compose exec postgres pg_dump -U postgres pydotorg > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres pydotorg < backup.sql
```

### Redis Operations

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Flush all data (development only!)
docker-compose exec redis redis-cli FLUSHALL
```

## Building the Application Image

### Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install --system -e ".[dev]"

# Copy application code
COPY . .

# Run development server
CMD ["litestar", "run", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system -e "."

FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV LITESTAR_APP=pydotorg.main:app

CMD ["litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
```

### Building Images

```bash
# Build development image
docker build -f Dockerfile.dev -t pydotorg:dev .

# Build production image
docker build -t pydotorg:latest .

# Build with specific tag
docker build -t pydotorg:v1.0.0 .
```

## Full Docker Development

### Complete Docker Compose Stack

```yaml
# docker-compose.full.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: pydotorg-web
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from mount
    environment:
      - DEBUG=true
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/pydotorg
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: litestar run --reload --host 0.0.0.0 --port 8000

  worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: pydotorg-worker
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/pydotorg
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: python -m saq worker pydotorg.tasks.base.worker

  postgres:
    image: postgres:15
    container_name: pydotorg-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: pydotorg
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: pydotorg-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Running Full Stack

```bash
# Start full stack
docker-compose -f docker-compose.full.yml up

# Start in background
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose -f docker-compose.full.yml logs -f web

# Run migrations
docker-compose -f docker-compose.full.yml exec web litestar database upgrade

# Run tests inside container
docker-compose -f docker-compose.full.yml exec web pytest
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Check container status
docker-compose ps

# Inspect container
docker inspect pydotorg-web
```

### Database Connection Issues

```bash
# Verify postgres is running
docker-compose ps postgres

# Test connection from host
psql postgresql://postgres:postgres@localhost:5432/pydotorg -c "SELECT 1"

# Test connection from web container
docker-compose exec web python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@postgres:5432/pydotorg')
print('Connected!' if engine.connect() else 'Failed')
"
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Use different port
docker-compose up -d -e "PORT=8001"
```

### Clean Up

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove unused volumes (data loss!)
docker volume prune

# Full cleanup
docker system prune -a
```

## Best Practices

1. **Use health checks** - Always define health checks for production
2. **Non-root user** - Run containers as non-root user
3. **Multi-stage builds** - Keep production images small
4. **Pin versions** - Use specific image tags, not `latest`
5. **Volume data** - Use volumes for persistent data
6. **Environment variables** - Never hardcode secrets
7. **Resource limits** - Set memory and CPU limits

## See Also

- [Deployment Guide](deployment.md) - Production deployment
- [Configuration Guide](configuration.md) - Environment configuration

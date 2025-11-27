# Docker Setup Guide

This guide covers Docker-based development and deployment workflows for litestar-pydotorg.

## Quick Start

### Development (Recommended)

Start the full development environment with hot-reload:

```bash
# Build and start all services
make docker-up

# Follow logs
make docker-logs

# Stop services
make docker-down
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Litestar app with hot-reload (port 8000)
- SAQ background worker

### Infrastructure Only

If you prefer running the app locally but need database/redis:

```bash
# Start only PostgreSQL and Redis
make infra-up

# Run app locally
make serve

# Stop infrastructure
make infra-down
```

## Docker Profiles

The `docker-compose.yml` uses profiles to control which services start:

### `dev` Profile (Default Development)
```bash
docker compose --profile dev up -d
```
Services: postgres, redis, app, worker

### `full` Profile (Development + Search)
```bash
docker compose --profile full up -d
# or
make docker-full
```
Services: postgres, redis, app, worker, meilisearch

## Available Make Commands

### Development
- `make docker-up` - Start dev stack (app + worker + infra)
- `make docker-down` - Stop all services
- `make docker-logs` - Follow logs
- `make docker-build` - Build Docker images
- `make docker-rebuild` - Rebuild without cache
- `make docker-shell` - Open shell in app container

### Infrastructure Only
- `make infra-up` - Start PostgreSQL and Redis only
- `make infra-down` - Stop infrastructure
- `make infra-logs` - Follow infra logs
- `make infra-reset` - Reset database (delete volumes)

### Full Stack
- `make docker-full` - Start with Meilisearch
- `make docker-reset` - Remove all containers and volumes

### Production
- `make docker-prod-up` - Start production stack (requires .env.prod)
- `make docker-prod-down` - Stop production stack

## Environment Configuration

### Development (.env.docker)
Copy the example and customize:
```bash
cp .env.docker.example .env.docker
```

Development defaults are already configured in `docker-compose.yml`:
- `DATABASE_URL`: postgresql+asyncpg://postgres:postgres@postgres:5432/pydotorg
- `REDIS_URL`: redis://redis:6379/0
- Hot-reload enabled
- Debug mode on

### Production (.env.prod)
Copy the example and set production secrets:
```bash
cp .env.docker.example .env.prod
```

**Required variables** (will fail without these):
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `SESSION_SECRET_KEY`
- `CSRF_SECRET`
- `OAUTH_REDIRECT_BASE_URL`
- `MEILI_MASTER_KEY` (if using search)

## Dockerfiles

### `Dockerfile` (Production)
Multi-stage build optimized for production:
- Uses `uv` for dependency management
- Compiles bytecode for faster startup
- Non-root user (app:app)
- No dev dependencies
- Granian with 4 workers

### `Dockerfile.dev` (Development)
Development-optimized build:
- Includes dev dependencies
- Hot-reload enabled
- Mounts source code as volumes
- Single Granian worker with --reload

## Port Mappings

| Service      | Port  | Access                    |
|--------------|-------|---------------------------|
| PostgreSQL   | 5432  | localhost:5432            |
| Redis        | 6379  | localhost:6379            |
| App          | 8000  | http://localhost:8000     |
| Meilisearch  | 7700  | http://localhost:7700     |

## Volume Mounts (Development)

The dev setup mounts source code for hot-reload:
```yaml
volumes:
  - ./src:/app/src:ro                                    # Source code
  - ./src/pydotorg/templates:/app/src/pydotorg/templates:ro  # Templates
  - ./static:/app/static:ro                              # Static files
```

Changes to these directories trigger automatic reload.

## Production Deployment

### Docker Compose

1. Create `.env.prod` with production secrets
2. Build production images:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml build
   ```
3. Start services:
   ```bash
   make docker-prod-up
   ```

### Docker Swarm

The production override includes deploy configuration for Docker Swarm:

```bash
docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml pydotorg
```

Features:
- **2 replicas** for app and worker (high availability)
- **Resource limits**: CPU and memory constraints
- **Health checks**: Automatic restart on failure
- **Rolling updates**: Zero-downtime deployments
- **Automatic rollback**: On deployment failure

### Kubernetes

Convert to Kubernetes manifests using Kompose:
```bash
kompose convert -f docker-compose.yml -f docker-compose.prod.yml
```

## Troubleshooting

### Build Fails
```bash
# Clear build cache and rebuild
make docker-rebuild
```

### Database Connection Issues
```bash
# Check PostgreSQL is healthy
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Reset database
make infra-reset
```

### Hot-Reload Not Working
Ensure volumes are mounted correctly:
```bash
docker compose --profile dev config | grep volumes -A 5
```

### Permission Issues
The production image runs as non-root user `app:app` (UID 1000). Ensure mounted volumes have correct permissions.

### Memory Issues
Increase Docker Desktop memory allocation:
- Docker Desktop > Settings > Resources > Memory: 4GB+

## Advanced Usage

### Custom Build Args
```bash
docker compose build --build-arg PYTHON_VERSION=3.13
```

### Override Environment Variables
```bash
DATABASE_URL=postgresql://custom:url@host/db docker compose --profile dev up
```

### Run Database Migrations
```bash
docker exec -it pydotorg-app uv run alembic upgrade head
```

### Access Django Admin Shell
```bash
docker exec -it pydotorg-app uv run python -i -c "from pydotorg.main import app"
```

### Backup Database
```bash
docker exec pydotorg-postgres pg_dump -U postgres pydotorg > backup.sql
```

### Restore Database
```bash
docker exec -i pydotorg-postgres psql -U postgres pydotorg < backup.sql
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Build Docker Image
  run: docker compose build

- name: Run Tests in Container
  run: docker compose run --rm app uv run pytest

- name: Push to Registry
  run: |
    docker tag pydotorg:latest ghcr.io/jacobcoffee/litestar-pydotorg:latest
    docker push ghcr.io/jacobcoffee/litestar-pydotorg:latest
```

## Resource Usage

### Development
- **app**: ~300MB RAM, 0.5 CPU
- **worker**: ~200MB RAM, 0.25 CPU
- **postgres**: ~100MB RAM
- **redis**: ~30MB RAM

### Production (per replica)
- **app**: 512MB-2GB RAM, 0.5-2.0 CPU
- **worker**: 256MB-1GB RAM, 0.25-1.0 CPU

## Security Considerations

1. **Never commit** `.env.prod` or `.env.docker`
2. **Change all secrets** in production (SECRET_KEY, passwords, etc.)
3. **Use Docker secrets** for sensitive data in Swarm/Kubernetes
4. **Keep images updated**: `docker compose pull` regularly
5. **Scan for vulnerabilities**: `docker scout cve <image>`

## Performance Optimization

### Build Cache
```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
```

### Multi-Stage Builds
The production Dockerfile uses multi-stage builds to minimize image size:
- Builder stage: ~800MB
- Final image: ~400MB (50% reduction)

### Layer Caching
Dependencies are installed before copying source code to maximize cache hits.

## Support

For issues or questions:
- GitHub Issues: https://github.com/JacobCoffee/litestar-pydotorg/issues
- Litestar Discord: https://discord.gg/litestar

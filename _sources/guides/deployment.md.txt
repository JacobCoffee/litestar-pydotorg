# Deployment Guide

This guide covers deploying litestar-pydotorg from local development through to production.

## Prerequisites

Before deploying, ensure you have:

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.13+ | Runtime |
| PostgreSQL | 16+ | Database |
| Redis | 7+ | Cache, sessions, task queue |
| Docker | 24+ | Containerization (optional) |
| uv | Latest | Python package manager |
| Bun | Latest | Frontend build (or Node.js 20+) |

### Required Accounts (Production)

- **GitHub/Google OAuth**: For social authentication
- **SendGrid/SMTP Provider**: For transactional emails
- **Fastly CDN** (optional): For edge caching and CDN
- **Container Registry**: For Docker image storage (GitHub Container Registry, Docker Hub, etc.)

---

## Development Setup

### Local Development (Recommended for Active Development)

1. **Clone and Install**

   ```bash
   git clone https://github.com/JacobCoffee/litestar-pydotorg.git
   cd litestar-pydotorg

   # Install Python dependencies
   make install

   # Install frontend dependencies
   make assets-install
   ```

2. **Configure Environment**

   ```bash
   cp .env.dev.example .env.dev
   ```

   The default development configuration works out of the box with local PostgreSQL and Redis.

3. **Start Infrastructure**

   ```bash
   # Start PostgreSQL and Redis containers
   make infra-up
   ```

4. **Initialize Database**

   ```bash
   # Run migrations
   make litestar-db-upgrade

   # Seed with development data
   make db-seed
   ```

5. **Start Development Servers**

   Option A - Separate terminals:
   ```bash
   # Terminal 1: Litestar API server with hot-reload
   make serve

   # Terminal 2: SAQ background worker
   make worker

   # Terminal 3: TailwindCSS watcher (optional)
   make css-watch
   ```

   Option B - tmux (recommended):
   ```bash
   make dev-tmux
   # Attach with: tmux attach -t pydotorg
   ```

6. **Verify Installation**

   - Application: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs
   - Admin Panel: http://localhost:8000/admin
   - MailDev (email): http://localhost:1080

### Docker Development

For a fully containerized development experience:

```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Litestar app with hot-reload (port 8000)
- SAQ background worker
- MailDev for email testing (ports 1025/1080)

#### Docker Profiles

```bash
# Development profile (default)
docker compose --profile dev up -d

# Full profile (includes Meilisearch for search)
docker compose --profile full up -d
# or
make docker-full
```

---

## Environment Configuration

### Environment Variables Reference

#### Core Settings

| Variable | Description | Default | Required in Prod |
|----------|-------------|---------|-----------------|
| `APP_ENV` | Environment (`dev`, `staging`, `prod`) | `dev` | Yes |
| `SECRET_KEY` | Application secret (32+ chars) | - | Yes |
| `DEBUG` | Enable debug mode | `true` in dev | No (auto-set) |

#### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg` |
| `DATABASE_POOL_SIZE` | Connection pool size | `20` |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | `10` |

#### Redis

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

#### Security

| Variable | Description | Required in Prod |
|----------|-------------|-----------------|
| `SESSION_SECRET_KEY` | Session encryption key (32+ chars) | Yes |
| `CSRF_SECRET` | CSRF token secret (32+ chars) | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm | No (`HS256`) |
| `JWT_EXPIRATION_MINUTES` | JWT token lifetime | No (`10080`) |

#### OAuth

| Variable | Description |
|----------|-------------|
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `OAUTH_REDIRECT_BASE_URL` | OAuth callback base URL |

#### Email (SMTP)

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `localhost` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `SMTP_FROM_EMAIL` | Sender email address | `noreply@python.org` |
| `SMTP_FROM_NAME` | Sender display name | `Python.org` |
| `SMTP_USE_TLS` | Enable TLS | `true` |

#### Search (Meilisearch)

| Variable | Description | Default |
|----------|-------------|---------|
| `MEILISEARCH_URL` | Meilisearch server URL | `http://127.0.0.1:7700` |
| `MEILISEARCH_API_KEY` | Meilisearch API key | - |
| `MEILISEARCH_INDEX_PREFIX` | Index name prefix | `pydotorg_` |

#### CDN (Fastly)

| Variable | Description |
|----------|-------------|
| `FASTLY_API_KEY` | Fastly API key for cache invalidation |

### Generating Secrets

Generate secure secrets for production:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32

# Using uv
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Generate multiple secrets at once:

```bash
echo "SECRET_KEY=$(openssl rand -base64 32)"
echo "SESSION_SECRET_KEY=$(openssl rand -base64 32)"
echo "CSRF_SECRET=$(openssl rand -base64 32)"
```

---

## Production Deployment

### Docker Compose Production

1. **Create Production Environment File**

   ```bash
   cp .env.prod.example .env.prod
   ```

   Edit `.env.prod` with production values:

   ```bash
   # Required - change these!
   APP_ENV=prod
   SECRET_KEY=<generate-secure-key>
   SESSION_SECRET_KEY=<generate-secure-key>
   CSRF_SECRET=<generate-secure-key>

   # Database
   DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@db.example.com:5432/pydotorg
   DATABASE_POOL_SIZE=40
   DATABASE_MAX_OVERFLOW=20

   # Redis
   REDIS_URL=redis://redis.example.com:6379/0

   # OAuth (production URLs)
   OAUTH_REDIRECT_BASE_URL=https://www.python.org
   GITHUB_CLIENT_ID=your-production-client-id
   GITHUB_CLIENT_SECRET=your-production-client-secret

   # Email
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   ```

2. **Build Production Image**

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml build
   ```

3. **Start Production Stack**

   ```bash
   make docker-prod-up
   # or
   docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile dev up -d
   ```

4. **Run Migrations**

   ```bash
   docker exec pydotorg-app alembic upgrade head
   ```

### Production Dockerfile

The production `Dockerfile` uses a multi-stage build:

1. **Frontend Builder**: Compiles Vite/TailwindCSS assets using Bun
2. **Python Builder**: Installs dependencies with uv (no dev deps)
3. **Runtime**: Minimal image with compiled bytecode

Key features:
- Non-root user (`appuser:appuser`, UID 1000)
- Compiled Python bytecode for faster startup
- 4 Granian workers by default
- Health check endpoint monitoring
- Approximately 400MB final image size

### Database Setup

#### PostgreSQL Configuration

Recommended production settings in `postgresql.conf`:

```ini
# Connection settings
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 6GB

# Write-ahead logging
wal_level = replica
max_wal_senders = 3

# Query optimization
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

#### Running Migrations

```bash
# Using Litestar CLI (preferred)
LITESTAR_APP=pydotorg.main:app uv run litestar database upgrade

# Using Alembic directly
uv run alembic upgrade head

# In Docker
docker exec pydotorg-app alembic upgrade head
```

### Redis Configuration

Production Redis settings in `redis.conf`:

```ini
# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Memory management
maxmemory 1gb
maxmemory-policy allkeys-lru

# Security
requirepass your-redis-password
protected-mode yes

# Logging
loglevel warning
```

### Background Worker (SAQ)

The SAQ worker handles asynchronous tasks:

- Email sending
- Feed synchronization
- Search indexing
- Cache warming
- Event reminders
- Job expiration

#### Running the Worker

```bash
# Local
make worker
# or
uv run saq pydotorg.tasks.worker.saq_settings

# Docker
docker compose up worker -d

# Multiple workers for high volume
docker compose up --scale worker=3 -d
```

#### Cron Jobs

The worker includes scheduled tasks:

| Task | Schedule | Description |
|------|----------|-------------|
| `cron_refresh_feeds` | Every 15 min | Refresh blog feeds |
| `cron_event_reminders` | Daily | Send event reminders |
| `cron_expire_jobs` | Daily | Expire old job listings |
| `cron_rebuild_indexes` | Weekly | Rebuild search indexes |
| `cron_warm_homepage_cache` | Every 5 min | Warm homepage cache |
| `cron_sync_events` | Every 6 hours | Sync external events |
| `cron_sync_news` | Every hour | Sync news feeds |

### Reverse Proxy Configuration

#### Nginx

```nginx
upstream pydotorg {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name python.org www.python.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name python.org www.python.org;

    ssl_certificate /etc/letsencrypt/live/python.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/python.org/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # Static files (if not using CDN)
    location /static/ {
        alias /var/www/pydotorg/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check (no logging)
    location = /health {
        proxy_pass http://pydotorg;
        access_log off;
    }

    # Application
    location / {
        proxy_pass http://pydotorg;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 32k;
    }
}
```

#### Caddy

```text
python.org, www.python.org {
    # Static files
    handle /static/* {
        root * /var/www/pydotorg
        file_server
        header Cache-Control "public, max-age=31536000, immutable"
    }

    # Health check
    handle /health {
        reverse_proxy localhost:8000
        log {
            output discard
        }
    }

    # Application
    handle {
        reverse_proxy localhost:8000 {
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Security headers
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }

    # Compression
    encode gzip

    # Logging
    log {
        output file /var/log/caddy/pydotorg.log {
            roll_size 100mb
            roll_keep 5
        }
    }
}
```

---

## Kubernetes Deployment

### Convert Docker Compose to Kubernetes

```bash
# Using Kompose
kompose convert -f docker-compose.yml -f docker-compose.prod.yml

# This generates:
# - app-deployment.yaml
# - app-service.yaml
# - worker-deployment.yaml
# - postgres-deployment.yaml
# - redis-deployment.yaml
# - configmaps and secrets
```

### Kubernetes Manifests

#### Deployment

```yaml
# k8s/app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pydotorg-app
  labels:
    app: pydotorg
    component: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pydotorg
      component: app
  template:
    metadata:
      labels:
        app: pydotorg
        component: app
    spec:
      containers:
      - name: app
        image: ghcr.io/jacobcoffee/litestar-pydotorg:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: pydotorg-secrets
        - configMapRef:
            name: pydotorg-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service

```yaml
# k8s/app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: pydotorg-app
spec:
  selector:
    app: pydotorg
    component: app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pydotorg-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - python.org
    - www.python.org
    secretName: pydotorg-tls
  rules:
  - host: python.org
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pydotorg-app
            port:
              number: 80
```

#### ConfigMap and Secret

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pydotorg-config
data:
  APP_ENV: "prod"
  DATABASE_POOL_SIZE: "40"
  SMTP_HOST: "smtp.sendgrid.net"
  SMTP_PORT: "587"

---
# k8s/secret.yaml (use sealed-secrets or external-secrets in production)
apiVersion: v1
kind: Secret
metadata:
  name: pydotorg-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  SESSION_SECRET_KEY: "your-session-secret"
  CSRF_SECRET: "your-csrf-secret"
  DATABASE_URL: "postgresql+asyncpg://..."
  REDIS_URL: "redis://..."
```

#### Worker Deployment

```yaml
# k8s/worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pydotorg-worker
  labels:
    app: pydotorg
    component: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pydotorg
      component: worker
  template:
    metadata:
      labels:
        app: pydotorg
        component: worker
    spec:
      containers:
      - name: worker
        image: ghcr.io/jacobcoffee/litestar-pydotorg:latest
        command: ["saq", "pydotorg.tasks.worker.saq_settings"]
        envFrom:
        - secretRef:
            name: pydotorg-secrets
        - configMapRef:
            name: pydotorg-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Helm Chart (Optional)

For more complex deployments, consider creating a Helm chart:

```bash
helm create pydotorg
```

---

## Health Checks

### Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Application health | `{"status": "healthy", "database": true}` |

### Health Check Response

```json
{
  "status": "healthy",
  "database": true
}
```

Unhealthy response (HTTP 503):

```json
{
  "status": "unhealthy",
  "database": false,
  "error": "Connection refused"
}
```

### Docker Health Check

The production Dockerfile includes:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

### External Monitoring

Configure uptime monitoring services to check:

1. `https://python.org/health` - Primary health check
2. `https://python.org/` - Homepage renders
3. `https://python.org/api/docs` - API documentation loads

---

## Monitoring and Logging

### Structured Logging

The application uses structlog for structured JSON logging in production:

```python
# Production log format (JSON)
{
  "event": "Request completed",
  "level": "info",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "abc123",
  "method": "GET",
  "path": "/",
  "status_code": 200,
  "duration_ms": 45
}
```

### Log Aggregation

Configure log shipping to your preferred platform:

#### Docker Logging

```yaml
# docker-compose.prod.yml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
```

#### Loki/Grafana Stack

```yaml
# docker-compose.monitoring.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Prometheus Metrics

For Prometheus integration, add to the application:

```python
# Custom metrics endpoint (if needed)
@get("/metrics", exclude_from_auth=True)
async def metrics() -> str:
    return generate_prometheus_metrics()
```

### Application Insights

Key metrics to monitor:

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| Response time (p95) | > 500ms | Application latency |
| Error rate | > 1% | HTTP 5xx responses |
| Database connections | > 80% pool | Connection pool usage |
| Memory usage | > 80% | Container memory |
| CPU usage | > 70% sustained | Container CPU |
| Queue depth | > 1000 | SAQ pending tasks |

---

## Backup and Restore

### Database Backup

#### Automated Backups

```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pydotorg_${DATE}.sql.gz"

# Create backup
docker exec pydotorg-postgres pg_dump -U postgres pydotorg | gzip > "$BACKUP_FILE"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_FILE" s3://your-bucket/backups/

# Retain only last 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

#### Manual Backup

```bash
# Plain SQL
docker exec pydotorg-postgres pg_dump -U postgres pydotorg > backup.sql

# Compressed
docker exec pydotorg-postgres pg_dump -U postgres pydotorg | gzip > backup.sql.gz

# Custom format (parallel restore)
docker exec pydotorg-postgres pg_dump -U postgres -Fc pydotorg > backup.dump
```

### Database Restore

```bash
# From SQL file
docker exec -i pydotorg-postgres psql -U postgres pydotorg < backup.sql

# From gzip
gunzip -c backup.sql.gz | docker exec -i pydotorg-postgres psql -U postgres pydotorg

# From custom format
docker exec -i pydotorg-postgres pg_restore -U postgres -d pydotorg < backup.dump
```

### Redis Backup

Redis data persists via RDB snapshots and AOF:

```bash
# Manual backup
docker exec pydotorg-redis redis-cli BGSAVE

# Copy dump file
docker cp pydotorg-redis:/data/dump.rdb ./redis-backup.rdb
```

### Media Files Backup

```bash
# Backup uploads/media directory
tar -czvf media-backup.tar.gz /path/to/media/

# Sync to S3
aws s3 sync /path/to/media/ s3://your-bucket/media/ --delete
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```
DATABASE CONNECTION FAILED
Connection refused
```

Solution:
```bash
# Check PostgreSQL is running
docker compose ps postgres
docker compose logs postgres

# Start PostgreSQL
make infra-up
```

#### Migration Errors

```
alembic.util.exc.CommandError: Can't locate revision
```

Solution:
```bash
# Show current state
make litestar-db-current
make litestar-db-history

# Reset if needed (development only)
make db-reset
```

#### Worker Not Processing Tasks

```bash
# Check worker status
docker compose logs worker

# Verify Redis connection
docker exec pydotorg-redis redis-cli ping

# Check queue status
docker exec pydotorg-app python -c "
from saq import Queue
from pydotorg.config import settings
import asyncio

async def check():
    q = Queue.from_url(settings.redis_url)
    print(await q.stats())

asyncio.run(check())
"
```

#### Out of Memory

```bash
# Check container memory
docker stats pydotorg-app

# Increase limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G
```

### Debug Mode

Enable debug logging temporarily:

```bash
# Set log level
PYDOTORG_LOG_LEVEL=DEBUG make serve

# Or in Docker
docker compose run -e DEBUG=true -e PYDOTORG_LOG_LEVEL=DEBUG app
```

### Performance Profiling

```bash
# Run with profiling
uv run python -m cProfile -o profile.stats -m granian ...

# Analyze results
uv run python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

---

## Security Checklist

Before deploying to production:

- [ ] All secrets are unique, secure (32+ characters), and not defaults
- [ ] `APP_ENV=prod` is set
- [ ] `DEBUG=false` or unset (auto-disabled in prod)
- [ ] Database uses non-default credentials
- [ ] Database is not accessible from public internet
- [ ] Redis has password authentication
- [ ] HTTPS is enforced via reverse proxy
- [ ] Security headers are configured
- [ ] CORS is restricted to allowed origins
- [ ] OAuth redirect URLs are production URLs
- [ ] Email credentials are production SMTP
- [ ] Container runs as non-root user
- [ ] No sensitive data in logs
- [ ] `.env.prod` is NOT committed to git
- [ ] Firewall rules restrict access to internal services

---

## Quick Reference

### Make Commands

```bash
# Development
make install          # Install dependencies
make serve            # Run development server
make worker           # Run SAQ worker
make infra-up         # Start PostgreSQL + Redis

# Docker
make docker-up        # Start dev stack
make docker-prod-up   # Start production stack
make docker-logs      # View logs

# Database
make litestar-db-upgrade  # Run migrations
make litestar-db-make     # Create migration
make db-seed              # Seed data

# Quality
make ci               # Run all checks
make test             # Run tests
```

### Port Reference

| Service | Port | Development | Production |
|---------|------|-------------|------------|
| Litestar App | 8000 | Exposed | Internal only |
| PostgreSQL | 5432 | Exposed | Internal only |
| Redis | 6379 | Exposed | Internal only |
| Meilisearch | 7700 | Exposed | Internal only |
| MailDev | 1080 | Exposed | N/A |

### Resource Requirements

| Component | Development | Production (min) | Production (recommended) |
|-----------|-------------|------------------|--------------------------|
| App | 512MB / 0.5 CPU | 1GB / 1 CPU | 2GB / 2 CPU |
| Worker | 256MB / 0.25 CPU | 512MB / 0.5 CPU | 1GB / 1 CPU |
| PostgreSQL | 256MB | 1GB | 4GB+ |
| Redis | 64MB | 256MB | 1GB |
| Meilisearch | 256MB | 512MB | 1GB+ |

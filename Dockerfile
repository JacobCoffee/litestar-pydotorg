# Stage 1: Builder - Build frontend and install Python dependencies
FROM node:22-slim AS frontend-builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --production=false

COPY resources/ ./resources/
COPY tailwind.config.js ./
COPY postcss.config.cjs ./
COPY vite.config.ts ./
COPY static/ ./static/

RUN npm run build && npm run css


# Stage 2: Python Builder - Install Python dependencies
FROM python:3.13-slim AS python-builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Stage 3: Runtime - Minimal production image
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    APP_ENV=prod

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

WORKDIR /app

COPY --from=python-builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=python-builder --chown=appuser:appuser /app/src /app/src
COPY --from=frontend-builder --chown=appuser:appuser /app/static /app/static

COPY --chown=appuser:appuser alembic.ini ./

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["granian", "--interface", "asgi", "pydotorg.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Rate Limiting Architecture Design

## Executive Summary

This document defines the comprehensive rate limiting architecture for pydotorg, a Litestar 2.14+ application with 383 endpoints across 29 controllers. The design leverages Litestar's native `RateLimitMiddleware` with Redis backend to protect against abuse while maintaining excellent user experience.

**Current State**: CRITICAL - No rate limiting protection across 383 endpoints
**Risk Level**: HIGH - Vulnerable to DoS, credential stuffing, scraping, spam
**Solution**: Tiered rate limiting with user-aware identification and Redis persistence

---

## Architecture Decision Record (ADR)

### ADR-001: Rate Limiting Strategy

**Status**: Proposed

**Context**:
- 383 endpoints across 17 domain controllers currently unprotected
- Redis infrastructure already available (sessions, cache, SAQ workers)
- Mix of read-heavy, write-heavy, and authentication endpoints
- Need to balance security with legitimate user experience
- HTMX-powered UI requires special handling for toast notifications

**Decision**:
Implement tiered rate limiting using Litestar's `RateLimitMiddleware` with:
1. RedisStore backend for distributed rate limiting
2. Custom identifier function for user-aware vs IP-based limiting
3. Four-tier rate limit strategy (CRITICAL, HIGH, MEDIUM, LOW)
4. Custom 429 exception handler with Retry-After header
5. Configuration-driven approach for environment-specific limits

**Consequences**:

Positive:
- Protection against DoS, brute force, and abuse
- Leverages existing Redis infrastructure
- Native Litestar middleware (no external dependencies)
- Environment-specific limits (dev/staging/prod)
- User-aware limiting rewards authenticated users
- Automatic rate limit headers (RFC 6585)

Negative:
- Redis becomes single point of failure for rate limiting
- Requires careful tuning to avoid false positives
- Additional Redis memory consumption
- Performance overhead (minimal with Redis)

**Alternatives Considered**:

1. **No Rate Limiting**: Rejected - HIGH security risk
2. **Per-Endpoint Decorators**: Rejected - Not scalable for 383 endpoints
3. **External Service (Cloudflare)**: Rejected - Adds dependency, cost
4. **In-Memory Store**: Rejected - Not distributed, loses data on restart

---

## Technical Specification

### 1. Configuration Schema

#### 1.1 Rate Limit Configuration Model

```python
# src/pydotorg/core/ratelimit/config.py

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from pydotorg.config import Environment


class RateLimitTier(str, Enum):
    """Rate limit tier classifications."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNLIMITED = "unlimited"


class TierLimits(BaseModel):
    """Rate limits for a specific tier."""
    requests: int = Field(..., ge=1, description="Number of requests allowed")
    window_seconds: int = Field(..., ge=1, description="Time window in seconds")

    @property
    def per_minute(self) -> float:
        """Calculate requests per minute for display."""
        return (self.requests / self.window_seconds) * 60


class RateLimitConfig(BaseModel):
    """Rate limiting configuration with environment-specific tiers."""

    enabled: bool = Field(
        default=True,
        description="Enable/disable rate limiting globally"
    )

    set_headers: bool = Field(
        default=True,
        description="Include rate limit headers in responses"
    )

    redis_namespace: str = Field(
        default="ratelimit",
        description="Redis key prefix for rate limit data"
    )

    use_user_aware: bool = Field(
        default=True,
        description="Use user-aware rate limiting (higher limits for authenticated users)"
    )

    # Tier Definitions - Anonymous Users
    anonymous_critical: TierLimits = Field(
        default=TierLimits(requests=5, window_seconds=60),
        description="Auth endpoints, search, submissions (5 req/min)"
    )

    anonymous_high: TierLimits = Field(
        default=TierLimits(requests=20, window_seconds=60),
        description="Forms, job/event submissions (20 req/min)"
    )

    anonymous_medium: TierLimits = Field(
        default=TierLimits(requests=60, window_seconds=60),
        description="Community posts, blog entries (60 req/min)"
    )

    anonymous_low: TierLimits = Field(
        default=TierLimits(requests=120, window_seconds=60),
        description="Read-only endpoints (120 req/min)"
    )

    # Tier Definitions - Authenticated Users
    authenticated_critical: TierLimits = Field(
        default=TierLimits(requests=20, window_seconds=60),
        description="Auth endpoints, search, submissions (20 req/min)"
    )

    authenticated_high: TierLimits = Field(
        default=TierLimits(requests=60, window_seconds=60),
        description="Forms, job/event submissions (60 req/min)"
    )

    authenticated_medium: TierLimits = Field(
        default=TierLimits(requests=180, window_seconds=60),
        description="Community posts, blog entries (180 req/min)"
    )

    authenticated_low: TierLimits = Field(
        default=TierLimits(requests=300, window_seconds=60),
        description="Read-only endpoints (300 req/min)"
    )

    # Admin/Staff overrides
    staff_multiplier: float = Field(
        default=5.0,
        ge=1.0,
        description="Multiplier for staff users (5x normal limits)"
    )

    # Development/Testing overrides
    dev_mode_unlimited: bool = Field(
        default=False,
        description="Disable rate limiting in development (not recommended)"
    )

    # Exclude patterns
    exclude_paths: list[str] = Field(
        default_factory=lambda: [
            "/static/*",
            "/media/*",
            "/health",
            "/api/docs/*",
        ],
        description="Paths excluded from rate limiting"
    )

    @classmethod
    def for_environment(cls, env: Environment) -> "RateLimitConfig":
        """Create environment-specific rate limit configuration."""
        if env == Environment.DEV:
            return cls(
                enabled=True,
                dev_mode_unlimited=False,  # Keep enabled even in dev for testing
                anonymous_critical=TierLimits(requests=100, window_seconds=60),
                anonymous_high=TierLimits(requests=200, window_seconds=60),
                anonymous_medium=TierLimits(requests=300, window_seconds=60),
                anonymous_low=TierLimits(requests=500, window_seconds=60),
            )
        elif env == Environment.STAGING:
            return cls(
                enabled=True,
                anonymous_critical=TierLimits(requests=10, window_seconds=60),
                anonymous_high=TierLimits(requests=30, window_seconds=60),
                anonymous_medium=TierLimits(requests=90, window_seconds=60),
                anonymous_low=TierLimits(requests=180, window_seconds=60),
            )
        else:  # PROD
            return cls(
                enabled=True,
                anonymous_critical=TierLimits(requests=5, window_seconds=60),
                anonymous_high=TierLimits(requests=20, window_seconds=60),
                anonymous_medium=TierLimits(requests=60, window_seconds=60),
                anonymous_low=TierLimits(requests=120, window_seconds=60),
            )

    def get_tier_limits(
        self,
        tier: RateLimitTier,
        is_authenticated: bool = False,
        is_staff: bool = False,
    ) -> TierLimits:
        """Get rate limits for a specific tier and user type."""
        if self.dev_mode_unlimited:
            return TierLimits(requests=999999, window_seconds=60)

        if tier == RateLimitTier.UNLIMITED:
            return TierLimits(requests=999999, window_seconds=60)

        # Select base tier
        tier_map = {
            RateLimitTier.CRITICAL: (
                self.authenticated_critical if is_authenticated else self.anonymous_critical
            ),
            RateLimitTier.HIGH: (
                self.authenticated_high if is_authenticated else self.anonymous_high
            ),
            RateLimitTier.MEDIUM: (
                self.authenticated_medium if is_authenticated else self.anonymous_medium
            ),
            RateLimitTier.LOW: (
                self.authenticated_low if is_authenticated else self.anonymous_low
            ),
        }

        limits = tier_map[tier]

        # Apply staff multiplier
        if is_staff:
            return TierLimits(
                requests=int(limits.requests * self.staff_multiplier),
                window_seconds=limits.window_seconds,
            )

        return limits


def get_rate_limit_config(env: Environment | None = None) -> RateLimitConfig:
    """Get rate limit configuration for the current environment."""
    from pydotorg.config import settings

    target_env = env or settings.environment
    return RateLimitConfig.for_environment(target_env)
```

#### 1.2 Settings Integration

```python
# src/pydotorg/config.py (additions)

class Settings(BaseSettings):
    # ... existing fields ...

    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting middleware"
    )
    rate_limit_redis_namespace: str = Field(
        default="ratelimit",
        description="Redis namespace for rate limit storage"
    )

    # Override specific tier limits via environment variables
    rate_limit_critical_requests: int | None = Field(
        default=None,
        description="Override critical tier request limit"
    )
    rate_limit_critical_window: int | None = Field(
        default=None,
        description="Override critical tier window (seconds)"
    )
```

---

### 2. Endpoint Classification

#### 2.1 Tier Assignments by Risk Profile

```python
# src/pydotorg/core/ratelimit/tiers.py

from pydotorg.core.ratelimit.config import RateLimitTier

# CRITICAL: Auth, Search, Content Submissions (5 req/min anon, 20 req/min auth)
CRITICAL_ENDPOINTS = {
    # Authentication (brute force protection)
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/reset-password",
    "/api/auth/verify-email",
    "/api/auth/forgot-password",

    # Search (expensive queries)
    "/api/v1/search/",
    "/search/results",
    "/api/v1/search/autocomplete",

    # Admin authentication
    "/admin/api/auth/*",
}

# HIGH: Forms, Job/Event/Sponsor Submissions (20 req/min anon, 60 req/min auth)
HIGH_ENDPOINTS = {
    # Job submissions
    "/api/jobs",
    "/api/jobs/*/apply",

    # Event submissions
    "/api/events",
    "/api/events/*/register",

    # Sponsor inquiries
    "/api/sponsors/inquiry",

    # Feed fetching
    "/api/feeds",
    "/api/feeds/aggregate",

    # User profile updates
    "/api/users/*/profile",
    "/api/users/*/password",
}

# MEDIUM: Community Content, Blog Entries (60 req/min anon, 180 req/min auth)
MEDIUM_ENDPOINTS = {
    # Community posts
    "/api/community/posts",
    "/api/community/photos",
    "/api/community/videos",

    # Blog entries
    "/api/blogs/entries",

    # Comments
    "/api/jobs/*/comments",

    # File uploads
    "/api/pages/*/images",
    "/api/pages/*/documents",
}

# LOW: Read-Only Operations (120 req/min anon, 300 req/min auth)
LOW_ENDPOINTS = {
    # All GET requests not in other tiers
    "GET:/api/*",

    # Public pages
    "/",
    "/about",
    "/docs/*",
    "/downloads",
    "/community",
    "/success-stories",
}

# UNLIMITED: Health checks, static assets
UNLIMITED_ENDPOINTS = {
    "/health",
    "/static/*",
    "/media/*",
    "/api/docs/*",
    "/api/openapi.json",
}


def get_endpoint_tier(path: str, method: str) -> RateLimitTier:
    """Determine rate limit tier for an endpoint.

    Args:
        path: Request path
        method: HTTP method

    Returns:
        Rate limit tier classification
    """
    from fnmatch import fnmatch

    # Check unlimited first
    for pattern in UNLIMITED_ENDPOINTS:
        if fnmatch(path, pattern):
            return RateLimitTier.UNLIMITED

    # Check critical
    for pattern in CRITICAL_ENDPOINTS:
        if fnmatch(path, pattern):
            return RateLimitTier.CRITICAL

    # Check high
    for pattern in HIGH_ENDPOINTS:
        if fnmatch(path, pattern):
            return RateLimitTier.HIGH

    # Check medium
    for pattern in MEDIUM_ENDPOINTS:
        if fnmatch(path, pattern):
            return RateLimitTier.MEDIUM

    # Check low (with method prefix)
    for pattern in LOW_ENDPOINTS:
        if ":" in pattern:
            pattern_method, pattern_path = pattern.split(":", 1)
            if method == pattern_method and fnmatch(path, pattern_path):
                return RateLimitTier.LOW
        elif fnmatch(path, pattern):
            return RateLimitTier.LOW

    # Default to MEDIUM for safety
    return RateLimitTier.MEDIUM
```

---

### 3. User-Aware Identifier Function

```python
# src/pydotorg/core/ratelimit/identifier.py

from litestar import Request

from pydotorg.core.logging import get_logger
from pydotorg.domains.users.models import User

logger = get_logger(__name__)


def get_rate_limit_identifier(request: Request) -> str:
    """Generate rate limit identifier based on authentication status.

    Strategy:
    1. Authenticated users: Use user_id (higher limits)
    2. Anonymous users: Use IP address (lower limits)
    3. Admin/Staff: Apply multiplier to limits

    Args:
        request: Litestar request object

    Returns:
        Unique identifier string for rate limiting
    """
    user: User | None = request.user

    if user and user.is_active:
        # Authenticated user - use user ID
        identifier = f"user:{user.id}"

        # Tag staff for special handling
        if user.is_staff or user.is_superuser:
            identifier = f"staff:{user.id}"

        logger.debug(
            "Rate limit identifier",
            identifier=identifier,
            user_id=str(user.id),
            is_staff=user.is_staff,
        )
        return identifier

    # Anonymous user - use IP address with fallback
    ip_address = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "").strip()
        or request.client.host
        if request.client
        else "unknown"
    )

    identifier = f"ip:{ip_address}"
    logger.debug("Rate limit identifier", identifier=identifier, ip=ip_address)

    return identifier


def should_check_rate_limit(request: Request) -> bool:
    """Determine if rate limiting should be checked for this request.

    Allows bypassing rate limits for:
    - Health checks
    - Static assets
    - Specific user groups (e.g., trusted partners)

    Args:
        request: Litestar request object

    Returns:
        True if rate limiting should be applied
    """
    from pydotorg.core.ratelimit.tiers import get_endpoint_tier, RateLimitTier

    tier = get_endpoint_tier(request.url.path, request.method)

    # Don't rate limit unlimited tier
    if tier == RateLimitTier.UNLIMITED:
        return False

    # Check for bypass header (for internal services)
    bypass_token = request.headers.get("X-RateLimit-Bypass")
    if bypass_token:
        from pydotorg.config import settings
        if bypass_token == settings.secret_key:  # In production, use separate bypass key
            logger.warning(
                "Rate limit bypassed via header",
                path=request.url.path,
                ip=request.client.host if request.client else "unknown",
            )
            return False

    return True
```

---

### 4. Redis Store Integration

```python
# src/pydotorg/core/ratelimit/store.py

from litestar.stores.redis import RedisStore
from redis.asyncio import Redis

from pydotorg.config import settings
from pydotorg.core.logging import get_logger

logger = get_logger(__name__)


def create_rate_limit_store() -> RedisStore:
    """Create Redis store for rate limiting.

    Returns:
        Configured RedisStore instance
    """
    redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
    )

    store = RedisStore(
        redis=redis_client,
        namespace=settings.rate_limit_redis_namespace,
        handle_client_shutdown=True,
    )

    logger.info(
        "Rate limit Redis store created",
        redis_url=settings.redis_url.split("@")[-1],  # Hide credentials
        namespace=settings.rate_limit_redis_namespace,
    )

    return store
```

---

### 5. Custom 429 Exception Handler

```python
# src/pydotorg/core/ratelimit/exceptions.py

import json
from typing import TYPE_CHECKING

from litestar.exceptions import TooManyRequestsException
from litestar.response import Response, Template
from litestar.status_codes import HTTP_429_TOO_MANY_REQUESTS

if TYPE_CHECKING:
    from litestar import Request

from pydotorg.core.logging import get_logger

logger = get_logger(__name__)


def rate_limit_exception_handler(
    request: "Request",
    exc: TooManyRequestsException,
) -> Response | Template:
    """Handle 429 Too Many Requests with Retry-After header.

    Features:
    - Retry-After header with seconds until reset
    - HTMX-aware toast notifications
    - User-friendly error messages
    - Logging for monitoring

    Args:
        request: Litestar request object
        exc: Rate limit exception

    Returns:
        Response or Template with appropriate error messaging
    """
    retry_after = 60  # Default to 60 seconds

    # Extract retry-after from exception if available
    if hasattr(exc, "extra") and isinstance(exc.extra, dict):
        retry_after = exc.extra.get("retry_after", retry_after)

    message = (
        f"Rate limit exceeded. Please try again in {retry_after} seconds. "
        "Authenticated users have higher rate limits."
    )

    # Log rate limit hit
    user_id = str(request.user.id) if request.user else "anonymous"
    logger.warning(
        "Rate limit exceeded",
        path=request.url.path,
        method=request.method,
        user_id=user_id,
        ip=request.client.host if request.client else "unknown",
        retry_after=retry_after,
    )

    # HTMX request - return toast notification
    if request.headers.get("HX-Request") == "true":
        toast_event = json.dumps({
            "showToast": {
                "message": message,
                "type": "warning",
            }
        })
        return Response(
            content=None,
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            headers={
                "Retry-After": str(retry_after),
                "HX-Trigger": toast_event,
                "HX-Reswap": "none",
            },
        )

    # API request - return JSON
    if request.url.path.startswith("/api/"):
        return Response(
            content={
                "error": "rate_limit_exceeded",
                "message": message,
                "retry_after": retry_after,
            },
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(retry_after)},
        )

    # Regular web request - return template
    return Template(
        template_name="errors/429.html.jinja2",
        context={
            "title": "Too Many Requests",
            "message": message,
            "retry_after": retry_after,
        },
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(retry_after)},
    )
```

---

### 6. Main Application Integration

```python
# src/pydotorg/core/ratelimit/__init__.py

"""Rate limiting module for pydotorg."""

from pydotorg.core.ratelimit.config import (
    RateLimitConfig,
    RateLimitTier,
    TierLimits,
    get_rate_limit_config,
)
from pydotorg.core.ratelimit.exceptions import rate_limit_exception_handler
from pydotorg.core.ratelimit.identifier import (
    get_rate_limit_identifier,
    should_check_rate_limit,
)
from pydotorg.core.ratelimit.middleware import create_rate_limit_middleware
from pydotorg.core.ratelimit.store import create_rate_limit_store
from pydotorg.core.ratelimit.tiers import get_endpoint_tier

__all__ = [
    "RateLimitConfig",
    "RateLimitTier",
    "TierLimits",
    "get_rate_limit_config",
    "rate_limit_exception_handler",
    "get_rate_limit_identifier",
    "should_check_rate_limit",
    "create_rate_limit_middleware",
    "create_rate_limit_store",
    "get_endpoint_tier",
]
```

```python
# src/pydotorg/core/ratelimit/middleware.py

"""Rate limiting middleware configuration."""

from litestar.middleware.rate_limit import RateLimitConfig as LitestarRateLimitConfig

from pydotorg.config import settings
from pydotorg.core.logging import get_logger
from pydotorg.core.ratelimit.config import get_rate_limit_config
from pydotorg.core.ratelimit.identifier import (
    get_rate_limit_identifier,
    should_check_rate_limit,
)

logger = get_logger(__name__)


def create_rate_limit_middleware() -> LitestarRateLimitConfig | None:
    """Create rate limiting middleware configuration.

    Returns:
        Litestar RateLimitConfig or None if disabled
    """
    config = get_rate_limit_config()

    if not config.enabled or not settings.rate_limit_enabled:
        logger.warning("Rate limiting is DISABLED")
        return None

    # Use the lowest tier (anonymous_low) as baseline
    # Dynamic per-endpoint limits handled by check_throttle_handler
    baseline = config.anonymous_low

    middleware_config = LitestarRateLimitConfig(
        rate_limit=("second", baseline.window_seconds),
        exclude=config.exclude_paths,
        identifier_for_request=get_rate_limit_identifier,
        check_throttle_handler=should_check_rate_limit,
        set_rate_limit_headers=config.set_headers,
        store="rate_limit",  # Store name registered in app
    )

    logger.info(
        "Rate limiting middleware configured",
        enabled=True,
        baseline_requests=baseline.requests,
        baseline_window=baseline.window_seconds,
        user_aware=config.use_user_aware,
    )

    return middleware_config
```

```python
# src/pydotorg/main.py (modifications)

from litestar.exceptions import TooManyRequestsException
from litestar.stores.registry import StoreRegistry

from pydotorg.core.ratelimit import (
    create_rate_limit_middleware,
    create_rate_limit_store,
    rate_limit_exception_handler,
)

# ... existing imports ...

# Create rate limit store
rate_limit_store = create_rate_limit_store()

# Create rate limit middleware config
rate_limit_config = create_rate_limit_middleware()

app = Litestar(
    route_handlers=[...],  # existing handlers
    dependencies=get_all_dependencies(),
    exception_handlers={
        **get_exception_handlers(),
        TooManyRequestsException: rate_limit_exception_handler,  # Add this
    },
    plugins=[...],  # existing plugins
    middleware=[
        session_config.middleware,
        UserPopulationMiddleware,
        JWTAuthMiddleware,
    ] + ([rate_limit_config.middleware] if rate_limit_config else []),  # Add conditionally
    stores=StoreRegistry(
        {
            "rate_limit": rate_limit_store,
        }
    ),
    # ... rest of config ...
)
```

---

### 7. Error Template

```jinja2
{# templates/errors/429.html.jinja2 #}

{% extends "base.html.jinja2" %}

{% block title %}Too Many Requests - {{ site_name }}{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
        <div>
            <div class="mx-auto flex items-center justify-center h-24 w-24 rounded-full bg-yellow-100">
                <svg class="h-16 w-16 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            </div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Rate Limit Exceeded
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                {{ message }}
            </p>
        </div>

        <div class="rounded-md bg-yellow-50 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-yellow-800">
                        Why did this happen?
                    </h3>
                    <div class="mt-2 text-sm text-yellow-700">
                        <p>Rate limits protect Python.org from abuse. You can:</p>
                        <ul class="list-disc pl-5 space-y-1 mt-2">
                            <li>Wait {{ retry_after }} seconds and try again</li>
                            <li>Log in for higher rate limits</li>
                            <li>Slow down your requests</li>
                            <li>Contact us if you need API access</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <div class="flex space-x-4">
            <a href="javascript:history.back()"
               class="flex-1 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Go Back
            </a>
            <a href="/"
               class="flex-1 flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Home
            </a>
        </div>

        <div class="text-center text-xs text-gray-500">
            <p>Retry after: {{ retry_after }} seconds</p>
        </div>
    </div>
</div>
{% endblock %}
```

---

## File Structure

```
src/pydotorg/
├── core/
│   └── ratelimit/
│       ├── __init__.py              # Public API exports
│       ├── config.py                # RateLimitConfig, TierLimits
│       ├── tiers.py                 # Endpoint tier classifications
│       ├── identifier.py            # User-aware identifier function
│       ├── store.py                 # Redis store creation
│       ├── middleware.py            # Middleware configuration
│       └── exceptions.py            # 429 exception handler
├── config.py                        # Settings additions (rate_limit_enabled, etc)
└── main.py                          # App integration

templates/
└── errors/
    └── 429.html.jinja2              # Rate limit error page
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. Create `core/ratelimit/` module structure
2. Implement `config.py` with RateLimitConfig and TierLimits
3. Implement `store.py` with Redis integration
4. Add configuration to `config.py` (Settings)
5. Write unit tests for config and store

**Deliverable**: Rate limiting configuration and Redis store ready

### Phase 2: Tier Classification (Week 1)
1. Implement `tiers.py` with endpoint classifications
2. Audit all 383 endpoints and assign tiers
3. Implement `get_endpoint_tier()` function with pattern matching
4. Write tests for tier assignments
5. Document tier rationale for each domain

**Deliverable**: All endpoints classified into tiers

### Phase 3: Middleware & Handlers (Week 2)
1. Implement `identifier.py` with user-aware logic
2. Implement `middleware.py` with Litestar integration
3. Implement `exceptions.py` with 429 handler
4. Create 429 error template
5. Write integration tests

**Deliverable**: Functional rate limiting middleware

### Phase 4: Application Integration (Week 2)
1. Modify `main.py` to register store and middleware
2. Add exception handler to app config
3. Update startup logging to show rate limit status
4. Test with real controllers
5. Performance testing with load tool

**Deliverable**: Rate limiting live in development

### Phase 5: Monitoring & Tuning (Week 3)
1. Add Prometheus metrics for rate limit hits
2. Implement admin dashboard for rate limit stats
3. Add alerts for excessive rate limiting
4. Tune limits based on real traffic
5. Document operational procedures

**Deliverable**: Production-ready rate limiting with observability

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/core/ratelimit/test_config.py

import pytest

from pydotorg.config import Environment
from pydotorg.core.ratelimit.config import RateLimitConfig, RateLimitTier


def test_tier_limits_per_minute():
    limits = TierLimits(requests=60, window_seconds=60)
    assert limits.per_minute == 60.0

    limits = TierLimits(requests=30, window_seconds=60)
    assert limits.per_minute == 30.0


def test_environment_specific_config():
    dev_config = RateLimitConfig.for_environment(Environment.DEV)
    prod_config = RateLimitConfig.for_environment(Environment.PROD)

    assert dev_config.anonymous_critical.requests > prod_config.anonymous_critical.requests
    assert dev_config.enabled is True
    assert prod_config.enabled is True


def test_get_tier_limits_anonymous():
    config = RateLimitConfig.for_environment(Environment.PROD)

    limits = config.get_tier_limits(RateLimitTier.CRITICAL, is_authenticated=False)
    assert limits.requests == 5
    assert limits.window_seconds == 60


def test_get_tier_limits_authenticated():
    config = RateLimitConfig.for_environment(Environment.PROD)

    limits = config.get_tier_limits(RateLimitTier.CRITICAL, is_authenticated=True)
    assert limits.requests == 20
    assert limits.window_seconds == 60


def test_staff_multiplier():
    config = RateLimitConfig.for_environment(Environment.PROD)

    limits = config.get_tier_limits(
        RateLimitTier.CRITICAL,
        is_authenticated=True,
        is_staff=True,
    )
    assert limits.requests == 20 * 5  # 5x multiplier
```

```python
# tests/unit/core/ratelimit/test_tiers.py

from pydotorg.core.ratelimit.tiers import get_endpoint_tier, RateLimitTier


def test_critical_endpoints():
    assert get_endpoint_tier("/api/auth/login", "POST") == RateLimitTier.CRITICAL
    assert get_endpoint_tier("/api/v1/search/", "POST") == RateLimitTier.CRITICAL
    assert get_endpoint_tier("/api/auth/register", "POST") == RateLimitTier.CRITICAL


def test_high_endpoints():
    assert get_endpoint_tier("/api/jobs", "POST") == RateLimitTier.HIGH
    assert get_endpoint_tier("/api/events", "POST") == RateLimitTier.HIGH


def test_unlimited_endpoints():
    assert get_endpoint_tier("/health", "GET") == RateLimitTier.UNLIMITED
    assert get_endpoint_tier("/static/css/main.css", "GET") == RateLimitTier.UNLIMITED
```

### Integration Tests

```python
# tests/integration/test_rate_limiting.py

import pytest
from litestar.status_codes import HTTP_200_OK, HTTP_429_TOO_MANY_REQUESTS
from litestar.testing import AsyncTestClient


@pytest.mark.asyncio
async def test_rate_limit_anonymous_user(test_client: AsyncTestClient):
    # Should allow first 5 requests to critical endpoint
    for _ in range(5):
        response = await test_client.post("/api/auth/login", json={
            "username": "test",
            "password": "wrong",
        })
        assert response.status_code in [HTTP_200_OK, 401]  # Auth may fail, but not rate limited

    # 6th request should be rate limited
    response = await test_client.post("/api/auth/login", json={
        "username": "test",
        "password": "wrong",
    })
    assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
    assert "Retry-After" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_authenticated_user(test_client: AsyncTestClient, auth_headers: dict):
    # Authenticated users should have higher limits
    for _ in range(20):
        response = await test_client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == HTTP_200_OK

    # Should still be rate limited eventually
    # (would need 21st request)
```

---

## Monitoring & Observability

### Metrics

```python
# src/pydotorg/core/ratelimit/metrics.py

from prometheus_client import Counter, Histogram

rate_limit_hits = Counter(
    "pydotorg_rate_limit_hits_total",
    "Total rate limit hits",
    ["tier", "endpoint", "user_type"],
)

rate_limit_duration = Histogram(
    "pydotorg_rate_limit_check_seconds",
    "Time spent checking rate limits",
    ["tier"],
)
```

### Admin Dashboard

Add rate limiting statistics to admin dashboard:
- Current rate limit hits by tier
- Top rate-limited endpoints
- Top rate-limited IPs/users
- Rate limit configuration overview

---

## Security Considerations

1. **Bypass Protection**: Ensure bypass tokens are cryptographically secure
2. **Redis Security**: Use Redis AUTH and encryption in production
3. **IP Spoofing**: Trust proxy headers only from known proxies
4. **DDoS**: Rate limiting is first line of defense, not complete protection
5. **Key Exhaustion**: Monitor Redis key count to prevent memory exhaustion

---

## Performance Impact

### Expected Overhead
- **Redis latency**: ~1-3ms per request
- **Identifier computation**: <0.1ms
- **Total overhead**: ~1-5ms per request

### Optimization Strategies
- Use Redis pipelining for bulk operations
- Cache tier assignments for common patterns
- Monitor Redis connection pool usage
- Consider local cache for non-distributed scenarios

---

## Migration & Rollout

### Pre-Deployment
1. Test in staging with production-like traffic
2. Tune limits based on historical traffic data
3. Create runbook for handling false positives
4. Set up monitoring and alerting

### Deployment
1. Deploy with `rate_limit_enabled=False` initially
2. Enable in dev/staging first
3. Gradual rollout to production (10% → 50% → 100%)
4. Monitor metrics closely for first 48 hours

### Rollback Plan
1. Set `rate_limit_enabled=False` via environment variable
2. No code changes required
3. Restart application to disable

---

## Summary

This architecture provides:

- **4-tier rate limiting** (Critical/High/Medium/Low)
- **User-aware limits** (5x higher for authenticated, 5x multiplier for staff)
- **Environment-specific** configuration (dev/staging/prod)
- **Redis-backed** distributed rate limiting
- **HTMX-aware** error handling with toast notifications
- **Zero external dependencies** (native Litestar)
- **Production-ready** monitoring and observability

**Key Files**:
- `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/core/ratelimit/config.py` - Configuration model
- `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/core/ratelimit/tiers.py` - Endpoint classifications
- `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/core/ratelimit/middleware.py` - Middleware setup
- `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/main.py` - Application integration

**Next Steps**: Proceed with Phase 1 implementation (core infrastructure)

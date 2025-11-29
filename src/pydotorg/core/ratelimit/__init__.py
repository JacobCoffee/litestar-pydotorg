"""Rate limiting module for API endpoint protection.

This module provides tiered rate limiting with support for different user types:
- Anonymous users: Base rate limits
- Authenticated users: 4x base limits
- Staff users: 20x base limits (4x auth * 5x staff)

Rate limit tiers:
- CRITICAL (5/min): Authentication, password reset
- HIGH (20/min): Mutations, content creation
- MEDIUM (60/min): Standard API endpoints
- LOW (120/min): Read-only, public content

Components:
    - config: Tiered rate limit configuration
    - identifier: User-aware rate limit identifier
    - middleware: Litestar RateLimitConfig factory
    - exceptions: Custom 429 exception handler with Retry-After support

Usage:
    from pydotorg.core.ratelimit import (
        RateLimitTier,
        ratelimit_config,
        create_rate_limit_middleware,
        rate_limit_exception_handler,
    )

    limit = ratelimit_config.get_limit(
        RateLimitTier.MEDIUM,
        is_authenticated=True,
        is_staff=False
    )

    rate_limit_config = create_rate_limit_middleware(settings)
"""

from __future__ import annotations

from pydotorg.core.ratelimit.config import (
    RateLimitConfig,
    RateLimitTier,
    get_ratelimit_config,
    ratelimit_config,
)
from pydotorg.core.ratelimit.exceptions import rate_limit_exception_handler
from pydotorg.core.ratelimit.identifier import get_rate_limit_identifier
from pydotorg.core.ratelimit.middleware import (
    create_rate_limit_config,
    create_response_cache_config,
)

__all__ = [
    "RateLimitConfig",
    "RateLimitTier",
    "create_rate_limit_config",
    "create_response_cache_config",
    "get_rate_limit_identifier",
    "get_ratelimit_config",
    "rate_limit_exception_handler",
    "ratelimit_config",
]

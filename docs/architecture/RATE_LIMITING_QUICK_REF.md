:orphan:

# Rate Limiting Quick Reference

## Developer Cheat Sheet

### Quick Start

```python
# Rate limiting is automatically applied to all endpoints
# No decorator or manual configuration needed!
```

### Endpoint Tier Assignment

When creating new endpoints, they are automatically assigned a tier based on path patterns:

| Tier | Anonymous Limit | Authenticated Limit | Use Case |
|------|----------------|---------------------|----------|
| CRITICAL | 5 req/min | 20 req/min | Auth, search, submissions |
| HIGH | 20 req/min | 60 req/min | Forms, job/event posts |
| MEDIUM | 60 req/min | 180 req/min | Community content |
| LOW | 120 req/min | 300 req/min | Read-only operations |
| UNLIMITED | ∞ | ∞ | Health, static, media |

### Override Rate Limit for Specific Endpoint

If you need custom limits for a specific endpoint:

```python
from litestar import get
from litestar.middleware.rate_limit import RateLimitConfig

@get(
    "/api/special/endpoint",
    middleware=[
        RateLimitConfig(
            rate_limit=("minute", 10),  # 10 requests per minute
        ).middleware
    ]
)
async def special_endpoint() -> dict:
    return {"message": "Custom rate limited"}
```

### Exclude Endpoint from Rate Limiting

To completely exclude an endpoint:

```python
# Option 1: Add to exclude_paths in config
# src/pydotorg/core/ratelimit/config.py
exclude_paths: list[str] = [
    "/static/*",
    "/health",
    "/my-special-endpoint",  # Add here
]

# Option 2: Add to UNLIMITED_ENDPOINTS
# src/pydotorg/core/ratelimit/tiers.py
UNLIMITED_ENDPOINTS = {
    "/health",
    "/my-special-endpoint",  # Add here
}
```

### Testing Rate Limits

```python
# tests/integration/test_my_feature.py

@pytest.mark.asyncio
async def test_rate_limit_enforcement(test_client: AsyncTestClient):
    # Test that endpoint is rate limited after N requests
    for i in range(5):  # CRITICAL tier allows 5
        response = await test_client.post("/api/auth/login", json={...})
        assert response.status_code != 429, f"Rate limited at request {i+1}"

    # 6th request should be rate limited
    response = await test_client.post("/api/auth/login", json={...})
    assert response.status_code == 429
    assert "Retry-After" in response.headers
```

### Environment Variables

```bash
# .env
RATE_LIMIT_ENABLED=true                    # Enable/disable globally
RATE_LIMIT_REDIS_NAMESPACE=ratelimit       # Redis key prefix
RATE_LIMIT_CRITICAL_REQUESTS=5             # Override critical tier
RATE_LIMIT_CRITICAL_WINDOW=60              # Override critical window
```

### Monitoring Rate Limits

```bash
# Check Redis keys
redis-cli KEYS "ratelimit:*"

# Get current count for an identifier
redis-cli GET "ratelimit:ip:192.168.1.100:critical"

# Check TTL (time to reset)
redis-cli TTL "ratelimit:ip:192.168.1.100:critical"
```

### Common Scenarios

#### Scenario 1: New Authentication Endpoint
```python
# Automatically CRITICAL tier (5 req/min anonymous)
@post("/api/auth/new-login-method")
async def new_auth(data: LoginData) -> TokenResponse:
    # Rate limit automatically applied
    pass
```

#### Scenario 2: New Read-Only API
```python
# Automatically LOW tier (120 req/min anonymous)
@get("/api/stats/summary")
async def get_stats() -> dict:
    # Higher limits for read operations
    pass
```

#### Scenario 3: Admin-Only Endpoint
```python
# Staff users get 5x multiplier automatically
@post("/api/admin/bulk-operation", guards=[require_superuser])
async def bulk_op() -> dict:
    # Staff: 20 req/min × 5 = 100 req/min
    pass
```

### Troubleshooting

#### Problem: Getting 429 Too Many Requests
```
Cause: Exceeded rate limit for your tier
Solution:
1. Wait for Retry-After seconds (check header)
2. Log in for higher limits (4x increase)
3. Contact admin if you need API access
```

#### Problem: Rate Limits Too Strict
```
Solution:
1. Update limits in RateLimitConfig.for_environment()
2. Consider if endpoint should be in different tier
3. Use environment variables for temporary override
```

#### Problem: Rate Limiting Not Working
```
Check:
1. RATE_LIMIT_ENABLED=true in .env
2. Redis is running and accessible
3. Endpoint not in UNLIMITED_ENDPOINTS
4. Check logs for middleware errors
```

### Response Headers

All rate-limited responses include:

```
RateLimit-Policy: 5;w=60         # 5 requests per 60 seconds
RateLimit-Remaining: 3           # 3 requests remaining
RateLimit-Reset: 1234567890      # Unix timestamp for reset
RateLimit-Limit: 5               # Total requests allowed
```

When rate limited (429):
```
Retry-After: 45                  # Seconds until reset
```

### Best Practices

1. **Don't bypass rate limits** - They protect the application
2. **Test with realistic load** - Don't artificially inflate limits
3. **Log in users** - Authenticated users get higher limits
4. **Monitor metrics** - Watch for false positives
5. **Document custom limits** - Explain why if you override
6. **Consider user experience** - Don't make limits too strict
7. **Use retry logic** - Implement exponential backoff in clients

### Architecture Files

- Configuration: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/core/ratelimit/config.py`
- Tier Assignments: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/core/ratelimit/tiers.py`
- Identifier Logic: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/core/ratelimit/identifier.py`
- Main Integration: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/main.py`

### Need Help?

- Full Architecture: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/architecture/RATE_LIMITING_ARCHITECTURE.md`
- Visual Diagram: `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/docs/architecture/rate_limiting_diagram.txt`
- Litestar Docs: https://docs.litestar.dev/latest/usage/middleware/rate-limit.html

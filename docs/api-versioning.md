# API Versioning

The Litestar pydotorg rewrite includes a comprehensive API versioning system that supports multiple version negotiation strategies and provides deprecation warnings.

## Features

- **Multiple Version Negotiation Methods**
  - Accept header (`application/vnd.pydotorg.v1+json`)
  - URL path prefix (`/api/v1/...`)
  - Query parameter (`?api_version=1`)
  - Default version fallback

- **Deprecation Support**
  - Mark versions as deprecated
  - Set sunset dates for version removal
  - Automatic response headers with deprecation info

- **Response Headers**
  - `X-API-Version`: Current API version used
  - `X-API-Deprecated`: true/false
  - `X-API-Sunset-Date`: ISO date when deprecated version will be removed
  - `X-API-Deprecation-Info`: JSON with detailed deprecation information

## Architecture

### Components

1. **APIVersion**: Immutable dataclass representing a semantic version with deprecation metadata
2. **APIVersionRegistry**: Singleton registry of supported versions
3. **APIVersionMiddleware**: Litestar middleware that negotiates versions and adds headers

### Version Negotiation Order

The middleware checks for version information in this order:

1. **Accept Header** (highest priority)
   ```
   Accept: application/vnd.pydotorg.v1+json
   ```

2. **URL Path**
   ```
   /api/v1/users
   ```

3. **Query Parameter**
   ```
   /api/users?api_version=1
   ```

4. **Default Version** (fallback)
   - Currently: v1.0.0

## Usage

### Client Requests

#### Using Accept Header (Recommended for API clients)

```bash
curl -H "Accept: application/vnd.pydotorg.v1+json" \
     https://api.python.org/api/v1/users
```

#### Using URL Path (Current pattern)

```bash
curl https://api.python.org/api/v1/users
```

#### Using Query Parameter (Fallback)

```bash
curl https://api.python.org/api/users?api_version=1
```

### Server Configuration

#### Adding a New Version

```python
from pydotorg.lib.api_versioning import add_version

# Add v2 as a new version
add_version(2, 0, 0, is_default=False)

# Or make it the default
add_version(2, 0, 0, is_default=True)
```

#### Deprecating a Version

```python
from datetime import date
from pydotorg.lib.api_versioning import deprecate_version

# Deprecate v1 with a sunset date
deprecate_version(1, sunset_date=date(2026, 12, 31))
```

#### Accessing Version in Route Handlers

The negotiated version is available in the request scope:

```python
from litestar import Request, get
from pydotorg.lib.api_versioning import APIVersion

@get("/api/v1/example")
async def example_handler(request: Request) -> dict:
    version: APIVersion = request.scope.get("api_version")
    return {
        "version": str(version),
        "deprecated": version.deprecated,
    }
```

## Response Examples

### Non-Deprecated Version

```http
HTTP/1.1 200 OK
X-API-Version: v2.0.0
X-API-Deprecated: false
Content-Type: application/json

{"data": "..."}
```

### Deprecated Version

```http
HTTP/1.1 200 OK
X-API-Version: v1.0.0
X-API-Deprecated: true
X-API-Sunset-Date: 2026-12-31
X-API-Deprecation-Info: {"deprecated":true,"sunset_date":"2026-12-31","message":"API version v1.0.0 is deprecated and will be removed on 2026-12-31","current_version":"v2.0.0"}
Content-Type: application/json

{"data": "..."}
```

## Implementation Details

### Middleware Stack Order

The `APIVersionMiddleware` is positioned early in the middleware stack to ensure version information is available for all subsequent middleware and handlers:

```python
middleware=[
    session_config.middleware,
    APIVersionMiddleware,  # <- Early in the stack
    SitewideBannerMiddleware,
    APIBannerMiddleware,
    # ... other middleware
]
```

### Version Format

- **Storage**: Semantic versioning (major.minor.patch)
- **Display**: Full format `v1.0.0` or short format `v1`
- **Parsing**: Supports `v1`, `1`, `1.2`, `1.2.3`

### Immutability

`APIVersion` objects are frozen dataclasses to ensure thread safety and prevent accidental mutations. To update a version (e.g., deprecate it), a new version object is created and registered.

## Best Practices

1. **Always use Accept header for programmatic clients**
   - Most explicit and follows REST conventions
   - Doesn't pollute URLs
   - Easy to version content types

2. **Use URL path for browser/documentation access**
   - Currently implemented: `/api/v1/...`
   - Human-readable and bookmarkable
   - Good for API documentation

3. **Reserve query parameters for exceptional cases**
   - Useful when Accept header and URL aren't available
   - Good for testing and debugging

4. **Set sunset dates when deprecating**
   - Gives clients time to migrate
   - Include deprecation info in API documentation
   - Communicate changes via release notes

5. **Maintain at least 2 versions**
   - Current stable version
   - Previous version (deprecated with sunset date)
   - Gives clients 6-12 months to migrate

## Migration Example

### Phase 1: Announce New Version
```python
# Add v2 but keep v1 as default
add_version(2, 0, 0, is_default=False)
```

### Phase 2: Promote New Version (3 months later)
```python
# Make v2 default, deprecate v1
add_version(2, 0, 0, is_default=True)
deprecate_version(1, sunset_date=date(2026, 6, 30))
```

### Phase 3: Remove Old Version (6 months after deprecation)
```python
# Remove v1 from registry
# Update documentation
# Return 410 Gone for v1 requests
```

## Testing

Tests are handled by the Tester agent. The test suite covers:

- Version parsing from all sources (Accept, path, query)
- Version negotiation priority order
- Response header injection
- Deprecation warning headers
- Registry operations (add, deprecate, get)
- Edge cases (invalid versions, missing versions, etc.)

## Future Enhancements

- [ ] Version-specific route handlers
- [ ] Automatic OpenAPI spec per version
- [ ] Version negotiation analytics
- [ ] Breaking change detection
- [ ] Version migration helpers

# API Usage Guide

This guide covers how to work with the litestar-pydotorg REST API.

## Overview

The Python.org API provides programmatic access to:

- **Python Releases** - Download information, version history, and release files
- **Job Board** - Python job postings with search and filtering
- **Events** - Community events, calendars, and locations
- **Content** - Blog posts, success stories, and community content
- **Sponsors** - PSF sponsors and sponsorship information
- **Users** - User management and authentication

## Base URL and Versioning

All API endpoints are available at:

```
https://python.org/api/v1/
```

For local development:

```
http://localhost:8000/api/v1/
```

The API is versioned using URL path prefixes. Currently, `v1` is the active version.

## API Documentation

Interactive API documentation is available at:

| UI | URL | Description |
|----|-----|-------------|
| **Scalar** | `/api/` | Modern, feature-rich API explorer (recommended) |
| **Swagger** | `/api/swagger` | Classic OpenAPI UI |
| **ReDoc** | `/api/redoc` | Clean, responsive documentation |

## Making Requests

### Basic GET Request

```bash
curl "http://localhost:8000/api/v1/releases/latest"
```

### Python Example

```python
import httpx

response = httpx.get("http://localhost:8000/api/v1/releases/latest")
release = response.json()

print(f"Latest Python: {release['name']}")
print(f"Released: {release['release_date']}")
```

### JavaScript Example

```javascript
const response = await fetch("http://localhost:8000/api/v1/releases/latest");
const release = await response.json();

console.log(`Latest Python: ${release.name}`);
```

## Authentication

Most read endpoints are public, but write operations require authentication. See the [Authentication Guide](authentication.md) for complete details.

### Quick Authentication

```bash
# Login and get tokens
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use the access token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Pagination

The API supports two pagination patterns:

### Limit/Offset (Most Endpoints)

```bash
# Get results 21-40
curl "http://localhost:8000/api/v1/jobs?limit=20&offset=20"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum items to return (1-1000) |
| `offset` | integer | 0 | Number of items to skip |

### Page-Based (Some Endpoints)

```bash
# Get page 2 with 20 items per page
curl "http://localhost:8000/api/v1/releases?currentPage=2&pageSize=20"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `currentPage` | integer | 1 | Page number (1-indexed) |
| `pageSize` | integer | 20 | Items per page |

## Error Handling

The API uses standard HTTP status codes:

| Code | Meaning | Example Scenario |
|------|---------|-----------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but lacking permissions |
| 404 | Not Found | Resource does not exist |
| 422 | Unprocessable Entity | Validation error in request data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "status_code": 404,
  "extra": {}
}
```

### Handling Errors

```python
import httpx

response = httpx.get("http://localhost:8000/api/v1/jobs/nonexistent-id")

if response.status_code == 200:
    job = response.json()
elif response.status_code == 404:
    print("Job not found")
elif response.status_code == 401:
    print("Authentication required")
elif response.status_code == 429:
    retry_after = response.headers.get("Retry-After", 60)
    print(f"Rate limited. Retry after {retry_after} seconds")
else:
    error = response.json()
    print(f"Error: {error['detail']}")
```

## Rate Limiting

The API implements rate limiting to ensure fair usage.

### Rate Limit Tiers

| Tier | Anonymous | Authenticated | Staff |
|------|-----------|---------------|-------|
| **CRITICAL** | 5/min | 20/min | 100/min |
| **HIGH** | 20/min | 60/min | 300/min |
| **MEDIUM** | 60/min | 180/min | 900/min |
| **LOW** | 120/min | 300/min | 1500/min |

### Checking Your Quota

Rate limit information is included in response headers:

```
RateLimit-Policy: 120;w=60
RateLimit-Remaining: 118
RateLimit-Reset: 1735689600
RateLimit-Limit: 120
```

### Handling Rate Limits

```python
import time
import httpx

def request_with_retry(url: str, max_retries: int = 3) -> httpx.Response:
    """Make request with exponential backoff for rate limits."""
    for attempt in range(max_retries):
        response = httpx.get(url)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            wait_time = retry_after * (2 ** attempt)
            print(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            continue

        return response

    raise Exception("Max retries exceeded")
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create new account |
| POST | `/api/auth/login` | JWT login |
| POST | `/api/auth/refresh` | Refresh JWT tokens |
| POST | `/api/auth/logout` | Logout (invalidate tokens) |
| POST | `/api/auth/me` | Get current user info |

### Downloads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/releases/` | List all releases |
| GET | `/api/v1/releases/latest` | Get latest Python 3 release |
| GET | `/api/v1/releases/latest/{ver}` | Get latest for version (2, 3) |
| GET | `/api/v1/releases/{id}` | Get release by ID |
| GET | `/api/v1/files/release/{id}` | List files for a release |

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/jobs/` | List all jobs |
| GET | `/api/v1/jobs/{id}` | Get job by ID |
| POST | `/api/v1/jobs/search` | Search jobs with filters |
| GET | `/api/v1/job-types/` | List job types |
| GET | `/api/v1/job-categories/` | List job categories |

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/events/` | List events |
| GET | `/api/v1/events/upcoming` | Get upcoming events |
| GET | `/api/v1/events/featured` | Get featured events |
| GET | `/api/v1/events/{id}` | Get event by ID |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search/` | Full-text search |
| GET | `/api/v1/search/autocomplete` | Autocomplete suggestions |

## Client SDKs

### Generating Python Client

```bash
pip install openapi-python-client

openapi-python-client generate \
  --url http://localhost:8000/api/openapi.json \
  --output-path ./python-org-client
```

### Generating TypeScript Client

```bash
npx openapi-typescript http://localhost:8000/api/openapi.json \
  --output ./types/python-org-api.ts
```

## Best Practices

### Caching

Respect `Cache-Control` and `ETag` headers:

```python
etag = None
cached_data = None

def get_releases():
    global etag, cached_data

    headers = {}
    if etag:
        headers["If-None-Match"] = etag

    response = httpx.get(
        "http://localhost:8000/api/v1/releases",
        headers=headers
    )

    if response.status_code == 304:
        return cached_data

    etag = response.headers.get("ETag")
    cached_data = response.json()
    return cached_data
```

### Request Batching

Use list endpoints instead of individual requests:

```python
# Instead of multiple single requests
# for id in ids:
#     httpx.get(f"/api/v1/jobs/{id}")

# Use list endpoint with filtering
response = httpx.get(
    "http://localhost:8000/api/v1/jobs",
    params={"limit": 100}
)
```

### Error Retry Strategy

```python
import httpx
from httpx import HTTPTransport

transport = HTTPTransport(retries=3)
client = httpx.Client(transport=transport)

response = client.get("http://localhost:8000/api/v1/releases")
```

## Testing with the API

### Using HTTPie

```bash
pip install httpie

# Get latest release
http http://localhost:8000/api/v1/releases/latest

# Search jobs
http POST http://localhost:8000/api/v1/jobs/search query="django" limit:=10

# Authenticated request
http http://localhost:8000/api/auth/me "Authorization:Bearer $TOKEN"
```

### Using Postman

1. Open Postman
2. Click **Import**
3. Select **Link** tab
4. Enter: `http://localhost:8000/api/openapi.json`
5. Click **Continue** and then **Import**

## See Also

- [Authentication Guide](authentication.md) - Detailed authentication flows
- [Rate Limiting Architecture](../architecture/RATE_LIMITING_ARCHITECTURE.md) - Rate limiting details
- [API Tags Structure](../architecture/API_TAGS_STRUCTURE.md) - API organization

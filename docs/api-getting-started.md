# API Getting Started Guide

Welcome to the Python.org API. This guide covers everything you need to start building applications that integrate with Python.org.

## Introduction

### What the API Provides

The Python.org API gives you programmatic access to:

- **Python Releases**: Download information, version history, and release files
- **Job Board**: Python job postings with search and filtering
- **Events**: Community events, calendars, and locations
- **Content**: Blog posts, success stories, and community content
- **Sponsors**: PSF sponsors and sponsorship information
- **Users**: User management and authentication

### Base URL and Versioning

All API endpoints are available at:

```
https://python.org/api/v1/
```

The API is versioned using URL path prefixes. Currently, `v1` is the active version.

### API Documentation UIs

Interactive API documentation is available at:

| UI | URL | Description |
|-----|-----|-------------|
| **Scalar** | `/api/` | Modern, feature-rich API explorer (recommended) |
| **Swagger** | `/api/swagger` | Classic OpenAPI UI |
| **ReDoc** | `/api/redoc` | Clean, responsive documentation |

Visit these endpoints in your browser to explore the full API schema and try requests interactively.

---

## Authentication

Most read endpoints are public, but write operations require authentication. The API supports JWT (JSON Web Tokens) for stateless authentication.

### Quick Start with JWT Tokens

**Step 1: Get a Token**

```bash
curl -X POST https://python.org/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Step 2: Use the Token**

Include the access token in the `Authorization` header for authenticated requests:

```bash
curl https://python.org/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Lifetimes

| Token Type | Lifetime | Purpose |
|-----------|----------|---------|
| Access Token | 7 days | API access |
| Refresh Token | 30 days | Renew access tokens |

### Refreshing Tokens

When your access token expires, use the refresh token to get new tokens:

```bash
curl -X POST https://python.org/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'
```

For comprehensive authentication documentation, see [API Authentication Guide](./api-authentication.md).

---

## Making Your First Request

### Example: Get List of Jobs

Fetch approved Python job postings:

#### cURL

```bash
curl "https://python.org/api/v1/jobs?status=approved&limit=10"
```

#### Python (requests)

```python
import requests

response = requests.get(
    "https://python.org/api/v1/jobs",
    params={"status": "approved", "limit": 10}
)

jobs = response.json()
for job in jobs:
    print(f"{job['job_title']} at {job['company_name']}")
```

#### Python (httpx - async)

```python
import httpx

async def get_jobs():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://python.org/api/v1/jobs",
            params={"status": "approved", "limit": 10}
        )
        return response.json()

# Run with: asyncio.run(get_jobs())
```

#### JavaScript (fetch)

```javascript
const response = await fetch(
  "https://python.org/api/v1/jobs?status=approved&limit=10"
);

const jobs = await response.json();
jobs.forEach(job => {
  console.log(`${job.job_title} at ${job.company_name}`);
});
```

### Example: Get a Specific Release

Fetch details about the latest Python release:

#### cURL

```bash
curl "https://python.org/api/v1/releases/latest"
```

#### Python

```python
import requests

response = requests.get("https://python.org/api/v1/releases/latest")
release = response.json()

print(f"Latest Python: {release['name']}")
print(f"Released: {release['release_date']}")
print(f"Download: {release['resource_uri']}")
```

#### JavaScript

```javascript
const response = await fetch("https://python.org/api/v1/releases/latest");
const release = await response.json();

console.log(`Latest Python: ${release.name}`);
console.log(`Released: ${release.release_date}`);
```

### Example: Search Jobs with Filters

```python
import requests

response = requests.post(
    "https://python.org/api/v1/jobs/search",
    json={
        "query": "django",
        "location": "remote",
        "job_type_ids": ["uuid-for-full-time"]
    }
)

matching_jobs = response.json()
```

---

## Common Patterns

### Pagination

The API supports two pagination patterns depending on the endpoint:

#### Pattern 1: Limit/Offset (Most Endpoints)

```bash
# Get results 21-40
curl "https://python.org/api/v1/jobs?limit=20&offset=20"
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum items to return (1-1000) |
| `offset` | integer | 0 | Number of items to skip |

**Example (Python):**

```python
import requests

def get_all_jobs():
    """Fetch all jobs using pagination."""
    all_jobs = []
    offset = 0
    limit = 100

    while True:
        response = requests.get(
            "https://python.org/api/v1/jobs",
            params={"limit": limit, "offset": offset, "status": "approved"}
        )
        jobs = response.json()

        if not jobs:
            break

        all_jobs.extend(jobs)
        offset += limit

        if len(jobs) < limit:
            break

    return all_jobs
```

#### Pattern 2: Page-Based (Some List Endpoints)

```bash
# Get page 2 with 20 items per page
curl "https://python.org/api/v1/releases?currentPage=2&pageSize=20"
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `currentPage` | integer | 1 | Page number (1-indexed) |
| `pageSize` | integer | 20 | Items per page |

### Filtering and Searching

Most list endpoints support filtering via query parameters:

```bash
# Filter jobs by status
curl "https://python.org/api/v1/jobs?status=approved"

# Filter releases by Python version
curl "https://python.org/api/v1/releases/latest/3"

# Filter events by upcoming
curl "https://python.org/api/v1/events?upcoming=true"
```

For complex searches, use the search endpoints:

```python
# Full-text search across content
response = requests.post(
    "https://python.org/api/v1/search",
    json={
        "query": "asyncio tutorial",
        "indexes": ["pages", "blogs"],
        "limit": 20
    }
)
```

### Error Handling

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

**Error Response Format:**

```json
{
  "detail": "Human-readable error message",
  "status_code": 404,
  "extra": {}
}
```

**Handling Errors (Python):**

```python
import requests

response = requests.get("https://python.org/api/v1/jobs/nonexistent-id")

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

**Handling Errors (JavaScript):**

```javascript
try {
  const response = await fetch("https://python.org/api/v1/jobs/nonexistent-id");

  if (!response.ok) {
    if (response.status === 404) {
      console.log("Job not found");
    } else if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After") || 60;
      console.log(`Rate limited. Retry after ${retryAfter} seconds`);
    } else {
      const error = await response.json();
      console.log(`Error: ${error.detail}`);
    }
    return;
  }

  const job = await response.json();
} catch (err) {
  console.error("Network error:", err);
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage and protect against abuse.

### Rate Limit Tiers

The API uses a 4-tier rate limiting system based on endpoint sensitivity:

| Tier | Anonymous | Authenticated | Staff | Use Cases |
|------|-----------|---------------|-------|-----------|
| **CRITICAL** | 5/min | 20/min | 100/min | Auth, search, submissions |
| **HIGH** | 20/min | 60/min | 300/min | Forms, job/event posts |
| **MEDIUM** | 60/min | 180/min | 900/min | Community content |
| **LOW** | 120/min | 300/min | 1500/min | Read-only operations |

Authenticated users receive 4x the anonymous limit. Staff users receive 5x the authenticated limit.

### Checking Your Quota

Rate limit information is included in response headers:

```
RateLimit-Policy: 120;w=60      # 120 requests per 60 seconds
RateLimit-Remaining: 118        # 118 requests remaining
RateLimit-Reset: 1735689600     # Unix timestamp for reset
RateLimit-Limit: 120            # Total requests allowed
```

### Handling 429 Responses

When rate limited, you receive a `429 Too Many Requests` response:

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "status_code": 429
}
```

**Response Headers:**

```
Retry-After: 45                 # Seconds until reset
```

**Best Practice: Implement Exponential Backoff**

```python
import time
import requests

def request_with_retry(url, max_retries=3):
    """Make request with exponential backoff for rate limits."""
    for attempt in range(max_retries):
        response = requests.get(url)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            wait_time = retry_after * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            continue

        return response

    raise Exception("Max retries exceeded")
```

---

## API Endpoints Overview

### Quick Reference by Domain

| Domain | Base Path | Key Endpoints |
|--------|-----------|---------------|
| **Authentication** | `/api/auth/` | `POST login`, `POST register`, `POST refresh` |
| **Users** | `/api/v1/users/` | `GET /`, `GET /{id}`, `POST /` |
| **Releases** | `/api/v1/releases/` | `GET /`, `GET /latest`, `GET /{id}` |
| **Jobs** | `/api/v1/jobs/` | `GET /`, `POST /search`, `GET /{id}` |
| **Events** | `/api/v1/events/` | `GET /`, `GET /upcoming`, `GET /{id}` |
| **Blogs** | `/api/blogs/` | `GET /`, `GET /entries/{id}` |
| **Sponsors** | `/api/v1/sponsors/` | `GET /`, `GET /{id}` |
| **Search** | `/api/v1/search/` | `POST /`, `GET /autocomplete` |
| **Pages** | `/api/pages/` | `GET /`, `GET /{id}` |

### Downloads Domain

```
GET  /api/v1/os/                    # List operating systems
GET  /api/v1/os/{id}                # Get OS by ID
GET  /api/v1/os/slug/{slug}         # Get OS by slug

GET  /api/v1/releases/              # List all releases
GET  /api/v1/releases/{id}          # Get release by ID
GET  /api/v1/releases/slug/{slug}   # Get release by slug
GET  /api/v1/releases/latest        # Get latest Python 3 release
GET  /api/v1/releases/latest/{ver}  # Get latest for version (2, 3)
GET  /api/v1/releases/published     # List published releases
GET  /api/v1/releases/download-page # Releases for download page

GET  /api/v1/files/{id}             # Get release file by ID
GET  /api/v1/files/release/{id}     # List files for a release
GET  /api/v1/files/os/{id}          # List files for an OS
```

### Jobs Domain

```
GET   /api/v1/jobs/                 # List all jobs
GET   /api/v1/jobs/{id}             # Get job by ID
POST  /api/v1/jobs/search           # Search jobs with filters
GET   /api/v1/jobs/mine             # List user's jobs (auth required)

GET   /api/v1/job-types/            # List job types
GET   /api/v1/job-types/{id}        # Get job type by ID

GET   /api/v1/job-categories/       # List job categories
GET   /api/v1/job-categories/{id}   # Get job category by ID
```

### Events Domain

```
GET  /api/v1/events/                # List events
GET  /api/v1/events/{id}            # Get event by ID
GET  /api/v1/events/upcoming        # Get upcoming events
GET  /api/v1/events/featured        # Get featured events

GET  /api/v1/calendars/             # List calendars
GET  /api/v1/event-categories/      # List event categories
GET  /api/v1/event-locations/       # List event locations
GET  /api/v1/event-occurrences/     # List event occurrences
```

### Search Endpoints

```
POST /api/v1/search/                # Full-text search
GET  /api/v1/search/autocomplete    # Autocomplete suggestions
```

### Full OpenAPI Specification

The complete API specification is available at:

```
GET /api/openapi.json
```

This JSON schema can be used with OpenAPI tools for client generation, testing, and documentation.

---

## SDKs and Tools

### OpenAPI Specification

The OpenAPI 3.0 specification is available at:

```
https://python.org/api/openapi.json
```

You can use this specification with various tools:

- **Postman**: Import the spec for API testing
- **Swagger Codegen**: Generate client SDKs
- **OpenAPI Generator**: Generate clients in 50+ languages

### Generating Client SDKs

#### Python Client (using openapi-python-client)

```bash
pip install openapi-python-client

openapi-python-client generate \
  --url https://python.org/api/openapi.json \
  --output-path ./python-org-client
```

#### TypeScript Client (using openapi-typescript)

```bash
npx openapi-typescript https://python.org/api/openapi.json \
  --output ./types/python-org-api.ts
```

#### Go Client (using oapi-codegen)

```bash
go install github.com/deepmap/oapi-codegen/cmd/oapi-codegen@latest

oapi-codegen -package pythonorg \
  https://python.org/api/openapi.json > pythonorg/client.go
```

### Postman Collection

A Postman collection is available for quick API exploration:

1. Open Postman
2. Click **Import**
3. Select **Link** tab
4. Enter: `https://python.org/api/openapi.json`
5. Click **Continue** and then **Import**

The collection includes all endpoints with example requests.

### Testing with HTTPie

[HTTPie](https://httpie.io/) is a user-friendly command-line HTTP client:

```bash
# Install
pip install httpie

# Get latest release
http https://python.org/api/v1/releases/latest

# Search jobs
http POST https://python.org/api/v1/jobs/search query="django" limit:=10

# Authenticated request
http https://python.org/api/auth/me "Authorization:Bearer $TOKEN"
```

---

## Best Practices

### Caching

The API returns caching headers. Respect `Cache-Control` and `ETag` headers to reduce unnecessary requests:

```python
import requests

# Store ETag from previous request
etag = None
cached_data = None

def get_releases():
    global etag, cached_data

    headers = {}
    if etag:
        headers["If-None-Match"] = etag

    response = requests.get(
        "https://python.org/api/v1/releases",
        headers=headers
    )

    if response.status_code == 304:
        return cached_data  # Use cached version

    etag = response.headers.get("ETag")
    cached_data = response.json()
    return cached_data
```

### Request Batching

When fetching multiple resources, batch your requests where possible:

```python
# Instead of multiple single requests:
# requests.get("/api/v1/jobs/1")
# requests.get("/api/v1/jobs/2")
# requests.get("/api/v1/jobs/3")

# Use list endpoint with filtering:
response = requests.get(
    "https://python.org/api/v1/jobs",
    params={"limit": 100}
)
```

### Error Retry Strategy

Implement proper retry logic for transient errors:

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create a requests session with retry logic."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session

# Usage
session = create_session()
response = session.get("https://python.org/api/v1/releases")
```

---

## Next Steps

- **Explore the API**: Visit `/api/` to use the interactive Scalar documentation
- **Read Authentication Guide**: See [API Authentication](./api-authentication.md) for detailed auth flows
- **Check Rate Limits**: Review the [Rate Limiting Quick Reference](./architecture/RATE_LIMITING_QUICK_REF.md)
- **Generate a Client**: Use the OpenAPI spec to generate a client SDK for your language
- **Report Issues**: Found a bug? Report it at [GitHub Issues](https://github.com/python/pythondotorg/issues)

---

## Support

For API-related questions and issues:

- **GitHub Issues**: https://github.com/python/pythondotorg/issues
- **Security Issues**: security@python.org
- **General Questions**: https://discuss.python.org/

---

*Last updated: 2025-11-29*

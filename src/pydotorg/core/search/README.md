# Search Module

This module provides full-text search functionality using Meilisearch for the Python.org Litestar rewrite.

## Overview

The search module consists of:

- **Service Layer** (`service.py`): Async Meilisearch client wrapper with index management
- **Schemas** (`schemas.py`): Pydantic models for search queries, results, and indexed documents
- **Controllers** (`domains/search/controllers.py`): API and HTML endpoints for search
- **Templates** (`templates/search/`): Jinja2 templates for search UI

## Features

- Full-text search across multiple content types (jobs, events, blogs, pages)
- Faceted filtering by content type
- Real-time search with htmx integration
- Autocomplete suggestions
- Pagination support
- Highlighted search results
- Flexible index management

## Configuration

Add these environment variables to your `.env` file:

```bash
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=your-master-key-here  # Optional for dev
MEILISEARCH_INDEX_PREFIX=pydotorg_
```

## Usage

### Starting Meilisearch

```bash
# Using Docker
docker run -d \
  --name meilisearch \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest

# Or install locally
brew install meilisearch
meilisearch
```

### Indexing Documents

```python
from pydotorg.core.search import SearchService
from pydotorg.core.search.schemas import JobDocument

# Initialize service
search_service = SearchService(
    url="http://localhost:7700",
    index_prefix="pydotorg_"
)

# Create index
await search_service.create_index("jobs")

# Configure index for optimal search
await search_service.configure_index(
    "jobs",
    searchable_attributes=["title", "description", "company_name", "location"],
    filterable_attributes=["remote", "job_types", "status"],
    sortable_attributes=["created", "modified"],
)

# Index documents
jobs = [
    JobDocument(
        id="job-1",
        title="Senior Python Developer",
        description="We're looking for...",
        url="/jobs/senior-python-developer",
        company_name="Acme Corp",
        location="San Francisco, CA",
        remote=True,
        job_types=["Full-time", "Remote"],
        created=datetime.now(),
    )
]

await search_service.index_documents("jobs", jobs)
```

### Searching

```python
from pydotorg.core.search.schemas import SearchQuery

# Simple search
query = SearchQuery(query="python developer", limit=10)
results = await search_service.search(query)

# Filtered search
query = SearchQuery(
    query="python",
    indexes=["jobs", "events"],
    filters={"remote": True},
    limit=20,
    offset=0,
)
results = await search_service.search(query)
```

### API Endpoints

#### POST /api/v1/search
Search across all content types.

**Request Body:**
```json
{
  "query": "python developer",
  "indexes": ["jobs", "events"],
  "limit": 20,
  "offset": 0
}
```

**Response:**
```json
{
  "hits": [
    {
      "id": "job-1",
      "index": "jobs",
      "title": "Senior Python Developer",
      "description": "...",
      "url": "/jobs/senior-python-developer",
      "content_type": "job",
      "created": "2025-11-26T10:00:00Z"
    }
  ],
  "total": 42,
  "offset": 0,
  "limit": 20,
  "processing_time_ms": 15,
  "query": "python developer"
}
```

#### GET /api/v1/search/autocomplete?q=python&limit=5
Get autocomplete suggestions.

**Response:**
```json
[
  {
    "id": "job-1",
    "title": "Senior Python Developer",
    "url": "/jobs/senior-python-developer",
    "type": "job"
  }
]
```

### Web Interface

- **GET /search** - Main search page with filters
- **GET /search?q=python** - Search results page
- **GET /search/results?q=python** - htmx-compatible results partial

## Index Definitions

### Jobs Index
```python
JobDocument(
    id: str,                    # Unique job ID
    title: str,                 # Job title
    description: str,           # Job description
    company_name: str,          # Company name
    location: str,              # Job location
    remote: bool,               # Remote position
    job_types: list[str],       # ["Full-time", "Contract"]
    url: str,                   # /jobs/{slug}
    created: datetime,
    status: str,                # "approved"
)
```

### Events Index
```python
EventDocument(
    id: str,
    title: str,
    description: str,
    venue: str,
    location: str,
    start_date: datetime,
    end_date: datetime,
    url: str,
    created: datetime,
)
```

### Blogs Index
```python
BlogDocument(
    id: str,
    title: str,
    description: str,
    content: str,
    author: str,
    published: datetime,
    url: str,
    tags: list[str],
)
```

### Pages Index
```python
PageDocument(
    id: str,
    title: str,
    description: str,
    content: str,
    path: str,
    url: str,
    created: datetime,
    modified: datetime,
)
```

## Index Management

### Creating Indexes
```python
await search_service.create_index("jobs", primary_key="id")
```

### Configuring Indexes
```python
await search_service.configure_index(
    "jobs",
    searchable_attributes=["title", "description", "company_name"],
    filterable_attributes=["remote", "status"],
    sortable_attributes=["created"],
    ranking_rules=[
        "words",
        "typo",
        "proximity",
        "attribute",
        "sort",
        "exactness",
        "created:desc",
    ],
)
```

### Updating Documents
```python
await search_service.update_documents("jobs", updated_jobs)
```

### Deleting Documents
```python
await search_service.delete_documents("jobs", ["job-1", "job-2"])
```

### Clearing Index
```python
await search_service.clear_index("jobs")
```

### Deleting Index
```python
await search_service.delete_index("jobs")
```

## Best Practices

1. **Index on Creation/Update**: Index documents when they're created or updated
2. **Batch Operations**: Use batch operations for multiple documents
3. **Configure Indexes**: Set up searchable/filterable attributes for optimal performance
4. **Filter by Status**: Only index approved/published content
5. **Update on Changes**: Re-index when content is modified
6. **Remove on Delete**: Remove from index when content is deleted

## Example: Indexing Jobs

```python
from pydotorg.domains.jobs.services import JobService
from pydotorg.core.search import SearchService
from pydotorg.core.search.schemas import JobDocument

async def index_approved_jobs():
    job_service = JobService()
    search_service = SearchService()

    # Get approved jobs
    jobs = await job_service.list_by_status(JobStatus.APPROVED, limit=1000)

    # Convert to search documents
    job_docs = [
        JobDocument(
            id=str(job.id),
            title=job.job_title,
            description=job.description or "",
            company_name=job.company_name,
            location=f"{job.city}, {job.country}" if job.city else job.country,
            remote=job.telecommuting,
            job_types=[jt.name for jt in job.job_types],
            url=f"/jobs/{job.slug}",
            created=job.created,
            status=job.status.value,
        )
        for job in jobs
    ]

    # Index in batches of 100
    for i in range(0, len(job_docs), 100):
        batch = job_docs[i:i+100]
        await search_service.index_documents("jobs", batch)
```

## Testing

The search service can be tested using pytest with the provided fixtures:

```python
import pytest
from pydotorg.core.search import SearchService

@pytest.fixture
def search_service():
    return SearchService(url="http://localhost:7700")

async def test_search(search_service):
    query = SearchQuery(query="python", limit=10)
    results = await search_service.search(query)
    assert results.total >= 0
```

## Troubleshooting

### Meilisearch not responding
```bash
# Check if Meilisearch is running
curl http://localhost:7700/health

# Check logs
docker logs meilisearch
```

### Index not found
```bash
# List all indexes
curl http://localhost:7700/indexes

# Create missing index
await search_service.create_index("jobs")
```

### Documents not appearing in search
1. Check if documents were indexed: `await search_service.get_index_stats("jobs")`
2. Verify document format matches schema
3. Check if status field is set correctly
4. Ensure Meilisearch has finished indexing (check `is_indexing` flag)

## Performance Considerations

- **Index Size**: Keep indexes under 10GB for optimal performance
- **Document Count**: Meilisearch handles millions of documents efficiently
- **Search Latency**: Most searches complete in <50ms
- **Batch Size**: Index documents in batches of 100-1000
- **Memory**: Allocate at least 2GB RAM for Meilisearch

## Further Reading

- [Meilisearch Documentation](https://docs.meilisearch.com/)
- [Meilisearch Python SDK](https://github.com/meilisearch/meilisearch-python-sdk)
- [Search Best Practices](https://docs.meilisearch.com/learn/what_is_meilisearch/philosophy.html)

# Blogs Domain

The blogs domain aggregates external blog feeds and displays blog entries. It does NOT host original blog content - instead, it fetches and displays content from external RSS/Atom feeds.

## Structure

```
blogs/
├── __init__.py           # Domain exports
├── models.py             # SQLAlchemy models
├── schemas.py            # Pydantic schemas
├── repositories.py       # Database access layer
├── services.py           # Business logic
├── dependencies.py       # Dependency injection
├── controllers.py        # API and HTML controllers
└── README.md            # This file
```

## Models

### Feed
Represents an external blog feed source.

- `name`: Feed name
- `website_url`: Website URL
- `feed_url`: RSS/Atom feed URL (unique)
- `last_fetched`: Last fetch timestamp
- `is_active`: Active status flag
- Relationships: One-to-many with `BlogEntry`

### BlogEntry
Individual blog post from a feed.

- `feed_id`: Foreign key to Feed
- `title`: Entry title
- `summary`: Short summary (optional)
- `content`: Full content (optional)
- `url`: Entry URL
- `pub_date`: Publication date
- `guid`: Unique identifier for deduplication (unique)
- Relationships: Many-to-one with `Feed`

### FeedAggregate
Groups multiple feeds together.

- `name`: Aggregate name
- `slug`: URL-friendly slug
- `description`: Description (optional)
- Relationships: Many-to-many with `Feed` via `feed_aggregate_feeds`

### RelatedBlog
External blog links for reference.

- `blog_name`: Blog name
- `blog_website`: Blog URL
- `description`: Description (optional)

## API Endpoints

### Feeds
- `GET /api/v1/feeds` - List all feeds
- `GET /api/v1/feeds/{feed_id}` - Get feed by ID
- `GET /api/v1/feeds/active` - List active feeds
- `POST /api/v1/feeds` - Create feed
- `PUT /api/v1/feeds/{feed_id}` - Update feed
- `DELETE /api/v1/feeds/{feed_id}` - Delete feed
- `POST /api/v1/feeds/{feed_id}/fetch` - Fetch feed entries

### Blog Entries
- `GET /api/v1/blog-entries` - List all entries
- `GET /api/v1/blog-entries/{entry_id}` - Get entry by ID
- `GET /api/v1/blog-entries/recent` - List recent entries
- `GET /api/v1/blog-entries/feed/{feed_id}` - List entries by feed
- `POST /api/v1/blog-entries` - Create entry
- `PUT /api/v1/blog-entries/{entry_id}` - Update entry
- `DELETE /api/v1/blog-entries/{entry_id}` - Delete entry

### Feed Aggregates
- `GET /api/v1/feed-aggregates` - List all aggregates
- `GET /api/v1/feed-aggregates/{aggregate_id}` - Get aggregate by ID
- `GET /api/v1/feed-aggregates/slug/{slug}` - Get aggregate by slug
- `POST /api/v1/feed-aggregates` - Create aggregate
- `PUT /api/v1/feed-aggregates/{aggregate_id}` - Update aggregate
- `DELETE /api/v1/feed-aggregates/{aggregate_id}` - Delete aggregate

### Related Blogs
- `GET /api/v1/related-blogs` - List all related blogs
- `GET /api/v1/related-blogs/{blog_id}` - Get related blog by ID
- `POST /api/v1/related-blogs` - Create related blog
- `PUT /api/v1/related-blogs/{blog_id}` - Update related blog
- `DELETE /api/v1/related-blogs/{blog_id}` - Delete related blog

## HTML Pages
- `GET /blogs/` - Main blogs index page
- `GET /blogs/feed/{slug}/` - Feed detail page

## Key Features

### RSS/Atom Feed Parsing
The `FeedService.fetch_feed()` method uses `feedparser` to parse external feeds and create/update blog entries:

```python
entries = await feed_service.fetch_feed(feed)
```

Features:
- Handles both RSS and Atom formats
- Uses GUID for deduplication
- Extracts title, summary, content, publication date
- Updates existing entries if GUID matches
- Logs errors for problematic feeds

### Background Tasks
Feed fetching should be scheduled as a background task using SAQ:

```python
from datetime import datetime, timedelta

cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
feeds_needing_update = await feed_service.get_feeds_needing_update(cutoff_time)

for feed in feeds_needing_update:
    await feed_service.fetch_feed(feed)
```

### Entry Listing
Get recent entries across all feeds:

```python
recent_entries = await blog_entry_service.get_recent_entries(limit=20)
```

Get entries for a specific feed:

```python
entries = await blog_entry_service.get_by_feed_id(feed_id, limit=100)
```

### Feed Aggregates
Group feeds and fetch entries from all feeds in the group:

```python
aggregate, entries = await feed_aggregate_service.get_entries_for_aggregate(aggregate_id)
```

## Dependencies

Required Python packages:
- `feedparser` - RSS/Atom feed parsing
- `sqlalchemy` - Database ORM
- `advanced-alchemy` - Repository pattern
- `litestar` - Web framework
- `pydantic` - Schema validation

## Usage Example

```python
from pydotorg.domains.blogs import FeedService, BlogEntryService

async def fetch_blog_feed():
    feed = await feed_service.create({
        "name": "Python Blog",
        "website_url": "https://blog.python.org",
        "feed_url": "https://blog.python.org/feeds/posts/default",
        "is_active": True,
    })

    entries = await feed_service.fetch_feed(feed)
    print(f"Fetched {len(entries)} entries")

    recent = await blog_entry_service.get_recent_entries(limit=10)
    for entry in recent:
        print(f"{entry.title} - {entry.pub_date}")
```

## Database Migrations

When adding/modifying models, generate and apply migrations:

```bash
uv run alembic revision --autogenerate -m "Add blogs domain models"
uv run alembic upgrade head
```

## Testing

Write tests for:
- Feed fetching and parsing
- Entry deduplication via GUID
- Aggregate entry retrieval
- Error handling for malformed feeds
- Repository methods
- Service business logic

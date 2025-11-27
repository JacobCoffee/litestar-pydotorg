# SAQ Background Tasks

This module configures SAQ (Simple Async Queue) for asynchronous task processing in the litestar-pydotorg application.

## Overview

SAQ provides:
- Async task processing with Redis backend
- Scheduled tasks via cron jobs
- Worker pools with configurable concurrency
- Task retry mechanisms
- Clean shutdown handling

## Architecture

```
tasks/
├── __init__.py          # Package exports
├── worker.py            # SAQ worker configuration
├── feeds.py             # RSS/Atom feed processing tasks
├── search.py            # Search indexing tasks
└── README.md           # This file
```

## Configuration

### Environment Variables

```bash
# Redis URL for task queue (default: redis://localhost:6379/0)
REDIS_URL=redis://localhost:6379/0

# Optional: Set concurrency in URL
REDIS_URL=redis://localhost:6379/0?concurrency=20

# Database URL (inherited from main config)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pydotorg
```

### Worker Settings

The worker is configured in `worker.py`:

```python
settings_dict = {
    "queue": queue,                    # Redis queue instance
    "functions": TASK_FUNCTIONS,       # List of task functions
    "concurrency": WORKER_CONCURRENCY, # Number of concurrent workers
    "cron_jobs": CRON_JOBS,           # Scheduled tasks
    "startup": startup,                # Startup hook
    "shutdown": shutdown,              # Shutdown hook
    "before_process": before_process,  # Pre-task hook
    "after_process": after_process,    # Post-task hook
}
```

## Running the Worker

### Development

```bash
# Start Redis (if not running)
docker run -d -p 6379:6379 redis:7-alpine

# Run the worker
uv run saq pydotorg.tasks.worker.settings_dict

# With verbose logging
uv run saq pydotorg.tasks.worker.settings_dict --verbose

# With specific concurrency
REDIS_URL=redis://localhost:6379/0?concurrency=5 uv run saq pydotorg.tasks.worker.settings_dict
```

### Production

```bash
# Run with systemd or supervisor
uv run saq pydotorg.tasks.worker.settings_dict --web

# With web interface on port 8080
uv run saq pydotorg.tasks.worker.settings_dict --web --port 8080
```

## Available Tasks

### Feed Tasks (`feeds.py`)

#### `refresh_all_feeds`
Fetches and processes all active RSS/Atom feeds.

**Schedule**: Every 6 hours (cron: `0 */6 * * *`)

**Manual trigger**:
```python
from pydotorg.tasks import queue
from pydotorg.tasks.feeds import refresh_all_feeds

# Enqueue task
await queue.enqueue("refresh_all_feeds")
```

#### `refresh_single_feed`
Refreshes a specific feed by URL.

**Parameters**:
- `feed_url` (str): URL of the feed to refresh

**Manual trigger**:
```python
await queue.enqueue(
    "refresh_single_feed",
    feed_url="https://blog.python.org/feeds/posts/default?alt=rss"
)
```

### Search Tasks (`search.py`)

#### `rebuild_search_index`
Rebuilds the entire Meilisearch index.

**Schedule**: Daily at 2 AM (cron: `0 2 * * *`)

**Manual trigger**:
```python
await queue.enqueue("rebuild_search_index")
```

#### `index_content`
Indexes a single piece of content.

**Parameters**:
- `content_type` (str): Type of content (page, blog, job, etc.)
- `content_id` (str): ID of the content to index

**Manual trigger**:
```python
await queue.enqueue(
    "index_content",
    content_type="page",
    content_id="abc-123"
)
```

## Adding New Tasks

### 1. Create Task Module

Create a new file in `tasks/` (e.g., `email.py`):

```python
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def send_welcome_email(ctx: dict[str, Any], user_id: str) -> dict[str, bool]:
    """Send welcome email to new user.

    Args:
        ctx: SAQ worker context with database session maker
        user_id: ID of the user to email

    Returns:
        Dictionary with success status
    """
    session_maker = ctx["session_maker"]

    async with session_maker() as session:
        # Your task logic here
        logger.info("Welcome email sent", extra={"user_id": user_id})
        return {"success": True}
```

### 2. Register Task in Worker

Update `worker.py`:

```python
from pydotorg.tasks.email import send_welcome_email

TASK_FUNCTIONS: list[Callable[..., Any]] = [
    # ... existing tasks
    send_welcome_email,
]
```

### 3. Enqueue from Application

```python
from litestar import post
from pydotorg.tasks import queue


@post("/api/users")
async def create_user(...) -> User:
    user = await user_service.create(...)

    # Enqueue welcome email task
    await queue.enqueue("send_welcome_email", user_id=str(user.id))

    return user
```

## Adding Scheduled Tasks (Cron Jobs)

Add to `worker.py`:

```python
CRON_JOBS: list[CronJob] = [
    # ... existing jobs
    CronJob(
        function=send_weekly_digest,
        cron="0 9 * * 1",  # Every Monday at 9 AM
        unique=True,
    ),
]
```

### Cron Format

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-7, Sunday=0 or 7)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Examples**:
- `0 */6 * * *` - Every 6 hours
- `0 2 * * *` - Daily at 2 AM
- `*/15 * * * *` - Every 15 minutes
- `0 9 * * 1` - Every Monday at 9 AM
- `0 0 1 * *` - First day of every month at midnight

## Monitoring

### Web Interface

SAQ provides a built-in web interface:

```bash
uv run saq pydotorg.tasks.worker.settings_dict --web --port 8080
```

Access at: http://localhost:8080

### Logging

All tasks log to the application logger with structured metadata:

```python
logger.info(
    "Task completed",
    extra={
        "task_name": "refresh_all_feeds",
        "feeds_processed": 10,
        "entries_created": 25,
    }
)
```

### Redis Inspection

```bash
# Connect to Redis CLI
redis-cli

# List all queues
KEYS saq:*

# Get queue length
LLEN saq:default:queued

# Monitor commands
MONITOR
```

## Error Handling

### Automatic Retries

SAQ automatically retries failed tasks with exponential backoff:

```python
await queue.enqueue(
    "refresh_single_feed",
    feed_url="...",
    retries=3,  # Retry up to 3 times
)
```

### Custom Error Handling

```python
async def my_task(ctx: dict[str, Any], param: str) -> dict[str, Any]:
    try:
        # Task logic
        return {"success": True}
    except SpecificError as e:
        logger.error("Specific error occurred", extra={"error": str(e)})
        raise  # Re-raise for SAQ retry
    except Exception as e:
        logger.exception("Unexpected error")
        return {"success": False, "error": str(e)}
```

## Testing

### Unit Tests

```python
import pytest
from pydotorg.tasks.feeds import refresh_all_feeds


@pytest.mark.asyncio
async def test_refresh_all_feeds(db_session):
    ctx = {"session_maker": lambda: db_session}

    result = await refresh_all_feeds(ctx)

    assert result["feeds_processed"] >= 0
    assert result["entries_created"] >= 0
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_task_enqueue(test_queue):
    job = await test_queue.enqueue("refresh_all_feeds")

    assert job.function == "refresh_all_feeds"
    assert job.status == "queued"
```

## Best Practices

1. **Idempotency**: Tasks should be safe to run multiple times
2. **Small Tasks**: Break large operations into smaller tasks
3. **Error Logging**: Always log errors with context
4. **Resource Cleanup**: Use context managers for DB sessions
5. **Timeouts**: Set appropriate timeouts for long-running tasks
6. **Monitoring**: Track task duration and success rates

## Troubleshooting

### Worker Won't Start

```bash
# Check Redis connectivity
redis-cli ping

# Check Redis URL in environment
echo $REDIS_URL

# Run with verbose logging
uv run saq pydotorg.tasks.worker.settings_dict --verbose
```

### Tasks Stuck in Queue

```bash
# Clear failed jobs
redis-cli DEL saq:default:failed

# Clear entire queue (CAUTION)
redis-cli FLUSHDB
```

### Database Connection Issues

Check the worker startup logs for database connection errors. Ensure:
- `DATABASE_URL` is set correctly
- Database is accessible from worker process
- Connection pool settings are appropriate for worker concurrency

## References

- [SAQ Documentation](https://github.com/tobymao/saq)
- [Redis Documentation](https://redis.io/documentation)
- [Crontab Guru](https://crontab.guru/) - Cron expression helper

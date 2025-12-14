# Debugging Guide

This guide covers debugging techniques and tools for litestar-pydotorg.

## Debug Mode

### Enable Debug Mode

Set in your `.env` file:

```bash
DEBUG=true
```

This enables:
- Detailed error pages with stack traces
- SQL query logging
- Debug toolbar (if installed)
- More verbose logging

### Database Query Logging

```bash
# In .env
DATABASE_ECHO=true
```

All SQL queries will be logged to console.

## Using Breakpoints

### Python Built-in Debugger

```python
# Add breakpoint in code
breakpoint()

# When execution reaches this line, you'll enter pdb
```

Common pdb commands:
- `n` - Next line
- `s` - Step into function
- `c` - Continue execution
- `l` - List source code
- `p variable` - Print variable
- `q` - Quit debugger

### IPython Debugger

For a better debugging experience, use ipdb:

```python
import ipdb; ipdb.set_trace()
```

Install with:

```bash
uv pip install ipdb
```

## Logging

### Basic Logging

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")

# Log with exception info
try:
    risky_operation()
except Exception:
    logger.error("Operation failed", exc_info=True)
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info("user_created", user_id="123", email="test@example.com")
logger.error("operation_failed", error_code="E001", details={"reason": "timeout"})
```

### Configure Log Level

```bash
# In .env
LOG_LEVEL=DEBUG
```

## Debugging HTTP Requests

### Request Inspection

```python
from litestar import Request, get

@get("/debug")
async def debug_endpoint(request: Request) -> dict:
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "path_params": request.path_params,
    }
```

### Response Debugging

```python
from litestar import Response

@get("/debug-response")
async def debug_response() -> Response:
    response = Response(
        content={"message": "debug"},
        headers={"X-Debug": "true"}
    )
    # Log response before sending
    logger.debug(f"Response: {response}")
    return response
```

## Database Debugging

### Query Inspection

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    logger.debug(f"SQL: {statement}")
    logger.debug(f"Params: {parameters}")
```

### Connection Pool Status

```python
from pydotorg.core.database import engine

# Check pool status
pool = engine.pool
logger.info(f"Pool size: {pool.size()}")
logger.info(f"Checked out: {pool.checkedout()}")
logger.info(f"Overflow: {pool.overflow()}")
```

### Interactive Database Shell

```bash
# PostgreSQL shell
psql $DATABASE_URL

# Python shell with app context
uv run python scripts/shell.py
```

## Debugging Background Tasks

### SAQ Worker Logging

```bash
# Start worker with verbose logging
LOG_LEVEL=DEBUG uv run python -m saq worker pydotorg.tasks.base.worker
```

### Task Inspection

```python
from pydotorg.tasks.base import queue

# Get queue status
async def check_queue():
    stats = await queue.stats()
    logger.info(f"Queue stats: {stats}")

    # List pending jobs
    jobs = await queue.jobs()
    for job in jobs:
        logger.info(f"Job: {job.id}, Status: {job.status}")
```

## Memory Debugging

### Memory Profiling

```python
import tracemalloc

tracemalloc.start()

# ... your code ...

current, peak = tracemalloc.get_traced_memory()
logger.info(f"Current memory: {current / 10**6:.1f} MB")
logger.info(f"Peak memory: {peak / 10**6:.1f} MB")
tracemalloc.stop()
```

### Object Reference Tracking

```python
import gc
import sys

# Force garbage collection
gc.collect()

# Count objects of a type
user_count = sum(1 for obj in gc.get_objects() if isinstance(obj, User))
logger.info(f"User objects in memory: {user_count}")
```

## Performance Debugging

### Request Timing Middleware

```python
import time
from litestar import Litestar, Request
from litestar.middleware import MiddlewareProtocol

class TimingMiddleware(MiddlewareProtocol):
    async def __call__(self, scope, receive, send):
        start = time.perf_counter()
        await self.app(scope, receive, send)
        elapsed = time.perf_counter() - start
        logger.info(f"Request took {elapsed:.3f}s")
```

### Profile Specific Code

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Code to profile
    result = expensive_operation()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumulative")
    stats.print_stats(10)  # Top 10 functions

    return result
```

## Debugging Tests

### Run Single Test with Output

```bash
uv run pytest tests/unit/test_file.py::test_name -v -s
```

### Debug Failing Tests

```bash
# Enter debugger on failure
uv run pytest --pdb

# Enter debugger on first failure and stop
uv run pytest -x --pdb
```

### Show Local Variables

```bash
uv run pytest -l  # Show locals in tracebacks
```

## IDE Debugging

### VS Code

1. Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Litestar",
      "type": "python",
      "request": "launch",
      "module": "litestar",
      "args": ["run", "--reload"],
      "env": {
        "LITESTAR_APP": "pydotorg.main:app"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

2. Set breakpoints by clicking in the gutter
3. Press F5 to start debugging

### PyCharm

1. Right-click on file and select "Debug"
2. Set breakpoints by clicking in the gutter
3. Use debug panel to inspect variables

## Common Issues

### Import Errors

```bash
# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify package installation
uv pip show pydotorg
```

### Connection Issues

```bash
# Test database connection
uv run python -c "
from pydotorg.core.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        await conn.execute('SELECT 1')
        print('Database OK')
asyncio.run(test())
"

# Test Redis connection
uv run python -c "
import redis
r = redis.from_url('redis://localhost:6379')
print('Redis:', r.ping())
"
```

### Environment Issues

```bash
# Print all environment variables
uv run python -c "
import os
for key, value in sorted(os.environ.items()):
    if 'PYDOTORG' in key or 'DATABASE' in key:
        print(f'{key}={value}')
"
```

## Troubleshooting Checklist

1. Check if services are running: `docker-compose ps`
2. Verify environment variables: `cat .env`
3. Check database connection: `psql $DATABASE_URL -c "SELECT 1"`
4. Check Redis connection: `redis-cli ping`
5. Review logs: `docker-compose logs -f`
6. Clear cache: `redis-cli FLUSHALL`
7. Restart services: `make infra-down && make infra-up`
8. Reinstall dependencies: `make install`

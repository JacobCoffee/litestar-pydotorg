# ADR-002: Use SAQ for Background Task Processing

## Status

Accepted

## Context

The Django python.org application currently uses Celery for background task processing. During the Litestar migration, we need to choose a task queue system that:

### Problem Statement

- Celery has significant complexity overhead for our use cases
- Celery's async support is still maturing
- We want native async/await task processing
- Current tasks are relatively simple (cache updates, email sending, event imports)
- Need reliable task scheduling and retry logic

### Constraints

- Must support async/await natively
- Must integrate well with our async stack (Litestar, SQLAlchemy 2.0)
- Must support Redis (already in our stack)
- Must handle scheduled/periodic tasks
- Must provide retry logic with backoff
- Should be simpler to operate than Celery

### Requirements

**Functional Requirements**:
- Enqueue async tasks
- Schedule periodic tasks (cron-like)
- Retry failed tasks with exponential backoff
- Task result tracking
- Dead letter queue for failed tasks
- Multiple workers for concurrency

**Non-Functional Requirements**:
- Low latency task processing (< 1 second)
- Handle 1000+ tasks per hour
- Simple deployment and monitoring
- Minimal operational overhead
- Python 3.12+ compatibility

## Decision

We will use **SAQ (Simple Async Queue)** as the background task processing system.

### Chosen Solution

SAQ provides:
- Native async/await support
- Redis-based queue (simple, reliable)
- Built-in cron scheduling
- Exponential backoff retry logic
- Task timeouts and cancellation
- Dead letter queue
- Simple worker process
- Minimal configuration

### Rationale

1. **Async Native**: Written for async Python from the ground up
2. **Simplicity**: Much simpler than Celery, easier to understand and debug
3. **Performance**: Excellent performance for async tasks
4. **Redis Integration**: Works seamlessly with our existing Redis instance
5. **Maintenance**: Smaller codebase, easier to contribute fixes if needed
6. **Modern**: Actively maintained with Python 3.12+ support

## Consequences

### Positive Consequences

- **Simplicity**: Significantly less complexity than Celery
- **Performance**: Native async processing, no thread/process overhead
- **Integration**: Seamless integration with async SQLAlchemy and Litestar
- **Debugging**: Easier to debug with simpler architecture
- **Resource Usage**: Lower memory footprint than Celery
- **Development Velocity**: Faster to implement and test tasks

### Negative Consequences

- **Ecosystem**: Smaller ecosystem compared to Celery
- **Features**: Fewer advanced features (canvas, chord, etc.)
- **Community**: Smaller community, less Stack Overflow content
- **Battle Testing**: Less proven at massive scale
- **Monitoring**: Fewer monitoring tool integrations

### Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SAQ can't handle load | Low | High | Load test extensively, have Celery as fallback |
| Missing critical feature | Low | Medium | Contribute to SAQ or implement custom |
| Project abandonment | Low | High | Fork if needed, evaluate alternatives annually |
| Complex task requirements | Medium | Low | Re-evaluate if needs exceed SAQ capabilities |

### Migration Path

1. **Week 1**: Install SAQ, configure workers
2. **Week 2**: Migrate simple tasks (cache updates, email)
3. **Week 3**: Migrate scheduled tasks (periodic updates)
4. **Week 4**: Migrate complex tasks (event imports, search indexing)
5. **Week 5**: Performance testing and optimization
6. **Week 6**: Production deployment with monitoring

## Alternatives Considered

### Alternative 1: Keep Celery

**Description**: Continue using Celery with async worker support

**Pros**:
- Already familiar to team
- Battle-tested at massive scale
- Rich ecosystem of plugins
- Excellent monitoring tools (Flower, Prometheus exporters)
- Comprehensive documentation
- Supports many backends (RabbitMQ, Redis, SQS)

**Cons**:
- Complex architecture with many moving parts
- Async support still maturing
- Heavy resource usage (processes/threads)
- Verbose configuration
- Difficult to debug
- Designed for sync tasks primarily

**Why not chosen**: Celery's complexity outweighs benefits for our use case. Our task requirements are simple enough that SAQ's feature set is sufficient, and SAQ's native async support aligns better with our stack.

### Alternative 2: Arq

**Description**: Another async task queue for Python

**Pros**:
- Async native
- Redis-based
- Simple API
- Good documentation
- Designed by Samuel Colvin (Pydantic author)

**Cons**:
- Less active development than SAQ
- Fewer features than SAQ
- No built-in cron scheduling
- Smaller community
- Less flexible retry logic

**Why not chosen**: SAQ has more active development, better scheduling support, and more features while maintaining simplicity. SAQ's retry logic and dead letter queue are more sophisticated.

### Alternative 3: RQ (Redis Queue)

**Description**: Simple Redis-based task queue

**Pros**:
- Very simple
- Well-documented
- Stable and mature
- Good monitoring tools
- Large community

**Cons**:
- No native async support
- Requires sync-to-async adapters
- Thread-based workers
- Less efficient for async tasks
- No built-in scheduling

**Why not chosen**: Lack of native async support is a dealbreaker. Using sync tasks with our async stack would create unnecessary complexity and performance overhead.

### Alternative 4: TaskIQ

**Description**: Modern async task queue with broker abstraction

**Pros**:
- Async native
- Multiple broker support (Redis, RabbitMQ, Kafka)
- Good scheduling support
- Modern design
- Type-safe

**Cons**:
- Newer project, less proven
- More complex than SAQ
- Heavier dependencies
- Smaller community

**Why not chosen**: While TaskIQ is promising, it's more complex than we need, and SAQ's focus on Redis simplicity better fits our requirements.

## Implementation Notes

### Timeline

- **Setup**: 1 week
- **Simple Task Migration**: 1 week
- **Scheduled Task Migration**: 1 week
- **Complex Task Migration**: 1 week
- **Testing & Optimization**: 1 week
- **Production Deployment**: 1 week
- **Total**: ~6 weeks

### Dependencies

- **SAQ**: Latest stable version
- **Redis**: 7.x (already in stack)
- **Croniter**: For cron scheduling
- **Integration**: Custom Litestar plugin for task management

### Success Criteria

- All Celery tasks migrated successfully
- Task processing latency < 1 second (p95)
- Handle 1000+ tasks per hour
- Zero task loss during failures
- Successful retry of failed tasks
- Scheduled tasks run on time (within 1 minute)

### Rollback Strategy

If SAQ proves insufficient:

1. **Immediate**: Keep Celery workers running in parallel during transition
2. **Short-term**: Route tasks back to Celery
3. **Long-term**: Full migration back to Celery if needed

Maintain Celery configuration for 60 days post-migration.

## Task Migration Examples

### Simple Task (Django Celery → SAQ)

**Before (Celery)**:
```python
# tasks.py
from celery import shared_task

@shared_task
def update_download_boxes():
    service = ReleaseService()
    service.update_boxes()
```

**After (SAQ)**:
```python
# tasks/downloads.py
from saq import Queue
from pydotorg.domains.downloads.services import ReleaseService

async def update_download_boxes(ctx: dict) -> None:
    async with get_db_session() as session:
        service = ReleaseService(session)
        await service.update_boxes()

# Enqueue
await queue.enqueue("update_download_boxes")
```

### Scheduled Task

**Before (Celery Beat)**:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'update-boxes': {
        'task': 'tasks.update_download_boxes',
        'schedule': crontab(hour='*/6'),
    },
}
```

**After (SAQ Cron)**:
```python
# On app startup
await queue.schedule(
    "update_download_boxes",
    cron="0 */6 * * *",  # Every 6 hours
)
```

## Monitoring Strategy

### Metrics to Track

- Task queue length
- Task processing time (p50, p95, p99)
- Task failure rate
- Worker utilization
- Dead letter queue size

### Implementation

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

task_counter = Counter('saq_tasks_total', 'Total tasks', ['task_name', 'status'])
task_duration = Histogram('saq_task_duration_seconds', 'Task duration', ['task_name'])

# In task wrapper
async def tracked_task(ctx: dict) -> None:
    start = time.time()
    try:
        await original_task(ctx)
        task_counter.labels(task_name=ctx['task'], status='success').inc()
    except Exception:
        task_counter.labels(task_name=ctx['task'], status='failure').inc()
        raise
    finally:
        duration = time.time() - start
        task_duration.labels(task_name=ctx['task']).observe(duration)
```

## References

- [SAQ Documentation](https://saq-py.readthedocs.io/)
- [SAQ GitHub Repository](https://github.com/tobymao/saq)
- [Celery Async Workers](https://docs.celeryproject.org/en/stable/userguide/workers.html#asynchronous-workers)
- [Async Task Queue Comparison](https://github.com/asyncio-docs/asyncio-task-queues)

## Metadata

- **Author**: ARCHITECT Agent
- **Date**: 2025-11-25
- **Reviewers**: TBD
- **Related ADRs**: ADR-001 (Litestar Framework)
- **Tags**: background-tasks, async, infrastructure, performance

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-25 | ARCHITECT | Initial version |

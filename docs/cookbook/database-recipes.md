# Database Recipes

Common database patterns and query recipes for litestar-pydotorg.

## Basic Queries

### Get by ID

```python
async def get_by_id(session: AsyncSession, model_id: UUID) -> Model | None:
    return await session.get(Model, model_id)
```

### Get All with Pagination

```python
from sqlalchemy import select

async def list_all(
    session: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Model]:
    query = select(Model).limit(limit).offset(offset)
    result = await session.execute(query)
    return result.scalars().all()
```

### Get with Filters

```python
async def list_filtered(
    session: AsyncSession,
    *,
    is_active: bool | None = None,
    category: str | None = None,
) -> Sequence[Model]:
    query = select(Model)

    if is_active is not None:
        query = query.where(Model.is_active == is_active)

    if category is not None:
        query = query.where(Model.category == category)

    result = await session.execute(query)
    return result.scalars().all()
```

## Relationship Loading

### Eager Loading (Prevent N+1)

```python
from sqlalchemy.orm import selectinload, joinedload

async def get_with_relations(
    session: AsyncSession,
    user_id: UUID,
) -> User | None:
    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.posts),
            selectinload(User.comments),
            joinedload(User.profile),
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()
```

### Lazy Loading (When Needed)

```python
async def get_user_posts(
    session: AsyncSession,
    user: User,
) -> Sequence[Post]:
    # Explicitly load relationship
    await session.refresh(user, ["posts"])
    return user.posts
```

### Subquery Loading for Collections

```python
from sqlalchemy.orm import subqueryload

async def list_users_with_posts(session: AsyncSession) -> Sequence[User]:
    query = (
        select(User)
        .options(subqueryload(User.posts))
        .where(User.is_active == True)
    )
    result = await session.execute(query)
    return result.scalars().unique().all()
```

## Advanced Queries

### Search with ILIKE

```python
async def search(
    session: AsyncSession,
    query_text: str,
    *,
    limit: int = 20,
) -> Sequence[Model]:
    query = (
        select(Model)
        .where(Model.name.ilike(f"%{query_text}%"))
        .limit(limit)
    )
    result = await session.execute(query)
    return result.scalars().all()
```

### Full-Text Search (PostgreSQL)

```python
from sqlalchemy import func

async def full_text_search(
    session: AsyncSession,
    search_query: str,
) -> Sequence[Model]:
    query = (
        select(Model)
        .where(
            func.to_tsvector('english', Model.title + ' ' + Model.content)
            .match(search_query)
        )
        .order_by(
            func.ts_rank(
                func.to_tsvector('english', Model.title + ' ' + Model.content),
                func.plainto_tsquery('english', search_query)
            ).desc()
        )
    )
    result = await session.execute(query)
    return result.scalars().all()
```

### Aggregate Queries

```python
from sqlalchemy import func

async def get_statistics(session: AsyncSession) -> dict:
    query = select(
        func.count(Model.id).label("total"),
        func.count(Model.id).filter(Model.is_active == True).label("active"),
        func.avg(Model.price).label("avg_price"),
        func.max(Model.created_at).label("latest"),
    )
    result = await session.execute(query)
    row = result.one()

    return {
        "total": row.total,
        "active": row.active,
        "avg_price": float(row.avg_price or 0),
        "latest": row.latest,
    }
```

### Group By with Having

```python
async def get_category_counts(
    session: AsyncSession,
    min_count: int = 5,
) -> list[dict]:
    query = (
        select(
            Model.category,
            func.count(Model.id).label("count"),
        )
        .group_by(Model.category)
        .having(func.count(Model.id) >= min_count)
        .order_by(func.count(Model.id).desc())
    )
    result = await session.execute(query)

    return [
        {"category": row.category, "count": row.count}
        for row in result
    ]
```

### Date Range Queries

```python
from datetime import datetime, timedelta

async def get_recent(
    session: AsyncSession,
    days: int = 7,
) -> Sequence[Model]:
    since = datetime.utcnow() - timedelta(days=days)
    query = (
        select(Model)
        .where(Model.created_at >= since)
        .order_by(Model.created_at.desc())
    )
    result = await session.execute(query)
    return result.scalars().all()


async def get_by_date_range(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> Sequence[Model]:
    query = (
        select(Model)
        .where(Model.created_at >= start_date)
        .where(Model.created_at <= end_date)
        .order_by(Model.created_at)
    )
    result = await session.execute(query)
    return result.scalars().all()
```

## Transactions

### Basic Transaction

```python
async def transfer_funds(
    session: AsyncSession,
    from_id: UUID,
    to_id: UUID,
    amount: float,
) -> None:
    async with session.begin():
        from_account = await session.get(Account, from_id)
        to_account = await session.get(Account, to_id)

        if from_account.balance < amount:
            raise ValueError("Insufficient funds")

        from_account.balance -= amount
        to_account.balance += amount
        # Commits automatically on success
```

### Nested Transactions (Savepoints)

```python
async def process_order(session: AsyncSession, order: Order) -> None:
    async with session.begin_nested():
        try:
            # Process payment
            await process_payment(session, order)

            # Update inventory
            await update_inventory(session, order)

            # Send confirmation
            await send_confirmation(order)
        except PaymentError:
            # Rollback just this savepoint
            raise
```

### Manual Transaction Control

```python
async def bulk_import(session: AsyncSession, items: list[dict]) -> int:
    imported = 0

    try:
        for item in items:
            model = Model(**item)
            session.add(model)
            imported += 1

            # Flush periodically for large imports
            if imported % 100 == 0:
                await session.flush()

        await session.commit()
        return imported
    except Exception:
        await session.rollback()
        raise
```

## Bulk Operations

### Bulk Insert

```python
async def bulk_insert(
    session: AsyncSession,
    items: list[dict],
) -> None:
    models = [Model(**item) for item in items]
    session.add_all(models)
    await session.flush()
```

### Bulk Insert with Returning

```python
from sqlalchemy.dialects.postgresql import insert

async def bulk_insert_returning(
    session: AsyncSession,
    items: list[dict],
) -> list[UUID]:
    stmt = insert(Model).values(items).returning(Model.id)
    result = await session.execute(stmt)
    return [row.id for row in result]
```

### Bulk Update

```python
from sqlalchemy import update

async def bulk_update(
    session: AsyncSession,
    updates: dict[UUID, dict],
) -> int:
    updated = 0
    for model_id, values in updates.items():
        stmt = (
            update(Model)
            .where(Model.id == model_id)
            .values(**values)
        )
        result = await session.execute(stmt)
        updated += result.rowcount
    await session.flush()
    return updated
```

### Upsert (Insert or Update)

```python
from sqlalchemy.dialects.postgresql import insert

async def upsert(
    session: AsyncSession,
    data: dict,
) -> Model:
    stmt = insert(Model).values(**data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Model.external_id],
        set_={
            "name": stmt.excluded.name,
            "updated_at": func.now(),
        }
    ).returning(Model)

    result = await session.execute(stmt)
    return result.scalar_one()
```

## Soft Delete

### Model with Soft Delete

```python
from datetime import datetime

class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class Product(Base, SoftDeleteMixin):
    __tablename__ = "products"
    # ... other fields
```

### Query Non-Deleted

```python
async def list_active(session: AsyncSession) -> Sequence[Product]:
    query = select(Product).where(Product.deleted_at.is_(None))
    result = await session.execute(query)
    return result.scalars().all()
```

### Soft Delete Operation

```python
async def soft_delete(session: AsyncSession, product_id: UUID) -> None:
    product = await session.get(Product, product_id)
    if product:
        product.deleted_at = datetime.utcnow()
        await session.flush()
```

### Restore Soft-Deleted

```python
async def restore(session: AsyncSession, product_id: UUID) -> None:
    query = (
        select(Product)
        .where(Product.id == product_id)
        .where(Product.deleted_at.is_not(None))
    )
    result = await session.execute(query)
    product = result.scalar_one_or_none()

    if product:
        product.deleted_at = None
        await session.flush()
```

## Connection Pool Management

### Check Pool Status

```python
from pydotorg.core.database import engine

def get_pool_status() -> dict:
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount(),
    }
```

### Configure Pool

```python
# In config.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,           # Minimum connections
    max_overflow=10,       # Additional connections allowed
    pool_timeout=30,       # Wait time for connection
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Verify connections before use
)
```

## See Also

- [Domain Patterns](domain-patterns.md) - Using queries in services
- [Testing Recipes](testing-recipes.md) - Testing database operations
- [Architecture](../architecture/DATABASE_SCHEMA.md) - Database schema

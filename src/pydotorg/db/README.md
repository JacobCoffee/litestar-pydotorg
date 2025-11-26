# Database Layer

This directory contains the database migration and seeding infrastructure for the Python.org Litestar rebuild.

## Structure

```
db/
├── __init__.py
├── seed.py              # Database seeding script
├── migrations/
│   ├── env.py           # Alembic environment configuration
│   ├── script.py.mako   # Migration template
│   └── versions/        # Migration version files
│       └── 001_initial_migration.py
```

## Running Migrations

### Apply Migrations

Run all pending migrations to bring the database to the latest schema:

```bash
make db-migrate
# or
uv run alembic upgrade head
```

### Create a New Migration

After modifying models, generate a new migration:

```bash
make db-revision
# or
uv run alembic revision --autogenerate -m "Description of changes"
```

### Downgrade Migration

Rollback the last migration:

```bash
make db-downgrade
# or
uv run alembic downgrade -1
```

### Reset Database

Drop all tables and re-apply migrations (WARNING: Data loss!):

```bash
make db-reset
# or
uv run alembic downgrade base
uv run alembic upgrade head
```

## Seeding the Database

The seeding script creates development data for all domains:

### Seed Development Data

```bash
make db-seed
# or
uv run python -m pydotorg.db.seed
```

This creates:
- 10 users (including admin@python.org / admin123 and test@python.org / test123)
- 5 memberships
- 15 pages
- 4 operating systems (Windows, macOS, Linux, Source)
- 5 Python releases with files
- 5 sponsors
- 5 sponsorships

### Clear Database

Remove all data without dropping tables:

```bash
make db-clear
# or
uv run python -m pydotorg.db.seed clear
```

### Initialize Database

Run migrations and seed data in one command:

```bash
make db-init
```

## Test Accounts

After seeding, you can use these accounts:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Superuser |
| test | test123 | Regular user |

## Using Polyfactory

The seed script uses `polyfactory` to generate realistic test data. Example:

```python
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pydotorg.domains.users.models import User

class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __set_relationships__ = False

    @classmethod
    def password_hash(cls) -> str:
        return bcrypt.hash("password123")

# Generate a single user
user = UserFactory.build()

# Generate multiple users
users = UserFactory.batch(10)
```

## Configuration

Database connection is configured in `src/pydotorg/config.py`:

```python
database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg"
```

Override with environment variable:

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"
```

## Migration Best Practices

1. Always review auto-generated migrations before applying
2. Test migrations on a development database first
3. Create small, focused migrations
4. Include both upgrade() and downgrade() logic
5. Never edit existing migration files after they've been applied

## Async Support

All database operations use SQLAlchemy 2.0 async:

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

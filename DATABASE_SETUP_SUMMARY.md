# Database Layer Setup - Summary

## Overview

The complete database layer has been implemented for the Python.org Litestar rebuild, including migrations, seeding, and health checks.

## Files Created/Modified

### Created Files

1. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/alembic.ini`**
   - Alembic configuration file
   - Configures migration path and logging
   - Uses environment variables for database URL

2. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/__init__.py`**
   - Package initialization for database utilities

3. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/migrations/env.py`**
   - Alembic environment configuration
   - Async engine support
   - Auto-imports all models for migration generation
   - Imported models: User, Membership, UserGroup, Page, Image, DocumentFile, OS, Release, ReleaseFile, Sponsor, Sponsorship

4. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/migrations/script.py.mako`**
   - Migration template for new migrations
   - Follows Python best practices with type hints

5. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/migrations/versions/001_initial_migration.py`**
   - Initial database migration
   - Creates all tables for 4 domains:
     - Users: users, memberships, user_groups
     - Pages: pages, page_images, page_documents
     - Downloads: download_os, releases, release_files
     - Sponsors: sponsors, sponsorships
   - Includes all indexes, constraints, and enums
   - Includes downgrade logic

6. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/seed.py`**
   - Database seeding script using polyfactory
   - Creates development test data
   - Factories for all models
   - Command-line interface for seeding and clearing

7. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/README.md`**
   - Complete documentation for database layer
   - Usage examples and best practices

### Modified Files

1. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/main.py`**
   - Updated health check endpoint
   - Added database connectivity verification
   - Returns HTTP 200 if database is healthy, HTTP 503 if unhealthy
   - Shows database status in response

2. **`/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/Makefile`**
   - Added `make db-seed` - Seed database with development data
   - Added `make db-clear` - Clear all data from database
   - Added `make db-init` - Initialize database (migrate + seed)

## Usage Instructions

### 1. Run Migrations

Apply all migrations to create the database schema:

```bash
make db-migrate
```

Or directly:

```bash
uv run alembic upgrade head
```

### 2. Seed the Database

Populate the database with development data:

```bash
make db-seed
```

Or directly:

```bash
uv run python -m pydotorg.db.seed
```

### 3. Initialize Database (One Command)

Run migrations and seed data together:

```bash
make db-init
```

### 4. Check Health

Verify database connectivity:

```bash
curl http://localhost:8000/health
```

Response when healthy:

```json
{
  "status": "healthy",
  "database": true
}
```

Response when database is unavailable:

```json
{
  "status": "unhealthy",
  "database": false,
  "error": "connection error details"
}
```

## Development Data Created

The seeding script creates:

- **10 Users**
  - `admin@python.org` / `admin123` (superuser)
  - `test@python.org` / `test123` (regular user)
  - 8 additional random users

- **5 Memberships**
  - 1 Fellow member
  - 1 Contributing member
  - 1 Supporting member
  - 2 Basic members

- **15 Pages**
  - Home page (`/`)
  - About page (`/about`)
  - Downloads page (`/downloads`)
  - 12 additional random pages

- **4 Operating Systems**
  - Windows
  - macOS
  - Linux
  - Source

- **5 Python Releases**
  - 3.13.0 (latest, stable)
  - 3.12.7 (stable)
  - 3.11.10 (stable)
  - 3.10.15 (stable)
  - 3.14.0a1 (pre-release)
  - Each with 4 release files (one per OS)

- **5 Sponsors**
  - Python Software Foundation
  - JetBrains
  - Microsoft
  - Google
  - Amazon Web Services

- **5 Sponsorships**
  - 3 finalized
  - 2 approved

## Database Schema

The migration creates tables for all 4 domains:

### Users Domain

- `users` - User accounts with authentication
- `memberships` - PSF membership information
- `user_groups` - Community user groups

### Pages Domain

- `pages` - Content pages with markdown/RST/HTML support
- `page_images` - Page image attachments
- `page_documents` - Page document attachments

### Downloads Domain

- `download_os` - Operating systems (Windows, macOS, Linux, etc.)
- `releases` - Python version releases
- `release_files` - Downloadable files for each release

### Sponsors Domain

- `sponsors` - Sponsor organizations
- `sponsorships` - Sponsorship agreements and status

## Next Steps

1. **Start the Database**
   ```bash
   # If using Docker
   docker-compose up -d postgres

   # If using local PostgreSQL
   # Ensure PostgreSQL is running on localhost:5432
   ```

2. **Run Migrations**
   ```bash
   make db-migrate
   ```

3. **Seed Development Data**
   ```bash
   make db-seed
   ```

4. **Start the Application**
   ```bash
   make serve
   ```

5. **Verify Setup**
   ```bash
   curl http://localhost:8000/health
   ```

## Additional Commands

### Create a New Migration

After modifying models:

```bash
make db-revision
# Enter migration message when prompted
```

### Downgrade One Migration

```bash
make db-downgrade
```

### Reset Database (WARNING: Data Loss)

```bash
make db-reset
```

### Clear All Data

```bash
make db-clear
```

## Technical Details

### Async Support

All database operations use SQLAlchemy 2.0 async with asyncpg:

- Async session management
- Async migrations via Alembic
- Connection pooling configured in `config.py`

### Polyfactory Integration

The seeding script uses polyfactory for realistic test data generation:

```python
class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __set_relationships__ = False

    @classmethod
    def password_hash(cls) -> str:
        return bcrypt.hash("password123")
```

### Health Check

The health endpoint now verifies:

- Application status
- Database connectivity
- Returns appropriate HTTP status codes

### Configuration

Database URL is configured in `src/pydotorg/config.py`:

```python
database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/pydotorg"
```

Override with environment variable:

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"
```

## Testing

Run tests to verify database functionality:

```bash
make test
```

Run tests with coverage:

```bash
make test-cov
```

## Documentation

For more detailed information, see:

- `/Users/coffee/git/public/JacobCoffee/litestar-pydotorg/src/pydotorg/db/README.md`
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Advanced Alchemy Documentation](https://docs.advanced-alchemy.jolt.rs/)

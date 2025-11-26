# SQLAdmin Integration

This module provides a full-featured admin panel for Python.org using SQLAdmin.

## Overview

SQLAdmin provides a modern, user-friendly interface for managing database records through a web UI. It's integrated into the Litestar application and mounted at `/sqladmin`.

## Features

- Full CRUD operations for all domain models
- Search and filtering capabilities
- Sorting and pagination
- Secure authentication requiring superuser privileges
- Integration with Advanced-Alchemy audit fields

## Access

The admin panel is available at: `http://localhost:8000/sqladmin`

## Authentication

Access to the admin panel requires:
- A valid user account
- `is_superuser=True` flag set on the user
- `is_active=True` flag set on the user

The authentication backend validates credentials against the User model and creates a secure session.

## Available Admin Views

### User Management
- **Users**: Manage user accounts, permissions, and profiles
- **Memberships**: PSF membership records and voting eligibility
- **User Groups**: Community groups, meetups, and mailing lists

### Jobs
- **Jobs**: Job board postings with status management
- **Job Types**: Employment types (full-time, contract, etc.)
- **Job Categories**: Job classification categories
- **Job Review Comments**: Internal review comments for job postings

### Events
- **Events**: Community events and conferences
- **Calendars**: Event calendar management
- **Event Categories**: Event classification
- **Event Locations**: Venue information
- **Event Occurrences**: Individual event dates/times

### Sponsors
- **Sponsors**: PSF sponsor organizations
- **Sponsorships**: Sponsorship contracts and agreements
- **Sponsorship Levels**: Sponsor tier definitions (Platinum, Gold, etc.)

### Content Management
- **Pages**: CMS pages with markdown/RST/HTML support
- **Page Images**: Uploaded images for pages
- **Page Documents**: Attached documents for pages
- **Blog Entries**: Aggregated blog posts
- **Feeds**: RSS feed sources
- **Feed Aggregates**: Grouped feed collections
- **Related Blogs**: External Python-related blogs

## Model View Configuration

Each model view is configured with:
- **column_list**: Columns displayed in list view
- **column_searchable_list**: Fields available for search
- **column_sortable_list**: Fields that can be sorted
- **column_default_sort**: Default sort order
- **form_excluded_columns**: Fields hidden from forms

## Architecture

### File Structure

```
src/pydotorg/domains/sqladmin/
├── __init__.py           # Public exports
├── auth.py              # Authentication backend
├── config.py            # Plugin configuration
├── views.py             # Model view definitions
└── README.md            # This file
```

### Components

1. **AdminAuthBackend** (`auth.py`)
   - Handles login/logout/authentication
   - Validates superuser status
   - Manages secure sessions

2. **SQLAdminConfig** (`config.py`)
   - Custom Litestar plugin implementation
   - Integrates SQLAdmin with Litestar's ASGI router
   - Mounts admin interface at `/sqladmin`

3. **ModelView Classes** (`views.py`)
   - One view class per model
   - Uses SQLAdmin's `ModelView` base class
   - AuditModelView for models with audit fields

## Integration with Litestar

The admin panel is integrated as a Litestar plugin in `main.py`:

```python
from pydotorg.domains.sqladmin import create_sqladmin_plugin

sqladmin_plugin = create_sqladmin_plugin(
    engine=sqlalchemy_config.get_engine(),
    session_maker=sqlalchemy_config.create_session_maker(),
    secret_key=settings.session_secret_key,
)

app = Litestar(
    plugins=[sqlalchemy_plugin, sqladmin_plugin],
    ...
)
```

## Security Considerations

- Admin access is restricted to superusers only
- Sessions are encrypted with `session_secret_key` from settings
- All database operations use the async SQLAlchemy engine
- Authentication state is validated on every request
- Password hashes are never exposed in the UI

## Development

To add a new model to the admin panel:

1. Create a ModelView class in `views.py`:
```python
class MyModelAdmin(ModelView, model=MyModel):
    name = "My Model"
    name_plural = "My Models"
    icon = "fa-solid fa-icon"

    column_list = [MyModel.id, MyModel.name, ...]
    column_searchable_list = [MyModel.name]
    column_sortable_list = [MyModel.created_at]
```

2. Add the view to `create_sqladmin_plugin()` in `config.py`:
```python
self.admin.add_view(MyModelAdmin)
```

3. Export it from `views.py` `__all__` list

## Dependencies

- `sqladmin>=0.22.0` - Core admin framework
- `sqladmin-litestar-plugin>=0.2.0` - Litestar integration
- `itsdangerous>=2.2.0` - Session encryption
- `wtforms>=3.1.2` - Form handling
- `python-multipart>=0.0.20` - File uploads

## Troubleshooting

### "No module named 'itsdangerous'"
Install the dependency: `uv add itsdangerous`

### Cannot access admin panel
1. Ensure you have a superuser account
2. Check database connection
3. Verify `/sqladmin` route is mounted

### Database session errors
Ensure the SQLAlchemy plugin is initialized before the SQLAdmin plugin in `main.py`.

## References

- [SQLAdmin Documentation](https://aminalaee.dev/sqladmin/)
- [Litestar Plugins](https://docs.litestar.dev/latest/usage/plugins/index.html)
- [Advanced-Alchemy](https://docs.advanced-alchemy.dev/)

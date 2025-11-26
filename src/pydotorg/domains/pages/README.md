# Pages Domain

The Pages domain handles CMS-style content pages for the application. It provides functionality for creating, managing, and rendering static and dynamic content pages with support for multiple content formats.

## Architecture

Following the standard applet structure:

```
pages/
├── __init__.py        # Public exports
├── controllers.py     # Litestar HTTP controllers
├── urls.py           # URL path constants
├── dependencies.py   # DI providers
├── services.py       # Business logic layer
├── models.py         # SQLAlchemy models
├── schemas.py        # Pydantic schemas
├── repositories.py   # Data access layer
└── README.md         # This file
```

## Models

### Page
Main content page model with:
- **Content Management**: Title, path, content with markdown/RST/HTML support
- **SEO**: Keywords, description metadata
- **Publishing**: is_published flag for draft/live control
- **Templates**: Customizable template_name per page
- **Audit Trail**: ContentManageableMixin provides creator/modifier tracking

### Image
Attached images for pages:
- Belongs to a Page (cascade delete)
- File path storage
- Creator tracking

### DocumentFile
Attached documents for pages:
- Belongs to a Page (cascade delete)
- File path storage
- Creator tracking

## Content Types

Pages support three content rendering formats:

1. **MARKDOWN** (default): GitHub-flavored markdown via `cmarkgfm`
2. **RESTRUCTUREDTEXT**: Python documentation format via `docutils`
3. **HTML**: Raw HTML passthrough

Content is rendered dynamically via `PageService.render_content()`.

## API Endpoints

### Pages
- `GET /api/v1/pages` - List all pages (paginated)
- `GET /api/v1/pages/published` - List published pages only
- `GET /api/v1/pages/{page_id}` - Get page by ID
- `POST /api/v1/pages/path` - Get page by path
- `POST /api/v1/pages` - Create new page
- `PUT /api/v1/pages/{page_id}` - Update page
- `PATCH /api/v1/pages/{page_id}/publish` - Publish page
- `PATCH /api/v1/pages/{page_id}/unpublish` - Unpublish page
- `DELETE /api/v1/pages/{page_id}` - Delete page

### Images
- `GET /api/v1/pages/{page_id}/images` - List page images
- `GET /api/v1/images/{image_id}` - Get image by ID
- `POST /api/v1/pages/{page_id}/images` - Upload image to page
- `DELETE /api/v1/images/{image_id}` - Delete image

### Documents
- `GET /api/v1/pages/{page_id}/documents` - List page documents
- `GET /api/v1/documents/{document_id}` - Get document by ID
- `POST /api/v1/pages/{page_id}/documents` - Upload document to page
- `DELETE /api/v1/documents/{document_id}` - Delete document

### Page Rendering (HTML)
- `GET /{path}` - Render published page as HTML using Jinja2 template

## Services

### PageService
- Page CRUD with path validation
- Content rendering (markdown/RST/HTML)
- Publishing controls
- Path-based lookups

### ImageService
- Image attachment management
- Page-specific image listing

### DocumentFileService
- Document attachment management
- Page-specific document listing

## Repositories

All repositories extend `SQLAlchemyAsyncRepository` with custom query methods:

### PageRepository
- `get_by_path()` - Lookup by URL path
- `list_published()` - Filter published pages
- `exists_by_path()` - Path uniqueness validation

### ImageRepository
- `list_by_page_id()` - Get all images for a page

### DocumentFileRepository
- `list_by_page_id()` - Get all documents for a page

## Dependency Injection

Register via `get_page_dependencies()`:

```python
from pydotorg.domains.pages import get_page_dependencies

app = Litestar(
    route_handlers=[...],
    dependencies=get_page_dependencies(),
)
```

## Usage Example

```python
from pydotorg.domains.pages import PageService, PageCreate, ContentType

# Create a page
page_data = PageCreate(
    title="About Python",
    path="/about/",
    content="# Python is awesome\n\nHere's why...",
    content_type=ContentType.MARKDOWN,
    is_published=True,
)
page = await page_service.create_page(page_data)

# Render content
html = await page_service.render_content(page)

# Publish/unpublish
await page_service.publish(page.id)
await page_service.unpublish(page.id)
```

## Templates

Pages are rendered using Jinja2 templates. The template is specified by `page.template_name` (default: `pages/default.html`).

Template context includes:
- `page` - The Page model instance
- `content` - Rendered HTML content
- `title` - Page title
- `description` - Page description
- `keywords` - SEO keywords

## Notes

- All paths should include leading and trailing slashes (e.g., `/about/`)
- Images and documents are cascade-deleted when parent page is deleted
- Only published pages are served via the HTML rendering endpoint
- Content rendering happens on-demand, not cached in database

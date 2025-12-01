# Litestar Integration Example

This document shows how to integrate the template system with your Litestar application.

## Complete Example Route Handler

```python
from pathlib import Path
from litestar import Litestar, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

# Configure Jinja2 templates
template_config = TemplateConfig(
    directory=Path("src/pydotorg/templates"),
    engine=JinjaTemplateEngine,
)

# Configure static files
static_files_router = create_static_files_router(
    path="/static",
    directories=["static"],
    name="static",
)


# Example route handlers
@get("/", name="home")
async def index() -> Template:
    """Homepage with Python branding."""
    return Template(
        template_name="pages/index.html.jinja2",
        context={
            "messages": [],
        },
    )


@get("/about", name="about")
async def about() -> Template:
    """About page example."""
    return Template(
        template_name="pages/about.html.jinja2",
        context={
            "breadcrumbs": [
                {"title": "About"}
            ],
        },
    )


@get("/news", name="news")
async def news() -> Template:
    """News listing page."""
    news_items = [
        {
            "title": "Python 3.12.0 Released",
            "excerpt": "The latest version includes performance improvements...",
            "date": "2024-10-02",
            "url": "/news/python-3120",
            "author": "Python Release Team",
        },
    ]

    return Template(
        template_name="pages/news.html.jinja2",
        context={
            "breadcrumbs": [
                {"title": "News"}
            ],
            "news_items": news_items,
        },
    )


# Create app instance
app = Litestar(
    route_handlers=[
        index,
        about,
        news,
        static_files_router,
    ],
    template_config=template_config,
)
```

## Example Page Template

Create `src/pydotorg/templates/pages/about.html.jinja2`:

```jinja2
{% extends "base.html.jinja2" %}
{% import "macros/buttons.html.jinja2" as buttons %}

{% block title %}About Python - Python.org{% endblock %}

{% block breadcrumbs %}
  {% include 'partials/breadcrumbs.html.jinja2' %}
{% endblock %}

{% block content %}
<section class="bg-base-100 py-16">
    <div class="section-container">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-5xl font-bold text-python-blue mb-6">
                About Python
            </h1>

            <div class="prose prose-lg max-w-none">
                <p class="lead">
                    Python is a programming language that lets you work quickly
                    and integrate systems more effectively.
                </p>

                <h2>Why Python?</h2>
                <ul>
                    <li>Easy to learn and read</li>
                    <li>Extensive standard library</li>
                    <li>Large, active community</li>
                    <li>Cross-platform compatibility</li>
                </ul>

                <div class="mt-8">
                    {{ buttons.primary_button('Get Started', '/about/gettingstarted', 'button', 'lg') }}
                    {{ buttons.outline_button('Download', '/downloads', 'button', 'lg') }}
                </div>
            </div>
        </div>
    </div>
</section>
{% endblock %}
```

## Passing Messages to Templates

```python
from litestar import post
from litestar.response import Redirect

@post("/contact")
async def contact_form(data: ContactFormData) -> Redirect:
    # Process form...

    # Redirect with flash message
    return Redirect(
        path="/",
        headers={
            "Set-Cookie": "flash_message=Your message was sent!; Path=/; Max-Age=5"
        }
    )


# In your route handler, read the flash message:
@get("/")
async def index(request: Request) -> Template:
    messages = []

    if flash := request.cookies.get("flash_message"):
        messages.append({
            "type": "success",
            "content": flash,
        })

    return Template(
        template_name="pages/index.html.jinja2",
        context={"messages": messages},
    )
```

## Working with Sidebar

```python
@get("/docs")
async def documentation() -> Template:
    sidebar_links = [
        {"title": "Tutorial", "url": "/docs/tutorial", "active": False},
        {"title": "Library Reference", "url": "/docs/library", "active": False},
        {"title": "Language Reference", "url": "/docs/reference", "active": True},
        {"title": "Python HOWTOs", "url": "/docs/howto", "active": False},
    ]

    return Template(
        template_name="pages/docs.html.jinja2",
        context={
            "sidebar_links": sidebar_links,
        },
    )
```

Then in your template:

```jinja2
{% extends "base.html.jinja2" %}

{% block content %}
<div class="section-container py-12">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div class="lg:col-span-1">
            {% include 'partials/sidebar.html.jinja2' %}
        </div>
        <div class="lg:col-span-3">
            <!-- Main content here -->
        </div>
    </div>
</div>
{% endblock %}
```

## Custom Jinja2 Filters

Add custom filters to your template config:

```python
from datetime import datetime

def format_date(value: datetime, format: str = "%B %d, %Y") -> str:
    """Format datetime object."""
    return value.strftime(format)

def truncate_words(text: str, count: int = 50) -> str:
    """Truncate text to word count."""
    words = text.split()
    if len(words) <= count:
        return text
    return " ".join(words[:count]) + "..."


template_config = TemplateConfig(
    directory=Path("src/pydotorg/templates"),
    engine=JinjaTemplateEngine,
    engine_instance=JinjaTemplateEngine(
        directory=Path("src/pydotorg/templates"),
        engine_instance_options={
            "filters": {
                "format_date": format_date,
                "truncate_words": truncate_words,
            }
        }
    )
)
```

Use in templates:

```jinja2
{{ article.published_at|format_date }}
{{ article.content|truncate_words(30) }}
```

## Error Pages

Create custom error pages:

```python
from litestar import Response
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

async def not_found_handler(request: Request, exc: HTTPException) -> Template:
    return Template(
        template_name="errors/404.html.jinja2",
        context={
            "status_code": HTTP_404_NOT_FOUND,
            "message": "Page not found",
        },
    )

async def server_error_handler(request: Request, exc: Exception) -> Template:
    return Template(
        template_name="errors/500.html.jinja2",
        context={
            "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
        },
    )


app = Litestar(
    route_handlers=[...],
    template_config=template_config,
    exception_handlers={
        HTTP_404_NOT_FOUND: not_found_handler,
        HTTP_500_INTERNAL_SERVER_ERROR: server_error_handler,
    },
)
```

Create `src/pydotorg/templates/errors/404.html.jinja2`:

```jinja2
{% extends "base.html.jinja2" %}
{% import "macros/buttons.html.jinja2" as buttons %}

{% block title %}Page Not Found - Python.org{% endblock %}

{% block content %}
<section class="bg-base-100 py-16 min-h-[60vh] flex items-center">
    <div class="section-container">
        <div class="max-w-2xl mx-auto text-center">
            <h1 class="text-9xl font-bold text-python-blue">404</h1>
            <h2 class="text-4xl font-bold mt-4 mb-6">Page Not Found</h2>
            <p class="text-xl text-base-content/70 mb-8">
                The page you're looking for doesn't exist or has been moved.
            </p>
            <div class="flex gap-4 justify-center">
                {{ buttons.primary_button('Go Home', '/') }}
                {{ buttons.outline_button('Search', '/search') }}
            </div>
        </div>
    </div>
</section>
{% endblock %}
```

## Environment-Specific Context

Add global context variables:

```python
import os
from litestar.connection import ASGIConnection
from litestar.datastructures import State

async def global_context(connection: ASGIConnection, state: State) -> dict:
    """Add global context variables to all templates."""
    return {
        "request": connection,
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "site_name": "Python.org",
        "current_year": datetime.now().year,
    }


template_config = TemplateConfig(
    directory=Path("src/pydotorg/templates"),
    engine=JinjaTemplateEngine,
    context_processors=[global_context],
)
```

Use in templates:

```jinja2
<footer>
    <p>&copy; {{ current_year }} {{ site_name }}</p>
    {% if debug %}
        <div class="alert alert-warning">Debug mode is enabled</div>
    {% endif %}
</footer>
```

# Frontend Template System - Setup Guide

This document describes the TailwindCSS + DaisyUI + Jinja2 template system for the Python.org rebuild.

## Overview

The frontend uses:
- **Jinja2** for server-side templating (replacing Django templates)
- **TailwindCSS** for utility-first CSS styling
- **DaisyUI** for pre-built component classes
- **Python branding** with official colors (#3776AB blue, #FFD43B yellow)

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies (if not already done)
make install

# Install Node.js dependencies for TailwindCSS
make install-frontend
```

### 2. Build CSS

```bash
# Production build (minified)
make css

# Development mode (watch for changes)
make css-watch
```

### 3. Run Development Server

Open two terminal windows:

**Terminal 1 - Litestar Server:**
```bash
make serve
```

**Terminal 2 - CSS Watcher:**
```bash
make css-watch
```

## File Structure

```
litestar-pydotorg/
├── package.json                    # Node.js dependencies
├── tailwind.config.js              # TailwindCSS configuration
├── postcss.config.js               # PostCSS configuration
├── static/
│   ├── css/
│   │   ├── input.css              # CSS entry point (source)
│   │   └── tailwind.css           # Generated CSS (gitignored)
│   └── js/
│       └── main.js                # JavaScript utilities
└── src/pydotorg/templates/
    ├── base.html.jinja2           # Base layout
    ├── partials/                  # Reusable template parts
    │   ├── navbar.html.jinja2
    │   ├── footer.html.jinja2
    │   ├── sidebar.html.jinja2
    │   ├── breadcrumbs.html.jinja2
    │   └── alert.html.jinja2
    ├── macros/                    # Component helpers
    │   ├── buttons.html.jinja2
    │   ├── cards.html.jinja2
    │   ├── forms.html.jinja2
    │   └── alerts.html.jinja2
    └── pages/                     # Page templates
        └── index.html.jinja2      # Homepage
```

## Template Usage

### Extending Base Template

```jinja2
{% extends "base.html.jinja2" %}

{% block title %}My Page - Python.org{% endblock %}

{% block content %}
  <div class="section-container py-12">
    <h1 class="text-4xl font-bold text-python-blue">Page Title</h1>
  </div>
{% endblock %}
```

### Using Macros

```jinja2
{% import "macros/buttons.html.jinja2" as buttons %}
{% import "macros/cards.html.jinja2" as cards %}

{{ buttons.primary_button('Click Me', '/some-url') }}

{{ cards.news_card(
    title='Article Title',
    excerpt='Short description...',
    date='2024-11-25',
    url='/news/article'
) }}
```

### Using Breadcrumbs

```jinja2
{% block breadcrumbs %}
  {% set breadcrumbs = [
    {'title': 'About', 'url': '/about'},
    {'title': 'Current Page'}
  ] %}
  {% include 'partials/breadcrumbs.html.jinja2' %}
{% endblock %}
```

## Custom CSS Classes

### Python Brand Colors

```html
<!-- Blue -->
<div class="bg-python-blue">Primary Blue</div>
<div class="text-python-blue-light">Light Blue</div>

<!-- Yellow -->
<div class="bg-python-yellow">Primary Yellow</div>
<div class="text-python-yellow-dark">Dark Yellow</div>
```

### Utility Classes

```html
<!-- Container with padding -->
<div class="section-container">Content here</div>

<!-- Python-styled link -->
<a href="#" class="python-link">Link</a>

<!-- Gradient button -->
<button class="python-btn-primary">Primary Button</button>

<!-- Card component -->
<div class="python-card">Card content</div>
```

## DaisyUI Themes

Two themes are configured:
- **python** (light mode) - Default
- **pythondark** (dark mode)

Theme toggle is built into the navbar. Theme preference is stored in localStorage.

### Using DaisyUI Components

```html
<!-- Button -->
<button class="btn btn-primary">Button</button>

<!-- Card -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Card Title</h2>
    <p>Card content</p>
  </div>
</div>

<!-- Alert -->
<div class="alert alert-success">Success message</div>

<!-- Badge -->
<span class="badge badge-primary">New</span>
```

See [DaisyUI Documentation](https://daisyui.com/components/) for all components.

## Litestar Integration

### Configure Template Engine

In your Litestar app configuration:

```python
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from pathlib import Path

template_config = TemplateConfig(
    directory=Path("src/pydotorg/templates"),
    engine=JinjaTemplateEngine,
)

app = Litestar(
    route_handlers=[...],
    template_config=template_config,
)
```

### Serve Static Files

```python
from litestar.static_files import create_static_files_router

static_files_router = create_static_files_router(
    path="/static",
    directories=["static"],
)

app = Litestar(
    route_handlers=[..., static_files_router],
    template_config=template_config,
)
```

### Render Templates

```python
from litestar import get
from litestar.response import Template

@get("/")
async def index() -> Template:
    return Template(
        template_name="pages/index.html.jinja2",
        context={
            "title": "Welcome to Python.org",
        }
    )
```

## Development Workflow

### Typical Development Session

```bash
# Terminal 1: Start Litestar server with hot-reload
make serve

# Terminal 2: Start TailwindCSS watcher
make css-watch
```

Now you can:
1. Edit templates in `src/pydotorg/templates/`
2. Edit CSS in `static/css/input.css`
3. Changes auto-reload in browser

### Before Committing

```bash
# Build production CSS
make css

# Run all checks
make ci
```

## Accessibility

All templates follow WCAG 2.1 AA standards:
- Semantic HTML5 elements
- ARIA labels on interactive elements
- Color contrast ratios meet AA standards
- Keyboard navigation support
- Screen reader friendly

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile browsers (iOS Safari, Chrome Android)

## Performance

- CSS is minified in production builds
- Tailwind purges unused styles (only ~10KB final CSS)
- Dark mode uses CSS variables (no flash)
- Images should use lazy loading

## Troubleshooting

### CSS not updating

```bash
# Delete generated CSS and rebuild
rm static/css/tailwind.css
make css
```

### Node modules missing

```bash
make install-frontend
```

### Template not found

Ensure template path is relative to `src/pydotorg/templates/`:
```python
# Correct
Template(template_name="pages/index.html.jinja2")

# Incorrect
Template(template_name="src/pydotorg/templates/pages/index.html.jinja2")
```

## Additional Resources

- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [DaisyUI Components](https://daisyui.com/components/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Litestar Template Documentation](https://docs.litestar.dev/latest/usage/templating.html)

# Template System Quick Start

Get up and running with the new template system in 5 minutes.

## 1. Install Dependencies

```bash
make install-frontend
```

This installs TailwindCSS, DaisyUI, PostCSS, and Autoprefixer.

## 2. Build CSS

```bash
make css
```

This generates `static/css/tailwind.css` from `static/css/input.css`.

## 3. Test the Setup

Start the CSS watcher in one terminal:
```bash
make css-watch
```

The watcher will rebuild CSS whenever you modify:
- `static/css/input.css`
- Any `.jinja2` template file
- `tailwind.config.js`

## 4. View the Homepage

The homepage template is ready at:
`src/pydotorg/templates/pages/index.html.jinja2`

To see it rendered, you need to integrate it with your Litestar app (see step 5).

## 5. Integrate with Litestar

Add this to your Litestar app (e.g., `src/pydotorg/main.py`):

```python
from pathlib import Path
from litestar import Litestar, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

# Template configuration
template_config = TemplateConfig(
    directory=Path(__file__).parent / "templates",
    engine=JinjaTemplateEngine,
)

# Static files
static_router = create_static_files_router(
    path="/static",
    directories=["static"],
)

# Homepage route
@get("/")
async def homepage() -> Template:
    return Template(template_name="pages/index.html.jinja2")

# Create app
app = Litestar(
    route_handlers=[homepage, static_router],
    template_config=template_config,
)
```

## 6. Run the Server

```bash
make serve
```

Visit http://localhost:8000 to see your site!

## 7. Start Development

Keep two terminals open:

**Terminal 1** - CSS Watcher:
```bash
make css-watch
```

**Terminal 2** - Litestar Server:
```bash
make serve
```

Now you can:
- Edit templates in `src/pydotorg/templates/`
- Modify CSS in `static/css/input.css`
- Changes reload automatically!

## What You Get

### Ready-to-Use Components

**Buttons:**
```jinja2
{% import "macros/buttons.html.jinja2" as buttons %}
{{ buttons.primary_button('Click Me', '/url') }}
{{ buttons.download_button('Download Python', '/downloads', version='3.12.0') }}
```

**Cards:**
```jinja2
{% import "macros/cards.html.jinja2" as cards %}
{{ cards.news_card(
    title='Article Title',
    excerpt='Description...',
    date='2024-11-25',
    url='/news/article'
) }}
```

**Forms:**
```jinja2
{% import "macros/forms.html.jinja2" as forms %}
{{ forms.input_field('email', 'Email Address', type='email', required=true) }}
```

### Pre-Built Layouts

**Base Template:**
```jinja2
{% extends "base.html.jinja2" %}

{% block title %}My Page{% endblock %}

{% block content %}
  <div class="section-container py-12">
    <h1 class="text-4xl font-bold text-python-blue">Hello World</h1>
  </div>
{% endblock %}
```

**With Sidebar:**
```jinja2
{% block content %}
<div class="section-container py-12">
  <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
    <div class="lg:col-span-1">
      {% include 'partials/sidebar.html.jinja2' %}
    </div>
    <div class="lg:col-span-3">
      <!-- Main content -->
    </div>
  </div>
</div>
{% endblock %}
```

### Python Brand Colors

```html
<!-- Blue -->
<div class="bg-python-blue text-white">Python Blue</div>
<button class="btn btn-primary">Primary Button</button>

<!-- Yellow -->
<div class="bg-python-yellow text-gray-900">Python Yellow</div>
<button class="btn btn-secondary">Secondary Button</button>

<!-- Gradients -->
<div class="python-gradient text-white">Blue Gradient</div>
```

### Dark Mode

Dark mode toggle is built into the navbar. Theme persists in localStorage.

Access current theme in CSS:
```css
[data-theme="python"] .my-element { /* light mode */ }
[data-theme="pythondark"] .my-element { /* dark mode */ }
```

## File Locations

**Templates:**
- Base: `src/pydotorg/templates/base.html.jinja2`
- Partials: `src/pydotorg/templates/partials/`
- Macros: `src/pydotorg/templates/macros/`
- Pages: `src/pydotorg/templates/pages/`

**Static Files:**
- CSS Source: `static/css/input.css`
- CSS Output: `static/css/tailwind.css` (auto-generated)
- JavaScript: `static/js/main.js`

**Configuration:**
- TailwindCSS: `tailwind.config.js`
- PostCSS: `postcss.config.js`
- NPM: `package.json`

## Common Tasks

### Add a New Page

1. Create template: `src/pydotorg/templates/pages/mypage.html.jinja2`
```jinja2
{% extends "base.html.jinja2" %}

{% block title %}My Page{% endblock %}

{% block content %}
  <div class="section-container py-12">
    <h1 class="text-4xl font-bold text-python-blue">My Page</h1>
  </div>
{% endblock %}
```

2. Add route handler:
```python
@get("/mypage")
async def my_page() -> Template:
    return Template(template_name="pages/mypage.html.jinja2")
```

### Add Custom CSS

Edit `static/css/input.css`:
```css
@layer components {
  .my-custom-class {
    @apply bg-python-blue text-white p-4 rounded-lg;
  }
}
```

CSS rebuilds automatically if `make css-watch` is running.

### Use DaisyUI Components

DaisyUI is pre-configured. Use any component from https://daisyui.com/components/

```html
<button class="btn btn-primary">Button</button>
<div class="card bg-base-100 shadow-xl">...</div>
<div class="alert alert-success">Success!</div>
```

## Next Steps

- Read `FRONTEND_SETUP.md` for detailed documentation
- Check `INTEGRATION_EXAMPLE.md` for more Litestar examples
- Review `TEMPLATE_SYSTEM_SUMMARY.md` for complete file listing
- Explore existing templates in `src/pydotorg/templates/`

## Need Help?

**CSS not updating?**
```bash
rm static/css/tailwind.css
make css
```

**Node modules issues?**
```bash
rm -rf node_modules package-lock.json
make install-frontend
```

**Template not found?**
- Check path is relative to `src/pydotorg/templates/`
- Verify file extension is `.jinja2`
- Ensure template config is set in Litestar app

## Resources

- TailwindCSS Docs: https://tailwindcss.com/docs
- DaisyUI Components: https://daisyui.com/components/
- Jinja2 Docs: https://jinja.palletsprojects.com/
- Litestar Docs: https://docs.litestar.dev/

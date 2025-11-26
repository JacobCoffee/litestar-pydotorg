# Component Usage Examples

Quick reference guide for using Jinja2 components.

## Quick Start

### Basic Import Pattern
```jinja2
{% from "components/sections/hero.html.jinja2" import hero %}
{% from "components/widgets/download_button.html.jinja2" import download_button %}
```

### Using Components in Templates
```jinja2
{% block content %}
  {{ hero(title="Welcome", subtitle="Get started") }}
  {{ download_button(version="3.13", url="/downloads/") }}
{% endblock %}
```

---

## Section Components

### Hero Sections

**Standard Hero**
```jinja2
{% from "components/sections/hero.html.jinja2" import hero %}

{{ hero(
    title="Python",
    subtitle="Programming for Everyone",
    cta_text="Download Now",
    cta_url="/downloads/",
    style="gradient",  # or 'solid', 'image'
    size="lg"          # or 'sm', 'xl'
) }}
```

**Split Hero**
```jinja2
{% from "components/sections/hero.html.jinja2" import hero_split %}

{{ hero_split(
    title="Learn Python",
    subtitle="Start your journey today",
    cta_text="Get Started",
    cta_url="/tutorial/",
    image_url="/static/images/learn.jpg",
    reverse=False
) }}
```

### Features

**Feature Grid**
```jinja2
{% from "components/sections/features.html.jinja2" import feature_grid %}

{{ feature_grid(
    title="Why Python?",
    subtitle="Python is powerful and easy to learn",
    features=[
        {
            'title': 'Easy to Learn',
            'description': 'Simple syntax, readable code',
            'icon': '<svg>...</svg>',
            'url': '/features/easy/'
        },
        {
            'title': 'Powerful',
            'description': 'Build anything from web apps to AI',
            'icon': '<svg>...</svg>',
            'url': '/features/powerful/'
        }
    ],
    columns=3
) }}
```

### News Feed

**Grid Layout**
```jinja2
{% from "components/sections/news_feed.html.jinja2" import news_feed %}

{{ news_feed(
    articles=[
        {
            'title': 'Python 3.13 Released',
            'excerpt': 'New features and improvements...',
            'url': '/news/3-13-release/',
            'date': '2024-10-07',
            'author': 'PSF',
            'category': 'Release',
            'image_url': '/static/news/3-13.jpg'
        }
    ],
    title="Latest News",
    show_all_link="/news/",
    columns=3
) }}
```

**List Layout**
```jinja2
{% from "components/sections/news_feed.html.jinja2" import news_list %}

{{ news_list(
    articles=recent_news,
    title="Recent Updates",
    show_all_link="/news/"
) }}
```

### Events

**Events Grid**
```jinja2
{% from "components/sections/events_list.html.jinja2" import events_grid %}

{{ events_grid(
    events=[
        {
            'title': 'PyCon US 2025',
            'date': '2025-05-15',
            'time': '9:00 AM',
            'location': 'Pittsburgh, PA',
            'url': '/events/pycon-2025/',
            'type': 'Conference',
            'description': 'The largest Python conference',
            'is_featured': True
        }
    ],
    title="Upcoming Events",
    show_all_link="/events/",
    columns=3
) }}
```

**Timeline View**
```jinja2
{% from "components/sections/events_list.html.jinja2" import events_timeline %}

{{ events_timeline(
    events=upcoming_events,
    title="Event Schedule"
) }}
```

### Sponsors

**Multi-Tier Grid**
```jinja2
{% from "components/sections/sponsors_grid.html.jinja2" import sponsors_grid %}

{{ sponsors_grid(
    sponsors=[
        {
            'name': 'Platinum Sponsor',
            'logo_url': '/static/sponsors/platinum.png',
            'url': 'https://example.com',
            'tier': 'platinum'
        },
        {
            'name': 'Gold Sponsor',
            'logo_url': '/static/sponsors/gold.png',
            'url': 'https://example.com',
            'tier': 'gold'
        }
    ],
    title="Our Sponsors",
    subtitle="Thank you to our amazing sponsors",
    tier_names={
        'platinum': 'Platinum Partners',
        'gold': 'Gold Sponsors',
        'silver': 'Silver Sponsors'
    }
) }}
```

### Statistics

**Stats Bar**
```jinja2
{% from "components/sections/stats_bar.html.jinja2" import stats_bar %}

{{ stats_bar(
    stats=[
        {
            'label': 'Downloads',
            'value': '500M+',
            'description': 'Monthly downloads',
            'icon': '<svg>...</svg>',
            'trend': '+12%',
            'trend_direction': 'up'
        }
    ],
    title="Python by the Numbers",
    bg_style="gradient"  # or 'solid', 'light'
) }}
```

**Stats Grid**
```jinja2
{% from "components/sections/stats_bar.html.jinja2" import stats_grid %}

{{ stats_grid(
    stats=statistics,
    title="Community Stats",
    columns=4
) }}
```

### Call-to-Action

**CTA Banner**
```jinja2
{% from "components/sections/cta_banner.html.jinja2" import cta_banner %}

{{ cta_banner(
    title="Get Started with Python Today",
    description="Download Python and start coding in minutes",
    cta_text="Download Python",
    cta_url="/downloads/",
    secondary_cta_text="View Docs",
    secondary_cta_url="/docs/",
    style="gradient"
) }}
```

### Testimonials

**Grid Layout**
```jinja2
{% from "components/sections/testimonials.html.jinja2" import testimonials_grid %}

{{ testimonials_grid(
    testimonials=[
        {
            'quote': 'Python changed my career!',
            'name': 'Jane Developer',
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'avatar_url': '/static/avatars/jane.jpg',
            'rating': 5
        }
    ],
    title="What Developers Say",
    columns=3
) }}
```

**Carousel**
```jinja2
{% from "components/sections/testimonials.html.jinja2" import testimonials_carousel %}

{{ testimonials_carousel(
    testimonials=testimonials_list,
    title="Success Stories",
    auto_rotate=True
) }}
```

---

## Navigation Components

### Main Menu

```jinja2
{% from "components/nav/main_menu.html.jinja2" import main_menu %}

{{ main_menu(
    items=[
        {
            'label': 'About',
            'url': '/about/',
            'children': [
                {'label': 'Python', 'url': '/about/python/'},
                {'label': 'Community', 'url': '/about/community/'}
            ]
        },
        {'label': 'Downloads', 'url': '/downloads/'}
    ],
    current_path=request.url.path
) }}
```

### Mobile Menu

```jinja2
{% from "components/nav/mobile_menu.html.jinja2" import mobile_menu %}

{{ mobile_menu(
    items=menu_items,
    current_path=request.url.path
) }}
```

### Footer Links

```jinja2
{% from "components/nav/footer_links.html.jinja2" import footer_links %}

{{ footer_links(
    sections=[
        {
            'title': 'About',
            'links': [
                {'label': 'About Python', 'url': '/about/'},
                {'label': 'Community', 'url': '/community/'}
            ]
        },
        {
            'title': 'Downloads',
            'links': [
                {'label': 'Latest Release', 'url': '/downloads/'},
                {'label': 'All Releases', 'url': '/downloads/all/'}
            ]
        }
    ]
) }}
```

### Social Links

```jinja2
{% from "components/nav/social_links.html.jinja2" import social_links %}

{{ social_links(
    links=[
        {'name': 'Twitter', 'url': 'https://twitter.com/ThePSF'},
        {'name': 'GitHub', 'url': 'https://github.com/python'},
        {'name': 'Discord', 'url': 'https://discord.gg/python'}
    ],
    style='icons',  # or 'buttons', 'vertical'
    size='md'       # or 'sm', 'lg'
) }}
```

---

## Widget Components

### Download Buttons

**Simple Button**
```jinja2
{% from "components/widgets/download_button.html.jinja2" import download_button %}

{{ download_button(
    version="3.13.0",
    url="/downloads/python-3.13.0.exe",
    platform="Windows",
    size="lg",
    style="primary"
) }}
```

**Download Hero**
```jinja2
{% from "components/widgets/download_button.html.jinja2" import download_hero %}

{{ download_hero(
    latest_version="3.13.0",
    platforms=[
        {'name': 'Windows', 'url': '/dl/win/', 'icon': '<svg>...</svg>'},
        {'name': 'macOS', 'url': '/dl/mac/', 'icon': '<svg>...</svg>'},
        {'name': 'Linux', 'url': '/dl/linux/', 'icon': '<svg>...</svg>'}
    ],
    pre_release={'version': '3.14.0a1', 'url': '/dl/pre/'}
) }}
```

### Version Selector

```jinja2
{% from "components/widgets/version_selector.html.jinja2" import version_selector %}

{{ version_selector(
    versions=[
        {
            'version': '3.13',
            'slug': '3.13',
            'is_latest': True
        },
        {
            'version': '3.12',
            'slug': '3.12',
            'is_deprecated': False
        }
    ],
    current_version="3.13",
    base_url="/docs/python/"
) }}
```

### Search Box

**Inline Search**
```jinja2
{% from "components/widgets/search_box.html.jinja2" import search_box %}

{{ search_box(
    placeholder="Search Python.org...",
    action="/search",
    size="md"
) }}
```

**Modal Search**
```jinja2
{% from "components/widgets/search_box.html.jinja2" import search_modal %}

{{ search_modal(
    placeholder="Search...",
    action="/search"
) }}
```

### Newsletter Signup

**Inline Form**
```jinja2
{% from "components/widgets/newsletter_signup.html.jinja2" import newsletter_signup %}

{{ newsletter_signup(
    title="Stay Updated",
    description="Get Python news in your inbox",
    action="/newsletter/subscribe",
    button_text="Subscribe",
    style="inline"  # or 'card'
) }}
```

**Full Banner**
```jinja2
{% from "components/widgets/newsletter_signup.html.jinja2" import newsletter_banner %}

{{ newsletter_banner(
    title="Join Our Newsletter",
    description="Get the latest Python news and updates",
    action="/newsletter/subscribe"
) }}
```

### Language Selector

```jinja2
{% from "components/widgets/language_selector.html.jinja2" import language_selector %}

{{ language_selector(
    languages=[
        {'code': 'en', 'name': 'English'},
        {'code': 'es', 'name': 'Español'},
        {'code': 'fr', 'name': 'Français'}
    ],
    current_lang="en"
) }}
```

---

## Code Display Components

### Code Blocks

**Basic Code Block**
```jinja2
{% from "components/code/code_block.html.jinja2" import code_block %}

{{ code_block(
    code='print("Hello, World!")',
    language="python",
    filename="hello.py",
    show_line_numbers=True
) }}
```

**Inline Code**
```jinja2
{% from "components/code/code_block.html.jinja2" import inline_code %}

Use {{ inline_code("pip install") }} to install packages.
```

**Code Tabs**
```jinja2
{% from "components/code/code_block.html.jinja2" import code_tabs %}

{{ code_tabs(
    tabs=[
        {
            'label': 'Python',
            'language': 'python',
            'code': 'print("Hello")'
        },
        {
            'label': 'JavaScript',
            'language': 'javascript',
            'code': 'console.log("Hello")'
        }
    ],
    default_tab=0
) }}
```

**Terminal Output**
```jinja2
{% from "components/code/code_block.html.jinja2" import terminal_output %}

{{ terminal_output(
    commands=[
        {'type': 'input', 'text': 'python --version'},
        {'type': 'output', 'text': 'Python 3.13.0'}
    ],
    prompt='$'
) }}
```

### Interactive REPL

```jinja2
{% from "components/code/repl_demo.html.jinja2" import repl_demo %}

{{ repl_demo(
    examples=[
        {
            'input': 'print("Hello, World!")',
            'output': 'Hello, World!'
        },
        {
            'input': '2 + 2',
            'output': '4'
        }
    ],
    title="Try Python in Your Browser"
) }}
```

### Code Playground

```jinja2
{% from "components/code/repl_demo.html.jinja2" import code_playground %}

{{ code_playground(
    default_code='def greet(name):\n    print(f"Hello, {name}!")\n\ngreet("Python")',
    language="python",
    height="500px"
) }}
```

---

## Common Patterns

### Full Page Layout

```jinja2
{% extends "base.html.jinja2" %}

{% from "components/sections/hero.html.jinja2" import hero %}
{% from "components/sections/features.html.jinja2" import feature_grid %}
{% from "components/sections/cta_banner.html.jinja2" import cta_banner %}

{% block content %}
  {{ hero(...) }}
  {{ feature_grid(...) }}
  {{ cta_banner(...) }}
{% endblock %}
```

### With Caller Block

Some components support `caller()` for custom content:

```jinja2
{% from "components/sections/hero.html.jinja2" import hero %}

{% call hero(title="Welcome", subtitle="Get Started") %}
  <a href="/docs/" class="btn btn-outline btn-lg">Read Docs</a>
{% endcall %}
```

### Conditional Rendering

```jinja2
{% if latest_news %}
  {{ news_feed(articles=latest_news) }}
{% endif %}
```

### Loop with Components

```jinja2
{% for event_group in events_by_month %}
  {{ events_grid(
      events=event_group.events,
      title=event_group.month
  ) }}
{% endfor %}
```

---

## Tips

1. **Import at the top** - Keep all imports together for clarity
2. **Use variables** - Prepare complex data in Python, not templates
3. **Leverage defaults** - Many parameters are optional
4. **Compose components** - Mix and match to build complex layouts
5. **Check README.md** - Complete documentation with all parameters

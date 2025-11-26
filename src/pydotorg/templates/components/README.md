# Jinja2 Template Components

This directory contains reusable Jinja2 template components that replace Django Boxes.
All components are pure templates (no database storage) and are version-controlled in git.

## Directory Structure

```
components/
├── __init__.py                    # Empty file for IDE recognition
├── sections/                      # Large page sections
│   ├── hero.html.jinja2
│   ├── features.html.jinja2
│   ├── news_feed.html.jinja2
│   ├── events_list.html.jinja2
│   ├── sponsors_grid.html.jinja2
│   ├── stats_bar.html.jinja2
│   ├── cta_banner.html.jinja2
│   └── testimonials.html.jinja2
├── nav/                           # Navigation components
│   ├── main_menu.html.jinja2
│   ├── mobile_menu.html.jinja2
│   ├── footer_links.html.jinja2
│   └── social_links.html.jinja2
├── widgets/                       # Utility widgets
│   ├── download_button.html.jinja2
│   ├── version_selector.html.jinja2
│   ├── search_box.html.jinja2
│   ├── newsletter_signup.html.jinja2
│   └── language_selector.html.jinja2
└── code/                          # Code display components
    ├── code_block.html.jinja2
    └── repl_demo.html.jinja2
```

## Usage Pattern

### 1. Import Components

```jinja2
{# At the top of your template #}
{% from "components/sections/hero.html.jinja2" import hero %}
{% from "components/sections/features.html.jinja2" import feature_grid %}
{% from "components/widgets/download_button.html.jinja2" import download_button %}
```

### 2. Call Macros

```jinja2
{% block content %}
  {{ hero(
      title="Welcome to Python.org",
      subtitle="The official home of Python",
      cta_text="Download Python 3.13",
      cta_url="/downloads/"
  ) }}

  {{ feature_grid(
      features=[
          {
              'title': 'Easy to Learn',
              'description': 'Python has a simple syntax...',
              'icon': '<svg>...</svg>',
              'url': '/about/'
          }
      ],
      columns=3
  ) }}
{% endblock %}
```

## Component Categories

### Sections (Large Content Blocks)

**Hero Banners**
- `hero()` - Full-width hero with gradient background
- `hero_split()` - Split hero with image and text

**Feature Displays**
- `feature_grid()` - Grid of feature cards
- `feature_list()` - Vertical list of features

**News & Articles**
- `news_feed()` - Grid of news articles
- `news_list()` - Vertical list of news items

**Events**
- `events_grid()` - Grid of event cards
- `events_timeline()` - Timeline view of events

**Sponsors**
- `sponsors_grid()` - Multi-tier sponsor logos
- `sponsors_carousel()` - Carousel of sponsors
- `sponsor_become_cta()` - Sponsorship CTA banner

**Statistics**
- `stats_bar()` - Horizontal stats bar
- `stats_grid()` - Grid of stat cards
- `counter_stat()` - Individual animated counter

**CTAs**
- `cta_banner()` - Full-width CTA banner
- `cta_split()` - Split CTA with image
- `cta_card()` - Card-style CTA

**Testimonials**
- `testimonials_grid()` - Grid of testimonials
- `testimonials_carousel()` - Carousel of testimonials

### Navigation

**Menus**
- `main_menu()` - Desktop navigation menu
- `mega_menu()` - Multi-column mega menu
- `mobile_menu()` - Mobile drawer menu

**Footer**
- `footer_links()` - Multi-column footer links
- `footer_simple()` - Simple horizontal footer
- `footer_legal()` - Legal/copyright footer

**Social**
- `social_links()` - Social media icon links
- `social_share()` - Share buttons

### Widgets

**Downloads**
- `download_button()` - Single download button
- `download_card()` - Download card with details
- `download_hero()` - Hero section for downloads

**Versions**
- `version_selector()` - Dropdown version picker
- `version_tabs()` - Tabbed version display
- `version_badge()` - Version badge with status

**Search**
- `search_box()` - Inline search form
- `search_modal()` - Modal search dialog
- `search_autocomplete()` - Search with suggestions

**Newsletter**
- `newsletter_signup()` - Inline signup form
- `newsletter_banner()` - Full-width signup banner
- `newsletter_modal()` - Modal signup form

**Language**
- `language_selector()` - Language dropdown
- `language_flags()` - Flag-based language picker

### Code Display

**Code Blocks**
- `code_block()` - Syntax highlighted code
- `inline_code()` - Inline code snippet
- `code_tabs()` - Tabbed code examples
- `code_compare()` - Before/after comparison
- `terminal_output()` - Terminal command output

**Interactive**
- `repl_demo()` - Interactive Python REPL
- `code_playground()` - Split-pane code editor

## Complete Examples

### Homepage Example

```jinja2
{% extends "base.html.jinja2" %}

{% from "components/sections/hero.html.jinja2" import hero %}
{% from "components/sections/features.html.jinja2" import feature_grid %}
{% from "components/sections/news_feed.html.jinja2" import news_feed %}
{% from "components/sections/stats_bar.html.jinja2" import stats_bar %}
{% from "components/widgets/download_button.html.jinja2" import download_button %}
{% from "components/code/repl_demo.html.jinja2" import repl_demo %}

{% block content %}
  {# Hero Section #}
  {{ hero(
      title="Python",
      subtitle="Programming for Everyone",
      cta_text="Download Python 3.13",
      cta_url="/downloads/",
      style="gradient",
      size="xl"
  ) }}

  {# Statistics #}
  {{ stats_bar(
      stats=[
          {'label': 'Downloads', 'value': '500M+', 'icon': '<svg>...</svg>'},
          {'label': 'Packages', 'value': '500K+', 'icon': '<svg>...</svg>'},
          {'label': 'Contributors', 'value': '2000+', 'icon': '<svg>...</svg>'}
      ],
      bg_style="gradient"
  ) }}

  {# Features #}
  {{ feature_grid(
      title="Why Python?",
      subtitle="Python is powerful, versatile, and easy to learn",
      features=features_data,
      columns=3
  ) }}

  {# Interactive Demo #}
  {{ repl_demo(
      title="Try Python in Your Browser",
      examples=[
          {'input': 'print("Hello, World!")', 'output': 'Hello, World!'},
          {'input': '2 + 2', 'output': '4'}
      ]
  ) }}

  {# Latest News #}
  {{ news_feed(
      articles=latest_news,
      title="Latest News",
      show_all_link="/news/",
      columns=3
  ) }}
{% endblock %}
```

### Downloads Page Example

```jinja2
{% extends "base.html.jinja2" %}

{% from "components/widgets/download_button.html.jinja2" import download_hero, download_card %}
{% from "components/widgets/version_selector.html.jinja2" import version_selector %}

{% block content %}
  {# Download Hero #}
  {{ download_hero(
      latest_version="3.13.0",
      platforms=[
          {'name': 'Windows', 'url': '/downloads/windows/', 'icon': '<svg>...</svg>'},
          {'name': 'macOS', 'url': '/downloads/macos/', 'icon': '<svg>...</svg>'},
          {'name': 'Linux', 'url': '/downloads/linux/', 'icon': '<svg>...</svg>'}
      ],
      pre_release={'version': '3.14.0a1', 'url': '/downloads/pre-release/'}
  ) }}

  <section class="py-16">
    <div class="section-container">
      {# Version Selector #}
      <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold">All Releases</h2>
        {{ version_selector(versions=all_versions, current_version=current_version) }}
      </div>

      {# Download Cards #}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {% for download in downloads %}
        {{ download_card(
            platform=download.platform,
            version=download.version,
            size=download.size,
            url=download.url,
            icon=download.icon
        ) }}
        {% endfor %}
      </div>
    </div>
  </section>
{% endblock %}
```

### Community Page Example

```jinja2
{% extends "base.html.jinja2" %}

{% from "components/sections/hero.html.jinja2" import hero_split %}
{% from "components/sections/events_list.html.jinja2" import events_grid %}
{% from "components/sections/testimonials.html.jinja2" import testimonials_grid %}
{% from "components/sections/cta_banner.html.jinja2" import cta_banner %}
{% from "components/nav/social_links.html.jinja2" import social_links %}

{% block content %}
  {{ hero_split(
      title="Join the Python Community",
      subtitle="Connect with developers worldwide",
      cta_text="Get Involved",
      cta_url="/community/join/",
      image_url="/static/images/community.jpg"
  ) }}

  {{ events_grid(
      events=upcoming_events,
      title="Upcoming Events",
      show_all_link="/events/",
      columns=3
  ) }}

  {{ testimonials_grid(
      testimonials=community_testimonials,
      title="What Pythonistas Say",
      columns=3
  ) }}

  <section class="py-16 bg-base-100">
    <div class="section-container text-center">
      <h2 class="text-3xl font-bold text-python-blue mb-6">Connect With Us</h2>
      {{ social_links(
          links=[
              {'name': 'Twitter', 'url': 'https://twitter.com/ThePSF'},
              {'name': 'GitHub', 'url': 'https://github.com/python'},
              {'name': 'Discord', 'url': 'https://discord.gg/python'}
          ],
          style='buttons',
          size='lg'
      ) }}
    </div>
  </section>

  {{ cta_banner(
      title="Become a PSF Member",
      description="Support Python and join a global community",
      cta_text="Join Today",
      cta_url="/psf/membership/",
      style="gradient"
  ) }}
{% endblock %}
```

## Best Practices

1. **Import only what you need** - Don't import all components if you only use a few
2. **Pass data from views** - Component data should come from your route handlers
3. **Use descriptive variable names** - Make it clear what data each component expects
4. **Leverage default parameters** - Many macros have sensible defaults
5. **Compose components** - Build complex layouts by combining multiple components
6. **Keep business logic in Python** - Templates should focus on presentation

## Data Structure Examples

### Feature Object
```python
{
    'title': 'Easy to Learn',
    'description': 'Python has a simple, intuitive syntax',
    'icon': '<svg>...</svg>',  # Optional
    'url': '/features/easy/'   # Optional
}
```

### Article Object
```python
{
    'title': 'Python 3.13 Released',
    'excerpt': 'The latest version brings...',
    'url': '/news/python-3-13/',
    'date': '2024-10-07',
    'author': 'PSF',           # Optional
    'category': 'Release',     # Optional
    'image_url': '/img/...'    # Optional
}
```

### Event Object
```python
{
    'title': 'PyCon US 2025',
    'date': '2025-05-15',
    'time': '9:00 AM PST',     # Optional
    'location': 'Pittsburgh, PA',
    'url': '/events/pycon/',
    'type': 'Conference',       # Optional
    'description': '...',       # Optional
    'is_featured': True         # Optional
}
```

### Sponsor Object
```python
{
    'name': 'Company Name',
    'logo_url': '/static/sponsors/logo.png',
    'url': 'https://example.com',
    'tier': 'platinum'  # platinum, gold, silver, bronze
}
```

## Styling Notes

- All components use **TailwindCSS** + **DaisyUI** classes
- Python brand colors: `text-python-blue`, `bg-python-blue`
- Responsive by default (mobile-first approach)
- Dark mode compatible via DaisyUI themes
- Accessible with ARIA labels and semantic HTML

## Migrating from Django Boxes

**Before (Django Box):**
```django
{% load boxes %}
{% box "homepage_hero" %}
```

**After (Jinja2 Component):**
```jinja2
{% from "components/sections/hero.html.jinja2" import hero %}
{{ hero(title=hero_data.title, subtitle=hero_data.subtitle) }}
```

Key differences:
- No database lookups
- Data comes from route handlers
- Version controlled in git
- Type-safe with IDE autocomplete
- Easier to test and preview

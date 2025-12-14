"""Sphinx configuration for litestar-pydotorg documentation."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../src"))


# Filter duplicate object warnings
class DuplicateObjectFilter(logging.Filter):
    """Filter out duplicate object description warnings."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "duplicate object description" in msg:
            return False
        return True


# Apply the filter to the Sphinx logger
for handler in logging.getLogger("sphinx").handlers:
    handler.addFilter(DuplicateObjectFilter())
logging.getLogger("sphinx.domains.python").addFilter(DuplicateObjectFilter())

project = "litestar-pydotorg"
copyright = f"{datetime.now().year}, Jacob Coffee"
author = "Jacob Coffee"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_design",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "internal"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "shibuya"
html_static_path = ["_static"]
html_title = "litestar-pydotorg"

html_theme_options = {
    "accent_color": "violet",
    "github_url": "https://github.com/JacobCoffee/litestar-pydotorg",
    "nav_links": [
        {"title": "Litestar", "url": "https://litestar.dev/"},
        {"title": "Python.org", "url": "https://python.org/"},
    ],
}

html_css_files = [
    "custom.css",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

autodoc_class_signature = "separated"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autodoc_inherit_docstrings = True

# Disable autosummary generation - use pre-generated stubs instead
# This significantly speeds up builds (from 90s to ~15s)
autosummary_generate = False

# Mock heavy imports to speed up autodoc and avoid circular imports
autodoc_mock_imports = [
    "granian",
    "saq",
    "meilisearch",
    "meilisearch_python_sdk",
    "redis",
    "asyncpg",
    "httpx",
    "aiosmtplib",
    "posthog",
    "sentry_sdk",
    "pydotorg.main",
    "pydotorg.core.auth",
    "pydotorg.core.auth.guards",
    "pydotorg.core.auth.jwt",
    "pydotorg.core.auth.middleware",
    "pydotorg.core.auth.oauth",
    "pydotorg.core.auth.password",
    "pydotorg.core.auth.schemas",
    "pydotorg.core.auth.session",
    "pydotorg.domains",
    "pydotorg.domains.about",
    "pydotorg.domains.admin",
    "pydotorg.domains.banners",
    "pydotorg.domains.blogs",
    "pydotorg.domains.codesamples",
    "pydotorg.domains.community",
    "pydotorg.domains.docs",
    "pydotorg.domains.downloads",
    "pydotorg.domains.events",
    "pydotorg.domains.jobs",
    "pydotorg.domains.mailing",
    "pydotorg.domains.minutes",
    "pydotorg.domains.nominations",
    "pydotorg.domains.pages",
    "pydotorg.domains.search",
    "pydotorg.domains.sponsors",
    "pydotorg.domains.sqladmin",
    "pydotorg.domains.successstories",
    "pydotorg.domains.users",
    "pydotorg.domains.work_groups",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_preprocess_types = True
napoleon_attr_annotations = True

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

myst_heading_anchors = 3

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "litestar": ("https://docs.litestar.dev/2/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "advanced-alchemy": ("https://docs.advanced-alchemy.litestar.dev/latest/", None),
}

intersphinx_disabled_reftypes = ["*"]

# Suppress common warnings for cleaner builds
suppress_warnings = [
    "intersphinx",
    "autodoc",
    "autodoc.mocked_object",
    "autodoc.import_object",
    "ref.python",
    "ref.doc",
    "docutils",
    "sphinx_autodoc_typehints.forward_reference",
    "sphinx_autodoc_typehints.guarded_import",
    "ref.obj",
    "py.duplicate_object_description",
]

# Don't fail on missing references
nitpicky = False

# Allow multiple documentation of same objects
add_module_names = False

todo_include_todos = True

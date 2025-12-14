"""Sphinx configuration for litestar-pydotorg documentation."""

from __future__ import annotations

import os
import sys
import warnings
from datetime import datetime

from sqlalchemy.exc import SAWarning

# Filter SQLAlchemy warnings during autodoc
warnings.filterwarnings("ignore", category=SAWarning)

sys.path.insert(0, os.path.abspath("../src"))

project = "litestar-pydotorg"
copyright = f"{datetime.now().year}, Jacob Coffee"
author = "Jacob Coffee"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
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

# Autodoc settings - match Litestar style
autoclass_content = "class"
autodoc_class_signature = "separated"
autodoc_default_options = {
    "members": True,
    "special-members": "__init__",
    "show-inheritance": True,
}
autodoc_member_order = "bysource"
autodoc_typehints_format = "short"

# Only mock external libraries that aren't installed or cause issues
autodoc_mock_imports = [
    "granian",
    "meilisearch_python_sdk",
]

napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
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

nitpicky = False
add_module_names = False
todo_include_todos = True

# Suppress warnings for inherited docstrings from external libraries with RST issues
suppress_warnings = [
    "autodoc.import_object",
    "sphinx_autodoc_typehints.forward_reference",
    "sphinx_autodoc_typehints.guarded_import",
]


def autodoc_skip_member(app, what, name, obj, skip, options):
    """Skip inherited attributes from SQLAdmin ModelView that have malformed docstrings."""
    sqladmin_attrs = {
        "column_list",
        "column_searchable_list",
        "column_sortable_list",
        "column_default_sort",
        "column_details_list",
        "column_details_exclude_list",
        "column_export_list",
        "column_export_exclude_list",
        "column_formatters",
        "column_formatters_detail",
        "column_formatters_export",
        "column_type_formatters",
        "column_labels",
        "form_columns",
        "form_excluded_columns",
        "form_include_pk",
        "form_widget_args",
        "form_args",
        "form_overrides",
        "form_ajax_refs",
        "form_rules",
        "form_converter",
        "form_base_class",
        "form_create_rules",
        "form_edit_rules",
    }
    if name in sqladmin_attrs:
        return True
    return skip


def setup(app):
    """Setup Sphinx app hooks."""
    app.connect("autodoc-skip-member", autodoc_skip_member)

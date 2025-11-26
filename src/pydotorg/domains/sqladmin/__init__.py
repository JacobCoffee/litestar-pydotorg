"""SQLAdmin integration for Python.org admin panel."""

from __future__ import annotations

from pydotorg.domains.sqladmin.auth import AdminAuthBackend
from pydotorg.domains.sqladmin.config import create_sqladmin_plugin

__all__ = ["AdminAuthBackend", "create_sqladmin_plugin"]

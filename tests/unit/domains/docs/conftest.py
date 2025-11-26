"""Test fixtures for docs domain tests."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.testing import TestClient

from pydotorg.domains.docs import DocsRenderController

if TYPE_CHECKING:
    from litestar.testing import TestClient as TestClientType


def configure_template_engine(engine: JinjaTemplateEngine) -> None:
    """Configure the Jinja2 template engine with global context."""
    engine.engine.globals.update(
        {
            "now": datetime.now,
        }
    )


@pytest.fixture
def docs_test_client() -> TestClientType:
    """Test client with docs routes configured."""
    templates_dir = Path(__file__).parent.parent.parent.parent.parent / "src" / "pydotorg" / "templates"

    app = Litestar(
        route_handlers=[DocsRenderController],
        template_config=TemplateConfig(
            directory=templates_dir,
            engine=JinjaTemplateEngine,
            engine_callback=configure_template_engine,
        ),
        debug=True,
    )
    return TestClient(app=app)

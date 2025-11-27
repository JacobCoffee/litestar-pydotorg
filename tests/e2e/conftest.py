"""Playwright E2E testing configuration and fixtures.

E2E tests require a running server. They will be automatically skipped
if no server is available at the configured URL.
"""

from __future__ import annotations

import os
import socket
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from sqlalchemy.ext.asyncio import create_async_engine

from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.database.base import AuditBase
from pydotorg.domains.users.auth_controller import AuthController, AuthPageController
from pydotorg.main import health_check

if TYPE_CHECKING:
    from playwright.async_api import Playwright


def _is_server_running(host: str = "localhost", port: int = 8000, timeout: float = 1.0) -> bool:
    """Check if the test server is running."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False


@pytest.fixture(scope="session")
def e2e_server_url() -> str:
    """Get the E2E test server URL from environment or use default."""
    return os.environ.get("E2E_SERVER_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def e2e_server_available(e2e_server_url: str) -> bool:
    """Check if the E2E test server is available."""
    from urllib.parse import urlparse

    parsed = urlparse(e2e_server_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    return _is_server_running(host, port)


@pytest.fixture(scope="session")
async def playwright_instance(e2e_server_available: bool) -> AsyncIterator[Playwright]:
    """Create a Playwright instance for the test session."""
    if not e2e_server_available:
        pytest.skip("E2E tests require a running server")
    async with async_playwright() as p:
        yield p


@pytest.fixture(scope="session")
async def browser(playwright_instance: Playwright) -> AsyncIterator[Browser]:
    """Launch a browser instance for the test session."""
    browser = await playwright_instance.chromium.launch(headless=True)
    yield browser
    await browser.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncIterator[BrowserContext]:
    """Create a new browser context for each test."""
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="en-US",
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncIterator[Page]:
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
async def test_app(postgres_uri: str) -> AsyncIterator[Litestar]:
    """Create test application with database for E2E tests."""
    engine = create_async_engine(postgres_uri, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.drop_all)
        await conn.run_sync(AuditBase.metadata.create_all)

    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    app = Litestar(
        route_handlers=[health_check, AuthController, AuthPageController],
        plugins=[sqlalchemy_plugin],
        middleware=[JWTAuthMiddleware],
        debug=True,
    )

    yield app


@pytest.fixture
async def test_server_url(e2e_server_url: str, e2e_server_available: bool) -> str:
    """Return the test server URL, skipping if server is not available."""
    if not e2e_server_available:
        pytest.skip("E2E tests require a running server. Start with 'make serve' or set E2E_SERVER_URL.")
    return e2e_server_url


@pytest.fixture
async def registered_test_user(page: Page, test_server_url: str) -> dict[str, str]:
    """Create a test user by registering through the UI."""
    user_data = {
        "username": "e2e_testuser",
        "email": "e2e_test@example.com",
        "password": "E2ETestPass123!",
        "first_name": "E2E",
        "last_name": "TestUser",
    }

    await page.goto(f"{test_server_url}/api/auth/register")
    response = await page.request.post(
        f"{test_server_url}/api/auth/register",
        data={
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "password_confirm": user_data["password"],
        },
    )

    assert response.ok, f"Failed to create test user: {await response.text()}"

    return user_data

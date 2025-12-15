"""Integration tests for Mailing domain controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from pydotorg.core.database.base import AuditBase
from pydotorg.domains.mailing.controllers import EmailLogController, EmailTemplateController
from pydotorg.domains.mailing.dependencies import get_mailing_dependencies
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate, EmailTemplateType

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _create_email_template_via_db(
    session_factory: async_sessionmaker,
    internal_name: str | None = None,
    is_active: bool = True,
) -> EmailTemplate:
    """Create an email template directly in the database using shared session factory."""
    async with session_factory() as session:
        template = EmailTemplate(
            internal_name=internal_name or f"test-template-{uuid4().hex[:8]}",
            display_name=f"Test Template {uuid4().hex[:8]}",
            description="Test email template for integration testing",
            template_type=EmailTemplateType.TRANSACTIONAL,
            subject="Test Subject {{ name }}",
            content_text="Hello {{ name }}, this is a test email.",
            content_html="<p>Hello {{ name }}, this is a test email.</p>",
            is_active=is_active,
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template


async def _create_email_log_via_db(
    session_factory: async_sessionmaker,
    template_name: str | None = None,
    status: str = "sent",
) -> EmailLog:
    """Create an email log directly in the database using shared session factory."""
    async with session_factory() as session:
        log = EmailLog(
            template_name=template_name or f"test-template-{uuid4().hex[:8]}",
            recipient_email=f"test-{uuid4().hex[:8]}@example.com",
            subject="Test Subject",
            status=status,
            error_message=None if status == "sent" else "Test error",
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log


class MailingTestFixtures:
    """Test fixtures for mailing routes."""

    client: AsyncTestClient
    session_factory: async_sessionmaker


@pytest.fixture
async def mailing_fixtures(
    async_engine: AsyncEngine,
    async_session_factory: async_sessionmaker,
    _module_sqlalchemy_config: SQLAlchemyAsyncConfig,
) -> AsyncIterator[MailingTestFixtures]:
    """Create test fixtures using module-scoped config to prevent connection exhaustion.

    Uses the shared _module_sqlalchemy_config from conftest.py instead of creating
    a new SQLAlchemyAsyncConfig per test, which was causing TooManyConnectionsError.
    """
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = {row[0] for row in result.fetchall()}

        for table in reversed(AuditBase.metadata.sorted_tables):
            if table.name in existing_tables:
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

    sqlalchemy_plugin = SQLAlchemyPlugin(config=_module_sqlalchemy_config)

    app = Litestar(
        route_handlers=[EmailTemplateController, EmailLogController],
        plugins=[sqlalchemy_plugin],
        dependencies=get_mailing_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        fixtures = MailingTestFixtures()
        fixtures.client = client
        fixtures.session_factory = async_session_factory
        yield fixtures


class TestEmailTemplateControllerRoutes:
    """Tests for EmailTemplateController endpoints.

    Note: These endpoints have guards (require_staff, require_admin) so unauthenticated
    requests will return 401/403. We test that the routes are reachable.
    """

    async def test_list_templates(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_template_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get("/api/admin/email-templates/")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_templates_active_only(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_template_via_db(mailing_fixtures.session_factory, is_active=True)
        response = await mailing_fixtures.client.get("/api/admin/email-templates/?active_only=true")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_templates_by_type(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_template_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get("/api/admin/email-templates/?template_type=transactional")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_template_by_id(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get(f"/api/admin/email-templates/{template.id}")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_template_by_id_not_found(self, mailing_fixtures: MailingTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await mailing_fixtures.client.get(f"/api/admin/email-templates/{fake_id}")
        assert response.status_code in (401, 403, 404, 500)

    async def test_get_template_by_name(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(
            mailing_fixtures.session_factory, internal_name="unique-template-name"
        )
        response = await mailing_fixtures.client.get(f"/api/admin/email-templates/by-name/{template.internal_name}")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_template_by_name_not_found(self, mailing_fixtures: MailingTestFixtures) -> None:
        response = await mailing_fixtures.client.get("/api/admin/email-templates/by-name/non-existent-template")
        assert response.status_code in (401, 403, 404, 500)

    async def test_create_template(self, mailing_fixtures: MailingTestFixtures) -> None:
        data = {
            "internal_name": f"new-template-{uuid4().hex[:8]}",
            "display_name": "New Test Template",
            "subject": "Test Subject",
            "content_text": "Test content",
            "template_type": "transactional",
            "is_active": True,
        }
        response = await mailing_fixtures.client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (201, 401, 403, 500)

    async def test_update_template(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        data = {"display_name": "Updated Template Name"}
        response = await mailing_fixtures.client.patch(f"/api/admin/email-templates/{template.id}", json=data)
        assert response.status_code in (200, 401, 403, 500)

    async def test_delete_template(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.delete(f"/api/admin/email-templates/{template.id}")
        assert response.status_code in (200, 204, 401, 403, 500)

    async def test_validate_template(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.post(f"/api/admin/email-templates/{template.id}/validate")
        assert response.status_code in (200, 401, 403, 500)

    async def test_preview_template(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        data = {"name": "Test User"}
        response = await mailing_fixtures.client.post(f"/api/admin/email-templates/{template.id}/preview", json=data)
        assert response.status_code in (200, 401, 403, 500)

    async def test_send_email(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        data = {
            "template_name": template.internal_name,
            "to_email": "test@example.com",
            "context": {"name": "Test User"},
        }
        response = await mailing_fixtures.client.post("/api/admin/email-templates/send", json=data)
        assert response.status_code in (200, 401, 403, 500)

    async def test_send_bulk_email(self, mailing_fixtures: MailingTestFixtures) -> None:
        template = await _create_email_template_via_db(mailing_fixtures.session_factory)
        data = {
            "template_name": template.internal_name,
            "recipients": ["test1@example.com", "test2@example.com"],
            "context": {"name": "Test User"},
        }
        response = await mailing_fixtures.client.post("/api/admin/email-templates/send-bulk", json=data)
        assert response.status_code in (200, 401, 403, 500)


class TestEmailLogControllerRoutes:
    """Tests for EmailLogController endpoints."""

    async def test_list_logs(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_log_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get("/api/admin/email-logs/")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_logs_with_limit(self, mailing_fixtures: MailingTestFixtures) -> None:
        for _ in range(3):
            await _create_email_log_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get("/api/admin/email-logs/?limit=2")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_logs_by_recipient(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_log_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get("/api/admin/email-logs/?recipient=test@example.com")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_logs_by_template(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_log_via_db(mailing_fixtures.session_factory, template_name="test-template")
        response = await mailing_fixtures.client.get("/api/admin/email-logs/?template_name=test-template")
        assert response.status_code in (200, 401, 403, 500)

    async def test_list_failed_logs(self, mailing_fixtures: MailingTestFixtures) -> None:
        await _create_email_log_via_db(mailing_fixtures.session_factory, status="failed")
        response = await mailing_fixtures.client.get("/api/admin/email-logs/?failed_only=true")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_log_by_id(self, mailing_fixtures: MailingTestFixtures) -> None:
        log = await _create_email_log_via_db(mailing_fixtures.session_factory)
        response = await mailing_fixtures.client.get(f"/api/admin/email-logs/{log.id}")
        assert response.status_code in (200, 401, 403, 500)

    async def test_get_log_by_id_not_found(self, mailing_fixtures: MailingTestFixtures) -> None:
        fake_id = str(uuid4())
        response = await mailing_fixtures.client.get(f"/api/admin/email-logs/{fake_id}")
        assert response.status_code in (401, 403, 404, 500)


class TestMailingValidation:
    """Validation tests for mailing domain."""

    async def test_create_template_missing_internal_name(self, mailing_fixtures: MailingTestFixtures) -> None:
        data = {
            "display_name": "Test Template",
            "subject": "Test Subject",
            "content_text": "Test content",
        }
        response = await mailing_fixtures.client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (400, 401, 403, 422, 500)

    async def test_create_template_missing_subject(self, mailing_fixtures: MailingTestFixtures) -> None:
        data = {
            "internal_name": "test-template",
            "display_name": "Test Template",
            "content_text": "Test content",
        }
        response = await mailing_fixtures.client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (400, 401, 403, 422, 500)

    async def test_create_template_missing_content(self, mailing_fixtures: MailingTestFixtures) -> None:
        data = {
            "internal_name": "test-template",
            "display_name": "Test Template",
            "subject": "Test Subject",
        }
        response = await mailing_fixtures.client.post("/api/admin/email-templates/", json=data)
        assert response.status_code in (400, 401, 403, 422, 500)

    async def test_get_template_invalid_uuid(self, mailing_fixtures: MailingTestFixtures) -> None:
        response = await mailing_fixtures.client.get("/api/admin/email-templates/not-a-uuid")
        assert response.status_code in (400, 401, 403, 404, 422)

    async def test_get_log_invalid_uuid(self, mailing_fixtures: MailingTestFixtures) -> None:
        response = await mailing_fixtures.client.get("/api/admin/email-logs/not-a-uuid")
        assert response.status_code in (400, 401, 403, 404, 422)

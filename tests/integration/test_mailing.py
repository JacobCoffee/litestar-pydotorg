"""Integration tests for Mailing domain."""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import SQLAlchemyAsyncConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pydotorg.core.auth.middleware import JWTAuthMiddleware
from pydotorg.core.database.base import AuditBase
from pydotorg.domains.mailing.controllers import EmailLogController, EmailTemplateController
from pydotorg.domains.mailing.dependencies import get_mailing_dependencies
from pydotorg.domains.mailing.models import EmailLog, EmailTemplate, EmailTemplateType
from pydotorg.domains.mailing.services import EmailLogService, EmailTemplateService, MailingService
from pydotorg.domains.users.models import User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def _is_maildev_available() -> bool:
    """Check if MailDev is running on localhost:1025."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            return sock.connect_ex(("127.0.0.1", 1025)) == 0
    except Exception:
        return False


async def _create_db_session(postgres_uri: str) -> tuple[AsyncSession, any]:
    """Helper to create a database session."""
    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session_factory()
    return session, engine


async def _create_sample_template(session: AsyncSession) -> EmailTemplate:
    """Helper to create a sample template."""
    template = EmailTemplate(
        internal_name=f"test_template_{uuid4().hex[:8]}",
        display_name="Test Template",
        description="A test email template",
        template_type=EmailTemplateType.TRANSACTIONAL,
        subject="Hello {{ name }}!",
        content_text="Hello {{ name }}, this is a test email.",
        content_html="<h1>Hello {{ name }}!</h1><p>This is a test email.</p>",
        is_active=True,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


@pytest.mark.integration
class TestEmailTemplateService:
    """Integration tests for EmailTemplateService."""

    async def test_create_template(self, postgres_uri: str) -> None:
        """Test creating an email template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailTemplateService(session=session)
            template = await service.create(
                EmailTemplate(
                    internal_name=f"welcome_email_{uuid4().hex[:8]}",
                    display_name="Welcome Email",
                    template_type=EmailTemplateType.TRANSACTIONAL,
                    subject="Welcome to {{ site_name }}!",
                    content_text="Welcome {{ username }}!",
                )
            )

            assert template.id is not None
            assert "welcome_email" in template.internal_name
            assert template.display_name == "Welcome Email"
            assert template.is_active is True
        finally:
            await session.close()
            await engine.dispose()

    async def test_get_by_internal_name(self, postgres_uri: str) -> None:
        """Test retrieving template by internal name."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = EmailTemplateService(session=session)
            found = await service.get_by_internal_name(sample_template.internal_name)

            assert found is not None
            assert found.id == sample_template.id
            assert found.internal_name == sample_template.internal_name
        finally:
            await session.close()
            await engine.dispose()

    async def test_get_by_internal_name_not_found(self, postgres_uri: str) -> None:
        """Test retrieving non-existent template returns None."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailTemplateService(session=session)
            found = await service.get_by_internal_name("nonexistent_template")

            assert found is None
        finally:
            await session.close()
            await engine.dispose()

    async def test_get_active_by_name(self, postgres_uri: str) -> None:
        """Test retrieving active template by name."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = EmailTemplateService(session=session)
            found = await service.get_active_by_name(sample_template.internal_name)

            assert found is not None
            assert found.is_active is True
        finally:
            await session.close()
            await engine.dispose()

    async def test_get_active_by_name_inactive(self, postgres_uri: str) -> None:
        """Test that inactive templates are not returned."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailTemplateService(session=session)
            template = await service.create(
                EmailTemplate(
                    internal_name=f"inactive_template_{uuid4().hex[:8]}",
                    display_name="Inactive Template",
                    template_type=EmailTemplateType.NOTIFICATION,
                    subject="Test",
                    content_text="Test",
                    is_active=False,
                )
            )

            found = await service.get_active_by_name(template.internal_name)
            assert found is None
        finally:
            await session.close()
            await engine.dispose()

    async def test_list_by_type(self, postgres_uri: str) -> None:
        """Test listing templates by type."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailTemplateService(session=session)

            await service.create(
                EmailTemplate(
                    internal_name=f"newsletter_{uuid4().hex[:8]}",
                    display_name="Newsletter",
                    template_type=EmailTemplateType.NEWSLETTER,
                    subject="Newsletter",
                    content_text="Newsletter content",
                )
            )
            await service.create(
                EmailTemplate(
                    internal_name=f"notification_{uuid4().hex[:8]}",
                    display_name="Notification",
                    template_type=EmailTemplateType.NOTIFICATION,
                    subject="Notification",
                    content_text="Notification content",
                )
            )

            newsletters = await service.list_by_type(EmailTemplateType.NEWSLETTER)
            assert len(newsletters) >= 1
            assert all(t.template_type == EmailTemplateType.NEWSLETTER for t in newsletters)
        finally:
            await session.close()
            await engine.dispose()

    async def test_list_active(self, postgres_uri: str) -> None:
        """Test listing only active templates."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailTemplateService(session=session)

            await service.create(
                EmailTemplate(
                    internal_name=f"active_{uuid4().hex[:8]}",
                    display_name="Active",
                    template_type=EmailTemplateType.SYSTEM,
                    subject="Active",
                    content_text="Active content",
                    is_active=True,
                )
            )
            await service.create(
                EmailTemplate(
                    internal_name=f"inactive_{uuid4().hex[:8]}",
                    display_name="Inactive",
                    template_type=EmailTemplateType.SYSTEM,
                    subject="Inactive",
                    content_text="Inactive content",
                    is_active=False,
                )
            )

            active = await service.list_active()
            assert all(t.is_active for t in active)
        finally:
            await session.close()
            await engine.dispose()

    async def test_validate_template_valid(self, postgres_uri: str) -> None:
        """Test validating a valid template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = EmailTemplateService(session=session)
            errors = await service.validate_template(sample_template.id)

            assert errors == []
        finally:
            await session.close()
            await engine.dispose()

    async def test_validate_template_invalid(self, postgres_uri: str) -> None:
        """Test validating an invalid template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailTemplateService(session=session)
            template = await service.create(
                EmailTemplate(
                    internal_name=f"invalid_{uuid4().hex[:8]}",
                    display_name="Invalid Template",
                    template_type=EmailTemplateType.TRANSACTIONAL,
                    subject="Invalid {% if unclosed",
                    content_text="Valid content",
                )
            )

            errors = await service.validate_template(template.id)
            assert len(errors) > 0
            assert any("subject" in error.lower() for error in errors)
        finally:
            await session.close()
            await engine.dispose()

    async def test_preview_template(self, postgres_uri: str) -> None:
        """Test previewing a rendered template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = EmailTemplateService(session=session)
            preview = await service.preview_template(sample_template.id, {"name": "John"})

            assert "error" not in preview
            assert preview["subject"] == "Hello John!"
            assert "Hello John" in preview["content_text"]
            assert "<h1>Hello John!</h1>" in preview["content_html"]
        finally:
            await session.close()
            await engine.dispose()


@pytest.mark.integration
class TestEmailLogService:
    """Integration tests for EmailLogService."""

    async def test_create_log(self, postgres_uri: str) -> None:
        """Test creating an email log entry."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailLogService(session=session)
            log = await service.create(
                EmailLog(
                    template_name="welcome_email",
                    recipient_email="test@example.com",
                    subject="Welcome!",
                    status="sent",
                )
            )

            assert log.id is not None
            assert log.template_name == "welcome_email"
            assert log.status == "sent"
        finally:
            await session.close()
            await engine.dispose()

    async def test_list_by_recipient(self, postgres_uri: str) -> None:
        """Test listing logs by recipient."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailLogService(session=session)
            email = f"recipient_{uuid4().hex[:8]}@example.com"

            await service.create(
                EmailLog(
                    template_name="template1",
                    recipient_email=email,
                    subject="Test 1",
                    status="sent",
                )
            )
            await service.create(
                EmailLog(
                    template_name="template2",
                    recipient_email=email,
                    subject="Test 2",
                    status="sent",
                )
            )
            await service.create(
                EmailLog(
                    template_name="template3",
                    recipient_email="other@example.com",
                    subject="Test 3",
                    status="sent",
                )
            )

            logs = await service.list_by_recipient(email)
            assert len(logs) == 2
            assert all(log.recipient_email == email for log in logs)
        finally:
            await session.close()
            await engine.dispose()

    async def test_list_by_template(self, postgres_uri: str) -> None:
        """Test listing logs by template name."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailLogService(session=session)
            template_name = f"template_{uuid4().hex[:8]}"

            await service.create(
                EmailLog(
                    template_name=template_name,
                    recipient_email="user1@example.com",
                    subject="Test 1",
                    status="sent",
                )
            )
            await service.create(
                EmailLog(
                    template_name=template_name,
                    recipient_email="user2@example.com",
                    subject="Test 2",
                    status="sent",
                )
            )

            logs = await service.list_by_template(template_name)
            assert len(logs) == 2
            assert all(log.template_name == template_name for log in logs)
        finally:
            await session.close()
            await engine.dispose()

    async def test_list_failed(self, postgres_uri: str) -> None:
        """Test listing failed email logs."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = EmailLogService(session=session)

            await service.create(
                EmailLog(
                    template_name="test",
                    recipient_email="success@example.com",
                    subject="Success",
                    status="sent",
                )
            )
            await service.create(
                EmailLog(
                    template_name="test",
                    recipient_email="failed@example.com",
                    subject="Failed",
                    status="failed",
                    error_message="SMTP error",
                )
            )

            failed = await service.list_failed()
            assert len(failed) >= 1
            assert all(log.status == "failed" for log in failed)
        finally:
            await session.close()
            await engine.dispose()


@pytest.mark.integration
class TestMailingService:
    """Integration tests for MailingService."""

    async def test_send_email_template_not_found(self, postgres_uri: str) -> None:
        """Test sending email with non-existent template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = MailingService(session=session)
            log = await service.send_email(
                template_name="nonexistent_template",
                to_email="test@example.com",
            )

            assert log.status == "failed"
            assert "not found" in log.error_message.lower()
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_email_inactive_template(self, postgres_uri: str) -> None:
        """Test sending email with inactive template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            template_service = EmailTemplateService(session=session)
            await template_service.create(
                EmailTemplate(
                    internal_name=f"inactive_send_test_{uuid4().hex[:8]}",
                    display_name="Inactive",
                    template_type=EmailTemplateType.TRANSACTIONAL,
                    subject="Test",
                    content_text="Test",
                    is_active=False,
                )
            )

            service = MailingService(session=session)
            log = await service.send_email(
                template_name=f"inactive_send_test_{uuid4().hex[:8]}",
                to_email="test@example.com",
            )

            assert log.status == "failed"
            assert "not found" in log.error_message.lower() or "inactive" in log.error_message.lower()
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_email_success(self, postgres_uri: str) -> None:
        """Test successful email sending."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = MailingService(session=session)

            with patch.object(service, "_send_smtp"):
                log = await service.send_email(
                    template_name=sample_template.internal_name,
                    to_email="recipient@example.com",
                    context={"name": "Test User"},
                )

                assert log.status == "sent"
                assert log.subject == "Hello Test User!"
                assert log.recipient_email == "recipient@example.com"
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_email_smtp_failure(self, postgres_uri: str) -> None:
        """Test email sending with SMTP failure."""
        import smtplib

        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = MailingService(session=session)

            with patch.object(service, "_send_smtp", side_effect=smtplib.SMTPException("Connection refused")):
                log = await service.send_email(
                    template_name=sample_template.internal_name,
                    to_email="recipient@example.com",
                    context={"name": "Test User"},
                )

                assert log.status == "failed"
                assert "SMTP" in log.error_message
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_bulk_email(self, postgres_uri: str) -> None:
        """Test bulk email sending."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = MailingService(session=session)
            recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

            with patch.object(service, "_send_smtp") as mock_smtp:
                logs = await service.send_bulk_email(
                    template_name=sample_template.internal_name,
                    recipients=recipients,
                    context={"name": "User"},
                )

                assert len(logs) == 3
                assert all(log.status == "sent" for log in logs)
                assert mock_smtp.call_count == 3
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_bulk_email_with_per_recipient_context(self, postgres_uri: str) -> None:
        """Test bulk email with per-recipient context."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = MailingService(session=session)
            recipients = ["alice@example.com", "bob@example.com"]
            per_recipient = {
                "alice@example.com": {"name": "Alice"},
                "bob@example.com": {"name": "Bob"},
            }

            with patch.object(service, "_send_smtp"):
                logs = await service.send_bulk_email(
                    template_name=sample_template.internal_name,
                    recipients=recipients,
                    per_recipient_context=per_recipient,
                )

                assert len(logs) == 2
                alice_log = next(log for log in logs if log.recipient_email == "alice@example.com")
                bob_log = next(log for log in logs if log.recipient_email == "bob@example.com")
                assert "Alice" in alice_log.subject
                assert "Bob" in bob_log.subject
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_custom_email(self, postgres_uri: str) -> None:
        """Test sending custom email without template."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = MailingService(session=session)

            with patch.object(service, "_send_smtp"):
                log = await service.send_custom_email(
                    to_email="test@example.com",
                    subject="Custom Subject",
                    text_content="Custom text content",
                    html_content="<p>Custom HTML content</p>",
                )

                assert log.status == "sent"
                assert log.template_name == "custom"
                assert log.subject == "Custom Subject"
        finally:
            await session.close()
            await engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(not _is_maildev_available(), reason="MailDev not available")
class TestMailingServiceWithMailDev:
    """Integration tests for MailingService with actual MailDev connection.

    These tests require MailDev to be running:
        docker compose up -d maildev
    """

    async def test_send_email_to_maildev(self, postgres_uri: str) -> None:
        """Test sending actual email to MailDev."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            service = MailingService(session=session)
            service.smtp_host = "127.0.0.1"
            service.smtp_port = 1025
            service.use_tls = False
            service.smtp_user = ""
            service.smtp_password = ""

            log = await service.send_email(
                template_name=sample_template.internal_name,
                to_email="maildev-test@example.com",
                context={"name": "MailDev Test"},
            )

            assert log.status == "sent"
            assert log.recipient_email == "maildev-test@example.com"
        finally:
            await session.close()
            await engine.dispose()

    async def test_send_custom_email_to_maildev(self, postgres_uri: str) -> None:
        """Test sending custom email to MailDev."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            service = MailingService(session=session)
            service.smtp_host = "127.0.0.1"
            service.smtp_port = 1025
            service.use_tls = False
            service.smtp_user = ""
            service.smtp_password = ""

            log = await service.send_custom_email(
                to_email="custom-test@example.com",
                subject="Test from Integration Tests",
                text_content="This is a test email from the integration tests.",
                html_content="<h1>Test Email</h1><p>This is from integration tests.</p>",
            )

            assert log.status == "sent"
        finally:
            await session.close()
            await engine.dispose()


@pytest.mark.integration
class TestEmailTemplateModel:
    """Integration tests for EmailTemplate model rendering."""

    async def test_render_subject(self, postgres_uri: str) -> None:
        """Test rendering template subject."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            subject = sample_template.render_subject({"name": "World"})
            assert subject == "Hello World!"
        finally:
            await session.close()
            await engine.dispose()

    async def test_render_content_text(self, postgres_uri: str) -> None:
        """Test rendering plain text content."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            content = sample_template.render_content_text({"name": "World"})
            assert "Hello World" in content
        finally:
            await session.close()
            await engine.dispose()

    async def test_render_content_html(self, postgres_uri: str) -> None:
        """Test rendering HTML content."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            content = sample_template.render_content_html({"name": "World"})
            assert "<h1>Hello World!</h1>" in content
        finally:
            await session.close()
            await engine.dispose()

    async def test_render_content_html_none(self) -> None:
        """Test rendering template without HTML content."""
        template = EmailTemplate(
            internal_name="text_only",
            display_name="Text Only",
            template_type=EmailTemplateType.TRANSACTIONAL,
            subject="Test",
            content_text="Text only",
            content_html=None,
        )
        result = template.render_content_html()
        assert result is None

    async def test_validate_templates_valid(self, postgres_uri: str) -> None:
        """Test validation of valid templates."""
        session, engine = await _create_db_session(postgres_uri)
        try:
            sample_template = await _create_sample_template(session)
            errors = sample_template.validate_templates()
            assert errors == []
        finally:
            await session.close()
            await engine.dispose()

    async def test_validate_templates_syntax_error(self) -> None:
        """Test validation catches syntax errors."""
        template = EmailTemplate(
            internal_name="invalid",
            display_name="Invalid",
            template_type=EmailTemplateType.TRANSACTIONAL,
            subject="{% if unclosed",
            content_text="Valid",
        )
        errors = template.validate_templates()
        assert len(errors) > 0


class MailingTestFixtures:
    """Container for mailing test fixtures."""

    client: AsyncTestClient
    postgres_uri: str
    staff_user: User
    regular_user: User
    admin_user: User


@pytest.fixture
async def mailing_fixtures(postgres_uri: str) -> AsyncIterator[MailingTestFixtures]:
    """Async test client with mailing controllers and test users.

    Creates the database schema, test users, and client in the correct order
    to ensure all tests have access to the same database state.
    """
    from sqlalchemy import text

    engine = create_async_engine(postgres_uri, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(AuditBase.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        staff = User(
            username=f"staff_{uuid4().hex[:8]}",
            email=f"staff_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Staff",
            last_name="User",
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        regular = User(
            username=f"regular_{uuid4().hex[:8]}",
            email=f"regular_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Regular",
            last_name="User",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        admin = User(
            username=f"admin_{uuid4().hex[:8]}",
            email=f"admin_{uuid4().hex[:8]}@example.com",
            password_hash="hashed_password",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        session.add_all([staff, regular, admin])
        await session.commit()
        for user in [staff, regular, admin]:
            await session.refresh(user)

        staff_data = User(id=staff.id, email=staff.email, username=staff.username, is_staff=True, is_superuser=False)
        regular_data = User(
            id=regular.id, email=regular.email, username=regular.username, is_staff=False, is_superuser=False
        )
        admin_data = User(id=admin.id, email=admin.email, username=admin.username, is_staff=True, is_superuser=True)

    await engine.dispose()

    sqlalchemy_config = SQLAlchemyAsyncConfig(
        connection_string=postgres_uri,
        metadata=AuditBase.metadata,
        create_all=False,
        before_send_handler="autocommit",
    )
    sqlalchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)

    test_app = Litestar(
        route_handlers=[EmailTemplateController, EmailLogController],
        plugins=[sqlalchemy_plugin],
        middleware=[JWTAuthMiddleware],
        dependencies=get_mailing_dependencies(),
        debug=True,
    )

    async with AsyncTestClient(
        app=test_app,
        base_url="http://testserver.local",
    ) as test_client:
        fixtures = MailingTestFixtures()
        fixtures.client = test_client
        fixtures.postgres_uri = postgres_uri
        fixtures.staff_user = staff_data
        fixtures.regular_user = regular_data
        fixtures.admin_user = admin_data
        yield fixtures


@pytest.mark.integration
class TestEmailTemplateControllerRoutes:
    """Route-level integration tests for EmailTemplateController."""

    async def test_list_templates_requires_auth(self, mailing_fixtures: MailingTestFixtures) -> None:
        """Test that list templates endpoint requires authentication."""
        response = await mailing_fixtures.client.get("/api/admin/email-templates/")
        assert response.status_code == 401

    async def test_list_templates_requires_staff(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test that list templates requires staff permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.regular_user.id)
        response = await mailing_fixtures.client.get(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_list_templates_success(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test listing templates with staff user."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.staff_user.id)
        response = await mailing_fixtures.client.get(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_template_requires_admin(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test that creating templates requires admin (superuser) permissions."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.staff_user.id)
        response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": "test_create",
                "display_name": "Test Create",
                "subject": "Test Subject",
                "content_text": "Test content",
            },
        )
        assert response.status_code == 403

    async def test_create_template_success(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test creating a template as admin."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)
        internal_name = f"test_create_{uuid4().hex[:8]}"
        response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Test Create Template",
                "subject": "Test Subject {{ name }}",
                "content_text": "Hello {{ name }}!",
                "template_type": "transactional",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["internal_name"] == internal_name
        assert data["display_name"] == "Test Create Template"
        assert "id" in data

    async def test_get_template_by_id(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test getting a template by ID."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_get_{uuid4().hex[:8]}"
        create_response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Test Get Template",
                "subject": "Test",
                "content_text": "Test",
            },
        )
        template_id = create_response.json()["id"]

        response = await mailing_fixtures.client.get(
            f"/api/admin/email-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == template_id

    async def test_get_template_not_found(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test getting a non-existent template returns 404."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.staff_user.id)
        fake_id = str(uuid4())
        response = await mailing_fixtures.client.get(
            f"/api/admin/email-templates/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_get_template_by_name(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test getting a template by internal name."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_name_{uuid4().hex[:8]}"
        await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Test Name Template",
                "subject": "Test",
                "content_text": "Test",
            },
        )

        response = await mailing_fixtures.client.get(
            f"/api/admin/email-templates/by-name/{internal_name}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["internal_name"] == internal_name

    async def test_update_template(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test updating a template."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_update_{uuid4().hex[:8]}"
        create_response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Original Name",
                "subject": "Original Subject",
                "content_text": "Original content",
            },
        )
        template_id = create_response.json()["id"]

        response = await mailing_fixtures.client.patch(
            f"/api/admin/email-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "display_name": "Updated Name",
                "subject": "Updated Subject",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["subject"] == "Updated Subject"

    async def test_delete_template(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test deleting a template."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_delete_{uuid4().hex[:8]}"
        create_response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "To Delete",
                "subject": "Delete Me",
                "content_text": "This will be deleted",
            },
        )
        template_id = create_response.json()["id"]

        response = await mailing_fixtures.client.delete(
            f"/api/admin/email-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        get_response = await mailing_fixtures.client.get(
            f"/api/admin/email-templates/{template_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    async def test_validate_template(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test validating a template's syntax."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_validate_{uuid4().hex[:8]}"
        create_response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Valid Template",
                "subject": "Hello {{ name }}",
                "content_text": "Welcome {{ name }}!",
            },
        )
        template_id = create_response.json()["id"]

        response = await mailing_fixtures.client.post(
            f"/api/admin/email-templates/{template_id}/validate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["errors"] == []

    async def test_preview_template(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test previewing a rendered template."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_preview_{uuid4().hex[:8]}"
        create_response = await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Preview Template",
                "subject": "Hello {{ name }}!",
                "content_text": "Welcome {{ name }} to {{ site }}!",
                "content_html": "<h1>Hello {{ name }}!</h1>",
            },
        )
        template_id = create_response.json()["id"]

        response = await mailing_fixtures.client.post(
            f"/api/admin/email-templates/{template_id}/preview",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "John", "site": "Python.org"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Hello John!"
        assert "John" in data["content_text"]
        assert "Python.org" in data["content_text"]
        assert "<h1>Hello John!</h1>" in data["content_html"]

    async def test_send_email_endpoint(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test sending email via the API endpoint."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_send_{uuid4().hex[:8]}"
        await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Send Test",
                "subject": "Test Email",
                "content_text": "Test content",
            },
        )

        with patch.object(MailingService, "_send_smtp", return_value=None):
            response = await mailing_fixtures.client.post(
                "/api/admin/email-templates/send",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "template_name": internal_name,
                    "to_email": "recipient@example.com",
                    "context": {},
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "log_id" in data

    async def test_send_bulk_email_endpoint(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test bulk email sending via the API endpoint."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_bulk_{uuid4().hex[:8]}"
        await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Bulk Test",
                "subject": "Bulk Email",
                "content_text": "Bulk content",
            },
        )

        with patch.object(MailingService, "_send_smtp", return_value=None):
            response = await mailing_fixtures.client.post(
                "/api/admin/email-templates/send-bulk",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "template_name": internal_name,
                    "recipients": ["user1@example.com", "user2@example.com"],
                    "context": {},
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["sent"] == 2
        assert len(data["log_ids"]) == 2


@pytest.mark.integration
class TestEmailLogControllerRoutes:
    """Route-level integration tests for EmailLogController."""

    async def test_list_logs_requires_auth(self, mailing_fixtures: MailingTestFixtures) -> None:
        """Test that list logs endpoint requires authentication."""
        response = await mailing_fixtures.client.get("/api/admin/email-logs/")
        assert response.status_code == 401

    async def test_list_logs_success(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test listing email logs as staff user."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.staff_user.id)
        response = await mailing_fixtures.client.get(
            "/api/admin/email-logs/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_logs_filter_by_recipient(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test filtering logs by recipient."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_log_filter_{uuid4().hex[:8]}"
        await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Log Filter Test",
                "subject": "Test",
                "content_text": "Test",
            },
        )

        test_email = f"filter_test_{uuid4().hex[:8]}@example.com"
        with patch.object(MailingService, "_send_smtp", return_value=None):
            await mailing_fixtures.client.post(
                "/api/admin/email-templates/send",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "template_name": internal_name,
                    "to_email": test_email,
                    "context": {},
                },
            )

        response = await mailing_fixtures.client.get(
            f"/api/admin/email-logs/?recipient={test_email}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) >= 1
        assert all(log["recipient_email"] == test_email for log in logs)

    async def test_get_log_by_id(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test getting a specific log by ID."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.admin_user.id)

        internal_name = f"test_log_get_{uuid4().hex[:8]}"
        await mailing_fixtures.client.post(
            "/api/admin/email-templates/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "internal_name": internal_name,
                "display_name": "Log Get Test",
                "subject": "Test",
                "content_text": "Test",
            },
        )

        with patch.object(MailingService, "_send_smtp", return_value=None):
            send_response = await mailing_fixtures.client.post(
                "/api/admin/email-templates/send",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "template_name": internal_name,
                    "to_email": "logtest@example.com",
                    "context": {},
                },
            )
        log_id = send_response.json()["log_id"]

        response = await mailing_fixtures.client.get(
            f"/api/admin/email-logs/{log_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == log_id

    async def test_get_log_not_found(
        self,
        mailing_fixtures: MailingTestFixtures,
    ) -> None:
        """Test getting a non-existent log returns 404."""
        from pydotorg.core.auth.jwt import jwt_service

        token = jwt_service.create_access_token(mailing_fixtures.staff_user.id)
        fake_id = str(uuid4())
        response = await mailing_fixtures.client.get(
            f"/api/admin/email-logs/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

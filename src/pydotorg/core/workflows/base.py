"""Base workflow step classes with common functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar_workflows import BaseHumanStep, BaseMachineStep

if TYPE_CHECKING:
    from litestar_workflows import WorkflowContext


class EmailNotificationStep(BaseMachineStep):
    """Base step that sends email notifications on execution.

    Subclasses should define:
        - name: Step identifier
        - template_name: Email template internal name
        - get_recipient(context): Method to get recipient email
        - get_email_context(context): Method to build template context

    Example:
        class NotifyApproval(EmailNotificationStep):
            name = "notify_approval"
            template_name = "sponsorship_approved"

            def get_recipient(self, context: WorkflowContext) -> str:
                return context.get("sponsor_email")

            def get_email_context(self, context: WorkflowContext) -> dict:
                return {"sponsor_name": context.get("sponsor_name")}
    """

    template_name: str = ""

    def get_recipient(self, context: WorkflowContext) -> str:
        """Get the email recipient address.

        Args:
            context: Workflow context with instance data.

        Returns:
            Email address to send notification to.
        """
        raise NotImplementedError("Subclasses must implement get_recipient")

    def get_email_context(self, context: WorkflowContext) -> dict[str, Any]:
        """Build the email template context.

        Args:
            context: Workflow context with instance data.

        Returns:
            Dictionary of template variables.
        """
        return {}

    async def execute(self, context: WorkflowContext) -> None:
        """Send email notification using the mailing service.

        Args:
            context: Workflow context with instance data.
        """
        # Import here to avoid circular imports
        from pydotorg.domains.mailing.services import MailingService

        if not self.template_name:
            return

        recipient = self.get_recipient(context)
        email_context = self.get_email_context(context)

        # Queue email via SAQ task
        # Note: In production, this would use the injected mailing service
        # For now, we store the notification intent in context
        context.set(
            f"_email_notification_{self.name}",
            {
                "template": self.template_name,
                "recipient": recipient,
                "context": email_context,
            },
        )


class StatusTransitionStep(BaseMachineStep):
    """Base step that updates a model's status field.

    Subclasses should define:
        - name: Step identifier
        - target_status: The status value to set
        - model_id_key: Context key containing the model ID
        - update_status(context, model_id): Method to perform the update

    Example:
        class ApproveSponsorship(StatusTransitionStep):
            name = "approve"
            target_status = "approved"
            model_id_key = "sponsorship_id"

            async def update_status(self, context, model_id):
                # Use injected service to update
                service = context.get("sponsorship_service")
                await service.approve(model_id)
    """

    target_status: str = ""
    model_id_key: str = "model_id"

    async def update_status(self, context: WorkflowContext, model_id: str) -> None:
        """Perform the status update on the model.

        Args:
            context: Workflow context with instance data.
            model_id: ID of the model to update.
        """
        raise NotImplementedError("Subclasses must implement update_status")

    async def execute(self, context: WorkflowContext) -> None:
        """Update the model status.

        Args:
            context: Workflow context with instance data.
        """
        model_id = context.get(self.model_id_key)
        if model_id:
            await self.update_status(context, model_id)
            context.set("current_status", self.target_status)


class ApprovalStep(BaseHumanStep):
    """Base human step for approval decisions.

    Provides a standard approval form with approved/rejected and comments.

    Subclasses should define:
        - name: Step identifier
        - title: Display title for the approval form
        - description: Instructions for the approver
    """

    form_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "approved": {
                "type": "boolean",
                "title": "Approve",
                "description": "Approve or reject this request",
            },
            "comments": {
                "type": "string",
                "title": "Comments",
                "description": "Optional comments or feedback",
            },
        },
        "required": ["approved"],
    }


class DocumentUploadStep(BaseHumanStep):
    """Base human step for document uploads.

    Used for steps that require file attachments (contracts, signatures, etc.).

    Subclasses should define:
        - name: Step identifier
        - title: Display title
        - document_field: Name of the document field in the form
    """

    document_field: str = "document"

    @property
    def form_schema(self) -> dict[str, Any]:
        """Generate form schema with document upload field."""
        return {
            "type": "object",
            "properties": {
                self.document_field: {
                    "type": "string",
                    "title": "Document",
                    "description": "Upload or provide document URL",
                    "format": "uri",
                },
                "notes": {
                    "type": "string",
                    "title": "Notes",
                    "description": "Optional notes about this document",
                },
            },
            "required": [self.document_field],
        }

"""Workflow automation module for pydotorg.

This module provides workflow automation using litestar-workflows for:
- Sponsor contract workflows (DRAFT → AWAITING_SIGNATURE → EXECUTED)
- Sponsorship approval workflows (APPLIED → APPROVED/REJECTED → FINALIZED)
- Job posting workflows (DRAFT → SUBMITTED → APPROVED → PUBLISHED)
- Event submission workflows (community submissions with moderation)

Usage:
    from pydotorg.core.workflows import get_workflow_plugin, workflow_registry

    # In main.py
    app = Litestar(plugins=[get_workflow_plugin()])

    # In services
    async def start_contract_workflow(contract_id: UUID) -> WorkflowInstance:
        engine = workflow_registry.get_engine()
        return await engine.start_workflow(
            "sponsor_contract",
            initial_data={"contract_id": str(contract_id)},
        )
"""

from __future__ import annotations

from pydotorg.core.workflows.config import get_workflow_plugin, workflow_plugin_config
from pydotorg.core.workflows.registry import workflow_registry

__all__ = [
    "get_workflow_plugin",
    "workflow_plugin_config",
    "workflow_registry",
]

"""Workflow plugin configuration for Litestar integration."""

from __future__ import annotations

from litestar_workflows import (
    LocalExecutionEngine,
    WorkflowPlugin,
    WorkflowPluginConfig,
)

from pydotorg.core.workflows.registry import workflow_registry


def get_workflow_plugin() -> WorkflowPlugin:
    """Create and configure the workflow plugin.

    Returns:
        Configured WorkflowPlugin instance for Litestar integration.

    The plugin provides:
        - Workflow registry for definition management
        - Local execution engine for workflow processing
        - REST API at /api/workflows for workflow management
        - Staff-only access to workflow API endpoints
    """
    # Import guard here to avoid circular import
    from pydotorg.core.auth.guards import require_staff

    engine = LocalExecutionEngine(registry=workflow_registry)

    config = WorkflowPluginConfig(
        registry=workflow_registry,
        engine=engine,
        enable_api=True,
        api_path_prefix="/api/workflows",
        api_guards=[require_staff],
        api_tags=["Workflows"],
        include_api_in_schema=False,  # Hide from public OpenAPI, show in admin docs
    )

    return WorkflowPlugin(config=config)


# Lazy-loaded config for reference
workflow_plugin_config: WorkflowPluginConfig | None = None

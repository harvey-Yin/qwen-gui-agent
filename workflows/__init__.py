"""
Workflows module for GUI-Agent.
Provides workflow orchestration for multi-step task automation.
"""
from workflows.base_workflow import BaseWorkflow, WorkflowStep
from workflows.open_kdocs_excel import OpenKDocsExcelWorkflow

# Workflow registry
WORKFLOW_REGISTRY = {
    "open_kdocs_latest_excel": OpenKDocsExcelWorkflow,
}


def get_workflow(name: str) -> BaseWorkflow:
    """Get a workflow instance by name."""
    if name not in WORKFLOW_REGISTRY:
        raise ValueError(f"Unknown workflow: {name}. Available: {list(WORKFLOW_REGISTRY.keys())}")
    return WORKFLOW_REGISTRY[name]()


def list_workflows() -> list:
    """List all available workflow names and descriptions."""
    return [
        {"name": name, "description": cls.description}
        for name, cls in WORKFLOW_REGISTRY.items()
    ]

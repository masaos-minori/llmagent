#!/usr/bin/env python3
"""mcp/cicd/models.py
Config loading and Pydantic request models for cicd-mcp.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger

_models_logger = Logger(__name__, "/opt/llm/logs/cicd-mcp.log")

_cfg: dict[str, Any] | None = None


def _get_cfg() -> dict[str, Any]:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("cicd_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


class TriggerWorkflowRequest(BaseModel):
    """Request body for the trigger_workflow tool."""

    repo: str = Field(..., description="Repository slug (owner/repo)")
    workflow: str = Field(
        ...,
        description="Workflow file name (e.g. ci.yml) or workflow ID",
    )
    ref: str = Field(
        default="main",
        description="Branch name, tag, or SHA to run the workflow on",
    )
    inputs: dict[str, str] = Field(
        default_factory=dict,
        description="Input parameters for the workflow (key-value pairs)",
    )


class GetWorkflowRunsRequest(BaseModel):
    """Request body for the get_workflow_runs tool."""

    repo: str = Field(..., description="Repository slug (owner/repo)")
    workflow: str = Field(
        ...,
        description="Workflow file name (e.g. ci.yml) or workflow ID",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of runs to return",
    )


class GetWorkflowStatusRequest(BaseModel):
    """Request body for the get_workflow_status tool."""

    repo: str = Field(..., description="Repository slug (owner/repo)")
    run_id: int = Field(..., gt=0, description="Workflow run ID")


class GetWorkflowLogsRequest(BaseModel):
    """Request body for the get_workflow_logs tool."""

    repo: str = Field(..., description="Repository slug (owner/repo)")
    run_id: int = Field(..., gt=0, description="Workflow run ID")

#!/usr/bin/env python3
"""mcp/cicd/models.py
Config loading, Pydantic models, and domain exceptions for cicd-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


def _get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(f"Config key {key!r} must be str, got {type(v).__name__}")
    return v


@dataclasses.dataclass
class CicdConfig:
    """Typed configuration for the CICD MCP server."""

    auth_token: str = ""
    repo_allowlist: list[str] = dataclasses.field(default_factory=list)
    workflow_allowlist: list[str] = dataclasses.field(default_factory=list)
    max_log_size_kb: int = 256
    github_token: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CicdConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            auth_token=_get_str(d, "auth_token"),
            repo_allowlist=list(d.get("repo_allowlist", [])),
            workflow_allowlist=list(d.get("workflow_allowlist", [])),
            max_log_size_kb=int(d.get("max_log_size_kb", 256)),
            github_token=_get_str(d, "github_token"),
        )

    @classmethod
    def load(cls) -> CicdConfig:
        """Load from cicd_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("cicd_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class CicdAuthorizationError(RuntimeError):
    """Raised when authentication/authorization fails."""


class CicdNotFoundError(ValueError):
    """Raised when a CICD resource is not found."""


class CicdValidationError(ValueError):
    """Raised on invalid input."""


class CicdUpstreamError(RuntimeError):
    """Raised on upstream service failures (e.g. GitHub API 5xx)."""


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────


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
    dry_run: bool = Field(
        default=False,
        description="Preview only; workflow dispatch is not triggered",
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

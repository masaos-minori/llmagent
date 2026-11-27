#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_models.py

Config loading, Pydantic models, and domain exceptions for cicd-mcp.

The request models are the single source of the published tool schemas: they
inherit the shared strict base so the contract a client discovers at `/v1/tools`
is the contract enforced at call time. `canonical_workflow_id()` is the only
identifier normalizer, used by both the request path and the allowlist comparison.

Dependency direction: models → (external: pydantic, shared) + mcp_servers.request_contract
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import Field
from shared.config_loader import ConfigLoader
from shared.config_utils import get_non_negative_number, get_str, get_typed
from shared.repo_identity import is_canonical_repo_key, normalize_repo_key

from mcp_servers.request_contract import StrictRequestModel

logger = logging.getLogger(__name__)

# Hard maximums approved by the Plan on 20261126 (UNK-03); they are constants, not
# configuration values, so the config file and the docs can state them.
MAX_LOG_SIZE_KB = 1024
MAX_ALLOWLIST_SIZE = 100


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
# Canonical identifier
# ──────────────────────────────────────────────────────────────────────────────


def canonical_workflow_id(value: str) -> str:
    """Return the canonical form of a workflow identifier.

    Accepts a workflow file name (e.g. `ci.yml`) or a positive numeric workflow ID;
    both forms are the two identifier forms the documentation names. A value that is
    already canonical is returned unchanged.

    Raises CicdValidationError for a blank value, a path separator, percent-encoding,
    a wildcard, or a numeric ID below 1, so the request path and the allowlist
    comparison cannot diverge.
    """
    if not isinstance(value, str):
        raise CicdValidationError(
            f"workflow identifier must be str, got {type(value).__name__}"
        )
    stripped = value.strip()
    if not stripped:
        raise CicdValidationError("workflow identifier is empty")
    if "/" in stripped or "\\" in stripped:
        raise CicdValidationError(
            f"workflow identifier contains a path separator and is rejected: {value!r}"
        )
    if "%" in stripped:
        raise CicdValidationError(
            f"workflow identifier contains percent-encoding and is rejected: {value!r}"
        )
    if "*" in stripped:
        raise CicdValidationError(
            f"workflow identifier contains a wildcard and is rejected: {value!r}"
        )
    canonical = stripped.lower()
    if canonical.isdigit():
        if int(canonical) < 1:
            raise CicdValidationError(
                f"numeric workflow ID must be positive: {value!r}"
            )
        return canonical
    return canonical


def canonical_repo_key(repo: str) -> str:
    """Return the canonical `owner/repo` key for a request slug.

    Raises CicdValidationError when the slug is not `owner/repo`.
    """
    parts = repo.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise CicdValidationError(
            f"Invalid repo slug {repo!r}: expected 'owner/repo' format"
        )
    return normalize_repo_key(parts[0], parts[1])


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


def _validate_allowlist(key: str, entries: list[str]) -> list[str]:
    """Reject an allowlist above the hard maximum or carrying a wildcard entry.

    Entries are returned unchanged: a non-canonical entry is reported, never rewritten,
    so the guard can still detect it instead of silently matching nothing.
    """
    if len(entries) > MAX_ALLOWLIST_SIZE:
        raise ValueError(
            f"Config key {key!r} has {len(entries)} entries; the hard maximum is {MAX_ALLOWLIST_SIZE}"
        )
    for entry in entries:
        if not isinstance(entry, str):
            raise ValueError(
                f"Config key {key!r} entries must be str, got {type(entry).__name__}"
            )
        if "*" in entry:
            raise ValueError(
                f"Config key {key!r} entry {entry!r} is a wildcard and is rejected"
            )
    return entries


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
        repo_allowlist = _validate_allowlist(
            "repo_allowlist",
            get_typed(d, "repo_allowlist", list, "a list", default=[]),
        )
        workflow_allowlist = _validate_allowlist(
            "workflow_allowlist",
            get_typed(d, "workflow_allowlist", list, "a list", default=[]),
        )
        for entry in repo_allowlist:
            if not is_canonical_repo_key(entry):
                raise ValueError(
                    f"Config key 'repo_allowlist' entry {entry!r} is not in canonical 'owner/repo' form"
                )
        for entry in workflow_allowlist:
            canonical_workflow_id(entry)

        max_log_size_kb = get_non_negative_number(
            d, "max_log_size_kb", int, "an integer", default=256
        )
        if max_log_size_kb < 1:
            raise ValueError(
                f"Config key 'max_log_size_kb' must be at least 1, got {max_log_size_kb}"
            )
        if max_log_size_kb > MAX_LOG_SIZE_KB:
            raise ValueError(
                f"Config key 'max_log_size_kb' must be at most {MAX_LOG_SIZE_KB}, got {max_log_size_kb}"
            )

        return cls(
            auth_token=get_str(d, "auth_token"),
            repo_allowlist=list(repo_allowlist),
            workflow_allowlist=list(workflow_allowlist),
            max_log_size_kb=max_log_size_kb,
            github_token=get_str(d, "github_token"),
        )

    @classmethod
    def load(cls) -> CicdConfig:
        """Load from cicd_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("cicd_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────

# Descriptions are the client-visible text published by build_input_schema(); they
# live on the model fields so the published schema and the enforced contract match.
_REPO_DESC = "Repository slug in 'owner/repo' format"
_WORKFLOW_DESC = "Workflow file name (e.g. ci.yml) or numeric workflow ID"
_RUN_ID_DESC = "Workflow run ID (from get_workflow_runs output)"


class TriggerWorkflowRequest(StrictRequestModel):
    """Request body for the trigger_workflow tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    workflow: str = Field(..., min_length=1, description=_WORKFLOW_DESC)
    ref: str = Field(
        default="main",
        min_length=1,
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


class GetWorkflowRunsRequest(StrictRequestModel):
    """Request body for the get_workflow_runs tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    workflow: str = Field(..., min_length=1, description=_WORKFLOW_DESC)
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of runs to return",
    )


class GetWorkflowStatusRequest(StrictRequestModel):
    """Request body for the get_workflow_status tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    run_id: int = Field(..., gt=0, description=_RUN_ID_DESC)


class GetWorkflowLogsRequest(StrictRequestModel):
    """Request body for the get_workflow_logs tool."""

    repo: str = Field(..., min_length=1, description=_REPO_DESC)
    run_id: int = Field(..., gt=0, description=_RUN_ID_DESC)

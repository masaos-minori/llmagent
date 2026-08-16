"""tests/mcp_servers/cicd/test_cicd_models.py

Characterization tests for scripts/mcp_servers/cicd/cicd_models.py.

These lock the current public behavior (JSON schema shape, field
constraints/defaults, config parsing, exception hierarchy) before a
refactor that extracts duplicated ``Field(...)`` description literals
into module-level constants. No behavior change is intended; these
tests exist to prove that before/after schema and validation behavior
are identical.
"""

from __future__ import annotations

import pytest
from mcp_servers.cicd.cicd_models import (
    CicdAuthorizationError,
    CicdConfig,
    CicdNotFoundError,
    CicdUpstreamError,
    CicdValidationError,
    GetWorkflowLogsRequest,
    GetWorkflowRunsRequest,
    GetWorkflowStatusRequest,
    TriggerWorkflowRequest,
)
from pydantic import ValidationError

# ──────────────────────────────────────────────────────────────────────────────
# JSON schema shape (public API surface seen by MCP clients)
# ──────────────────────────────────────────────────────────────────────────────


def test_trigger_workflow_request_schema() -> None:
    schema = TriggerWorkflowRequest.model_json_schema()
    assert schema["required"] == ["repo", "workflow"]
    assert schema["properties"]["repo"]["description"] == "Repository slug (owner/repo)"
    assert (
        schema["properties"]["workflow"]["description"]
        == "Workflow file name (e.g. ci.yml) or workflow ID"
    )
    assert schema["properties"]["ref"]["default"] == "main"
    assert (
        schema["properties"]["ref"]["description"]
        == "Branch name, tag, or SHA to run the workflow on"
    )
    assert schema["properties"]["inputs"]["type"] == "object"
    assert (
        schema["properties"]["inputs"]["description"]
        == "Input parameters for the workflow (key-value pairs)"
    )
    assert schema["properties"]["dry_run"]["default"] is False
    assert (
        schema["properties"]["dry_run"]["description"]
        == "Preview only; workflow dispatch is not triggered"
    )


def test_get_workflow_runs_request_schema() -> None:
    schema = GetWorkflowRunsRequest.model_json_schema()
    assert schema["required"] == ["repo", "workflow"]
    assert schema["properties"]["repo"]["description"] == "Repository slug (owner/repo)"
    assert (
        schema["properties"]["workflow"]["description"]
        == "Workflow file name (e.g. ci.yml) or workflow ID"
    )
    assert schema["properties"]["limit"]["default"] == 10
    assert schema["properties"]["limit"]["minimum"] == 1
    assert schema["properties"]["limit"]["maximum"] == 50
    assert (
        schema["properties"]["limit"]["description"]
        == "Maximum number of runs to return"
    )


def test_get_workflow_status_request_schema() -> None:
    schema = GetWorkflowStatusRequest.model_json_schema()
    assert schema["required"] == ["repo", "run_id"]
    assert schema["properties"]["repo"]["description"] == "Repository slug (owner/repo)"
    assert schema["properties"]["run_id"]["exclusiveMinimum"] == 0
    assert schema["properties"]["run_id"]["description"] == "Workflow run ID"


def test_get_workflow_logs_request_schema() -> None:
    schema = GetWorkflowLogsRequest.model_json_schema()
    assert schema["required"] == ["repo", "run_id"]
    assert schema["properties"]["repo"]["description"] == "Repository slug (owner/repo)"
    assert schema["properties"]["run_id"]["exclusiveMinimum"] == 0
    assert schema["properties"]["run_id"]["description"] == "Workflow run ID"


# ──────────────────────────────────────────────────────────────────────────────
# Field validation / boundary behavior
# ──────────────────────────────────────────────────────────────────────────────


def test_trigger_workflow_request_requires_repo_and_workflow() -> None:
    with pytest.raises(ValidationError):
        TriggerWorkflowRequest.model_validate({})


def test_trigger_workflow_request_applies_defaults() -> None:
    req = TriggerWorkflowRequest(repo="o/r", workflow="ci.yml")
    assert req.ref == "main"
    assert req.inputs == {}
    assert req.dry_run is False


@pytest.mark.parametrize("limit", [0, 51])
def test_get_workflow_runs_request_rejects_out_of_range_limit(limit: int) -> None:
    with pytest.raises(ValidationError):
        GetWorkflowRunsRequest(repo="o/r", workflow="ci.yml", limit=limit)


@pytest.mark.parametrize("limit", [1, 50])
def test_get_workflow_runs_request_accepts_boundary_limit(limit: int) -> None:
    req = GetWorkflowRunsRequest(repo="o/r", workflow="ci.yml", limit=limit)
    assert req.limit == limit


def test_get_workflow_runs_request_default_limit() -> None:
    req = GetWorkflowRunsRequest(repo="o/r", workflow="ci.yml")
    assert req.limit == 10


@pytest.mark.parametrize("run_id", [0, -1])
def test_get_workflow_status_request_rejects_non_positive_run_id(run_id: int) -> None:
    with pytest.raises(ValidationError):
        GetWorkflowStatusRequest(repo="o/r", run_id=run_id)


def test_get_workflow_logs_request_rejects_non_positive_run_id() -> None:
    with pytest.raises(ValidationError):
        GetWorkflowLogsRequest(repo="o/r", run_id=0)


def test_get_workflow_status_request_accepts_positive_run_id() -> None:
    req = GetWorkflowStatusRequest(repo="o/r", run_id=123)
    assert req.run_id == 123


# ──────────────────────────────────────────────────────────────────────────────
# CicdConfig
# ──────────────────────────────────────────────────────────────────────────────


def test_cicd_config_from_dict_defaults() -> None:
    config = CicdConfig.from_dict({})
    assert config.auth_token == ""
    assert config.repo_allowlist == []
    assert config.workflow_allowlist == []
    assert config.max_log_size_kb == 256
    assert config.github_token == ""


def test_cicd_config_from_dict_populated() -> None:
    config = CicdConfig.from_dict(
        {
            "auth_token": "tok",
            "repo_allowlist": ["o/r"],
            "workflow_allowlist": ["ci.yml"],
            "max_log_size_kb": 512,
            "github_token": "ghtok",
        }
    )
    assert config.auth_token == "tok"
    assert config.repo_allowlist == ["o/r"]
    assert config.workflow_allowlist == ["ci.yml"]
    assert config.max_log_size_kb == 512
    assert config.github_token == "ghtok"


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions — type hierarchy relied upon by callers
# ──────────────────────────────────────────────────────────────────────────────


def test_exception_hierarchy() -> None:
    assert issubclass(CicdAuthorizationError, RuntimeError)
    assert issubclass(CicdNotFoundError, ValueError)
    assert issubclass(CicdValidationError, ValueError)
    assert issubclass(CicdUpstreamError, RuntimeError)
